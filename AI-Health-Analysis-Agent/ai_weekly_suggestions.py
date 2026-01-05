# ai_weekly_coach.py

import os
from openai import OpenAI
from typing import Dict, List
from datetime import date
from dotenv import load_dotenv

# === ENVIRONMENT SETUP ===
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY_HW"))


def format_week_data(
    nut_by_day: Dict[date, Dict[str, float]],
    ex_by_day: Dict[date, Dict],
    days: List[date],
    targets: Dict[str, float]
) -> str:
    """
    Formats a week of nutrition and exercise data into a readable string for the AI.
    
    This is the 'bridge' between your raw data and the AI prompt.
    """
    lines = []
    
    for d in sorted(days):
        nut = nut_by_day.get(d, {})
        ex = ex_by_day.get(d, {})
        
        # Format nutrition
        cal = nut.get("calories", 0)
        pro = nut.get("protein", 0)
        carbs = nut.get("carbs", 0)
        fat = nut.get("fat", 0)
        
        # Format exercise
        mins = ex.get("minutes", 0)
        sessions = ex.get("sessions", 0)
        types = ex.get("types", {})
        type_str = ", ".join(types.keys()) if types else "none"
        
        # Day name for context (Monday, Tuesday, etc.)
        day_name = d.strftime("%A")
        
        lines.append(
            f"{day_name} ({d}): "
            f"{cal:.0f} kcal, P:{pro:.0f}g, C:{carbs:.0f}g, F:{fat:.0f}g | "
            f"Exercise: {mins:.0f} min ({type_str})"
        )
    
    # Add targets for context
    header = f"""Daily targets: {targets['calories']:.0f} kcal, P:{targets['protein']:.0f}g, C:{targets['carbs']:.0f}g, F:{targets['fat']:.0f}g

Day-by-day breakdown:
"""
    
    return header + "\n".join(lines)


def get_weekly_coaching(
    nut_by_day: Dict[date, Dict[str, float]],
    ex_by_day: Dict[date, Dict],
    days: List[date],
    targets: Dict[str, float]
) -> str:
    """
    Sends a week of data to AI and gets personalized coaching insights.
    
    Returns 2-3 actionable observations about patterns and improvements.
    """
    # Prepare the data as readable text
    week_summary = format_week_data(nut_by_day, ex_by_day, days, targets)
    
    prompt = f"""You are a supportive nutrition and fitness coach. Analyze this week's data and provide exactly 3 brief insights.

{week_summary}

Guidelines:
- Look for PATTERNS (not just single days)
- Compare weekdays vs weekends if relevant
- Note consistency or inconsistency
- Connect nutrition to exercise days
- Be encouraging but honest
- Each insight should be 1-2 sentences max

Format your response as:
1. [Insight about patterns]
2. [Insight about what's working or needs work]  
3. [One specific actionable tip for next week]
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.7
    )
    
    return response.choices[0].message.content.strip()


# === TEST WITH SAMPLE DATA ===
if __name__ == "__main__":
    from datetime import timedelta
    
    # Create sample week of data
    today = date.today()
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]  # Last 7 days, oldest first
    
    # Sample nutrition data (realistic variation)
    sample_nutrition = {
        days[0]: {"calories": 2100, "protein": 155, "carbs": 230, "fat": 58},  # Monday
        days[1]: {"calories": 1950, "protein": 140, "carbs": 220, "fat": 55},  # Tuesday
        days[2]: {"calories": 2200, "protein": 160, "carbs": 250, "fat": 62},  # Wednesday
        days[3]: {"calories": 2050, "protein": 150, "carbs": 235, "fat": 57},  # Thursday
        days[4]: {"calories": 2400, "protein": 120, "carbs": 300, "fat": 80},  # Friday (eating out?)
        days[5]: {"calories": 2600, "protein": 100, "carbs": 320, "fat": 90},  # Saturday
        days[6]: {"calories": 1800, "protein": 130, "carbs": 200, "fat": 50},  # Sunday
    }
    
    # Sample exercise data
    sample_exercise = {
        days[0]: {"minutes": 45, "sessions": 1, "types": {"Weights": 1}},
        days[1]: {"minutes": 0, "sessions": 0, "types": {}},
        days[2]: {"minutes": 30, "sessions": 1, "types": {"Running": 1}},
        days[3]: {"minutes": 45, "sessions": 1, "types": {"Weights": 1}},
        days[4]: {"minutes": 0, "sessions": 0, "types": {}},
        days[5]: {"minutes": 60, "sessions": 1, "types": {"Cycling": 1}},
        days[6]: {"minutes": 0, "sessions": 0, "types": {}},
    }
    
    targets = {"calories": 2130, "protein": 160, "carbs": 240, "fat": 60}
    
    print("📊 Week data being sent to AI:\n")
    print(format_week_data(sample_nutrition, sample_exercise, days, targets))
    print("\n" + "="*50 + "\n")
    
    print("🏋️ Weekly Coach Insights:\n")
    coaching = get_weekly_coaching(sample_nutrition, sample_exercise, days, targets)
    print(coaching)