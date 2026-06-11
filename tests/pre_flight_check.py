#!/usr/bin/env python3
"""
Pre-flight check script for UNAGI v1
Validates syntax, imports, and dependencies before first run
"""

import sys
import subprocess
from pathlib import Path

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")

def check_syntax():
    """Check Python syntax for all .py files"""
    print_header("1. Checking Python Syntax")
    
    project_root = Path(__file__).parent
    py_files = list(project_root.rglob("*.py"))
    py_files = [f for f in py_files if "venv" not in str(f) and "__pycache__" not in str(f)]
    
    errors = []
    for py_file in py_files:
        result = subprocess.run(
            ["python3", "-m", "py_compile", str(py_file)],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            errors.append((py_file, result.stderr))
    
    if errors:
        print("❌ Syntax errors found:")
        for file, error in errors:
            print(f"  {file}: {error}")
        return False
    else:
        print(f"✅ All {len(py_files)} Python files have valid syntax")
        return True

def check_dependencies():
    """Check if all required packages are installed"""
    print_header("2. Checking Dependencies")
    
    required = {
        'openai': 'openai',
        'python-dotenv': 'dotenv',
        'pyyaml': 'yaml',
        'gitpython': 'git',
        'rich': 'rich',
        'prompt_toolkit': 'prompt_toolkit',
        'python-frontmatter': 'frontmatter',
        'python-dateutil': 'dateutil'
    }
    
    missing = []
    for package, import_name in required.items():
        try:
            __import__(import_name)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing {len(missing)} package(s)")
        print(f"Run: pip3 install {' '.join(missing)}")
        return False
    else:
        print(f"\n✅ All {len(required)} dependencies installed")
        return True

def check_imports():
    """Test all module imports"""
    print_header("3. Testing Module Imports")
    
    imports = [
        ("config.settings", ["Settings", "get_settings"]),
        ("agent.prompts", ["get_system_prompt", "MICRONUTRIENT_ORDER"]),
        ("agent.llm", ["LLMClient", "get_llm_client"]),
        ("agent.context", ["ContextLoader"]),
        ("agent.chat", ["ChatAgent"]),
        ("vault.parser", ["parse_log_file", "validate_log_data", "format_log_data", "merge_log_data"]),
        ("vault.reader", ["VaultReader", "get_vault_reader"]),
        ("vault.writer", ["VaultWriter", "get_vault_writer"]),
        ("git_manager.commits", ["GitManager", "get_git_manager"]),
        ("onboarding.setup", ["run_onboarding_flow"]),
        ("ui.mascot", ["get_ross_unagi_art", "get_startup_banner", "get_help_text", "get_goodbye_message"]),
        ("ui.cli", ["CLI"]),
    ]
    
    errors = []
    for module, names in imports:
        try:
            mod = __import__(module, fromlist=names)
            for name in names:
                if not hasattr(mod, name):
                    errors.append(f"{module}.{name} not found")
            print(f"✅ {module}")
        except Exception as e:
            errors.append(f"{module}: {e}")
            print(f"❌ {module}: {e}")
    
    if errors:
        print(f"\n❌ {len(errors)} import error(s)")
        return False
    else:
        print(f"\n✅ All {len(imports)} modules import successfully")
        return True

def check_file_structure():
    """Verify project structure"""
    print_header("4. Checking File Structure")
    
    required_files = [
        "main.py",
        "requirements.txt",
        ".env.example",
        "config.yaml",
        ".gitignore",
        "README.md",
        "QUICKSTART.md",
        "config/__init__.py",
        "config/settings.py",
        "agent/__init__.py",
        "agent/prompts.py",
        "agent/llm.py",
        "agent/context.py",
        "agent/chat.py",
        "vault/__init__.py",
        "vault/parser.py",
        "vault/reader.py",
        "vault/writer.py",
        "git_manager/__init__.py",
        "git_manager/commits.py",
        "onboarding/__init__.py",
        "onboarding/setup.py",
        "ui/__init__.py",
        "ui/mascot.py",
        "ui/cli.py",
    ]
    
    project_root = Path(__file__).parent
    missing = []
    
    for file in required_files:
        file_path = project_root / file
        if file_path.exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file}")
            missing.append(file)
    
    if missing:
        print(f"\n❌ {len(missing)} file(s) missing")
        return False
    else:
        print(f"\n✅ All {len(required_files)} required files present")
        return True

def main():
    print("\n" + "="*60)
    print("  UNAGI v1 - Pre-Flight Check")
    print("  Validating installation before first run")
    print("="*60)
    
    checks = [
        check_file_structure(),
        check_syntax(),
        check_dependencies(),
        check_imports(),
    ]
    
    print_header("Summary")
    
    if all(checks):
        print("✅ All checks passed!")
        print("\nYou're ready to run UNAGI:")
        print("  1. Copy .env.example to .env and add your API key")
        print("  2. Run: python3 main.py")
        print("\nFor detailed setup instructions, see README.md")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
