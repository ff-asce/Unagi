#!/bin/bash
# UNAGI launcher script - automatically activates venv and runs the app

cd "$(dirname "$0")"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate venv and run
source venv/bin/activate
python main.py "$@"

# Made with Bob
