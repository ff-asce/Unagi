"""CLI interface for Unagi using Rich for formatting."""
from typing import Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from agent import get_chat_agent, get_context_loader
from config import get_settings
from .mascot import (
    get_startup_banner,
    get_help_text,
    get_goodbye_message,
    get_error_banner
)


class CLI:
    """Command-line interface for Unagi."""
    
    def __init__(self):
        """Initialize the CLI."""
        self.console = Console()
        self.settings = get_settings()
        self.agent = get_chat_agent()
        self.context_loader = get_context_loader()
        self.session = PromptSession(history=InMemoryHistory())
        self.running = False
    
    def show_startup(self):
        """Display startup screen with mascot."""
        if self.settings.ui_show_mascot:
            # Get user info for personalized greeting
            profile = self.context_loader.load_user_profile()
            user_name = profile.get('name') if profile else None
            
            # Get last log info
            today_log = self.context_loader.get_today_summary()
            if today_log:
                last_log = f"Last log: Today — {today_log.get('calories', 0)} kcal"
            else:
                logs = self.context_loader.load_recent_logs(1)
                if logs:
                    last_log = f"Last log: {logs[0].get('date', 'Unknown')} — {logs[0].get('calories', 0)} kcal | Deficit: {logs[0].get('deficit', 0)}"
                else:
                    last_log = None
            
            banner = get_startup_banner(user_name, last_log)
            self.console.print(banner, style="cyan")
    
    def show_response(self, text: str, response_type: str = "info"):
        """Display agent response with formatting.
        
        Args:
            text: Response text
            response_type: Type of response (info, success, warning, error)
        """
        style_map = {
            "info": "blue",
            "success": "green",
            "warning": "yellow",
            "error": "red"
        }
        
        style = style_map.get(response_type, "blue")
        
        # Check if it's a success message (starts with ✅)
        if text.startswith("✅"):
            panel = Panel(
                text,
                title="[bold green]Success[/bold green]",
                border_style="green",
                padding=(1, 2)
            )
        elif "error" in text.lower() or "failed" in text.lower():
            panel = Panel(
                text,
                title="[bold red]Error[/bold red]",
                border_style="red",
                padding=(1, 2)
            )
        else:
            # Regular response
            self.console.print(f"\n[{style}]Unagi:[/{style}] {text}\n")
            return
        
        self.console.print(panel)
    
    def show_today_summary(self):
        """Display today's log summary."""
        today_log = self.context_loader.get_today_summary()
        
        if not today_log:
            self.console.print("\n[yellow]No log for today yet.[/yellow]\n")
            return
        
        table = Table(title="Today's Summary", show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Date", str(today_log.get('date', 'Unknown')))
        table.add_row("Calories", f"{today_log.get('calories', 0)} kcal")
        table.add_row("Protein", f"{today_log.get('protein', 0)}g")
        table.add_row("Carbs", f"{today_log.get('carbs', 0)}g")
        table.add_row("Fats", f"{today_log.get('fats', 0)}g")
        table.add_row("Fiber", f"{today_log.get('fiber', 0)}g")
        table.add_row("Deficit", str(today_log.get('deficit', 0)))
        
        self.console.print("\n")
        self.console.print(table)
        self.console.print("\n")
    
    def show_week_summary(self):
        """Display last 7 days summary."""
        weekly = self.context_loader.get_weekly_summary()
        
        if weekly['days'] == 0:
            self.console.print("\n[yellow]No logs found for the past week.[/yellow]\n")
            return
        
        table = Table(title="Weekly Summary (Last 7 Days)", show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Days Logged", str(weekly['days']))
        table.add_row("Avg Calories", f"{weekly['avg_calories']} kcal/day")
        table.add_row("Avg Protein", f"{weekly['avg_protein']}g/day")
        table.add_row("Avg Deficit", str(weekly['avg_deficit']))
        table.add_row("Total Deficit", str(weekly['total_deficit']))
        
        self.console.print("\n")
        self.console.print(table)
        self.console.print("\n")
    
    def show_profile(self):
        """Display user profile."""
        profile = self.context_loader.load_user_profile()
        
        if not profile:
            self.console.print("\n[yellow]User profile not found.[/yellow]\n")
            return
        
        table = Table(title="User Profile", show_header=True, header_style="bold cyan")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Name", str(profile.get('name', 'Unknown')))
        table.add_row("Weight", f"{profile.get('current_weight', 0)} kg")
        table.add_row("Height", f"{profile.get('height_cm', 0)} cm")
        table.add_row("Gender", str(profile.get('gender', 'Unknown')))
        table.add_row("Goal", str(profile.get('goal', 'Unknown')))
        table.add_row("Maintenance", f"{profile.get('maintenance_calories', 0)} kcal/day")
        table.add_row("Protein Target", f"{profile.get('protein_target_per_kg', 1.3)}g/kg")
        
        self.console.print("\n")
        self.console.print(table)
        self.console.print("\n")
    
    def show_config(self):
        """Display current configuration (masked)."""
        table = Table(title="Configuration", show_header=True, header_style="bold cyan")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("LLM Model", self.settings.llm_model_name)
        table.add_row("LLM Base URL", self.settings.llm_base_url)
        table.add_row("API Key", "********" if self.settings.llm_api_key else "NOT SET")
        table.add_row("Vault Root", self.settings.vault_root or "NOT SET")
        table.add_row("Git Enabled", "Yes" if self.settings.git_enabled else "No")
        table.add_row("Git Auto-Push", "Yes" if self.settings.git_auto_push else "No")
        table.add_row("Context Days", str(self.settings.agent_context_days))
        
        self.console.print("\n")
        self.console.print(table)
        self.console.print("\n")
    
    def show_help(self):
        """Display help text."""
        help_text = get_help_text()
        self.console.print(help_text, style="cyan")
    
    def handle_special_command(self, command: str) -> bool:
        """Handle special commands.
        
        Args:
            command: Command string (e.g., "/help", "/today")
            
        Returns:
            True if command was handled, False otherwise
        """
        command = command.lower().strip()
        
        if command == "/help":
            self.show_help()
            return True
        elif command == "/today":
            self.show_today_summary()
            return True
        elif command == "/week":
            self.show_week_summary()
            return True
        elif command == "/profile":
            self.show_profile()
            return True
        elif command == "/config":
            self.show_config()
            return True
        elif command.startswith("/migrate"):
            self.handle_migrate_command(command)
        elif command == "/seed-ingredients":
            self.handle_seed_ingredients_command()
            return True
            return True
        elif command == "/exit" or command == "/quit":
            self.running = False
            return True
        
        return False
    
    def handle_migrate_command(self, command: str):
        """Handle /migrate command for vault migration."""
        from migration import VaultMigrator
        from git_manager import get_git_manager
        
        migrator = VaultMigrator(self.settings.vault_root)
        
        # Check for --cleanup flag
        if '--cleanup' in command:
            detection = migrator.detect()
            if not detection.get("has_old_structure"):
                self.console.print("\n[yellow]No original files to clean up.[/yellow]\n")
                return
            
            self.console.print("\n[yellow]⚠️  This will permanently delete the original Nutrition/ folder.[/yellow]")
            confirm = input("Delete original Nutrition/ files? (yes/no) ").strip().lower()
            
            if confirm in ['yes', 'y']:
                if migrator.delete_originals():
                    self.console.print("\n[green]✅ Originals deleted[/green]\n")
                    if self.settings.git_enabled:
                        try:
                            git = get_git_manager()
                            git.commit_deletion()
                            self.console.print("[green]✅ Deletion committed to Git[/green]\n")
                        except Exception as e:
                            self.console.print(f"[yellow]⚠️  Git commit failed: {str(e)}[/yellow]\n")
                else:
                    self.console.print("\n[red]⚠️  Could not delete originals[/red]\n")
            return
        
        # Standard migration
        detection = migrator.detect()
        
        if not detection.get("has_old_structure"):
            # Check for files added since last migration
            new_files = migrator.get_files_to_migrate()
            if new_files:
                self.console.print(
                    f"\n[cyan]Found {len(new_files)} new files "
                    f"not yet in Unagi/Daily Logs/[/cyan]\n"
                )
                self._run_migration_flow(migrator)
            else:
                self.console.print("\n[green]✅ All files already migrated. Nothing to do.[/green]\n")
            return
        
        # Run migration flow
        self._run_migration_flow(migrator)
    
    def _run_migration_flow(self, migrator):
        """Run the interactive migration flow."""
        from git_manager import get_git_manager
        
        self.console.print("\n[cyan]Validating files...[/cyan]")
        
        # Dry run first to validate
        dry_report = migrator.migrate(dry_run=True)
        
        if dry_report.has_issues():
            self.console.print(f"\n[yellow]⚠️  Found issues with {len(dry_report.failed_files)} files:[/yellow]")
            for f in dry_report.failed_files:
                self.console.print(f"   - {f['path']}: {f['reason']}")
            self.console.print(
                "\n[yellow]These files will be skipped. "
                "All other files will migrate successfully.[/yellow]"
            )
            response = input("\nContinue anyway? (yes/no) ").strip().lower()
            if response not in ['yes', 'y']:
                self.console.print("\n[yellow]Migration cancelled.[/yellow]\n")
                return
        
        self.console.print(f"\n[cyan]Migrating {dry_report.successfully_copied} files...[/cyan]")
        
        # Run actual migration with progress
        def progress(current, total, filename):
            bar_len = 30
            filled = int(bar_len * current / total)
            bar = '█' * filled + '░' * (bar_len - filled)
            print(f"\r  [{bar}] {current}/{total} — {filename}",
                  end="", flush=True)
        
        report = migrator.migrate(dry_run=False, on_progress=progress)
        print()  # Newline after progress bar
        
        self.console.print(f"\n{report.summary()}\n")
        
        # Show warnings
        if report.validation_warnings:
            self.console.print(f"[yellow]⚠️  {len(report.validation_warnings)} files migrated with warnings:[/yellow]")
            for w in report.validation_warnings[:5]:  # Show max 5
                self.console.print(f"   - {w['path']}: {', '.join(w['issues'])}")
            if len(report.validation_warnings) > 5:
                self.console.print(f"   ... and {len(report.validation_warnings) - 5} more")
            self.console.print()
        
        # Git commit
        if self.settings.git_enabled:
            try:
                git = get_git_manager()
                git.commit_migration(report)
                self.console.print("[green]✅ Changes committed to Git[/green]\n")
            except Exception as e:
                self.console.print(f"[yellow]⚠️  Git commit failed: {str(e)}[/yellow]\n")
        
        # Offer to delete originals
        self.console.print(
            "[cyan]Original files are preserved at: Nutrition/Daily Logs/[/cyan]\n"
            "[cyan]You can delete them once you've verified everything looks correct in Obsidian.[/cyan]"
        )
        response = input("\nDelete originals now? (yes/no) ").strip().lower()
        
        if response in ['yes', 'y']:
            if migrator.delete_originals():
                self.console.print("\n[green]✅ Originals deleted[/green]\n")
                if self.settings.git_enabled:
                    try:
                        git = get_git_manager()
                        git.commit_deletion()
                    except Exception:
                        pass
            else:
                self.console.print("\n[red]⚠️  Could not delete originals — remove manually if needed[/red]\n")
        else:
            self.console.print(
                "\n[cyan]Originals kept. Run '/migrate --cleanup' to delete them later.[/cyan]\n"
            )
    
    def handle_seed_ingredients_command(self):
        """Handle /seed-ingredients command for ingredient seeding."""
        from onboarding import IngredientSeeder
        from agent.llm import LLMClient
        from vault.reader import get_vault_reader
        from vault.writer import get_vault_writer
        
        seeder = IngredientSeeder(
            llm_client=LLMClient(),
            vault_reader=get_vault_reader(),
            vault_writer=get_vault_writer()
        )
        
        # Check if already seeded
        if seeder.has_known_ingredients():
            response = input(
                "\nYou already have known ingredients. "
                "Scan for new ones? (yes/no) "
            ).strip().lower()
            if response not in ['yes', 'y']:
                self.console.print("\n[yellow]Cancelled.[/yellow]\n")
                return
        
        count = seeder.run()
        if count > 0:
            # Invalidate context cache so new ingredients are
            # picked up immediately
            self.context_loader.invalidate()
            self.console.print(
                f"\n[green]✅ {count} ingredients added. "
                f"They'll be used from your next log entry.[/green]\n"
            )
    
    def get_user_input(self) -> Optional[str]:
        """Get input from user with prompt.
        
        Returns:
            User input string, or None if interrupted
        """
        try:
            user_input = self.session.prompt("You > ")
            return user_input.strip()
        except KeyboardInterrupt:
            return None
        except EOFError:
            return None
    
    def run(self):
        """Run the main CLI loop."""
        self.running = True
        self.show_startup()
        
        while self.running:
            try:
                user_input = self.get_user_input()
                
                if user_input is None:
                    # Ctrl+C or Ctrl+D
                    self.running = False
                    break
                
                if not user_input:
                    continue
                
                # Check for special commands
                if user_input.startswith('/'):
                    self.handle_special_command(user_input)
                    continue
                
                # Process message through agent
                response = self.agent.process_message(user_input)
                
                # Display response
                if response.startswith("✅"):
                    self.show_response(response, "success")
                elif "error" in response.lower() or "failed" in response.lower():
                    self.show_response(response, "error")
                else:
                    self.show_response(response, "info")
                
            except KeyboardInterrupt:
                self.running = False
                break
            except Exception as e:
                self.console.print(f"\n[red]Error: {str(e)}[/red]\n")
        
        # Show goodbye message
        goodbye = get_goodbye_message()
        self.console.print(goodbye, style="cyan")


def run_cli():
    """Run the CLI interface."""
    cli = CLI()
    cli.run()

# Made with Bob
