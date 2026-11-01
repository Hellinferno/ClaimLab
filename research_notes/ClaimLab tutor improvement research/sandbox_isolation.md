# Safely executing untrusted, LLM-written Python (numpy) for ClaimLab: isolation options, trade-offs, and a layered design

Research date: 2026-10-31. All vendor prices below were read from the vendor's own page on 2026-10-31 unless marked otherwise. Sources older than 2025 are tagged **[pre-2025]**.

ClaimLab context this note is written against (from the brief and a quick look at the repo): the child is launched from `backend/src/claimlab/sandbox/executor.py` with `subprocess.Popen(..., "-I", "-S", "-X", "utf8", child.py)`. On Windows it is created `CREATE_SUSPENDED` and then put in a Job Object. On POSIX it uses `start_new_session=True` plus `os.killpg`. `backend/src/claimlab/sandbox/policy.py` already blocks the numpy file and FFI attributes named in public escapes: `ctypes`, `ctypeslib`, `tofile`, `fromfile`, `dump`, `load`, `save*`, `memmap`, `DataSource`, `openfile`, `lib`, `f2py`, `testing`, `Formatter`, `vformat`, `get_field`, `attrgetter`, `methodcaller`, and so on. The policy works as an attribute **denylist** on top of a module allowlist.

---

## Q1. Container-based isolation (Docker with no network, read-only rootfs, non-root, seccomp/AppArmor, cgroups; rootless Podman): what it gives, what attacks remain, overhead, and warm pools

### Takeaway
A hardened Docker/Podman container gives real OS-level guarantees that ClaimLab lacks today. With no network namespace there is no network. A read-only rootfs with only a tmpfs leaves no user files to read. cgroups enforce memory and PID limits, and the default seccomp profile filters syscalls. However, the container shares the host kernel. Kernel bugs and container-runtime (runc) bugs remain escape paths: three runc escape CVEs were disclosed in 2025. A plain container is therefore adequate for a single-tenant demo, and a multi-tenant host needs gVisor or a microVM underneath it.

### Cited Findings
- Docker's default seccomp profile is applied unless you override it with `--security-opt`. It "disables around 44 system calls out of 300+" and is an allowlist whose default action returns a permission error. Blocked calls include `clone`/`unshare`/`setns`/`mount`/`pivot_root`, `bpf`, `ptrace`, `perf_event_open`, kernel-module and kexec calls, and keyring calls. `io_uring_setup/enter/register` are "Blocked due to security vulnerabilities that can be exploited to break out of containers." `socket` is blocked for `AF_ALG` (CVE-2026-31431) and `AF_VSOCK` — [Docker docs: Seccomp security profiles](https://docs.docker.com/engine/security/seccomp/)
- Docker's default seccomp profile does not block user-namespace creation (`unshare --user`) — [Docker docs: Seccomp](https://docs.docker.com/engine/security/seccomp/)
- OWASP hardening flags:
  - Run as non-root with `docker run -u 4000` or a Dockerfile `USER`, or use `--userns-remap=default`.
  - Use `--cap-drop all` and add back only what is needed. Never use `--privileged`.
  - Use `--security-opt=no-new-privileges`.
  - Use `--read-only --tmpfs /tmp`, and mount volumes `:ro`.
  - Set `--ulimit nofile/nproc`.
  - Never expose the Docker socket ("Mounting the socket read-only does not restrict the API").
  - Keep the default seccomp profile and apply per-container AppArmor/SELinux.
  - Rootless mode is recommended but "does not protect against kernel vulnerabilities". Podman is suggested as an alternative.
  - Source: [OWASP Docker Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html)
