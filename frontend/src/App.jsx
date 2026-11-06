import { Link, Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./AuthContext";
import ChatRoom from "./pages/ChatRoom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Rooms from "./pages/Rooms";

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <p className="center">Loading...</p>;
  return user ? children : <Navigate to="/login" replace />;
}

export default function App() {
  const { user, logout } = useAuth();

  return (
    <>
      <header className="navbar">
        <Link to="/" className="brand">
          Team Chat
        </Link>
        {user && (
          <div className="nav-right">
            <span>{user.username}</span>
            <button className="btn small secondary" onClick={logout}>
              Logout
            </button>
          </div>
        )}
      </header>

      <main className="container">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Rooms />
              </ProtectedRoute>
            }
          />
          <Route
            path="/rooms/:id"
            element={
              <ProtectedRoute>
                <ChatRoom />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </>
  );
}
