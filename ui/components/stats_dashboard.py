"""Stats dashboard component for displaying nutrition tracking."""
from textual.widgets import Static
from textual.containers import Vertical
from textual.reactive import reactive
from rich.text import Text
from .retro_assets import (
    COLORS,
    ICONS,
    get_progress_bar,
    create_sparkline
)


class MacroDisplay(Static):
    """Display for macronutrient tracking."""
    
    calories = reactive(0)
    protein = reactive(0)
    carbs = reactive(0)
    fat = reactive(0)
    
    def __init__(self, goals: dict, *args, **kwargs):
        """Initialize macro display.
        
        Args:
            goals: Dictionary with calorie and macro goals
        """
        super().__init__(*args, **kwargs)
        self.goals = goals
    
    def render(self) -> Text:
        """Render macro progress bars."""
        text = Text()
        
        # Header
        text.append(f"{ICONS['fire']} TODAY'S MACROS\n", 
                   style=f"bold {COLORS['ORANGE']}")
        text.append("─" * 30 + "\n", style=COLORS['BORDER'])
        
        # Calories
        cal_pct = int((self.calories / self.goals.get('calories', 2200)) * 100)
        text.append(f"Calories: {self.calories} / {self.goals.get('calories', 2200)} kcal\n",
                   style=COLORS['LIGHT_TEXT'])
        text.append(get_progress_bar(cal_pct, 20) + "\n\n", 
                   style=COLORS['LIGHT_TEXT'])
        
        # Protein
        prot_pct = int((self.protein / self.goals.get('protein', 165)) * 100)
        text.append(f"Protein: {self.protein}g / {self.goals.get('protein', 165)}g\n",
                   style=COLORS['LIGHT_TEXT'])
        text.append(get_progress_bar(prot_pct, 20) + "\n\n",
                   style=COLORS['LIGHT_TEXT'])
        
        # Carbs
        carb_pct = int((self.carbs / self.goals.get('carbs', 220)) * 100)
        text.append(f"Carbs: {self.carbs}g / {self.goals.get('carbs', 220)}g\n",
                   style=COLORS['LIGHT_TEXT'])
        text.append(get_progress_bar(carb_pct, 20) + "\n\n",
                   style=COLORS['LIGHT_TEXT'])
        
        # Fat
        fat_pct = int((self.fat / self.goals.get('fat', 73)) * 100)
        text.append(f"Fat: {self.fat}g / {self.goals.get('fat', 73)}g\n",
                   style=COLORS['LIGHT_TEXT'])
        text.append(get_progress_bar(fat_pct, 20) + "\n",
                   style=COLORS['LIGHT_TEXT'])
        
        return text
    
    def update_values(self, calories: int, protein: int, carbs: int, fat: int) -> None:
        """Update macro values.
        
        Args:
            calories: Current calories
            protein: Current protein in grams
            carbs: Current carbs in grams
            fat: Current fat in grams
        """
        self.calories = calories
        self.protein = protein
        self.carbs = carbs
        self.fat = fat


class MicroDisplay(Static):
    """Display for micronutrient tracking."""
    
    def __init__(self, *args, **kwargs):
        """Initialize micro display."""
        super().__init__(*args, **kwargs)
        self.micros = {}
    
    def render(self) -> Text:
        """Render micronutrient status."""
        text = Text()
        
        # Header
        text.append(f"\n{ICONS['brain']} MICRONUTRIENTS\n", 
                   style=f"bold {COLORS['PURPLE']}")
        text.append("─" * 30 + "\n", style=COLORS['BORDER'])
        
        if not self.micros:
            text.append("No data yet\n", style=f"italic {COLORS['INFO']}")
            return text
        
        # Show top 10 micronutrients
        for i, (name, pct) in enumerate(list(self.micros.items())[:10]):
            # Status emoji
            if pct >= 80:
                status = ICONS['check']
                color = COLORS['SUCCESS']
            elif pct >= 50:
                status = ICONS['warning']
                color = COLORS['WARNING']
            else:
                status = ICONS['cross']
                color = COLORS['ERROR']
            
            text.append(f"{status} {name}: {pct}%\n", style=color)
        
        if len(self.micros) > 10:
            text.append(f"\n... and {len(self.micros) - 10} more (scroll to see)\n",
                       style=f"italic {COLORS['INFO']}")
        
        return text
    
    def update_micros(self, micros: dict) -> None:
        """Update micronutrient data.
        
        Args:
            micros: Dictionary of micronutrient name -> percentage
        """
        self.micros = micros
        self.refresh()


class WeeklyTrend(Static):
    """Display for weekly nutrition trends."""
    
    def __init__(self, *args, **kwargs):
        """Initialize weekly trend display."""
        super().__init__(*args, **kwargs)
        self.weekly_data = []
    
    def render(self) -> Text:
        """Render weekly trend sparklines."""
        text = Text()
        
        # Header
        text.append(f"\n{ICONS['star']} WEEKLY TREND\n", 
                   style=f"bold {COLORS['ORANGE']}")
        text.append("─" * 30 + "\n", style=COLORS['BORDER'])
        
        if not self.weekly_data:
            text.append("No weekly data yet\n", style=f"italic {COLORS['INFO']}")
            return text
        
        # Extract data for sparklines
        calories = [day.get('calories', 0) for day in self.weekly_data]
        protein = [day.get('protein', 0) for day in self.weekly_data]
        
        # Sparklines
        text.append("Calories: ", style=COLORS['LIGHT_TEXT'])
        text.append(create_sparkline(calories) + "\n", style=COLORS['ORANGE'])
        
        text.append("Protein:  ", style=COLORS['LIGHT_TEXT'])
        text.append(create_sparkline(protein) + "\n", style=COLORS['PURPLE'])
        
        return text
    
    def update_weekly_data(self, data: list) -> None:
        """Update weekly data.
        
        Args:
            data: List of daily log dictionaries
        """
        self.weekly_data = data
        self.refresh()


class StatsDashboard(Vertical):
    """Complete stats dashboard with macros, micros, and trends."""
    
    visible = reactive(True)
    
    def __init__(self, goals: dict, *args, **kwargs):
        """Initialize stats dashboard.
        
        Args:
            goals: Dictionary with nutrition goals
        """
        super().__init__(*args, **kwargs)
        self.goals = goals
        self.macro_display = MacroDisplay(goals)
        self.micro_display = MicroDisplay()
        self.weekly_trend = WeeklyTrend()
    
    def compose(self):
        """Compose the dashboard widgets."""
        yield self.macro_display
        yield self.micro_display
        yield self.weekly_trend
    
    def toggle_visibility(self) -> None:
        """Toggle dashboard visibility."""
        self.visible = not self.visible
        self.display = self.visible
    
    def update_stats(self, calories: int, protein: int, carbs: int, fat: int,
                    micros: dict, weekly_data: list) -> None:
        """Update all dashboard stats.
        
        Args:
            calories: Current calories
            protein: Current protein
            carbs: Current carbs
            fat: Current fat
            micros: Micronutrient data
            weekly_data: Weekly trend data
        """
        self.macro_display.update_values(calories, protein, carbs, fat)
        self.micro_display.update_micros(micros)
        self.weekly_trend.update_weekly_data(weekly_data)


# Made with Bob