# ✈️ Travel Buddy - Gemini-Powered Conversational Chatbot

A topic-specific conversational chatbot built with Google Gemini LLM, FastAPI backend, and React frontend. Travel Buddy specializes in travel-related conversations including destination suggestions, itinerary planning, and local tips.

## 🎯 Features

### Backend (FastAPI + Gemini)
- ✅ Google Gemini 2.0 Flash integration with custom system prompts
- ✅ Multi-session conversation management
- ✅ SQLite database for persistent chat history
- ✅ Context-aware responses (maintains last 40 messages)
- ✅ RESTful API with CORS support
- ✅ Session statistics and analytics

### Frontend (React + Vite)
- ✅ Modern, responsive chat interface
- ✅ Sessions sidebar with create/rename/delete
- ✅ Markdown rendering for bot responses
- ✅ Real-time message counter
- ✅ Smooth animations and loading states
- ✅ Local storage for session persistence

### Database
- ✅ SQLAlchemy ORM with SQLite
- ✅ Indexed queries for performance
- ✅ Session-based message isolation
- ✅ Timestamp tracking

## 🏗 Architecture

```
├── backend/
│   ├── main.py              # FastAPI app with all endpoints
│   ├── database.py          # SQLAlchemy models and DB setup
│   ├── .env                 # Gemini API key
│   └── chat_history.db      # SQLite database (auto-created)
│
└── frontend/
    ├── src/
    │   ├── App.jsx          # Main chat component
    │   ├── SessionsSidebar.jsx  # Session management UI
    │   ├── Chat.css         # Modern styling
    │   └── main.jsx         # React entry point
    └── package.json
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+
- Google Gemini API key ([Get one here](https://aistudio.google.com/app/apikey))

### Backend Setup

1. **Install Python dependencies:**
```bash
pip install fastapi uvicorn google-generativeai python-dotenv sqlalchemy
```

2. **Configure API key:**
Edit `.env` file and add your Gemini API key:
```
GEMINI_API_KEY=your_api_key_here
```

3. **Run the backend:**
```bash
uvicorn main:app --reload
```
Backend will run on `http://127.0.0.1:8000`

### Frontend Setup

1. **Navigate to frontend directory:**
```bash
cd frontend
```

2. **Install dependencies:**
```bash
npm install
```

3. **Run development server:**
```bash
npm run dev
```
Frontend will run on `http://localhost:5173`

## 📡 API Endpoints

### Chat
- `POST /api/chat` - Send message and get bot response
  ```json
  {
    "session_id": "uuid",
    "message": "Suggest places to visit in Japan"
  }
  ```

### History
- `GET /api/history?session_id={id}` - Fetch chat history for a session

### Sessions
- `GET /api/sessions` - List all chat sessions
- `POST /api/sessions` - Create new session
- `POST /api/sessions/rename` - Rename a session
- `DELETE /api/sessions` - Delete a session

### Stats
- `GET /api/stats?session_id={id}` - Get message count

### Clear
- `DELETE /api/clear` - Clear chat history for a session

## 🎨 Customization

### Change Bot Topic/Persona

Edit the `SYSTEM_INSTRUCTION` in `main.py`:

```python
SYSTEM_INSTRUCTION = """
You are 'Fitness Coach' — a motivational fitness companion.
Your ONLY domain is FITNESS & HEALTH...
"""
```

### Adjust Context Window

Modify the history limit in `main.py`:

```python
N = 40  # Number of messages to include in context
```

### Styling

All styles are in `frontend/src/Chat.css`. The design uses:
- Teal gradient theme (#0f766e)
- Inter font family
- Glassmorphism effects
- Smooth animations

## 🔒 Security Notes

⚠️ **Important for Production:**
- Never commit `.env` file with real API keys
- Update CORS settings in `main.py` to restrict origins
- Add rate limiting for API endpoints
- Use environment variables for sensitive data
- Consider adding authentication

## 🧪 Testing

### Test Backend
```bash
# Check if server is running
curl http://127.0.0.1:8000/api/sessions

# Test chat endpoint
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test","message":"Hello"}'
```

### Test Frontend
Open browser to `http://localhost:5173` and:
1. Create a new chat session
2. Send a travel-related message
3. Verify bot responds appropriately
4. Test session switching and deletion

## 📊 Database Schema

```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY,
    session_id VARCHAR NOT NULL,
    role VARCHAR NOT NULL,  -- 'user', 'bot', or 'system'
    content VARCHAR NOT NULL,
    timestamp DATETIME NOT NULL
);
```

## 🎯 Project Requirements Met

✅ Topic-specific chatbot (Travel domain)
✅ Gemini API integration with system prompts
✅ FastAPI backend with RESTful endpoints
✅ SQLite database for persistence
✅ Conversation memory (40 messages context)
✅ React frontend with modern UI
✅ Session management
✅ Chat history loading
✅ Message statistics
✅ Markdown rendering
✅ Responsive design

## 🚧 Future Enhancements

- [ ] User authentication
- [ ] Export chat history
- [ ] Voice input/output
- [ ] Image sharing for destinations
- [ ] Multi-language support
- [ ] Suggested prompts/quick replies
- [ ] Search within chat history

## 📝 License

This is a case study project for educational purposes.

## 🤝 Contributing

Feel free to fork and customize for your own topic-specific chatbot!
