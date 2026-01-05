# ai_suggestions.py

import os
from openai import OpenAI
from typing import Dict
from dotenv import load_dotenv

# === ENVIRONMENT SETUP ===
load_dotenv()

# Initialize OpenAI client (reads OPENAI_API_KEY from environment)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY_HW"))

def get_nutrition_suggestion(
    consumed: Dict[str, float],
    targets: Dict[str, float]
) -> str:
    """
    Takes current consumption and targets, asks AI for a helpful suggestion.
    
    consumed: {"calories": 1500, "protein": 80, "carbs": 200, "fat": 40}
    targets:  {"calories": 2130, "protein": 160, "carbs": 240, "fat": 60}
    
    Returns: A short, actionable suggestion string.
    """
    # Calculate what's remaining
    remaining = {k: targets[k] - consumed.get(k, 0) for k in targets}
    
    # Build a simple prompt
    prompt = f"""
Based on this nutrition data, give ONE short, actionable food suggestion (max 2 sentences).

Consumed today:
- Calories: {consumed.get('calories', 0):.0f} kcal
- Protein: {consumed.get('protein', 0):.0f}g
- Carbs: {consumed.get('carbs', 0):.0f}g
- Fat: {consumed.get('fat', 0):.0f}g

Remaining to hit targets:
- Calories: {remaining['calories']:.0f} kcal
- Protein: {remaining['protein']:.0f}g
- Carbs: {remaining['carbs']:.0f}g
- Fat: {remaining['fat']:.0f}g

Focus on the biggest gap. Be specific about foods and portions.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # cheap and fast for simple suggestions
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100,
        temperature=0.7
    )
    
    return response.choices[0].message.content.strip()


# Quick test when running this file directly
if __name__ == "__main__":
    # Example data
    test_consumed = {"calories": 1500, "protein": 80, "carbs": 180, "fat": 45}
    test_targets = {"calories": 2130, "protein": 160, "carbs": 240, "fat": 60}
    
    suggestion = get_nutrition_suggestion(test_consumed, test_targets)
    print("💡 AI Suggestion:")
    print(suggestion)