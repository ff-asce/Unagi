#!/usr/bin/env python3
"""
UNAGI - Total Food Awareness
Main entry point for the nutrition agent.
"""
import sys
from pathlib import Path

def main():
    """Main entry point for Unagi."""
    try:
        # Import modules
        from config import get_settings, ConfigError
        from onboarding import needs_onboarding, run_onboarding_flow, OnboardingError
        from vault import get_vault_writer
        from ui import run_cli
        from ui.mascot import get_error_banner
        
        # Load configuration
        try:
            settings = get_settings()
        except ConfigError as e:
            print(get_error_banner("Configuration"))
            print(f"\n{str(e)}\n")
            print("Please check your .env and config.yaml files.")
            print("See README.md for setup instructions.\n")
            sys.exit(1)
        
        # Check if vault root is configured
        if not settings.vault_root:
            print(get_error_banner("Configuration"))
            print("\nVault root is not configured.")
            print("Please set 'vault.root' in config.yaml to your Obsidian vault path.\n")
            print("Example:")
            print("  vault:")
            print("    root: /path/to/your/ObsidianVault\n")
            sys.exit(1)
        
        # Ensure vault root exists
        vault_path = Path(settings.vault_root)
        if not vault_path.exists():
            print(get_error_banner("Configuration"))
            print(f"\nVault root does not exist: {settings.vault_root}")
            print("Please create the directory or update config.yaml with the correct path.\n")
            sys.exit(1)
        
        # Check if onboarding is needed
        if needs_onboarding():
            print("\n🐍 First-time setup detected!\n")
            try:
                success = run_onboarding_flow()
                if not success:
                    print("\nOnboarding cancelled. Exiting.\n")
                    sys.exit(0)
            except OnboardingError as e:
                print(get_error_banner("Onboarding"))
                print(f"\n{str(e)}\n")
                sys.exit(1)
            except KeyboardInterrupt:
                print("\n\nOnboarding cancelled. Exiting.\n")
                sys.exit(0)
        
        # Initialize vault structure (creates folders if needed)
        try:
            writer = get_vault_writer()
            writer._ensure_vault_structure()
            writer.create_dashboard_if_missing()
        except Exception as e:
            print(get_error_banner("Vault"))
            print(f"\nFailed to initialize vault structure: {str(e)}\n")
            sys.exit(1)
        
        # Run the CLI
        try:
            run_cli()
        except KeyboardInterrupt:
            print("\n\nGoodbye! 🐍\n")
            sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n\nGoodbye! 🐍\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
