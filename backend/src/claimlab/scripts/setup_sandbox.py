"""Create the dedicated experiment sandbox venv (numpy only) and run a smoke experiment.

Usage, from the repository root: python -m claimlab.scripts.setup_sandbox
Idempotent: an existing venv is reused and numpy is pinned to the application's version.
"""
import json
import os
import subprocess
import sys
import venv
from pathlib import Path

import numpy as np

from claimlab.config import settings
from claimlab.sandbox import run_python_experiment, sandbox_environment

SMOKE_EXPERIMENT = """
import numpy as np
rng = np.random.default_rng(params["seed"])
walk = np.cumsum(rng.normal(size=params["steps"]))
result = {
    "summary": "Smoke test: a seeded random walk.",
    "metrics": {"final_value": walk[-1], "steps": params["steps"]},
    "series": [{"name": "walk", "y": walk}],
    "checks": [{"name": "one value per step", "passed": len(walk) == params["steps"]}],
}
"""


def main() -> int:
    venv_dir = Path(settings.SANDBOX_VENV_DIR).resolve()
    if not (venv_dir / "pyvenv.cfg").is_file():
        print(f"Creating sandbox venv at {venv_dir}")
        venv.EnvBuilder(with_pip=True, clear=False).create(venv_dir)
    python = venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    requirement = f"numpy=={np.__version__}"
    print(f"Installing {requirement} into the sandbox venv")
    subprocess.run(
        [str(python), "-m", "pip", "install", "--disable-pip-version-check", "--quiet", requirement],
        check=True,
    )
    print(json.dumps(sandbox_environment(), indent=2))
    result = run_python_experiment(SMOKE_EXPERIMENT, {"seed": 7, "steps": 50})
    print(f"Smoke experiment: {result.status} in {result.duration_ms} ms "
          f"(environment={result.environment}, python={result.python_version}, numpy={result.numpy_version})")
    if result.error:
        print(f"Error: {result.error}")
    return 0 if result.status == "succeeded" and result.environment == "sandbox-venv" else 1


if __name__ == "__main__":
    sys.exit(main())
