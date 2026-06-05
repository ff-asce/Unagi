"""Test for intent detection fast-path improvements.

This test ensures that common food logging phrases are correctly
identified as 'log' intent without relying on LLM classification.
"""

from agent.chat import ChatAgent


def test_intent_detection_fast_paths():
    """Test that common food logging phrases are detected via fast-path."""
    agent = ChatAgent()
    
    # Test "I ate" pattern
    assert agent.detect_intent("I ate 140 grams of rice") == "log"
    
    # Test "I had" pattern
    assert agent.detect_intent("I had 200g chicken for lunch") == "log"
    
    # Test quantity detection (grams)
    assert agent.detect_intent("Consumed 50 grams of almonds") == "log"
    
    # Test quantity detection (ml)
    assert agent.detect_intent("Drank 250 ml of milk") == "log"
    
    # Test explicit log command
    assert agent.detect_intent("log 100g oats") == "log"
    
    # Test meal prefix
    assert agent.detect_intent("breakfast: eggs and toast") == "log"
    
    # Test questions should be chat
    assert agent.detect_intent("How am I doing?") == "chat"
    assert agent.detect_intent("What should I eat?") == "chat"
    
    print("✅ All intent detection fast-path tests passed!")


if __name__ == "__main__":
    test_intent_detection_fast_paths()
