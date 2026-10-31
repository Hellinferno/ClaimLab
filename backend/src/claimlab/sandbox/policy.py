"""Static policy for agent-written experiment code.

Stdlib only: the sandbox child process loads this same file to re-check code
before executing it, so it must not import claimlab or third-party packages.
"""
import ast
from typing import List, Optional, Tuple

MAX_CODE_CHARS = 12000

ALLOWED_MODULES = frozenset({
    "numpy", "math", "cmath", "statistics", "random", "itertools", "functools", "collections",
    "fractions", "decimal", "bisect", "heapq", "operator", "json", "re", "string",
})

# numpy is reachable only through these packages and their submodules. Its other subpackages
# hold file readers under unlisted names (numpy.ma.mrecords.openfile opened any path), so they
# are allowed by name rather than blocked by name.
NUMPY_PACKAGES = ("numpy.random", "numpy.linalg", "numpy.fft", "numpy.polynomial")

BLOCKED_NAMES = frozenset({
    "open", "exec", "eval", "compile", "__import__", "getattr", "setattr", "delattr", "globals", "locals",
    "vars", "input", "breakpoint", "help", "exit", "quit", "memoryview", "super", "classmethod",
    "staticmethod", "property",
})

BLOCKED_ATTRIBUTES = frozenset({
    # numpy file I/O, pickle, native-code bridges, and test runners
    "load", "save", "savez", "savez_compressed", "savetxt", "loadtxt", "genfromtxt", "fromfile", "tofile",
    "fromregex", "memmap", "open_memmap", "ctypeslib", "f2py", "distutils", "testing", "lib", "dump",
    "DataSource", "ctypes", "system", "popen", "test", "openfile", "fromtextfile",
    # numpy subpackages outside NUMPY_PACKAGES, and host configuration reports
    "ma", "mrecords", "rec", "records", "char", "strings", "core", "typing", "emath", "matlib",
    "show_config", "show_runtime", "info", "get_include",
    # attribute lookup by a runtime string
    "attrgetter", "methodcaller", "Formatter", "get_field", "vformat",
    # frame and code objects reachable from generators and tracebacks
    "gi_frame", "gi_code", "gi_yieldfrom", "cr_frame", "cr_code", "cr_await", "ag_frame", "ag_code",
    "ag_await", "f_back", "f_globals", "f_locals", "f_builtins", "f_code", "f_trace", "tb_frame", "tb_next",
    # modules that allowed modules re-export
    "sys", "os", "builtins", "importlib", "subprocess", "shutil", "socket", "pathlib", "io", "posix", "nt",
    "multiprocessing", "threading", "inspect", "gc", "marshal", "pickle", "pty", "pdb", "runpy", "tempfile",
    "glob", "urllib", "http", "mmap", "resource", "sysconfig", "site", "linecache",
})

AVAILABLE = ", ".join(sorted(ALLOWED_MODULES)) + " (numpy as numpy, numpy.random, numpy.linalg, numpy.fft, numpy.polynomial)"


class SandboxPolicyError(ValueError):
    """Experiment code violates the sandbox policy; the message is safe to show the author."""


def is_private(name: Optional[str]) -> bool:
    """Leading-underscore names reach dunders and internals; a bare '_' is a harmless placeholder."""
    return bool(name) and name.startswith("_") and name != "_"


def module_allowed(name: str) -> bool:
    parts = name.split(".") if name else [""]
    if parts[0] not in ALLOWED_MODULES or any(not part or part.startswith("_") for part in parts):
        return False
    if parts[0] == "numpy" and name != "numpy" and not any(name == p or name.startswith(p + ".") for p in NUMPY_PACKAGES):
        return False
    return not any(part in BLOCKED_ATTRIBUTES for part in parts[1:])


def name_allowed(name: str) -> bool:
    """Whether `from module import name` may bind this name."""
    return name != "*" and not is_private(name) and name not in BLOCKED_ATTRIBUTES and name not in BLOCKED_NAMES


