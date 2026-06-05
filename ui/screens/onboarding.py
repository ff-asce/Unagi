"""Onboarding screen for Unagi TUI."""
from textual.screen import Screen
from textual.widgets import Static, Input, Button
from textual.containers import Container, Vertical, Horizontal
from rich.text import Text
from rich.panel import Panel
from typing import Dict, Any


class OnboardingScreen(Screen):
    """First-run onboarding screen to collect user profile."""
    
    def __init__(self, container: 'Container', **kwargs):
        super().__init__(**kwargs)
        self.container = container
        self.profile_data: Dict[str, Any] = {}
        self.current_step = 0
        self.steps = [
            self._step_welcome,
            self._step_weight,
            self._step_height,
            self._step_age,
            self._step_activity,
            self._step_goal,
            self._step_protein_target,
            self._step_complete
        ]
    
    def compose(self):
        """Compose the onboarding screen."""
        with Container(id="onboarding-container"):
            with Vertical(id="onboarding-content"):
                # Title
                yield Static(Text("🐍 Welcome to UNAGI", style="bold #bc8cff", justify="center"), id="onboarding-title")
                
                # Step content (will be updated)
                yield Static("", id="step-content")
                
                # Input field
                yield Input(placeholder="", id="onboarding-input")
                
                # Buttons
                with Horizontal(id="onboarding-buttons"):
                    yield Button("Back", variant="default", id="back-button")
                    yield Button("Next", variant="primary", id="next-button")
    
    def on_mount(self):
        """Initialize first step when mounted."""
        self._show_current_step()
    
    def _show_current_step(self):
        """Show the current onboarding step."""
        if self.current_step < len(self.steps):
            self.steps[self.current_step]()
        
        # Update button states
        back_button = self.query_one("#back-button", Button)
        next_button = self.query_one("#next-button", Button)
        
        back_button.disabled = self.current_step == 0
        next_button.label = "Finish" if self.current_step == len(self.steps) - 1 else "Next"
    
    def _step_welcome(self):
        """Welcome step."""
        content = self.query_one("#step-content", Static)
        input_field = self.query_one("#onboarding-input", Input)
        
        text = Text()
        text.append("Welcome to UNAGI - Total Food Awareness!\n\n", style="bold")
        text.append("Let's set up your profile to get started.\n\n")
        text.append("UNAGI will help you:\n")
        text.append("• Track your nutrition with AI assistance\n")
        text.append("• Hit your protein targets\n")
        text.append("• Maintain a calorie deficit\n")
        text.append("• Build sustainable habits\n\n")
        text.append("Press Next to continue.", style="dim")
        
        content.update(text)
        input_field.display = False
    
    def _step_weight(self):
        """Weight input step."""
        content = self.query_one("#step-content", Static)
        input_field = self.query_one("#onboarding-input", Input)
        
        text = Text()
        text.append("What is your current weight?\n\n", style="bold")
        text.append("Enter your weight in kilograms (e.g., 75)", style="dim")
        
        content.update(text)
        input_field.display = True
        input_field.placeholder = "Weight in kg"
        input_field.value = str(self.profile_data.get('current_weight', ''))
        input_field.focus()
    
    def _step_height(self):
        """Height input step."""
        content = self.query_one("#step-content", Static)
        input_field = self.query_one("#onboarding-input", Input)
        
        text = Text()
        text.append("What is your height?\n\n", style="bold")
        text.append("Enter your height in centimeters (e.g., 175)", style="dim")
        
        content.update(text)
        input_field.placeholder = "Height in cm"
        input_field.value = str(self.profile_data.get('height', ''))
        input_field.focus()
    
    def _step_age(self):
        """Age input step."""
        content = self.query_one("#step-content", Static)
        input_field = self.query_one("#onboarding-input", Input)
        
        text = Text()
        text.append("What is your age?\n\n", style="bold")
        text.append("Enter your age in years (e.g., 30)", style="dim")
        
        content.update(text)
        input_field.placeholder = "Age in years"
        input_field.value = str(self.profile_data.get('age', ''))
        input_field.focus()
    
    def _step_activity(self):
        """Activity level step."""
        content = self.query_one("#step-content", Static)
        input_field = self.query_one("#onboarding-input", Input)
        
        text = Text()
        text.append("What is your activity level?\n\n", style="bold")
        text.append("1. Sedentary (little or no exercise)\n")
        text.append("2. Lightly active (1-3 days/week)\n")
        text.append("3. Moderately active (3-5 days/week)\n")
        text.append("4. Very active (6-7 days/week)\n")
        text.append("5. Extremely active (physical job + exercise)\n\n")
        text.append("Enter a number (1-5)", style="dim")
        
        content.update(text)
        input_field.placeholder = "Activity level (1-5)"
        input_field.value = str(self.profile_data.get('activity_level', ''))
        input_field.focus()
    
    def _step_goal(self):
        """Goal selection step."""
        content = self.query_one("#step-content", Static)
        input_field = self.query_one("#onboarding-input", Input)
        
        text = Text()
        text.append("What is your primary goal?\n\n", style="bold")
        text.append("1. Lose weight (calorie deficit)\n")
        text.append("2. Maintain weight\n")
        text.append("3. Gain weight (calorie surplus)\n\n")
        text.append("Enter a number (1-3)", style="dim")
        
        content.update(text)
        input_field.placeholder = "Goal (1-3)"
        input_field.value = str(self.profile_data.get('goal', ''))
        input_field.focus()
    
    def _step_protein_target(self):
        """Protein target step."""
        content = self.query_one("#step-content", Static)
        input_field = self.query_one("#onboarding-input", Input)
        
        text = Text()
        text.append("Protein target per kg of body weight?\n\n", style="bold")
        text.append("Recommended ranges:\n")
        text.append("• Sedentary: 0.8-1.0 g/kg\n")
        text.append("• Active: 1.2-1.6 g/kg\n")
        text.append("• Athlete: 1.6-2.2 g/kg\n\n")
        text.append("Enter your target (e.g., 1.3)", style="dim")
        
        content.update(text)
        input_field.placeholder = "Protein g/kg (e.g., 1.3)"
        input_field.value = str(self.profile_data.get('protein_target_per_kg', ''))
        input_field.focus()
    
    def _step_complete(self):
        """Completion step."""
        content = self.query_one("#step-content", Static)
        input_field = self.query_one("#onboarding-input", Input)
        
        text = Text()
        text.append("Setup Complete! 🎉\n\n", style="bold green")
        text.append("Your profile has been saved.\n\n")
        text.append("You can update these settings anytime by saying:\n")
        text.append("'update my profile'\n\n", style="cyan")
        text.append("Press Finish to start using UNAGI!", style="dim")
        
        content.update(text)
        input_field.display = False
    
    def on_button_pressed(self, event: Button.Pressed):
        """Handle button presses."""
        if event.button.id == "next-button":
            self._handle_next()
        elif event.button.id == "back-button":
            self._handle_back()
    
    def _handle_next(self):
        """Handle next button press."""
        # Validate and save current step data
        if not self._validate_current_step():
            return
        
        # Move to next step or finish
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self._show_current_step()
        else:
            # Save profile and exit onboarding
            self._save_profile()
            self.app.pop_screen()
    
    def _handle_back(self):
        """Handle back button press."""
        if self.current_step > 0:
            self.current_step -= 1
            self._show_current_step()
    
    def _validate_current_step(self) -> bool:
        """Validate current step input."""
        input_field = self.query_one("#onboarding-input", Input)
        value = input_field.value.strip()
        
        # Steps that don't need validation
        if self.current_step in [0, 7]:  # Welcome and complete
            return True
        
        # Weight
        if self.current_step == 1:
            try:
                weight = float(value)
                if weight <= 0 or weight > 300:
                    self._show_error("Please enter a valid weight (1-300 kg)")
                    return False
                self.profile_data['current_weight'] = weight
            except ValueError:
                self._show_error("Please enter a valid number")
                return False
        
        # Height
        elif self.current_step == 2:
            try:
                height = int(value)
                if height <= 0 or height > 250:
                    self._show_error("Please enter a valid height (1-250 cm)")
                    return False
                self.profile_data['height'] = height
            except ValueError:
                self._show_error("Please enter a valid number")
                return False
        
        # Age
        elif self.current_step == 3:
            try:
                age = int(value)
                if age <= 0 or age > 120:
                    self._show_error("Please enter a valid age (1-120 years)")
                    return False
                self.profile_data['age'] = age
            except ValueError:
                self._show_error("Please enter a valid number")
                return False
        
        # Activity level
        elif self.current_step == 4:
            try:
                level = int(value)
                if level < 1 or level > 5:
                    self._show_error("Please enter a number between 1 and 5")
                    return False
                self.profile_data['activity_level'] = level
            except ValueError:
                self._show_error("Please enter a valid number")
                return False
        
        # Goal
        elif self.current_step == 5:
            try:
                goal = int(value)
                if goal < 1 or goal > 3:
                    self._show_error("Please enter a number between 1 and 3")
                    return False
                goal_map = {1: 'lose', 2: 'maintain', 3: 'gain'}
                self.profile_data['goal'] = goal_map[goal]
            except ValueError:
                self._show_error("Please enter a valid number")
                return False
        
        # Protein target
        elif self.current_step == 6:
            try:
                protein = float(value)
                if protein <= 0 or protein > 3:
                    self._show_error("Please enter a valid protein target (0.1-3.0 g/kg)")
                    return False
                self.profile_data['protein_target_per_kg'] = protein
            except ValueError:
                self._show_error("Please enter a valid number")
                return False
        
        return True
    
    def _show_error(self, message: str):
        """Show error message."""
        # TODO: Show error in UI
        pass
    
    def _save_profile(self):
        """Save profile to context manager."""
        self.container.context_manager.update_profile(self.profile_data)


# Made with Bob