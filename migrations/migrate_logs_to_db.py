"""Migration script to import existing markdown logs into database and vector store."""
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_settings
from vault import get_vault_reader
from memory.database import MemoryDatabase
from memory.vector_store import VectorStore
from memory.embeddings import generate_embedding


async def migrate_logs():
    """Migrate all existing markdown logs to database and vector store."""
    print("🐍 UNAGI Log Migration")
    print("=" * 50)
    
    # Initialize components
    settings = get_settings()
    reader = get_vault_reader()
    
    db_path = settings.vault_path / "memory.db"
    vector_path = settings.vault_path / "vector_store"
    
    print(f"\nDatabase path: {db_path}")
    print(f"Vector store path: {vector_path}")
    
    # Check if database already exists
    if db_path.exists():
        response = input("\n⚠️  Database already exists. Overwrite? (yes/no): ")
        if response.lower() != 'yes':
            print("Migration cancelled.")
            return
        db_path.unlink()
    
    # Initialize database and vector store
    print("\n📦 Initializing database and vector store...")
    memory_db = MemoryDatabase(db_path)
    vector_store = VectorStore(vector_path)
    
    # Initialize database schema
    await memory_db.initialize()
    print("✓ Database schema created")
    
    # Get all log files
    logs_path = settings.get_logs_path()
    if not logs_path.exists():
        print(f"\n❌ Logs directory not found: {logs_path}")
        return
    
    log_files = sorted(logs_path.glob("*.md"))
    print(f"\n📄 Found {len(log_files)} log files")
    
    if not log_files:
        print("No logs to migrate.")
        return
    
    # Migrate each log
    migrated = 0
    failed = 0
    
    print("\n🔄 Migrating logs...")
    for log_file in log_files:
        try:
            # Extract date from filename (YYYY-MM-DD.md)
            date_str = log_file.stem
            date = datetime.strptime(date_str, "%Y-%m-%d")
            
            # Read log data
            log_data = reader.read_daily_log(date)
            if not log_data:
                print(f"  ⚠️  Skipping {date_str}: Could not parse")
                failed += 1
                continue
            
            # Prepare data for database
            db_data = {
                'date': date.date().isoformat(),
                'calories': log_data.get('calories'),
                'protein': log_data.get('protein'),
                'carbs': log_data.get('carbs'),
                'fats': log_data.get('fats'),
                'fiber': log_data.get('fiber'),
                'water_ml': log_data.get('water_ml'),
                'weight_kg': log_data.get('weight_kg'),
                'goal_calories': log_data.get('goal_calories'),
                'goal_protein': log_data.get('goal_protein'),
                'goal_carbs': log_data.get('goal_carbs'),
                'goal_fats': log_data.get('goal_fats'),
                'notes': log_data.get('notes'),
                'meals': log_data.get('meals', [])
            }
            
            # Insert into database
            log_id = await memory_db.insert_log(db_data)
            
            # Read full markdown content for embedding
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Generate embedding and add to vector store
            embedding = generate_embedding(content)
            await vector_store.add_document(
                doc_id=f"log_{date_str}",
                text=content,
                embedding=embedding,
                metadata={
                    'date': date_str,
                    'log_id': log_id,
                    'type': 'daily_log'
                }
            )
            
            migrated += 1
            print(f"  ✓ {date_str}")
            
        except Exception as e:
            print(f"  ❌ {log_file.name}: {str(e)}")
            failed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"✅ Migration complete!")
    print(f"   Migrated: {migrated}")
    print(f"   Failed: {failed}")
    print(f"   Total: {len(log_files)}")
    
    # Verify
    print("\n🔍 Verifying migration...")
    async with memory_db.get_connection() as conn:
        cursor = await conn.execute("SELECT COUNT(*) FROM daily_logs")
        count = await cursor.fetchone()
        print(f"   Database records: {count[0]}")
    
    vector_count = await vector_store.count()
    print(f"   Vector store documents: {vector_count}")
    
    if count[0] == migrated and vector_count == migrated:
        print("\n✅ Verification passed!")
    else:
        print("\n⚠️  Verification warning: Counts don't match")


def main():
    """Run the migration."""
    try:
        asyncio.run(migrate_logs())
    except KeyboardInterrupt:
        print("\n\n⚠️  Migration interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

# Made with Bob
