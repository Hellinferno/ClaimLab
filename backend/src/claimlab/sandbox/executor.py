"""Launches agent-written experiments in an isolated interpreter and validates their output.

Isolation layers: the static policy (checked here and again in the child),
restricted builtins with a guarded importer, a dedicated numpy-only venv, a
scrubbed environment and throwaway working directory, and OS limits — a
Windows job object (memory, one process, kill on close) or POSIX rlimits.
"""
import contextlib
import json
import logging
import math
import os
import platform
import re
import shutil
import signal
import subprocess
import sys
import sysconfig
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple

from pydantic import ValidationError

from claimlab.config import settings
from claimlab.sandbox.policy import SandboxPolicyError, validate_code
from claimlab.sandbox.schema import RESULT_KEYS, SandboxOutput

logger = logging.getLogger(__name__)

SENTINEL = "<<CLAIMLAB_RESULT>>"
PACKAGE_DIR = Path(__file__).resolve().parent
MAX_STDOUT_BYTES = 1024 * 1024
MAX_PARAMS = 32
CREATE_SUSPENDED = 0x00000004
CREATE_NO_WINDOW = 0x08000000
WINDOWS_PATH = re.compile(r"[A-Za-z]:\\[^\s'\"<>|]*")
POSIX_PATH = re.compile(r"(?<![\w.])/(?:[\w.+-]+/)+[\w.+-]*")


@dataclass
class SandboxResult:
    status: Literal["succeeded", "failed", "rejected", "timeout"]
    output: Optional[SandboxOutput]
    stdout: str
    error: Optional[str]
    duration_ms: int
    environment: str
    python_version: str
    numpy_version: Optional[str]


class IsolationError(RuntimeError):
    """The OS confinement could not be applied, so the experiment must not run."""


