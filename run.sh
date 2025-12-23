#!/bin/bash

# Script to run the Skill Gap Identification System

echo "Starting Skill Gap Identification System..."

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source env/bin/activate
fi

# Check if Groq API key is set
if [ -z "$GROQ_API_KEY" ]; then
    echo "Warning: GROQ_API_KEY environment variable is not set."
    echo "Please set it with: export GROQ_API_KEY=your_key"
    echo "Or create a .env file with: GROQ_API_KEY=your_key"
    echo "Get your API key from: https://console.groq.com/"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Start the FastAPI server
echo "Starting FastAPI server on http://localhost:8000"
echo "API docs available at http://localhost:8000/docs"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

