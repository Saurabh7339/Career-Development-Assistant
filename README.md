# Skill Gap Identification System

An AI-powered system for identifying skill gaps between user profiles and target roles using FastAPI, RAG (Retrieval Augmented Generation), and free LLM models.

## Architecture Overview

### High-Level Design

```
┌─────────────────┐
│   FastAPI API   │
│   (Backend)     │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼──────┐
│  RAG  │ │   LLM   │
│Pipeline│ │ Service │
└───┬───┘ └──┬──────┘
    │        │
┌───▼────────▼───┐
│  ChromaDB      │
│  (Vector Store)│
└────────────────┘
```

### Components

1. **FastAPI Backend**: RESTful API for profile upload, gap analysis, and reporting
2. **RAG Pipeline**: 
   - Document processing and chunking
   - Embedding generation (Sentence Transformers)
   - Vector storage (ChromaDB)
   - Semantic search and retrieval
3. **LLM Service**: 
   - Uses Groq API (online LLM service)
   - Model: llama-3.1-70b-versatile (via Groq)
   - Profile extraction from text
   - Skill gap analysis
   - Upskilling recommendations
4. **Skill Analyzer**: 
   - Rule-based skill matching
   - Fuzzy skill matching
   - Proficiency level comparison
   - Gap score calculation

## Data Flow

1. **Profile Upload**:
   - User uploads profile (text/JSON/file)
   - LLM extracts structured information
   - Text is chunked and embedded
   - Stored in ChromaDB vector store

2. **Target Role Definition**:
   - User provides target role with required skills
   - Can include skill framework documents

3. **Gap Analysis**:
   - Rule-based matching (exact + fuzzy)
   - RAG retrieval for enhanced context
   - LLM generates comprehensive analysis
   - Calculates gap scores and recommendations

4. **Report Generation**:
   - Skills met/missing/weak categorization
   - Overall gap score (0-100)
   - AI-generated upskilling path
   - Detailed analysis summary

## Installation

### Prerequisites

- Python 3.8+
- Groq API Key (free at https://console.groq.com/)

### Setup

1. **Activate virtual environment**:
```bash
source env/bin/activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Get Groq API Key**:
```bash
# Visit https://console.groq.com/
# Sign up for free account
# Get your API key from the dashboard
# Create .env file:
echo "GROQ_API_KEY=your_api_key_here" > .env
```

## Running the Application

```bash
# Start the FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc

## API Endpoints

### 1. Health Check
```
GET /health
```

### 2. Upload Profile (Text)
```
POST /api/profiles/upload
Body: {
  "profile_text": "John is a software developer with 5 years...",
  "name": "John Doe",
  "current_role": "Software Developer"
}
```

### 3. Upload Profile (File)
```
POST /api/profiles/upload-file
Body: multipart/form-data with file
```

### 4. Create Profile (Structured)
```
POST /api/profiles/create
Body: {
  "name": "John Doe",
  "current_role": "Software Developer",
  "skills": [
    {"name": "Python", "proficiency": "advanced"},
    {"name": "FastAPI", "proficiency": "intermediate"}
  ],
  ...
}
```

### 5. Analyze Skill Gap
```
POST /api/analyze
Body: {
  "user_profile": {...},
  "target_role": {
    "role_name": "Senior Data Engineer",
    "required_skills": [
      {"name": "Python", "proficiency": "expert"},
      {"name": "Spark", "proficiency": "advanced"}
    ]
  },
  "use_rag": true
}
```

### 6. Add Skill Framework
```
POST /api/frameworks/add
Body: {
  "framework_name": "SFIA Framework",
  "framework_text": "...",
  "metadata": {...}
}
```

## Example Usage

### Python Example

```python
import requests

# Upload profile
response = requests.post("http://localhost:8000/api/profiles/upload", json={
    "profile_text": """
    John is a software developer with 5 years of experience in Python and web development.
    He has worked with FastAPI, React, and PostgreSQL. He holds a certification in AWS.
    Currently working as a mid-level developer.
    """
})

profile_id = response.json()["profile_id"]

# Analyze gap
analysis = requests.post("http://localhost:8000/api/analyze", json={
    "user_profile_id": profile_id,
    "target_role": {
        "role_name": "Senior Full-Stack Engineer",
        "required_skills": [
            {"name": "Python", "proficiency": "expert"},
            {"name": "React", "proficiency": "advanced"},
            {"name": "Kubernetes", "proficiency": "intermediate"},
            {"name": "System Design", "proficiency": "advanced"}
        ]
    },
    "use_rag": True
})

print(analysis.json())
```

### cURL Example

```bash
# Upload profile
curl -X POST "http://localhost:8000/api/profiles/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "profile_text": "Jane is a data scientist with expertise in machine learning and Python."
  }'

# Analyze gap
curl -X POST "http://localhost:8000/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "user_profile": {
      "name": "Jane",
      "current_role": "Data Scientist",
      "skills": [
        {"name": "Python", "proficiency": "advanced"},
        {"name": "Machine Learning", "proficiency": "advanced"}
      ]
    },
    "target_role": {
      "role_name": "ML Engineer",
      "required_skills": [
        {"name": "Python", "proficiency": "expert"},
        {"name": "MLOps", "proficiency": "intermediate"},
        {"name": "Docker", "proficiency": "advanced"}
      ]
    }
  }'
```

## Features

### Current Features
- ✅ Text-based profile upload with LLM extraction
- ✅ File upload support (JSON, text)
- ✅ Structured profile creation
- ✅ RAG-enhanced skill gap analysis
- ✅ Rule-based + AI-based skill matching
- ✅ Fuzzy skill matching (e.g., "JS" ≈ "JavaScript")
- ✅ Proficiency level comparison
- ✅ Gap score calculation (0-100)
- ✅ AI-generated upskilling recommendations
- ✅ Skill framework document storage

### Extensions (Future)
- [ ] Weighted skill importance
- [ ] Learning resource recommendations (courses, mentors)
- [ ] Skill taxonomy with hierarchical matching
- [ ] Multi-role comparison
- [ ] Progress tracking over time
- [ ] Export reports (PDF, CSV)

## Technology Stack

- **Backend**: FastAPI
- **Vector Store**: ChromaDB
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **LLM**: Ollama (llama3.2:1b) - free, local
- **Text Processing**: LangChain
- **Data Models**: Pydantic

## Debugging & Troubleshooting

### Common Issues

1. **Ollama not running**:
   ```bash
   ollama serve
   ```

2. **Model not found**:
   ```bash
   ollama pull llama3.2:1b
   ```

3. **ChromaDB errors**: Delete `./chroma_db` folder and restart

4. **Port already in use**: Change port in `uvicorn` command

### Logs

Check the console output for:
- Embedding model loading
- RAG pipeline status
- LLM generation errors
- API request/response logs

## Project Structure

```
assgnmnt/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application
│   ├── models.py          # Pydantic models
│   ├── rag_pipeline.py   # RAG implementation
│   ├── llm_service.py    # LLM integration
│   └── skill_analyzer.py # Core analysis logic
├── requirements.txt
├── README.md
└── chroma_db/            # Vector store (created at runtime)
```

## License

MIT License

