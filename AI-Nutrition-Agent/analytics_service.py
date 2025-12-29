# analytics_service.py
"""
Analytics and suggestion engine for NutritionBot.
Provides insights on remaining macros and food suggestions.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from db_models import get_session, FoodItem


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
