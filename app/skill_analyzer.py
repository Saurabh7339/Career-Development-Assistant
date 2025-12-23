"""
Skill Gap Analyzer - Core logic for comparing skills
"""
from typing import List, Dict, Any, Optional, Tuple
from app.models import (
    UserProfile, TargetRole, SkillGapReport, SkillGapItem,
    ProficiencyLevel, Skill
)
from app.llm_service import LLMService
from app.rag_pipeline import RAGPipeline
from app.llm_parser import LLMResponseParser
import re


class SkillAnalyzer:
    """Core skill gap analysis engine"""
    
    def __init__(self, llm_service: LLMService, rag_pipeline: Optional[RAGPipeline] = None):
        self.llm_service = llm_service
        self.rag_pipeline = rag_pipeline
    
    def analyze_gap(
        self,
        user_profile: UserProfile,
        target_role: TargetRole,
        user_query: Optional[str] = None,
        use_rag: bool = True
    ) -> Tuple[SkillGapReport, TargetRole]:
        """
        Perform comprehensive skill gap analysis
        """
        # Prepare profile text
        profile_text = self._format_profile(user_profile)
        
        # Prepare target role text
        role_text = self._format_target_role(target_role)
        
        # Get RAG context if enabled
        rag_context = None
        if use_rag and self.rag_pipeline:
            try:
                # Search for relevant context
                profile_query = f"{user_profile.name} {user_profile.current_role} skills experience"
                role_query = f"{target_role.role_name} required skills competencies"
                
                profile_context = self.rag_pipeline.search_skill_frameworks(profile_query, top_k=3)
                role_context = self.rag_pipeline.search_skill_frameworks(role_query, top_k=3)
                
                rag_context = f"Profile Context:\n{profile_context}\n\nRole Context:\n{role_context}"
            except Exception as e:
                print(f"RAG context retrieval error: {e}")
        
        # Step 1: Get structured LLM analysis with user query (LLM will determine required skills)
        llm_analysis = self.llm_service.generate_skill_gap_analysis(
            profile_text, role_text, rag_context, user_query
        )
        
        # Parse LLM response to extract structured data
        structured_analysis = llm_analysis.get("analysis", "")
        
        # Extract structured data from LLM response
        skills_met, skills_missing, skills_weak, required_skills, gap_score, upskilling_path = \
            LLMResponseParser.parse_analysis_response(structured_analysis, user_profile.skills)
        
        # If we got required skills from LLM, update target_role
        if required_skills:
            # Store required skills in target_role (will be saved to DB in main.py)
            target_role.required_skills = required_skills
        
        # Step 2: Format the structured analysis into a nice, pleasant written style
        formatted_summary = self.llm_service.format_analysis_response(
            structured_analysis=structured_analysis,
            user_name=user_profile.name,
            current_role=user_profile.current_role,
            target_role=target_role.role_name,
            gap_score=gap_score,
            user_query=user_query
        )
        
        report = SkillGapReport(
            user_name=user_profile.name,
            current_role=user_profile.current_role,
            target_role=target_role.role_name,
            skills_met=skills_met,
            skills_missing=skills_missing,
            skills_weak=skills_weak,
            overall_gap_score=gap_score,
            upskilling_path=upskilling_path if upskilling_path else None,
            analysis_summary=formatted_summary  # Use the nicely formatted version
        )
        
        return report, target_role
    
    def _rule_based_analysis(
        self,
        user_profile: UserProfile,
        target_role: TargetRole
    ) -> List[SkillGapItem]:
        """Perform rule-based skill matching"""
        gap_items = []
        
        user_skills_map = {
            skill.name.lower().strip(): skill 
            for skill in user_profile.skills
        }
        
        for required_skill in target_role.required_skills:
            skill_name = required_skill.name
            skill_name_lower = skill_name.lower().strip()
            
            # Try exact match first
            if skill_name_lower in user_skills_map:
                user_skill = user_skills_map[skill_name_lower]
                gap_item = self._compare_skill_levels(user_skill, required_skill, skill_name)
            else:
                # Try fuzzy matching
                matched_skill = self._fuzzy_match_skill(skill_name_lower, user_skills_map)
                if matched_skill:
                    gap_item = self._compare_skill_levels(matched_skill, required_skill, skill_name)
                else:
                    # Skill is missing
                    gap_item = SkillGapItem(
                        skill_name=skill_name,
                        status="missing",
                        required_proficiency=required_skill.proficiency,
                        gap_severity="high",
                        recommendation=f"Consider learning {skill_name} to meet role requirements"
                    )
            
            gap_items.append(gap_item)
        
        return gap_items
    
    def _fuzzy_match_skill(
        self,
        skill_name: str,
        user_skills_map: Dict[str, Skill]
    ) -> Optional[Skill]:
        """Fuzzy matching for similar skills"""
        # Simple keyword-based matching
        skill_keywords = set(skill_name.split())
        
        for user_skill_name, user_skill in user_skills_map.items():
            user_keywords = set(user_skill_name.split())
            
            # Check for significant overlap
            overlap = len(skill_keywords & user_keywords)
            if overlap > 0 and overlap >= len(skill_keywords) * 0.5:
                return user_skill
        
        # Check for common skill aliases
        aliases = {
            "js": "javascript",
            "react": "reactjs",
            "node": "nodejs",
            "ml": "machine learning",
            "ai": "artificial intelligence",
            "devops": "dev ops",
            "ui": "user interface",
            "ux": "user experience"
        }
        
        for alias, full_name in aliases.items():
            if alias in skill_name and full_name in user_skills_map:
                return user_skills_map[full_name]
            if full_name in skill_name and alias in user_skills_map:
                return user_skills_map[alias]
        
        return None
    
    def _compare_skill_levels(
        self,
        user_skill: Skill,
        required_skill: Skill,
        skill_name: str
    ) -> SkillGapItem:
        """Compare user skill level with required level"""
        if not required_skill.proficiency:
            # No proficiency requirement specified
            return SkillGapItem(
                skill_name=skill_name,
                status="met",
                current_proficiency=user_skill.proficiency,
                gap_severity="low",
                recommendation="Skill present, maintain proficiency"
            )
        
        if not user_skill.proficiency:
            # User has skill but no level specified - assume intermediate
            return SkillGapItem(
                skill_name=skill_name,
                status="weak",
                current_proficiency=ProficiencyLevel.INTERMEDIATE,
                required_proficiency=required_skill.proficiency,
                gap_severity="medium",
                recommendation=f"Improve {skill_name} proficiency to {required_skill.proficiency.value}"
            )
        
        # Compare proficiency levels
        proficiency_order = {
            ProficiencyLevel.BEGINNER: 1,
            ProficiencyLevel.INTERMEDIATE: 2,
            ProficiencyLevel.ADVANCED: 3,
            ProficiencyLevel.EXPERT: 4
        }
        
        user_level = proficiency_order.get(user_skill.proficiency, 0)
        required_level = proficiency_order.get(required_skill.proficiency, 0)
        
        if user_level >= required_level:
            return SkillGapItem(
                skill_name=skill_name,
                status="met",
                current_proficiency=user_skill.proficiency,
                required_proficiency=required_skill.proficiency,
                gap_severity="low",
                recommendation="Skill requirement met"
            )
        elif user_level >= required_level - 1:
            return SkillGapItem(
                skill_name=skill_name,
                status="weak",
                current_proficiency=user_skill.proficiency,
                required_proficiency=required_skill.proficiency,
                gap_severity="medium",
                recommendation=f"Improve {skill_name} from {user_skill.proficiency.value} to {required_skill.proficiency.value}"
            )
        else:
            return SkillGapItem(
                skill_name=skill_name,
                status="weak",
                current_proficiency=user_skill.proficiency,
                required_proficiency=required_skill.proficiency,
                gap_severity="high",
                recommendation=f"Significant improvement needed in {skill_name}"
            )
    
    def _calculate_gap_score(
        self,
        gap_items: List[SkillGapItem],
        total_skills: int
    ) -> float:
        """Calculate overall gap score (0-100, higher = better match)"""
        if total_skills == 0:
            return 100.0
        
        met_count = sum(1 for item in gap_items if item.status == "met")
        weak_count = sum(1 for item in gap_items if item.status == "weak")
        missing_count = sum(1 for item in gap_items if item.status == "missing")
        
        # Weighted scoring
        score = (met_count * 100 + weak_count * 50 + missing_count * 0) / total_skills
        
        return round(score, 2)
    
    def _format_profile(self, profile: UserProfile) -> str:
        """Format user profile as text"""
        text = f"Name: {profile.name}\n"
        text += f"Current Role: {profile.current_role}\n"
        
        if profile.experience_years:
            text += f"Years of Experience: {profile.experience_years}\n"
        
        if profile.skills:
            text += "\nSkills:\n"
            for skill in profile.skills:
                skill_text = f"  - {skill.name}"
                if skill.proficiency:
                    skill_text += f" ({skill.proficiency.value})"
                if skill.years_experience:
                    skill_text += f" - {skill.years_experience} years"
                text += skill_text + "\n"
        
        if profile.certifications:
            text += f"\nCertifications: {', '.join(profile.certifications)}\n"
        
        if profile.bio:
            text += f"\nBio: {profile.bio}\n"
        
        if profile.raw_text:
            text += f"\nAdditional Information:\n{profile.raw_text}\n"
        
        return text
    
    def _format_target_role(self, role: TargetRole) -> str:
        """Format target role as text"""
        text = f"Target Role: {role.role_name}\n"
        
        if role.description:
            text += f"Description: {role.description}\n"
        
        if role.skill_framework:
            text += f"Skill Framework: {role.skill_framework}\n"
        
        return text

