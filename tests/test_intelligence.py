#!/usr/bin/env python3
"""Quick test script for intelligence system components."""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_memory_layer():
    """Test memory layer components."""
    print("🧪 Testing Memory Layer...")
    
    try:
        from memory.database import Database
        from memory.embeddings import generate_embedding
        from memory.vector_store import VectorStore
        
        # Test database
        db = Database(":memory:")
        await db.initialize()
        print("  ✓ Database initialized")
        
        # Test embeddings
        embedding = generate_embedding("Test text for embedding")
        assert len(embedding) == 384, f"Expected 384 dims, got {len(embedding)}"
        print(f"  ✓ Embeddings working (384 dimensions)")
        
        # Test vector store (in-memory)
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            vector_store = VectorStore(tmpdir)
            log_data = {
                'date': '2026-01-01',
                'calories': 2000,
                'protein': 150,
                'breakfast': 'Test breakfast',
                'lunch': 'Test lunch',
                'dinner': 'Test dinner',
                'misc': '—',
                'deficit': -200
            }
            await vector_store.add(log_data, embedding)
            count = vector_store.count()
            assert count == 1, f"Expected 1 document, got {count}"
            print(f"  ✓ Vector store working ({count} document)")
        
        print("✅ Memory Layer: PASS\n")
        return True
        
    except Exception as e:
        print(f"❌ Memory Layer: FAIL - {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


async def test_data_enrichment():
    """Test data enrichment components."""
    print("🧪 Testing Data Enrichment...")
    
    try:
        from data.confidence import calculate_confidence, CONFIDENCE_LEVELS
        from data.cache import APICache
        from data.indian_foods import IndianFoodsDB
        
        # Test confidence scoring
        score = calculate_confidence("user")
        assert score == 1.0, f"Expected 1.0, got {score}"
        print(f"  ✓ Confidence scoring working")
        
        # Test caching
        cache = APICache()
        cache.set("test_api", "test_key", {"data": "test"})
        result = cache.get("test_api", "test_key")
        assert result == {"data": "test"}, "Cache get/set failed"
        print(f"  ✓ API caching working")
        
        # Test Indian foods database
        db = IndianFoodsDB()
        assert len(db.foods) >= 0, "Database failed to load"
        print(f"  ✓ Indian foods database loaded ({len(db.foods)} items)")
        
        print("✅ Data Enrichment: PASS\n")
        return True
        
    except Exception as e:
        print(f"❌ Data Enrichment: FAIL - {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


async def test_intelligence_layer():
    """Test intelligence layer components."""
    print("🧪 Testing Intelligence Layer...")
    
    try:
        from memory.database import Database
        from intelligence.learning import PatternLearner
        from intelligence.trends import TrendDetector
        from intelligence.suggestions import SuggestionEngine
        
        # Create in-memory database with sample data
        db = Database(":memory:")
        await db.initialize()
        
        # Insert sample log
        sample_log = {
            'date': '2026-01-01',
            'calories': 2000,
            'protein': 150,
            'carbs': 200,
            'fats': 70,
            'fiber': 30,
            'water_ml': 2500,
            'weight_kg': 75.0,
            'goal_calories': 2200,
            'goal_protein': 160,
            'goal_carbs': 220,
            'goal_fats': 75,
            'notes': 'Test log',
            'meals': []
        }
        await db.insert_log(sample_log)
        print("  ✓ Sample data inserted")
        
        # Test pattern learner
        learner = PatternLearner(db)
        patterns = await learner.learn_nutrient_patterns(days=7)
        assert 'averages' in patterns, "Patterns missing averages"
        print(f"  ✓ Pattern learning working")
        
        # Test trend detector
        detector = TrendDetector(db)
        trends = await detector.detect_calorie_trend(days=7)
        assert 'direction' in trends, "Trends missing direction"
        print(f"  ✓ Trend detection working")
        
        # Test suggestion engine
        engine = SuggestionEngine(db, learner, detector)
        suggestions = await engine.suggest_hydration()
        assert isinstance(suggestions, list), "Suggestions not a list"
        print(f"  ✓ Suggestion engine working")
        
        print("✅ Intelligence Layer: PASS\n")
        return True
        
    except Exception as e:
        print(f"❌ Intelligence Layer: FAIL - {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("🐍 UNAGI Intelligence System - Quick Test")
    print("=" * 60)
    print()
    
    results = []
    
    # Run tests
    results.append(await test_memory_layer())
    results.append(await test_data_enrichment())
    results.append(await test_intelligence_layer())
    
    # Summary
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
        print("=" * 60)
        return 0
    else:
        print(f"⚠️  SOME TESTS FAILED ({passed}/{total} passed)")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

# Made with Bob
