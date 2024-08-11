import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [response, setResponse] = useState(null);

  const handleGetData = async () => {
    try {
      const res = await axios.get('http://127.0.0.1:8000/get_data');
      setResponse(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleSummarize = async () => {
    try {
      const res = await axios.get('http://127.0.0.1:8000/summarize');
      setResponse(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="app-container">
      <h1 className="app-title">YouTube Data Collector</h1>
      <div className="button-container">
        <button className="custom-button" onClick={handleGetData}>
          Get YouTube Data
        </button>
        <button className="custom-button" onClick={handleSummarize}>
          Summarize
        </button>
      </div>
      {response && (
        <div className="response-container">
          <h2>Response:</h2>
          <p>{response}</p>
        </div>
      )}
    </div>
  );
}

export default App;
