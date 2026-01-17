import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeSanitize from "rehype-sanitize";
import "./ChatPanel.css";
import './index.css';

function ChatPanel({ articleId, summaryId }) {
  const [question, setQuestion] = useState("");
  const [reply, setReply] = useState("");
  const [loading, setLoading] = useState(false);
  const [count, setCount] = useState(0);

  const MAX_FREE = 5;
  const token = localStorage.getItem("access_token");

  const askAI = async () => {
    if (!question.trim() || loading || count >= MAX_FREE) return;

    setLoading(true);
    setReply("");

    try {
      const res = await fetch("http://127.0.0.1:8000/api/chat/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          article_id: articleId,
          summary_id: summaryId,
          question,
        }),
      });

      const data = await res.json();
      setReply(data?.reply || "⚠️ No response from AI.");
      setCount((c) => c + 1);
      setQuestion(""); // ✅ clear input after send
    } catch (err) {
      setReply("⚠️ Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-panel">
      <div className="chat-panel-title">
        <h2>Ask Gemini</h2>
      </div>
      <input
        className="question-inputbox"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            e.preventDefault();
            askAI(); //  send on Enter
          }
        }}
        placeholder="Ask about this article..."
      />

      <button
        type="button"
        className="send-button"
        onClick={askAI}
        disabled={loading || count >= MAX_FREE}
      >
        ➤
      </button>

      {/* Loading state */}
      {loading && (
        <div className="ai-reply">
          Gemini is thinking…
        </div>
      )}

      {/* AI reply (markdown) */}
      {reply && !loading && (
        <div className="ai-reply markdown-body">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeSanitize]}
          >
            {reply}
          </ReactMarkdown>
        </div>
      )}
    </div>
  );
}

export default ChatPanel;
