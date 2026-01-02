# analytics_service.py
"""
Analytics and suggestion engine for NutritionBot.
Provides insights on remaining macros and food suggestions.
"""
import os
import json
import re
from typing import Dict, List, Optional
from dataclasses import dataclass
from db_models import get_session, FoodItem
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY_HW")
CHAT_MODEL = "gpt-4o-mini"


def get_openai_client() -> OpenAI:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY_HW is not set")
    return OpenAI(api_key=OPENAI_API_KEY)


@dataclass
class RemainingMacros:
    """What's left to hit daily targets."""
    calories: float
    protein: float
    fat: float
    carbs: float
    
    # Percentages completed
    calories_pct: float
    protein_pct: float
    fat_pct: float
    carbs_pct: float


@dataclass
class FoodSuggestion:
    """A suggested food with reasoning."""
    food: FoodItem
    reason: str  # "high protein", "low calorie", etc.
    portion: str  # "200g" or "1 piece"
    would_add: Dict[str, float]  # What this portion adds


def calculate_remaining(totals: Dict[str, float], targets: Dict[str, float]) -> RemainingMacros:
    """
    Calculate remaining macros for the day.
    
    Args:
        totals: Current day's totals {"calories": x, "protein": y, ...}
        targets: Daily targets {"calories": 2130, "protein": 160, ...}
    
    Returns:
        RemainingMacros with what's left and percentages
    """
    def remaining(key):
        return max(0, targets.get(key, 0) - totals.get(key, 0))
    
    def pct(key):
        target = targets.get(key, 0)
        if target == 0:
            return 100.0
        return min(100.0, round((totals.get(key, 0) / target) * 100, 1))
    
    return RemainingMacros(
        calories=remaining("calories"),
        protein=remaining("protein"),
        fat=remaining("fat"),
        carbs=remaining("carbs"),
        calories_pct=pct("calories"),
        protein_pct=pct("protein"),
        fat_pct=pct("fat"),
        carbs_pct=pct("carbs")
    )


def format_remaining_message(remaining: RemainingMacros) -> str:
    """Format remaining macros as a Telegram message."""
    
    # Progress bars
    def bar(pct: float) -> str:
        filled = int(pct / 10)
        empty = 10 - filled
        return "█" * filled + "░" * empty
    
    # Status emoji based on percentage
    def status(pct: float) -> str:
        if pct >= 100:
            return "✅"
        elif pct >= 75:
            return "🟢"
        elif pct >= 50:
            return "🟡"
        else:
            return "🔴"
    
    msg = "📊 *Remaining for Today*\n\n"
    
    msg += f"{status(remaining.calories_pct)} *Calories:* {remaining.calories:.0f} kcal left\n"
    msg += f"   {bar(remaining.calories_pct)} {remaining.calories_pct:.0f}%\n\n"
    
    msg += f"{status(remaining.protein_pct)} *Protein:* {remaining.protein:.0f}g left\n"
    msg += f"   {bar(remaining.protein_pct)} {remaining.protein_pct:.0f}%\n\n"
    
    msg += f"{status(remaining.fat_pct)} *Fat:* {remaining.fat:.0f}g left\n"
    msg += f"   {bar(remaining.fat_pct)} {remaining.fat_pct:.0f}%\n\n"
    
    msg += f"{status(remaining.carbs_pct)} *Carbs:* {remaining.carbs:.0f}g left\n"
    msg += f"   {bar(remaining.carbs_pct)} {remaining.carbs_pct:.0f}%"
    
    # Add summary insight
    if remaining.calories <= 0 and remaining.protein <= 0:
        msg += "\n\n🎉 *All targets hit!*"
    elif remaining.protein > 30 and remaining.calories < 300:
        msg += "\n\n⚠️ *Low calories but need protein* - try lean protein sources"
    elif remaining.protein > 50:
        msg += "\n\n💪 *Focus on protein* to hit your target"
    
    return msg


