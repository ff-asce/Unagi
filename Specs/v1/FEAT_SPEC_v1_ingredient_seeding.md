# 🐍 UNAGI — Feature Spec: Ingredient Seeding
### `specs/v1/FEAT_SPEC_v1_ingredient_seeding.md`
**Version:** 1.0
**Status:** Ready for implementation
**Last Updated:** 2026-05-26
**Applies To:** Post-onboarding, post-migration flow
**Companion Specs:** `FIX_SPEC_v1.md`, `ARCH_SPEC_v1.md`, `FEAT_SPEC_v1_migration.md`

---

## Problem Statement

After onboarding, `User Profile.md` has an empty `known_ingredients` list:

```yaml
known_ingredients: []
```

The agent's nutritional reasoning relies on this list to give accurate results for the user's recurring foods. Without it:

- `"yogurt"` is estimated generically instead of using Amul Masti Dahi's exact macros
- `"soaked seeds"` is unknown — the agent can't know it's 18g Chia + 6g Basil
- `"peanut oil"` is estimated without knowing the user's typical 1 tsp amounts
- Every log entry on day one is less accurate than the logs the user already has

The user has months of log history. Their recurring ingredients are already documented in their existing logs — the agent just hasn't read them yet.

Ingredient seeding extracts this knowledge automatically from existing logs and asks the user to confirm it, turning months of implicit history into explicit profile knowledge in a single post-onboarding step.

---

## User Story

> As a user who has just onboarded and migrated my existing logs, I want Unagi to scan my log history, identify my frequently used ingredients, and ask me to confirm their details — so the agent immediately knows my food vocabulary without me having to manually type it all in.

**Acceptance criteria:**
- After onboarding + migration, ingredient seeding runs automatically
- The agent scans the last 30 days of migrated logs (or all available if fewer)
- Recurring ingredients are extracted from meal description strings
- The LLM is used to identify and deduplicate ingredients from natural language descriptions
- The user is shown a list of detected ingredients with estimated macros
- The user can confirm, edit, or skip each ingredient
- Confirmed ingredients are written to `User Profile.md` under `known_ingredients`
- The flow is conversational and fast — not a data entry form
- Ingredient seeding can be re-run via `/seed-ingredients` command
- The agent can add new ingredients to the profile at any time when it notices a new food

---

## What Gets Extracted

From meal descriptions like:

```
"450g Chicken Breast (r) in 150g Amul Masti Dahi sauce + spices (1 tsp Peanut Oil).
Side: 150g raw carrots. Drank soaked seeds (18g Chia + 6g Basil)."
```

The seeder should extract:
- `Chicken Breast (raw)` — appears frequently, large quantities
- `Amul Masti Dahi` — specific brand name, recurring
- `Peanut Oil` — recurring, small amounts (1 tsp)
- `Soaked Seeds Mix` — recurring, with composition (18g Chia + 6g Basil)
- `Carrots (raw)` — recurring vegetable

**Not extracted:**
- Generic spices (no macro significance)
- Green tea / cold brew (beverages with near-zero macros, unless frequently large)
- One-off ingredients that appear in only one log

---

## Extraction Logic

### Step 1 — Collect meal strings from recent logs

```python
def collect_meal_strings(logs: List[Dict], days: int = 30) -> List[str]:
    """
    Extract all non-empty meal description strings from recent logs.
    Returns a flat list of meal description strings.
    """
    meal_strings = []
    for log in logs[:days]:
        for field in ['breakfast', 'lunch', 'dinner', 'misc']:
            value = log.get(field, '—')
            if value and value != '—':
                meal_strings.append(value)
    return meal_strings
```

### Step 2 — LLM extraction pass

Send the collected meal strings to the LLM with a specialized extraction prompt. This is a one-time call, not a per-message call — it runs once during seeding.

