"""Onboarding module for first-time setup."""
from .setup import (
    run_onboarding_flow,
    needs_onboarding,
    create_user_profile,
    calculate_tdee,
    OnboardingError
)
from .ingredient_seeder import IngredientSeeder

__all__ = [
    "run_onboarding_flow",
    "needs_onboarding",
    "create_user_profile",
    "calculate_tdee",
    "OnboardingError",
    "IngredientSeeder",
]

# Made with Bob
