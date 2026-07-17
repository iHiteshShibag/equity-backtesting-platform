#!/usr/bin/env python3
"""Cross-platform bootstrap for the Equity Backtesting Platform.

Run identically on Ubuntu or Windows:
    python scripts/bootstrap.py

Replaces the old setup.sh / setup-windows.bat pair with a single
script so the two platforms can never drift out of sync.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

MIN_PYTHON = (3, 10)
IS_WINDOWS = platform.system() == "Windows"

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
VENV_DIR = BACKEND_DIR / ".venv"
REQUIREMENTS_FILE = BACKEND_DIR / "requirements" / "dev.txt"


def section(title: str) -> None:
    print(f"\n{'=' * 60}\n {title}\n{'=' * 60}")


def run(cmd) -> bool:
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


# --------------------------------------------------------------------------
# 1. Detect host OS
# --------------------------------------------------------------------------
def detect_os() -> str:
    section("1. Detecting Host OS")
    system = platform.system()
    print(f"platform.system() -> {system}")
    print(f"os.name           -> {os.name}")
    print(f"Full platform     -> {platform.platform()}")
    return system


# --------------------------------------------------------------------------
# 2. Validate prerequisites: Python 3.10+ and Docker
# --------------------------------------------------------------------------
def validate_python() -> bool:
    major, minor = sys.version_info[:2]
    ok = (major, minor) >= MIN_PYTHON
    tag = "OK" if ok else "FAIL"
    print(f"[{tag}] Python {major}.{minor}.{sys.version_info.micro} "
          f"(required >= {MIN_PYTHON[0]}.{MIN_PYTHON[1]})")
    return ok


def validate_docker() -> bool:
    cli_found = shutil.which("docker") is not None
    if not cli_found:
        print("[FAIL] Docker CLI not found on PATH.")
        print("       Install Docker Desktop (Windows) or Docker Engine (Ubuntu):")
        print("       https://www.docker.com/products/docker-desktop/")
        return False
    print("[OK] Docker CLI found")

    daemon_ok = run(["docker", "info"])
    if daemon_ok:
        print("[OK] Docker daemon is running")
    else:
        print("[WARN] Docker CLI found but the daemon isn't responding.")
        print("       Start Docker Desktop / the Docker service and re-run this script.")

    compose_ok = run(["docker", "compose", "version"])
    if compose_ok:
        print("[OK] Docker Compose plugin available")
    else:
        print("[WARN] 'docker compose version' failed — Compose v2 plugin may be missing.")

    return cli_found and daemon_ok and compose_ok


def validate_prerequisites() -> tuple[bool, bool]:
    section("2. Validating Prerequisites")
    return validate_python(), validate_docker()


# --------------------------------------------------------------------------
# 3. Bootstrap local .env files from their .env.example templates
# --------------------------------------------------------------------------
def ensure_env_file(service_dir: Path, label: str) -> None:
    env_path = service_dir / ".env"
    example_path = service_dir / ".env.example"

    if env_path.exists():
        print(f"[OK] {label}/.env already exists — leaving it untouched")
        return

    if not example_path.exists() or not os.access(example_path, os.R_OK):
        print(f"[SKIP] {label}/.env.example not found — nothing to copy")
        return

    shutil.copyfile(example_path, env_path)
    print(f"[CREATED] {label}/.env  (copied from {label}/.env.example — edit it with real values)")


def bootstrap_env_files() -> None:
    section("3. Bootstrapping Local .env Files")
    ensure_env_file(BACKEND_DIR, "backend")
    ensure_env_file(FRONTEND_DIR, "frontend")


# --------------------------------------------------------------------------
# 4. Create the backend virtual environment and upgrade pip
# --------------------------------------------------------------------------
def venv_python_path(venv_dir: Path) -> Path:
    # venv layout differs by OS: Scripts/ + .exe on Windows, bin/ on Linux/macOS.
    if IS_WINDOWS:
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def bootstrap_virtualenv() -> bool:
    section("4. Setting Up Backend Virtual Environment")

    if VENV_DIR.exists():
        print(f"[OK] Virtual environment already exists at {VENV_DIR}")
    else:
        print(f"Creating virtual environment at {VENV_DIR} ...")
        if not run([sys.executable, "-m", "venv", str(VENV_DIR)]):
            print("[FAIL] Could not create virtual environment")
            return False
        print("[CREATED] Virtual environment")

    venv_python = venv_python_path(VENV_DIR)
    if not venv_python.exists():
        print(f"[FAIL] Expected venv interpreter at {venv_python} but it's missing")
        return False

    print("Upgrading pip inside the virtual environment ...")
    if run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"]):
        print("[OK] pip upgraded")
    else:
        print("[WARN] Failed to upgrade pip — continuing anyway")

    return True


# --------------------------------------------------------------------------
# 5. Summary
# --------------------------------------------------------------------------
def print_summary(python_ok: bool, docker_ok: bool, venv_ok: bool) -> None:
    section("Setup Summary")

    if IS_WINDOWS:
        activate_hint = str(VENV_DIR / "Scripts" / "activate")
    else:
        activate_hint = f"source {VENV_DIR / 'bin' / 'activate'}"

    try:
        requirements_hint = REQUIREMENTS_FILE.relative_to(ROOT_DIR)
    except ValueError:
        requirements_hint = REQUIREMENTS_FILE

    print("Recommended path — Docker (identical behavior on Ubuntu & Windows):")
    print("  docker compose up --build")

    print("\nAlternative — native virtual environment:")
    print(f"  {activate_hint}")
    print(f"  pip install -r {requirements_hint}")
    print("  uvicorn app.main:app --reload   (run this from inside backend/)")

    if not python_ok:
        print(f"\n[ACTION REQUIRED] Install Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+: "
              "https://www.python.org/downloads/")
    if not docker_ok:
        print("\n[ACTION REQUIRED] Install/start Docker before using the recommended path: "
              "https://www.docker.com/products/docker-desktop/")
    if not venv_ok:
        print("\n[ACTION REQUIRED] Re-run this script after resolving the virtual "
              "environment error above.")

    print("\nNext step either way: edit backend/.env (and frontend/.env) with real values.")


def main() -> int:
    section("Equity Backtesting Platform — Cross-Platform Bootstrap")

    detect_os()
    python_ok, docker_ok = validate_prerequisites()
    bootstrap_env_files()
    venv_ok = bootstrap_virtualenv()
    print_summary(python_ok, docker_ok, venv_ok)

    all_ok = python_ok and docker_ok and venv_ok
    print("\nBootstrap completed successfully." if all_ok
          else "\nBootstrap completed with warnings — see [FAIL]/[WARN] items above.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
