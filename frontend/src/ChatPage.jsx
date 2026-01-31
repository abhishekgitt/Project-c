import { useParams, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { motion as Motion } from "framer-motion";
import { ArrowLeft, Sparkles } from "lucide-react";
import ChatPanel from "./ChatPanel";
import "./ChatPage.css";

function ChatPage() {
    const { id } = useParams();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const navigate = useNavigate();
    const token = localStorage.getItem("access_token");

    useEffect(() => {
        fetch("http://127.0.0.1:8000/api/summaries/", {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        })
            .then((res) => {
                if (res.status === 401) {
                    localStorage.clear();
                    navigate("/login");
                    return;
                }
                return res.json();
            })
            .then((all) => {
                const found = all?.find((item) => item.id === Number(id));
                if (!found) {
                    setError("Article not found.");
                }
                setData(found);
                setLoading(false);
            })
            .catch(() => {
                setError("Failed to load session context.");
                setLoading(false);
            });
    }, [id, navigate, token]);

    if (loading) return (
        <div className="status-container">
            <div className="loader" />
            <p>Initializing intelligence channel...</p>
        </div>
    );

    if (error || !data) return (
        <div className="status-container">
            <p className="error">{error || "Context missing."}</p>
            <button className="back-btn" onClick={() => navigate("/")}>
                <ArrowLeft size={18} /> Return Home
            </button>
        </div>
    );

    return (
        <Motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="chat-page"
        >
            <nav className="chat-page-nav">
                <button className="back-btn" onClick={() => navigate(`/summary/${id}`)}>
                    <ArrowLeft size={18} />
                    Back to Analysis
                </button>
                <div className="header-badge">
                    <Sparkles size={14} className="icon-pulse" />
                    <span>AI Interaction Mode</span>
                </div>
            </nav>

            <Motion.div
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.2 }}
                className="chat-page-content"
            >
                <div style={{ marginBottom: '20px' }}>
                    <h2>{data.article.title}</h2>
                    <p style={{ color: 'var(--text-secondary)' }}>Interactive intelligence session</p>
                </div>

                <ChatPanel
                    articleId={data.article.id}
                    summaryId={data.id}
                />
            </Motion.div>
        </Motion.div>
    );
}

export default ChatPage;
