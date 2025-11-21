# main.py
import os
from fastapi import FastAPI, Depends, HTTPException, Request
from pydantic import BaseModel, Field
import google.generativeai as genai
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from sqlalchemy import func

# Import database & models
from database import ChatMessage, get_db

from fastapi.middleware.cors import CORSMiddleware

# 1. Load env
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY not set in environment")

genai.configure(api_key=API_KEY)

# 2. System instruction / persona
SYSTEM_INSTRUCTION = """
You are 'Travel Buddy' — a friendly, enthusiastic travel-focused companion.
Your ONLY domain is TRAVEL. Your purpose is to help users with:
• destination suggestions
• itinerary planning
• hotel/food recommendations
• travel budgeting
• cultural/local tips
• season-based travel ideas
• exploring places and experiences

❌ You MUST NOT answer anything outside travel.
If the user asks about:
• coding/programming
• maths or logic problems
• politics or news opinions
• medical or legal advice
• personal life problems
• homework/assignments
• random general knowledge

→ Politely refuse AND immediately redirect them back to travel.

Tone Rules:
• Short, energetic, emoji-friendly responses.
• Conversational, NOT long factual paragraphs.
• Do NOT repeat your introduction every time.
• Maintain continuity in travel conversations.
"""

# Use the selected model (unchanged)
model = genai.GenerativeModel('gemini-2.0-flash', system_instruction=SYSTEM_INSTRUCTION)

app = FastAPI()

# CORS for development; lock this down for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class UserMessage(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=5000)

class ClearRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=200)

# Helpers
def build_gemini_history(db_msgs: List[ChatMessage]):
    history = []
    for m in db_msgs:
        # Skip system messages (titles)
        if m.role == "system":
            continue
        # Correct Gemini roles:
        role = "user" if m.role == "user" else "model"
        history.append({"role": role, "parts": [m.content]})
    return history

def generate_title_from_message(message: str) -> str:
    """Generate a short title from the first user message using Gemini."""
    try:
        title_model = genai.GenerativeModel('gemini-2.0-flash')
        prompt = f"Generate a very short title (max 5 words) for this message: '{message}'. Only return the title, nothing else."
        response = title_model.generate_content(prompt)
        title = response.text.strip().strip('"').strip("'")
        # Limit to 50 chars
        return title[:50] if len(title) > 50 else title
    except:
        # Fallback: use first few words
        words = message.split()[:5]
        return " ".join(words) + ("..." if len(message.split()) > 5 else "")

# --- Endpoints ---

@app.post("/api/chat")
async def chat_with_gemini(user_input: UserMessage, db: Session = Depends(get_db)):
    """
    Expects JSON:
    {
      "session_id": "uuid-or-local-id",
      "message": "Hi, suggest places..."
    }
    """
    session_id = user_input.session_id.strip()
    message_text = user_input.message.strip()
    if not message_text:
        raise HTTPException(status_code=400, detail="Empty message")

    try:
        # Check if this is the first user message in the session
        message_count = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id,
            ChatMessage.role.in_(["user", "bot"])
        ).count()
        
        is_first_message = message_count == 0
        
        # 1) Save user message
        user_msg_entry = ChatMessage(session_id=session_id, role="user", content=message_text, timestamp=datetime.utcnow())
        db.add(user_msg_entry)
        db.commit()
        db.refresh(user_msg_entry)

        # 2) If first message, generate and save title
        if is_first_message:
            title = generate_title_from_message(message_text)
            title_msg = ChatMessage(session_id=session_id, role="system", content=f"[title]{title}", timestamp=datetime.utcnow())
            db.add(title_msg)
            db.commit()

        # 3) Fetch recent session-specific history (limit to last N messages)
        N = 40  # number of DB messages to include; tune as needed
        history_rows = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.id.desc())
            .limit(N)
            .all()
        )
        history_rows = history_rows[::-1]  # chronological order

        # 4) Format history for Gemini
        chat_history = build_gemini_history(history_rows)

        # 5) Start conversation + generate response
        chat = model.start_chat(history=chat_history)
        response = chat.send_message(message_text)
        bot_reply_text = response.text if hasattr(response, "text") else str(response)

        # 6) Save bot reply
        bot_msg_entry = ChatMessage(session_id=session_id, role="bot", content=bot_reply_text, timestamp=datetime.utcnow())
        db.add(bot_msg_entry)
        db.commit()
        db.refresh(bot_msg_entry)

        return {"reply": bot_reply_text, "title_generated": is_first_message}

    except Exception as e:
        # On unexpected errors, return 500 with message (don't leak secrets)
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.get("/api/history")
def get_chat_history(session_id: str, limit: Optional[int] = 200, db: Session = Depends(get_db)):
    """
    GET /api/history?session_id=...&limit=100
    If session_id is provided, returns messages only for that session (recommended).
    If omitted, returns last `limit` messages globally (useful for admin).
    """
    limit = min(int(limit or 200), 2000)
    if session_id:
        msgs = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.id.asc())
            .all()
        )
    
    # serialize
    return [
        {
            "id": m.id,
            "session_id": m.session_id,
            "role": m.role,
            "content": m.content,
            "timestamp": m.timestamp.isoformat() if m.timestamp else None,
        }
        for m in msgs
    ]

