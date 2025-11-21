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
import pytz
from collections import defaultdict
import time

# IST timezone
IST = pytz.timezone('Asia/Kolkata')

def get_ist_now():
    """Get current time in IST"""
    return datetime.now(IST)

# Import database & models
from database import ChatMessage, get_db

from fastapi.middleware.cors import CORSMiddleware

# 1. Load env
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY not set in environment")

genai.configure(api_key=API_KEY)

# 2. System instructions for different personas
PERSONAS = {
    "travel": {
        "name": "Travel Companion",
        "emoji": "✈️",
        "instruction": """
You are 'Travel Companion' — a friendly, enthusiastic travel-focused companion.
Your ONLY domain is TRAVEL. Your purpose is to help users with:
• destination suggestions
• itinerary planning
• hotel/food recommendations
• travel budgeting
• cultural/local tips
• season-based travel ideas
• exploring places and experiences

❌ You MUST NOT answer anything outside travel.
If the user asks about non-travel topics, politely refuse and redirect them back to travel.

Tone Rules:
• Short, energetic, emoji-friendly responses.
• Conversational, NOT long factual paragraphs.
• Do NOT repeat your introduction every time.
• Maintain continuity in conversations.
"""
    },
    "career": {
        "name": "Career Mentor",
        "emoji": "💼",
        "instruction": """
You are 'Career Mentor' — a professional, supportive career guidance expert.
Your ONLY domain is CAREER & PROFESSIONAL DEVELOPMENT. Your purpose is to help users with:
• career path planning
• resume and interview tips
• skill development advice
• job search strategies
• workplace challenges
• professional networking
• career transitions

❌ You MUST NOT answer anything outside career/professional topics.
If the user asks about non-career topics, politely refuse and redirect them back to career guidance.

Tone Rules:
• Professional yet approachable.
• Provide actionable, practical advice.
• Be encouraging and supportive.
• Do NOT repeat your introduction every time.
"""
    },
    "fitness": {
        "name": "Fitness Coach",
        "emoji": "💪",
        "instruction": """
You are 'Fitness Coach' — an energetic, motivating fitness and wellness expert.
Your ONLY domain is FITNESS & WELLNESS. Your purpose is to help users with:
• workout routines and exercises
• nutrition and diet advice
• fitness goal setting
• form and technique tips
• motivation and consistency
• injury prevention
• healthy lifestyle habits

❌ You MUST NOT answer anything outside fitness/wellness topics.
⚠️ IMPORTANT: You are NOT a medical professional. For medical concerns, always advise consulting a doctor.
If the user asks about non-fitness topics, politely refuse and redirect them back to fitness.

Tone Rules:
• Energetic, motivating, and positive.
• Use encouraging language.
• Be practical and safety-conscious.
• Do NOT repeat your introduction every time.
"""
    },
    "movie": {
        "name": "Movie Recommender",
        "emoji": "🎬",
        "instruction": """
You are 'Movie Recommender' — an enthusiastic, knowledgeable film expert and entertainment guide.
Your ONLY domain is MOVIES & ENTERTAINMENT. Your purpose is to help users with:
• movie recommendations based on preferences
• film analysis and reviews
• genre exploration
• actor/director information
• streaming platform suggestions
• movie trivia and facts
• watch lists and collections

❌ You MUST NOT answer anything outside movies/entertainment topics.
If the user asks about non-movie topics, politely refuse and redirect them back to movies.

Tone Rules:
• Enthusiastic and engaging.
• Share interesting insights without spoilers (unless asked).
• Be conversational and fun.
• Do NOT repeat your introduction every time.
"""
    }
}

def get_model_for_persona(persona: str):
    """Get a Gemini model configured for the specified persona"""
    persona_config = PERSONAS.get(persona, PERSONAS["travel"])
    return genai.GenerativeModel('gemini-2.0-flash', system_instruction=persona_config["instruction"])

app = FastAPI()

# CORS for development; lock this down for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple rate limiting: track requests per IP
rate_limit_store = defaultdict(list)
RATE_LIMIT_REQUESTS = 10  # max requests
RATE_LIMIT_WINDOW = 60  # per 60 seconds

def check_rate_limit(request: Request):
    """Simple rate limiting by IP address"""
    client_ip = request.client.host
    current_time = time.time()
    
    # Clean old requests outside the window
    rate_limit_store[client_ip] = [
        req_time for req_time in rate_limit_store[client_ip]
        if current_time - req_time < RATE_LIMIT_WINDOW
    ]
    
    # Check if limit exceeded
    if len(rate_limit_store[client_ip]) >= RATE_LIMIT_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds."
        )
    
    # Add current request
    rate_limit_store[client_ip].append(current_time)

# Pydantic models
class UserMessage(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=5000)
    persona: str = Field(default="travel", min_length=1, max_length=50)

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

