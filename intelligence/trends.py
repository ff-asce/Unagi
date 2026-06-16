"""Trend detection from historical data."""
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import statistics

from memory.database import Database


class TrendDetector:
    """Detect trends in nutrition data over time."""
    
    def __init__(self, database: Database):
        """Initialize trend detector.
        
        Args:
            database: Memory database instance
        """
        self.db = database
    
    async def detect_calorie_trend(self, days: int = 30) -> Dict[str, Any]:
        """Detect trend in calorie intake.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with trend information:
            - direction: 'increasing', 'decreasing', or 'stable'
            - change_percent: Percentage change
            - average_daily: Average daily calories
            - recent_average: Average for last 7 days
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        async with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT date, calories
                FROM daily_logs
                WHERE date >= ? AND calories IS NOT NULL
                ORDER BY date
            """, (cutoff_date.date().isoformat(),))
            logs = cursor.fetchall()
        
        if len(logs) < 7:
            return {
                'direction': 'insufficient_data',
                'change_percent': 0.0,
                'average_daily': 0.0,
                'recent_average': 0.0
            }
        
        # Calculate averages
        all_calories = [log[1] for log in logs]
        recent_calories = [log[1] for log in logs[-7:]]
        
        avg_daily = statistics.mean(all_calories)
        recent_avg = statistics.mean(recent_calories)
        
        # Calculate trend
        change_percent = ((recent_avg - avg_daily) / avg_daily) * 100
        
        # Determine direction (>5% change is significant)
        if change_percent > 5:
            direction = 'increasing'
        elif change_percent < -5:
            direction = 'decreasing'
        else:
            direction = 'stable'
        
        return {
            'direction': direction,
            'change_percent': round(change_percent, 1),
            'average_daily': round(avg_daily, 1),
            'recent_average': round(recent_avg, 1)
        }
    
    async def detect_nutrient_trends(self, days: int = 30) -> Dict[str, Dict[str, Any]]:
        """Detect trends for all major nutrients.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with trends for each nutrient
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        async with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT date, protein, carbs, fats, fiber
                FROM daily_logs
                WHERE date >= ?
                ORDER BY date
            """, (cutoff_date.date().isoformat(),))
            logs = cursor.fetchall()
        
        if len(logs) < 7:
            return {
                'protein': {'direction': 'insufficient_data'},
                'carbs': {'direction': 'insufficient_data'},
                'fats': {'direction': 'insufficient_data'},
                'fiber': {'direction': 'insufficient_data'}
            }
        
        nutrients = {
            'protein': [log[1] for log in logs if log[1] is not None],
            'carbs': [log[2] for log in logs if log[2] is not None],
            'fats': [log[3] for log in logs if log[3] is not None],
            'fiber': [log[4] for log in logs if log[4] is not None]
        }
        
        trends = {}
        for nutrient, values in nutrients.items():
            if len(values) < 7:
                trends[nutrient] = {'direction': 'insufficient_data'}
                continue
            
            avg_all = statistics.mean(values)
            avg_recent = statistics.mean(values[-7:])
            change_percent = ((avg_recent - avg_all) / avg_all) * 100
            
            if change_percent > 5:
                direction = 'increasing'
            elif change_percent < -5:
                direction = 'decreasing'
            else:
                direction = 'stable'
            
            trends[nutrient] = {
                'direction': direction,
                'change_percent': round(change_percent, 1),
                'average': round(avg_all, 1),
                'recent_average': round(avg_recent, 1)
            }
        
        return trends
    
    async def detect_meal_timing_drift(self, days: int = 30) -> Dict[str, Any]:
        """Detect if meal times are drifting earlier or later.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with timing drift for each meal type
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        async with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT m.meal_type, m.time, l.date
                FROM meals m
                JOIN daily_logs l ON m.log_id = l.id
                WHERE l.date >= ?
                ORDER BY l.date, m.time
            """, (cutoff_date.date().isoformat(),))
            meals = cursor.fetchall()
        
        if len(meals) < 14:
            return {'insufficient_data': True}
        
        # Group by meal type
        meal_times = {}
        for meal_type, time_str, date_str in meals:
            if meal_type not in meal_times:
                meal_times[meal_type] = []
            
            try:
                time_obj = datetime.strptime(time_str, "%H:%M").time()
                minutes = time_obj.hour * 60 + time_obj.minute
                date_obj = datetime.fromisoformat(date_str).date()
                meal_times[meal_type].append((date_obj, minutes))
            except ValueError:
                continue
        
        # Analyze drift for each meal type
        drift_results = {}
        for meal_type, times in meal_times.items():
            if len(times) < 7:
                continue
            
            # Sort by date
            times.sort(key=lambda x: x[0])
            
            # Compare first half vs second half
            mid = len(times) // 2
            first_half = [t[1] for t in times[:mid]]
            second_half = [t[1] for t in times[mid:]]
            
            avg_first = statistics.mean(first_half)
            avg_second = statistics.mean(second_half)
            
            drift_minutes = avg_second - avg_first
            
            if abs(drift_minutes) > 30:  # More than 30 min is significant
                direction = 'later' if drift_minutes > 0 else 'earlier'
            else:
                direction = 'stable'
            
            drift_results[meal_type] = {
                'direction': direction,
                'drift_minutes': round(drift_minutes, 0),
                'average_time_first_half': self._minutes_to_time(avg_first),
                'average_time_second_half': self._minutes_to_time(avg_second)
            }
        
        return drift_results
    
    async def detect_consistency_changes(self, days: int = 30) -> Dict[str, Any]:
        """Detect if user's eating patterns are becoming more or less consistent.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with consistency metrics
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        async with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT date, calories
                FROM daily_logs
                WHERE date >= ? AND calories IS NOT NULL
                ORDER BY date
            """, (cutoff_date.date().isoformat(),))
            logs = cursor.fetchall()
        
        if len(logs) < 14:
            return {'insufficient_data': True}
        
        # Split into two periods
        mid = len(logs) // 2
        first_period = [log[1] for log in logs[:mid]]
        second_period = [log[1] for log in logs[mid:]]
        
        # Calculate standard deviation for each period
        stdev_first = statistics.stdev(first_period) if len(first_period) > 1 else 0
        stdev_second = statistics.stdev(second_period) if len(second_period) > 1 else 0
        
        # Lower stdev = more consistent
        if stdev_second < stdev_first * 0.8:
            trend = 'more_consistent'
        elif stdev_second > stdev_first * 1.2:
            trend = 'less_consistent'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'first_period_stdev': round(stdev_first, 1),
            'second_period_stdev': round(stdev_second, 1),
            'change_percent': round(((stdev_second - stdev_first) / stdev_first) * 100, 1) if stdev_first > 0 else 0
        }
    
    async def detect_weekly_patterns(self, weeks: int = 4) -> Dict[str, Any]:
        """Detect day-of-week patterns (e.g., higher calories on weekends).
        
        Args:
            weeks: Number of weeks to analyze
            
        Returns:
            Dictionary with patterns by day of week
        """
        cutoff_date = datetime.now() - timedelta(weeks=weeks)
        
        async with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT date, calories
                FROM daily_logs
                WHERE date >= ? AND calories IS NOT NULL
                ORDER BY date
            """, (cutoff_date.date().isoformat(),))
            logs = cursor.fetchall()
        
        if len(logs) < 14:
            return {'insufficient_data': True}
        
        # Group by day of week (0=Monday, 6=Sunday)
        day_calories = {i: [] for i in range(7)}
        
        for date_str, calories in logs:
            date_obj = datetime.fromisoformat(date_str).date()
            day_of_week = date_obj.weekday()
            day_calories[day_of_week].append(calories)
        
        # Calculate averages
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_averages = {}
        
        for day, calories_list in day_calories.items():
            if calories_list:
                day_averages[day_names[day]] = round(statistics.mean(calories_list), 1)
        
        if not day_averages:
            return {'insufficient_data': True}
        
        # Find highest and lowest days
        sorted_days = sorted(day_averages.items(), key=lambda x: x[1])
        lowest_day = sorted_days[0]
        highest_day = sorted_days[-1]
        
        # Check if weekends are significantly different
        weekend_days = ['Saturday', 'Sunday']
        weekday_days = [d for d in day_names if d not in weekend_days]
        
        weekend_avg = statistics.mean([day_averages[d] for d in weekend_days if d in day_averages])
        weekday_avg = statistics.mean([day_averages[d] for d in weekday_days if d in day_averages])
        
        weekend_difference = ((weekend_avg - weekday_avg) / weekday_avg) * 100
        
        return {
            'day_averages': day_averages,
            'highest_day': {'day': highest_day[0], 'calories': highest_day[1]},
            'lowest_day': {'day': lowest_day[0], 'calories': lowest_day[1]},
            'weekend_vs_weekday': {
                'weekend_average': round(weekend_avg, 1),
                'weekday_average': round(weekday_avg, 1),
                'difference_percent': round(weekend_difference, 1)
            }
        }
    
    async def get_all_trends(self) -> Dict[str, Any]:
        """Get all detected trends in one call.
        
        Returns:
            Dictionary with all trend types
        """
        calorie_trend = await self.detect_calorie_trend()
        nutrient_trends = await self.detect_nutrient_trends()
        timing_drift = await self.detect_meal_timing_drift()
        consistency = await self.detect_consistency_changes()
        weekly_patterns = await self.detect_weekly_patterns()
        
        return {
            'calorie_trend': calorie_trend,
            'nutrient_trends': nutrient_trends,
            'meal_timing_drift': timing_drift,
            'consistency_changes': consistency,
            'weekly_patterns': weekly_patterns,
            'detected_at': datetime.now().isoformat()
        }
    
    @staticmethod
    def _minutes_to_time(minutes: float) -> str:
        """Convert minutes since midnight to HH:MM format."""
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        return f"{hours:02d}:{mins:02d}"

# Made with Bob
