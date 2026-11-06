import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
export const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000";

const api = axios.create({ baseURL: `${API_URL}/api` });

// Attach the access token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// If the access token expired, refresh it once and retry the request
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    const refresh = localStorage.getItem("refresh");
    const isAuthCall = original?.url?.startsWith("/auth/");

    if (error.response?.status === 401 && refresh && !original._retry && !isAuthCall) {
      original._retry = true;
      try {
        const { data } = await axios.post(`${API_URL}/api/auth/refresh/`, { refresh });
        localStorage.setItem("access", data.access);
        original.headers.Authorization = `Bearer ${data.access}`;
        return api(original);
      } catch {
        localStorage.clear();
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default api;
