# 🤖 Multi-Persona Conversational Chatbot

A production-ready, Gemini-powered conversational AI platform with 4 specialized personas. Built with Python FastAPI backend and React frontend, featuring intelligent session management and domain-specific expertise.

## ✨ Features

### 🎭 Four Specialized AI Personas

Each persona is an expert in their domain with 10-20 years of experience, providing professional, focused responses:

#### ✈️ Travel Companion
- **Expertise:** 15+ years of global travel experience
- **Specialties:** Destination recommendations, itinerary planning, budget optimization, local culture tips, visa requirements, travel hacks
- **Style:** Enthusiastic, knowledgeable, practical with insider tips

#### 💼 Career Mentor  
- **Expertise:** 20+ years in HR, recruiting, and professional development
- **Specialties:** Resume optimization (ATS-friendly), interview prep (STAR method), salary negotiation, LinkedIn optimization, career transitions
- **Style:** Professional yet warm, honest, actionable advice with frameworks

#### 💪 Fitness Coach
- **Expertise:** 10+ years certified personal training and nutrition coaching
- **Specialties:** Workout programming, exercise form, nutrition planning, goal setting, injury prevention, habit building
- **Style:** Energetic, motivating, safety-conscious with specific workout plans

#### 🎬 Movie Recommender
- **Expertise:** Encyclopedic knowledge of cinema across all genres and eras
- **Specialties:** Personalized recommendations, film analysis, hidden gems, streaming availability, spoiler-free insights
- **Style:** Enthusiastic, engaging, with mood-based suggestions

### 💬 Advanced Chat Features

- **Smart Session Management** - Create unlimited sessions, each remembers its persona
- **Auto-Generated Titles** - AI creates meaningful titles after 3 messages based on context
- **Persona Switching** - Seamlessly switch between personas anytime via dropdown
- **Persistent History** - All conversations saved in SQLite with IST timestamps
- **Real-time Messaging** - Instant responses with typing indicators
- **Markdown Support** - Rich text formatting in bot responses
- **Rate Limiting** - 10 requests per 60 seconds per IP for API protection
- **Professional Boundaries** - Each persona politely refuses off-topic questions

### 🎨 Modern UI/UX

- **WhatsApp-Inspired Design** - Clean, familiar interface
- **Responsive Layout** - Works perfectly on desktop, tablet, and mobile
- **Session Sidebar** - Quick navigation with persona emoji indicators
- **Dynamic Interface** - Header and placeholders adapt to selected persona
- **Smooth Animations** - Professional fade-ins and transitions
- **IST Timezone** - All timestamps in Indian Standard Time

## 🚀 Quick Start

### Prerequisites

Before starting, ensure you have the following installed:

