# db_models.py
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://nutrition:nutrition@localhost:5433/nutrition"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class FoodItem(Base):
    """
    Cached food database with verified nutritional values.
    Simple text matching - no embeddings needed.
    """
    __tablename__ = "food_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Food identification
    name = Column(String, nullable=False)  # "Magere kwark"
    brand = Column(String, nullable=True)  # "Albert Heijn"
    display_name = Column(String, nullable=False)  # "Magere kwark (Albert Heijn)"
    
    # Search keys (lowercase, for matching)
    search_name = Column(String, nullable=False, index=True)  # "magere kwark"
    search_brand = Column(String, nullable=True, index=True)  # "albert heijn"
    
    # Nutrition per 100g/100ml (for scaling)
    calories_per_100 = Column(Float, default=0)
    protein_per_100 = Column(Float, default=0)
    fat_per_100 = Column(Float, default=0)
    carbs_per_100 = Column(Float, default=0)
    
    # Default serving info
    default_serving = Column(Float, default=100)
    serving_unit = Column(String, default="g")
    grams_per_serving = Column(Float, nullable=True)
    
    # Metadata
    verified = Column(Boolean, default=False)
    times_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def init_db():
    Base.metadata.create_all(engine)


def get_session():
    return SessionLocal()