def get_suggestions(remaining: RemainingMacros, limit: int = 5) -> List[FoodSuggestion]:
    """
    Get food suggestions based on remaining macros.
    Prioritizes foods from user's database that fit their needs.
    
    Strategy:
    - If low on protein: suggest high-protein foods
    - If low on calories: suggest calorie-dense foods
    - If over on fat/carbs: suggest alternatives
    """
    session = get_session()
    suggestions = []
    
    try:
        # Get all foods from database, ordered by most used
        foods = session.query(FoodItem).order_by(FoodItem.times_used.desc()).all()
        
        if not foods:
            return []
        
        # Determine what we need most
        need_protein = remaining.protein > 20
        need_calories = remaining.calories > 300
        low_fat_budget = remaining.fat < 20
        low_carb_budget = remaining.carbs < 30
        
        for food in foods:
            if len(suggestions) >= limit:
                break
            
            # Calculate protein ratio (protein per 100 kcal)
            protein_ratio = (food.protein_per_100 / food.calories_per_100 * 100) if food.calories_per_100 > 0 else 0
            
            # Determine ideal portion based on remaining macros
            portion_size, portion_unit = calculate_ideal_portion(food, remaining)
            
            # Calculate what this portion would add
            factor = portion_size / 100.0 if portion_unit == "g" else 1
            would_add = {
                "calories": round(food.calories_per_100 * factor, 1),
                "protein": round(food.protein_per_100 * factor, 1),
                "fat": round(food.fat_per_100 * factor, 1),
                "carbs": round(food.carbs_per_100 * factor, 1)
            }
            
            # Skip if it would exceed remaining calories significantly
            if would_add["calories"] > remaining.calories + 100:
                continue
            
            # Determine reason for suggestion
            reason = None
            
            if need_protein and protein_ratio > 15:
                reason = "high protein"
            elif need_protein and food.protein_per_100 > 15:
                reason = f"{food.protein_per_100:.0f}g protein per 100g"
            elif low_fat_budget and food.fat_per_100 < 3:
                reason = "low fat"
            elif low_carb_budget and food.carbs_per_100 < 5:
                reason = "low carb"
            elif need_calories and food.calories_per_100 > 150:
                reason = "good calories"
            elif food.times_used >= 3:
                reason = "your favorite"
            
            if reason:
                suggestions.append(FoodSuggestion(
                    food=food,
                    reason=reason,
                    portion=f"{portion_size:.0f}{portion_unit}",
                    would_add=would_add
                ))
        
        # If we don't have enough suggestions, add most-used foods
        if len(suggestions) < 3:
            for food in foods[:5]:
                if not any(s.food.id == food.id for s in suggestions):
                    portion_size, portion_unit = calculate_ideal_portion(food, remaining)
                    factor = portion_size / 100.0 if portion_unit == "g" else 1
                    would_add = {
                        "calories": round(food.calories_per_100 * factor, 1),
                        "protein": round(food.protein_per_100 * factor, 1),
                        "fat": round(food.fat_per_100 * factor, 1),
                        "carbs": round(food.carbs_per_100 * factor, 1)
                    }
                    suggestions.append(FoodSuggestion(
                        food=food,
                        reason="frequently used",
                        portion=f"{portion_size:.0f}{portion_unit}",
                        would_add=would_add
                    ))
                    if len(suggestions) >= limit:
                        break
        
        return suggestions
        
    finally:
        session.close()


def calculate_ideal_portion(food: FoodItem, remaining: RemainingMacros) -> tuple:
    """
    Calculate ideal portion size based on remaining macros.
    Returns (portion_size, unit).
    """
    # Default portion
    default_size = food.default_serving or 100
    unit = food.serving_unit or "g"
    
    if unit in ["piece", "pieces", "stuk", "stuks", "serving"]:
        # For pieces, suggest 1 or 2
        return (1, unit)
    
    # For grams, calculate based on what fits
    # Don't exceed remaining calories
    if food.calories_per_100 > 0:
        max_by_cal = (remaining.calories / food.calories_per_100) * 100
    else:
        max_by_cal = 500
    
    # Aim for a reasonable portion (50-300g typically)
    ideal = min(max_by_cal, 250)
    ideal = max(ideal, 50)  # At least 50g
    
    # Round to nice numbers
    if ideal > 200:
        ideal = round(ideal / 50) * 50
    else:
        ideal = round(ideal / 25) * 25
    
    return (ideal, "g")