def _read_pyvenv(venv: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for line in (venv / "pyvenv.cfg").read_text(encoding="utf-8").splitlines():
        key, sep, value = line.partition("=")
        if sep:
            values[key.strip().lower()] = value.strip()
    return values


def _venv_site_packages(venv: Path) -> Optional[Path]:
    candidates = [venv / "Lib" / "site-packages"] if os.name == "nt" else sorted(venv.glob("lib/python3*/site-packages"))
    return next((path for path in candidates if path.is_dir()), None)


def _is_venv_interpreter(path: Path) -> bool:
    return (path.parent / "pyvenv.cfg").is_file() or (path.parent.parent / "pyvenv.cfg").is_file()


def _base_interpreter(config: Dict[str, str]) -> Optional[Path]:
    """The venv's base interpreter.

    On Windows a venv's python.exe is a launcher that spawns a second process,
    which the one-process job limit refuses; a venv created from inside another
    venv even records that launcher as `executable`. Only a real base interpreter qualifies.
    """
    home = config.get("home")
    names = ("python.exe",) if os.name == "nt" else ("python3", "python")
    candidates = [Path(home) / name for name in names] if home else []
    if config.get("executable"):
        candidates.append(Path(config["executable"]))
    return next((path for path in candidates if path.is_file() and not _is_venv_interpreter(path)), None)


def sandbox_environment() -> Dict[str, Any]:
    """Which interpreter and packages an experiment will run with."""
    venv = Path(settings.SANDBOX_VENV_DIR).resolve()
    info: Dict[str, Any] = {
        "venv_dir": str(venv),
        "venv_exists": (venv / "pyvenv.cfg").is_file(),
        "isolation": "windows-job-object" if os.name == "nt" else "posix-rlimits",
    }
    if info["venv_exists"]:
        config = _read_pyvenv(venv)
        site_packages = _venv_site_packages(venv)
        interpreter = _base_interpreter(config)
        if site_packages and interpreter and (site_packages / "numpy").is_dir():
            version = config.get("version_info") or config.get("version") or ""
            info.update(
                environment="sandbox-venv", interpreter=str(interpreter), site_packages=str(site_packages),
                python_version=".".join(version.split(".")[:3]),
            )
            return info
    fallbacks = [Path(getattr(sys, "_base_executable", None) or sys.executable),
                 Path(sys.base_prefix) / ("python.exe" if os.name == "nt" else "bin/python3")]
    info.update(
        environment="app-venv-fallback",
        interpreter=str(next((path for path in fallbacks if path.is_file() and not _is_venv_interpreter(path)), fallbacks[0])),
        site_packages=sysconfig.get_paths()["purelib"],
        python_version=platform.python_version(),
    )
    return info


_warned_fallback = False


def _warn_fallback(info: Dict[str, Any]) -> None:
    global _warned_fallback
    if not _warned_fallback:
        _warned_fallback = True
        logger.warning(
            "Experiment sandbox venv is not ready at %s; using the application interpreter's packages. "
            "Run `python -m claimlab.scripts.setup_sandbox` to create it.", info["venv_dir"],
        )


def _clean_params(params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Run parameters are plain bounded values; anything else is a policy violation."""
    if params is None:
        return {}
    if not isinstance(params, dict) or len(params) > MAX_PARAMS:
        raise SandboxPolicyError(f"Parameters must be a dict with at most {MAX_PARAMS} entries")
    clean: Dict[str, Any] = {}
    for key, value in params.items():
        if not isinstance(key, str) or not key.isidentifier() or key.startswith("_") or len(key) > 40:
            raise SandboxPolicyError(f"Parameter name {key!r} must be a short identifier not starting with '_'")
        clean[key] = _clean_value(key, value)
    return clean


def _clean_value(key: str, value: Any) -> Any:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise SandboxPolicyError(f"Parameter '{key}' must be a finite number")
        return value
    if isinstance(value, str):
        if len(value) > 200:
            raise SandboxPolicyError(f"Parameter '{key}' is longer than 200 characters")
        return value
    if isinstance(value, (list, tuple)) and len(value) <= 1000 and not any(isinstance(item, (list, tuple, dict)) for item in value):
        return [_clean_value(key, item) for item in value]
    raise SandboxPolicyError(f"Parameter '{key}' must be a number, text, boolean, or a flat list of those (up to 1000)")


def _scrubbed_env(workdir: str) -> Dict[str, str]:
    """Only what the interpreter needs; secrets such as API keys never reach the child."""
    env = {
        "TEMP": workdir, "TMP": workdir, "TMPDIR": workdir,
        "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
    }
    if os.name == "nt":
        root = os.environ.get("SYSTEMROOT") or os.environ.get("WINDIR") or r"C:\Windows"
        env.update(SYSTEMROOT=root, WINDIR=root, PATH=os.path.join(root, "System32"))
    else:
        env["PATH"] = "/usr/bin:/bin"
    return env


class _WindowsJob:
    """A job object confining one process: memory cap, no child processes, killed when closed."""

    LIMIT_ACTIVE_PROCESS = 0x00000008
    LIMIT_PROCESS_MEMORY = 0x00000100
    LIMIT_DIE_ON_UNHANDLED_EXCEPTION = 0x00000400
    LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
    EXTENDED_LIMIT_INFORMATION = 9
    BASIC_UI_RESTRICTIONS = 4
    UILIMIT_ALL = 0x000000FF

    def __init__(self, memory_mb: int):
        import ctypes
        from ctypes import wintypes

        class IoCounters(ctypes.Structure):
            _fields_ = [(name, ctypes.c_ulonglong) for name in (
                "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

        class BasicLimits(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
                ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD), ("SchedulingClass", wintypes.DWORD),
            ]

        class ExtendedLimits(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", BasicLimits), ("IoInfo", IoCounters),
                ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t),
            ]

        self.ctypes = ctypes
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.ntdll = ctypes.WinDLL("ntdll")
        self.kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        self.kernel32.CreateJobObjectW.restype = wintypes.HANDLE
        self.kernel32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        self.kernel32.SetInformationJobObject.restype = wintypes.BOOL
        self.kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        self.kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
        self.kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel32.CloseHandle.restype = wintypes.BOOL
        self.ntdll.NtResumeProcess.argtypes = [wintypes.HANDLE]
        self.ntdll.NtResumeProcess.restype = ctypes.c_long

        self.handle = self.kernel32.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            limits = ExtendedLimits()
            limits.BasicLimitInformation.LimitFlags = (
                self.LIMIT_ACTIVE_PROCESS | self.LIMIT_PROCESS_MEMORY
                | self.LIMIT_DIE_ON_UNHANDLED_EXCEPTION | self.LIMIT_KILL_ON_JOB_CLOSE
            )
            limits.BasicLimitInformation.ActiveProcessLimit = 1
            limits.ProcessMemoryLimit = memory_mb * 1024 * 1024
            self._set(self.EXTENDED_LIMIT_INFORMATION, limits)
            self._set(self.BASIC_UI_RESTRICTIONS, wintypes.DWORD(self.UILIMIT_ALL))
        except OSError:
            self.close()
            raise

    def _set(self, info_class: int, value: Any) -> None:
        ctypes = self.ctypes
        if not self.kernel32.SetInformationJobObject(self.handle, info_class, ctypes.byref(value), ctypes.sizeof(value)):
            raise ctypes.WinError(ctypes.get_last_error())

    def confine_and_resume(self, process: subprocess.Popen) -> None:
        """Assign the suspended process to the job, then let it run."""
        ctypes = self.ctypes
        handle = int(process._handle)  # type: ignore[attr-defined]
        if not self.kernel32.AssignProcessToJobObject(self.handle, handle):
            raise ctypes.WinError(ctypes.get_last_error())
        status = self.ntdll.NtResumeProcess(handle)
        if status != 0:
            raise OSError(f"NtResumeProcess failed with status {status & 0xFFFFFFFF:#x}")

    def close(self) -> None:
        """Closing the last handle kills every process still in the job."""
        if self.handle:
            self.kernel32.CloseHandle(self.handle)
            self.handle = None


def _launch(argv: List[str], payload: bytes, env: Dict[str, str], cwd: str, timeout_s: float, memory_mb: int) -> Tuple[bytes, bytes, bool]:
    """Run the child confined by OS limits; returns (stdout, stderr, timed_out)."""
    if os.name == "nt":
        return _launch_windows(argv, payload, env, cwd, timeout_s, memory_mb)
    return _launch_posix(argv, payload, env, cwd, timeout_s)


def _launch_windows(argv: List[str], payload: bytes, env: Dict[str, str], cwd: str, timeout_s: float, memory_mb: int) -> Tuple[bytes, bytes, bool]:
    try:
        job = _WindowsJob(memory_mb)
    except OSError as exc:
        raise IsolationError(str(exc)) from exc
    try:
        process = subprocess.Popen(
            argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=cwd, env=env, creationflags=CREATE_SUSPENDED | CREATE_NO_WINDOW,
        )
        try:
            job.confine_and_resume(process)
        except OSError as exc:
            process.kill()
            process.communicate()
            raise IsolationError(str(exc)) from exc
        try:
            stdout, stderr = process.communicate(payload, timeout=timeout_s)
            return stdout, stderr, False
        except subprocess.TimeoutExpired:
            job.close()
            process.kill()
            stdout, stderr = process.communicate()
            return stdout, stderr, True
    finally:
        job.close()


def _launch_posix(argv: List[str], payload: bytes, env: Dict[str, str], cwd: str, timeout_s: float) -> Tuple[bytes, bytes, bool]:
    # The child lowers its own rlimits before reading code; no preexec_fn, which is unsafe with threads.
    process = subprocess.Popen(
        argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        cwd=cwd, env=env, start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(payload, timeout=timeout_s)
        return stdout, stderr, False
    except subprocess.TimeoutExpired:
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(process.pid, signal.SIGKILL)
        process.kill()
        stdout, stderr = process.communicate()
        return stdout, stderr, True


def _redact(text: Optional[str], extra: Tuple[str, ...] = ()) -> Optional[str]:
    if text is None:
        return None
    for path in sorted((p for p in extra if p), key=len, reverse=True):
        text = text.replace(path, "<sandbox>")
    return POSIX_PATH.sub("<path>", WINDOWS_PATH.sub("<path>", text))


def _parse_report(stdout: bytes) -> Optional[Dict[str, Any]]:
    if len(stdout) > MAX_STDOUT_BYTES:
        return None
    for line in reversed(stdout.decode("utf-8", errors="replace").splitlines()):
        if line.startswith(SENTINEL):
            try:
                report = json.loads(line[len(SENTINEL):])
            except json.JSONDecodeError:
                return None
            return report if isinstance(report, dict) else None
    return None


def _describe_validation(exc: ValidationError) -> str:
    error = exc.errors()[0]
    location = "result" + "".join(f"[{part!r}]" if isinstance(part, str) else f"[{part}]" for part in error["loc"])
    if error["type"] == "extra_forbidden":
        return f"{location} is not a supported field; allowed keys: {', '.join(RESULT_KEYS)}"
    return f"{location}: {error['msg']}"


def run_python_experiment(
    code: str,
    params: Optional[Dict[str, Any]] = None,
    *,
    timeout_s: Optional[float] = None,
    memory_mb: Optional[int] = None,
) -> SandboxResult:
    """Validate, run, and check one experiment. Bad experiment code never raises; it yields a status."""
    started = time.monotonic()
    info = sandbox_environment()
    timeout = float(timeout_s if timeout_s is not None else settings.SANDBOX_TIMEOUT_SECONDS)
    memory = int(memory_mb if memory_mb is not None else settings.SANDBOX_MEMORY_MB)
    redactions: Tuple[str, ...] = (info["site_packages"], info["venv_dir"])

    def finish(status: str, output: Optional[SandboxOutput] = None, stdout: str = "", error: Optional[str] = None,
               report: Optional[Dict[str, Any]] = None) -> SandboxResult:
        report = report or {}
        return SandboxResult(
            status=status,  # type: ignore[arg-type]
            output=output,
            stdout=(_redact(stdout, redactions) or "")[:4000],
            error=_redact(error, redactions)[:500] if error else None,
            duration_ms=int((time.monotonic() - started) * 1000),
            environment=info["environment"],
            python_version=str(report.get("python_version") or info["python_version"]),
            numpy_version=report.get("numpy_version"),
        )

    try:
        validate_code(code)
        clean_params = _clean_params(params)
    except SandboxPolicyError as exc:
        return finish("rejected", error=str(exc))
    if info["environment"] != "sandbox-venv":
        _warn_fallback(info)

    with tempfile.TemporaryDirectory(prefix="claimlab-sandbox-", ignore_cleanup_errors=True) as workdir:
        for name in ("child.py", "policy.py"):
            shutil.copyfile(PACKAGE_DIR / name, Path(workdir) / name)
        argv = [
            info["interpreter"], "-I", "-S", "-X", "utf8", str(Path(workdir) / "child.py"),
            info["site_packages"], str(memory), str(timeout),
        ]
        payload = json.dumps({"code": code, "params": clean_params}).encode("utf-8")
        redactions += (workdir,)
        try:
            stdout, stderr, timed_out = _launch(argv, payload, _scrubbed_env(workdir), workdir, timeout, memory)
        except IsolationError as exc:
            logger.error("Sandbox isolation failed: %s", exc)
            return finish("failed", error="Sandbox isolation could not be applied; the experiment did not run.")
        except OSError as exc:
            logger.error("Sandbox interpreter could not start: %s", exc)
            return finish("failed", error="The sandbox interpreter could not be started.")

    if timed_out:
        return finish("timeout", error=f"The experiment exceeded the {timeout:g} s time limit.")
    report = _parse_report(stdout)
    if report is None:
        lines = [line for line in stderr.decode("utf-8", errors="replace").splitlines() if line.strip()]
        detail = lines[-1].strip()[:300] if lines else ""
        return finish("failed", error="The experiment process ended without a result" + (f": {detail}" if detail else "."))
    captured = str(report.get("stdout") or "")
    if report.get("status") == "rejected":
        return finish("rejected", stdout=captured, error=str(report.get("error") or "Experiment code was rejected"), report=report)
    if report.get("status") != "succeeded":
        return finish("failed", stdout=captured, error=str(report.get("error") or "The experiment failed."), report=report)
    try:
        output = SandboxOutput.model_validate(report.get("output"))
    except ValidationError as exc:
        return finish("failed", stdout=captured, error=_describe_validation(exc), report=report)
    return finish("succeeded", output=output, stdout=captured, report=report)
