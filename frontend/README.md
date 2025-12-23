# Skill Gap Analyzer - Frontend

A modern React frontend for the Skill Gap Identification System.

## Features

- **Profile Management**: Create and manage user profiles with skills and certifications
- **Skill Analysis**: AI-powered skill gap analysis with chatbot interface
- **Markdown Rendering**: Beautiful markdown rendering for analysis responses
- **Professional UI**: Modern, responsive design with Tailwind CSS

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Make sure the backend API is running on `http://localhost:8000`

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ProfileForm.jsx      # Profile creation form
│   │   ├── ProfileDisplay.jsx   # Profile details display
│   │   ├── ProfileList.jsx      # List of all profiles
│   │   ├── AnalysisChat.jsx    # Chatbot-style analysis interface
│   │   └── MarkdownRenderer.jsx # Markdown rendering component
│   ├── services/
│   │   └── api.js              # API service layer
│   ├── App.jsx                 # Main application component
│   ├── main.jsx                # Application entry point
│   └── index.css               # Global styles with Tailwind
├── tailwind.config.js          # Tailwind CSS configuration
└── package.json                # Dependencies and scripts
```

## Usage

1. **Create Profile**: Click "Create New Profile" and fill in your details
2. **View Profile**: Click on any profile to view details
3. **Analyze Skills**: Click "Analyze Skills" to start the chatbot interface
4. **Enter Target Role**: Type your target role in the input field
5. **Ask Questions**: Describe your career goals and get AI-powered analysis

## API Integration

The frontend communicates with the FastAPI backend at `http://localhost:8000`. Make sure CORS is enabled on the backend.

## Technologies

- React 19
- Vite
- Tailwind CSS
- Axios
- React Markdown
- React Syntax Highlighter
