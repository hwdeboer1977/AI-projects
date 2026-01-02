# food_service.py
"""
Simple food lookup service with text-based matching.
No embeddings - just PostgreSQL ILIKE search.
"""
import os
import json
import re
import logging
from typing import Optional, List
from dataclasses import dataclass

from openai import OpenAI

# Setup logging
logger = logging.getLogger("food-service")
logger.setLevel(logging.DEBUG)
from sqlalchemy import func
from db_models import get_session, FoodItem
from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY_HW")
CHAT_MODEL = "gpt-4o-mini"

# Brand aliases (Dutch shortcuts)
BRAND_ALIASES = {
    "ah": "albert heijn",
    "a.h.": "albert heijn",
    "albert heijn": "albert heijn",
    "jumbo": "jumbo",
    "lidl": "lidl",
    "aldi": "aldi",
    "plus": "plus",
    "dirk": "dirk",
}


@dataclass
class ParsedInput:
    quantity: float
    unit: str
    food_name: str
    brand: Optional[str]


@dataclass
class FoodMatch:
    food_item: FoodItem
    scaled_nutrition: dict
    needs_serving_size: bool = False
    serving_unit_requested: str = None


def get_openai_client() -> OpenAI:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY_HW is not set")
    return OpenAI(api_key=OPENAI_API_KEY)


def parse_food_input(user_input: str) -> ParsedInput:
    """
    Parse input like "200g magere kwark AH" into structured data.
    """
    client = get_openai_client()
    
    prompt = f"""Parse this food input into structured data.

RULES:
1. quantity: the number (default 1)
2. unit: MUST be one of: "g", "ml", "piece", "serving"
   - "portie", "serving", "portion" → "serving"
   - "stuk", "stuks", "piece", "pieces" → "piece"
   - grams, "g" → "g"
   - ml, milliliters → "ml"
   - no unit mentioned → "g"
3. food_name: ONLY the food itself
   - REMOVE quantity words (1, 2, 100g, etc.)
   - REMOVE unit words (portie, serving, stuk, piece, gram, g, ml)
   - REMOVE brand names
   - Keep ONLY the actual food name
4. brand: store/brand if mentioned, else null
   - Dutch shortcuts: AH = Albert Heijn

JSON only:
{{"quantity": number, "unit": string, "food_name": string, "brand": string|null}}

Examples:
- "1 portie babi pangang met bami" → {{"quantity": 1, "unit": "serving", "food_name": "babi pangang met bami", "brand": null}}
- "1 serving babi pangang" → {{"quantity": 1, "unit": "serving", "food_name": "babi pangang", "brand": null}}
- "2 stuks banaan" → {{"quantity": 2, "unit": "piece", "food_name": "banaan", "brand": null}}
- "200g kipfilet AH" → {{"quantity": 200, "unit": "g", "food_name": "kipfilet", "brand": "albert heijn"}}
- "magere kwark" → {{"quantity": 1, "unit": "g", "food_name": "magere kwark", "brand": null}}

Input: {user_input}"""

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    
    content = response.choices[0].message.content.strip()
    content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.DOTALL)
    data = json.loads(content)
    
    # Normalize brand
    brand = data.get("brand")
    if brand:
        brand = BRAND_ALIASES.get(brand.lower(), brand.lower())
    
    # Clean up food_name - remove any unit words that slipped through
    food_name = data.get("food_name", user_input).lower().strip()
    unit_words = ["portie", "porties", "serving", "servings", "stuk", "stuks", "piece", "pieces", "gram", "g", "ml"]
    for word in unit_words:
        food_name = re.sub(rf"^\s*{word}\s+", "", food_name)  # Remove from start
        food_name = re.sub(rf"\s+{word}\s*$", "", food_name)  # Remove from end
    food_name = food_name.strip()
    
    result = ParsedInput(
        quantity=float(data.get("quantity", 1)),
        unit=data.get("unit", "g"),
        food_name=food_name,
        brand=brand
    )
    
    logger.info(f"=== parse_food_input ===")
    logger.info(f"Input: '{user_input}'")
    logger.info(f"AI returned: {data}")
    logger.info(f"Final parsed: quantity={result.quantity}, unit='{result.unit}', food_name='{result.food_name}', brand={result.brand}")
    
    return result


