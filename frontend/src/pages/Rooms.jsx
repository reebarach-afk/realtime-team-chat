import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";

export default function Rooms() {
  const navigate = useNavigate();
  const [rooms, setRooms] = useState([]);
  const [name, setName] = useState("");
  const [error, setError] = useState("");

  const load = () => api.get("/rooms/").then((res) => setRooms(res.data));

  useEffect(() => {
    load();
  }, []);

  const createRoom = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const { data } = await api.post("/rooms/", { name });
      setName("");
      navigate(`/rooms/${data.id}`);
    } catch (err) {
      setError(err.response?.data?.name?.[0] || "Could not create room.");
    }
  };

  const joinRoom = async (id) => {
    await api.post(`/rooms/${id}/join/`);
    navigate(`/rooms/${id}`);
  };

  return (
    <div>
      <form className="card row" onSubmit={createRoom}>
        <input placeholder="New room name" value={name} onChange={(e) => setName(e.target.value)} required />
        <button className="btn">Create room</button>
      </form>
      {error && <p className="error">{error}</p>}

      <h3>All rooms</h3>
      {rooms.length === 0 && <p className="muted">No rooms yet. Create the first one!</p>}
      {rooms.map((room) => (
        <div key={room.id} className="card row space">
          <div>
            <strong>{room.name}</strong>
            <div className="muted">
              {room.member_count} member{room.member_count !== 1 && "s"}
              {room.my_role && ` • you are ${room.my_role}`}
            </div>
          </div>
          {room.my_role ? (
            <button className="btn small" onClick={() => navigate(`/rooms/${room.id}`)}>
              Open
            </button>
          ) : (
            <button className="btn small secondary" onClick={() => joinRoom(room.id)}>
              Join
            </button>
          )}
        </div>
      ))}
    </div>
  );
}
