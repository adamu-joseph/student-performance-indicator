#!/usr/bin/env python
"""
Dependency Management Script
Handles renaming requirements.in and freezing dependencies to requirements.txt
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Main script execution"""
    project_root = Path(__file__).parent
    requirements_in = project_root / "requirements.in"
    requirements_txt = project_root / "requirements.txt"

    print("=" * 60)
    print("DEPENDENCY MANAGEMENT SCRIPT")
    print("=" * 60)

    # Step: Freeze dependencies to requirements.txt
    print("\n[Step 2] Freezing dependencies to requirements.txt...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            capture_output=True,
            text=True,
            check=True,
        )

        # Write frozen dependencies to requirements.txt
        with open(requirements_txt, "w") as f:
            f.write(result.stdout)

        print("✓ Successfully froze dependencies to requirements.txt")

        # Count packages
        package_count = len(result.stdout.strip().split("\n"))
        print(f"✓ Total packages: {package_count}")

    except subprocess.CalledProcessError as e:
        print(f"✗ Error freezing dependencies: {e}")
        sys.exit(1)

    # Step 3: Display confirmation
    print("\n" + "=" * 60)
    print("CONFIRMATION")
    print("=" * 60)
    print(f"✓ requirements.in: {requirements_in.exists()}")
    print(f"✓ requirements.txt: {requirements_txt.exists()}")
    print("\nDependency freeze completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
