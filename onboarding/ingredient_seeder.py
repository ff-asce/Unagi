"""
Post-onboarding ingredient seeding.
Extracts recurring ingredients from log history and adds them to
the user profile's known_ingredients list.
"""
import json
from typing import List, Dict, Any, Optional
from pathlib import Path


class IngredientSeeder:
    """
    Extracts and confirms recurring ingredients from existing log history.
    
    Runs once after onboarding + migration.
    Can be re-run via /seed-ingredients command.
    
    In Phase 2, this grows to also update known_ingredients automatically
    when the agent notices a new ingredient appearing in multiple logs.
    """
    
    def __init__(
        self,
        llm_client: 'LLMClient',
        vault_reader: 'VaultReader',
        vault_writer: 'VaultWriter',
        scan_days: int = 30
    ):
        self.llm = llm_client
        self.reader = vault_reader
        self.writer = vault_writer
        self.scan_days = scan_days
    
    def has_known_ingredients(self) -> bool:
        """Check if the profile already has known ingredients seeded."""
        try:
            profile = self.reader.read_user_profile()
            if not profile:
                return False
            ingredients = profile.get('known_ingredients', [])
            return len(ingredients) > 0
        except Exception:
            return False
    
    def has_enough_logs(self) -> bool:
        """Check if there are enough logs to extract from."""
        logs = self.reader.read_recent_logs(self.scan_days)
        return len(logs) >= 3  # Need at least 3 days to identify patterns
    
    def extract_ingredients(self) -> List[Dict[str, Any]]:
        """
        Use LLM to extract recurring ingredients from log history.
        Returns a list of ingredient dicts with name, macros, etc.
        """
        logs = self.reader.read_recent_logs(self.scan_days)
        
        if not logs:
            return []
        
        # Collect all meal strings
        meal_strings = []
        for log in logs:
            for field in ['breakfast', 'lunch', 'dinner', 'misc']:
                value = log.get(field, '—')
                if value and value != '—':
                    meal_strings.append(f"- {value}")
        
        if not meal_strings:
            return []
        
        meal_text = "\n".join(meal_strings[:100])  # Cap at 100 entries
        
        extraction_prompt = f"""You are analyzing a user's food log history to extract their recurring ingredients.

Below are meal description strings from the past {self.scan_days} days.
Extract ingredients that appear FREQUENTLY (in at least 2-3 log entries).

For each ingredient provide:
- name: Specific name (preserve brand names exactly as written)
- typical_amount: Most common amount (e.g. "150g", "1 tsp")
- category: protein/dairy/vegetable/fat/grain/seeds/beverage/other
- per_100g: {{calories, protein, carbs, fats, fiber}} as numbers
- composition: For mixed ingredients (e.g. "18g Chia + 6g Basil seeds")
- notes: Special info (raw weight note, usage pattern, etc.)

Rules:
- Preserve brand names (Amul Masti Dahi NOT just yogurt)
- Skip generic spices — negligible macro impact
- Consolidate duplicates (raw/uncooked are the same ingredient)
- Capture seed mix compositions fully
- Return ONLY valid JSON, no other text

Return:
{{"ingredients": [
  {{
    "name": "...",
    "typical_amount": "...",
    "category": "...",
    "per_100g": {{"calories": 0, "protein": 0, "carbs": 0, "fats": 0, "fiber": 0}},
    "composition": "...",
    "notes": "..."
  }}
]}}

Meal log history:
{meal_text}"""
        
        try:
            response = self.llm.chat(
                messages=[{"role": "user", "content": extraction_prompt}],
                temperature=0.2,
                json_mode=True
            )
            data = json.loads(response)
            return data.get("ingredients", [])
        except Exception as e:
            print(f"Warning: Ingredient extraction failed: {str(e)}")
            return []
    
    def confirm_ingredients_cli(
        self, 
        ingredients: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Interactive CLI confirmation flow.
        Returns list of confirmed/edited ingredients.
        """
        if not ingredients:
            return []
        
        confirmed = []
        
        print(f"\n{'─' * 60}")
        print(
            f"I found {len(ingredients)} recurring ingredients "
            f"in your recent logs."
        )
        print("Let me confirm them with you quickly.\n")
        
        for i, ingredient in enumerate(ingredients, 1):
            print(f"{'─' * 60}")
            print(f"{i}/{len(ingredients)}  {ingredient['name']}")
            
            if ingredient.get('composition'):
                print(f"     Composition: {ingredient['composition']}")
            
            if ingredient.get('typical_amount'):
                print(
                    f"     Typical amount: {ingredient['typical_amount']}"
                )
            
            per_100g = ingredient.get('per_100g', {})
            print(f"\n     My estimates per 100g:")
            print(
                f"     Calories: {per_100g.get('calories', 0)}  ·  "
                f"Protein: {per_100g.get('protein', 0)}g  ·  "
                f"Carbs: {per_100g.get('carbs', 0)}g  ·  "
                f"Fats: {per_100g.get('fats', 0)}g  ·  "
                f"Fiber: {per_100g.get('fiber', 0)}g"
            )
            
            if ingredient.get('notes'):
                print(f"     Note: {ingredient['notes']}")
            
            print(
                f"\n     [Enter/y] Confirm  "
                f"[e] Edit values  "
                f"[s] Skip"
            )
            
            while True:
                response = input("     > ").strip().lower()
                
                if response in ['', 'y', 'yes']:
                    # Confirmed as-is
                    confirmed.append(
                        self._format_for_profile(ingredient)
                    )
                    print(f"     ✅ Added")
                    break
                
                elif response == 'e':
                    # Edit mode
                    edited = self._edit_ingredient_cli(ingredient)
                    if edited:
                        confirmed.append(
                            self._format_for_profile(edited)
                        )
                        print(f"     ✅ Added (edited)")
                    break
                
                elif response in ['s', 'n', 'skip']:
                    print(f"     ⏭  Skipped")
                    break
                
                else:
                    print(
                        "     Please press Enter to confirm, "
                        "'e' to edit, or 's' to skip"
                    )
        
        print(f"\n{'─' * 60}")
        print(f"✅ {len(confirmed)} ingredients added to your profile")
        
        return confirmed
    
    def _edit_ingredient_cli(
        self, 
        ingredient: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Interactive edit flow for a single ingredient."""
        print(f"\n     Editing: {ingredient['name']}")
        print("     Press Enter to keep current value\n")
        
        per_100g = ingredient.get('per_100g', {})
        
        def get_value(field, current, unit=""):
            prompt = f"     {field.capitalize():10} [{current}{unit}]: "
            response = input(prompt).strip()
            if not response:
                return current
            try:
                return float(response) if '.' in response else int(response)
            except ValueError:
                return current
        
        new_calories = get_value("Calories", per_100g.get('calories', 0))
        new_protein = get_value("Protein", per_100g.get('protein', 0), "g")
        new_carbs = get_value("Carbs", per_100g.get('carbs', 0), "g")
        new_fats = get_value("Fats", per_100g.get('fats', 0), "g")
        new_fiber = get_value("Fiber", per_100g.get('fiber', 0), "g")
        
        current_notes = ingredient.get('notes', '')
        notes_input = input(
            f"     Notes      [{current_notes}]: "
        ).strip()
        new_notes = notes_input if notes_input else current_notes
        
        return {
            **ingredient,
            'per_100g': {
                'calories': new_calories,
                'protein': new_protein,
                'carbs': new_carbs,
                'fats': new_fats,
                'fiber': new_fiber
            },
            'notes': new_notes
        }
    
    def _format_for_profile(
        self, 
        ingredient: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert extracted ingredient to User Profile format."""
        per_100g = ingredient.get('per_100g', {})
        
        formatted = {
            'name': ingredient['name'],
            'serving': ingredient.get('typical_amount', '100g'),
            'calories': per_100g.get('calories', 0),
            'protein': per_100g.get('protein', 0),
            'carbs': per_100g.get('carbs', 0),
            'fats': per_100g.get('fats', 0),
            'fiber': per_100g.get('fiber', 0),
        }
        
        # Add composition if present (for seed mixes etc.)
        if ingredient.get('composition'):
            formatted['composition'] = ingredient['composition']
        
        # Add notes if present
        if ingredient.get('notes'):
            formatted['notes'] = ingredient['notes']
        
        return formatted
    
    def save_ingredients(
        self, 
        ingredients: List[Dict[str, Any]]
    ) -> bool:
        """
        Save confirmed ingredients to User Profile.
        Merges with any existing ingredients (doesn't replace).
        """
        if not ingredients:
            return True
        
        try:
            profile = self.reader.read_user_profile()
            if not profile:
                print(
                    "Warning: User profile not found. "
                    "Cannot save ingredients."
                )
                return False
            
            # Merge with existing — don't overwrite ingredients
            # that are already in the profile
            existing = profile.get('known_ingredients', [])
            existing_names = {
                i['name'].lower() for i in existing
            }
            
            new_ingredients = [
                i for i in ingredients
                if i['name'].lower() not in existing_names
            ]
            
            profile['known_ingredients'] = existing + new_ingredients
            self.writer.write_user_profile(profile)
            
            return True
            
        except Exception as e:
            print(f"Warning: Could not save ingredients: {str(e)}")
            return False
    
    def run(self) -> int:
        """
        Run the full ingredient seeding flow.
        Returns the number of ingredients added.
        """
        if not self.has_enough_logs():
            print(
                "\nNot enough log history to extract ingredients. "
                "Log a few days first and run /seed-ingredients later."
            )
            return 0
        
        print("\n🔍 Scanning your log history for recurring ingredients...")
        ingredients = self.extract_ingredients()
        
        if not ingredients:
            print(
                "\nNo recurring ingredients found. "
                "You can add them manually to your User Profile.md, "
                "or run /seed-ingredients after logging a few more days."
            )
            return 0
        
        confirmed = self.confirm_ingredients_cli(ingredients)
        
        if confirmed:
            self.save_ingredients(confirmed)
            return len(confirmed)
        
        return 0


# Made with Bob