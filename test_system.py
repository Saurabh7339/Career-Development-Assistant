"""
Simple system test to verify installation and basic functionality
"""
import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    try:
        from app.models import UserProfile, TargetRole, SkillGapReport
        from app.rag_pipeline import RAGPipeline
        from app.llm_service import LLMService
        from app.skill_analyzer import SkillAnalyzer
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_rag_pipeline():
    """Test RAG pipeline initialization"""
    print("\nTesting RAG pipeline...")
    try:
        rag = RAGPipeline(persist_directory="./test_chroma_db")
        print("✅ RAG pipeline initialized")
        
        # Test adding a profile
        test_text = "John is a Python developer with 3 years of experience."
        chunks = rag.add_profile("test_profile_1", test_text, {"name": "John"})
        print(f"✅ Profile added ({chunks} chunks)")
        
        # Test retrieval
        contexts = rag.retrieve_relevant_context("Python developer", top_k=2)
        print(f"✅ Context retrieval works ({len(contexts)} results)")
        
        return True
    except Exception as e:
        print(f"❌ RAG pipeline error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_llm_service():
    """Test LLM service (requires Groq API key)"""
    print("\nTesting LLM service...")
    try:
        # Check if API key is set
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("⚠️  GROQ_API_KEY not set")
            print("   Set it with: export GROQ_API_KEY=your_key")
            print("   Get key from: https://console.groq.com/")
            return False
        
        llm = LLMService()
        print("✅ LLM service initialized")
        print(f"✅ Groq API key found (model: {llm.model_name})")
        
        return True
    except Exception as e:
        print(f"❌ LLM service error: {e}")
        print("   Make sure GROQ_API_KEY is set correctly")
        return False

def test_skill_analyzer():
    """Test skill analyzer"""
    print("\nTesting skill analyzer...")
    try:
        from app.models import Skill, ProficiencyLevel
        
        # Create test profile
        profile = UserProfile(
            name="Test User",
            current_role="Developer",
            skills=[
                Skill(name="Python", proficiency=ProficiencyLevel.ADVANCED),
                Skill(name="JavaScript", proficiency=ProficiencyLevel.INTERMEDIATE)
            ]
        )
        
        # Create target role
        target = TargetRole(
            role_name="Senior Developer",
            required_skills=[
                Skill(name="Python", proficiency=ProficiencyLevel.EXPERT),
                Skill(name="React", proficiency=ProficiencyLevel.ADVANCED)
            ]
        )
        
        # Initialize analyzer (without LLM for quick test)
        from app.rag_pipeline import RAGPipeline
        from app.llm_service import LLMService
        rag = RAGPipeline(persist_directory="./test_chroma_db")
        llm = LLMService()
        analyzer = SkillAnalyzer(llm, rag)
        
        print("✅ Skill analyzer initialized")
        print("   (Full analysis requires GROQ_API_KEY to be set)")
        
        return True
    except Exception as e:
        print(f"❌ Skill analyzer error: {e}")
        import traceback
        traceback.print_exc()
        return False

def cleanup():
    """Clean up test files"""
    import shutil
    try:
        if os.path.exists("./test_chroma_db"):
            shutil.rmtree("./test_chroma_db")
            print("\n✅ Test files cleaned up")
    except:
        pass

def main():
    """Run all tests"""
    print("=" * 60)
    print("Skill Gap Identification System - System Test")
    print("=" * 60)
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("RAG Pipeline", test_rag_pipeline()))
    results.append(("LLM Service", test_llm_service()))
    results.append(("Skill Analyzer", test_skill_analyzer()))
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    cleanup()
    
    if all_passed:
        print("\n🎉 All tests passed! System is ready.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

