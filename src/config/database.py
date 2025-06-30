from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config.settings import settings

# Use centralized settings for database configuration
DATABASE_URL = settings.database_url

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    echo=settings.database_echo_enabled,  # Enable SQL logging in development only
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300  # Recycle connections every 5 minutes
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

def get_db():
    """
    Dependency function to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()