def is_greeting(message: str) -> bool:
    """Check if message is just a greeting"""
    greetings = [
        "hi", "hello", "hey", "hii", "hiii", "hiiii", "helo", "helo", 
        "yo", "sup", "wassup", "whatsup", "namaste", "namaskar",
        "good morning", "good afternoon", "good evening", "good night",
        "gm", "gn", "morning", "evening"
    ]
    msg_lower = message.lower().strip().strip('!.,?')
    return msg_lower in greetings or len(message.strip()) < 3

def generate_title_from_conversation(messages: List[ChatMessage]) -> str:
    """Generate a meaningful title from conversation context (first 3 messages)"""
    try:
        # Get first 3 user messages (skip greetings)
        user_messages = [m.content for m in messages if m.role == "user" and not is_greeting(m.content)][:3]
        
        if not user_messages:
            return "New Chat"
        
        # Combine messages for context
        context = " | ".join(user_messages)
        
        title_model = genai.GenerativeModel('gemini-2.0-flash')
        prompt = f"""Based on this conversation context, generate a very short, meaningful title (max 4-5 words).
Context: {context}

Rules:
- Be specific and descriptive
- Use proper spelling (fix any typos in context)
- Focus on the main topic/intent
- Don't use greetings
- Return ONLY the title, nothing else

Title:"""
        response = title_model.generate_content(prompt)
        title = response.text.strip().strip('"').strip("'").strip('.')
        # Limit to 50 chars
        return title[:50] if len(title) > 50 else title
    except Exception as e:
        # Fallback: use first non-greeting message
        for m in messages:
            if m.role == "user" and not is_greeting(m.content):
                words = m.content.split()[:5]
                return " ".join(words) + ("..." if len(m.content.split()) > 5 else "")
        return "New Chat"

# --- Endpoints ---

@app.post("/api/chat")
async def chat_with_gemini(user_input: UserMessage, request: Request, db: Session = Depends(get_db)):
    """
    Expects JSON:
    {
      "session_id": "uuid-or-local-id",
      "message": "Hi, suggest places...",
      "persona": "travel" (optional, defaults to travel)
    }
    """
    # Apply rate limiting
    check_rate_limit(request)
    
    session_id = user_input.session_id.strip()
    message_text = user_input.message.strip()
    persona = user_input.persona or "travel"
    
    if not message_text:
        raise HTTPException(status_code=400, detail="Empty message")
    
    # Validate persona
    if persona not in PERSONAS:
        raise HTTPException(status_code=400, detail=f"Invalid persona. Choose from: {', '.join(PERSONAS.keys())}")

    try:
        # Check if this is the first user message in the session
        message_count = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id,
            ChatMessage.role.in_(["user", "bot"])
        ).count()
        
        is_first_message = message_count == 0
        
        # 1) Save user message with persona
        user_msg_entry = ChatMessage(session_id=session_id, role="user", content=message_text, persona=persona, timestamp=get_ist_now())
        db.add(user_msg_entry)
        db.commit()
        db.refresh(user_msg_entry)

        # 2) Smart title generation logic
        # Count user messages (after adding current one)
        user_msg_count = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id,
            ChatMessage.role == "user"
        ).count()
        
        # Generate/update title after 3rd user message (or 1st if not a greeting)
        should_generate_title = False
        
        if user_msg_count == 1 and not is_greeting(message_text):
            # First message and not a greeting - create temporary title
            should_generate_title = True
        elif user_msg_count == 3:
            # After 3 messages - generate meaningful title from context
            should_generate_title = True
        
        if should_generate_title:
            # Get all messages for context
            all_messages = db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id,
                ChatMessage.role.in_(["user", "bot"])
            ).order_by(ChatMessage.id.asc()).all()
            
            title = generate_title_from_conversation(all_messages)
            
            # Check if title already exists
            existing_title = db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id,
                ChatMessage.role == "system",
                ChatMessage.content.like("[title]%")
            ).first()
            
            if existing_title:
                # Update existing title
                existing_title.content = f"[title]{title}"
            else:
                # Create new title
                title_msg = ChatMessage(session_id=session_id, role="system", content=f"[title]{title}", timestamp=get_ist_now())
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

        # 5) Get model for current persona and start conversation
        model = get_model_for_persona(persona)
        chat = model.start_chat(history=chat_history)
        response = chat.send_message(message_text)
        bot_reply_text = response.text if hasattr(response, "text") else str(response)

        # 6) Save bot reply with persona
        bot_msg_entry = ChatMessage(session_id=session_id, role="bot", content=bot_reply_text, persona=persona, timestamp=get_ist_now())
        db.add(bot_msg_entry)
        db.commit()
        db.refresh(bot_msg_entry)

        return {"reply": bot_reply_text, "title_generated": should_generate_title}

    except HTTPException:
        # Re-raise HTTP exceptions (like rate limit)
        raise
    except Exception as e:
        # Log the full error for debugging
        import traceback
        print("ERROR in /api/chat:")
        print(traceback.format_exc())
        
        # Handle specific Gemini API errors
        error_msg = str(e)
        if "403" in error_msg or "PermissionDenied" in error_msg:
            raise HTTPException(status_code=403, detail="API key issue. Please check your Gemini API key.")
        elif "429" in error_msg or "quota" in error_msg.lower():
            raise HTTPException(status_code=429, detail="API rate limit exceeded. Please try again later.")
        elif "timeout" in error_msg.lower():
            raise HTTPException(status_code=504, detail="Request timeout. Please try again.")
        else:
            raise HTTPException(status_code=500, detail="An error occurred while processing your request.")

