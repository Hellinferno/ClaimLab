"""Sandbox child: executes one agent-written experiment inside the parent's isolation.

Run as `python -I -S -X utf8 child.py <site-packages> <memory_mb> <timeout_s>` with a
copy of policy.py beside it. Stdlib and numpy only; it must never import claimlab.
The experiment arrives on stdin after start-up, so the parent can confine the
process before any experiment code exists inside it.
"""
import builtins
import contextlib
import io
import json
import math
import os
import sys
import traceback
import types
from decimal import Decimal
from fractions import Fraction
from typing import Any, Callable, Dict, List, Optional

SENTINEL = "<<CLAIMLAB_RESULT>>"
FILENAME = "<experiment>"
MAX_INPUT_BYTES = 256 * 1024
MAX_CAPTURE_CHARS = 4000
MAX_RESULT_CHARS = 256 * 1024
MAX_ELEMENTS = 100_000
RESULT_KEYS = ("summary", "metrics", "chart", "series", "table", "checks")

SAFE_BUILTINS = (
    "abs", "all", "any", "bool", "dict", "enumerate", "filter", "float", "int", "len", "list", "map", "max",
    "min", "pow", "range", "reversed", "round", "set", "sorted", "str", "sum", "tuple", "zip", "isinstance",
    "issubclass", "divmod", "iter", "next", "slice", "frozenset", "complex", "hash", "repr", "format", "chr",
    "ord", "bin", "hex", "oct", "callable",
)
SAFE_EXCEPTIONS = (
    "Exception", "ValueError", "TypeError", "ZeroDivisionError", "ArithmeticError", "IndexError", "KeyError",
    "RuntimeError", "StopIteration", "AssertionError", "OverflowError", "NotImplementedError", "AttributeError",
    "NameError", "LookupError", "FloatingPointError", "MemoryError", "RecursionError", "ImportError",
    "Warning", "RuntimeWarning", "UserWarning",
)

REDACTIONS: List[str] = []


class ResultError(ValueError):
    """The experiment's `result` does not satisfy the output contract."""


class CappedBuffer(io.StringIO):
    """Captures print and warning output, silently dropping text beyond the cap."""

    def __init__(self, limit: int):
        super().__init__()
        self.limit = limit
        self.size = 0

    def write(self, text: str) -> int:
        room = self.limit - self.size
        if room > 0:
            chunk = str(text)[:room]
            self.size += len(chunk)
            super().write(chunk)
        return len(text)


def make_module_view(policy: Any) -> type:
    """Read-only module proxies: attributes holding modules off the allowlist are unreachable."""

    class ModuleView:
        __slots__ = ("_target",)

        def __init__(self, module: types.ModuleType):
            object.__setattr__(self, "_target", module)

        def __getattr__(self, name: str) -> Any:
            if name.startswith("_") or name in policy.BLOCKED_ATTRIBUTES:
                raise AttributeError(f"'{name}' is not available in experiments")
            value = getattr(object.__getattribute__(self, "_target"), name)
            if isinstance(value, types.ModuleType):
                if not policy.module_allowed(value.__name__):
                    raise AttributeError(f"Module '{value.__name__}' is not available in experiments")
                return ModuleView(value)
            return value

        def __setattr__(self, name: str, value: Any) -> None:
            raise AttributeError("Modules are read-only in experiments")

        def __delattr__(self, name: str) -> None:
            raise AttributeError("Modules are read-only in experiments")

        def __repr__(self) -> str:
            return f"<module '{object.__getattribute__(self, '_target').__name__}'>"

    return ModuleView


