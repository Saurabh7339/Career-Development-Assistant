"""
Data models for Skill Gap Identification System
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ProficiencyLevel(str, Enum):
    """Skill proficiency levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class Skill(BaseModel):
    """Individual skill representation"""
    name: str = Field(..., description="Name of the skill")
    proficiency: Optional[ProficiencyLevel] = Field(None, description="Proficiency level")
    years_experience: Optional[float] = Field(None, description="Years of experience")
    certification: Optional[str] = Field(None, description="Related certification if any")


class UserProfile(BaseModel):
    """User profile with current skills and experience"""
    name: str = Field(..., description="User's name")
    current_role: str = Field(..., description="Current job role")
    skills: List[Skill] = Field(default_factory=list, description="List of current skills")
    certifications: List[str] = Field(default_factory=list, description="List of certifications")
    experience_years: Optional[float] = Field(None, description="Total years of experience")
    bio: Optional[str] = Field(None, description="Additional bio or description")
    raw_text: Optional[str] = Field(None, description="Raw text description for RAG processing")


class TargetRole(BaseModel):
    """Target role or skill framework"""
    role_name: str = Field(..., description="Name of the target role")
    description: Optional[str] = Field(None, description="Role description")
    skill_framework: Optional[str] = Field(None, description="Skill framework name (e.g., SFIA, NIST)")
    required_skills: List[Skill] = Field(default_factory=list, description="Required skills (populated by LLM analysis)")


class SkillGapItem(BaseModel):
    """Individual skill gap item"""
    skill_name: str
    status: str  # "met", "missing", "weak"
    current_proficiency: Optional[ProficiencyLevel] = None
    required_proficiency: Optional[ProficiencyLevel] = None
    gap_severity: str  # "low", "medium", "high"
    recommendation: Optional[str] = None


class SkillGapReport(BaseModel):
    """Complete skill gap analysis report"""
    user_name: str
    current_role: str
    target_role: str
    skills_met: List[SkillGapItem] = Field(default_factory=list)
    skills_missing: List[SkillGapItem] = Field(default_factory=list)
    skills_weak: List[SkillGapItem] = Field(default_factory=list)
    overall_gap_score: float = Field(..., ge=0, le=100, description="Overall gap score (0-100)")
    upskilling_path: Optional[List[str]] = Field(None, description="Suggested upskilling path")
    analysis_summary: Optional[str] = Field(None, description="AI-generated analysis summary")


class ProfileUploadRequest(BaseModel):
    """Request model for uploading user profile"""
    profile_text: str = Field(..., description="Text description of user profile")
    name: Optional[str] = Field(None, description="User name (optional)")
    current_role: Optional[str] = Field(None, description="Current role (optional)")


class GapAnalysisRequest(BaseModel):
    """Request model for skill gap analysis"""
    user_profile_id: str = Field(..., description="ID of user profile in database")
    user_query: str = Field(..., description="User's question/goal and any additional context (e.g., 'I want to become a Senior Data Engineer. I have 3 years experience as a Data Analyst.')")
    target_role: TargetRole = Field(..., description="Target role (system will determine required skills)")
    use_rag: bool = Field(True, description="Whether to use RAG for enhanced analysis")

