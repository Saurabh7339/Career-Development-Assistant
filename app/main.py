"""
FastAPI Main Application - Skill Gap Identification System
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import json
import uuid
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.models import (
    UserProfile, TargetRole, SkillGapReport,
    ProfileUploadRequest, GapAnalysisRequest
)
from app.skill_analyzer import SkillAnalyzer
from app.llm_service import LLMService
from app.rag_pipeline import RAGPipeline
from app.database import init_db, get_db
from app import crud
from fastapi import Depends
from sqlalchemy.orm import Session

# Initialize FastAPI app
app = FastAPI(
    title="Skill Gap Identification System",
    description="AI-powered system for identifying skill gaps between user profiles and target roles",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
rag_pipeline = RAGPipeline()
llm_service = LLMService()
skill_analyzer = SkillAnalyzer(llm_service, rag_pipeline)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    print("Database initialized")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Skill Gap Identification System API",
        "version": "1.0.0",
        "endpoints": {
            "upload_profile": "/api/profiles/upload",
            "analyze_gap": "/api/analyze",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "rag_pipeline": "active",
        "llm_service": "active"
    }


@app.post("/api/profiles/upload", response_model=Dict[str, Any])
async def upload_profile(
    request: ProfileUploadRequest,
    db: Session = Depends(get_db)
):
    """
    Upload a user profile via text description.
    The system will extract structured information using LLM and store it in database and RAG.
    """
    try:
        # Generate profile ID
        profile_id = str(uuid.uuid4())
        
        # Extract profile using LLM
        extraction_result = llm_service.extract_profile_from_text(request.profile_text)
        
        # Create a basic profile from extracted info (you might want to parse extraction_result)
        # For now, store the raw text
        profile = UserProfile(
            name=request.name or "Unknown",
            current_role=request.current_role or "Unknown",
            raw_text=request.profile_text
        )
        
        # Store in database
        crud.create_user_profile(db, profile, profile_id)
        
        # Store in RAG pipeline
        metadata = {
            "profile_id": profile_id,
            "name": profile.name,
            "current_role": profile.current_role
        }
        
        chunks_added = rag_pipeline.add_profile(
            profile_id=profile_id,
            profile_text=request.profile_text,
            metadata=metadata
        )
        
        return {
            "profile_id": profile_id,
            "status": "uploaded",
            "chunks_added": chunks_added,
            "extracted_info": extraction_result.get("extracted_info", ""),
            "message": "Profile uploaded and processed successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading profile: {str(e)}")


@app.post("/api/profiles/upload-file")
async def upload_profile_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a user profile via file (text, JSON, etc.)
    """
    try:
        content = await file.read()
        text_content = content.decode('utf-8')
        
        # Try to parse as JSON first
        try:
            profile_data = json.loads(text_content)
            # If JSON, convert to text format
            profile_text = json.dumps(profile_data, indent=2)
        except:
            profile_text = text_content
        
        profile_id = str(uuid.uuid4())
        
        # Extract and store
        extraction_result = llm_service.extract_profile_from_text(profile_text)
        
        # Create profile and store in database
        profile = UserProfile(
            name="Unknown",
            current_role="Unknown",
            raw_text=profile_text
        )
        crud.create_user_profile(db, profile, profile_id)
        
        metadata = {
            "profile_id": profile_id,
            "filename": file.filename
        }
        
        chunks_added = rag_pipeline.add_profile(
            profile_id=profile_id,
            profile_text=profile_text,
            metadata=metadata
        )
        
        return {
            "profile_id": profile_id,
            "status": "uploaded",
            "chunks_added": chunks_added,
            "filename": file.filename,
            "extracted_info": extraction_result.get("extracted_info", ""),
            "message": "Profile file uploaded and processed successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


@app.post("/api/analyze", response_model=SkillGapReport)
async def analyze_skill_gap(
    request: GapAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Perform skill gap analysis between user profile and target role.
    Fetches user profile from database and provides detailed actionable recommendations.
    """
    try:
        # Retrieve user profile from database
        user_profile_data = crud.get_user_profile(db, request.user_profile_id)
        if not user_profile_data:
            raise HTTPException(
                status_code=404,
                detail=f"Profile {request.user_profile_id} not found"
            )
        
        # Convert dict to UserProfile object if needed
        # Remove 'id' key if present as it's not part of UserProfile model
        if isinstance(user_profile_data, dict):
            profile_dict = {k: v for k, v in user_profile_data.items() if k != 'id'}
            user_profile = UserProfile(**profile_dict)
        else:
            user_profile = user_profile_data
        
        # Perform analysis with user query
        gap_report, target_role_with_skills = skill_analyzer.analyze_gap(
            user_profile=user_profile,
            target_role=request.target_role,
            user_query=request.user_query,
            use_rag=request.use_rag
        )
        
        # Save target role with required skills to database (if extracted from LLM)
        target_role_id = None
        if target_role_with_skills.required_skills:
            try:
                # Create or update target role in database
                target_role_id = crud.create_target_role(db, target_role_with_skills)
            except Exception as e:
                print(f"Warning: Could not save target role to database: {e}")
        
        # Save report to database
        try:
            crud.save_skill_gap_report(db, gap_report, request.user_profile_id, target_role_id)
        except Exception as e:
            print(f"Warning: Could not save report to database: {e}")
        
        return gap_report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing gap: {str(e)}")


@app.post("/api/profiles/create", response_model=Dict[str, str])
async def create_profile(
    profile: UserProfile,
    db: Session = Depends(get_db)
):
    """
    Create a user profile directly (structured input)
    """
    try:
        profile_id = str(uuid.uuid4())
        
        # Store in database
        crud.create_user_profile(db, profile, profile_id)
        
        # Also add to RAG for future queries
        profile_text = skill_analyzer._format_profile(profile)
        rag_pipeline.add_profile(
            profile_id=profile_id,
            profile_text=profile_text,
            metadata={"profile_id": profile_id, "name": profile.name}
        )
        
        return {
            "profile_id": profile_id,
            "status": "created",
            "message": "Profile created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating profile: {str(e)}")


@app.post("/api/frameworks/add")
async def add_skill_framework(
    framework_name: str,
    framework_text: str,
    metadata: Optional[Dict] = None
):
    """
    Add a skill framework document to the RAG knowledge base
    """
    try:
        framework_id = str(uuid.uuid4())
        chunks_added = rag_pipeline.add_skill_framework(
            framework_id=framework_id,
            framework_text=framework_text,
            metadata={**(metadata or {}), "name": framework_name}
        )
        
        return {
            "framework_id": framework_id,
            "chunks_added": chunks_added,
            "message": "Skill framework added successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding framework: {str(e)}")


@app.get("/api/profiles/{profile_id}")
async def get_profile(profile_id: str, db: Session = Depends(get_db)):
    """Get a stored profile"""
    profile = crud.get_user_profile(db, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@app.get("/api/profiles")
async def list_profiles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all user profiles"""
    profiles = crud.get_all_profiles(db, skip=skip, limit=limit)
    return profiles


@app.put("/api/profiles/{profile_id}")
async def update_profile(
    profile_id: str,
    profile: UserProfile,
    db: Session = Depends(get_db)
):
    """Update a user profile"""
    success = crud.update_user_profile(db, profile_id, profile)
    if not success:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"status": "updated", "message": "Profile updated successfully"}


@app.delete("/api/profiles/{profile_id}")
async def delete_profile(profile_id: str, db: Session = Depends(get_db)):
    """Delete a user profile"""
    success = crud.delete_user_profile(db, profile_id)
    if not success:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"status": "deleted", "message": "Profile deleted successfully"}


@app.get("/api/profiles/{profile_id}/reports")
async def get_profile_reports(profile_id: str, db: Session = Depends(get_db)):
    """Get all skill gap reports for a profile"""
    reports = crud.get_reports_by_profile(db, profile_id)
    return reports


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

