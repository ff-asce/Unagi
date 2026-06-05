"""Today panel widget for Unagi TUI."""
from textual.widgets import Static
from textual.containers import VerticalScroll
from rich.text import Text
from rich.table import Table
from typing import Optional, Dict, Any, List


class TodayPanel(VerticalScroll):
    """Panel showing today's summary and recent meals."""
    
    def __init__(self, container: 'Container', **kwargs):
        super().__init__(**kwargs)
        self.container = container
        self.today_data: Optional[Dict[str, Any]] = None
    
    def on_mount(self):
        """Load initial data when mounted."""
        self.refresh_data()
    
    def refresh_data(self):
        """Refresh today's data from context manager."""
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
        """Update the panel display."""
        self.remove_children()
        
        # Title
        title = Static(Text("📅 Today", style="bold #bc8cff"))
        title.add_class("today-title")
        self.mount(title)
        
        if not self.today_data:
            # No log today
            no_log = Static(Text("No meals logged yet today.", style="dim"))
            self.mount(no_log)
            return
        
        # Summary stats
        summary = self._build_summary()
        self.mount(summary)
        
        # Meals list
        meals = self._build_meals_list()
        if meals:
            self.mount(meals)
    
    def _build_summary(self) -> Static:
        """Build summary stats widget."""
        cal = self.today_data.get('calories', 0)
        protein = self.today_data.get('protein', 0)
        carbs = self.today_data.get('carbs', 0)
        fat = self.today_data.get('fat', 0)
        fiber = self.today_data.get('fiber', 0)
        
        # Get targets
        context = self.container.context_manager.get_context()
        profile = context.profile or {}
        weight = profile.get('current_weight', 100)
        protein_target = int(weight * profile.get('protein_target_per_kg', 1.3))
        
        # Build table
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Metric", style="dim")
        table.add_column("Value", justify="right")
        
        # Calories
        table.add_row("Calories", f"{cal} kcal")
        
        # Protein with target
        protein_style = "green" if protein >= protein_target else "yellow"
        table.add_row("Protein", f"[{protein_style}]{protein}g[/] / {protein_target}g")
        
        # Macros
        table.add_row("Carbs", f"{carbs}g")
        table.add_row("Fat", f"{fat}g")
        table.add_row("Fiber", f"{fiber}g")
        
        # Deficit
        deficit = self.today_data.get('deficit', 0)
        deficit_style = "green" if deficit < 0 else "red"
        deficit_text = f"{deficit:+d} kcal" if deficit != 0 else "0 kcal"
        table.add_row("Deficit", f"[{deficit_style}]{deficit_text}[/]")
        
        widget = Static(table)
        widget.add_class("today-summary")
        return widget
    
    def _build_meals_list(self) -> Optional[Static]:
        """Build meals list widget."""
        meals = self.today_data.get('meals', [])
        if not meals:
            return None
        
        # Build meals text
        text = Text("\n")
        text.append("Meals:\n", style="bold dim")
        
        for i, meal in enumerate(meals, 1):
            meal_name = meal.get('name', 'Unknown')
            meal_cal = meal.get('calories', 0)
            meal_protein = meal.get('protein', 0)
            
            text.append(f"{i}. ", style="dim")
            text.append(f"{meal_name}\n", style="")
            text.append(f"   {meal_cal} kcal · P: {meal_protein}g\n", style="dim")
        
        widget = Static(text)
        widget.add_class("today-meals")
        return widget
    
    def show_empty_state(self):
        """Show empty state when no data."""
        self.remove_children()
        
        title = Static(Text("📅 Today", style="bold #bc8cff"))
        self.mount(title)
        
        empty = Static(Text("No meals logged yet today.\n\nTry: 'log breakfast'", style="dim"))
        self.mount(empty)


class TodaySummaryWidget(Static):
    """Widget showing today's summary stats."""
    
    def __init__(self, data: Dict[str, Any], profile: Dict[str, Any], **kwargs):
        super().__init__(**kwargs)
        self.data = data
        self.profile = profile
    
    def render(self):
        """Render the summary."""
        cal = self.data.get('calories', 0)
        protein = self.data.get('protein', 0)
        carbs = self.data.get('carbs', 0)
        fat = self.data.get('fat', 0)
        fiber = self.data.get('fiber', 0)
        deficit = self.data.get('deficit', 0)
        
        # Get protein target
        weight = self.profile.get('current_weight', 100)
        protein_target = int(weight * self.profile.get('protein_target_per_kg', 1.3))
        
        # Build table
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Metric", style="dim")
        table.add_column("Value", justify="right")
        
        table.add_row("Calories", f"{cal} kcal")
        
        protein_style = "green" if protein >= protein_target else "yellow"
        table.add_row("Protein", f"[{protein_style}]{protein}g[/] / {protein_target}g")
        
        table.add_row("Carbs", f"{carbs}g")
        table.add_row("Fat", f"{fat}g")
        table.add_row("Fiber", f"{fiber}g")
        
        deficit_style = "green" if deficit < 0 else "red"
        deficit_text = f"{deficit:+d} kcal" if deficit != 0 else "0 kcal"
        table.add_row("Deficit", f"[{deficit_style}]{deficit_text}[/]")
        
        return table


# Made with Bob