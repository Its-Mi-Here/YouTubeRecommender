import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleGetData = async () => {
    setLoading(true);
    try {
      const res = await axios.get('http://127.0.0.1:8000/get_data');
      setResponse(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSummarize = async () => {
    setLoading(true);
    try {
      const res = await axios.get('http://127.0.0.1:8000/summarize');
      setResponse(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <h1 className="app-title">YouTube Data Collector</h1>
      <div className="button-container">
        <button className="custom-button" onClick={handleGetData} disabled={loading}>
          Get YouTube Data
        </button>
        <button className="custom-button" onClick={handleSummarize} disabled={loading}>
          Summarize
        </button>
      </div>
      {loading && (
        <div className="loading-bar-container">
          <div className="loading-bar"></div>
        </div>
      )}
      {response && (
        <div className="response-container">
          <h2>Summary of Interests:</h2>
          <p>{response}</p>
        </div>
      )}
    </div>
  );
}

export default App;