@app.get("/api/stats")
def get_stats(session_id: Optional[str] = None, db: Session = Depends(get_db)):
    """
    GET /api/stats?session_id=...
    Returns total_messages either for session or globally.
    """
    if session_id:
        count = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).count()
    else:
        count = db.query(ChatMessage).count()
    return {"total_messages": count}

@app.delete("/api/clear")
def clear_history(req: ClearRequest, db: Session = Depends(get_db)):
    """
    Clears chat history for the provided session_id ONLY.
    Request body: { "session_id": "..." }
    """
    session_id = req.session_id.strip()
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")

    try:
        deleted = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
        db.commit()
        return {"message": "Cleared session", "deleted": deleted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions")
def list_sessions(db: Session = Depends(get_db)):
    """
    Return a list of sessions with auto-generated titles.
    """
    # Get all unique session IDs
    session_ids = db.query(ChatMessage.session_id).distinct().all()
    
    sessions = []
    for (sid,) in session_ids:
        # Get title from system message if exists
        title_msg = db.query(ChatMessage).filter(
            ChatMessage.session_id == sid,
            ChatMessage.role == "system",
            ChatMessage.content.like("[title]%")
        ).first()
        
        # Get last message timestamp
        last_msg = db.query(ChatMessage).filter(
            ChatMessage.session_id == sid
        ).order_by(ChatMessage.timestamp.desc()).first()
        
        # Get first user message as fallback
        first_user_msg = db.query(ChatMessage).filter(
            ChatMessage.session_id == sid,
            ChatMessage.role == "user"
        ).order_by(ChatMessage.timestamp.asc()).first()
        
        if title_msg:
            title = title_msg.content.replace("[title]", "").strip()
        elif first_user_msg:
            # Use first few words as title
            words = first_user_msg.content.split()[:5]
            title = " ".join(words) + ("..." if len(first_user_msg.content.split()) > 5 else "")
        else:
            title = "New Chat"
        
        sessions.append({
            "session_id": sid,
            "title": title,
            "last_message_time": last_msg.timestamp.isoformat() if last_msg else None,
            "snippet": first_user_msg.content[:60] if first_user_msg else ""
        })
    
    # Sort by last message time
    sessions.sort(key=lambda x: x["last_message_time"] or "", reverse=True)
    
    return {"sessions": sessions}

class NewSessionRequest(BaseModel):
    title: Optional[str] = None

@app.post("/api/sessions")
def create_session(req: NewSessionRequest = None, db: Session = Depends(get_db)):
    """
    Create a new session id and optionally a system message/title.
    Returns { session_id, title (optional) }.
    """
    import uuid
    sid = str(uuid.uuid4())
    # Optionally create an initial system message or title marker (not required)
    if req and req.title:
        msg = ChatMessage(session_id=sid, role="system", content=f"[title]{req.title}", timestamp=datetime.utcnow())
        db.add(msg)
        db.commit()
    return {"session_id": sid, "title": req.title if req else None}

class RenameSessionRequest(BaseModel):
    session_id: str
    title: str

@app.post("/api/sessions/rename")
def rename_session(req: RenameSessionRequest, db: Session = Depends(get_db)):
    """
    Rename a session by inserting a system marker message with the title.
    (Simple approach: store a system message as a title marker.)
    """
    sid = req.session_id.strip()
    if not sid:
        raise HTTPException(status_code=400, detail="session_id required")
    marker = ChatMessage(session_id=sid, role="system", content=f"[title]{req.title}", timestamp=datetime.utcnow())
    db.add(marker)
    db.commit()
    return {"ok": True}

class DeleteSessionRequest(BaseModel):
    session_id: str

@app.delete("/api/sessions")
def delete_session(req: DeleteSessionRequest, db: Session = Depends(get_db)):
    """
    Delete all messages for a session.
    """
    deleted = db.query(ChatMessage).filter(ChatMessage.session_id == req.session_id).delete()
    db.commit()
    return {"deleted": deleted}