# Placeholder for database models using SQLAlchemy

import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.sql import func # For default timestamps
from dotenv import load_dotenv
import logging
from sqlalchemy.dialects.postgresql import JSONB # Import JSONB for PostgreSQL
from sqlalchemy import TypeDecorator # Needed for JSON compatibility
import json

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get DB URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    logger.error("DATABASE_URL not found in environment variables. Database connection cannot be established.")
    # Depending on requirements, you might want to exit or raise an error
    engine = None
    SessionLocal = None
else:
    logger.info("DATABASE_URL found, configuring SQLAlchemy engine.")
    try:
        # connect_args only needed for SQLite, remove if using PostgreSQL
        # For PostgreSQL, ensure DATABASE_URL is like: "postgresql://user:password@host:port/database"
        connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
        engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False) # Set echo=True for SQL logging
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    except Exception as e:
        logger.error(f"Failed to create SQLAlchemy engine or session: {e}")
        engine = None
        SessionLocal = None

# --- JSON Handling for SQLAlchemy ---
# Define a type to handle JSON storage compatibly across DBs if needed,
# but prefer native JSONB for PostgreSQL.
class JSONEncodedDict(TypeDecorator):
    """Represents an immutable structure as a json-encoded string.
    Usage: JSONEncodedDict(255)
    """
    impl = Text
    cache_ok = True # Indicate that the type is cacheable

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value

# Base class for declarative models
Base = declarative_base()

# --- Database Models ---

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    google_id = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String)
    picture_url = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to tokens (one-to-one or one-to-many if storing multiple token types)
    oauth_token = relationship("OAuthToken", back_populates="user", uselist=False, cascade="all, delete-orphan")

    # Add relationship to DailyPlan (one-to-many)
    daily_plans = relationship("DailyPlan", back_populates="user", cascade="all, delete-orphan")

class OAuthToken(Base):
    __tablename__ = "oauth_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    token_type = Column(String, default="Bearer")
    # Store tokens as Text; consider encryption in production!
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True) # Google provides refresh token only on first auth
    expires_at = Column(DateTime(timezone=True), nullable=True)
    scope = Column(Text)
    # Timestamps for tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship back to user
    user = relationship("User", back_populates="oauth_token")

# New Model for Daily Plans
class DailyPlan(Base):
    __tablename__ = "daily_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    plan_date = Column(DateTime(timezone=True), nullable=False, index=True) # Use DateTime to store the date the plan is *for*
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    # Use native JSONB for PostgreSQL for better performance and querying
    plan_data = Column(JSONB, nullable=False) 
    # If not using PostgreSQL, use the custom type:
    # plan_data = Column(JSONEncodedDict, nullable=False)

    # Relationship back to user
    user = relationship("User", back_populates="daily_plans")

# Add more models as needed (e.g., SavedPlan, UserSettings)

# --- Database Initialization ---

def create_db_tables():
    """Creates database tables based on the defined models."""
    if not engine:
        logger.error("Database engine not initialized. Cannot create tables.")
        return
    try:
        logger.info("Attempting to create database tables if they don't exist...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables checked/created.")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}", exc_info=True)

# --- Dependency for FastAPI ---

def get_db():
    """FastAPI dependency that provides a database session."""
    if not SessionLocal:
        logger.error("Database SessionLocal not initialized.")
        raise RuntimeError("Database not configured.") # Or handle appropriately
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Note: create_db_tables() should be called once during application startup.

print("Database models placeholder loaded. Uncomment and configure.") 