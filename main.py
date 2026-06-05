#!/usr/bin/env python3
"""
UNAGI - Total Food Awareness
Main entry point for the nutrition agent.
"""
import sys
from pathlib import Path


def _run_migration_flow(migrator, settings) -> bool:
    """
    Run the interactive migration flow.
    Returns True if migration completed successfully.
    """
    from git_manager import get_git_manager
    
    print("\nValidating files...")
    
    # Dry run first to validate
    dry_report = migrator.migrate(dry_run=True)
    
    if dry_report.has_issues():
        print(f"\n⚠️  Found issues with {len(dry_report.failed_files)} files:")
        for f in dry_report.failed_files:
            print(f"   - {f['path']}: {f['reason']}")
        print(
            "\nThese files will be skipped. "
            "All other files will migrate successfully."
        )
        response = input("\nContinue anyway? (yes/no) ").strip().lower()
        if response not in ['yes', 'y']:
            print("Migration cancelled.")
            return False
    
    print(f"\nMigrating {dry_report.successfully_copied} files...")
    
    # Run actual migration with progress
    def progress(current, total, filename):
        bar_len = 30
        filled = int(bar_len * current / total)
        bar = '█' * filled + '░' * (bar_len - filled)
        print(f"\r  [{bar}] {current}/{total} — {filename}",
              end="", flush=True)
    
    report = migrator.migrate(dry_run=False, on_progress=progress)
    print()  # Newline after progress bar
    
    print(f"\n{report.summary()}")
    
    # Validate warnings
    if report.validation_warnings:
        print(f"\n⚠️  {len(report.validation_warnings)} files migrated "
              f"with warnings:")
        for w in report.validation_warnings[:5]:  # Show max 5
            print(f"   - {w['path']}: {', '.join(w['issues'])}")
        if len(report.validation_warnings) > 5:
            print(f"   ... and {len(report.validation_warnings) - 5} more")
    
    # Git commit
    if settings.git_enabled:
        try:
            git = get_git_manager()
            git.commit_migration(report)
            print("\n✅ Changes committed to Git")
        except Exception as e:
            print(f"\n⚠️  Git commit failed: {str(e)}")
    
    # Offer to delete originals
    print(
        f"\nOriginal files are preserved at: "
        f"Nutrition/Daily Logs/"
    )
    print(
        "You can delete them once you've verified everything "
        "looks correct in Obsidian."
    )
    response = input(
        "\nDelete originals now? (yes/no) "
    ).strip().lower()
    
    if response in ['yes', 'y']:
        if migrator.delete_originals():
            print("✅ Originals deleted")
            if settings.git_enabled:
                try:
                    git = get_git_manager()
                    git.commit_deletion()
                except Exception:
                    pass
        else:
            print("⚠️  Could not delete originals — remove manually if needed")
    else:
        print(
            "\nOriginals kept. Run '/migrate --cleanup' "
            "to delete them later."
        )
    
    return report.successfully_copied > 0


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
        
        # Check for old vault structure and offer migration
        from migration import VaultMigrator
        migrator = VaultMigrator(settings.vault_root)
        detection = migrator.detect()
        
        if detection.get("has_old_structure"):
            count = detection["log_count"]
            date_range = detection.get("date_range")
            
            print(f"\n📁 Found {count} existing log files in old structure")
            if date_range:
                start, end = date_range
                print(
                    f"   Date range: {start.strftime('%d %b %Y')} → "
                    f"{end.strftime('%d %b %Y')}"
                )
            print(f"\n   These need to be moved to the new Unagi/ folder structure.")
            print(f"   This is safe — originals won't be deleted until you confirm.\n")
            
            response = input("Migrate existing logs now? (yes/no) ").strip().lower()
            
            if response in ['yes', 'y']:
                _run_migration_flow(migrator, settings)
            else:
                print(
                    "\n⚠️  Skipping migration. "
                    "Run '/migrate' at any time to migrate later.\n"
                )
        
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
        
        # Run ingredient seeding after onboarding (if applicable)
        from onboarding import IngredientSeeder
        from agent.llm import LLMClient
        from vault.reader import get_vault_reader
        from vault.writer import get_vault_writer
        
        seeder = IngredientSeeder(
            llm_client=LLMClient(),
            vault_reader=get_vault_reader(),
            vault_writer=get_vault_writer()
        )
        
        if not seeder.has_known_ingredients() and seeder.has_enough_logs():
            print(
                "\n📋 Before we start, let me scan your log history "
                "to learn your common ingredients."
            )
            print(
                "   This helps me give you more accurate nutritional "
                "estimates going forward.\n"
            )
            
            response = input(
                "Scan logs for common ingredients? "
                "(yes/no, takes ~10 seconds) "
            ).strip().lower()
            
            if response in ['yes', 'y', '']:
                count = seeder.run()
                if count > 0:
                    print(
                        f"\n✅ Added {count} ingredients to your profile. "
                        f"I'll use these for accurate tracking going forward.\n"
                    )
                else:
                    print(
                        "\nNo ingredients added. "
                        "You can run /seed-ingredients later.\n"
                    )
        
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
