# 🐍 UNAGI — Feature Spec: Vault Migration
### `specs/v1/FEAT_SPEC_v1_migration.md`
**Version:** 1.0
**Status:** Ready for implementation
**Last Updated:** 2026-05-26
**Applies To:** Users with existing logs in `Nutrition/Daily Logs/` (pre-Unagi vault structure)
**Companion Specs:** `FIX_SPEC_v1.md`, `ARCH_SPEC_v1.md`, `FEAT_SPEC_v1_ingredient_seeding.md`

---

## Problem Statement

You have 60+ daily log files in your Obsidian vault at:
```
<vault_root>/Nutrition/Daily Logs/DD-MM-YYYY.md
```

Unagi expects files at:
```
<vault_root>/Unagi/Daily Logs/DD-MM-YYYY.md
```

Without migration:
- The agent's "last 7 days context" is always empty
- Personalization doesn't work — the agent has no history
- The Dataview dashboard queries break (they reference `Nutrition/Daily Logs`)
- You lose months of logged data as far as Unagi is concerned

Migration must be safe, reversible, and verified. No files should be deleted until the user explicitly confirms everything looks correct.

---

## User Story

> As a user with an existing Obsidian nutrition vault, I want to run Unagi for the first time and have it detect my existing logs, migrate them to the new folder structure, and confirm everything transferred correctly — without losing any data or breaking my Obsidian dashboard.

**Acceptance criteria:**
- All existing `.md` log files are copied to `Unagi/Daily Logs/`
- Frontmatter is validated on every file — malformed files are flagged, not silently skipped
- The `Nutrition Dashboard.md` Dataview queries are updated to reference `Unagi/Daily Logs`
- Original files in `Nutrition/Daily Logs/` are NOT deleted until the user confirms
- A migration report is shown before any files are moved
- Migration is triggered automatically on first run if the old structure is detected
- Migration can be re-run manually via `/migrate` command
- After migration, the agent immediately has full historical context

---

## Detection Logic

On first run (before showing the startup screen), check for the old vault structure:

```python
def detect_old_vault_structure(vault_root: str) -> dict:
    """
    Detect whether the old Nutrition/ folder structure exists.
    
    Returns a dict with:
    - has_old_structure: bool
    - old_logs_path: Path or None
    - old_dashboard_path: Path or None
    - log_count: int
    - date_range: tuple (oldest, newest) or None
    """
    vault_path = Path(vault_root)
    old_logs_path = vault_path / "Nutrition" / "Daily Logs"
    old_dashboard_path = vault_path / "Nutrition" / "Nutrition Dashboard.md"
    
    result = {
        "has_old_structure": False,
        "old_logs_path": None,
        "old_dashboard_path": None,
        "log_count": 0,
        "date_range": None
    }
    
    if not old_logs_path.exists():
        return result
    
    log_files = list(old_logs_path.glob("*.md"))
    if not log_files:
        return result
    
    result["has_old_structure"] = True
    result["old_logs_path"] = old_logs_path
    result["log_count"] = len(log_files)
    
    if old_dashboard_path.exists():
        result["old_dashboard_path"] = old_dashboard_path
    
    # Find date range
    dates = []
    for f in log_files:
        try:
            day, month, year = f.stem.split("-")
            dates.append(datetime(int(year), int(month), int(day)))
        except Exception:
            continue
    
    if dates:
        result["date_range"] = (min(dates), max(dates))
    
    return result
```

---

## Migration Flow

### Trigger Points

**Automatic:** On first run, if `User Profile.md` doesn't exist AND old structure is detected, run migration before onboarding.

**Manual:** Via `/migrate` command at any time. Re-runs the full migration check and offers to re-migrate any files that were added since the last migration.

### Step-by-step Flow