def make_guarded_import(policy: Any, real_import: Callable[..., Any] = builtins.__import__) -> Callable[..., Any]:
    view = make_module_view(policy)

    def guarded_import(name: str, globals: Any = None, locals: Any = None, fromlist: Any = (), level: int = 0) -> Any:
        if level:
            raise ImportError("Relative imports are not allowed in experiments")
        if isinstance(fromlist, list):
            # C-level PyImport_Import (numpy's lazy internals, e.g. numpy._core._methods) passes a list
            # and discards the return value; import statements pass None or a tuple and are checked fully.
            if name.split(".")[0] not in policy.ALLOWED_MODULES:
                raise ImportError(f"Import of '{name}' is not allowed in experiments")
            real_import(name, None, None, fromlist, 0)
            return None
        if not policy.module_allowed(name):
            raise ImportError(f"Import of '{name}' is not allowed; available modules: {policy.AVAILABLE}")
        for item in fromlist or ():
            if not policy.name_allowed(item):
                raise ImportError(f"Importing '{item}' from '{name}' is not allowed")
        return view(real_import(name, None, None, tuple(fromlist or ()), 0))

    return guarded_import


def build_builtins(policy: Any, capture: CappedBuffer) -> Dict[str, Any]:
    safe = {name: getattr(builtins, name) for name in SAFE_BUILTINS + SAFE_EXCEPTIONS}

    def safe_print(*args: Any, sep: Optional[str] = " ", end: Optional[str] = "\n", file: Any = None, flush: bool = False) -> None:
        capture.write((" " if sep is None else str(sep)).join(str(arg) for arg in args) + ("\n" if end is None else str(end)))

    safe["print"] = safe_print
    safe["__import__"] = make_guarded_import(policy)
    return safe


def redact(text: str) -> str:
    for path in sorted(REDACTIONS, key=len, reverse=True):
        text = text.replace(path, "<sandbox>")
    return text


def to_jsonable(value: Any, path: str, numpy_module: Any, depth: int = 0) -> Any:
    if depth > 6:
        raise ResultError(f"{path} is nested too deeply")
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ResultError(f"{path} is {value}; experiment outputs must be finite numbers")
        return value
    if isinstance(value, (Fraction, Decimal)):
        return to_jsonable(float(value), path, numpy_module, depth)
    if numpy_module is not None and isinstance(value, numpy_module.ndarray):
        if value.size > MAX_ELEMENTS:
            raise ResultError(f"{path} has {value.size} elements; keep outputs small (series up to 500 points)")
        return to_jsonable(value.tolist(), path, numpy_module, depth)
    if numpy_module is not None and isinstance(value, numpy_module.generic):
        return to_jsonable(value.item(), path, numpy_module, depth)
    if isinstance(value, dict):
        if len(value) > MAX_ELEMENTS:
            raise ResultError(f"{path} has too many entries")
        return {str(key): to_jsonable(item, f"{path}[{str(key)!r}]", numpy_module, depth + 1) for key, item in value.items()}
    if isinstance(value, (list, tuple, range)):
        if len(value) > MAX_ELEMENTS:
            raise ResultError(f"{path} has {len(value)} elements; keep outputs small (series up to 500 points)")
        return [to_jsonable(item, f"{path}[{index}]", numpy_module, depth + 1) for index, item in enumerate(value)]
    raise ResultError(f"{path} has unsupported type {type(value).__name__}; use numbers, text, lists, and dicts")


def collect_result(namespace: Dict[str, Any], numpy_module: Any) -> Dict[str, Any]:
    if "result" not in namespace:
        raise ResultError(
            "The experiment did not assign `result`. End the code with result = {...} "
            f"using the keys: {', '.join(RESULT_KEYS)}"
        )
    result = namespace["result"]
    if not isinstance(result, dict):
        raise ResultError(f"`result` must be a dict, not {type(result).__name__}")
    unknown = [str(key) for key in result if key not in RESULT_KEYS]
    if unknown:
        raise ResultError(f"`result` has unsupported key(s) {', '.join(unknown)}; allowed keys: {', '.join(RESULT_KEYS)}")
    output = to_jsonable(result, "result", numpy_module)
    if len(json.dumps(output, allow_nan=False)) > MAX_RESULT_CHARS:
        raise ResultError("`result` is too large; keep series to 500 points and tables to 50 rows")
    return output