def format_suggestions_message(suggestions: List[FoodSuggestion], remaining: RemainingMacros) -> str:
    """Format suggestions as a Telegram message."""
    
    if not suggestions:
        return "🤔 *No suggestions yet*\n\nLog some foods first so I can learn your preferences!"
    
    msg = "💡 *Suggested Foods*\n"
    msg += f"_Based on: {remaining.protein:.0f}g protein, {remaining.calories:.0f} kcal remaining_\n\n"
    
    for i, s in enumerate(suggestions, 1):
        verified = "✓" if s.food.verified else ""
        msg += f"*{i}. {s.food.display_name}* {verified}\n"
        msg += f"   📏 {s.portion} → {s.would_add['calories']:.0f} kcal, {s.would_add['protein']:.0f}g P\n"
        msg += f"   _{s.reason}_\n\n"
    
    return msg


def get_macro_insight(remaining: RemainingMacros) -> str:
    """Generate a short insight about current macro balance."""
    
    insights = []
    
    # Check protein vs calories ratio
    if remaining.protein_pct < remaining.calories_pct - 20:
        insights.append("🥩 Protein is lagging - prioritize lean protein sources")
    
    if remaining.fat_pct > 90 and remaining.calories_pct < 70:
        insights.append("🧈 Fat target almost hit - choose low-fat options")
    
    if remaining.carbs_pct > 90 and remaining.calories_pct < 70:
        insights.append("🍞 Carbs target almost hit - choose low-carb options")
    
    if remaining.calories_pct > 100:
        insights.append("⚡ Over calorie target - consider lighter choices tomorrow")
    
    if remaining.protein_pct >= 100 and remaining.calories_pct < 80:
        insights.append("💪 Great protein intake! Room for some treats")
    
    if not insights:
        if remaining.calories_pct < 50:
            insights.append("🍽️ Plenty of room left - enjoy your meals!")
        else:
            insights.append("👍 On track for the day")
    
    return "\n".join(insights)


@dataclass
class AISuggestion:
    """An AI-generated food suggestion."""
    name: str
    portion: str
    calories: float
    protein: float
    fat: float
    carbs: float
    reason: str
    where_to_get: str  # "supermarket", "restaurant", "homemade"


