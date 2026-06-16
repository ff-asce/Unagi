"""Proactive suggestion generation based on patterns and trends."""
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import random

from memory.database import Database
from .learning import PatternLearner
from .trends import TrendDetector


class SuggestionEngine:
    """Generate proactive suggestions based on learned patterns and trends."""
    
    def __init__(self, database: Database, learner: PatternLearner, detector: TrendDetector):
        """Initialize suggestion engine.
        
        Args:
            database: Memory database instance
            learner: Pattern learner instance
            detector: Trend detector instance
        """
        self.db = database
        self.learner = learner
        self.detector = detector
    
    async def suggest_meal_timing(self) -> List[Dict[str, Any]]:
        """Suggest optimal meal times based on learned patterns.
        
        Returns:
            List of timing suggestions
        """
        patterns = await self.learner.learn_meal_patterns()
        drift = await self.detector.detect_meal_timing_drift()
        
        suggestions = []
        
        # Check if user has established meal times
        meal_times = patterns.get('meal_times', {})
        if meal_times:
            current_time = datetime.now().time()
            current_minutes = current_time.hour * 60 + current_time.minute
            
            for meal_type, time_str in meal_times.items():
                time_obj = datetime.strptime(time_str, "%H:%M").time()
                meal_minutes = time_obj.hour * 60 + time_obj.minute
                
                # Suggest if within 30 minutes of typical time
                diff = abs(current_minutes - meal_minutes)
                if diff <= 30:
                    suggestions.append({
                        'type': 'meal_timing',
                        'priority': 'medium',
                        'message': f"It's around your usual {meal_type} time ({time_str}). Ready to log your meal?",
                        'action': f'log_{meal_type}'
                    })
        
        # Check for timing drift
        if not drift.get('insufficient_data'):
            for meal_type, drift_info in drift.items():
                if drift_info['direction'] in ['earlier', 'later']:
                    suggestions.append({
                        'type': 'timing_drift',
                        'priority': 'low',
                        'message': f"Your {meal_type} has been drifting {drift_info['direction']} by about {abs(drift_info['drift_minutes'])} minutes. Consider adjusting your schedule.",
                        'action': None
                    })
        
        return suggestions
    
    async def suggest_nutrient_balance(self) -> List[Dict[str, Any]]:
        """Suggest nutrient adjustments based on trends and goals.
        
        Returns:
            List of nutrient balance suggestions
        """
        trends = await self.detector.detect_nutrient_trends()
        goal_progress = await self.learner.learn_goal_progress()
        
        suggestions = []
        
        # Check for concerning trends
        for nutrient, trend_info in trends.items():
            if trend_info.get('direction') == 'insufficient_data':
                continue
            
            if trend_info['direction'] == 'decreasing' and trend_info['change_percent'] < -15:
                suggestions.append({
                    'type': 'nutrient_trend',
                    'priority': 'high',
                    'message': f"Your {nutrient} intake has decreased by {abs(trend_info['change_percent'])}% recently. Consider adding more {nutrient}-rich foods.",
                    'action': f'suggest_{nutrient}_foods'
                })
            elif trend_info['direction'] == 'increasing' and trend_info['change_percent'] > 15:
                suggestions.append({
                    'type': 'nutrient_trend',
                    'priority': 'medium',
                    'message': f"Your {nutrient} intake has increased by {trend_info['change_percent']}% recently. Make sure this aligns with your goals.",
                    'action': None
                })
        
        # Check goal achievement
        achievement_rates = goal_progress.get('goal_achievement_rate', {})
        for nutrient, rate in achievement_rates.items():
            if rate < 50:  # Achieving goals less than 50% of the time
                suggestions.append({
                    'type': 'goal_achievement',
                    'priority': 'high',
                    'message': f"You're only meeting your {nutrient} goal {rate}% of the time. Would you like to adjust your goal or get tips?",
                    'action': f'adjust_{nutrient}_goal'
                })
        
        # Check for improving trend
        if goal_progress.get('improving_trend') is True:
            suggestions.append({
                'type': 'positive_feedback',
                'priority': 'low',
                'message': "Great progress! You're getting closer to your nutrition goals over time. Keep it up!",
                'action': None
            })
        
        return suggestions
    
    async def suggest_ingredients(self) -> List[Dict[str, Any]]:
        """Suggest ingredients based on preferences and variety.
        
        Returns:
            List of ingredient suggestions
        """
        prefs = await self.learner.learn_ingredient_preferences()
        
        suggestions = []
        
        # Suggest variety if user is repetitive
        frequent = prefs.get('frequent_ingredients', [])
        if len(frequent) >= 5:
            top_5_count = sum(item['count'] for item in frequent[:5])
            total_count = sum(item['count'] for item in frequent)
            
            if total_count > 0 and (top_5_count / total_count) > 0.7:
                # User is using same 5 ingredients 70%+ of the time
                suggestions.append({
                    'type': 'variety',
                    'priority': 'medium',
                    'message': "You tend to use the same ingredients often. Want suggestions for adding variety to your meals?",
                    'action': 'suggest_new_ingredients'
                })
        
        # Suggest complementary ingredients
        combinations = prefs.get('ingredient_combinations', [])
        if combinations:
            top_combo = combinations[0]
            suggestions.append({
                'type': 'ingredient_pairing',
                'priority': 'low',
                'message': f"You often pair {' and '.join(top_combo['ingredients'])}. These work great together!",
                'action': None
            })
        
        return suggestions
    
    async def suggest_meal_prep(self) -> List[Dict[str, Any]]:
        """Suggest meal prep opportunities based on patterns.
        
        Returns:
            List of meal prep suggestions
        """
        patterns = await self.learner.learn_meal_patterns()
        weekly = await self.detector.detect_weekly_patterns()
        
        suggestions = []
        
        # Check meal frequency
        frequency = patterns.get('meal_frequency', {})
        for meal_type, freq in frequency.items():
            if freq >= 5:  # Eating this meal 5+ times per week
                typical_meals = patterns.get('typical_meals', {}).get(meal_type, [])
                if typical_meals:
                    suggestions.append({
                        'type': 'meal_prep',
                        'priority': 'low',
                        'message': f"You have {meal_type} {freq} times per week, often with {typical_meals[0]}. Consider meal prepping to save time!",
                        'action': 'meal_prep_tips'
                    })
        
        # Check for weekend patterns
        if not weekly.get('insufficient_data'):
            weekend_diff = weekly.get('weekend_vs_weekday', {}).get('difference_percent', 0)
            if abs(weekend_diff) > 20:
                direction = 'more' if weekend_diff > 0 else 'less'
                suggestions.append({
                    'type': 'weekly_pattern',
                    'priority': 'low',
                    'message': f"You tend to eat {abs(weekend_diff):.0f}% {direction} on weekends. Plan accordingly!",
                    'action': None
                })
        
        return suggestions
    
    async def suggest_hydration(self) -> List[Dict[str, Any]]:
        """Suggest hydration reminders based on time and patterns.
        
        Returns:
            List of hydration suggestions
        """
        # Get today's water intake
        today = datetime.now().date()
        
        async with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT water_ml
                FROM daily_logs
                WHERE date = ?
            """, (today.isoformat(),))
            row = cursor.fetchone()
        
        suggestions = []
        current_water = row[0] if row and row[0] else 0
        
        # Recommend based on time of day and current intake
        current_hour = datetime.now().hour
        
        if current_hour < 12 and current_water < 500:
            suggestions.append({
                'type': 'hydration',
                'priority': 'medium',
                'message': "Morning hydration is important! Have you had water today?",
                'action': 'log_water'
            })
        elif current_hour >= 12 and current_hour < 18 and current_water < 1500:
            suggestions.append({
                'type': 'hydration',
                'priority': 'medium',
                'message': "Stay hydrated throughout the day. Time for some water?",
                'action': 'log_water'
            })
        elif current_hour >= 18 and current_water < 2000:
            suggestions.append({
                'type': 'hydration',
                'priority': 'low',
                'message': "Don't forget to reach your hydration goal before bed!",
                'action': 'log_water'
            })
        
        return suggestions
    
    async def suggest_goal_adjustments(self) -> List[Dict[str, Any]]:
        """Suggest goal adjustments based on achievement patterns.
        
        Returns:
            List of goal adjustment suggestions
        """
        goal_progress = await self.learner.learn_goal_progress()
        
        suggestions = []
        
        achievement_rates = goal_progress.get('goal_achievement_rate', {})
        deviations = goal_progress.get('average_deviation', {})
        
        for nutrient, rate in achievement_rates.items():
            deviation = deviations.get(nutrient, 0)
            
            # Goals too aggressive (low achievement, high deviation)
            if rate < 40 and deviation > 20:
                suggestions.append({
                    'type': 'goal_adjustment',
                    'priority': 'high',
                    'message': f"Your {nutrient} goal might be too aggressive. You're off by {deviation:.0f}% on average. Consider adjusting it to be more achievable.",
                    'action': f'adjust_{nutrient}_goal'
                })
            
            # Goals too easy (very high achievement)
            elif rate > 90 and deviation < 5:
                suggestions.append({
                    'type': 'goal_adjustment',
                    'priority': 'low',
                    'message': f"You're consistently exceeding your {nutrient} goal! Consider setting a more challenging target.",
                    'action': f'adjust_{nutrient}_goal'
                })
        
        return suggestions
    
    async def suggest_consistency_improvements(self) -> List[Dict[str, Any]]:
        """Suggest ways to improve consistency.
        
        Returns:
            List of consistency improvement suggestions
        """
        consistency = await self.detector.detect_consistency_changes()
        
        suggestions = []
        
        if consistency.get('trend') == 'less_consistent':
            suggestions.append({
                'type': 'consistency',
                'priority': 'medium',
                'message': f"Your eating patterns have become less consistent recently (variability increased by {consistency['change_percent']:.0f}%). Would you like tips for building routine?",
                'action': 'consistency_tips'
            })
        elif consistency.get('trend') == 'more_consistent':
            suggestions.append({
                'type': 'positive_feedback',
                'priority': 'low',
                'message': "Your eating patterns are becoming more consistent. Great job building healthy habits!",
                'action': None
            })
        
        return suggestions
    
    async def get_all_suggestions(self, max_per_type: int = 2) -> List[Dict[str, Any]]:
        """Get all suggestions, limited per type.
        
        Args:
            max_per_type: Maximum suggestions per type
            
        Returns:
            List of all suggestions, prioritized
        """
        # Gather all suggestions
        timing = await self.suggest_meal_timing()
        nutrients = await self.suggest_nutrient_balance()
        ingredients = await self.suggest_ingredients()
        meal_prep = await self.suggest_meal_prep()
        hydration = await self.suggest_hydration()
        goals = await self.suggest_goal_adjustments()
        consistency = await self.suggest_consistency_improvements()
        
        all_suggestions = (
            timing + nutrients + ingredients + 
            meal_prep + hydration + goals + consistency
        )
        
        # Limit per type
        type_counts = {}
        filtered = []
        
        for suggestion in all_suggestions:
            sug_type = suggestion['type']
            if type_counts.get(sug_type, 0) < max_per_type:
                filtered.append(suggestion)
                type_counts[sug_type] = type_counts.get(sug_type, 0) + 1
        
        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        filtered.sort(key=lambda x: priority_order.get(x['priority'], 3))
        
        return filtered
    
    async def get_contextual_suggestions(self, context: str) -> List[Dict[str, Any]]:
        """Get suggestions relevant to current context.
        
        Args:
            context: Current context (e.g., 'morning', 'pre_workout', 'meal_logging')
            
        Returns:
            List of contextual suggestions
        """
        all_suggestions = await self.get_all_suggestions()
        
        # Filter based on context
        if context == 'morning':
            return [s for s in all_suggestions if s['type'] in ['meal_timing', 'hydration', 'goal_adjustment']]
        elif context == 'meal_logging':
            return [s for s in all_suggestions if s['type'] in ['ingredient_pairing', 'nutrient_trend', 'variety']]
        elif context == 'weekly_review':
            return [s for s in all_suggestions if s['type'] in ['weekly_pattern', 'consistency', 'goal_achievement']]
        else:
            return all_suggestions[:5]  # Return top 5 for general context

# Made with Bob
