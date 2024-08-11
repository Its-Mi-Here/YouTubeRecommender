import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [response, setResponse] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const item = { name, description };
    try {
      const res = await axios.get('http://127.0.0.1:8000/summarize');
      setResponse(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleGetData = async (e) => {
    e.preventDefault();
    const item = { name, description };
    try {
      const res = await axios.get('http://127.0.0.1:8000/get_data');
      setResponse(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div>
      <h1>Collect YouTube Data</h1>
      <button type="submit" onClick={handleGetData}>Get YouTube data</button>
      <button type="submit" onClick={handleSubmit}>Summarize</button>

      {/* <form onSubmit={handleSubmit}>
        <button type="submit">Summarize</button>
      </form> */}
      {response && (
        <div>
          <h2>Response:</h2>
          <p>{response}</p>
        </div>
      )}
    </div>
  );
}

export default App;
