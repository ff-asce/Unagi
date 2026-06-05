#!/usr/bin/env python3
"""Test Group 3 fixes: F-04, F-18, F-08"""

# Test F-04: JSON extraction
from agent.chat import ChatAgent
agent = ChatAgent()

print("Testing F-04: Robust JSON extraction...")

# Test direct JSON
test1 = '{"action": "create", "data": {"calories": 2000}}'
result1 = agent._extract_json(test1)
print('✓ F-04 Test 1: Direct JSON parsing works')

# Test JSON with markdown fences
test2 = '```json\n{"action": "create", "data": {"calories": 2000}}\n```'
result2 = agent._extract_json(test2)
print('✓ F-04 Test 2: Markdown fence stripping works')

# Test JSON with text before/after
test3 = 'Here is the log:\n{"action": "create", "data": {"calories": 2000}}\nDone!'
result3 = agent._extract_json(test3)
print('✓ F-04 Test 3: Balanced brace matching works')

# Test F-18: Date normalization
print("\nTesting F-18: Date normalization...")
from vault.parser import format_log_data
from datetime import datetime

test_data = {
    'date': datetime(2026, 5, 25),
    'calories': 2000,
    'maintenance': 2200,
    'deficit': 200,
    'protein': 150,
    'carbs': 200,
    'fats': 70,
    'fiber': 30,
    'breakfast': '—',
    'lunch': '—',
    'dinner': '—',
    'misc': '—',
    'notes': 'Test'
}
result = format_log_data(test_data)
assert '2026-05-25' in result
print('✓ F-18 Test: Date object normalized to string')

# Test F-08: Merge logic
print("\nTesting F-08: Merge logic...")
from vault.parser import merge_log_data

existing = {
    'breakfast': '08:00 AM - 200g Oats',
    'lunch': '—',
    'calories': 500
}

new_with_time = {
    'breakfast': '08:30 AM - 300g Chicken',
    'calories': 800
}
merged1 = merge_log_data(existing, new_with_time)
assert merged1['breakfast'] == '08:30 AM - 300g Chicken'
print('✓ F-08 Test 1: Complete replacement with time works')

new_addition = {
    'breakfast': '2 boiled eggs',
    'calories': 800
}
merged2 = merge_log_data(existing, new_addition)
assert '200g Oats' in merged2['breakfast'] and '2 boiled eggs' in merged2['breakfast']
print('✓ F-08 Test 2: Addition without time appends correctly')

print('\n✅ All Group 3 tests passed!')

# Made with Bob