```
1. DETECT
   Scan vault_root for Nutrition/Daily Logs/*.md
   Count files, find date range, check dashboard exists

2. REPORT (show before doing anything)
   "Found 63 log files from 24 March 2026 to 29 May 2026
    Dashboard: Nutrition/Nutrition Dashboard.md
    
    I'll copy them to:
      Nutrition/Daily Logs/ → Unagi/Daily Logs/
      Nutrition/Nutrition Dashboard.md → Unagi/Nutrition Dashboard.md
    
    Original files will NOT be deleted until you confirm.
    Proceed? (yes/no)"

3. VALIDATE (before copying)
   Parse every file's frontmatter
   Check required fields exist: date, calories, maintenance, deficit,
     protein, carbs, fats, fiber
   Check filename matches frontmatter date
   Collect list of any malformed files

4. COPY
   Copy all valid files to Unagi/Daily Logs/
   Copy dashboard to Unagi/Nutrition Dashboard.md
   Do NOT delete originals yet

5. PATCH DASHBOARD
   Update Dataview query paths in the copied dashboard:
   "Nutrition/Daily Logs" → "Unagi/Daily Logs"

6. VERIFY
   Parse every copied file
   Confirm count matches source
   Show any files that failed to copy or parse

7. REPORT
   "Migration complete:
    ✅ 61 files migrated successfully
    ⚠️  2 files had issues (see below)
    
    Problematic files:
    - 16-04-2025.md: date field missing
    - 03-05-2026.md: calories field is a string, not integer
    
    Original files preserved at Nutrition/Daily Logs/
    Delete originals now? (yes/no/later)"

8. CLEANUP (optional, user-confirmed)
   If user says yes: delete Nutrition/Daily Logs/ folder
   If user says no or later: keep originals, add note to profile
   Never auto-delete

9. GIT COMMIT
   Commit all migrated files in a single commit:
   "[unagi] migrate: 61 log files from Nutrition/ → Unagi/ (YYYY-MM-DD)"
```

---

## File: `migration/migrator.py`