- 2025 runc escape CVEs:
  - **CVE-2025-31133**: a race on `maskedPaths` uses symlinks so that `/proc/sys/kernel/core_pattern` can be left writable, which allows container escape. runc ignored ENOENT when bind-mounting `/dev/null` over masked paths.
  - **CVE-2025-52565**: a `/dev/console` / `/dev/pts` symlink race exposes procfs.
  - **CVE-2025-52881**: `/proc` write redirection bypasses LSM labels, so writes can reach targets such as `/proc/sysrq-trigger`.
  - Default AppArmor profiles mitigate part of this but not all. Upstream "strongly recommend all users use user namespaced containers."
  - Reported fixed versions are runc 1.2.8 / 1.3.3 / 1.4.0-rc.3. This comes from an aggregator; verify it against GHSA-9493-h29p-rfm2.
  - Sources: [eSecurity Planet](https://www.esecurityplanet.com/news/runc-vulnerability-container-risk/); [GitLab advisory CVE-2025-31133](https://advisories.gitlab.com/pkg/golang/github.com/opencontainers/runc/CVE-2025-31133/); [Docker Scout CVE-2025-31133](https://scout.docker.com/v/CVE-2025-31133); [Corgea](https://corgea.com/advisories/vulnerabilities/CVE-2025-31133)
- OpenAI infra talk on runtime choices: containers isolate through namespaces and limit through cgroups, "but containers are still host processes sharing the kernel". Seccomp reduces kernel attack surface, but it is hard to predict which syscalls agent workloads need. Plain fork-exec was rejected because it reaches the host kernel and gives no noisy-neighbour protection — [ZenML LLMOps DB summary of OpenAI talk (2026)](https://www.zenml.io/llmops-database/designing-agent-sandbox-infrastructure-at-scale-from-runtime-to-orchestration)
- Per-container start overhead: a community benchmark measured about 42 ms average container start under runc. This is a single setup, so treat it as indicative only — [williamzujkowski blog](https://williamzujkowski.github.io/posts/sandboxing-untrusted-containers-with-gvisor-lessons-from-g-fuzz-vulnerability-research)
- gVisor's own performance guide notes that most measured container startup time is Docker's overhead ("even the empty runc benchmark is slow"). It suggests invoking the OCI runtime directly to cut that overhead — [gVisor Performance Guide](https://gvisor.dev/docs/architecture_guide/performance/)
- Warm pools at OpenAI: pre-warmed pools trade idle CPU/memory for latency. Their hybrid design keeps a warm pool but refills it from memory snapshots. Snapshot-aware routing prefers nodes that already cache the image layers — [ZenML summary of OpenAI talk](https://www.zenml.io/llmops-database/designing-agent-sandbox-infrastructure-at-scale-from-runtime-to-orchestration)
- Docker Desktop on Windows with the WSL 2 backend:
  - All WSL 2 distros share one Linux kernel, so Docker "can't ensure the integrity of the kernel in the Docker Desktop Linux VM".
  - A user can run `wsl -d docker-desktop` to get root in the VM.
  - Enhanced Container Isolation (ECI) on WSL hardens containers but "can't prevent Docker Desktop users from breaching the Docker Desktop Linux VM". Using ECI with Hyper-V is "more secure than with WSL 2".
  - Docker's WSL setup page makes a narrower, conflicting claim that the integration adds no risk beyond standard WSL.
  - Sources: [Docker ECI limitations](https://docs.docker.com/enterprise/security/hardened-desktop/enhanced-container-isolation/limitations/); [Docker Desktop WSL 2 backend](https://docs.docker.com/docker-for-windows/wsl/)

### Inferences
- A concrete single-run container for ClaimLab's workload (numpy only, ≤768 MB, about 10 s CPU, no network) would look like this: `docker run --rm --network none --read-only --tmpfs /tmp:rw,size=16m,noexec -u 65534:65534 --cap-drop ALL --security-opt no-new-privileges --memory 768m --memory-swap 768m --pids-limit 32 --cpus 1 --ulimit nofile=64 -i claimlab-sandbox:py312-numpy python -I -S /runner.py < code`. Add `--runtime=runsc` where gVisor is installed. This closes the "child reads the user's files" hole: the image holds only Python + numpy + runner, and no host paths are mounted. It closes the network hole as well.
- Remaining attack classes in a plain (runc) container:
  - kernel exploits through any allowed syscall;
  - runc/containerd escapes like the 2025 trio;
  - side channels and resource-exhaustion DoS within the cgroup limits;
  - anything mounted or passed in by mistake (env secrets, the Docker socket).
  - Using user namespaces (rootless Podman or `userns-remap`) shrinks the impact of an escape, because the attacker lands as an unprivileged host UID.
- On a Windows 11 laptop, Docker Desktop puts a Hyper-V/WSL utility VM between the container and the Windows user session. That is an extra boundary compared with today's design, where the child runs as the Windows user. The ECI docs show this boundary is weaker on WSL 2 than on Hyper-V. Whether a process that escapes into the docker-desktop VM can reach the Windows user's files was not established here (see Gaps).
- Warm pool for a small deployment: keep N (2 to 4) pre-started one-shot containers. Each runs a runner already blocked on stdin with numpy pre-imported. A container serves exactly one job and is then destroyed and replaced. Never reuse a container across users. This removes both container start and `import numpy` from the user-visible latency.

### Gaps
- No primary measurement of `docker run` plus `import numpy` latency for a python:3.12-slim + numpy image was found. It needs to be measured locally.
- Rootless Podman specifics (slirp4netns/pasta overhead, cgroup v2 delegation needs) were not researched in depth.
- It was not established whether a container or VM escape on Docker Desktop with the WSL 2 backend can read `C:\Users\...`. WSL distros typically automount Windows drives, but no source was found specifically for the docker-desktop distro.

---

## Q2. Stronger isolation: gVisor (runsc), Firecracker microVMs, Kata Containers, nsjail/bubblewrap/minijail: startup, numpy compatibility, operations

### Takeaway
gVisor is the pragmatic step up. It is a drop-in OCI runtime (`runsc`) that intercepts syscalls in a user-space kernel. It has negligible overhead for CPU-bound numpy and does not need nested virtualization on its Systrap platform. Major vendors use it: Modal by default, and reportedly OpenAI's code interpreter. Firecracker, Kata, and Cloud Hypervisor microVMs give the strongest boundary (a separate guest kernel behind KVM). They need `/dev/kvm` and considerably more operational work, so they are best consumed through a managed service (E2B, Cloudflare) for a small team. nsjail is a lightweight Linux-only jail with namespaces, seccomp, cgroups, and rlimits. It is a good fit on a single Linux VM where Docker is unwanted, but it still shares the host kernel.

### Cited Findings
- **gVisor architecture and residual risk:** a user-space kernel (Sentry) and a file-access daemon (Gofer) intercept syscalls, so exploits must first compromise user-space code. Both still run on the host kernel, so chained exploits remain possible — [ZenML summary of OpenAI talk](https://www.zenml.io/llmops-database/designing-agent-sandbox-infrastructure-at-scale-from-runtime-to-orchestration)
- **gVisor performance (official guide, © 2026, undated):**
  - "gVisor does not perform emulation or otherwise interfere with the raw execution of CPU instructions", so CPU-bound and ML workloads see minimal overhead.
  - Raw memory access has no extra cost once mappings are installed.
  - Syscall-heavy and small-file VFS workloads carry the main overhead.
  - Systrap is recommended for best performance. ptrace works everywhere but is slowest. The KVM platform runs poorly under nested virtualization.
  - Startup overhead is mostly Docker's; `runsc do` or direct OCI invocation reduces it.
  - Source: [gVisor Performance Guide](https://gvisor.dev/docs/architecture_guide/performance/)
- **gVisor startup numbers (conflicting, measuring different things):**
  - Community: 42 ms (runc) vs 67 ms (gVisor) average container start — [williamzujkowski blog](https://williamzujkowski.github.io/posts/sandboxing-untrusted-containers-with-gvisor-lessons-from-g-fuzz-vulnerability-research)
  - Edera paper: about 0.44–0.68 s full container start depending on platform — [Edera, arXiv 2501.04580](https://arxiv.org/pdf/2501.04580)
  - A comparison table gives 70–150 ms cold start — [itnext](https://itnext.io/openais-code-execution-runtime-replicating-sandboxing-infrastructure-a2574e22dc3c)
- **gVisor and Python imports:** using the Sentry's in-sandbox tmpfs "halves the import latency of many modules", which matters for import-heavy stacks like numpy — [HotCloud '19, Young et al. **[pre-2025]**](https://www.usenix.net/system/files/hotcloud19-paper-young.pdf)
- **Firecracker:**
  - Startup is under 125 ms to the guest init process.
  - Overhead is under 5 MiB per microVM (Firecracker threads, excluding guest memory).
  - The `jailer` wraps the VMM in chroot, namespaces, a tight seccomp filter, and cgroups.
  - Sources: [LWN **[pre-2025]**](https://lwn.net/Articles/775736); [Northflank](https://northflank.com/blog/what-is-aws-firecracker)
  - The Edera paper measured about 2.4 s **full container start** for Firecracker (with container integration, 4 vCPU/4 GB). This does not contradict 125 ms; it measures VM init through container start — [Edera, arXiv 2501.04580](https://arxiv.org/pdf/2501.04580)
- **Kata Containers:**
  - Boots a guest kernel per workload, adding 150–300 ms depending on VMM/config (vendor claim) — [Northflank: Kata vs gVisor](https://northflank.com/blog/kata-containers-vs-gvisor)
  - About 1.9 s full start with the Dragonball VMM — [Edera, arXiv 2501.04580](https://arxiv.org/pdf/2501.04580)
  - Cloud Hypervisor boots to userspace in under 100 ms (vendor claim, not independently verified) — [Northflank: Cloud Hypervisor vs gVisor](https://northflank.com/blog/cloud-hypervisor-vs-gvisor)
- **Isolation strength:**
  - Vendors argue that a VM boundary requires compromising the guest kernel *and* then escaping KVM — [Northflank](https://northflank.com/blog/kata-containers-vs-firecracker-vs-gvisor)
  - OpenAI's agent-infra team calls hardware virtualization "the strongest boundary" and uses Cloud Hypervisor (Rust VMM) with jailed devices and virtio. The cost is guest/host context-switch overhead. Millisecond creation comes from microVM memory snapshots — [ZenML summary of OpenAI talk](https://www.zenml.io/llmops-database/designing-agent-sandbox-infrastructure-at-scale-from-runtime-to-orchestration)
  - A 2020 study found gVisor's "isolation is the best" but with significant I/O/syscall degradation. It predates current Kata/CLH — [Springer via unpaywall **[pre-2025]**](https://unpaywall.org/10.1007%2FS10586-021-03517-8)
- **nsjail:**
  - Namespaces: UTS, mount, PID, IPC, net, user, cgroup, time.
  - Filesystem: chroot/pivot_root, read-only (`-R`) and read-write (`-B`) bind mounts, tmpfs (`-T`).
  - seccomp-bpf in Kafel syntax (`-P`/`--seccomp_string`).
  - Limits: wall time `-t`, `--rlimit_cpu`, `--rlimit_as`, `--rlimit_nofile`, cgroup v1/v2 `--cgroup_mem_max` / `--cgroup_pids_max`.
  - The network namespace is cloned by default, so there is **no network** unless `-N` is passed.
  - Unprivileged use requires `kernel.unprivileged_userns_clone=1`; otherwise it runs as root.
  - Source: [google/nsjail README](https://github.com/google/nsjail)
- **Modal** runs sandboxes on gVisor by default or on a dedicated KVM VM with its own kernel, and supports arbitrary images, so numpy is fine — [Modal docs: Sandbox networking](https://modal.com/docs/guide/sandbox-networking)

### Inferences
- **numpy compatibility:** numpy is CPU and memory bound with few syscalls after import. That is the profile where gVisor's overhead is negligible per its own guide. The main cost is `import numpy` (many small file opens), which a warm pool or pre-imported runner hides. Firecracker and Kata run a full Linux guest, so numpy works unchanged.
- **Operational complexity, low to high:**
  1. nsjail or bubblewrap on a Linux VM: one binary, no daemon. You must hand-curate read-only bind mounts for `/usr/lib/python3.12` and site-packages.
  2. Docker + `--runtime=runsc`: install runsc and register it in `daemon.json`. Works on ordinary cloud VMs with Systrap and needs no nested virtualization.
  3. Kata: needs KVM, so bare metal or nested-virt-enabled instances.
  4. Firecracker directly: you build rootfs/kernel images and handle tap networking (or none), the jailer, and snapshotting. This is weeks of work for a small team and is the reason E2B/Cloudflare-style managed microVMs exist.
- **Recommended self-hosted Linux stack for ClaimLab:** Docker (or containerd) + gVisor runsc + the Q1 hardening flags, on a VM separate from the API server. Alternatively, use nsjail on the API VM, with the API server never holding secrets that the jail can reach.

### Gaps
- bubblewrap and minijail were not researched in this pass. No primary sources were fetched for their flags or limitations.
- No numpy-specific gVisor benchmark exists in the sources found. Benchmark `import numpy` + a representative experiment under runc vs runsc (Systrap) locally.
- Startup figures for nsjail were not found in a primary source; it is expected to be millisecond-scale, but this is unverified.

---

## Q3. In-process / language-level isolation: Pyodide/WebAssembly (browser or server-side), RestrictedPython, seccomp-only; numpy in WASM, performance, guarantees

### Takeaway
numpy does run in WebAssembly (Pyodide ships numpy 2.4.6). WASM is a genuine memory-safe boundary *only if the host runtime grants nothing*. Server-side Pyodide in Node or Deno was escaped in seven products in 2025–2026 via `ctypes` → Emscripten exports → JavaScript host. In-interpreter Python sandboxes (pysandbox, RestrictedPython, asteval) have a long record of escapes; pysandbox's author declared the approach "broken by design". ClaimLab's AST policy is valuable as a fast-fail and attack-surface filter but must not be the boundary.

### Cited Findings
- **Pyodide numpy:** numpy **2.4.6** is included per the docs page for Pyodide **314.0.7** (version numbers as shown on the page header, fetched 2026-10-31) — [Pyodide: Packages built in Pyodide](https://pyodide.org/en/stable/usage/packages-in-pyodide.html)
- **Cyera "Sandcastles, Not Sandboxes" (2026-08-07, ahead of DEF CON 34):**
  - Affected: n8n, Grist, cohere-terrarium, smolagents (WASM executor), langchain-sandbox, stlite, cibuildwheel.
  - "ctypes was available in all seven configurations we tested." `ctypes.CDLL(None)` exposes the Emscripten export table. `emscripten_run_script_string` runs JS in the host, and `system`/`popen`/`execve` reach libc.
  - Attribute walking from `object.__subclasses__()` → `warnings.catch_warnings` recovers `__builtins__`/`__import__`.
  - CVEs: CVE-2025-68668 (n8n, CVSS 9.9), CVE-2026-24002 (Grist, 9.1), CVE-2026-10613 (smolagents, 8.3), CVE-2026-61522 (cohere-terrarium, 9.3).
  - smolagents removed its WasmExecutor in May 2026. n8n moved to external runners in October 2025. Grist moved to Deno with restricted permissions (v1.7.9, December 2025).
  - Recommendations: module allowlists, not denylists; strip `emscripten_run_script*`/`system`/`popen`/`execve` from the WASM binary; run in a separate process/container/OS boundary; minimal Deno `--allow-*`; "Treat Python-level restrictions as one layer of defense in depth, not the sole boundary."
  - Source: [Cyera Research](https://www.cyera.com/research/sandcastles-not-sandboxes-how-one-architectural-flaw-exposed-seven-products)
- **Optimistic counter-view:** a 2026 guide claims Pyodide "inherits the browser's security model" (no filesystem, no network beyond fetch, no subprocess), including server-side under Deno/Node. This conflicts with Cyera's demonstrated escapes, so treat it cautiously — [Morph: WebAssembly Sandbox](https://www.morphllm.com/webassembly-sandbox)
- **Pyodide on servers:** Pyodide is "Not designed for server workloads (even though Cloudflare uses it)", per a Wasmer talk that points to native WASM runtimes (Wasmtime/Wasmer) instead — [Syrus Akbary, Speaker Deck](https://speakerdeck.com/syrusakbary/webassembly-python-and-the-future-of-ai-sandboxing)
- **Riza** executes code "inside a WebAssembly sandbox" with access only to provided args/env/stdin. At preview, filesystem, outbound network, and third-party packages were roadmap items. A self-hosted Docker image was available case by case. Pricing is unconfirmed (aggregators only) — [LangChain Riza integration](https://python.langchain.com/docs/integrations/tools/riza); [Dynamic Business](https://dynamicbusiness.com/ai-tools/riza-safely-execute-javascript-python-ruby-php-in-sandbox.html); [plushcap: self-hosted Riza](https://www.plushcap.com/content/riza/blog/riza-introducing-the-self-hosted-riza-code-interpreter)
- **pysandbox:** Victor Stinner, after three years, judged pysandbox "broken by design". He concluded that the whole Python process must go in an external sandbox, because there are "too many ways to escape the untrusted namespace using the various introspection features". A 2016 restricted-mode challenge was escaped via `cr_frame.f_back` → `f_builtins` — [LWN 2013 **[pre-2025]**](https://lwn.net/Articles/574323/); [python-dev 2013 **[pre-2025]**](https://mail.python.org/pipermail/python-dev/2013-November/130132.html); [python-dev 2016 thread **[pre-2025]**](https://mail.python.org/archives/list/python-dev@python.org/thread/76VBDNEXN3LE3JACAYW6KKOBZKHBAXQE/)
- **RestrictedPython:**
  - CVE-2025-22153: type confusion in `try/except*` bypasses the sandbox in 6.0 to <8.0, CVSS 7.9. The fix removes `try/except*` support.
  - CVE-2026-76825: escape via `string.Formatter` field resolution when `string`/Formatter is exposed, fixed in 8.4, CVSS 8.4.
  - CVE-2026-55830: guard-hook bypass via positional-only args, fixed in 8.3 (title only, unverified).
  - Sources: [Wiz CVE-2025-22153](https://www.wiz.io/vulnerability-database/cve/cve-2025-22153); [SOCRadar CVE-2026-76825](https://socradar.io/free-tools/cve-radar/CVE-2026-76825); [Corgea RestrictedPython advisories](https://corgea.com/advisories/packages/pypi/restrictedpython)
- **asteval numpy escape:**
  - asteval's numpy integration exposed `ndarray.ctypes`, which was not filtered by `safe_getattr`. This gave native memory read/write and code execution as the process user.
  - Reported 2025-01-31, fixed 2025-02-21, disclosed 2025-03-07. Versions ≤1.0.6 are affected.
  - A later fix (1.0.9) added `ctypes`, `dump`, and `tofile` as unsafe ndarray attributes.
  - Sources: [Full Disclosure 2025-03](https://seclists.org/fulldisclosure/2025/Mar/0); [Vulert](https://vulert.com/vuln-db/asteval-sandbox-escape--arbitrary-native-memory-read-write-via-numpy-ctypes-in-default-asteval-inter---)
  - Wiz assigns **CVE-2026-102734**, but the page says it is AI-generated and its dates are inconsistent; verify on NVD/GHSA — [Wiz CVE-2026-102734](https://www.wiz.io/vulnerability-database/cve/cve-2026-102734)
- **seccomp-only approaches:** Stinner pointed to OS-level options such as PyPy's sandbox (syscalls proxied to a checking process) and seccomp-nurse — [LWN **[pre-2025]**](https://lwn.net/Articles/574323/). OpenAI's team notes it is hard to predict which syscalls agent workloads need, which makes seccomp-only tuning fragile — [ZenML summary](https://www.zenml.io/llmops-database/designing-agent-sandbox-infrastructure-at-scale-from-runtime-to-orchestration)

### Inferences
- ClaimLab's policy already covers the publicly documented numpy/Python primitives: `ctypes`, `tofile`, `dump`, `fromfile`, `load`, `memmap`, `DataSource`, `openfile`, `lib`, the `Formatter`/`vformat`/`get_field` family, `attrgetter`/`methodcaller`, underscore names (which kills `__subclasses__` walking), and no `getattr`/`eval`/`exec`/`compile`. It is still a **denylist over numpy's attribute surface**, which is exactly the pattern Cyera and Stinner say fails over time. The `numpy.ma.mrecords.openfile` bypass the security review found is an instance of this.
- One further numpy surface worth checking: numpy BitGenerators (for example `np.random.PCG64`) expose `.ctypes` and `.cffi` pointer interfaces. `.ctypes` is already blocked by name. `.cffi` only works if cffi is installed, and the sandbox venv holds only numpy. This comes from general numpy API knowledge and was not re-verified in this research.
- **Browser-side Pyodide** moves execution off the server entirely: the learner's browser sandbox protects ClaimLab's host. However, results become client-supplied and forgeable, so the server must treat them as untrusted. It also adds a 10+ MB Pyodide download and moves the "reviewed code performs calculations" guarantee to the client. It suits optional "play" experiments, not the authoritative experiment record.
- **Server-side Pyodide/WASM** only helps if run under Deno with zero `--allow-*` permissions, or under Wasmtime with no WASI preopens and no sockets. It also needs a separate OS process with limits. At that point it offers little over a container for this workload, and numpy-on-WASI outside Pyodide is not readily available.
- **RestrictedPython** would add a rewrite-time guard layer, but it has had three sandbox-bypass CVEs in about 20 months. It is not a reason to drop OS isolation.

### Gaps
- No primary benchmark of numpy performance in Pyodide vs native was found. Expect it to be slower (single-threaded, no SIMD/BLAS parity), but this is unquantified.
- Whether numpy wheels exist for WASI (Wasmtime/Wasmer) outside the Emscripten/Pyodide toolchain was not verified.
- Riza's current pricing and numpy support were not confirmed from riza.io.

---

## Q4. Windows-specific: AppContainer / LPAC, Windows Sandbox, restricted tokens, Job Objects: what is realistic on Windows 11 for a local demo

### Takeaway
On Windows 11 Pro, the realistic local-demo upgrade is to launch the existing child inside an **LPAC (Less Privileged AppContainer)** with zero capabilities, keeping the current Job Object. An AppContainer with no capabilities has **no network**, cannot open the user's profile files unless they are explicitly ACL-granted, and gets a distinct SID so it cannot use the user's credentials. You must ACL-grant read+execute on the Python install and `.sandbox-venv`, plus read-write on a per-run workdir. Windows Sandbox (a disposable Hyper-V VM with networking disabled) is a stronger boundary but heavier and slower to start, so it is better as a "show the judges" alternative than as a per-run executor. Job Objects alone only limit resources; they are not an access-control boundary.

### Cited Findings
- **Microsoft Learn, AppContainer isolation (updated 2025-07-08):**
  - Credential isolation: the identity combines user and app, so "the application cannot impersonate the user".
  - Device isolation: camera, mic, and similar are blocked by default.
  - File isolation: read-write access only to granted files and registry keys, and "Read-only access is less restricted".
  - Network isolation: "Granular access can be granted for Internet access, Intranet access, and acting as a server".
  - Process and window isolation of kernel objects.
  - Source: [Microsoft Learn: AppContainer isolation](https://learn.microsoft.com/en-us/windows/win32/secauthz/appcontainer-isolation)
- **Practical AppContainer behaviour:** a process started without capabilities gets "no access to the FS (except the subtree allocated to the container in LocalAppData), no network access". File access is granted through object ACLs on the AppContainer SID — [blahcat: Cheap sandboxing with AppContainers (2020) **[pre-2025]**](https://blahcat.github.io/posts/2020/12/29/cheap-sandboxing-with-appcontainers.html). This is more absolute than Microsoft's "read-only access is less restricted" wording: system directories readable by ALL APPLICATION PACKAGES remain readable.
- **LPAC** (Windows 10 1703+) is stricter than a normal AppContainer in access checks — [Chromium sandbox app_container_test.cc](https://chromium.googlesource.com/chromium/src/sandbox/+/bee0ab3710fd565ea08afdb1b962c8723e8e1cd6/win/src/app_container_test.cc)
- **Reference implementation pattern (landstrip):**
  - Create a per-run LPAC profile.
  - Grant its SID access only to the needed read and read-write roots, and remove the grants after the process tree exits.
  - Assign the process to a Job Object with `KILL_ON_JOB_CLOSE`.
  - Source: [landstrip crate docs](https://docs.rs/crate/landstrip/0.16.9)
- **Network:** AppContainer capabilities are coarse. Fine-grained host/port policy needs Windows Filtering Platform rules keyed to the AppContainer SID. DNS often fails even with `internetClient`, which is irrelevant for a no-network sandbox — [rappct examples](https://docs.rs/crate/rappct/latest/source/EXAMPLES.md)
- **Windows Sandbox:**
  - Configured by an XML `.wsb` file. `<Networking>Disable</Networking>` "can decrease the attack surface" — [Microsoft Learn: Windows Sandbox configuration](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-configure-using-wsb-file)
  - Windows 11 24H2+ adds a `wsb` CLI, for example `wsb start --config "<Configuration><Networking>Disabled</Networking></Configuration>"`. Note the "Disable" vs "Disabled" spelling discrepancy between the two pages — [Microsoft Learn: Windows Sandbox CLI](https://learn.microsoft.com/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-cli)
- **Docker Desktop on WSL 2** is a weaker VM boundary than Hyper-V (shared WSL kernel; user can get root in the docker-desktop distro) — [Docker ECI limitations](https://docs.docker.com/enterprise/security/hardened-desktop/enhanced-container-isolation/limitations/)

### Inferences
- **Minimum viable Windows hardening for the demo, building on the current `executor.py`:**
  1. Create an AppContainer profile (`CreateAppContainerProfile`) once at startup. Launch the child via `CreateProcessW` with `STARTUPINFOEX` + `PROC_THREAD_ATTRIBUTE_SECURITY_CAPABILITIES` with zero capabilities, which means no network. Add `PROC_THREAD_ATTRIBUTE_ALL_APPLICATION_PACKAGES_POLICY` to opt into LPAC.
  2. Grant the AppContainer SID read/execute (and, for LPAC, explicit access) on the base Python install directory, `.sandbox-venv`, and `child.py`. Grant read-write only on a fresh per-run temp workdir. Revoke the grants afterwards.
  3. Keep the existing Job Object (memory/time). Add `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`, `ActiveProcessLimit=1` (no subprocesses), and UI restrictions.
  4. Pass a minimal environment block: no API keys, no `USERPROFILE`-derived paths beyond what Python needs.
  5. Verify the result with a negative test suite that tries `socket.create_connection` (via a deliberately unguarded harness, not via the policy) and tries reading `%USERPROFILE%\Documents\*`. Both should fail with access denied *even when the Python policy is disabled*.
- **Python in an AppContainer has known friction.** If Python is installed under `%LOCALAPPDATA%\Programs\Python`, it is not readable by the container until ACL-granted. numpy's DLLs (OpenBLAS) load from site-packages and need the same grant. The Microsoft Store Python build is itself a packaged app and may be harder to nest. Budget about 0.5–1.5 days, including testing.
- **Restricted tokens** (`CreateRestrictedToken` with deny-only SIDs) plus a low-integrity level are an older alternative. They block writes but not reads of user files, and they do not block network. AppContainer/LPAC is the better fit for ClaimLab's actual threat: *read user files, then exfiltrate via web_search*.
- Even with AppContainer, the child runs on the same Windows kernel. That is acceptable for a single-user local demo and not for hosting.
- **Windows Sandbox per run** is too heavy (VM boot, one instance at a time historically). It can be used for "run the whole backend inside Windows Sandbox for the demo", which puts the entire app, not just the child, away from personal files.

### Gaps
- No official Microsoft page fetched spells out exactly which file-system locations a zero-capability LPAC can read by default.
- No source was found for Windows Sandbox start-up time or concurrent-instance limits on 24H2.
- AppContainer + CPython + numpy compatibility has no public write-up found; it needs a local spike.

---

## Q5. Hosted code-execution sandboxes as a service (E2B, Modal, Daytona, Riza, Fly Machines, Cloudflare, Cloud Run, Lambda): isolation, numpy, latency, pricing, free tiers, privacy

### Takeaway
For a hackathon, E2B (Firecracker microVM, $100 one-time credit, no card) and Daytona ($200 credit) are the fastest ways to get a VM-grade boundary with numpy. Modal (gVisor or VM, $30/month recurring credit) is a close third. Cloudflare Sandbox/Containers (microVM per sandbox, from $5/month Workers Paid with included usage) is the cheapest recurring option if the backend is near Cloudflare. **Every provider defaults to outbound internet ON,** so network must be explicitly disabled. Per-run compute cost for a 10 s, 1 vCPU, 1 GiB job is a fraction of a cent everywhere. The real costs are idle time, plan fees, and an extra network round-trip.

### Cited Findings
- **E2B** (pricing page fetched 2026-10-31):
  - Hobby: $0, "$100 one-time usage credits", sessions up to 1 h, 20 concurrent sandboxes, no credit card.
  - Pro: $150/month + usage, 24 h sessions, 100 concurrent (add-ons up to 1,100).
  - Enterprise: custom, $3,000/month minimum, BYOC on request.
  - Rates: **$0.000014 per vCPU-second** and **$0.0000045 per GiB-second**; storage free. CPU-only.
  - The page has no data-retention/privacy terms.
  - Source: [E2B Pricing](https://e2b.dev/pricing)
  - Isolation: every sandbox is a Firecracker microVM with its own kernel — [E2B docs: calculate sandbox price](https://docs.e2b.dev/faq/calculate-sandbox-price); [Morph E2B pricing](https://www.morphllm.com/e2b-pricing)
  - Network: outbound internet **on by default**. Disable it with `Sandbox.create(allow_internet_access=False)`, equivalent to `network={"deny_out": ["0.0.0.0/0"]}`. Domain allowlists apply only to HTTP:80/TLS:443 — [E2B docs: Internet access](https://docs.e2b.dev/sandbox/internet-access)
- **Modal** (pricing page fetched 2026-10-31):
  - Starter: $0 + compute with **$30/month free credits**, 100 containers.
  - Team: $250/month with $100/month credits.
  - Sandbox CPU: **$0.00003942 per physical core-second** (1 core = 2 vCPU, minimum 0.125 core). Memory: **$0.00000667 per GiB-second**.
  - Sandboxes bill at non-preemptible rates (3x the base $0.0000131/core-s). A region-selection multiplier of 1.15–1.75x applies on top.
  - Source: [Modal Pricing](https://modal.com/pricing)
  - Isolation: gVisor or a dedicated KVM VM.
  - Network: default allows outbound to any public IP. `block_network=True` drops all outbound traffic; `outbound_cidr_allowlist` and `outbound_domain_allowlist` (beta) are available. DNS is unrestricted unless all outbound traffic is blocked.
  - Source: [Modal docs: Sandbox networking](https://modal.com/docs/guide/sandbox-networking)
  - Modal does not publish pricing for volumes/egress (aggregator claim) — [Northflank AI sandbox pricing](https://northflank.com/blog/ai-sandbox-pricing)
- **Daytona** (pricing page fetched 2026-10-31):
  - "$200 in free compute included", free trial without a credit card, startups up to $50k credits.
  - Rates: $0.0504/vCPU-h, $0.0162/GiB-h, storage $0.000108/GiB-h after 5 GiB free; Windows $0.0858/vCPU-h. Billed per second.
  - Claims "Sub 90ms sandbox creation". **The isolation technology is not stated** on the pricing page.
  - Source: [Daytona Pricing](https://www.daytona.io/pricing)
  - CostBench (June 2026) says there is no free plan, contradicting Daytona's own page — [CostBench Daytona](https://costbench.com/software/ai-code-execution/daytona/free-plan/)
- **Cloudflare Sandbox SDK / Containers** (fetched 2026-10-31):
  - Linux sandboxes run as containers, "each one is a microVM with its own kernel and network". `enableInternet: false` blocks internet. Inbound reaches the container only through your Worker. Dynamic Workers can run Python with `globalOutbound: null`. "Available on Workers Paid plan" — [Cloudflare Sandbox SDK](https://developers.cloudflare.com/sandbox/)
  - Pricing is billed per 10 ms active on the $5/month Workers Paid plan. Included: **375 vCPU-min, 25 GiB-h memory, 200 GB-h disk** per month. Overage: $0.000020/vCPU-s, $0.0000025/GiB-s, $0.00000007/GB-s disk. The Free plan has no container allowance.
  - Instance types: lite (1/16 vCPU, 256 MiB), basic (1/4 vCPU, 1 GiB), standard-1 (1/2 vCPU, 4 GiB), and larger.
  - Memory and disk are billed on provisioned size; CPU on active use.
  - Source: [Cloudflare Containers pricing](https://developers.cloudflare.com/containers/pricing/)
- **Fly Machines:** shared-cpu-1x 256 MB at $0.00000075/s (about $1.94/month), billed per second while started. Stopped machines pay rootfs storage at $0.15/GB-month. Extra RAM is $5/GB-month — [Fly.io pricing](https://fly.io/docs/pricing/); [Fly pricing.md](https://fly.io/pricing.md); [Fly credit cards doc](https://fly.io/docs/about/credit-cards/). The search results did not confirm the isolation technology.
- **Riza:** WASM-based; pricing and numpy support unconfirmed (see Q3) — [LangChain Riza](https://python.langchain.com/docs/integrations/tools/riza)
- **Third-party claim, uncorroborated:** Modal "cost 41% more per vCPU than E2B or Daytona" — [beri.net comparison](https://www.beri.net/article/e2b-vs-modal-vs-daytona-agent-sandbox-pricing-isolation-2026)

### Inferences
- **Per-run compute cost** for a 10 s run at 1 vCPU and 1 GiB, ignoring boot/teardown and plan fees:
  - E2B: 10 × (0.000014 + 0.0000045) ≈ **$0.000185**, about $0.19 per 1,000 runs. The $100 credit covers on the order of 500k such runs.
  - Daytona: same rates as E2B, ≈ **$0.000185**.
  - Modal: 10 × (0.5 × 0.00003942 + 0.00000667) ≈ **$0.00026**, about $0.26 per 1,000 runs. The $30/month credit covers about 100k runs per month.
  - Cloudflare `basic` (1/4 vCPU, 1 GiB): 10 s wall time ≈ 2.5 vCPU-s + 10 GiB-s, so the included tier covers roughly **9,000 runs/month** for $5. A 1/4 vCPU slows a CPU-bound job 4x, so `standard-1` may be needed.
  - These ignore sandbox lifetime overhead (boot, `import numpy`, idle keep-alive), which in practice dominates.
- **Data privacy:** ClaimLab's experiments use seeded synthetic data, so sending code and results to a vendor is low-sensitivity. The bigger privacy point is to never inject learner PII or source documents into the sandbox. Vendor DPAs and retention terms were not on the pricing pages.
- **Latency:** each hosted call adds a WAN round-trip plus sandbox create (tens to hundreds of ms per vendor claims). Keep one sandbox per active learner session (same tenant) alive for the session and kill it on idle, rather than creating one per run.

### Gaps
- Google Cloud Run jobs and AWS Lambda were not researched: no current pricing, cold-start, or isolation sources fetched. Both are plausible "container/function as sandbox" options, but Lambda's 15-min limit and Cloud Run job start latency are unverified here.
- Vendor data-retention and DPA terms for E2B/Modal/Daytona/Cloudflare were not found on pricing pages.
- Independent cold-start measurements for E2B/Daytona/Modal/Cloudflare were not found; only vendor claims (Daytona "sub 90ms").
- Daytona's isolation technology and Fly's VM technology are unconfirmed from primary sources in this pass.

---

## Q6. How major LLM products isolate code (reference designs)

### Takeaway
The common reference design is: no network, a workspace-scoped filesystem, fixed preinstalled libraries (numpy included), per-session containers with hard CPU/RAM/disk/time limits, and isolation below the container. OpenAI is reported to use gVisor for its code interpreter, and its agent-infra team uses Cloud Hypervisor microVMs with snapshot-based warm pools. Anthropic and Google document the *policy* (no internet, limits, libraries) but not the isolation technology.

### Cited Findings
- **Anthropic code execution tool** (docs fetched 2026-10-31):
  - Linux container, Python 3.11, x86_64; 1 CPU, 5 GiB RAM, 5 GiB workspace disk.
  - "Internet access: Completely disabled for security". "No outbound network requests allowed". "Full isolation from host system and other containers". "File access: Limited to workspace directory only".
  - Preinstalled: pandas, numpy, scipy, scikit-learn, statsmodels; no runtime package install.
  - Containers expire 30 days after creation and are checkpointed after about 5 minutes idle.
  - Pricing: 1,550 free hours per organization per month, then $0.05 per container-hour.
  - Not ZDR-eligible ("Container data retained up to 30 days"). The isolation technology is not named.
  - Source: [Claude Platform docs: Code execution tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/code-execution-tool)
- **Google Gemini code execution:**
  - "The maximum runtime of the code environment is 30 seconds."
  - Python only; numpy, pandas, SciPy, scikit-learn, SymPy preinstalled; "You can't install your own libraries".
  - Matplotlib-only graph output; the model may regenerate code up to 5 times on error.
  - No extra fee beyond tokens.
  - The page does not describe isolation or network policy.
  - Source: [Gemini API docs: Code execution](https://ai.google.dev/gemini-api/docs/code-execution)
- **OpenAI:**
  - Third-party analyses report the ChatGPT code interpreter runs in gVisor: a Jupyter kernel in a gVisor-sandboxed container, inferred from a gVisor boot string. This is not official — [itnext](https://itnext.io/openais-code-execution-runtime-replicating-sandboxing-infrastructure-a2574e22dc3c); [mkarots: Poking around ChatGPT's sandbox](https://hn.jakechampion.name/reader/https://mkarots.github.io/blog/chatgpt-sandbox-exploration)
  - An OpenAI RL/agent-infra talk (2026) compares fork-exec, containers, gVisor, and microVMs, and states the team uses Cloud Hypervisor microVMs with jailed devices. It also covers copy-on-write XFS snapshots, an object-storage-backed filesystem over NBD, a global control plane with snapshot-aware routing, and warm pools grown from memory snapshots — [ZenML LLMOps DB](https://www.zenml.io/llmops-database/designing-agent-sandbox-infrastructure-at-scale-from-runtime-to-orchestration)

### Inferences
- ClaimLab's target envelope (≈10 s, ≤768 MB, numpy, JSON out) is much smaller than these products (Anthropic: 1 CPU/5 GiB; Gemini: 30 s). It is closest to Gemini's model: short, stateless, fixed libraries, no installs, no network.
- **Design choices worth copying:**
  - the network fully off, not allowlisted;
  - fixed preinstalled libraries (ClaimLab already has this via `.sandbox-venv`);
  - a workspace-only filesystem;
  - a hard wall-clock limit with a typed error (`execution_time_exceeded`);
  - an isolation layer below the container (gVisor or microVM).
- These built-in tools are tied to their vendor's model. ClaimLab's tutor runs on a Meta model, so they are reference designs, not drop-in executors.

### Gaps
- OpenAI has not officially confirmed gVisor for the ChatGPT code interpreter in any source found. The ZenML piece is a summary of a talk, not an OpenAI engineering post.
- Anthropic and Google do not publish their sandbox isolation technology.
- Whether the Meta/Llama API offers a hosted code-execution tool was not researched.

---

## Q7. Known CVEs and escape techniques for Python sandboxes, and defence-in-depth guidance

### Takeaway
The escape catalogue is consistent:
- introspection and attribute walking (`__subclasses__`, frames, `__builtins__`);
- FFI (`ctypes`, including numpy's `ndarray.ctypes`);
- format-string field resolution (`string.Formatter`);
- new syntax (`try/except*`);
- file helpers hidden in large libraries (numpy `tofile`/`dump`/`mrecords.openfile`);
- below Python, container-runtime and kernel bugs.

Current guidance from Cyera (2026), Docker, OWASP, and runc upstream converges on the same rule: language-level filters are a layer, and the boundary must be OS-level (process + namespace/VM) with network and filesystem denied by default.

### Cited Findings
- Attribute-walking and `__builtins__` recovery, and `ctypes` → host functions, in seven Pyodide-based products (CVE-2025-68668, CVE-2026-24002, CVE-2026-10613, CVE-2026-61522) — [Cyera Research (2026-08-07)](https://www.cyera.com/research/sandcastles-not-sandboxes-how-one-architectural-flaw-exposed-seven-products)
- numpy `ndarray.ctypes` escape in asteval (≤1.0.6), with `ctypes`/`dump`/`tofile` later marked unsafe — [Full Disclosure 2025-03](https://seclists.org/fulldisclosure/2025/Mar/0); [Vulert](https://vulert.com/vuln-db/asteval-sandbox-escape--arbitrary-native-memory-read-write-via-numpy-ctypes-in-default-asteval-inter---)
- RestrictedPython CVE-2025-22153 (`try/except*` type confusion) and CVE-2026-76825 (`string.Formatter`) — [Wiz](https://www.wiz.io/vulnerability-database/cve/cve-2025-22153); [SOCRadar](https://socradar.io/free-tools/cve-radar/CVE-2026-76825)
- pysandbox "broken by design"; frame-walk escape (`cr_frame.f_back.f_builtins`) — [LWN **[pre-2025]**](https://lwn.net/Articles/574323/); [python-dev 2016 **[pre-2025]**](https://mail.python.org/archives/list/python-dev@python.org/thread/76VBDNEXN3LE3JACAYW6KKOBZKHBAXQE/)
- Container-runtime escapes CVE-2025-31133 / 52565 / 52881; mitigated by user-namespaced containers and LSMs — [eSecurity Planet](https://www.esecurityplanet.com/news/runc-vulnerability-container-risk/); [GitLab advisory](https://advisories.gitlab.com/pkg/golang/github.com/opencontainers/runc/CVE-2025-31133/)
- Docker blocks io_uring because of container-breakout vulnerabilities, and blocks `AF_ALG` sockets (CVE-2026-31431) — [Docker docs: Seccomp](https://docs.docker.com/engine/security/seccomp/)
- Cyera's defence list: module allowlists over denylists, strip dangerous exports, separate process/container/OS boundary, least-privilege runtime permissions, and "Treat Python-level restrictions as one layer of defense in depth, not the sole boundary" — [Cyera](https://www.cyera.com/research/sandcastles-not-sandboxes-how-one-architectural-flaw-exposed-seven-products)
- OWASP container guidance: non-root, cap-drop all, no-new-privileges, read-only rootfs, keep default seccomp, AppArmor/SELinux, never expose the Docker socket, and rootless mode does not stop kernel exploits — [OWASP Docker Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html)

### Inferences
- **ClaimLab-specific exfiltration chain.** The security review's concern was: child reads a file → returns it in `metrics`/`table` → tutor LLM places it in a `web_search` query. This means a network block *on the child alone* is insufficient. The filesystem must be denied at the OS level, and output must be treated as untrusted. Application-level controls are needed too:
  - cap output size;
  - validate the result schema (numbers, short labels, bounded arrays);
  - reject long free-text strings;
  - never let raw experiment output flow verbatim into `web_search` query text without a filter (for example, block high-entropy or path-like strings and strings longer than about 100 chars).
- **Keep the AST/import policy, but reposition it.** Its jobs are fast, friendly rejection of bad LLM code, reduced attack surface, and audit signal, not the security boundary. Consider converting `BLOCKED_ATTRIBUTES` toward a per-module **allowlist** of permitted numpy callables and attributes, given that numpy's attribute surface keeps growing.
- No Trail of Bits or NCC Group primary guidance on Python sandboxes was fetched in this pass. The equivalent recommendations come from Cyera, OWASP, Docker, and runc upstream.

### Gaps
- Trail of Bits and NCC Group write-ups were not retrieved, so no quotes from them are included.
- The CVE IDs CVE-2026-102734 (asteval) and CVE-2026-55830 (RestrictedPython) come from AI-generated or title-only aggregator pages and need NVD/GHSA confirmation.

---

## Q8. Recommended layered design: (a) hackathon demo in the next few days, (b) hosted multi-user deployment

### Takeaway
**(a) Demo:** keep everything ClaimLab has (allowlist AST policy, runtime guard, isolated `-I -S` interpreter in `.sandbox-venv`, Job Object). Add one real OS boundary that denies files and network by default. Choose one of the following:
- **(a1) running on the Windows laptop:** an LPAC AppContainer with zero capabilities and ACL grants only on Python, the venv, and the workdir;
- **(a2) deployed to a Linux VM:** a hardened `docker run --network none --read-only ...`, ideally with `--runtime=runsc`;
- **(a3) a hosted provider:** E2B with `allow_internet_access=False`, behind a single `SandboxBackend` interface.

Also add output-to-web_search filtering. **(b) Hosted multi-user:** one-shot (or per-session, same-tenant) sandboxes on gVisor or microVMs (self-hosted runsc on a dedicated node pool, or managed E2B/Modal/Cloudflare). Network fully off, read-only image, non-root, cgroup limits, no secrets, separate from the API host, a warm pool, and app-level output validation.

### Cited Findings
- Language-level sandboxes are not a boundary; use an external OS sandbox — [LWN **[pre-2025]**](https://lwn.net/Articles/574323/); [Cyera](https://www.cyera.com/research/sandcastles-not-sandboxes-how-one-architectural-flaw-exposed-seven-products)
- A zero-capability AppContainer has no network; file access needs explicit ACL grants — [Microsoft Learn](https://learn.microsoft.com/en-us/windows/win32/secauthz/appcontainer-isolation); [blahcat **[pre-2025]**](https://blahcat.github.io/posts/2020/12/29/cheap-sandboxing-with-appcontainers.html); [landstrip](https://docs.rs/crate/landstrip/0.16.9)
- Docker hardening flags and default seccomp — [OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html); [Docker seccomp](https://docs.docker.com/engine/security/seccomp/)
- gVisor has negligible CPU overhead, uses Systrap on ordinary VMs, and still runs on the host kernel — [gVisor perf guide](https://gvisor.dev/docs/architecture_guide/performance/); [ZenML/OpenAI](https://www.zenml.io/llmops-database/designing-agent-sandbox-infrastructure-at-scale-from-runtime-to-orchestration)
- E2B: Firecracker; `allow_internet_access=False`; $100 one-time credit; $0.000014/vCPU-s — [E2B pricing](https://e2b.dev/pricing); [E2B internet access](https://docs.e2b.dev/sandbox/internet-access)
- Modal: gVisor/VM; `block_network=True`; $30/month credits — [Modal pricing](https://modal.com/pricing); [Modal networking](https://modal.com/docs/guide/sandbox-networking)
- Cloudflare: microVM per sandbox; `enableInternet: false`; $5/month includes 375 vCPU-min + 25 GiB-h — [Cloudflare Sandbox](https://developers.cloudflare.com/sandbox/); [Cloudflare Containers pricing](https://developers.cloudflare.com/containers/pricing/)
- Warm pools plus snapshots — [ZenML/OpenAI](https://www.zenml.io/llmops-database/designing-agent-sandbox-infrastructure-at-scale-from-runtime-to-orchestration)
- Reference policy (no internet, workspace-only files, preinstalled numpy, hard limits) — [Anthropic code execution docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/code-execution-tool); [Gemini code execution](https://ai.google.dev/gemini-api/docs/code-execution)

### Inferences

**Comparison matrix.** This is a synthesis of the findings above. Latency and effort figures are estimates unless cited.

| Approach | Boundary vs host | Files / network by default | numpy | Cold start (cited or est.) | Setup effort | Cost | Where it runs |
|---|---|---|---|---|---|---|---|
| Current: AST policy + venv + Job Object | None at OS level (runs as user) | User files readable; network open | Yes | ~0.2–0.5 s est. (process + import) | Done | $0 | Win/Linux |
| + AppContainer/LPAC (0 caps) + Job Object | Windows token/ACL boundary, same kernel | Files denied unless ACL-granted; no network | Yes, needs ACL grants for Python/venv | Same as now + ms | 0.5–1.5 days est. | $0 | Windows 10 1703+ / 11 |
| Windows Sandbox (`Networking=Disable`) | Hyper-V VM | Clean disposable VM; no network | Must install in VM | Seconds+ (not sourced) | Low for "run whole app inside"; poor per-run | $0 (Pro/Ent) | Windows 11 Pro/Ent |
| Docker hardened (runc) | Namespaces + cgroups + seccomp, shared kernel | `--network none`, read-only image | Yes | ~42 ms container start (community) + import | 0.5 day | $0 / VM cost | Linux, or Docker Desktop (WSL2 VM) |
| nsjail / bubblewrap | Namespaces + seccomp + cgroups, shared kernel | No net by default (nsjail); only bound paths | Yes (bind python + site-packages) | ms (unverified) | 0.5–1 day | $0 | Linux only |
| Docker + gVisor runsc | User-space kernel over host kernel | Same as Docker | Yes; CPU overhead negligible | 67 ms (community) to 0.44–0.68 s (Edera) | +0.5 day over Docker | $0 / VM cost | Linux (Systrap, no nested virt needed) |
| Kata / Firecracker (self-hosted) | Hardware VM (KVM) | Guest-only FS; no NIC unless configured | Yes | <125 ms to init (FC); ~1.9–2.4 s full container (Edera) | Days to weeks | VM/bare-metal with KVM | Linux + /dev/kvm |
| Pyodide in browser | Browser sandbox (learner's machine) | No server FS/network involvement | numpy 2.4.6 | 10+ MB download, seconds (est.) | 1–2 days; results forgeable | $0 | Any browser |
| Pyodide server-side (Node/Deno) | WASM + host runtime; 7 products escaped | Only as strong as host permissions | Yes | Seconds (est.) | Medium; risky | $0 | Any |
| RestrictedPython | None (in-process) | N/A | Partial | ~0 | Medium | $0 | Any; 3 bypass CVEs 2025–26 |
| E2B | Firecracker microVM | **Internet ON by default**; `allow_internet_access=False` | Yes | Vendor-claimed fast; not verified | Hours (SDK) | $0.000014/vCPU-s; $100 one-time free | Hosted |
| Modal Sandboxes | gVisor (default) or KVM VM | Outbound ON by default; `block_network=True` | Yes | Not verified | Hours | $0.0000394/core-s (=2 vCPU); $30/month free | Hosted |
| Daytona | Not stated on pricing page | Not verified | Yes (general Linux) | "Sub 90ms" (vendor) | Hours | $0.0504/vCPU-h; $200 free | Hosted |
| Cloudflare Sandbox/Containers | microVM per sandbox | `enableInternet:false` | Yes (container image) | Not verified | ~1 day (Worker + container) | $5/month incl. 375 vCPU-min | Hosted, Workers Paid |

**(a) Hackathon demo: recommended layered design (in priority order)**
1. **L0, LLM-output gate (exists).** Keep the AST/import allowlist and runtime guard. Its job is fast rejection and friendly errors.
2. **L1, process hygiene (mostly exists).** Keep `-I -S`, the dedicated `.sandbox-venv`, and a minimal env with no API keys (ensure `META_API_KEY`-style variables are not inherited). Use a fresh temp workdir, a stdout JSON result with a hard byte cap (for example 256 KB), and strict schema validation on the host.
3. **L2, one OS boundary that denies files and network.** Pick by where the demo runs:
   - **Laptop demo (Windows 11 Pro):** LPAC AppContainer with zero capabilities + the existing Job Object (+ `KILL_ON_JOB_CLOSE`, `ActiveProcessLimit=1`). Add two negative tests that run with the Python policy *disabled*: "read `%USERPROFILE%` fails" and "open socket fails". These prove the OS layer works on its own.
   - **Deployed demo (Linux VM, judges hit a URL):** a one-shot hardened container per run (flags in Q1). Add `--runtime=runsc` if installable in time. Run 2–4 pre-warmed containers with numpy pre-imported.
   - **Least local work:** E2B (`allow_internet_access=False`) behind a `SandboxBackend` interface, falling back to local when there is no key. The Hobby tier is free with no card.
4. **L3, app-level exfiltration guard.** Results go to the tutor as structured numbers only. The `web_search` tool rejects queries containing path-like strings, base64/high-entropy runs, or verbatim experiment-output text over N chars. Log the code hash, policy verdict, and sandbox verdict.
5. **Fail closed.** If the OS sandbox can't start (for example, AppContainer creation fails), refuse to run rather than silently falling back to the unconfined child. Show this state in the UI.

**(b) Hosted multi-user: recommended layered design**
1. **L0/L1** as above. Additionally, rate-limit per user and per session, cap queued jobs, and set a per-tenant CPU-seconds budget.
2. **L2, VM-grade or gVisor-grade sandbox, network fully off.** Two options:
   - **Self-hosted:** containerd/Docker + **gVisor runsc** on a *dedicated* sandbox VM or node pool, separate from the API/DB hosts, with the Q1 flags (`--network none`, `--read-only`, tmpfs `/tmp` size-capped and `noexec`, UID 65534, `--cap-drop ALL`, `no-new-privileges`, default seccomp, `--memory 768m --memory-swap 768m`, `--pids-limit`, `--cpus 1`, wall-clock kill at about 15 s). Upgrade to Kata/Firecracker only if threat or compliance requires a hardware boundary and KVM-capable hosts are available.
   - **Managed:** E2B (Firecracker), Cloudflare Sandbox (microVM), or Modal (gVisor/VM), with the network explicitly disabled at creation (all three default to outbound-on).
3. **L3, host hygiene.**
   - Patched kernel and runc (≥ the 2025 fixes); user-namespaced containers.
   - No cloud credentials or metadata access on sandbox nodes (block 169.254.169.254).
   - The sandbox worker talks to the API only over a narrow queue (code in, JSON out).
   - No Docker socket exposed to the API container.
4. **L4, lifecycle.**
   - One sandbox per run, or per learner session with destroy-on-idle. Never share across tenants.
   - A warm pool sized to p95 concurrency (OpenAI pattern), refilled asynchronously.
   - Run the image read-only so no state persists between runs.
5. **L5, data and observability.** Only synthetic or seeded inputs enter the sandbox, with no learner PII or source documents. Store the code, policy decision, resource usage, and outcome for audit. Re-run the escape test corpus (asteval-style `ndarray.ctypes`, `__subclasses__` walks, `Formatter`, `mrecords.openfile`, socket open, `/etc/passwd` and `$HOME` reads) in CI against the real sandbox backend.

### Gaps
- No measured cold-start or `import numpy` latency exists for any option on ClaimLab's hardware or target cloud. Benchmark before choosing the warm-pool size.
- The cost of a dedicated Linux VM for self-hosting (for example a small 2 vCPU/4 GB instance on a major cloud) was not researched.
- No primary source confirms AppContainer + CPython 3.12 + numpy works without extra capabilities; it needs a local spike.
- Cloud Run jobs, AWS Lambda, bubblewrap, minijail, and vendor DPAs/retention terms were not covered (see earlier sections).
