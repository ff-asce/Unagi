"""SQLite database for structured memory storage."""
import sqlite3
import asyncio
from datetime import date, datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class Database:
    """SQLite database manager for Unagi's structured memory."""
    
    def __init__(self, db_path: str):
        """Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = None
        
    def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
        return self._conn
    
    async def initialize(self):
        """Create database schema if it doesn't exist."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Daily logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE UNIQUE NOT NULL,
                calories INTEGER,
                maintenance INTEGER,
                deficit INTEGER,
                protein INTEGER,
                carbs INTEGER,
                fats INTEGER,
                fiber INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Meals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_id INTEGER NOT NULL,
                meal_type TEXT NOT NULL,
                time TEXT,
                description TEXT NOT NULL,
                FOREIGN KEY (log_id) REFERENCES daily_logs(id)
            )
        """)
        
        # Food items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS food_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                brand TEXT,
                serving_size TEXT,
                calories REAL,
                protein REAL,
                carbs REAL,
                fats REAL,
                fiber REAL,
                confidence_score REAL,
                source TEXT,
                usda_fdc_id TEXT,
                last_used DATE,
                use_count INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Micronutrients table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS micronutrients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_id INTEGER NOT NULL,
                nutrient_name TEXT NOT NULL,
                amount REAL,
                unit TEXT,
                status TEXT,
                FOREIGN KEY (log_id) REFERENCES daily_logs(id)
            )
        """)
        
        # User patterns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                pattern_key TEXT NOT NULL,
                pattern_value TEXT NOT NULL,
                confidence REAL,
                occurrences INTEGER DEFAULT 1,
                last_seen DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(pattern_type, pattern_key)
            )
        """)
        
        # Trends table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trend_type TEXT NOT NULL,
                metric TEXT NOT NULL,
                start_date DATE,
                end_date DATE,
                severity TEXT,
                description TEXT,
                acknowledged BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_logs_date ON daily_logs(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_meals_log_id ON meals(log_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_food_items_name ON food_items(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_food_items_last_used ON food_items(last_used)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_micronutrients_log_id ON micronutrients(log_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_patterns_type_key ON user_patterns(pattern_type, pattern_key)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trends_type ON trends(trend_type)")
        
        conn.commit()
        logger.info(f"Database initialized at {self.db_path}")
    
    async def insert_log(self, log_data: Dict[str, Any]) -> int:
        """Insert a new daily log.
        
        Args:
            log_data: Dictionary containing log data
            
        Returns:
            ID of inserted log
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO daily_logs (date, calories, maintenance, deficit, protein, carbs, fats, fiber)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            log_data['date'],
            log_data.get('calories'),
            log_data.get('maintenance'),
            log_data.get('deficit'),
            log_data.get('protein'),
            log_data.get('carbs'),
            log_data.get('fats'),
            log_data.get('fiber')
        ))
        
        log_id = cursor.lastrowid
        
        # Insert meals
        for meal_type in ['breakfast', 'lunch', 'dinner', 'misc']:
            meal_desc = log_data.get(meal_type)
            if meal_desc and meal_desc != '—':
                # Extract time if present
                time = None
                if ' - ' in meal_desc:
                    time, meal_desc = meal_desc.split(' - ', 1)
                
                cursor.execute("""
                    INSERT INTO meals (log_id, meal_type, time, description)
                    VALUES (?, ?, ?, ?)
                """, (log_id, meal_type, time, meal_desc))
        
        conn.commit()
        return log_id
    
    async def update_log(self, log_date: str, log_data: Dict[str, Any]):
        """Update an existing log.
        
        Args:
            log_date: Date of log to update (YYYY-MM-DD)
            log_data: Updated log data
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE daily_logs
            SET calories = ?, maintenance = ?, deficit = ?, protein = ?, carbs = ?, fats = ?, fiber = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE date = ?
        """, (
            log_data.get('calories'),
            log_data.get('maintenance'),
            log_data.get('deficit'),
            log_data.get('protein'),
            log_data.get('carbs'),
            log_data.get('fats'),
            log_data.get('fiber'),
            log_date
        ))
        
        # Get log_id
        cursor.execute("SELECT id FROM daily_logs WHERE date = ?", (log_date,))
        row = cursor.fetchone()
        if row:
            log_id = row['id']
            
            # Delete old meals
            cursor.execute("DELETE FROM meals WHERE log_id = ?", (log_id,))
            
            # Insert updated meals
            for meal_type in ['breakfast', 'lunch', 'dinner', 'misc']:
                meal_desc = log_data.get(meal_type)
                if meal_desc and meal_desc != '—':
                    time = None
                    if ' - ' in meal_desc:
                        time, meal_desc = meal_desc.split(' - ', 1)
                    
                    cursor.execute("""
                        INSERT INTO meals (log_id, meal_type, time, description)
                        VALUES (?, ?, ?, ?)
                    """, (log_id, meal_type, time, meal_desc))
        
        conn.commit()
    
    async def get_log(self, log_date: str) -> Optional[Dict[str, Any]]:
        """Get a log by date.
        
        Args:
            log_date: Date in YYYY-MM-DD format
            
        Returns:
            Log data dictionary or None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM daily_logs WHERE date = ?", (log_date,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        log_data = dict(row)
        
        # Get meals
        cursor.execute("SELECT * FROM meals WHERE log_id = ?", (log_data['id'],))
        meals = cursor.fetchall()
        
        for meal in meals:
            meal_type = meal['meal_type']
            time = meal['time'] or ''
            desc = meal['description']
            log_data[meal_type] = f"{time} - {desc}" if time else desc
        
        return log_data
    
    async def query_logs(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Query logs in a date range.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            List of log dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM daily_logs
            WHERE date BETWEEN ? AND ?
            ORDER BY date DESC
        """, (start_date, end_date))
        
        logs = []
        for row in cursor.fetchall():
            log_data = dict(row)
            
            # Get meals
            cursor.execute("SELECT * FROM meals WHERE log_id = ?", (log_data['id'],))
            meals = cursor.fetchall()
            
            for meal in meals:
                meal_type = meal['meal_type']
                time = meal['time'] or ''
                desc = meal['description']
                log_data[meal_type] = f"{time} - {desc}" if time else desc
            
            logs.append(log_data)
        
        return logs
    
    async def learn_food_item(self, food_data: Dict[str, Any]):
        """Add or update a food item in the knowledge base.
        
        Args:
            food_data: Food item data
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Check if exists
        cursor.execute("""
            SELECT id, use_count FROM food_items
            WHERE name = ? AND (brand = ? OR (brand IS NULL AND ? IS NULL))
        """, (food_data['name'], food_data.get('brand'), food_data.get('brand')))
        
        row = cursor.fetchone()
        
        if row:
            # Update existing
            cursor.execute("""
                UPDATE food_items
                SET use_count = ?, last_used = ?, confidence_score = ?
                WHERE id = ?
            """, (row['use_count'] + 1, date.today().isoformat(), food_data.get('confidence_score', 0.5), row['id']))
        else:
            # Insert new
            cursor.execute("""
                INSERT INTO food_items (name, brand, serving_size, calories, protein, carbs, fats, fiber,
                                       confidence_score, source, usda_fdc_id, last_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                food_data['name'],
                food_data.get('brand'),
                food_data.get('serving_size'),
                food_data.get('calories'),
                food_data.get('protein'),
                food_data.get('carbs'),
                food_data.get('fats'),
                food_data.get('fiber'),
                food_data.get('confidence_score', 0.5),
                food_data.get('source', 'llm'),
                food_data.get('usda_fdc_id'),
                date.today().isoformat()
            ))
        
        conn.commit()
    
    async def get_similar_foods(self, name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find similar food items.
        
        Args:
            name: Food name to search for
            limit: Maximum results
            
        Returns:
            List of similar food items
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM food_items
            WHERE name LIKE ?
            ORDER BY use_count DESC, confidence_score DESC
            LIMIT ?
        """, (f"%{name}%", limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    async def record_pattern(self, pattern_type: str, pattern_key: str, pattern_value: str, confidence: float = 0.5):
        """Record or update a user pattern.
        
        Args:
            pattern_type: Type of pattern (common_meal, brand_preference, portion_size)
            pattern_key: Pattern identifier
            pattern_value: Pattern data (JSON string)
            confidence: Confidence score
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO user_patterns (pattern_type, pattern_key, pattern_value, confidence, occurrences, last_seen)
            VALUES (?, ?, ?, ?, 1, ?)
            ON CONFLICT(pattern_type, pattern_key) DO UPDATE SET
                occurrences = occurrences + 1,
                last_seen = ?,
                confidence = ?
        """, (pattern_type, pattern_key, pattern_value, confidence, date.today().isoformat(),
              date.today().isoformat(), confidence))
        
        conn.commit()
    
    async def get_patterns(self, pattern_type: str) -> List[Dict[str, Any]]:
        """Get patterns of a specific type.
        
        Args:
            pattern_type: Type of pattern to retrieve
            
        Returns:
            List of patterns
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM user_patterns
            WHERE pattern_type = ?
            ORDER BY occurrences DESC, confidence DESC
        """, (pattern_type,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    async def record_trend(self, trend_data: Dict[str, Any]):
        """Record a detected trend.
        
        Args:
            trend_data: Trend information
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO trends (trend_type, metric, start_date, end_date, severity, description)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            trend_data['trend_type'],
            trend_data['metric'],
            trend_data['start_date'],
            trend_data['end_date'],
            trend_data['severity'],
            trend_data['description']
        ))
        
        conn.commit()
    
    async def get_unacknowledged_trends(self) -> List[Dict[str, Any]]:
        """Get trends that haven't been acknowledged.
        
        Returns:
            List of unacknowledged trends
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM trends
            WHERE acknowledged = FALSE
            ORDER BY severity DESC, created_at DESC
        """)
        
        return [dict(row) for row in cursor.fetchall()]
    
    async def acknowledge_trend(self, trend_id: int):
        """Mark a trend as acknowledged.
        
        Args:
            trend_id: ID of trend to acknowledge
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE trends SET acknowledged = TRUE WHERE id = ?", (trend_id,))
        conn.commit()
    
    def close(self):
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

# Made with Bob
