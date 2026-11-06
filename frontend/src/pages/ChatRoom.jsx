import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import api, { WS_URL } from "../api";
import { useAuth } from "../AuthContext";

export default function ChatRoom() {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [messages, setMessages] = useState([]);
  const [members, setMembers] = useState([]);
  const [text, setText] = useState("");
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const bottomRef = useRef(null);

  const myRole = members.find((m) => m.user_id === user.id)?.role;
  const isAdmin = myRole === "admin";

  const loadMembers = () =>
    api
      .get(`/rooms/${id}/members/`)
      .then((res) => setMembers(res.data))
      .catch(() => navigate("/"));

  // Load history + members
  useEffect(() => {
    api
      .get(`/rooms/${id}/messages/`)
      .then((res) => setMessages(res.data))
      .catch(() => navigate("/"));
    loadMembers();
  }, [id]);

  // WebSocket connection (auto-reconnects if it drops)
  useEffect(() => {
    let closed = false;
    let retryTimer;

    const connect = async () => {
      try {
        // Any authenticated call refreshes an expired token before we connect
        await api.get("/auth/me/");
      } catch {
        return;
      }
      if (closed) return;

      const token = localStorage.getItem("access");
      const ws = new WebSocket(`${WS_URL}/ws/chat/${id}/?token=${token}`);
      wsRef.current = ws;

      ws.onopen = () => setConnected(true);
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "message") {
          setMessages((prev) => [...prev, data]);
        } else if (data.type === "deleted") {
          setMessages((prev) => prev.filter((m) => m.id !== data.id));
        }
      };
      ws.onclose = () => {
        setConnected(false);
        if (!closed) retryTimer = setTimeout(connect, 2000);
      };
    };

    connect();
    return () => {
      closed = true;
      clearTimeout(retryTimer);
      wsRef.current?.close();
    };
  }, [id]);

  // Auto-scroll to newest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = (e) => {
    e.preventDefault();
    const message = text.trim();
    if (!message || wsRef.current?.readyState !== WebSocket.OPEN) return;
    wsRef.current.send(JSON.stringify({ message }));
    setText("");
  };

  const deleteMessage = (msgId) => api.delete(`/messages/${msgId}/`).catch(() => {});

  const toggleRole = async (member) => {
    const role = member.role === "admin" ? "member" : "admin";
    try {
      await api.patch(`/rooms/${id}/members/${member.user_id}/`, { role });
      loadMembers();
    } catch (err) {
      alert(err.response?.data?.detail || "Could not change role.");
    }
  };

  const removeMember = async (member) => {
    try {
      await api.delete(`/rooms/${id}/members/${member.user_id}/`);
      if (member.user_id === user.id) navigate("/");
      else loadMembers();
    } catch (err) {
      alert(err.response?.data?.detail || "Could not remove member.");
    }
  };

  return (
    <div className="chat-layout">
      <section className="chat-main card">
        <div className="chat-head">
          <Link to="/">← Rooms</Link>
          <span className={connected ? "dot on" : "dot off"}>{connected ? "Connected" : "Reconnecting..."}</span>
        </div>

        <div className="messages">
          {messages.map((m) => (
            <div key={m.id} className={m.user_id === user.id ? "msg mine" : "msg"}>
              <div className="msg-meta">
                <strong>{m.username}</strong>
                <span>{new Date(m.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
                {(m.user_id === user.id || isAdmin) && (
                  <button className="link-btn" onClick={() => deleteMessage(m.id)}>
                    delete
                  </button>
                )}
              </div>
              <div>{m.content}</div>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>

        <form className="row" onSubmit={send}>
          <input placeholder="Type a message..." value={text} onChange={(e) => setText(e.target.value)} />
          <button className="btn" disabled={!connected}>
            Send
          </button>
        </form>
      </section>

      <aside className="members card">
        <h4>Members ({members.length})</h4>
        {members.map((m) => (
          <div key={m.id} className="member">
            <div>
              {m.username} <span className={`badge ${m.role}`}>{m.role}</span>
            </div>
            <div className="member-actions">
              {isAdmin && m.user_id !== user.id && (
                <>
                  <button className="link-btn" onClick={() => toggleRole(m)}>
                    {m.role === "admin" ? "make member" : "make admin"}
                  </button>
                  <button className="link-btn danger" onClick={() => removeMember(m)}>
                    remove
                  </button>
                </>
              )}
              {m.user_id === user.id && (
                <button className="link-btn danger" onClick={() => removeMember(m)}>
                  leave
                </button>
              )}
            </div>
          </div>
        ))}
      </aside>
    </div>
  );
}
