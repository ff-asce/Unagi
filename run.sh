#!/bin/bash
# Convenience script to run UNAGI with the virtual environment
# Usage: ./run.sh [arguments]
# Example: ./run.sh --simple

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

# Run main.py with any arguments passed to this script
python "$SCRIPT_DIR/main.py" "$@"

# Made with Bob