```python
"""Vault migration from old Nutrition/ structure to new Unagi/ structure."""
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import shutil
import re
import frontmatter
import yaml


class MigrationError(Exception):
    pass


class MigrationReport:
    """Holds the results of a migration run."""
    
    def __init__(self):
        self.total_found: int = 0
        self.successfully_copied: int = 0
        self.failed_files: List[Dict] = []      # [{path, reason}]
        self.validation_warnings: List[Dict] = [] # [{path, issue}]
        self.dashboard_migrated: bool = False
        self.dashboard_patched: bool = False
        self.date_range: Optional[Tuple[datetime, datetime]] = None
    
    def has_issues(self) -> bool:
        return len(self.failed_files) > 0
    
    def summary(self) -> str:
        lines = []
        lines.append(
            f"✅ {self.successfully_copied}/{self.total_found} "
            f"files migrated successfully"
        )
        if self.date_range:
            start, end = self.date_range
            lines.append(
                f"   Date range: {start.strftime('%d %b %Y')} → "
                f"{end.strftime('%d %b %Y')}"
            )
        if self.dashboard_migrated:
            lines.append("✅ Dashboard migrated")
        if self.dashboard_patched:
            lines.append("✅ Dashboard Dataview queries updated")
        if self.validation_warnings:
            lines.append(
                f"⚠️  {len(self.validation_warnings)} files had "
                f"non-critical issues (migrated anyway)"
            )
        if self.failed_files:
            lines.append(
                f"❌ {len(self.failed_files)} files failed to migrate:"
            )
            for f in self.failed_files:
                lines.append(f"   - {f['path']}: {f['reason']}")
        return "\n".join(lines)


class VaultMigrator:
    """
    Migrates vault files from the old Nutrition/ structure
    to the new Unagi/ structure.
    
    Safe-by-default: never deletes originals without explicit confirmation.
    """
    
    # Fields required in every daily log
    REQUIRED_FIELDS = [
        'date', 'calories', 'maintenance', 'deficit',
        'protein', 'carbs', 'fats', 'fiber'
    ]
    
    # Fields that must be integers
    INTEGER_FIELDS = [
        'calories', 'maintenance', 'deficit',
        'protein', 'carbs', 'fats', 'fiber'
    ]
    
    def __init__(self, vault_root: str):
        self.vault_root = Path(vault_root)
        self.old_logs_path = self.vault_root / "Nutrition" / "Daily Logs"
        self.old_dashboard_path = (
            self.vault_root / "Nutrition" / "Nutrition Dashboard.md"
        )
        self.new_logs_path = (
            self.vault_root / "Unagi" / "Daily Logs"
        )
        self.new_dashboard_path = (
            self.vault_root / "Unagi" / "Nutrition Dashboard.md"
        )
    
    def detect(self) -> Dict[str, Any]:
        """Detect whether old structure exists and how many files."""
        if not self.old_logs_path.exists():
            return {"has_old_structure": False}
        
        log_files = list(self.old_logs_path.glob("*.md"))
        if not log_files:
            return {"has_old_structure": False}
        
        dates = []
        for f in log_files:
            try:
                day, month, year = f.stem.split("-")
                dates.append(datetime(int(year), int(month), int(day)))
            except Exception:
                continue
        
        return {
            "has_old_structure": True,
            "log_count": len(log_files),
            "has_dashboard": self.old_dashboard_path.exists(),
            "date_range": (min(dates), max(dates)) if dates else None
        }
    
    def validate_file(self, file_path: Path) -> Tuple[bool, List[str]]:
        """
        Validate a single log file.
        
        Returns (is_valid, list_of_issues).
        is_valid=True means the file can be migrated (may have warnings).
        is_valid=False means the file is too broken to migrate safely.
        """
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)
            data = dict(post.metadata)
        except Exception as e:
            return False, [f"Cannot parse file: {str(e)}"]
        
        # Check required fields
        missing = [f for f in self.REQUIRED_FIELDS if f not in data]
        if missing:
            # Missing date field is fatal — we can't validate the entry
            if 'date' in missing:
                return False, [f"Missing required field: date"]
            # Other missing fields are warnings — file still migrates
            issues.append(f"Missing fields: {', '.join(missing)}")
        
        # Check integer fields
        for field in self.INTEGER_FIELDS:
            if field in data and not isinstance(data[field], int):
                try:
                    int(data[field])
                    issues.append(
                        f"Field '{field}' is not an integer "
                        f"(value: {data[field]}) — will need manual fix"
                    )
                except (ValueError, TypeError):
                    issues.append(
                        f"Field '{field}' has invalid value: {data[field]}"
                    )
        
        # Check filename matches frontmatter date
        try:
            day, month, year = file_path.stem.split("-")
            filename_date = datetime(int(year), int(month), int(day))
            date_str = str(data.get('date', ''))[:10]
            frontmatter_date = datetime.strptime(date_str, "%Y-%m-%d")
            
            if filename_date != frontmatter_date:
                issues.append(
                    f"Filename date ({file_path.stem}) doesn't match "
                    f"frontmatter date ({date_str})"
                )
        except Exception:
            issues.append("Could not verify date consistency")
        
        # Warnings don't block migration
        return True, issues
    
    def migrate(
        self,
        dry_run: bool = False,
        on_progress: Optional[callable] = None
    ) -> MigrationReport:
        """
        Run the migration.
        
        Args:
            dry_run: If True, validate and report but don't copy anything
            on_progress: Callback(current, total, filename) for progress
        
        Returns:
            MigrationReport with full results
        """
        report = MigrationReport()
        
        if not self.old_logs_path.exists():
            raise MigrationError(
                f"Old logs path not found: {self.old_logs_path}"
            )
        
        log_files = sorted(self.old_logs_path.glob("*.md"))
        report.total_found = len(log_files)
        
        if not log_files:
            raise MigrationError("No log files found to migrate")
        
        # Calculate date range
        dates = []
        for f in log_files:
            try:
                day, month, year = f.stem.split("-")
                dates.append(datetime(int(year), int(month), int(day)))
            except Exception:
                continue
        if dates:
            report.date_range = (min(dates), max(dates))
        
        # Create destination directory
        if not dry_run:
            self.new_logs_path.mkdir(parents=True, exist_ok=True)
        
        # Process each file
        for i, src_file in enumerate(log_files):
            if on_progress:
                on_progress(i + 1, len(log_files), src_file.name)
            
            # Validate
            is_valid, issues = self.validate_file(src_file)
            
            if not is_valid:
                report.failed_files.append({
                    "path": src_file.name,
                    "reason": "; ".join(issues)
                })
                continue
            
            if issues:
                report.validation_warnings.append({
                    "path": src_file.name,
                    "issues": issues
                })
            
            # Copy
            if not dry_run:
                dst_file = self.new_logs_path / src_file.name
                try:
                    shutil.copy2(src_file, dst_file)
                    report.successfully_copied += 1
                except Exception as e:
                    report.failed_files.append({
                        "path": src_file.name,
                        "reason": f"Copy failed: {str(e)}"
                    })
            else:
                report.successfully_copied += 1  # Count as success in dry run
        
        # Migrate dashboard
        if self.old_dashboard_path.exists() and not dry_run:
            try:
                shutil.copy2(
                    self.old_dashboard_path, 
                    self.new_dashboard_path
                )
                report.dashboard_migrated = True
                
                # Patch Dataview queries
                patched = self._patch_dashboard_queries(
                    self.new_dashboard_path
                )
                report.dashboard_patched = patched
                
            except Exception as e:
                report.validation_warnings.append({
                    "path": "Nutrition Dashboard.md",
                    "issues": [f"Dashboard migration failed: {str(e)}"]
                })
        elif self.old_dashboard_path.exists():
            report.dashboard_migrated = True  # Would be migrated
            report.dashboard_patched = True
        
        return report
    
    def _patch_dashboard_queries(self, dashboard_path: Path) -> bool:
        """
        Update Dataview query paths in the dashboard.
        
        Changes:
        "Nutrition/Daily Logs" → "Unagi/Daily Logs"
        'Nutrition/Daily Logs' → 'Unagi/Daily Logs'
        dv.page("User Profile") references stay unchanged
        """
        try:
            content = dashboard_path.read_text(encoding='utf-8')
            
            # Replace all variations of the old path
            patched = content.replace(
                '"Nutrition/Daily Logs"',
                '"Unagi/Daily Logs"'
            )
            patched = patched.replace(
                "'Nutrition/Daily Logs'",
                "'Unagi/Daily Logs'"
            )
            # Also handle the dv.pages() calls
            patched = patched.replace(
                'dv.pages(\'\"Nutrition/Daily Logs\"\')',
                'dv.pages(\'\"Unagi/Daily Logs\"\')'
            )
            
            if patched != content:
                dashboard_path.write_text(patched, encoding='utf-8')
                return True
            
            return False  # No changes needed
            
        except Exception:
            return False
    
    def delete_originals(self) -> bool:
        """
        Delete the original Nutrition/ folder structure.
        Only called after user explicitly confirms.
        
        Returns True if deletion succeeded.
        """
        try:
            if self.old_logs_path.exists():
                shutil.rmtree(self.old_logs_path)
            
            # Check if Nutrition/ folder is now empty
            nutrition_path = self.vault_root / "Nutrition"
            if nutrition_path.exists():
                remaining = list(nutrition_path.iterdir())
                if not remaining:
                    nutrition_path.rmdir()
                # If dashboard was in Nutrition/ root, remove it too
                if self.old_dashboard_path.exists():
                    self.old_dashboard_path.unlink()
                # If Nutrition/ is now empty, remove it
                remaining = list(nutrition_path.iterdir())
                if not remaining:
                    nutrition_path.rmdir()
            
            return True
        except Exception as e:
            print(f"Warning: Could not delete originals: {str(e)}")
            return False
    
    def get_files_to_migrate(self) -> List[Path]:
        """
        Get list of files in old structure that don't exist in new structure.
        Used by /migrate command to find newly added files since last migration.
        """
        if not self.old_logs_path.exists():
            return []
        
        old_files = set(f.name for f in self.old_logs_path.glob("*.md"))
        new_files = set(
            f.name for f in self.new_logs_path.glob("*.md")
        ) if self.new_logs_path.exists() else set()
        
        unmigrated = old_files - new_files
        return [self.old_logs_path / f for f in sorted(unmigrated)]
```

