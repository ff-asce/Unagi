#!/usr/bin/env python3
"""
Cross-platform launcher for UNAGI.
Automatically activates the virtual environment and runs main.py.

Usage:
    python unagi.py              # Run with TUI
    python unagi.py --simple     # Run with simple CLI
"""
import sys
import os
import subprocess
from pathlib import Path


def get_venv_python():
    """Get the path to the Python executable in the virtual environment."""
    script_dir = Path(__file__).parent
    venv_dir = script_dir / "venv"
    
    if sys.platform == "win32":
        python_path = venv_dir / "Scripts" / "python.exe"
    else:
        python_path = venv_dir / "bin" / "python"
    
    if not python_path.exists():
        print("❌ Virtual environment not found!")
        print(f"   Expected: {python_path}")
        print("\nPlease create the virtual environment first:")
        print("   python3 -m venv venv")
        print("   source venv/bin/activate  # On macOS/Linux")
        print("   venv\\Scripts\\activate    # On Windows")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    
    return python_path


def main():
    """Launch UNAGI with the virtual environment."""
    script_dir = Path(__file__).parent
    main_py = script_dir / "main.py"
    
    if not main_py.exists():
        print(f"❌ main.py not found at {main_py}")
        sys.exit(1)
    
    # Get venv python
    venv_python = get_venv_python()
    
    # Build command with arguments
    cmd = [str(venv_python), str(main_py)] + sys.argv[1:]
    
    # Run main.py with the venv python
    try:
        result = subprocess.run(cmd, cwd=str(script_dir))
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n\nGoodbye! 🐍\n")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error launching UNAGI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
