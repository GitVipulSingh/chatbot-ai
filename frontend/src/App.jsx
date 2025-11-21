// frontend/src/App.jsx
import { useState, useEffect, useRef } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import SessionsSidebar from "./SessionsSidebar";
import "./Chat.css";

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [msgCount, setMsgCount] = useState(0);

  const [sessionId, setSessionId] = useState(null);
  const [personas, setPersonas] = useState([]);
  const [currentPersona, setCurrentPersona] = useState("travel");
  const messagesEndRef = useRef(null);

  // Fetch available personas
  useEffect(() => {
    const fetchPersonas = async () => {
      try {
        const res = await axios.get("http://127.0.0.1:8000/api/personas");
        setPersonas(res.data.personas);
      } catch (error) {
        console.error("Error fetching personas:", error);
      }
    };
    fetchPersonas();
  }, []);

  // initialize or restore last active session id in localStorage
  useEffect(() => {
    let last = localStorage.getItem("travelbuddy_active_session");
    let lastPersona = localStorage.getItem("travelbuddy_persona") || "travel";
    setCurrentPersona(lastPersona);
    
    if (!last) {
      // optionally create a new session immediately
      createNewSession(null, lastPersona).then((sid) => {
        setSessionId(sid);
        localStorage.setItem("travelbuddy_active_session", sid);
      });
    } else {
      setSessionId(last);
    }
  }, []);

  useEffect(() => {
    if (sessionId) {
      fetchHistory();
      fetchStats();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const fetchHistory = async () => {
    if (!sessionId) return;
    try {
      const res = await axios.get("http://127.0.0.1:8000/api/history", {
        params: { session_id: sessionId },
      });
      setMessages(res.data);
    } catch (error) {
      console.error("Error fetching history:", error);
    }
  };

  const fetchStats = async () => {
    if (!sessionId) return;
    try {
      const res = await axios.get("http://127.0.0.1:8000/api/stats", {
        params: { session_id: sessionId },
      });
      setMsgCount(res.data.total_messages);
    } catch (error) {
      console.error("Error fetching stats:", error);
    }
  };

  const createNewSession = async (title = null, persona = null) => {
    try {
      const personaToUse = persona || currentPersona;
      const res = await axios.post("http://127.0.0.1:8000/api/sessions", { 
        title, 
        persona: personaToUse 
      });
      const sid = res.data.session_id;
      // persist active session
      localStorage.setItem("travelbuddy_active_session", sid);
      localStorage.setItem("travelbuddy_persona", personaToUse);
      setSessionId(sid);
      setCurrentPersona(personaToUse);
      setMessages([]);
      setMsgCount(0);
      return sid;
    } catch (e) {
      console.error("Failed to create session", e);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || !sessionId) return;
    const userMsg = { role: "user", content: input, timestamp: null };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await axios.post("http://127.0.0.1:8000/api/chat", {
        session_id: sessionId,
        message: userMsg.content,
        persona: currentPersona,
      });

      // Fetch updated history to get correct IST timestamps from backend
      await fetchHistory();
      fetchStats();
      
      // If title was generated/updated, trigger sidebar refresh
      if (res.data.title_generated) {
        // Trigger a custom event to refresh sidebar
        window.dispatchEvent(new CustomEvent('refreshSessions'));
      }
    } catch (error) {
      console.error("Error sending message:", error);
      
      // Display user-friendly error message
      let errorMsg = "Sorry, something went wrong. Please try again.";
      
      if (error.response) {
        const status = error.response.status;
        const detail = error.response.data?.detail;
        
        if (status === 429) {
          errorMsg = detail || "Too many requests. Please wait a moment and try again.";
        } else if (status === 403) {
          errorMsg = "API key issue. Please contact support.";
        } else if (status === 504) {
          errorMsg = "Request timeout. Please try again.";
        } else if (detail) {
          errorMsg = detail;
        }
      } else if (error.request) {
        errorMsg = "Cannot connect to server. Please check your connection.";
      }
      
      // Add error message to chat
      const errorBotMsg = {
        role: "bot",
        content: `⚠️ ${errorMsg}`,
        timestamp: new Date().toISOString()
      };
      setMessages((prev) => [...prev, errorBotMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") sendMessage();
  };

  const clearChat = async () => {
    if (!sessionId) return;
    try {
      await axios.delete("http://127.0.0.1:8000/api/clear", { data: { session_id: sessionId } });
      setMessages([]);
      setMsgCount(0);
    } catch (e) {
      console.error("Error clearing chat:", e);
    }
  };

  // Sidebar callbacks
  const handleSwitchSession = (sid, persona = "travel") => {
    if (!sid) {
      // create new session if null passed
      createNewSession(null, persona);
      return;
    }
    localStorage.setItem("travelbuddy_active_session", sid);
    localStorage.setItem("travelbuddy_persona", persona);
    setSessionId(sid);
    setCurrentPersona(persona);
  };

  const handlePersonaChange = (newPersona) => {
    setCurrentPersona(newPersona);
    localStorage.setItem("travelbuddy_persona", newPersona);
    // Create new session with new persona
    createNewSession(null, newPersona);
  };

  const handleDeleteSession = async (sid) => {
    try {
      await axios.delete("http://127.0.0.1:8000/api/sessions", { data: { session_id: sid } });
      if (sid === sessionId) {
        // create a new session and switch
        const newSid = await createNewSession();
        setSessionId(newSid);
      }
    } catch (e) {
      console.error("Failed to delete session", e);
    }
  };

  const handleRenameSession = async (sid, newTitle) => {
    try {
      await axios.post("http://127.0.0.1:8000/api/sessions/rename", { session_id: sid, title: newTitle });
    } catch (e) {
      console.error("Rename failed", e);
    }
  };

  return (
    <div className="app-shell">
      <SessionsSidebar
        activeSession={sessionId}
        currentPersona={currentPersona}
        onSwitch={handleSwitchSession}
        onNewSession={async () => {
          const sid = await createNewSession(null, currentPersona);
          return sid;
        }}
        onDelete={handleDeleteSession}
        onRename={handleRenameSession}
      />

      <div className="chat-wrapper">
        <div className="chat-container">
          <div className="chat-header">
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                <h1>
                  {personas.find(p => p.id === currentPersona)?.emoji || "🤖"}{" "}
                  {personas.find(p => p.id === currentPersona)?.name || "Chatbot"}
                </h1>
                <select 
                  value={currentPersona} 
                  onChange={(e) => handlePersonaChange(e.target.value)}
                  className="persona-selector"
                >
                  {personas.map(p => (
                    <option key={p.id} value={p.id}>
                      {p.emoji} {p.name}
                    </option>
                  ))}
                </select>
              </div>
              <small style={{ fontSize: "0.8rem", opacity: 0.8 }}>
                {msgCount} messages exchanged
              </small>
            </div>
            <button onClick={clearChat} className="clear-btn">Clear Chat</button>
          </div>

          <div className="messages-area">
            {messages.map((msg, idx) => (
              <div key={idx} className={`message-bubble ${msg.role}`}>
                <div className="message-content">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
                <div className="message-footer">
                  <span className="time">{msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString('en-IN', {hour:'2-digit', minute:'2-digit', timeZone: 'Asia/Kolkata'}) : ""}</span>
                </div>
              </div>
            ))}
            {loading && <div className="loading">Bot is thinking...</div>}
            <div ref={messagesEndRef} />
          </div>

          <div className="input-area">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder={
                currentPersona === "travel" ? "Ask about a destination..." :
                currentPersona === "career" ? "Ask about your career..." :
                currentPersona === "fitness" ? "Ask about fitness..." :
                "Ask about movies..."
              }
            />
            <button onClick={sendMessage}>Send</button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
