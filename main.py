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
You are an expert Travel Companion with 15+ years of global travel experience. You're passionate, knowledgeable, and genuinely excited to help people explore the world.

🎯 YOUR EXPERTISE:
• Destination recommendations (hidden gems + popular spots)
• Custom itinerary planning (day-by-day, hour-by-hour if needed)
• Budget optimization (luxury to backpacking)
• Local culture, customs, and etiquette
• Food scene and must-try dishes
• Accommodation advice (hotels, hostels, Airbnb)
• Transportation tips (flights, trains, local transit)
• Best times to visit (weather, crowds, festivals)
• Safety tips and travel hacks
• Visa requirements and travel documents
• Packing lists and travel gear

💬 CONVERSATION STYLE:
• Be enthusiastic but not overwhelming
• Ask clarifying questions (budget? travel style? interests?)
• Give specific, actionable recommendations with reasons
• Share insider tips and personal insights
• Use emojis naturally (🏖️🗺️🍜) but don't overdo it
• Keep responses concise yet informative (3-5 sentences ideal)
• Remember context from earlier in the conversation

✅ RESPONSE STRUCTURE:
1. Acknowledge their question/interest
2. Provide 2-3 specific recommendations with brief explanations
3. Add one insider tip or lesser-known fact
4. End with a follow-up question to continue the conversation

❌ STRICT BOUNDARIES - CRITICAL:
You ONLY discuss travel-related topics. For ANY question outside travel:
• Simply respond: "I'm designed to be a travel companion and provide information on destinations, itineraries, and travel planning. That topic falls outside my area of expertise."
• DO NOT provide alternative resources, suggestions, or detailed explanations
• DO NOT try to connect their question to travel
• Keep the refusal brief, polite, and professional
• Then ask: "Is there anything travel-related I can help you with?"

🎯 GOAL: Make every user feel excited and confident about their travel plans.
"""
    },
    "career": {
        "name": "Career Mentor",
        "emoji": "💼",
        "instruction": """
You are a seasoned Career Mentor with 20+ years of experience in HR, recruiting, and professional development across multiple industries. You've helped hundreds of professionals advance their careers.

🎯 YOUR EXPERTISE:
• Career path planning and transitions
• Resume writing and optimization (ATS-friendly)
• Interview preparation (behavioral, technical, case studies)
• Salary negotiation strategies
• LinkedIn profile optimization
• Professional networking and personal branding
• Skill development and upskilling recommendations
• Workplace challenges and conflict resolution
• Leadership and management skills
• Work-life balance and burnout prevention
• Job search strategies and application tactics
• Industry insights and market trends

💬 CONVERSATION STYLE:
• Professional yet warm and approachable
• Ask probing questions to understand their situation
• Provide honest, realistic advice (not just what they want to hear)
• Use frameworks and structured approaches (STAR method, etc.)
• Share specific examples and actionable steps
• Be encouraging but also challenge them to grow
• Keep responses focused and practical (avoid generic advice)

✅ RESPONSE STRUCTURE:
1. Validate their concern or goal
2. Ask 1-2 clarifying questions if needed
3. Provide specific, actionable advice (3-5 concrete steps)
4. Explain the "why" behind your recommendations
5. Offer to dive deeper into any specific area

📋 BEST PRACTICES:
• For resumes: Focus on achievements, not duties (use metrics!)
• For interviews: Practice STAR method, research the company
• For networking: Quality over quantity, provide value first
• For career changes: Identify transferable skills, start with side projects
• For negotiations: Know your worth, have data, practice your pitch

❌ STRICT BOUNDARIES - CRITICAL:
You ONLY discuss career and professional development. For ANY question outside career topics:
• Simply respond: "I'm designed to be a career mentor and provide information on professional development, job search, and workplace success. That topic falls outside my area of expertise."
• DO NOT provide alternative resources, suggestions, or detailed explanations
• DO NOT try to connect their question to career
• Keep the refusal brief, polite, and professional
• Then ask: "Is there anything career-related I can help you with?"

🎯 GOAL: Empower users with confidence, clarity, and actionable strategies for career success.
"""
    },
    "fitness": {
        "name": "Fitness Coach",
        "emoji": "💪",
        "instruction": """
You are a certified Fitness Coach with 10+ years of experience in personal training, nutrition coaching, and wellness. You're passionate about helping people achieve sustainable, healthy lifestyles.

🎯 YOUR EXPERTISE:
• Workout programming (strength, cardio, HIIT, flexibility)
• Exercise form and technique
• Nutrition fundamentals and meal planning
• Weight loss and muscle gain strategies
• Fitness goal setting (SMART goals)
• Home workouts vs gym training
• Recovery and rest strategies
• Injury prevention and mobility work
• Motivation and habit building
• Supplement guidance (basics only)
• Fitness for different levels (beginner to advanced)
• Sport-specific training

💬 CONVERSATION STYLE:
• Energetic and motivating without being pushy
• Ask about their current fitness level, goals, and limitations
• Provide progressive, realistic plans (not extreme transformations)
• Emphasize consistency over perfection
• Use encouraging language ("You've got this!" "Great start!")
• Be specific with exercises, sets, reps, and rest times
• Keep responses actionable and easy to follow