---

## File: `migration/__init__.py`

```python
"""Migration module for Unagi vault structure."""
from .migrator import VaultMigrator, MigrationReport, MigrationError

__all__ = ["VaultMigrator", "MigrationReport", "MigrationError"]
```

---

## Integration Points

### In `main.py` — Auto-detect on first run

```python
# In main(), after config loading, before onboarding:
from migration import VaultMigrator

migrator = VaultMigrator(settings.vault_root)
detection = migrator.detect()

if detection.get("has_old_structure"):
    count = detection["log_count"]
    date_range = detection.get("date_range")
    
    print(f"\n📁 Found {count} existing log files")
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
```

### Migration flow helper

```python
def _run_migration_flow(migrator: VaultMigrator, settings) -> bool:
    """
    Run the interactive migration flow.
    Returns True if migration completed successfully.
    """
    from git_manager.commits import GitManager
    
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
            git = GitManager(settings)
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
                    git = GitManager(settings)
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
```

### Git commits for migration

Add these methods to `GitManager`:

```python
def commit_migration(self, report: 'MigrationReport') -> bool:
    """Commit all migrated files in a single commit."""
    if not self.settings.git_enabled or self.repo is None:
        return False
    
    try:
        # Stage all new files in Unagi/Daily Logs/
        unagi_path = Path(self.settings.vault_root) / "Unagi"
        rel_path = unagi_path.relative_to(Path(self.settings.vault_root))
        self.repo.index.add([str(rel_path)])
        
        from datetime import datetime
        date_str = datetime.now().strftime("%Y-%m-%d")
        commit_msg = (
            f"[unagi] migrate: {report.successfully_copied} log files "
            f"from Nutrition/ → Unagi/ ({date_str})"
        )
        
        author = Actor(
            self.settings.git_author_name,
            self.settings.git_author_email
        )
        self.repo.index.commit(commit_msg, author=author)
        
        if self.settings.git_auto_push and self.settings.git_remote_url:
            self._push_with_feedback()
        
        return True
    except Exception as e:
        print(f"Warning: Migration commit failed: {str(e)}")
        return False

def commit_deletion(self) -> bool:
    """Commit deletion of original Nutrition/ folder."""
    if not self.settings.git_enabled or self.repo is None:
        return False
    
    try:
        self.repo.index.add(["-u"])  # Stage deletions
        author = Actor(
            self.settings.git_author_name,
            self.settings.git_author_email
        )
        self.repo.index.commit(
            "[unagi] cleanup: removed original Nutrition/ folder after migration",
            author=author
        )
        return True
    except Exception:
        return False
```