**Extraction prompt:**
```
You are analyzing a user's food log history to extract their recurring ingredients.

Below are meal description strings from the past 30 days of food logs.
Extract a list of ingredients that appear FREQUENTLY (in multiple log entries).

For each ingredient, provide:
- name: The specific name used (preserve brand names like "Amul Masti Dahi")  
- typical_amount: The most common amount used (e.g. "150g", "1 tsp", "18g Chia + 6g Basil")
- category: one of: protein, dairy, vegetable, fat, grain, seeds, beverage, other
- estimated_macros_per_100g: {calories, protein, carbs, fats, fiber}
- notes: any special info (e.g. "raw weight", "composition: 18g Chia + 6g Basil seeds")

Rules:
- Preserve brand names exactly as written (Amul Masti Dahi, not "yogurt")
- For ingredient compositions (soaked seeds), capture the full composition
- Skip generic spices — they have negligible macro impact
- Skip one-off ingredients that appear only once
- Consolidate duplicates (e.g. "Chicken Breast (r)" and "chicken breast (raw weight)" are the same)
- Return ONLY valid JSON, no other text

Return format:
{
  "ingredients": [
    {
      "name": "Amul Masti Dahi",
      "typical_amount": "150g",
      "category": "dairy",
      "estimated_macros_per_100g": {
        "calories": 60,
        "protein": 3.5,
        "carbs": 5.0,
        "fats": 2.5,
        "fiber": 0
      },
      "notes": "Full-fat yogurt, commonly used as sauce base"
    }
  ]
}

Meal log history:
{meal_strings}
```

### Step 3 — User confirmation flow

Present each extracted ingredient conversationally, not as a form:

```
I scanned your last 30 days of logs and found these recurring ingredients.
Let me go through them with you quickly — just confirm or correct each one.

─────────────────────────────────────────────────────────
1/5  Chicken Breast (raw)
     I see this in almost every log — usually 400-500g raw weight.
     
     My estimates per 100g:
     Calories: 110  ·  Protein: 23g  ·  Carbs: 0g  ·  Fats: 2.5g
     
     ✓ Looks right  ·  e Edit  ·  s Skip
─────────────────────────────────────────────────────────
```

