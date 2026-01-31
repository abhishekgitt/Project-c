import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion as Motion, AnimatePresence } from "framer-motion";
import { TrendingUp, Globe, BarChart3, Clock } from "lucide-react";
import ProfileMenu from "./ProfileMenu";
import "./Home.css";

function Home() {
  const [summaries, setSummaries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);


  const navigate = useNavigate();
  const token = localStorage.getItem("access_token");

  useEffect(() => {
    const headers = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    fetch("http://127.0.0.1:8000/api/summaries/", {
      headers: headers,
    })
      .then((res) => {
        if (res.status === 401) {
          // If unauthorized, we just don't show personalized stuff or maybe show public summaries if available.
          // For now, assuming API returns public summaries or empty list if not logged in, 
          // OR if the API strictly requires auth, we might need to handle that. 
          // Based on requirements, "land directly on News Page".
          // If the backend requires auth for summaries, we might need to adjust backend or show a "Login to view" state.
          // However, for this step, we just prevent auto-redirect.
          // If unauthorized, clear token and show public view (Login button will appear)
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          return res.json().catch(() => null);
        }
        return res.json();
      })
      .then((data) => {
        // If data is null (from catch above) or error
        if (!data || data.detail) {
          // handled quietly or show empty state
          setLoading(false);
          return;
        }

        if (data?.needs_onboarding) {
          // Backend no longer sends this, but if it did, we ignore it now. 
          // Or just remove this block entirely.
        }

        setSummaries(data || []);
        setLoading(false);
      })
      .catch(() => {
        setError("Failed to load summaries");
        setLoading(false);
      });
  }, [navigate, token]);



  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2
      }
    }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        type: "spring",
        stiffness: 100,
        damping: 15
      }
    }
  };

  if (loading) return (
    <div className="status-container">
      <Motion.div
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
        className="loader"
      />
      <p>Analyzing job market trends...</p>
    </div>
  );

  if (error) return <div className="status-container"><p className="error">{error}</p></div>;

  return (
    <div className="home-page">
      <Motion.header
        initial={{ y: -50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ type: "spring", stiffness: 80, damping: 20 }}
        className="home-header"
      >
        <div className="header-left">
          <div className="header-badge">
            <Globe size={14} className="icon-pulse" />
            <span>Real-time Intelligence</span>
          </div>
          <h1>AI Job Market <br /><span className="gradient-text">Trend Hub</span></h1>
          <p>Advanced AI-driven analysis of global employment and skill shifts.</p>
        </div>

        <div className="header-right" style={{ position: 'absolute', top: '20px', right: '20px', zIndex: 10 }}>
          <ProfileMenu />
        </div>
      </Motion.header>

      <Motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="card-grid"
      >
        <AnimatePresence>
          {summaries.map((item, index) => (
            <Motion.div
              layout
              key={item.id}
              variants={itemVariants}
              whileHover={{
                scale: 1.02,
                y: -5,
                transition: { type: "spring", stiffness: 400, damping: 10 }
              }}
              whileTap={{ scale: 0.98 }}
              className={`blog-card ${index === 0 ? 'featured-card' : ''}`}
              onClick={() => navigate(`/summary/${item.id}`)}
            >
              <div className="card-image-wrap">
                <img
                  src={item.hero_image || "/static/news/llama-logo.png"}
                  alt="article"
                  loading="lazy"
                  onError={(e) => {
                    e.target.onerror = null;
                    e.target.src = "/static/news/default-job.png"; // Fallback if llama-logo fails too? Or just keep it.
                  }}
                  className={!item.hero_image ? "default-logo" : ""}
                />
                <div className="image-overlay" />
              </div>

              <div className="card-content">
                <div className="card-meta">
                  <span className="tag-pill">{item.article.source}</span>
                  <span className="time-pill"><Clock size={12} /> 5m read</span>
                </div>
                <h3>{item.article.title}</h3>
                <p className="description">
                  {item.short_preview?.slice(0, 120)}...
                </p>

                <div className="card-footer">
                  <div className="footer-stat">
                    <TrendingUp size={14} />
                    <span>High Impact</span>
                  </div>
                  <Motion.div
                    className="arrow-link"
                    whileHover={{ x: 5 }}
                  >
                    Read Insight →
                  </Motion.div>
                </div>
              </div>
            </Motion.div>
          ))}
        </AnimatePresence>
      </Motion.div>
    </div>
  );
}

export default Home;