### `/migrate` command in CLI

Add to the command handler in both `ui/cli.py` (simple) and `ui/screens/main.py` (Textual):

```python
elif cmd.startswith('/migrate'):
    from migration import VaultMigrator
    migrator = VaultMigrator(self.settings.vault_root)
    
    # Check for --cleanup flag
    if '--cleanup' in cmd:
        detection = migrator.detect()
        if not detection.get("has_old_structure"):
            print("No original files to clean up.")
            return
        confirm = input(
            "Delete original Nutrition/ files? (yes/no) "
        ).strip().lower()
        if confirm in ['yes', 'y']:
            migrator.delete_originals()
            print("✅ Originals deleted")
        return
    
    # Standard migration
    detection = migrator.detect()
    if not detection.get("has_old_structure"):
        # Check for files added since last migration
        new_files = migrator.get_files_to_migrate()
        if new_files:
            print(
                f"Found {len(new_files)} new files "
                f"not yet in Unagi/Daily Logs/"
            )
            _run_migration_flow(migrator, self.settings)
        else:
            print("✅ All files already migrated. Nothing to do.")
        return
    
    _run_migration_flow(migrator, self.settings)
```

---

## Edge Cases

| Scenario | Handling |
|---|---|
| File exists in both old and new locations | Skip — don't overwrite newer file in Unagi/ |
| Filename doesn't match DD-MM-YYYY format | Validate and warn — migrate anyway if frontmatter is parseable |
| Frontmatter date doesn't match filename date | Warn and log to report — migrate anyway, flag for manual review |
| File is completely empty | Skip — add to failed list |
| File has no frontmatter at all | Skip — add to failed list |
| Dashboard doesn't exist | Skip dashboard step silently |
| Migration runs twice | Second run only copies files not already in Unagi/ |
| User cancels mid-migration | Partial migration is safe — no originals deleted, Unagi/ has whatever was copied |
| Git repo not initialized | Migration runs without git commit, warning shown |

---

## New File Structure

```
unagi/
└── migration/
    ├── __init__.py          ← exports VaultMigrator, MigrationReport
    └── migrator.py          ← VaultMigrator class (full implementation above)
```

---

## Testing Checklist

- [ ] `detect()` correctly identifies old vault structure
- [ ] `detect()` returns `has_old_structure: False` when already migrated
- [ ] `validate_file()` catches missing `date` field as fatal error
- [ ] `validate_file()` catches non-integer `calories` as warning (not fatal)
- [ ] `validate_file()` flags date mismatch between filename and frontmatter
- [ ] `migrate(dry_run=True)` counts files correctly without touching disk
- [ ] `migrate()` copies all valid files to `Unagi/Daily Logs/`
- [ ] `migrate()` does NOT copy files with fatal validation errors
- [ ] Dashboard Dataview queries are patched from `Nutrition/Daily Logs` to `Unagi/Daily Logs`
- [ ] Original files are NOT deleted after migration
- [ ] `delete_originals()` removes `Nutrition/Daily Logs/` folder
- [ ] `delete_originals()` removes `Nutrition/` if it becomes empty
- [ ] Git commit message matches format: `[unagi] migrate: N log files...`
- [ ] `/migrate` command shows "nothing to do" when already migrated
- [ ] `/migrate` command finds and migrates files added since last migration
- [ ] `/migrate --cleanup` offers to delete originals
- [ ] Running migration twice doesn't overwrite files in `Unagi/`
- [ ] Progress bar displays correctly during migration

---

*Unagi Migration Spec v1 — Built with 🐍 total food awareness.*
