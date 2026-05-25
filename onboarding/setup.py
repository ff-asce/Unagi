"""Onboarding flow for first-time setup."""
from typing import Dict, Any, Optional
from datetime import datetime
from config import get_settings
from vault import get_vault_writer


class OnboardingError(Exception):
    """Raised when onboarding fails."""
    pass


def calculate_tdee(
    weight_kg: float,
    height_cm: int,
    age: int,
    gender: str,
    activity_level: str = "sedentary"
) -> int:
    """Calculate Total Daily Energy Expenditure using Mifflin-St Jeor equation.
    
    Args:
        weight_kg: Weight in kilograms
        height_cm: Height in centimeters
        age: Age in years
        gender: 'male', 'female', or 'other'
        activity_level: Activity level (sedentary, light, moderate, active, very_active)
        
    Returns:
        Estimated TDEE in calories
    """
    # Mifflin-St Jeor BMR calculation
    if gender.lower() == 'male':
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    elif gender.lower() == 'female':
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
    else:
        # Use average for 'other'
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 78
    
    # Activity multipliers
    multipliers = {
        'sedentary': 1.2,      # Little or no exercise
        'light': 1.375,        # Light exercise 1-3 days/week
        'moderate': 1.55,      # Moderate exercise 3-5 days/week
        'active': 1.725,       # Hard exercise 6-7 days/week
        'very_active': 1.9     # Very hard exercise, physical job
    }
    
    multiplier = multipliers.get(activity_level.lower(), 1.2)
    tdee = int(bmr * multiplier)
    
    return tdee


def create_user_profile(
    name: str,
    weight_kg: float,
    height_cm: int,
    age: int,
    gender: str,
    goal: str,
    maintenance_calories: Optional[int] = None,
    protein_target_per_kg: float = 1.3,
    notes: str = ""
) -> Dict[str, Any]:
    """Create a user profile dictionary.
    
    Args:
        name: User's name
        weight_kg: Current weight in kg
        height_cm: Height in cm
        age: Age in years
        gender: 'male', 'female', or 'other'
        goal: 'cut', 'bulk', or 'maintain'
        maintenance_calories: Maintenance calories (calculated if not provided)
        protein_target_per_kg: Protein target per kg body weight
        notes: Additional notes about the user
        
    Returns:
        User profile dictionary
    """
    # Calculate maintenance if not provided
    if maintenance_calories is None:
        maintenance_calories = calculate_tdee(weight_kg, height_cm, age, gender)
    
    # Calculate date of birth from age
    current_year = datetime.now().year
    birth_year = current_year - age
    dob = f"{birth_year}-01-01"  # Approximate DOB
    
    profile = {
        'name': name,
        'current_weight': weight_kg,
        'height_cm': height_cm,
        'dob': dob,
        'gender': gender.lower(),
        'maintenance_calories': maintenance_calories,
        'protein_target_per_kg': protein_target_per_kg,
        'goal': goal.lower(),
        'known_ingredients': [],
        'notes': notes
    }
    
    return profile


def run_onboarding_flow() -> bool:
    """Run the interactive onboarding flow.
    
    Returns:
        True if onboarding completed successfully
        
    Raises:
        OnboardingError: If onboarding fails
    """
    try:
        print("\n" + "="*60)
        print("🐍  UNAGI — Total Food Awareness")
        print("="*60)
        print("\nHey! I'm Unagi, your personal nutrition agent.")
        print("Looks like this is your first time. Let's get you set up.")
        print("I'll ask a few quick questions to get started.\n")
        
        # Collect user information
        name = input("What's your name? ").strip()
        if not name:
            raise OnboardingError("Name is required")
        
        age_str = input("How old are you? ").strip()
        try:
            age = int(age_str)
            if age < 10 or age > 120:
                raise ValueError
        except ValueError:
            raise OnboardingError("Please enter a valid age")
        
        weight_str = input("What's your current weight in kg? ").strip()
        try:
            weight_kg = float(weight_str)
            if weight_kg < 30 or weight_kg > 300:
                raise ValueError
        except ValueError:
            raise OnboardingError("Please enter a valid weight")
        
        height_str = input("What's your height in cm? ").strip()
        try:
            height_cm = int(height_str)
            if height_cm < 100 or height_cm > 250:
                raise ValueError
        except ValueError:
            raise OnboardingError("Please enter a valid height")
        
        gender = input("What's your biological sex? (male/female/other) ").strip().lower()
        if gender not in ['male', 'female', 'other']:
            raise OnboardingError("Please enter male, female, or other")
        
        goal = input("What's your goal? (cut/bulk/maintain) ").strip().lower()
        if goal not in ['cut', 'bulk', 'maintain']:
            raise OnboardingError("Please enter cut, bulk, or maintain")
        
        # Calculate or get maintenance calories
        print("\nWhat's your estimated daily maintenance calories?")
        print("(Press Enter and I'll estimate it for you based on your stats)")
        maintenance_str = input("> ").strip()
        
        if maintenance_str:
            try:
                maintenance_calories = int(maintenance_str)
            except ValueError:
                raise OnboardingError("Please enter a valid number for calories")
        else:
            maintenance_calories = calculate_tdee(weight_kg, height_cm, age, gender)
            print(f"\nBased on your stats, I estimate your maintenance at {maintenance_calories} kcal/day")
        
        # Create profile
        profile = create_user_profile(
            name=name,
            weight_kg=weight_kg,
            height_cm=height_cm,
            age=age,
            gender=gender,
            goal=goal,
            maintenance_calories=maintenance_calories
        )
        
        # Write profile to vault
        writer = get_vault_writer()
        writer.write_user_profile(profile)
        
        print("\n✅ Perfect! I've set up your profile.")
        print("You can update any of these by telling me, e.g. 'My weight is now 103kg'.")
        print("\nWhat did you eat today?\n")
        
        return True
        
    except KeyboardInterrupt:
        print("\n\nOnboarding cancelled.")
        return False
    except Exception as e:
        raise OnboardingError(f"Onboarding failed: {str(e)}")


def needs_onboarding() -> bool:
    """Check if onboarding is needed.
    
    Returns:
        True if user profile doesn't exist
    """
    try:
        from vault import get_vault_reader
        reader = get_vault_reader()
        return not reader.user_profile_exists()
    except Exception:
        return True

# Made with Bob
