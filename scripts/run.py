from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _venv_paths(venv_dir: Path) -> tuple[Path, Path]:
    if sys.platform == "win32":
        python_path = venv_dir / "Scripts" / "python.exe"
        pip_path = venv_dir / "Scripts" / "pip.exe"
    else:
        python_path = venv_dir / "bin" / "python"
        pip_path = venv_dir / "bin" / "pip"
    return python_path, pip_path


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    venv_dir = project_root / ".venv"
    requirements = project_root / "requirements.txt"
    install_stamp = venv_dir / ".deps-installed"

    if not venv_dir.exists():
        subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)])

    venv_python, venv_pip = _venv_paths(venv_dir)
    if not venv_python.exists():
        raise SystemExit("Virtual environment missing python interpreter.")

    if requirements.exists():
        needs_install = not install_stamp.exists() or requirements.stat().st_mtime > install_stamp.stat().st_mtime
        if needs_install:
            subprocess.check_call(
                [
                    str(venv_pip),
                    "install",
                    "--disable-pip-version-check",
                    "-r",
                    str(requirements),
                ]
            )
            install_stamp.touch()

    env = os.environ.copy()
    src_path = str(project_root / "src")
    if env.get("PYTHONPATH"):
        env["PYTHONPATH"] = src_path + os.pathsep + env["PYTHONPATH"]
    else:
        env["PYTHONPATH"] = src_path
    subprocess.check_call([str(venv_python), str(project_root / "main.py")], env=env)


if __name__ == "__main__":
    main()