User responses:
- `Enter` or `y` or `✓` → confirmed, add to profile as-is
- `e` → open edit mode for that ingredient
- `s` or `n` → skip this ingredient (don't add to profile)

Edit mode:
```
Editing: Amul Masti Dahi
Current values (per 100g):
  Calories: 60 · Protein: 3.5g · Carbs: 5g · Fats: 2.5g

Enter corrected values, or press Enter to keep current:
  Calories [60]: _
  Protein  [3.5g]: _
  Carbs    [5g]: _
  Fats     [2.5g]: _
  Fiber    [0g]: _
  Notes    [Full-fat yogurt]: _
```

### Step 4 — Write to profile

After all confirmations, write the confirmed ingredients to `User Profile.md`:

```yaml
known_ingredients:
  - name: "Chicken Breast (raw)"
    serving: "100g"
    calories: 110
    protein: 23
    carbs: 0
    fats: 2.5
    fiber: 0
    notes: "Raw weight. Account for ~25% cooking loss."
  
  - name: "Amul Masti Dahi"
    serving: "100g"
    calories: 60
    protein: 3.5
    carbs: 5.0
    fats: 2.5
    fiber: 0
    notes: "Full-fat yogurt, used as sauce base"
  
  - name: "Soaked Seeds Mix"
    serving: "24g"
    calories: 117
    protein: 4.2
    carbs: 9.8
    fats: 6.1
    fiber: 8.4
    composition: "18g Chia seeds + 6g Basil seeds"
    notes: "Daily soaked seeds, always taken together"
```

---

## File: `onboarding/ingredient_seeder.py`

```python
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
```

---

## Integration Points

### In `main.py` — Run after onboarding and migration

```python
# After onboarding completes and migration runs:
from onboarding.ingredient_seeder import IngredientSeeder

seeder = IngredientSeeder(
    llm_client=container.llm_client,
    vault_reader=container.vault_reader,
    vault_writer=container.vault_writer
)

if not seeder.has_known_ingredients() and seeder.has_enough_logs():
    print(
        "\n📋 Before we start, let me scan your log history "
        "to learn your common ingredients."
    )
    print(
        "   This helps me give you more accurate nutritional "
        "estimates going forward.\n"
    )
    
    response = input(
        "Scan logs for common ingredients? "
        "(yes/no, takes ~10 seconds) "
    ).strip().lower()
    
    if response in ['yes', 'y', '']:
        count = seeder.run()
        if count > 0:
            print(
                f"\n✅ Added {count} ingredients to your profile. "
                f"I'll use these for accurate tracking going forward.\n"
            )
        else:
            print(
                "\nNo ingredients added. "
                "You can run /seed-ingredients later.\n"
            )
```

### In CLI command handler — `/seed-ingredients`

```python
elif cmd == '/seed-ingredients':
    from onboarding.ingredient_seeder import IngredientSeeder
    seeder = IngredientSeeder(
        llm_client=self.container.llm_client,
        vault_reader=self.container.vault_reader,
        vault_writer=self.container.vault_writer
    )
    
    # Check if already seeded
    if seeder.has_known_ingredients():
        response = input(
            "You already have known ingredients. "
            "Scan for new ones? (yes/no) "
        ).strip().lower()
        if response not in ['yes', 'y']:
            return
    
    count = seeder.run()
    if count > 0:
        # Invalidate context cache so new ingredients are
        # picked up immediately
        self.container.context_manager.invalidate()
        print(
            f"\n✅ {count} ingredients added. "
            f"They'll be used from your next log entry.\n"
        )
```

### Agent-initiated seeding (future Phase 2 hook)

In Phase 2, when the agent notices a new ingredient appearing multiple times, it can proactively suggest adding it. This is a stub for now:

```python
# In NutritionPipeline, after writing a log (Phase 2 hook):
def _check_for_new_ingredients(
    self, 
    log_data: Dict, 
    profile: Dict
) -> Optional[str]:
    """
    Check if today's log contains ingredients not in the profile.
    Returns a suggestion string if new ingredients found, else None.
    
    Phase 2: implement this. Phase 1: leave as stub.
    """
    return None
```

---

## `onboarding/__init__.py` — Updated exports

```python
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
```

---

## Complete First-Run Flow

This is the full ordered sequence when a new user runs Unagi for the first time with existing vault logs:

```
1. Load config (main.py)
   ↓
2. Detect old vault structure (migration)
   "Found 63 log files from 24 March → 29 May 2026. Migrate? (yes/no)"
   ↓
3. Run migration if confirmed
   Progress bar, validation report, git commit
   ↓
4. Run onboarding (user profile creation)
   Name, DOB, weight, height, gender, goal, maintenance
   ↓
5. Run ingredient seeding
   "Scanning your logs for common ingredients..."
   LLM extraction pass, confirmation flow, save to profile
   ↓
6. Launch main UI
   Startup screen with populated stats from migrated history
```

---

## Edge Cases

| Scenario | Handling |
|---|---|
| No logs available | Skip seeding, show message, offer to run later |
| Fewer than 3 logs | Skip seeding — too few to identify patterns |
| LLM extraction returns nothing | Show message, suggest manual profile edit |
| LLM extraction fails (API error) | Show error, offer to retry or skip |
| User skips all ingredients | Graceful — profile stays empty, suggest running later |
| User already has known_ingredients | Ask before re-seeding, merge don't replace |
| Same ingredient with two names | LLM should consolidate, but if not — both get added |
| Ingredient with no macro data | Still add with zeros, flag for manual update |
| Profile write fails | Show error, don't crash — ingredients available on next run |
| `/seed-ingredients` run after adding new logs | Finds only ingredients not already in profile |

---

## Testing Checklist

- [ ] `has_enough_logs()` returns False when fewer than 3 logs exist
- [ ] `has_enough_logs()` returns True when 3+ logs exist
- [ ] `has_known_ingredients()` returns False on fresh profile
- [ ] `has_known_ingredients()` returns True after seeding
- [ ] `extract_ingredients()` returns non-empty list from real log history
- [ ] Brand names are preserved (Amul Masti Dahi, not yogurt)
- [ ] Seed mix composition is captured (18g Chia + 6g Basil)
- [ ] Generic spices are not included
- [ ] One-off ingredients are not included
- [ ] Confirmation flow: Enter/y adds ingredient
- [ ] Confirmation flow: e opens edit mode
- [ ] Confirmation flow: s skips ingredient
- [ ] Edit mode: pressing Enter keeps current value
- [ ] Edit mode: entering a new value updates it correctly
- [ ] `save_ingredients()` merges with existing, doesn't replace
- [ ] `save_ingredients()` doesn't add duplicate names
- [ ] Context cache is invalidated after seeding
- [ ] `/seed-ingredients` command works after initial setup
- [ ] Re-running seeding doesn't duplicate existing ingredients
- [ ] Seeding works with 0 logs gracefully (no crash)
- [ ] Seeding works when LLM returns empty list gracefully

---

*Unagi Ingredient Seeding Spec v1 — Built with 🐍 total food awareness.*
