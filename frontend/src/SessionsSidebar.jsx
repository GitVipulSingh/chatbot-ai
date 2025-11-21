// frontend/src/SessionsSidebar.jsx
import React, { useEffect, useState } from "react";
import axios from "axios";

export default function SessionsSidebar({ activeSession, currentPersona, onSwitch, onNewSession, onDelete, onRename }) {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);
  
  const personaEmojis = {
    travel: "✈️",
    career: "💼",
    fitness: "💪",
    movie: "🎬"
  };

  const fetchSessions = async () => {
    setLoading(true);
    try {
      const res = await axios.get("http://127.0.0.1:8000/api/sessions");
      setSessions(res.data.sessions || []);
    } catch (e) {
      console.error("Failed to fetch sessions", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
    
    // Listen for custom refresh event
    const handleRefresh = () => fetchSessions();
    window.addEventListener('refreshSessions', handleRefresh);
    
    // refresh every 20s to show new sessions if needed
    const id = setInterval(fetchSessions, 20000);
    
    return () => {
      clearInterval(id);
      window.removeEventListener('refreshSessions', handleRefresh);
    };
  }, []);

  return (
    <aside className="sessions-sidebar">
      <div className="sidebar-header">
        <h3>Chats</h3>
        <button onClick={async () => { 
          const newId = await onNewSession(); 
          fetchSessions();
        }} className="new-chat-btn">+ New</button>
      </div>

      <div className="sessions-list">
        {loading && <div style={{padding: 12, color: '#667781'}}>Loading…</div>}
        {!loading && sessions.length === 0 && <div style={{padding: 12, color: '#667781'}}>No chats yet</div>}
        {sessions.map((s) => {
          const title = s.title || "New chat";
          const last = s.last_message_time ? new Date(s.last_message_time).toLocaleString([], {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
          }) : "";
          const isActive = activeSession === s.session_id;
          const personaEmoji = personaEmojis[s.persona] || "🤖";
          return (
            <div key={s.session_id} className={`session-item ${isActive ? "active" : ""}`}>
              <div onClick={() => onSwitch(s.session_id, s.persona)} className="session-main">
                <div className="session-title">
                  <span style={{ marginRight: "6px" }}>{personaEmoji}</span>
                  {title}
                </div>
                <div className="session-meta">{last}</div>
              </div>
              <div className="session-actions">
                <button 
                  title="Rename"
                  onClick={async (e)=>{ 
                    e.stopPropagation(); 
                    const newTitle = prompt("New title?", title); 
                    if(newTitle && newTitle !== title) { 
                      await onRename(s.session_id, newTitle); 
                      fetchSessions(); 
                    } 
                  }}>✎</button>
                <button 
                  title="Delete"
                  onClick={async (e)=>{ 
                    e.stopPropagation(); 
                    if(confirm("Delete this chat?")){ 
                      await onDelete(s.session_id); 
                      fetchSessions(); 
                      if(activeSession===s.session_id) onSwitch(null); 
                    }
                  }}>🗑</button>
              </div>
            </div>
          );
        })}
      </div>
    </aside>
  );
}
