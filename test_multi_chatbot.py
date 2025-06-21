import re
import pytest
from multi_chatbot import extract_city, is_weather_query

# --- Test: City Extraction ---

@pytest.mark.parametrize("text,expected", [
    ("What's the weather in New York?", "New York"),
    ("Tell me the forecast for Tokyo", "Tokyo"),
    ("Rain update for Bengaluru", "Bengaluru"),
    ("weather in   hyderabad", "Hyderabad"),
    ("how's weather for Chennai now", "Chennai"),
])
def test_extract_city(text, expected):
    assert extract_city(text) == expected

# --- Test: Weather query detection ---

@pytest.mark.parametrize("text", [
    "What's the weather in Mumbai?",
    "Give me the temperature",
    "Will it rain in Delhi?",
    "Is it sunny today?",
])
def test_is_weather_query(text):
    assert is_weather_query(text) == True

# --- Test: Fallback AI logic (mocked) ---

def test_generic_query_summary(monkeypatch):
    # We'll fake the Gemini response
    from multi_chatbot import query_google_ai

    def fake_gemini_response(prompt):
        if "summary of python" in prompt.lower():
            return "Python is a popular programming language."
        if "3 days tour to hyderabad" in prompt.lower():
            return "Here’s a 3-day itinerary for Hyderabad."
        return "Generic AI response."

    monkeypatch.setattr("multi_chatbot.model.generate_content", lambda prompt: type('', (), {"text": fake_gemini_response(prompt)})())

    assert "Python" in query_google_ai("Give me a summary of Python")
    assert "Hyderabad" in query_google_ai("Plan a 3 days tour to Hyderabad under ₹5000")