def describe_error(exc: BaseException) -> str:
    if isinstance(exc, ResultError):
        return redact(str(exc))[:500]
    frames = [frame for frame in traceback.extract_tb(exc.__traceback__) if frame.filename == FILENAME]
    message = str(exc)
    text = f"{type(exc).__name__}: {message}" if message else type(exc).__name__
    if frames:
        text += f" (line {frames[-1].lineno})"
    return redact(text)[:500]


def execute(code: str, params: Dict[str, Any], policy: Any, numpy_module: Any = None) -> Dict[str, Any]:
    """Re-check the policy, then run the code against restricted builtins and capture its result."""
    try:
        policy.validate_code(code)
    except policy.SandboxPolicyError as exc:
        return {"status": "rejected", "output": None, "stdout": "", "error": str(exc)}
    capture = CappedBuffer(MAX_CAPTURE_CHARS)
    namespace: Dict[str, Any] = {"__builtins__": build_builtins(policy, capture), "__name__": "experiment", "params": dict(params)}
    try:
        compiled = compile(code, FILENAME, "exec")
        with contextlib.redirect_stdout(capture), contextlib.redirect_stderr(capture):
            exec(compiled, namespace)
        output, status, error = collect_result(namespace, numpy_module), "succeeded", None
    except BaseException as exc:  # the experiment's failure is the report, never the child's
        output, status, error = None, "failed", describe_error(exc)
    return {"status": status, "output": output, "stdout": redact(capture.getvalue()), "error": error}


def lower_limit(resource: Any, kind: int, value: int) -> None:
    _, hard = resource.getrlimit(kind)
    if hard != resource.RLIM_INFINITY:
        value = min(value, hard)
    resource.setrlimit(kind, (value, value))


def apply_posix_limits(memory_mb: int, timeout_s: float) -> None:
    """Lower this process's own limits before any experiment code is read (POSIX only)."""
    try:
        import resource
    except ImportError:
        return  # Windows: the parent's job object enforces memory and process limits
    memory = memory_mb * 1024 * 1024
    # Linux counts private mappings in RLIMIT_DATA; RLIMIT_AS would also count BLAS address reservations.
    lower_limit(resource, resource.RLIMIT_DATA if sys.platform.startswith("linux") else resource.RLIMIT_AS, memory)
    lower_limit(resource, resource.RLIMIT_CPU, int(math.ceil(timeout_s)) + 1)
    lower_limit(resource, resource.RLIMIT_FSIZE, 1 << 20)
    with contextlib.suppress(ValueError, OSError, AttributeError):
        lower_limit(resource, resource.RLIMIT_NPROC, 0)


def main() -> int:
    real_stdout = sys.stdout
    site_packages, memory_mb, timeout_s = sys.argv[1], int(sys.argv[2]), float(sys.argv[3])
    apply_posix_limits(memory_mb, timeout_s)
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, here)
    import policy
    sys.path.remove(here)
    if site_packages:
        sys.path.append(site_packages)
    REDACTIONS.extend(path for path in {here, site_packages, sys.base_prefix, sys.prefix} if path)
    try:
        import numpy
    except Exception:
        numpy = None
    report: Dict[str, Any]
    try:
        raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        if len(raw) > MAX_INPUT_BYTES:
            raise ValueError("experiment request is too large")
        message = json.loads(raw.decode("utf-8"))
        report = execute(str(message.get("code", "")), dict(message.get("params") or {}), policy, numpy)
        json.dumps(report, allow_nan=False)
    except Exception as exc:
        report = {"status": "failed", "output": None, "stdout": "", "error": f"Sandbox protocol error: {type(exc).__name__}"}
    report["numpy_version"] = numpy.__version__ if numpy is not None else None
    report["python_version"] = sys.version.split()[0]
    encoded = json.dumps(report, allow_nan=False)
    real_stdout.write(SENTINEL + encoded + "\n")
    real_stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
