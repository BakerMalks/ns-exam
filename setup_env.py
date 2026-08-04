import os
import subprocess
import sys
import venv

# Configuration
ENV_DIR = ".venv"
REQ_FILE = "requirements.txt"


def main():
    # Create virtual environment
    print(f"Creating virtual environment in '{ENV_DIR}'...")
    builder = venv.EnvBuilder(with_pip=True)
    builder.create(ENV_DIR)

    if sys.platform == "win32":
        python_executable = os.path.join(ENV_DIR, "Scripts", "python.exe")
    else:
        python_executable = os.path.join(ENV_DIR, "bin", "python")

    # Install libararies for virtual environment
    if os.path.exists(REQ_FILE):
        print(f"Installing dependencies from {REQ_FILE}...")
        subprocess.run(
            [
                python_executable,
                "-m",
                "pip",
                "install",
                "-r",
                REQ_FILE,
            ],
            check=True,
        )
        print("\nSetup completed successfully!")

    else:
        print(
            f"\nWarning: '{REQ_FILE}' not found. Created empty environment."
        )


if __name__ == "__main__":
    main()