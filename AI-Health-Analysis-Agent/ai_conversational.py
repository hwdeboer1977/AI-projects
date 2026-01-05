# ai_conversational.py

import os
from openai import OpenAI
from typing import Dict, Optional
from datetime import date, timedelta
from dotenv import load_dotenv

# === ENVIRONMENT SETUP ===
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY_HW"))


def format_data_context(
    nut_by_day: Dict[date, Dict[str, float]],
    ex_by_day: Dict[date, Dict],
    num_days: int = 14
) -> str:
    """
    Formats recent data as context for the AI to reference when answering questions.
    
    Default 14 days gives enough history for most queries.
    """
    lines = []
    today = date.today()
    
    for i in range(num_days):
        d = today - timedelta(days=i)
        day_name = d.strftime("%A")
        
        nut = nut_by_day.get(d, {})
        ex = ex_by_day.get(d, {})
        
        # Nutrition
        if nut:
            cal = nut.get("calories", 0)
            pro = nut.get("protein", 0)
            carbs = nut.get("carbs", 0)
            fat = nut.get("fat", 0)
            nut_str = f"{cal:.0f} kcal, P:{pro:.0f}g, C:{carbs:.0f}g, F:{fat:.0f}g"
        else:
            nut_str = "no data"
        
        # Exercise
        if ex and ex.get("minutes", 0) > 0:
            mins = ex.get("minutes", 0)
            types = ", ".join(ex.get("types", {}).keys()) or "unknown"
            ex_str = f"{mins:.0f} min ({types})"
        else:
            ex_str = "none"
        
        lines.append(f"{day_name} {d}: Nutrition: {nut_str} | Exercise: {ex_str}")
    
    return "\n".join(lines)


def ask_nutrition_question(
    question: str,
    nut_by_day: Dict[date, Dict[str, float]],
    ex_by_day: Dict[date, Dict],
    targets: Dict[str, float]
) -> str:
    """
    Answer any natural language question about the user's nutrition/exercise data.
    
    The AI has access to recent history and can interpret queries like:
    - "What did I eat last Tuesday?"
    - "How's my protein this week?"
    - "Compare my weekday vs weekend eating"
    """
    today = date.today()
    data_context = format_data_context(nut_by_day, ex_by_day, num_days=14)
    
    prompt = f"""You are a helpful nutrition assistant with access to the user's food and exercise log.

Today's date: {today} ({today.strftime("%A")})

Daily targets: {targets['calories']:.0f} kcal, P:{targets['protein']:.0f}g, C:{targets['carbs']:.0f}g, F:{targets['fat']:.0f}g

Recent history (most recent first):
{data_context}

User question: {question}

Instructions:
- Answer based ONLY on the data provided
- Be concise (2-3 sentences max)
- If data is missing, say so
- Use specific numbers when relevant
- Be friendly and helpful
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
        temperature=0.5  # Lower temperature for factual answers
    )
    
    return response.choices[0].message.content.strip()


def chat_loop(
    nut_by_day: Dict[date, Dict[str, float]],
    ex_by_day: Dict[date, Dict],
    targets: Dict[str, float]
):
    """
    Interactive chat loop for testing conversational queries.
    Type 'quit' to exit.
    """
    print("💬 Nutrition Assistant")
    print("Ask me anything about your nutrition and exercise data.")
    print("Type 'quit' to exit.\n")
    
    while True:
        question = input("You: ").strip()
        
        if question.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        
        if not question:
            continue
        
        answer = ask_nutrition_question(question, nut_by_day, ex_by_day, targets)
        print(f"\n🤖 Assistant: {answer}\n")


# === TEST WITH SAMPLE DATA ===
if __name__ == "__main__":
    
    # Create sample 2 weeks of data
    today = date.today()
    
    sample_nutrition = {}
    sample_exercise = {}
    
    # Generate realistic sample data for 14 days
    import random
    random.seed(42)  # Reproducible results
    
    for i in range(14):
        d = today - timedelta(days=i)
        day_name = d.strftime("%A")
        
        # Weekends have different patterns
        is_weekend = day_name in ["Saturday", "Sunday"]
        
        sample_nutrition[d] = {
            "calories": random.randint(2200, 2800) if is_weekend else random.randint(1900, 2200),
            "protein": random.randint(90, 120) if is_weekend else random.randint(140, 170),
            "carbs": random.randint(250, 350) if is_weekend else random.randint(200, 260),
            "fat": random.randint(70, 100) if is_weekend else random.randint(50, 70),
        }
        
        # Exercise more on weekdays
        if is_weekend:
            if random.random() > 0.5:
                sample_exercise[d] = {"minutes": random.randint(30, 90), "sessions": 1, "types": {"Cycling": 1}}
        else:
            if random.random() > 0.3:
                ex_type = random.choice(["Weights", "Running", "Swimming"])
                sample_exercise[d] = {"minutes": random.randint(30, 60), "sessions": 1, "types": {ex_type: 1}}
    
    targets = {"calories": 2130, "protein": 160, "carbs": 240, "fat": 60}
    
    # Start interactive chat
    chat_loop(sample_nutrition, sample_exercise, targets)