def search_food_database(parsed: ParsedInput) -> Optional[FoodMatch]:
    """
    Search for matching food in database using ILIKE.
    Returns best match or None.
    """
    session = get_session()
    try:
        query = session.query(FoodItem)
        
        # Search by name (fuzzy with ILIKE)
        search_pattern = f"%{parsed.food_name}%"
        query = query.filter(FoodItem.search_name.ilike(search_pattern))
        
        # If brand specified, filter by brand
        if parsed.brand:
            query = query.filter(FoodItem.search_brand.ilike(f"%{parsed.brand}%"))
        
        # Order by most used first
        query = query.order_by(FoodItem.times_used.desc())
        
        food = query.first()
        
        if food:
            logger.info(f"=== search_food_database MATCH ===")
            logger.info(f"Search: '{parsed.food_name}' (brand: {parsed.brand})")
            logger.info(f"Found: {food.display_name} (ID: {food.id})")
            logger.info(f"DB values: cal_per_100={food.calories_per_100}, prot_per_100={food.protein_per_100}")
            logger.info(f"DB serving: unit={food.serving_unit}, default={food.default_serving}, grams_per_serving={getattr(food, 'grams_per_serving', None)}")
            
            scale_result = scale_nutrition(food, parsed.quantity, parsed.unit)
            return FoodMatch(
                food_item=food, 
                scaled_nutrition=scale_result.nutrition,
                needs_serving_size=scale_result.needs_serving_size,
                serving_unit_requested=scale_result.serving_unit_requested
            )
        
        logger.info(f"=== search_food_database NO MATCH ===")
        logger.info(f"Search: '{parsed.food_name}' (brand: {parsed.brand})")
        return None
    finally:
        session.close()


@dataclass
class ScaleResult:
    """Result of scaling nutrition - may need user input for serving size."""
    nutrition: dict
    needs_serving_size: bool = False
    serving_unit_requested: str = None


def scale_nutrition(food: FoodItem, quantity: float, unit: str) -> ScaleResult:
    """
    Scale nutrition from per-100g values to requested quantity.
    
    Logic:
    - If unit is g/ml: simple factor = quantity / 100
    - If unit is piece/serving: need grams_per_serving to convert
      → If grams_per_serving is NULL, return needs_serving_size=True
    
    Returns ScaleResult with nutrition dict and flag if serving size needed.
    """
    unit_lower = unit.lower()
    
    # Use INFO level so it actually shows in logs
    logger.info(f"=== scale_nutrition ===")
    logger.info(f"Food: {food.display_name} (ID: {food.id})")
    logger.info(f"Requested: {quantity} {unit} (unit_lower: '{unit_lower}')")
    logger.info(f"DB values: cal={food.calories_per_100}, prot={food.protein_per_100}")
    
    grams_per_serving = getattr(food, 'grams_per_serving', None)
    logger.info(f"DB grams_per_serving: {grams_per_serving}")
    
    is_serving_request = unit_lower in ["piece", "pieces", "serving", "servings", "stuk", "stuks", "portie", "porties"]
    logger.info(f"is_serving_request: {is_serving_request}")
    
    if is_serving_request:
        # Need to know how many grams per serving
        grams_per_serving = getattr(food, 'grams_per_serving', None)
        
        if grams_per_serving is None or grams_per_serving <= 0:
            # We don't know the serving size - ask user
            logger.info(f"Missing grams_per_serving for {food.display_name} - need user input")
            return ScaleResult(
                nutrition={"calories": 0, "protein": 0, "fat": 0, "carbs": 0},
                needs_serving_size=True,
                serving_unit_requested=unit_lower
            )
        
        # Calculate: 1 serving = X grams → factor = (X / 100) * quantity
        factor = (grams_per_serving / 100.0) * quantity
        logger.debug(f"Serving request: {quantity} x {grams_per_serving}g per serving → factor = {factor}")
    else:
        # User specified grams/ml directly
        factor = quantity / 100.0
        logger.debug(f"Gram/ml request: {quantity} / 100 = {factor}")
    
    result = {
        "calories": round(food.calories_per_100 * factor, 1),
        "protein": round(food.protein_per_100 * factor, 1),
        "fat": round(food.fat_per_100 * factor, 1),
        "carbs": round(food.carbs_per_100 * factor, 1)
    }
    
    logger.debug(f"Scaled result: {result}")
    logger.debug(f"=== END scale_nutrition ===")
    
    return ScaleResult(nutrition=result, needs_serving_size=False)


def ai_estimate_nutrition(user_input: str, parsed: ParsedInput) -> dict:
    """Use AI to estimate nutrition for unknown food."""
    client = get_openai_client()
    
    prompt = f"""Estimate nutrition for this Dutch food item.

CRITICAL: Determine if this is a COUNTABLE item (eggs, bananas, cookies) or a BULK item (rice, meat, yogurt):
- For COUNTABLE items: Give values PER PIECE and set serving_unit to "piece"
- For BULK items: Give values PER 100g/100ml and set serving_unit to "g" or "ml"

If there is no brand, use null (not the string "null").

JSON only:
{{
    "name": "food name",
    "brand": null,
    "calories_per_100": number,
    "protein_per_100": number,
    "fat_per_100": number,
    "carbs_per_100": number,
    "default_serving": number,
    "serving_unit": "g/ml/piece",
    "is_countable": true/false
}}

Examples:
- "2 eggs" → values per 1 egg, serving_unit="piece", is_countable=true
- "1 banana" → values per 1 banana, serving_unit="piece", is_countable=true
- "200g chicken" → values per 100g, serving_unit="g", is_countable=false
- "magere kwark" → values per 100g, serving_unit="g", is_countable=false

Input: {user_input}"""

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": "You are a nutritionist. Be accurate for Dutch supermarket products."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    
    content = response.choices[0].message.content.strip()
    content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.DOTALL)
    result = json.loads(content)
    
    logger.info(f"=== ai_estimate_nutrition ===")
    logger.info(f"Input: '{user_input}'")
    logger.info(f"AI result: {json.dumps(result, indent=2)}")
    
    return result


