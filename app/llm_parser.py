"""
Parser to extract structured data from LLM responses
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from app.models import SkillGapItem, ProficiencyLevel, Skill, TargetRole


class LLMResponseParser:
    """Parse LLM text responses into structured data"""
    
    @staticmethod
    def parse_analysis_response(
        analysis_text: str,
        user_profile_skills: List[Skill]
    ) -> Tuple[List[SkillGapItem], List[SkillGapItem], List[SkillGapItem], List[Skill], float, List[str]]:
        """
        Parse LLM analysis response to extract:
        - skills_met
        - skills_missing
        - skills_weak
        - required_skills (for target role)
        - gap_score
        - upskilling_path
        """
        skills_met = []
        skills_missing = []
        skills_weak = []
        required_skills = []
        upskilling_path = []
        
        # Create user skills map for matching
        user_skills_map = {
            skill.name.lower().strip(): skill 
            for skill in user_profile_skills
        }
        
        # Extract required skills from "1. REQUIRED SKILLS" section
        required_skills = LLMResponseParser._extract_required_skills(analysis_text)
        
        # Extract skill gaps from "2. SKILL GAP ANALYSIS" section
        gap_items = LLMResponseParser._extract_skill_gaps(analysis_text, user_skills_map)
        
        # If we have required skills but no gap items, create gap items for all required skills
        if required_skills and not gap_items:
            for skill in required_skills:
                # Check if user has this skill
                skill_lower = skill.name.lower().strip()
                user_skill = None
                for usk, usv in user_skills_map.items():
                    if skill_lower in usk or usk in skill_lower:
                        user_skill = usv
                        break
                
                if user_skill:
                    # User has skill - check proficiency
                    if user_skill.proficiency and skill.proficiency:
                        user_level = LLMResponseParser._proficiency_to_num(user_skill.proficiency)
                        req_level = LLMResponseParser._proficiency_to_num(skill.proficiency)
                        if user_level >= req_level:
                            status = "met"
                            severity = "low"
                        else:
                            status = "weak"
                            severity = "medium"
                    else:
                        status = "weak"
                        severity = "medium"
                else:
                    status = "missing"
                    severity = "high"
                
                gap_items.append(SkillGapItem(
                    skill_name=skill.name,
                    status=status,
                    current_proficiency=user_skill.proficiency if user_skill else None,
                    required_proficiency=skill.proficiency,
                    gap_severity=severity,
                    recommendation=f"Learn/improve {skill.name}" if status != "met" else "Maintain proficiency"
                ))
        
        # Categorize gap items
        for item in gap_items:
            if item.status == "met":
                skills_met.append(item)
            elif item.status == "missing":
                skills_missing.append(item)
            elif item.status == "weak":
                skills_weak.append(item)
        
        # Extract upskilling path from "5. UPSKILLING PATH" or "4. ACTION PLAN" section
        upskilling_path = LLMResponseParser._extract_upskilling_path(analysis_text)
        
        # Calculate gap score
        total_skills = len(required_skills) if required_skills else len(gap_items)
        if total_skills > 0:
            met_count = len(skills_met)
            weak_count = len(skills_weak)
            gap_score = round(((met_count * 100 + weak_count * 50) / total_skills), 2)
        else:
            gap_score = 50.0
        
        return skills_met, skills_missing, skills_weak, required_skills, gap_score, upskilling_path
    
    @staticmethod
    def _extract_required_skills(text: str) -> List[Skill]:
        """Extract required skills from the analysis"""
        skills = []
        seen = set()
        
        # Look for "1. REQUIRED SKILLS" or "REQUIRED SKILLS" section
        patterns = [
            r'(?:1\.\s*)?\*\*?REQUIRED\s+SKILLS\*\*?[:\s]*(.*?)(?=\n\s*\*\*?2\.|SKILL\s+GAP|$)',
            r'(?:1\.\s*)?REQUIRED\s+SKILLS[:\s]*(.*?)(?=\n\s*\*\*?2\.|SKILL\s+GAP|$)',
            r'REQUIRED\s+SKILLS\s+for[:\s]*(.*?)(?=\n\s*\*\*?2\.|SKILL\s+GAP|$)'
        ]
        
        skills_text = None
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                skills_text = match.group(1)
                break
        
        if skills_text:
            # Extract from table format - handle multi-column tables
            # Pattern: | Category | Core Skills | Typical Proficiency |
            # Extract from "Core Skills" column (usually column 2)
            table_lines = skills_text.split('\n')
            for line in table_lines:
                if '|' in line:
                    parts = [p.strip() for p in line.split('|')]
                    # Skip header rows
                    if len(parts) >= 3 and parts[1].lower() not in ['category', 'core skills', 'skill', 'skills', 'name']:
                        # Try to extract skills from the "Core Skills" column
                        skills_col = parts[1] if len(parts) > 1 else ""
                        proficiency_col = parts[2] if len(parts) > 2 else ""
                        
                        # Skills column might contain comma-separated skills
                        skill_names = [s.strip() for s in skills_col.split(',')]
                        proficiency = LLMResponseParser._parse_proficiency(proficiency_col.lower())
                        
                        for skill_name in skill_names:
                            if skill_name and len(skill_name) > 2 and skill_name.lower() not in ['core skills', 'skills']:
                                # Clean up skill name
                                skill_name = re.sub(r'\([^\)]+\)', '', skill_name).strip()
                                if skill_name and skill_name not in seen:
                                    seen.add(skill_name)
                                    skills.append(Skill(name=skill_name, proficiency=proficiency))
            
            # If no table format, try list format
            if not skills:
                # Look for patterns like "- Skill Name (proficiency)" or "• Skill Name"
                skill_lines = re.findall(
                    r'(?:[-•*]|\d+\.)\s*\*\*?([^*]+?)\*\*?(?:\s*\(([^\)]+)\))?',
                    skills_text
                )
                
                for skill_match in skill_lines:
                    skill_name = skill_match[0].strip()
                    proficiency_text = (skill_match[1] or "").strip().lower()
                    
                    if skill_name and len(skill_name) > 2:
                        proficiency = LLMResponseParser._parse_proficiency(proficiency_text)
                        if skill_name not in seen:
                            seen.add(skill_name)
                            skills.append(Skill(name=skill_name, proficiency=proficiency))
        
        # Fallback: extract from any table in the REQUIRED SKILLS section
        if not skills and skills_text:
            # Look for any table rows
            all_table_rows = re.findall(r'\|([^|]+)\|([^|]+)\|([^|]*)\|', skills_text)
            for row in all_table_rows:
                skill_name = row[1].strip()  # Usually skills are in second column
                proficiency_text = row[2].strip().lower() if len(row) > 2 else ""
                
                if (skill_name and len(skill_name) > 2 and 
                    skill_name.lower() not in ['skill', 'name', 'category', 'core skills', 'skills'] and
                    skill_name not in seen):
                    seen.add(skill_name)
                    proficiency = LLMResponseParser._parse_proficiency(proficiency_text)
                    skills.append(Skill(name=skill_name, proficiency=proficiency))
        
        return skills
    
    @staticmethod
    def _extract_skill_gaps(text: str, user_skills_map: Dict[str, Skill]) -> List[SkillGapItem]:
        """Extract skill gap items from the analysis"""
        gap_items = []
        
        # Look for "2. SKILL GAP ANALYSIS" or "SKILL GAP" section
        patterns = [
            r'(?:2\.\s*)?\*\*?SKILL\s+GAP\s+ANALYSIS\*\*?[:\s]*(.*?)(?=\n\s*\*\*?3\.|HOW\s+TO\s+START|$)',
            r'(?:2\.\s*)?SKILL\s+GAP\s+ANALYSIS[:\s]*(.*?)(?=\n\s*\*\*?3\.|HOW\s+TO\s+START|$)',
            r'SKILL\s+GAP[:\s]*(.*?)(?=\n\s*\*\*?3\.|HOW\s+TO\s+START|$)'
        ]
        
        gaps_text = None
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                gaps_text = match.group(1)
                break
        
        if gaps_text:
            # Extract from table format - handle various table structures
            table_lines = gaps_text.split('\n')
            for line in table_lines:
                if '|' in line and line.strip().startswith('|'):
                    parts = [p.strip() for p in line.split('|')]
                    # Skip separator rows and headers
                    if len(parts) >= 4 and parts[1].lower() not in ['skill', 'skill name', 'name', 'current level', 'required level', '---', '']:
                        skill_name = parts[1].strip()
                        current_level = parts[2].strip().lower() if len(parts) > 2 else ""
                        required_level = parts[3].strip().lower() if len(parts) > 3 else ""
                        status = parts[4].strip().lower() if len(parts) > 4 and parts[4] else ""
                        severity = parts[5].strip().lower() if len(parts) > 5 and parts[5] else "medium"
                        recommendation = parts[6].strip() if len(parts) > 6 and parts[6] else ""
                        
                        if skill_name and len(skill_name) > 2:
                            # Determine status if not provided
                            if not status:
                                if "missing" in current_level or "none" in current_level or not current_level:
                                    status = "missing"
                                elif "beginner" in current_level and ("advanced" in required_level or "expert" in required_level):
                                    status = "weak"
                                elif current_level and required_level and current_level == required_level:
                                    status = "met"
                                else:
                                    status = "weak" if current_level else "missing"
                            
                            gap_items.append(SkillGapItem(
                                skill_name=skill_name,
                                status=status,
                                current_proficiency=LLMResponseParser._parse_proficiency(current_level),
                                required_proficiency=LLMResponseParser._parse_proficiency(required_level),
                                gap_severity=severity if severity in ["low", "medium", "high"] else "medium",
                                recommendation=recommendation or f"Learn/improve {skill_name}"
                            ))
        
        # Fallback: extract from "What you already have" and "What needs improvement" sections
        if not gap_items:
            # Look for "What you already have" section
            have_pattern = r'What\s+you\s+already\s+have[:\s]*(.*?)(?=What\s+needs|$)'
            have_match = re.search(have_pattern, text, re.IGNORECASE | re.DOTALL)
            if have_match:
                have_text = have_match.group(1)
                skills = re.findall(r'[-•*]\s*\*\*?([^*]+?)\*\*?', have_text)
                for skill_name in skills:
                    skill_name = skill_name.strip()
                    if skill_name:
                        gap_items.append(SkillGapItem(
                            skill_name=skill_name,
                            status="met",
                            gap_severity="low",
                            recommendation="Maintain proficiency"
                        ))
            
            # Look for "What needs improvement" section
            need_pattern = r'What\s+needs\s+(?:improvement|addition)[:\s]*(.*?)(?=\n\s*\*\*?\d+\.|$)'
            need_match = re.search(need_pattern, text, re.IGNORECASE | re.DOTALL)
            if need_match:
                need_text = need_match.group(1)
                skills = re.findall(r'[-•*]\s*([^\n]+?)(?:\.|$)', need_text)
                for skill_desc in skills[:10]:
                    skill_name = skill_desc.split('(')[0].strip()
                    if skill_name and len(skill_name) > 2:
                        gap_items.append(SkillGapItem(
                            skill_name=skill_name,
                            status="missing",
                            gap_severity="high",
                            recommendation=f"Learn {skill_name}"
                        ))
        
        return gap_items
    
    @staticmethod
    def _extract_upskilling_path(text: str) -> List[str]:
        """Extract upskilling path from the analysis"""
        path = []
        
        # Look for "5. UPSKILLING PATH" or "ACTION PLAN" section
        patterns = [
            r'(?:5\.\s*)?UPSKILLING\s+PATH[:\s]*(.*?)(?=\n\s*\*\*?\d+\.|$)',
            r'ACTION\s+PLAN[:\s]*(.*?)(?=\n\s*\*\*?\d+\.|$)',
            r'(?:4\.\s*)?ACTION\s+PLAN[:\s]*(.*?)(?=\n\s*\*\*?5\.|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                path_text = match.group(1)
                # Extract numbered or bulleted items
                items = re.findall(r'(?:^\s*(?:\d+\.|[-•*])\s*)(.+?)(?=\n\s*(?:\d+\.|[-•*])|$)', path_text, re.MULTILINE)
                for item in items:
                    cleaned = item.strip()
                    if cleaned and len(cleaned) > 10:
                        path.append(cleaned)
                break
        
        return path[:7]  # Limit to 7 items
    
    @staticmethod
    def _parse_proficiency(text: str) -> Optional[ProficiencyLevel]:
        """Parse proficiency level from text"""
        if not text:
            return None
        
        text_lower = text.lower().strip()
        
        if "expert" in text_lower or "master" in text_lower:
            return ProficiencyLevel.EXPERT
        elif "advanced" in text_lower or "senior" in text_lower:
            return ProficiencyLevel.ADVANCED
        elif "intermediate" in text_lower or "mid" in text_lower:
            return ProficiencyLevel.INTERMEDIATE
        elif "beginner" in text_lower or "junior" in text_lower or "basic" in text_lower:
            return ProficiencyLevel.BEGINNER
        
        return None
    
    @staticmethod
    def _proficiency_to_num(proficiency: ProficiencyLevel) -> int:
        """Convert proficiency level to numeric value for comparison"""
        mapping = {
            ProficiencyLevel.BEGINNER: 1,
            ProficiencyLevel.INTERMEDIATE: 2,
            ProficiencyLevel.ADVANCED: 3,
            ProficiencyLevel.EXPERT: 4
        }
        return mapping.get(proficiency, 0)

