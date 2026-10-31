"""Sandbox for agent-written experiments: policy, isolation, and output validation."""
import os
import subprocess
import time

import pytest

from claimlab.sandbox import SandboxPolicyError, run_python_experiment, sandbox_environment, validate_code
from claimlab.sandbox import child, executor, policy

VALID = """
import numpy as np
rng = np.random.default_rng(params["seed"])
x = np.arange(params["steps"])
walk = np.cumsum(rng.normal(size=params["steps"]))
print("mean", float(walk.mean()))
result = {
    "summary": "A seeded random walk.",
    "metrics": {"final": walk[-1], "steps": np.int64(params["steps"]), "label": "walk", "bounded": np.bool_(True)},
    "chart": {"title": "Walk", "x_label": "step", "y_label": "value"},
    "series": [{"name": "walk", "x": x, "y": walk}],
    "table": {"columns": ["step", "value"], "rows": [[int(t), float(v)] for t, v in zip(x[:3], walk[:3])]},
    "checks": [{"name": "one value per step", "passed": len(walk) == params["steps"], "detail": "length"}],
}
"""


def test_valid_experiment_round_trips_output():
    first = run_python_experiment(VALID, {"seed": 7, "steps": 20})
    assert first.status == "succeeded", first.error
    output = first.output
    assert output.series[0].x == [float(step) for step in range(20)]
    assert len(output.series[0].y) == 20
    assert output.metrics["steps"] == 20 and output.metrics["label"] == "walk" and output.metrics["bounded"] is True
    assert output.table.rows[0][0] == 0
    assert output.checks[0].passed is True
    assert output.chart.title == "Walk"
    assert "mean" in first.stdout
    assert first.numpy_version and first.python_version
    again = run_python_experiment(VALID, {"seed": 7, "steps": 20})
    assert again.output == output


REJECTED = [
    "import os",
    "import subprocess",
    "from os import path",
    "x = open('notes.txt')",
    "x = eval('1')",
    "x = getattr(1, 'real')",
    "x = ().__class__.__bases__",
    "y = 1\nx = y._private",
    "x = 'a__b'",
    "import numpy as np\nx = np.load('f.npy')",
    "import numpy as np\nx = np.lib",
    "import numpy.ctypeslib",
    "from numpy import *",
    "from . import sibling",
    "with ctx:\n    pass",
    "class Model:\n    pass",
    "def walk():\n    yield 1\nframe = walk().gi_frame",
    "import operator\nget = operator.attrgetter('real')",
    "x = 1\n" * 2001,
    # numpy subpackages with file readers or host details (security review, 30 October)
    "import numpy.ma.mrecords as m\nf = m.openfile('C:/Windows/win.ini')",
    "from numpy.ma import mrecords",
    "import numpy as np\nx = np.ma",
    "import numpy as np\nx = np.rec.fromrecords([(1,)])",
    "import numpy.lib.npyio",
    "import numpy.char",
    "import numpy as np\nnp.show_config()",
]


@pytest.mark.parametrize("code", REJECTED)
def test_policy_rejects_before_any_process_starts(code, monkeypatch):
    def no_process(*args, **kwargs):
        raise AssertionError("rejected code must never start a process")

    monkeypatch.setattr(executor.subprocess, "Popen", no_process)
    result = run_python_experiment(code)
    assert result.status == "rejected"
    assert result.output is None
    with pytest.raises(SandboxPolicyError):
        validate_code(code)


def test_policy_names_the_first_violating_line():
    with pytest.raises(SandboxPolicyError, match=r"^Line 3: Import of 'os' is not allowed; available modules: .*numpy"):
        validate_code("import math\nx = math.pi\nimport os\nimport sys")


def test_common_idioms_pass_the_policy():
    validate_code("import numpy as np\nfrom collections import deque\nfor _ in range(3):\n    pass\n"
                  "try:\n    x = 1 / 0\nexcept ZeroDivisionError as error:\n    x = 0\nresult = {'summary': f'{x:.2f}'}")


def test_runtime_error_reports_type_and_line_without_host_paths():
    result = run_python_experiment("import numpy as np\nmatrix = np.zeros((2, 2))\ninverse = np.linalg.inv(matrix)")
    assert result.status == "failed"
    assert "LinAlgError" in result.error and "(line 3)" in result.error
    assert ":\\" not in result.error and "site-packages" not in result.error


def test_numpy_is_reachable_only_through_its_allowed_packages():
    # dtypes is not a blocked name, so only the runtime module guard stops this reference.
    hidden = run_python_experiment("import numpy as np\nhidden = np.dtypes\nresult = {}")
    assert hidden.status == "failed" and "numpy.dtypes" in hidden.error
    allowed = run_python_experiment(
        "import numpy as np\nfrom numpy.polynomial import Polynomial\nrng = np.random.default_rng(1)\n"
        "x = np.linspace(0, 1, 16)\nfit = Polynomial.fit(x, 2 * x + 1, 1)\n"
        "result = {'metrics': {'det': float(np.linalg.det(np.eye(2))), 'dc': float(np.fft.rfft(x)[0].real),"
        " 'draw': float(rng.random()), 'slope': float(fit.convert().coef[1])}}")
    assert allowed.status == "succeeded", allowed.error
    assert allowed.output.metrics["slope"] == pytest.approx(2.0)


