// frontend/src/SessionsSidebar.jsx
import React, { useEffect, useState } from "react";
import axios from "axios";

export default function SessionsSidebar({ activeSession, onSwitch, onNewSession, onDelete, onRename }) {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);

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
    // refresh every 20s to show new sessions if needed
    const id = setInterval(fetchSessions, 20000);
    return () => clearInterval(id);
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
        {loading && <div style={{padding: 12}}>Loading…</div>}
        {!loading && sessions.length === 0 && <div style={{padding: 12}}>No chats yet</div>}
        {sessions.map((s) => {
          const title = s.snippet ? s.snippet.slice(0, 60) : "New chat";
          const last = s.last_message_time ? new Date(s.last_message_time).toLocaleString() : "";
          const isActive = activeSession === s.session_id;
          return (
            <div key={s.session_id} className={`session-item ${isActive ? "active" : ""}`}>
              <div onClick={() => onSwitch(s.session_id)} className="session-main">
                <div className="session-title">{title}</div>
                <div className="session-meta">{last}</div>
              </div>
              <div className="session-actions">
                <button onClick={async (e)=>{ e.stopPropagation(); const newTitle = prompt("New title?"); if(newTitle) { await onRename(s.session_id, newTitle); fetchSessions(); } }}>✎</button>
                <button onClick={async (e)=>{ e.stopPropagation(); if(confirm("Delete this chat?")){ await onDelete(s.session_id); fetchSessions(); if(activeSession===s.session_id) onSwitch(null); }}}>🗑</button>
              </div>
            </div>
          );
        })}
      </div>
    </aside>
  );
}
