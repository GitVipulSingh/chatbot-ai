# 🤖 Multi-Persona Conversational Chatbot

A Gemini-powered conversational chatbot with multiple specialized personas built with Python FastAPI backend and React frontend.

## ✨ Features

### 🎭 Multiple Personas
Switch between different AI personalities, each specialized in their domain:

- **✈️ Travel Companion** - Your friendly travel guide for destinations, itineraries, and travel tips
- **💼 Career Mentor** - Professional career guidance, resume tips, and job search strategies
- **💪 Fitness Coach** - Workout routines, nutrition advice, and wellness guidance
- **🎬 Movie Recommender** - Film recommendations, reviews, and entertainment insights

### 💬 Chat Features
- **Session Management** - Create multiple chat sessions with different personas
- **Auto-Generated Titles** - Smart title generation based on conversation context
- **Persistent History** - All conversations saved in SQLite database
- **Real-time Messaging** - Instant responses with typing indicators
- **Markdown Support** - Rich text formatting in messages
- **Rate Limiting** - Built-in protection against API abuse

### 🎨 Modern UI
- WhatsApp-inspired clean interface
- Responsive design for all devices
- Session sidebar with persona indicators
- Easy persona switching
- Message timestamps in IST timezone

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+
- Gemini API Key ([Get one here](https://makersuite.google.com/app/apikey))

### Backend Setup

1. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up environment variables:**
Create a `.env` file in the root directory:
```
GEMINI_API_KEY=your_api_key_here
```

3. **Run database migration (if upgrading from old version):**
```bash
python migrate_db.py
```

4. **Start the FastAPI server:**
```bash
uvicorn main:app --reload
```

The backend will run on `http://127.0.0.1:8000`

### Frontend Setup

1. **Navigate to frontend directory:**
```bash
cd frontend
```

2. **Install dependencies:**
```bash
npm install
```

3. **Start the development server:**
```bash
npm run dev
```

The frontend will run on `http://localhost:5173`

## 📡 API Endpoints

### Chat
- `POST /api/chat` - Send a message and get AI response
- `GET /api/history` - Get chat history for a session
- `DELETE /api/clear` - Clear chat history for a session

### Sessions
- `GET /api/sessions` - List all chat sessions
- `POST /api/sessions` - Create a new session
- `POST /api/sessions/rename` - Rename a session
- `DELETE /api/sessions` - Delete a session

### Personas
- `GET /api/personas` - Get list of available personas

### Stats
- `GET /api/stats` - Get message count statistics

## 🎯 Usage

1. **Select a Persona** - Choose from the dropdown in the header
2. **Start Chatting** - Type your message and press Enter or click Send
3. **Switch Personas** - Change persona anytime to get specialized responses
4. **Manage Sessions** - Create, rename, or delete chat sessions from the sidebar
5. **View History** - All conversations are automatically saved

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - SQL toolkit and ORM
- **Google Gemini AI** - LLM for conversational AI
- **SQLite** - Lightweight database
- **Pydantic** - Data validation

### Frontend
- **React** - UI library
- **Axios** - HTTP client
- **React Markdown** - Markdown rendering
- **Vite** - Build tool

## 🔒 Security Features

- Rate limiting (10 requests per 60 seconds per IP)
- Input validation and sanitization
- CORS configuration
- Error handling with user-friendly messages

## 📝 Project Structure

```
.
├── main.py                 # FastAPI backend
├── database.py            # Database models and config
├── migrate_db.py          # Database migration script
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables
├── chat_history.db        # SQLite database
└── frontend/
    ├── src/
    │   ├── App.jsx        # Main React component
    │   ├── SessionsSidebar.jsx  # Sessions sidebar
    │   ├── Chat.css       # Styles
    │   └── main.jsx       # React entry point
    ├── package.json       # Node dependencies
    └── vite.config.js     # Vite configuration
```

## 🎨 Customization

### Adding New Personas

Edit `main.py` and add to the `PERSONAS` dictionary:

```python
PERSONAS = {
    "your_persona": {
        "name": "Your Persona Name",
        "emoji": "🎯",
        "instruction": """
        Your system instruction here...
        """
    }
}
```

### Modifying UI Theme

Edit `frontend/src/Chat.css` to customize colors, fonts, and layout.

## 🐛 Troubleshooting

**Backend won't start:**
- Check if Gemini API key is set in `.env`
- Ensure all Python dependencies are installed
- Check if port 8000 is available

**Frontend won't connect:**
- Verify backend is running on port 8000
- Check CORS settings in `main.py`
- Clear browser cache

**Database errors:**
- Run `python migrate_db.py` to update schema
- Delete `chat_history.db` to start fresh (loses all data)

## 📄 License

This project is open source and available for educational purposes.

## 🤝 Contributing

Feel free to fork, modify, and submit pull requests!

## 📧 Support

For issues or questions, please open an issue on the repository.

---

Built with ❤️ using Gemini AI, FastAPI, and React