def test_module_reexports_outside_the_allowlist_are_unreachable():
    result = run_python_experiment("import re\nhidden = re.enum\nresult = {}")
    assert result.status == "failed"
    assert "AttributeError" in result.error and "enum" in result.error


def test_non_finite_outputs_fail_with_a_clear_message():
    result = run_python_experiment("result = {'metrics': {'ratio': float('nan')}}")
    assert result.status == "failed"
    assert "finite" in result.error and "ratio" in result.error


def test_missing_result_tells_the_author_what_to_assign():
    result = run_python_experiment("x = 1")
    assert result.status == "failed"
    assert "assign `result`" in result.error


def test_output_contract_is_enforced_by_the_parent():
    result = run_python_experiment("result = {'series': [{'name': 'a', 'x': [1, 2], 'y': [1]}]}")
    assert result.status == "failed"
    assert "x values" in result.error


def test_infinite_loop_times_out():
    started = time.monotonic()
    result = run_python_experiment("while True:\n    pass", timeout_s=2)
    assert result.status == "timeout"
    assert time.monotonic() - started < 6
    assert "2 s time limit" in result.error


def test_memory_limit_is_enforced():
    # 800 MB would succeed without the limit on any development machine.
    result = run_python_experiment(
        "import numpy as np\nlarge = np.ones(100_000_000)\nresult = {'metrics': {'first': float(large[0])}}",
        memory_mb=512,
    )
    assert result.status == "failed"
    assert "MemoryError" in result.error
    bomb = run_python_experiment("import numpy as np\nlarge = np.ones(4_000_000_000)", memory_mb=256)
    assert bomb.status == "failed"


def test_child_environment_excludes_secrets(monkeypatch):
    for key in ("META_API_KEY", "TINYFISH_API_KEY", "SESSION_SECRET"):
        monkeypatch.setenv(key, "sekrit-value")
    seen = {}
    real_popen = subprocess.Popen

    def spy(*args, **kwargs):
        seen.update(kwargs.get("env") or {})
        return real_popen(*args, **kwargs)

    monkeypatch.setattr(executor.subprocess, "Popen", spy)
    result = run_python_experiment("result = {'summary': 'ok'}")
    assert result.status == "succeeded", result.error
    assert seen and not {"META_API_KEY", "TINYFISH_API_KEY", "SESSION_SECRET"} & set(seen)
    assert "sekrit-value" not in "".join(seen.values())


def test_parameters_must_be_plain_bounded_values():
    assert run_python_experiment("result = {}", {"nested": [[1]]}).status == "rejected"
    assert run_python_experiment("result = {}", {"_hidden": 1}).status == "rejected"
    assert run_python_experiment("result = {}", {"ratio": float("inf")}).status == "rejected"


def test_child_import_guard_wraps_modules():
    guard = child.make_guarded_import(policy)
    np = guard("numpy")
    assert int(np.array([1, 2]).sum()) == 3
    for name, kwargs in (("os", {}), ("numpy.ctypeslib", {}), ("numpy._core", {}), ("numpy", {"fromlist": ("load",)})):
        with pytest.raises(ImportError):
            guard(name, **kwargs)
    with pytest.raises(ImportError):
        guard("numpy", level=1)
    with pytest.raises(AttributeError):
        np.lib
    with pytest.raises(AttributeError):
        guard("re").enum
    with pytest.raises(AttributeError):
        np.injected = 1
    # C-level lazy imports (list fromlist) may load internals of allowed packages only.
    assert guard("numpy._core._methods", None, None, [], 0) is None
    with pytest.raises(ImportError):
        guard("os", None, None, [], 0)


def test_environment_reports_interpreter():
    info = sandbox_environment()
    assert info["environment"] in ("sandbox-venv", "app-venv-fallback")
    assert os.path.isfile(info["interpreter"])


@pytest.mark.skipif(os.name != "nt", reason="Windows job object")
def test_windows_job_object_blocks_child_processes(tmp_path):
    info = sandbox_environment()
    probe = (
        "import subprocess\n"
        "try:\n"
        "    subprocess.run(['cmd', '/c', 'exit 0'], check=True)\n"
        "    print('SPAWNED')\n"
        "except OSError as exc:\n"
        "    print('BLOCKED', exc.winerror)\n"
    )
    stdout, _, timed_out = executor._launch(
        [info["interpreter"], "-I", "-S", "-c", probe], b"", executor._scrubbed_env(str(tmp_path)),
        str(tmp_path), 20, 256,
    )
    assert not timed_out
    assert b"BLOCKED" in stdout and b"SPAWNED" not in stdout