@app.get("/api/history")
def get_chat_history(session_id: str, limit: Optional[int] = 200, db: Session = Depends(get_db)):
    """
    GET /api/history?session_id=...&limit=100
    Returns only user and bot messages (excludes system messages like titles).
    """
    limit = min(int(limit or 200), 2000)
    if session_id:
        msgs = (
            db.query(ChatMessage)
            .filter(
                ChatMessage.session_id == session_id,
                ChatMessage.role.in_(["user", "bot"])  # Exclude system messages
            )
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
    Return a list of sessions with auto-generated titles and persona info.
    """
    # Get all unique session IDs
    session_ids = db.query(ChatMessage.session_id).distinct().all()
    
    sessions = []
    for (sid,) in session_ids:
        # Get title from system message if exists (get the most recent one)
        title_msg = db.query(ChatMessage).filter(
            ChatMessage.session_id == sid,
            ChatMessage.role == "system",
            ChatMessage.content.like("[title]%")
        ).order_by(ChatMessage.timestamp.desc()).first()
        
        # Get last message timestamp (exclude system messages for sorting)
        last_msg = db.query(ChatMessage).filter(
            ChatMessage.session_id == sid,
            ChatMessage.role.in_(["user", "bot"])  # Only user/bot messages for sorting
        ).order_by(ChatMessage.timestamp.desc()).first()
        
        # Get first user message as fallback
        first_user_msg = db.query(ChatMessage).filter(
            ChatMessage.session_id == sid,
            ChatMessage.role == "user"
        ).order_by(ChatMessage.timestamp.asc()).first()
        
        # Get persona from last message
        persona = last_msg.persona if last_msg and last_msg.persona else "travel"
        
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
            "persona": persona,
            "last_message_time": last_msg.timestamp.isoformat() if last_msg else None,
            "snippet": first_user_msg.content[:60] if first_user_msg else ""
        })
    
    # Sort by last message time
    sessions.sort(key=lambda x: x["last_message_time"] or "", reverse=True)
    
    return {"sessions": sessions}

class NewSessionRequest(BaseModel):
    title: Optional[str] = None
    persona: Optional[str] = "travel"

@app.post("/api/sessions")
def create_session(req: NewSessionRequest = None, db: Session = Depends(get_db)):
    """
    Create a new session id and optionally a system message/title.
    Returns { session_id, title (optional), persona }.
    """
    import uuid
    sid = str(uuid.uuid4())
    persona = req.persona if req and req.persona else "travel"
    
    # Optionally create an initial system message or title marker (not required)
    if req and req.title:
        msg = ChatMessage(session_id=sid, role="system", content=f"[title]{req.title}", persona=persona, timestamp=get_ist_now())
        db.add(msg)
        db.commit()
    return {"session_id": sid, "title": req.title if req else None, "persona": persona}

class RenameSessionRequest(BaseModel):
    session_id: str
    title: str

@app.post("/api/sessions/rename")
def rename_session(req: RenameSessionRequest, db: Session = Depends(get_db)):
    """
    Rename a session by updating or creating a title marker message.
    """
    sid = req.session_id.strip()
    if not sid:
        raise HTTPException(status_code=400, detail="session_id required")
    
    # Find existing title message
    existing_title = db.query(ChatMessage).filter(
        ChatMessage.session_id == sid,
        ChatMessage.role == "system",
        ChatMessage.content.like("[title]%")
    ).first()
    
    if existing_title:
        # Update existing title (keep original timestamp to not affect sorting)
        existing_title.content = f"[title]{req.title}"
        # Don't update timestamp - keep original
    else:
        # Create new title message with current time
        marker = ChatMessage(session_id=sid, role="system", content=f"[title]{req.title}", timestamp=get_ist_now())
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

@app.get("/api/personas")
def get_personas():
    """
    Get list of available personas/bot roles.
    """
    return {
        "personas": [
            {
                "id": key,
                "name": config["name"],
                "emoji": config["emoji"]
            }
            for key, config in PERSONAS.items()
        ]
    }