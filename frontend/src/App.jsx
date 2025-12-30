import { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [summaries, setSummaries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // useEffect( ARGUMENT_1 , ARGUMENT_2 );
  useEffect(() => {
    fetch("http://127.0.0.1:8000/api/summaries/")
      .then((res) => {
        if (!res.ok) {
          throw new Error("Failed to fetch data");
        } 
      return res.json();
      })
      
      .then((data) => {
        setSummaries(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });

  }, []);

  if (loading) return <h2>Loading...</h2>;
  if (error) return <h2>Error: {error}</h2>;

  return (
    <div className="container">
      <h1 className="title">Global Economic News - AI</h1>

      {summaries.map((item) => (
        <div key={item.id} className="card">
          <h3 className="card-title">{item.article.title}</h3>
          <p><strong>Source:</strong> {item.article.source}</p>
          <p>{item.ai_summary}</p>
        </div>
      ))}
    </div>
  );
}

export default App;