def get_ai_suggestions(remaining: RemainingMacros, 
                       db_suggestions: List[FoodSuggestion],
                       limit: int = 5) -> List[AISuggestion]:
    """
    Get AI-powered food suggestions based on remaining macros.
    Complements database suggestions with new ideas.
    
    Args:
        remaining: What macros are left for the day
        db_suggestions: Already suggested foods from database (to avoid duplicates)
        limit: Number of AI suggestions to generate
    
    Returns:
        List of AI-generated suggestions
    """
    try:
        client = get_openai_client()
    except RuntimeError:
        return []  # No API key, skip AI suggestions
    
    # Build context about what's already suggested
    already_suggested = [s.food.display_name for s in db_suggestions]
    
    # Determine priority
    priorities = []
    if remaining.protein > 30:
        priorities.append(f"HIGH PROTEIN (need {remaining.protein:.0f}g more)")
    if remaining.calories > 500:
        priorities.append(f"CALORIES ({remaining.calories:.0f} kcal remaining)")
    if remaining.fat < 15:
        priorities.append("LOW FAT (fat budget almost used)")
    if remaining.carbs < 20:
        priorities.append("LOW CARB (carb budget almost used)")
    
    if not priorities:
        priorities.append("BALANCED meal to finish the day")
    
    prompt = f"""Suggest {limit} food options for someone in the Netherlands.

REMAINING MACROS:
- Calories: {remaining.calories:.0f} kcal
- Protein: {remaining.protein:.0f}g
- Fat: {remaining.fat:.0f}g  
- Carbs: {remaining.carbs:.0f}g

PRIORITY: {', '.join(priorities)}

ALREADY SUGGESTED (avoid these): {', '.join(already_suggested) if already_suggested else 'None'}

Give practical suggestions available in Dutch supermarkets (Albert Heijn, Jumbo) or easy to make at home.
Include specific products when relevant (e.g. "Almhof kwark", "AH kipfilet").

JSON array only:
[
  {{
    "name": "Food name",
    "portion": "amount with unit",
    "calories": number,
    "protein": number,
    "fat": number,
    "carbs": number,
    "reason": "why this fits the needs",
    "where_to_get": "supermarket/restaurant/homemade"
  }}
]"""

    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": "You are a Dutch nutritionist. Give practical, accurate suggestions with realistic macro values. Focus on common Dutch supermarket products."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        content = response.choices[0].message.content.strip()
        content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.DOTALL)
        data = json.loads(content)
        
        suggestions = []
        for item in data[:limit]:
            suggestions.append(AISuggestion(
                name=item.get("name", "Unknown"),
                portion=item.get("portion", "1 serving"),
                calories=float(item.get("calories", 0)),
                protein=float(item.get("protein", 0)),
                fat=float(item.get("fat", 0)),
                carbs=float(item.get("carbs", 0)),
                reason=item.get("reason", ""),
                where_to_get=item.get("where_to_get", "supermarket")
            ))
        
        return suggestions
        
    except Exception as e:
        print(f"AI suggestion error: {e}")
        return []


def format_ai_suggestions_message(ai_suggestions: List[AISuggestion]) -> str:
    """Format AI suggestions as a Telegram message."""
    
    if not ai_suggestions:
        return ""
    
    msg = "\n🤖 *AI Suggestions*\n"
    msg += "_Additional ideas based on your macros:_\n\n"
    
    for i, s in enumerate(ai_suggestions, 1):
        # Emoji for where to get
        where_emoji = {
            "supermarket": "🛒",
            "restaurant": "🍽️",
            "homemade": "👨‍🍳"
        }.get(s.where_to_get, "🛒")
        
        msg += f"*{i}. {s.name}* {where_emoji}\n"
        msg += f"   📏 {s.portion} → {s.calories:.0f} kcal, {s.protein:.0f}g P\n"
        msg += f"   _{s.reason}_\n\n"
    
    return msg


def get_combined_suggestions(remaining: RemainingMacros, 
                             db_limit: int = 3, 
                             ai_limit: int = 5) -> tuple:
    """
    Get both database and AI suggestions.
    
    Returns:
        Tuple of (db_suggestions, ai_suggestions)
    """
    # First get database suggestions
    db_suggestions = get_suggestions(remaining, limit=db_limit)
    
    # Then get AI suggestions (avoiding duplicates)
    ai_suggestions = get_ai_suggestions(remaining, db_suggestions, limit=ai_limit)
    
    return db_suggestions, ai_suggestions


def format_combined_suggestions(remaining: RemainingMacros,
                                db_suggestions: List[FoodSuggestion],
                                ai_suggestions: List[AISuggestion]) -> str:
    """Format both database and AI suggestions together."""
    
    msg = ""
    
    # Database suggestions first
    if db_suggestions:
        msg += "💡 *Your Foods*\n"
        msg += f"_Based on: {remaining.protein:.0f}g protein, {remaining.calories:.0f} kcal remaining_\n\n"
        
        for i, s in enumerate(db_suggestions, 1):
            verified = "✓" if s.food.verified else ""
            msg += f"*{i}. {s.food.display_name}* {verified}\n"
            msg += f"   📏 {s.portion} → {s.would_add['calories']:.0f} kcal, {s.would_add['protein']:.0f}g P\n"
            msg += f"   _{s.reason}_\n\n"
    else:
        msg += "📦 _No foods in your database yet_\n\n"
    
    # AI suggestions
    if ai_suggestions:
        msg += format_ai_suggestions_message(ai_suggestions)
    
    return msg
