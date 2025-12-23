"""
CRUD operations for database
"""
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import uuid
from app.database import (
    UserProfileDB, SkillDB, TargetRoleDB, 
    RequiredSkillDB, SkillGapReportDB
)
from app.models import UserProfile, Skill, TargetRole, SkillGapReport, SkillGapItem


def create_user_profile(db: Session, profile: UserProfile, profile_id: Optional[str] = None) -> str:
    """Create a new user profile in database"""
    if not profile_id:
        profile_id = str(uuid.uuid4())
    
    # Create profile record
    db_profile = UserProfileDB(
        id=profile_id,
        name=profile.name,
        current_role=profile.current_role,
        experience_years=profile.experience_years,
        bio=profile.bio,
        raw_text=profile.raw_text,
        certifications=profile.certifications if profile.certifications else [],
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat()
    )
    
    # Add skills
    for skill in profile.skills:
        db_skill = SkillDB(
            profile_id=profile_id,
            name=skill.name,
            proficiency=skill.proficiency.value if skill.proficiency else None,
            years_experience=skill.years_experience,
            certification=skill.certification
        )
        db_profile.skills.append(db_skill)
    
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    
    return profile_id


def get_user_profile(db: Session, profile_id: str) -> Optional[UserProfile]:
    """Get a user profile by ID"""
    db_profile = db.query(UserProfileDB).filter(UserProfileDB.id == profile_id).first()
    
    if not db_profile:
        return None
    
    # Convert to Pydantic model
    from app.models import ProficiencyLevel
    skills = [
        Skill(
            name=skill.name,
            proficiency=ProficiencyLevel(skill.proficiency) if skill.proficiency else None,
            years_experience=skill.years_experience,
            certification=skill.certification
        )
        for skill in db_profile.skills
    ]
    
    profile = UserProfile(
        name=db_profile.name,
        current_role=db_profile.current_role,
        skills=skills,
        certifications=db_profile.certifications or [],
        experience_years=db_profile.experience_years,
        bio=db_profile.bio,
        raw_text=db_profile.raw_text
    )
    # Add ID to the profile dict for API response
    profile_dict = profile.model_dump()
    profile_dict['id'] = db_profile.id
    return profile_dict


def get_all_profiles(db: Session, skip: int = 0, limit: int = 100) -> List[UserProfile]:
    """Get all user profiles"""
    db_profiles = db.query(UserProfileDB).offset(skip).limit(limit).all()
    
    from app.models import ProficiencyLevel
    profiles = []
    for db_profile in db_profiles:
        skills = [
            Skill(
                name=skill.name,
                proficiency=ProficiencyLevel(skill.proficiency) if skill.proficiency else None,
                years_experience=skill.years_experience,
                certification=skill.certification
            )
            for skill in db_profile.skills
        ]
        
        profile = UserProfile(
            name=db_profile.name,
            current_role=db_profile.current_role,
            skills=skills,
            certifications=db_profile.certifications or [],
            experience_years=db_profile.experience_years,
            bio=db_profile.bio,
            raw_text=db_profile.raw_text
        )
        # Add ID to the profile dict for API response
        profile_dict = profile.model_dump()
        profile_dict['id'] = db_profile.id
        profiles.append(profile_dict)
    
    return profiles


def update_user_profile(db: Session, profile_id: str, profile: UserProfile) -> bool:
    """Update a user profile"""
    db_profile = db.query(UserProfileDB).filter(UserProfileDB.id == profile_id).first()
    
    if not db_profile:
        return False
    
    # Update fields
    db_profile.name = profile.name
    db_profile.current_role = profile.current_role
    db_profile.experience_years = profile.experience_years
    db_profile.bio = profile.bio
    db_profile.raw_text = profile.raw_text
    db_profile.certifications = profile.certifications or []
    db_profile.updated_at = datetime.utcnow().isoformat()
    
    # Delete old skills and add new ones
    db.query(SkillDB).filter(SkillDB.profile_id == profile_id).delete()
    
    for skill in profile.skills:
        db_skill = SkillDB(
            profile_id=profile_id,
            name=skill.name,
            proficiency=skill.proficiency.value if skill.proficiency else None,
            years_experience=skill.years_experience,
            certification=skill.certification
        )
        db_profile.skills.append(db_skill)
    
    db.commit()
    return True


def delete_user_profile(db: Session, profile_id: str) -> bool:
    """Delete a user profile"""
    db_profile = db.query(UserProfileDB).filter(UserProfileDB.id == profile_id).first()
    
    if not db_profile:
        return False
    
    db.delete(db_profile)
    db.commit()
    return True


def create_target_role(db: Session, target_role: TargetRole, role_id: Optional[str] = None) -> str:
    """Create a new target role in database"""
    if not role_id:
        role_id = str(uuid.uuid4())
    
    db_role = TargetRoleDB(
        id=role_id,
        role_name=target_role.role_name,
        description=target_role.description,
        skill_framework=target_role.skill_framework,
        created_at=datetime.utcnow().isoformat()
    )
    
    # Add required skills
    for skill in target_role.required_skills:
        db_skill = RequiredSkillDB(
            target_role_id=role_id,
            name=skill.name,
            proficiency=skill.proficiency.value if skill.proficiency else None,
            years_experience=skill.years_experience,
            certification=skill.certification
        )
        db_role.required_skills.append(db_skill)
    
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    
    return role_id


