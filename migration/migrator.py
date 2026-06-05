"""Vault migration from old Nutrition/ structure to new Unagi/ structure."""
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import shutil
import frontmatter


class MigrationError(Exception):
    """Raised when migration cannot proceed."""
    pass


class MigrationReport:
    """Holds the results of a migration run."""
    
    def __init__(self):
        self.total_found: int = 0
        self.successfully_copied: int = 0
        self.failed_files: List[Dict] = []      # [{path, reason}]
        self.validation_warnings: List[Dict] = [] # [{path, issues}]
        self.dashboard_migrated: bool = False
        self.dashboard_patched: bool = False
        self.date_range: Optional[Tuple[datetime, datetime]] = None
    
    def has_issues(self) -> bool:
        """Check if there are any failed files."""
        return len(self.failed_files) > 0
    
    def summary(self) -> str:
        """Generate a human-readable summary of the migration."""
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
                # Ensure Unagi directory exists
                self.new_dashboard_path.parent.mkdir(parents=True, exist_ok=True)
                
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
                'dv.pages(\'"Nutrition/Daily Logs"\')',
                'dv.pages(\'"Unagi/Daily Logs"\')'
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

# Made with Bob
