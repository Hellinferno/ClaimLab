"""Isolated Numerical Recipe Runner entrypoint reading JSON from stdin and writing JSON to stdout."""
import json
import sys
from claimlab.numerics.runner import runner


def main():
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            sys.stderr.write("Error: Empty input\n")
            sys.exit(1)

        payload = json.loads(raw_input)
        recipe_id = payload.get("recipe_id")
        parameters = payload.get("parameters", {})

        result = runner.run(recipe_id, parameters)
        sys.stdout.write(result.model_dump_json())
        sys.stdout.flush()
        sys.exit(0)

    except Exception as e:
        sys.stderr.write(f"Runner error: {str(e)}\n")
        sys.exit(2)


if __name__ == "__main__":
    main()
