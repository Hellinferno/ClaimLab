# Experiment Engine and Numerical Contracts

## Release boundary

Execute reviewed recipes selected and parameterized by the agent or student. The model can formulate the investigation and interpret checked output; it cannot submit arbitrary Python or shell code. Each run is an actual bounded computation with retained inputs and checks.

This supports the original idea's “produce or select an implementation” behavior through verified method templates. General code synthesis and full-paper reproduction remain future scope.

## Recipe A — `softmax_sensitivity_v1`

Inputs: `logits` of length 2–12, each finite in [-20, 20]; `multiplier` in [0.25, 4]; integer `seed` retained for uniform run metadata though this recipe is deterministic.

Compute stable softmax of the base logits and multiplied logits by subtracting the maximum before exponentiation. Return input/output arrays, maximum probability, and entropy in natural-log units (nats). Define zero-probability entropy terms by their limiting value zero.

Checks: probabilities finite and nonnegative; each vector sums to one; adding a common constant leaves the distribution unchanged within tolerance; equal logits produce equal weights; independent scalar/reference calculation agrees. Do not claim every parameter change makes entropy strictly different: equal logits are a counterexample.

## Recipe B — `attention_scaling_v1`

Inputs: `dimensions`, 1–4 unique integers in [1, 256]; `n_keys` in [2, 16]; `trials` in [20, 200]; `seed` integer in [0, 2^32 - 1]. Use a documented NumPy generator and record its version.

For each dimension, sample independent standard-normal query/key components. Within a trial, use the exact same sampled vectors for scaled and unscaled comparisons. Compute unscaled dot products, scores divided by the square root of the dimension, and stable softmax for both.

Return per-dimension aggregate score variance, mean entropy, representative first-trial scores/weights, trial count, and seed. Statistics describe the chosen synthetic distribution. Changing dimension generates a different dimensional sample under the same recorded seed policy; the UI must not imply an identical vector was preserved across dimensions.

Checks: shapes, finite outputs, normalized weights, and agreement with an independent implementation. For every computed entry, scaled score multiplied by the square root of dimension must agree with its unscaled counterpart within tolerance. Statistical trends are observations; they are not hard monotonicity invariants for every random seed.

## Recipe C — `causal_masking_v1`

Inputs: a square `scores` matrix of size 2–8 with finite values in [-20, 20]; `seed` retained for metadata. The supported mask includes the current position and all earlier positions: column j is allowed when j <= row i.

Compute row-wise stable softmax over allowed entries only. Forbidden future entries have weight zero. Every row has at least one allowed element. Return the original scores, boolean allowed-mask matrix, masked attention weights, and unmasked comparison weights.

Internally masked entries may use negative infinity; never emit NaN or Infinity in JSON. Return the boolean mask and finite weights rather than serializing non-finite logits.

Checks: row normalization, exact zeros at forbidden positions, preserved relative softmax among allowed entries, and independent reference agreement. With all-zero 3×3 scores, expected rows are [1,0,0], [0.5,0.5,0], and [1/3,1/3,1/3]. This illustrates masking, not a complete language-model training setup.

## Common run contract

Each run records recipe/version, canonical parameter hash, seed, runner image digest, numerical package version, start/end timestamps, status, output hash, check results, assumptions, and source context. Output JSON is at most 1 MiB.

Check records contain name, status (`passed`, `failed`, `not_applicable`), tolerance where relevant, and bounded detail. Use float64 calculations; default comparison tolerances are absolute 1e-10 and relative 1e-8 unless a particular check documents a reason to differ.

An exit code zero with a failed check is a failed validation, not a successful experiment. Keep diagnostic output inspectable without presenting it as established evidence. A deterministic recipe's seed may be `not_used` in displayed assumptions, while still remaining in metadata.

## Isolation

Use an immutable reviewed image, a non-root user, no network, read-only root filesystem, dropped Linux capabilities, default seccomp, no-new-privileges, no privileged/host namespaces, and bounded CPU/memory/processes. Pass validated JSON through stdin; return bounded JSON through stdout. Capture and cap stderr separately.

The runner receives no raw PDF, API key, application database, Docker socket, or host workspace mount. A small tmpfs can support library temporary files. Run with a fixed executable argument list; never construct shell commands from model or user text. Apply the same isolation to untrusted PDF parsing with its own allowed parser entry point.

The trusted worker may control the container runtime on a dedicated host; that is a privileged infrastructure boundary. Limit and isolate that worker, and never expose its control channel through agent tools.

## Failure and cancellation

Kill the runner process/container at the wall deadline, on cancellation, or after output limits are exceeded. Reap child resources and record the terminal state. Do not automatically rerun after a worker restart. A new explicit retry produces a new run ID linked to the prior failure.

## Scientific scope

Display a distinction among source statement, added assumption, synthetic observation, and interpretation. The source can motivate the question while the experiment investigates only a small mechanism. Claims about trained models, benchmark performance, or student learning need separate evidence.