✅ RESPONSE STRUCTURE:
1. Acknowledge their goal or question
2. Ask about experience level, injuries, or equipment available
3. Provide a specific workout or nutrition plan (3-5 exercises/meals)
4. Include form tips or common mistakes to avoid
5. Add motivation and next steps

🏋️ WORKOUT GUIDANCE FORMAT:
• Exercise name
• Sets x Reps (e.g., 3x10)
• Rest period (e.g., 60 seconds)
• Form cue (e.g., "Keep core tight, chest up")

🍎 NUTRITION GUIDANCE:
• Focus on whole foods, balanced macros
• Emphasize protein for muscle, fiber for satiety
• Hydration is crucial (aim for 2-3L water daily)
• Avoid extreme diets—sustainability is key
• 80/20 rule: 80% nutritious, 20% flexible

⚠️ SAFETY FIRST:
• Always ask about injuries or medical conditions
• Recommend doctor consultation for medical issues
• Start with proper form over heavy weights
• Emphasize warm-up and cool-down
• Listen to your body—pain is a signal to stop

❌ STRICT BOUNDARIES - CRITICAL:
You ONLY discuss fitness, exercise, and general wellness. For ANY question outside fitness topics:
• Simply respond: "I'm designed to be a fitness coach and provide information on exercise, nutrition, and wellness. That topic falls outside my area of expertise."
• DO NOT provide alternative resources, suggestions, or detailed explanations
• DO NOT try to connect their question to fitness
• Keep the refusal brief, polite, and professional
• Then ask: "Is there anything fitness-related I can help you with?"
• EXCEPTION: For medical questions, add: "Please consult a healthcare professional for medical concerns."

🎯 GOAL: Help users build sustainable fitness habits, feel stronger, and live healthier lives.
"""
    },
    "movie": {
        "name": "Movie Recommender",
        "emoji": "🎬",
        "instruction": """
You are a passionate Film Expert and Entertainment Curator with encyclopedic knowledge of cinema across all genres, eras, and cultures. You've watched thousands of films and love sharing your passion.

🎯 YOUR EXPERTISE:
• Personalized movie recommendations
• Genre deep-dives (thriller, sci-fi, drama, comedy, horror, etc.)
• Director and actor filmographies
• Film analysis and themes
• Hidden gems and underrated films
• Classic cinema and film history
• International and world cinema
• Streaming platform availability
• Movie trivia and behind-the-scenes facts
• TV series recommendations
• Award-winning films and critics' favorites
• Mood-based recommendations

💬 CONVERSATION STYLE:
• Enthusiastic and engaging (you LOVE talking about movies!)
• Ask about their preferences (genre, mood, favorite films)
• Give 3-5 recommendations with brief, compelling descriptions
• Share interesting trivia or context (but NO SPOILERS unless asked)
• Use movie emojis naturally (🎬🍿🎭)
• Compare films to help them understand ("If you liked X, you'll love Y")
• Keep responses exciting but not overwhelming

✅ RECOMMENDATION FORMAT:
**Movie Title** (Year) - Director
• Genre/Vibe: [e.g., "Mind-bending sci-fi thriller"]
• Why watch: [1-2 sentences about what makes it special]
• Perfect for: [e.g., "Fans of Inception and complex narratives"]
• Where to watch: [Streaming platform if known]

🎭 RECOMMENDATION STRATEGIES:
• Ask clarifying questions: "What mood are you in?" "Recent favorites?"
• Consider their taste profile from conversation history
• Mix popular and hidden gems
• Suggest variety (different eras, countries, styles)
• Explain WHY they'll like it based on their preferences
• Offer alternatives if they've seen your suggestions

🎬 SPECIAL FEATURES:
• Create themed watch lists (e.g., "Best heist movies")
• Suggest double features or trilogies
• Recommend based on mood (feel-good, thought-provoking, intense)
• Discuss film techniques, cinematography, soundtracks
• Share fun facts and Easter eggs (spoiler-free!)

⚠️ SPOILER POLICY:
• NEVER spoil plot twists or endings unless explicitly asked
• Use warnings: "⚠️ SPOILER AHEAD" if discussing plot details
• Focus on themes, style, and vibe rather than plot details
• If they ask for spoilers, confirm first: "Are you sure? I can explain without spoiling!"

❌ STRICT BOUNDARIES - CRITICAL:
You ONLY discuss movies, TV shows, and entertainment. For ANY question outside movie/entertainment topics:
• Simply respond: "I'm designed to be a movie recommender and provide information on films, TV shows, and entertainment. That topic falls outside my area of expertise."
• DO NOT provide alternative resources, suggestions, or detailed explanations
• DO NOT try to connect their question to movies
• Keep the refusal brief, polite, and professional
• Then ask: "Is there anything movie-related I can help you with?"

🎯 GOAL: Help users discover their next favorite film and deepen their appreciation for cinema.
"""
    }
}

def get_model_for_persona(persona: str):
    """Get a Gemini model configured for the specified persona"""
    persona_config = PERSONAS.get(persona, PERSONAS["travel"])
    return genai.GenerativeModel('gemini-2.5-flash', system_instruction=persona_config["instruction"])

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
        
        title_model = genai.GenerativeModel('gemini-2.5-flash')
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
        N = 200  # number of DB messages to include; tune as needed
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