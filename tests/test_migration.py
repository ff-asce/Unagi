"""Test migration functionality."""
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from migration import VaultMigrator, MigrationReport


def create_test_vault():
    """Create a temporary test vault with old structure."""
    temp_dir = tempfile.mkdtemp()
    vault_path = Path(temp_dir)
    
    # Create old structure
    old_logs = vault_path / "Nutrition" / "Daily Logs"
    old_logs.mkdir(parents=True)
    
    # Create sample log files
    sample_log = """---
date: 2026-05-25
calories: 1250
maintenance: 2200
deficit: -950
protein: 140
carbs: 85
fats: 45
fiber: 28
breakfast: "—"
lunch: "450g Chicken Breast + 150g Amul Masti Dahi"
dinner: "200g Palak Paneer + 140g Basmati Rice"
misc: "Soaked seeds (18g Chia + 6g Basil)"
---

# Daily Log — 25 May 2026

Strong day. Hit protein target and maintained good deficit.
"""
    
    # Create 3 test files
    dates = [
        ("25-05-2026", "2026-05-25"),
        ("26-05-2026", "2026-05-26"),
        ("27-05-2026", "2026-05-27")
    ]
    
    for filename, date in dates:
        log_file = old_logs / f"{filename}.md"
        content = sample_log.replace("2026-05-25", date).replace("25 May 2026", 
                                                                   datetime.strptime(date, "%Y-%m-%d").strftime("%d %b %Y"))
        log_file.write_text(content)
    
    # Create dashboard
    dashboard = vault_path / "Nutrition" / "Nutrition Dashboard.md"
    dashboard.write_text("""# Nutrition Dashboard

```dataview
TABLE calories, protein, deficit
FROM "Nutrition/Daily Logs"
SORT date DESC
LIMIT 7
```
""")
    
    return temp_dir


def test_detection():
    """Test detection of old vault structure."""
    print("\n=== Test 1: Detection ===")
    temp_dir = create_test_vault()
    
    try:
        migrator = VaultMigrator(temp_dir)
        detection = migrator.detect()
        
        assert detection["has_old_structure"] == True
        assert detection["log_count"] == 3
        assert detection["has_dashboard"] == True
        assert detection["date_range"] is not None
        
        print("✅ Detection works correctly")
        print(f"   Found {detection['log_count']} files")
        print(f"   Dashboard: {detection['has_dashboard']}")
        
    finally:
        shutil.rmtree(temp_dir)


def test_validation():
    """Test file validation."""
    print("\n=== Test 2: Validation ===")
    temp_dir = create_test_vault()
    
    try:
        migrator = VaultMigrator(temp_dir)
        old_logs = Path(temp_dir) / "Nutrition" / "Daily Logs"
        
        # Test valid file
        valid_file = old_logs / "25-05-2026.md"
        is_valid, issues = migrator.validate_file(valid_file)
        assert is_valid == True
        print(f"✅ Valid file passes: {valid_file.name}")
        
        # Create invalid file (missing date field)
        invalid_file = old_logs / "28-05-2026.md"
        invalid_file.write_text("""---
calories: 1250
protein: 140
---

# Test
""")
        is_valid, issues = migrator.validate_file(invalid_file)
        assert is_valid == False
        assert "date" in str(issues)
        print(f"✅ Invalid file rejected: {invalid_file.name}")
        print(f"   Reason: {issues[0]}")
        
    finally:
        shutil.rmtree(temp_dir)


def test_dry_run():
    """Test dry run migration."""
    print("\n=== Test 3: Dry Run ===")
    temp_dir = create_test_vault()
    
    try:
        migrator = VaultMigrator(temp_dir)
        report = migrator.migrate(dry_run=True)
        
        assert report.total_found == 3
        assert report.successfully_copied == 3
        assert report.dashboard_migrated == True
        
        # Verify nothing was actually copied
        new_logs = Path(temp_dir) / "Unagi" / "Daily Logs"
        assert not new_logs.exists()
        
        print("✅ Dry run works correctly")
        print(f"   Would migrate: {report.successfully_copied}/{report.total_found} files")
        
    finally:
        shutil.rmtree(temp_dir)


def test_actual_migration():
    """Test actual migration."""
    print("\n=== Test 4: Actual Migration ===")
    temp_dir = create_test_vault()
    
    try:
        migrator = VaultMigrator(temp_dir)
        
        # Run migration
        report = migrator.migrate(dry_run=False)
        
        assert report.successfully_copied == 3
        assert report.dashboard_migrated == True
        assert report.dashboard_patched == True
        
        # Verify files were copied
        new_logs = Path(temp_dir) / "Unagi" / "Daily Logs"
        assert new_logs.exists()
        assert len(list(new_logs.glob("*.md"))) == 3
        
        # Verify dashboard was patched
        new_dashboard = Path(temp_dir) / "Unagi" / "Nutrition Dashboard.md"
        assert new_dashboard.exists()
        content = new_dashboard.read_text()
        assert "Unagi/Daily Logs" in content
        assert "Nutrition/Daily Logs" not in content
        
        # Verify originals still exist
        old_logs = Path(temp_dir) / "Nutrition" / "Daily Logs"
        assert old_logs.exists()
        
        print("✅ Migration successful")
        print(f"   Migrated: {report.successfully_copied} files")
        print(f"   Dashboard patched: {report.dashboard_patched}")
        print(f"\n{report.summary()}")
        
    finally:
        shutil.rmtree(temp_dir)


def test_deletion():
    """Test deletion of originals."""
    print("\n=== Test 5: Deletion ===")
    temp_dir = create_test_vault()
    
    try:
        migrator = VaultMigrator(temp_dir)
        
        # Migrate first
        migrator.migrate(dry_run=False)
        
        # Delete originals
        success = migrator.delete_originals()
        assert success == True
        
        # Verify originals are gone
        old_logs = Path(temp_dir) / "Nutrition" / "Daily Logs"
        assert not old_logs.exists()
        
        # Verify new files still exist
        new_logs = Path(temp_dir) / "Unagi" / "Daily Logs"
        assert new_logs.exists()
        assert len(list(new_logs.glob("*.md"))) == 3
        
        print("✅ Deletion successful")
        print("   Original files removed")
        print("   Migrated files preserved")
        
    finally:
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    print("🐍 Testing Unagi Migration")
    print("=" * 50)
    
    test_detection()
    test_validation()
    test_dry_run()
    test_actual_migration()
    test_deletion()
    
    print("\n" + "=" * 50)
    print("✅ All migration tests passed!")

# Made with Bob
