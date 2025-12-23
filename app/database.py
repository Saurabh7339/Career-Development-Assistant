"""
Database setup and models for SQLite
"""
from sqlalchemy import create_engine, Column, String, Float, Text, Integer, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
import os

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./skill_gap.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class UserProfileDB(Base):
    """SQLAlchemy model for user profiles"""
    __tablename__ = "user_profiles"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    current_role = Column(String, nullable=False)
    experience_years = Column(Float, nullable=True)
    bio = Column(Text, nullable=True)
    raw_text = Column(Text, nullable=True)
    certifications = Column(JSON, nullable=True)  # Store as JSON array
    created_at = Column(String, nullable=True)
    updated_at = Column(String, nullable=True)
    
    # Relationship to skills
    skills = relationship("SkillDB", back_populates="profile", cascade="all, delete-orphan")


class SkillDB(Base):
    """SQLAlchemy model for skills"""
    __tablename__ = "skills"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    profile_id = Column(String, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False, index=True)
    proficiency = Column(String, nullable=True)  # beginner, intermediate, advanced, expert
    years_experience = Column(Float, nullable=True)
    certification = Column(String, nullable=True)
    
    # Relationship back to profile
    profile = relationship("UserProfileDB", back_populates="skills")


class TargetRoleDB(Base):
    """SQLAlchemy model for target roles"""
    __tablename__ = "target_roles"
    
    id = Column(String, primary_key=True, index=True)
    role_name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    skill_framework = Column(String, nullable=True)
    created_at = Column(String, nullable=True)
    
    # Relationship to required skills
    required_skills = relationship("RequiredSkillDB", back_populates="target_role", cascade="all, delete-orphan")


class RequiredSkillDB(Base):
    """SQLAlchemy model for required skills in target roles"""
    __tablename__ = "required_skills"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    target_role_id = Column(String, ForeignKey("target_roles.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False, index=True)
    proficiency = Column(String, nullable=True)
    years_experience = Column(Float, nullable=True)
    certification = Column(String, nullable=True)
    
    # Relationship back to target role
    target_role = relationship("TargetRoleDB", back_populates="required_skills")


class SkillGapReportDB(Base):
    """SQLAlchemy model for storing skill gap reports"""
    __tablename__ = "skill_gap_reports"
    
    id = Column(String, primary_key=True, index=True)
    user_profile_id = Column(String, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    target_role_id = Column(String, ForeignKey("target_roles.id", ondelete="SET NULL"), nullable=True)
    user_name = Column(String, nullable=False)
    current_role = Column(String, nullable=False)
    target_role = Column(String, nullable=False)
    overall_gap_score = Column(Float, nullable=False)
    upskilling_path = Column(JSON, nullable=True)  # Store as JSON array
    analysis_summary = Column(Text, nullable=True)
    created_at = Column(String, nullable=True)
    
    # Store gap items as JSON
    skills_met = Column(JSON, nullable=True)
    skills_missing = Column(JSON, nullable=True)
    skills_weak = Column(JSON, nullable=True)


def init_db():
    """Initialize database - create all tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

