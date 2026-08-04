import os
import subprocess
import venv

# Configuration
ENV_DIR = ".venv"
REQ_FILE = "requirements.txt"


def main():
    # Create virtual environment
    print(f"Creating virtual environment in '{ENV_DIR}'...")
    builder = venv.EnvBuilder(with_pip=True)
    builder.create(ENV_DIR)

    # Install libararies for virtual environment
    if os.path.exists(REQ_FILE):
        print(f"Installing dependencies from {REQ_FILE}...")
        subprocess.run(
            [
                "python",
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