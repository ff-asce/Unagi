"""Pattern learning from historical data."""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter, defaultdict
import statistics

from memory.database import MemoryDatabase


class PatternLearner:
    """Learn patterns from user's historical nutrition data."""
    
    def __init__(self, database: MemoryDatabase):
        """Initialize pattern learner.
        
        Args:
            database: Memory database instance
        """
        self.db = database
    
    async def learn_meal_patterns(self, days: int = 30) -> Dict[str, Any]:
        """Learn meal timing and frequency patterns.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with meal patterns:
            - meal_times: Average time for each meal type
            - meal_frequency: How often each meal type occurs
            - typical_meals: Most common meals for each type
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get all meals from the period
        async with self.db.get_connection() as conn:
            cursor = await conn.execute("""
                SELECT m.meal_type, m.time, m.items
                FROM meals m
                JOIN daily_logs l ON m.log_id = l.id
                WHERE l.date >= ?
                ORDER BY l.date, m.time
            """, (cutoff_date.date().isoformat(),))
            meals = await cursor.fetchall()
        
        if not meals:
            return {
                'meal_times': {},
                'meal_frequency': {},
                'typical_meals': {}
            }
        
        # Analyze patterns
        meal_times = defaultdict(list)
        meal_counts = Counter()
        meal_items = defaultdict(list)
        
        for meal_type, time_str, items in meals:
            meal_counts[meal_type] += 1
            
            # Parse time
            try:
                time_obj = datetime.strptime(time_str, "%H:%M").time()
                meal_times[meal_type].append(time_obj.hour * 60 + time_obj.minute)
            except ValueError:
                continue
            
            # Track items
            if items:
                meal_items[meal_type].append(items)
        
        # Calculate average times
        avg_times = {}
        for meal_type, minutes_list in meal_times.items():
            if minutes_list:
                avg_minutes = int(statistics.mean(minutes_list))
                hours = avg_minutes // 60
                mins = avg_minutes % 60
                avg_times[meal_type] = f"{hours:02d}:{mins:02d}"
        
        # Calculate frequency (meals per week)
        frequency = {}
        weeks = days / 7
        for meal_type, count in meal_counts.items():
            frequency[meal_type] = round(count / weeks, 1)
        
        # Find typical meals (most common items)
        typical = {}
        for meal_type, items_list in meal_items.items():
            # Flatten and count all items
            all_items = []
            for items_str in items_list:
                all_items.extend([item.strip() for item in items_str.split(',')])
            
            if all_items:
                item_counts = Counter(all_items)
                typical[meal_type] = [item for item, _ in item_counts.most_common(5)]
        
        return {
            'meal_times': avg_times,
            'meal_frequency': frequency,
            'typical_meals': typical
        }
    
    async def learn_nutrient_patterns(self, days: int = 30) -> Dict[str, Any]:
        """Learn typical nutrient intake patterns.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with nutrient patterns:
            - averages: Average daily intake for each nutrient
            - ranges: Min/max ranges for each nutrient
            - consistency: Standard deviation (lower = more consistent)
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get all daily totals
        async with self.db.get_connection() as conn:
            cursor = await conn.execute("""
                SELECT calories, protein, carbs, fats, fiber
                FROM daily_logs
                WHERE date >= ?
                ORDER BY date
            """, (cutoff_date.date().isoformat(),))
            logs = await cursor.fetchall()
        
        if not logs:
            return {
                'averages': {},
                'ranges': {},
                'consistency': {}
            }
        
        # Organize by nutrient
        nutrients = {
            'calories': [log[0] for log in logs if log[0] is not None],
            'protein': [log[1] for log in logs if log[1] is not None],
            'carbs': [log[2] for log in logs if log[2] is not None],
            'fats': [log[3] for log in logs if log[3] is not None],
            'fiber': [log[4] for log in logs if log[4] is not None]
        }
        
        # Calculate statistics
        averages = {}
        ranges = {}
        consistency = {}
        
        for nutrient, values in nutrients.items():
            if values:
                averages[nutrient] = round(statistics.mean(values), 1)
                ranges[nutrient] = {
                    'min': round(min(values), 1),
                    'max': round(max(values), 1)
                }
                if len(values) > 1:
                    consistency[nutrient] = round(statistics.stdev(values), 1)
                else:
                    consistency[nutrient] = 0.0
        
        return {
            'averages': averages,
            'ranges': ranges,
            'consistency': consistency
        }
    
    async def learn_ingredient_preferences(self, days: int = 90) -> Dict[str, Any]:
        """Learn which ingredients user frequently uses.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with ingredient preferences:
            - frequent_ingredients: Most used ingredients with counts
            - ingredient_combinations: Common ingredient pairs
            - meal_type_preferences: Ingredients by meal type
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get all meals with items
        async with self.db.get_connection() as conn:
            cursor = await conn.execute("""
                SELECT m.meal_type, m.items
                FROM meals m
                JOIN daily_logs l ON m.log_id = l.id
                WHERE l.date >= ? AND m.items IS NOT NULL
            """, (cutoff_date.date().isoformat(),))
            meals = await cursor.fetchall()
        
        if not meals:
            return {
                'frequent_ingredients': [],
                'ingredient_combinations': [],
                'meal_type_preferences': {}
            }
        
        # Parse ingredients
        all_ingredients = []
        meal_type_ingredients = defaultdict(list)
        ingredient_pairs = []
        
        for meal_type, items_str in meals:
            items = [item.strip().lower() for item in items_str.split(',')]
            all_ingredients.extend(items)
            meal_type_ingredients[meal_type].extend(items)
            
            # Track pairs
            for i in range(len(items)):
                for j in range(i + 1, len(items)):
                    pair = tuple(sorted([items[i], items[j]]))
                    ingredient_pairs.append(pair)
        
        # Count frequencies
        ingredient_counts = Counter(all_ingredients)
        pair_counts = Counter(ingredient_pairs)
        
        # Format results
        frequent = [
            {'ingredient': ing, 'count': count}
            for ing, count in ingredient_counts.most_common(20)
        ]
        
        combinations = [
            {'ingredients': list(pair), 'count': count}
            for pair, count in pair_counts.most_common(10)
        ]
        
        meal_preferences = {}
        for meal_type, ingredients in meal_type_ingredients.items():
            counts = Counter(ingredients)
            meal_preferences[meal_type] = [
                {'ingredient': ing, 'count': count}
                for ing, count in counts.most_common(10)
            ]
        
        return {
            'frequent_ingredients': frequent,
            'ingredient_combinations': combinations,
            'meal_type_preferences': meal_preferences
        }
    
    async def learn_goal_progress(self, days: int = 30) -> Dict[str, Any]:
        """Analyze progress toward nutrition goals.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with goal progress:
            - goal_achievement_rate: % of days goals were met
            - average_deviation: How far off from goals on average
            - improving_trend: Whether user is getting closer to goals
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get logs with goals
        async with self.db.get_connection() as conn:
            cursor = await conn.execute("""
                SELECT date, calories, protein, carbs, fats,
                       goal_calories, goal_protein, goal_carbs, goal_fats
                FROM daily_logs
                WHERE date >= ? AND goal_calories IS NOT NULL
                ORDER BY date
            """, (cutoff_date.date().isoformat(),))
            logs = await cursor.fetchall()
        
        if not logs:
            return {
                'goal_achievement_rate': {},
                'average_deviation': {},
                'improving_trend': None
            }
        
        # Analyze goal achievement
        nutrients = ['calories', 'protein', 'carbs', 'fats']
        achievement_counts = {n: 0 for n in nutrients}
        deviations = {n: [] for n in nutrients}
        
        for log in logs:
            date, cal, prot, carb, fat, g_cal, g_prot, g_carb, g_fat = log
            actuals = [cal, prot, carb, fat]
            goals = [g_cal, g_prot, g_carb, g_fat]
            
            for i, nutrient in enumerate(nutrients):
                if actuals[i] is not None and goals[i] is not None:
                    # Within 10% is considered "achieved"
                    deviation = abs(actuals[i] - goals[i]) / goals[i]
                    deviations[nutrient].append(deviation * 100)
                    
                    if deviation <= 0.1:
                        achievement_counts[nutrient] += 1
        
        # Calculate rates
        total_days = len(logs)
        achievement_rate = {
            n: round((count / total_days) * 100, 1)
            for n, count in achievement_counts.items()
        }
        
        # Calculate average deviation
        avg_deviation = {
            n: round(statistics.mean(devs), 1) if devs else 0.0
            for n, devs in deviations.items()
        }
        
        # Check for improving trend (compare first half vs second half)
        improving = None
        if len(logs) >= 14:  # Need at least 2 weeks
            mid = len(logs) // 2
            first_half_devs = []
            second_half_devs = []
            
            for i, log in enumerate(logs):
                _, cal, prot, carb, fat, g_cal, g_prot, g_carb, g_fat = log
                if cal and g_cal:
                    dev = abs(cal - g_cal) / g_cal
                    if i < mid:
                        first_half_devs.append(dev)
                    else:
                        second_half_devs.append(dev)
            
            if first_half_devs and second_half_devs:
                first_avg = statistics.mean(first_half_devs)
                second_avg = statistics.mean(second_half_devs)
                improving = second_avg < first_avg
        
        return {
            'goal_achievement_rate': achievement_rate,
            'average_deviation': avg_deviation,
            'improving_trend': improving
        }
    
    async def get_all_patterns(self) -> Dict[str, Any]:
        """Get all learned patterns in one call.
        
        Returns:
            Dictionary with all pattern types
        """
        meal_patterns, nutrient_patterns, ingredient_prefs, goal_progress = await asyncio.gather(
            self.learn_meal_patterns(),
            self.learn_nutrient_patterns(),
            self.learn_ingredient_preferences(),
            self.learn_goal_progress()
        )
        
        return {
            'meal_patterns': meal_patterns,
            'nutrient_patterns': nutrient_patterns,
            'ingredient_preferences': ingredient_prefs,
            'goal_progress': goal_progress,
            'learned_at': datetime.now().isoformat()
        }

# Made with Bob