#### Required Software
- **Python 3.8 or higher** - [Download Python](https://www.python.org/downloads/)
  - Verify: `python --version`
- **Node.js 16 or higher** - [Download Node.js](https://nodejs.org/)
  - Verify: `node --version`
  - npm comes bundled with Node.js
- **Git** (optional, for cloning) - [Download Git](https://git-scm.com/downloads/)

#### Required API Key
- **Gemini API Key** - [Get free key](https://makersuite.google.com/app/apikey)
  - Sign in with Google account
  - Create new API key
  - Copy and save it securely

#### Python Virtual Environment
If you don't have a virtual environment set up:

```bash
# Create virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Activate it (Mac/Linux)
source venv/bin/activate
```

### Installation

#### 1. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Create .env file with your API key
echo GEMINI_API_KEY=your_actual_api_key_here > .env

# Activate virtual environment (IMPORTANT!)
venv\Scripts\activate

# Start the FastAPI server
uvicorn main:app --reload
```

**Note:** You must activate the virtual environment before running uvicorn, otherwise it won't find the installed packages.

Backend runs on `http://127.0.0.1:8000`

#### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend runs on `http://localhost:5173`

### First Use

1. Open `http://localhost:5173` in your browser
2. Select a persona from the dropdown (default: Travel Companion)
3. Start chatting! Try asking domain-specific questions
4. Switch personas anytime to access different expertise
5. Create multiple sessions for different topics

## 📡 API Documentation

### Chat Endpoints

#### POST `/api/chat`
Send a message and receive AI response.

**Request:**
```json
{
  "session_id": "uuid-string",
  "message": "Your question here",
  "persona": "travel"
}
```

**Response:**
```json
{
  "reply": "AI response text",
  "title_generated": false
}
```

#### GET `/api/history?session_id={id}`
Retrieve chat history for a session.

**Response:**
```json
[
  {
    "id": 1,
    "session_id": "uuid",
    "role": "user",
    "content": "Message text",
    "timestamp": "2024-01-01T12:00:00"
  }
]
```

#### DELETE `/api/clear`
Clear all messages in a session.

**Request:**
```json
{
  "session_id": "uuid-string"
}
```

### Session Endpoints

#### GET `/api/sessions`
List all chat sessions with metadata.

**Response:**
```json
{
  "sessions": [
    {
      "session_id": "uuid",
      "title": "Paris Travel Planning",
      "persona": "travel",
      "last_message_time": "2024-01-01T12:00:00",
      "snippet": "First message preview..."
    }
  ]
}
```

#### POST `/api/sessions`
Create a new session.

**Request:**
```json
{
  "title": "Optional title",
  "persona": "career"
}
```

#### POST `/api/sessions/rename`
Rename an existing session.

**Request:**
```json
{
  "session_id": "uuid",
  "title": "New Title"
}
```

#### DELETE `/api/sessions`
Delete a session and all its messages.

**Request:**
```json
{
  "session_id": "uuid"
}
```

### Utility Endpoints

#### GET `/api/personas`
Get list of available personas.

**Response:**
```json
{
  "personas": [
    {
      "id": "travel",
      "name": "Travel Companion",
      "emoji": "✈️"
    }
  ]
}
```

#### GET `/api/stats?session_id={id}`
Get message count statistics.

**Response:**
```json
{
  "total_messages": 42
}
```

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern, fast Python web framework
- **SQLAlchemy** - SQL toolkit and ORM
- **Google Gemini 2.0 Flash** - Latest LLM for conversational AI
- **SQLite** - Lightweight, serverless database
- **Pydantic** - Data validation using Python type hints
- **python-dotenv** - Environment variable management

### Frontend
- **React 18** - UI library with hooks
- **Vite** - Next-generation frontend build tool
- **Axios** - Promise-based HTTP client
- **React Markdown** - Markdown component for React
- **Pure CSS** - No heavy frameworks, optimized performance

### Development
- **Uvicorn** - Lightning-fast ASGI server
- **Hot Reload** - Both backend and frontend support live reloading

## 🔒 Security & Performance

### Security Features
- **Rate Limiting** - 10 requests per 60 seconds per IP address
- **Input Validation** - Pydantic models validate all inputs (1-5000 chars)
- **Persona Validation** - Only whitelisted personas accepted
- **SQL Injection Protection** - SQLAlchemy ORM prevents SQL injection
- **CORS Configuration** - Configurable cross-origin resource sharing
- **Error Handling** - User-friendly messages, no sensitive data exposed
- **API Key Protection** - Stored in .env, never exposed to frontend

### Performance Optimizations
- **Database Indexing** - Compound indexes on session_id and timestamp
- **Message History Limit** - Only last 40 messages sent to AI for context
- **Efficient Queries** - Optimized SQLAlchemy queries with proper filtering
- **Connection Pooling** - SQLAlchemy manages database connections
- **Frontend Optimization** - React memo, efficient re-renders

## 📝 Project Structure

```
multi-persona-chatbot/
├── main.py                      # FastAPI backend with all endpoints
├── database.py                  # SQLAlchemy models and database config
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables (API key)
├── .gitignore                   # Git ignore rules
├── chat_history.db             # SQLite database (auto-created)
├── README.md                    # This file
│
└── frontend/
    ├── src/
    │   ├── App.jsx              # Main React component
    │   ├── SessionsSidebar.jsx  # Session list sidebar component
    │   ├── Chat.css             # All styling (WhatsApp-inspired)
    │   └── main.jsx             # React entry point
    ├── public/
    │   └── vite.svg             # Favicon
    ├── index.html               # HTML template
    ├── package.json             # Node dependencies
    ├── vite.config.js           # Vite configuration
    └── eslint.config.js         # ESLint configuration
```

## 🎨 Customization Guide

### Adding a New Persona

1. **Edit `main.py`** and add to the `PERSONAS` dictionary:

```python
PERSONAS = {
    # ... existing personas
    "cooking": {
        "name": "Cooking Assistant",
        "emoji": "🍳",
        "instruction": """
You are a professional Cooking Assistant with 15+ years of culinary experience...

🎯 YOUR EXPERTISE:
• Recipe recommendations and modifications
• Cooking techniques and tips
• Ingredient substitutions
• Meal planning and prep

💬 CONVERSATION STYLE:
• Friendly and encouraging
• Provide step-by-step instructions
• Ask about dietary restrictions

❌ STRICT BOUNDARIES - CRITICAL:
You ONLY discuss cooking, recipes, and culinary topics. For ANY question outside cooking:
• Simply respond: "I'm designed to be a cooking assistant and provide information on recipes, cooking techniques, and meal planning. That topic falls outside my area of expertise."
• DO NOT provide alternative resources
• Keep the refusal brief and professional
• Then ask: "Is there anything cooking-related I can help you with?"

🎯 GOAL: Help users become confident, creative cooks.
"""
    }
}
```

2. **Update `frontend/src/SessionsSidebar.jsx`** - Add emoji mapping:

```javascript
const personaEmojis = {
    travel: "✈️",
    career: "💼",
    fitness: "💪",
    movie: "🎬",
    cooking: "🍳"  // Add your new persona
};
```

3. **Restart both servers** to see your new persona!

### Customizing UI Theme

Edit `frontend/src/Chat.css`:

```css
/* Change primary color */
.chat-header {
  background: #00a884;  /* Change this */
}

/* Change message bubble colors */
.message-bubble.user {
  background: #d9fdd3;  /* User messages */
}

.message-bubble.bot {
  background-color: #ffffff;  /* Bot messages */
}
```

### Modifying Rate Limits

Edit `main.py`:

```python
RATE_LIMIT_REQUESTS = 10  # Max requests
RATE_LIMIT_WINDOW = 60    # Per 60 seconds
```

## 🐛 Troubleshooting

### Backend Issues

**Error: "GEMINI_API_KEY not set"**
- Create `.env` file in root directory
- Add: `GEMINI_API_KEY=your_actual_key`
- Restart backend server

**Error: "Port 8000 already in use"**
```bash
# Use different port
uvicorn main:app --reload --port 8001
```

**Error: "Module not found"**
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### Frontend Issues

**Error: "Cannot connect to backend"**
- Verify backend is running on port 8000
- Check browser console for CORS errors
- Try: `http://localhost:5173` instead of `127.0.0.1`

**Error: "npm install fails"**
```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Database Issues

**Error: "Database locked"**
- Close all connections to database
- Restart backend server

**Want to reset database:**
```bash
# Delete database file (loses all data!)
rm chat_history.db
# Restart backend to recreate
```

## 🚀 Production Deployment

### Backend Deployment (Railway/Render)

1. **Update CORS settings** in `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

2. **Use PostgreSQL** instead of SQLite:
```python
DATABASE_URL = os.getenv("DATABASE_URL")
```

3. **Add Procfile**:
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Frontend Deployment (Vercel/Netlify)

1. **Build for production:**
```bash
cd frontend
npm run build
```

2. **Update API URL** in `App.jsx`:
```javascript
const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
```

3. **Deploy `dist/` folder** to your hosting platform

## 📊 Database Schema

```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,           -- 'user', 'bot', or 'system'
    content TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    persona TEXT DEFAULT 'travel', -- 'travel', 'career', 'fitness', 'movie'
    
    INDEX ix_messages_session_id (session_id),
    INDEX ix_messages_session_timestamp (session_id, timestamp)
);
```

## 🎯 Use Cases

1. **Travel Planning** - Plan vacations, get destination tips, create itineraries
2. **Career Development** - Resume reviews, interview prep, career advice
3. **Fitness Journey** - Workout plans, nutrition guidance, motivation
4. **Movie Discovery** - Find your next favorite film, explore genres
5. **Multi-Domain Assistant** - Switch personas for different needs in one app

## 📄 License

This project is open source and available for educational and commercial use.

## 🤝 Contributing

Contributions are welcome! Please feel free to:
- Report bugs
- Suggest new features
- Submit pull requests
- Add new personas
- Improve documentation

## 📧 Support

For issues, questions, or feature requests:
- Open an issue on GitHub
- Check existing documentation
- Review troubleshooting section

---

**Built with ❤️ using Google Gemini AI, FastAPI, and React**

**Version:** 1.0.0  
**Last Updated:** November 2025  
**Status:** Production Ready ✅
