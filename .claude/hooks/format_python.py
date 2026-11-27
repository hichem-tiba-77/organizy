"""Claude Code PostToolUse hook: format + lint a Python file right after it's edited.

Claude Code pipes a JSON payload on stdin, e.g.
  {"tool_name": "Edit", "tool_input": {"file_path": ".../backend/app/main.py", ...}}

- Not a backend .py file -> exit 0, do nothing.
- Runs `ruff check --fix` then `black` on that one file (config from backend/pyproject.toml).
- If ruff still reports problems it can't auto-fix -> exit 2 with the report on
  stderr: Claude Code feeds stderr back to Claude, which then fixes the code.
"""

import json
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2] / "backend"


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    file_path = (payload.get("tool_input") or {}).get("file_path")
    if not file_path:
        return 0

    path = Path(file_path).resolve()
    if path.suffix != ".py" or not path.is_file() or BACKEND not in path.parents:
        return 0

    def run(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["uv", "run", "--quiet", *args, str(path)],
            cwd=BACKEND,
            capture_output=True,
            text=True,
        )

    lint = run("ruff", "check", "--fix", "--quiet")
    run("black", "--quiet")  # black after ruff: ruff's fixes get formatted too
    if lint.returncode != 0:
        print(
            f"ruff found issues in {path.name}:\n{lint.stdout}{lint.stderr}",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