def _violation(node: ast.AST) -> Optional[str]:
    if isinstance(node, ast.Import):
        for alias in node.names:
            if not module_allowed(alias.name):
                return f"Import of '{alias.name}' is not allowed; available modules: {AVAILABLE}"
            if is_private(alias.asname):
                return f"Alias '{alias.asname}' must not start with '_'"
    elif isinstance(node, ast.ImportFrom):
        if node.level:
            return "Relative imports are not allowed"
        if not node.module or not module_allowed(node.module):
            return f"Import from '{node.module}' is not allowed; available modules: {AVAILABLE}"
        for alias in node.names:
            if alias.name == "*":
                return "Star imports are not allowed; import the names you use"
            if not name_allowed(alias.name):
                return f"Importing '{alias.name}' from '{node.module}' is not allowed"
            if is_private(alias.asname):
                return f"Alias '{alias.asname}' must not start with '_'"
    elif isinstance(node, ast.Name):
        if is_private(node.id):
            return f"Names starting with '_' are not allowed ('{node.id}')"
        if node.id in BLOCKED_NAMES:
            return f"'{node.id}' is not available in experiments"
    elif isinstance(node, ast.Attribute):
        if is_private(node.attr):
            return f"Attribute '.{node.attr}' is not allowed (names starting with '_' are blocked)"
        if node.attr in BLOCKED_ATTRIBUTES:
            return f"Attribute '.{node.attr}' is not allowed (file, process, or introspection access)"
    elif isinstance(node, ast.ClassDef):
        return "Class definitions are not supported; use functions, dicts, and lists"
    elif isinstance(node, (ast.AsyncFunctionDef, ast.AsyncFor, ast.AsyncWith, ast.Await)):
        return "Async code is not supported in experiments"
    elif isinstance(node, ast.With):
        return "'with' statements are not supported; use np.seterr(...) or np.where(...) to handle numeric warnings"
    elif isinstance(node, ast.Match):
        return "'match' statements are not supported in experiments"
    elif isinstance(node, (ast.FunctionDef, ast.Lambda)):
        name = getattr(node, "name", None)
        if is_private(name):
            return f"Function names must not start with '_' ('{name}')"
    elif isinstance(node, ast.arg):
        if is_private(node.arg):
            return f"Parameter names must not start with '_' ('{node.arg}')"
    elif isinstance(node, ast.ExceptHandler):
        if is_private(node.name):
            return f"Names starting with '_' are not allowed ('{node.name}')"
    elif isinstance(node, ast.keyword):
        if is_private(node.arg):
            return f"Keyword names must not start with '_' ('{node.arg}')"
    elif isinstance(node, (ast.Global, ast.Nonlocal)):
        for name in node.names:
            if is_private(name):
                return f"Names starting with '_' are not allowed ('{name}')"
    elif isinstance(node, ast.Constant):
        if isinstance(node.value, str) and "__" in node.value:
            return "Text containing '__' is not allowed"
        if isinstance(node.value, bytes) and b"__" in node.value:
            return "Bytes containing '__' are not allowed"
    return None


def validate_code(code: str) -> None:
    """Raise SandboxPolicyError naming the first violation (by line) in the experiment code."""
    if not isinstance(code, str) or not code.strip():
        raise SandboxPolicyError("Experiment code is empty")
    if len(code) > MAX_CODE_CHARS:
        raise SandboxPolicyError(f"Experiment code is {len(code)} characters; the limit is {MAX_CODE_CHARS}")
    try:
        tree = ast.parse(code, filename="<experiment>", mode="exec")
    except SyntaxError as exc:
        raise SandboxPolicyError(f"Line {exc.lineno or 1}: syntax error: {exc.msg}") from None
    except ValueError as exc:
        raise SandboxPolicyError(f"Experiment code could not be parsed: {exc}") from None
    found: List[Tuple[int, int, str]] = []
    for node in ast.walk(tree):
        message = _violation(node)
        if message:
            found.append((getattr(node, "lineno", 1), getattr(node, "col_offset", 0), message))
    if found:
        line, _, message = min(found)
        raise SandboxPolicyError(f"Line {line}: {message}")
