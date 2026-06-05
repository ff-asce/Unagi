"""Stats bar widget for Unagi TUI."""
from textual.widgets import Static
from typing import Optional, Dict, Any


class StatsBar(Static):
    """Stats bar showing today's metrics and protein progress."""
    
    def __init__(self, container: 'Container', **kwargs):
        super().__init__(**kwargs)
        self.container = container
        self.today_data: Optional[Dict[str, Any]] = None
    
    def on_mount(self):
        """Load initial data when mounted."""
        self.refresh_data()
    
    def refresh_data(self):
        """Refresh stats from context manager."""
        from datetime import date
        context = self.container.context_manager.get_context()
        
        # Find today's log
        today_str = str(date.today())
        self.today_data = None
        if context.recent_logs:
            for log in context.recent_logs:
                if log.get('date') == today_str:
                    self.today_data = log
                    break
        
        self._update_display()
    
    def _update_display(self):
        """Update the stats bar display."""
        if not self.today_data:
            # No log today
            self.update(self._build_no_log_text())
        else:
            self.update(self._build_stats_text())
    
    def _build_no_log_text(self) -> str:
        """Build text for when there's no log today."""
        # Try to get yesterday's data
        from datetime import date, timedelta
        yesterday_str = str(date.today() - timedelta(days=1))
        
        context = self.container.context_manager.get_context()
        yesterday_data = None
        if context.recent_logs:
            for log in context.recent_logs:
                if log.get('date') == yesterday_str:
                    yesterday_data = log
                    break
        
        if yesterday_data:
            cal = yesterday_data.get('calories', 0)
            protein = yesterday_data.get('protein', 0)
            deficit = yesterday_data.get('deficit', 0)
            line1 = f"No log today yet.  ·  Yesterday: {cal} kcal · P: {protein}g · Deficit: {deficit}"
        else:
            line1 = "No log today yet."
        
        line2 = ""
        return f"{line1}\n{line2}"
    
    def _build_stats_text(self) -> str:
        """Build stats text with today's data."""
        cal = self.today_data.get('calories', 0)
        protein = self.today_data.get('protein', 0)
        deficit = self.today_data.get('deficit', 0)
        fiber = self.today_data.get('fiber', 0)
        
        # Get protein target from profile
        context = self.container.context_manager.get_context()
        profile = context.profile or {}
        weight = profile.get('current_weight', 100)
        protein_per_kg = profile.get('protein_target_per_kg', 1.3)
        protein_target = int(weight * protein_per_kg)
        
        # Check if targets met
        protein_check = "✅" if protein >= protein_target else ""
        deficit_check = "✅" if deficit < 0 else ""
        
        line1 = f"Today: {cal} kcal  ·  Protein: {protein}g {protein_check}  ·  Deficit: {deficit} {deficit_check}  ·  Fiber: {fiber}g"
        
        # Build protein progress bar
        protein_pct = int((protein / protein_target) * 100) if protein_target > 0 else 0
        bar_length = 12
        filled = int((protein / protein_target) * bar_length) if protein_target > 0 else 0
        filled = min(filled, bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        # Calculate 7-day average deficit
        avg_deficit = self._calculate_weekly_avg_deficit()
        
        line2 = f"Protein {protein}/{protein_target}g  {bar}  {protein_pct}%   ·   7-day avg deficit: {avg_deficit} kcal"
        
        return f"{line1}\n{line2}"
    
    def _calculate_weekly_avg_deficit(self) -> int:
        """Calculate 7-day rolling average deficit."""
        from datetime import date, timedelta
        context = self.container.context_manager.get_context()
        
        week_ago = date.today() - timedelta(days=7)
        week_logs = [
            log for log in context.recent_logs
            if log.get('date') and date.fromisoformat(log['date']) >= week_ago
        ]
        
        if not week_logs:
            return 0
        
        total_deficit = sum(log.get('deficit', 0) for log in week_logs)
        return int(total_deficit / len(week_logs))


# Made with Bob