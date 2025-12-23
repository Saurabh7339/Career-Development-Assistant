"""
LLM Service for Skill Gap Analysis
Uses Groq API (online LLM service)
"""
import os
from typing import Optional, Dict, Any
from langchain_groq import ChatGroq


class LLMService:
    """Service for interacting with LLM models using Groq API"""
    
    def __init__(self, model_name: str = "openai/gpt-oss-120b", max_retries: int = 2):
        """
        Initialize LLM service with Groq
        Default: llama-3.1-70b-versatile (via Groq API)
        Alternatives: llama-3.1-8b-instant, mixtral-8x7b-32768, gemma2-9b-it
        """
        self.model_name = model_name
        self.max_retries = max_retries
        self.llm = self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize LLM with retry logic"""
        retries = 0
        while retries < self.max_retries:
            try:
                api_key = os.getenv("GROQ_API_KEY")
                if not api_key:
                    raise ValueError("GROQ_API_KEY environment variable not set")
                
                print(f"Initializing Groq LLM with model: {self.model_name}")
                print(f"API Key found: {'Yes' if api_key else 'No'}")
                
                return ChatGroq(
                    temperature=0.7,
                    model_name=self.model_name,
                    api_key=api_key
                )
            except Exception as error:
                retries += 1
                print(f"Groq initialization attempt {retries} failed: {error}")
                if retries >= self.max_retries:
                    raise ConnectionError(f"Failed to initialize Groq LLM after {self.max_retries} attempts: {error}")
                # Could add a small delay here if needed
    
    def generate_skill_gap_analysis(
        self,
        user_profile: str,
        target_role: str,
        rag_context: Optional[str] = None,
        user_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate skill gap analysis using LLM with optional RAG context and user query
        """
        # Build prompt
        prompt = self._build_analysis_prompt(
            user_profile, target_role, rag_context, user_query
        )
        
        try:
            # Use LangChain's invoke method for ChatGroq
            response = self.llm.invoke(prompt)
            
            # Extract content from LangChain message
            analysis_text = response.content if hasattr(response, 'content') else str(response)
            
            return {
                "analysis": analysis_text,
                "model": self.model_name,
                "success": True
            }
        except Exception as e:
            print(f"LLM generation error: {e}")
            return {
                "analysis": f"Error generating analysis: {str(e)}",
                "model": self.model_name,
                "success": False,
                "error": str(e)
            }
    
    def extract_profile_from_text(self, profile_text: str) -> Dict[str, Any]:
        """Extract structured profile information from text using LLM"""
        prompt = f"""Extract the following information from this user profile text and return it in a structured format:

User Profile Text:
{profile_text}

Please extract and return:
1. Name (if mentioned)
2. Current Role/Job Title
3. List of skills mentioned (with proficiency levels if available)
4. Certifications
5. Years of experience
6. Any other relevant information

Format your response as a clear, structured text that can be parsed."""
        
        try:
            response = self.llm.invoke(prompt)
            extracted_text = response.content if hasattr(response, 'content') else str(response)
            
            return {
                "extracted_info": extracted_text,
                "success": True
            }
        except Exception as e:
            return {
                "extracted_info": "",
                "success": False,
                "error": str(e)
            }
    
    def format_analysis_response(
        self,
        structured_analysis: str,
        user_name: str,
        current_role: str,
        target_role: str,
        gap_score: float,
        user_query: Optional[str] = None
    ) -> str:
        """
        Format the structured analysis into a nice, pleasant, well-documented written style.
        This is a second LLM call to transform the technical analysis into a user-friendly format.
        """
        # Determine assessment based on gap score
        if gap_score >= 80:
            assessment = "excellent progress—you're very close to your goal"
        elif gap_score >= 60:
            assessment = "good progress—you're well on your way"
        elif gap_score >= 40:
            assessment = "moderate progress—a clear path forward exists"
        else:
            assessment = "significant journey ahead, but the path is well-defined"
        
        prompt = f"""You are a friendly, professional career advisor. Transform the following technical skill gap analysis into a warm, encouraging, and well-formatted response.

USER INFORMATION:
- Name: {user_name}
- Current Role: {current_role}
- Target Role: {target_role}
- Overall Gap Score: {gap_score:.2f}
- User's Goal: {user_query if user_query else "Transition to target role"}

Role: Act as an expert Career Strategist and Senior Architect Mentor. Your goal is to help me transition from my current role to my target role by analyzing my specific skill data.

Input data: {structured_analysis}

Task:
1. Executive Summary: Start with a warm, professional greeting and a high-level overview of my "Overall Gap Score." Summarize the main focus of my transition.

2. Prioritized Roadmap: Group the "Skills Missing" and "Skills Weak" into a 4-phase upskilling roadmap. Order them by "logical dependency" (e.g., learn foundational design before advanced technical management). Explain the "Why" for each phase.

3. Gap Analysis Tables:
   - Create a table for High-Severity Gaps (Priority 1).
   - Create a table for Medium/Low-Severity Gaps (Priority 2).
   - Columns should include: Skill, Status, and your specific Recommendation.

4. The "Quick-Win" Project: Design a 4-week hypothetical project that forces me to use at least 5 of my missing skills in a real-world scenario. Break it down week-by-week.

5. First 7-Day Action Plan: Give me 4 concrete, low-friction tasks I can start today to build momentum.

Formatting Style:
- Use professional but encouraging tone.
- Use Emojis for section headers to make it scannable.
- Use Markdown tables and bold text for key terms.
- Use LaTeX for any technical units (e.g., $25\\text{{ m}}^2$).


"""
        
        try:
            response = self.llm.invoke(prompt)
            formatted_text = response.content if hasattr(response, 'content') else str(response)
            return formatted_text
        except Exception as e:
            print(f"Error formatting analysis: {e}")
            return structured_analysis  # Fallback to original if formatting fails
    
    def _build_analysis_prompt(
        self,
        user_profile: str,
        target_role: str,
        rag_context: Optional[str] = None,
        user_query: Optional[str] = None
    ) -> str:
        """Build a brief, focused analysis prompt"""
        base_prompt = f"""Analyze the skill gap and provide actionable recommendations.

USER'S GOAL:
{user_query if user_query else "User wants to transition to the target role"}

CURRENT PROFILE:
{user_profile}

TARGET ROLE:
{target_role}
"""
        
        if rag_context:
            base_prompt += f"""

ADDITIONAL CONTEXT:
{rag_context}
"""
        
        base_prompt += """

Provide a BRIEF, ACTIONABLE analysis in the following structured format. Use tables with pipe separators (|) for all structured data:

**1. REQUIRED SKILLS** (List all key skills needed for this role):
Format as a table:
| Category | Core Skills | Typical Proficiency |
|----------|-------------|---------------------|
| Design & Visualization | 3-D modeling, Revit, SketchUp | advanced |
| Technical Knowledge | Building codes, structural principles | advanced |

IMPORTANT: List each skill separately in the Core Skills column, separated by commas. Extract individual skills from the table.

**2. SKILL GAP ANALYSIS** (Compare user's current skills with required skills):
Format as a table with EXACTLY these columns:
| Skill | Current Level | Gap / Needed Level | Status | Severity | Recommendation |
|-------|---------------|--------------------|--------|----------|----------------|
| Skill Name | beginner/none/intermediate/advanced | intermediate/advanced/expert | met/missing/weak | high/medium/low | Brief recommendation |

For each required skill, create a row with:
- Status: "met" if user has it at required level, "weak" if user has it but below required level, "missing" if user doesn't have it
- Severity: "high" for critical missing skills, "medium" for important, "low" for nice-to-have

**3. HOW TO START** (For each missing/weak skill):
| Skill | What to Learn | How to Start | Quick Win Project |
|-------|---------------|--------------|------------------|
| Skill Name | Specific topics | Resources/courses | Simple project idea |

**4. ACTION PLAN** (3-5 immediate next steps for next week):
1. Step 1: ...
2. Step 2: ...
3. Step 3: ...

**5. UPSKILLING PATH** (Prioritized learning roadmap):
1. First priority skill and why
2. Second priority skill and why
3. ...

IMPORTANT: 
- Use proper table format with pipe separators (|)
- Ensure all required skills from section 1 appear in section 2's gap analysis
- Be specific and actionable"""
        
        return base_prompt

