# food_service.py
"""
Simple food lookup service with text-based matching.
No embeddings - just PostgreSQL ILIKE search.
"""
import os
import json
import re
from typing import Optional, List
from dataclasses import dataclass

from openai import OpenAI
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


def get_openai_client() -> OpenAI:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY_HW is not set")
    return OpenAI(api_key=OPENAI_API_KEY)


def parse_food_input(user_input: str) -> ParsedInput:
    """
    Parse input like "200g magere kwark AH" into structured data.
    """
    client = get_openai_client()
    
    prompt = f"""Parse this food input. Extract:
- quantity (number, default 1)
- unit (g, ml, piece, serving)
- food_name (just the food, no brand)
- brand (store/brand if mentioned, else null)

Dutch brand shortcuts: AH = Albert Heijn

JSON only:
{{"quantity": number, "unit": string, "food_name": string, "brand": string|null}}

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
    
    return ParsedInput(
        quantity=float(data.get("quantity", 1)),
        unit=data.get("unit", "g"),
        food_name=data.get("food_name", user_input).lower().strip(),
        brand=brand
    )


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
            scaled = scale_nutrition(food, parsed.quantity, parsed.unit)
            return FoodMatch(food_item=food, scaled_nutrition=scaled)
        
        return None
    finally:
        session.close()


def scale_nutrition(food: FoodItem, quantity: float, unit: str) -> dict:
    """Scale nutrition from per-100 values to requested quantity."""
    if unit in ["piece", "serving", "stuk", "stuks"]:
        # Use default serving size
        factor = (food.default_serving / 100.0) * quantity
    else:
        # Assume grams/ml
        factor = quantity / 100.0
    
    return {
        "calories": round(food.calories_per_100 * factor, 1),
        "protein": round(food.protein_per_100 * factor, 1),
        "fat": round(food.fat_per_100 * factor, 1),
        "carbs": round(food.carbs_per_100 * factor, 1)
    }


def ai_estimate_nutrition(user_input: str, parsed: ParsedInput) -> dict:
    """Use AI to estimate nutrition for unknown food."""
    client = get_openai_client()
    
    prompt = f"""Estimate nutrition for this Dutch food item.
Give values per 100g (or per 100ml for liquids, or per piece for countable items).

IMPORTANT: If there is no brand, use null (not the string "null").

JSON only:
{{
    "name": "food name",
    "brand": null,
    "calories_per_100": number,
    "protein_per_100": number,
    "fat_per_100": number,
    "carbs_per_100": number,
    "default_serving": number,
    "serving_unit": "g/ml/piece"
}}

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
    return json.loads(content)


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
            default_serving=estimation.get("default_serving", 100),
            serving_unit=estimation.get("serving_unit", "g"),
            verified=verified
        )
        session.add(food)
        session.commit()
        session.refresh(food)
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