def save_food_to_database(estimation: dict, parsed: ParsedInput, verified: bool = False) -> FoodItem:
    """Save a new food item to the database."""
    name = estimation.get("name", parsed.food_name)
    brand = estimation.get("brand") or parsed.brand
    
    # Handle "null" string as None
    if brand and brand.lower() in ["null", "none", ""]:
        brand = None
    
    display_name = name.title()
    if brand:
        display_name += f" ({brand.title()})"
    
    serving_unit = estimation.get("serving_unit", "g")
    default_serving = estimation.get("default_serving", 100)
    grams_per_serving = estimation.get("grams_per_serving")  # May be None
    
    logger.info(f"=== save_food_to_database ===")
    logger.info(f"Name: {name}, Brand: {brand}")
    logger.info(f"Values per 100g:")
    logger.info(f"  cal={estimation.get('calories_per_100', 0)}, prot={estimation.get('protein_per_100', 0)}")
    logger.info(f"  serving_unit={serving_unit}, default_serving={default_serving}, grams_per_serving={grams_per_serving}")
    
    session = get_session()
    try:
        food = FoodItem(
            name=name.title(),
            brand=brand.title() if brand else None,
            display_name=display_name,
            search_name=name.lower(),
            search_brand=brand.lower() if brand else None,
            calories_per_100=estimation.get("calories_per_100", 0),
            protein_per_100=estimation.get("protein_per_100", 0),
            fat_per_100=estimation.get("fat_per_100", 0),
            carbs_per_100=estimation.get("carbs_per_100", 0),
            default_serving=default_serving,
            serving_unit=serving_unit,
            grams_per_serving=grams_per_serving,
            verified=verified
        )
        session.add(food)
        session.commit()
        session.refresh(food)
        
        logger.info(f"Saved with ID: {food.id}")
        return food
    finally:
        session.close()


def increment_usage(food_id: int):
    """Increment times_used counter."""
    session = get_session()
    try:
        food = session.query(FoodItem).filter(FoodItem.id == food_id).first()
        if food:
            food.times_used += 1
            session.commit()
    finally:
        session.close()


def update_food_in_database(food_id: int, cal: float, prot: float, fat: float, carbs: float, verified: bool = True) -> Optional[FoodItem]:
    """Update existing food item with new nutrition values."""
    session = get_session()
    try:
        food = session.query(FoodItem).filter(FoodItem.id == food_id).first()
        if food:
            food.calories_per_100 = cal
            food.protein_per_100 = prot
            food.fat_per_100 = fat
            food.carbs_per_100 = carbs
            food.verified = verified
            session.commit()
            session.refresh(food)
            return food
        return None
    finally:
        session.close()


def update_grams_per_serving(food_id: int, grams: float) -> Optional[FoodItem]:
    """Update the grams_per_serving for a food item."""
    session = get_session()
    try:
        food = session.query(FoodItem).filter(FoodItem.id == food_id).first()
        if food:
            food.grams_per_serving = grams
            session.commit()
            session.refresh(food)
            logger.info(f"Updated grams_per_serving for {food.display_name} (ID: {food_id}) to {grams}g")
            return food
        return None
    finally:
        session.close()


def get_food_by_id(food_id: int) -> Optional[FoodItem]:
    """Get food item by ID."""
    session = get_session()
    try:
        return session.query(FoodItem).filter(FoodItem.id == food_id).first()
    finally:
        session.close()


def save_food_with_name(new_name: str, calories_per_100: float, protein_per_100: float, 
                        fat_per_100: float, carbs_per_100: float, brand: Optional[str] = None,
                        verified: bool = False) -> FoodItem:
    """Save a new food item with a specific name."""
    # Handle "null" string as None
    if brand and brand.lower() in ["null", "none", ""]:
        brand = None
    
    display_name = new_name.title()
    if brand:
        display_name += f" ({brand.title()})"
    
    session = get_session()
    try:
        food = FoodItem(
            name=new_name.title(),
            brand=brand.title() if brand else None,
            display_name=display_name,
            search_name=new_name.lower(),
            search_brand=brand.lower() if brand else None,
            calories_per_100=calories_per_100,
            protein_per_100=protein_per_100,
            fat_per_100=fat_per_100,
            carbs_per_100=carbs_per_100,
            verified=verified
        )
        session.add(food)
        session.commit()
        session.refresh(food)
        return food
    finally:
        session.close()