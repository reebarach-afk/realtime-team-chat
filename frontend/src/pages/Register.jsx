import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: "", email: "", password: "" });
  const [error, setError] = useState("");

  const update = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await register(form.username, form.email, form.password);
      navigate("/");
    } catch (err) {
      const data = err.response?.data;
      setError(data ? Object.values(data).flat().join(" ") : "Registration failed.");
    }
  };

  return (
    <form className="card auth-card" onSubmit={handleSubmit}>
      <h2>Register</h2>
      {error && <p className="error">{error}</p>}
      <input name="username" placeholder="Username" value={form.username} onChange={update} required />
      <input name="email" type="email" placeholder="Email" value={form.email} onChange={update} />
      <input name="password" type="password" placeholder="Password (min 6 characters)" value={form.password} onChange={update} required />
      <button className="btn">Create account</button>
      <p>
        Already registered? <Link to="/login">Login</Link>
      </p>
    </form>
  );
}
