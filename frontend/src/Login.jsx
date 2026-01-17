import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import "./Login.css";


function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);

  const navigate = useNavigate();

  const login = async () => {
    setError(null);

    const res = await fetch("http://127.0.0.1:8000/api/token/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });

    if (!res.ok) {
      setError("Invalid credentials");
      return;
    }

    const data = await res.json();
    localStorage.setItem("access_token", data.access);
    localStorage.setItem("refresh_token", data.refresh);

    navigate("/");
  };

  return (
    <div className="login-page">
      <div className="login-card">
        
        {/* LEFT SIDE */}
        <div className="login-left">
          <h2>Login</h2>

          {error && <p className="error">{error}</p>}

          <input
            className="password-inputbox"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />

          <input
            className="username-inputbox"
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          <button onClick={login}>Login</button>
          <p>
            Don’t have an account?{" "}
              <Link to="/signup">Sign up</Link>
          </p>
        </div>

        {/* RIGHT SIDE */}
        <div className="login-right">
          {/* <img src={illustration} alt="Illustration" /> */}
          <h3>Global News Analyzer AI</h3>
          <p>Personalized News Feeds From Different Languages To Your Language With Easy and Friendly AI Summaries </p>
        </div>

      </div>
    </div>
  );
}

export default Login;