def get_target_role(db: Session, role_id: str) -> Optional[TargetRole]:
    """Get a target role by ID"""
    db_role = db.query(TargetRoleDB).filter(TargetRoleDB.id == role_id).first()
    
    if not db_role:
        return None
    
    from app.models import ProficiencyLevel
    skills = [
        Skill(
            name=skill.name,
            proficiency=ProficiencyLevel(skill.proficiency) if skill.proficiency else None,
            years_experience=skill.years_experience,
            certification=skill.certification
        )
        for skill in db_role.required_skills
    ]
    
    return TargetRole(
        role_name=db_role.role_name,
        required_skills=skills,
        description=db_role.description,
        skill_framework=db_role.skill_framework
    )


def save_skill_gap_report(
    db: Session,
    report: SkillGapReport,
    profile_id: str,
    target_role_id: Optional[str] = None
) -> str:
    """Save a skill gap report to database"""
    report_id = str(uuid.uuid4())
    
    # Convert SkillGapItem lists to dicts for JSON storage
    def item_to_dict(item: SkillGapItem) -> dict:
        return {
            "skill_name": item.skill_name,
            "status": item.status,
            "current_proficiency": item.current_proficiency.value if item.current_proficiency else None,
            "required_proficiency": item.required_proficiency.value if item.required_proficiency else None,
            "gap_severity": item.gap_severity,
            "recommendation": item.recommendation
        }
    
    db_report = SkillGapReportDB(
        id=report_id,
        user_profile_id=profile_id,
        target_role_id=target_role_id,
        user_name=report.user_name,
        current_role=report.current_role,
        target_role=report.target_role,
        overall_gap_score=report.overall_gap_score,
        upskilling_path=report.upskilling_path,
        analysis_summary=report.analysis_summary,
        skills_met=[item_to_dict(item) for item in report.skills_met],
        skills_missing=[item_to_dict(item) for item in report.skills_missing],
        skills_weak=[item_to_dict(item) for item in report.skills_weak],
        created_at=datetime.utcnow().isoformat()
    )
    
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    
    return report_id


def get_skill_gap_report(db: Session, report_id: str) -> Optional[SkillGapReport]:
    """Get a skill gap report by ID"""
    db_report = db.query(SkillGapReportDB).filter(SkillGapReportDB.id == report_id).first()
    
    if not db_report:
        return None
    
    # Convert back from JSON
    def dict_to_item(data: dict) -> SkillGapItem:
        from app.models import ProficiencyLevel
        return SkillGapItem(
            skill_name=data["skill_name"],
            status=data["status"],
            current_proficiency=ProficiencyLevel(data["current_proficiency"]) if data.get("current_proficiency") else None,
            required_proficiency=ProficiencyLevel(data["required_proficiency"]) if data.get("required_proficiency") else None,
            gap_severity=data["gap_severity"],
            recommendation=data.get("recommendation")
        )
    
    return SkillGapReport(
        user_name=db_report.user_name,
        current_role=db_report.current_role,
        target_role=db_report.target_role,
        skills_met=[dict_to_item(item) for item in (db_report.skills_met or [])],
        skills_missing=[dict_to_item(item) for item in (db_report.skills_missing or [])],
        skills_weak=[dict_to_item(item) for item in (db_report.skills_weak or [])],
        overall_gap_score=db_report.overall_gap_score,
        upskilling_path=db_report.upskilling_path,
        analysis_summary=db_report.analysis_summary
    )


def get_reports_by_profile(db: Session, profile_id: str) -> List[SkillGapReport]:
    """Get all reports for a user profile"""
    db_reports = db.query(SkillGapReportDB).filter(
        SkillGapReportDB.user_profile_id == profile_id
    ).all()
    
    reports = []
    for db_report in db_reports:
        def dict_to_item(data: dict) -> SkillGapItem:
            from app.models import ProficiencyLevel
            return SkillGapItem(
                skill_name=data["skill_name"],
                status=data["status"],
                current_proficiency=ProficiencyLevel(data["current_proficiency"]) if data.get("current_proficiency") else None,
                required_proficiency=ProficiencyLevel(data["required_proficiency"]) if data.get("required_proficiency") else None,
                gap_severity=data["gap_severity"],
                recommendation=data.get("recommendation")
            )
        
        reports.append(SkillGapReport(
            user_name=db_report.user_name,
            current_role=db_report.current_role,
            target_role=db_report.target_role,
            skills_met=[dict_to_item(item) for item in (db_report.skills_met or [])],
            skills_missing=[dict_to_item(item) for item in (db_report.skills_missing or [])],
            skills_weak=[dict_to_item(item) for item in (db_report.skills_weak or [])],
            overall_gap_score=db_report.overall_gap_score,
            upskilling_path=db_report.upskilling_path,
            analysis_summary=db_report.analysis_summary
        ))
    
    return reports

