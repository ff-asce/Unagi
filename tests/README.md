# UNAGI Test Suite

This directory contains all test files for the UNAGI project.

## Test Files

### Core Functionality Tests

**test_group3.py**
- Tests for Group 3 fixes from FIX_SPEC_v1
- Validates bug fixes and improvements

**test_group4.py**
- Tests for Group 4 fixes from FIX_SPEC_v1
- Validates bug fixes and improvements

**test_group5.py**
- Tests for Group 5 fixes from FIX_SPEC_v1
- Validates bug fixes and improvements

**test_group6.py**
- Tests for Group 6 fixes from FIX_SPEC_v1
- Validates bug fixes and improvements

**test_intent_detection_fix.py**
- Tests for the critical intent detection bug fix
- Validates fast-path pattern matching
- Ensures proper intent classification

**test_migration.py**
- Comprehensive test suite for vault migration system
- Tests migration detection, validation, execution
- Tests incremental migration and cleanup
- 5 test suites covering all migration scenarios

### Utility Tests

**pre_flight_check.py**
- Pre-flight checks for system setup
- Validates dependencies and configuration
- Checks LLM connectivity

## Running Tests

### Run All Tests
```bash
cd /Users/parthjindal/Parth\ Projects/unagi
python3 -m pytest tests/
```

### Run Specific Test File
```bash
python3 -m pytest tests/test_migration.py
python3 -m pytest tests/test_intent_detection_fix.py
```

### Run with Verbose Output
```bash
python3 -m pytest tests/ -v
```

### Run Pre-flight Check
```bash
python3 tests/pre_flight_check.py
```

## Test Coverage

- ✅ FIX_SPEC_v1 fixes (Groups 3-6)
- ✅ Intent detection bug fix
- ✅ Vault migration system
- ⏳ Ingredient seeding (deferred)
- ⏳ Architectural refactor components (integration tests needed)

## Adding New Tests

When adding new tests:
1. Create test file in this directory
2. Follow naming convention: `test_<feature>.py`
3. Update this README with test description
4. Ensure tests are independent and can run in any order

## Test Dependencies

Tests require:
- pytest
- All dependencies from requirements.txt
- Valid .env configuration (for integration tests)

---

**Last Updated:** 2026-06-05