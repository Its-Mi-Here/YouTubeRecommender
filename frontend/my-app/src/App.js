import React, { useState } from 'react';
import axios from 'axios';
import { Pie } from 'react-chartjs-2';
import './App.css';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend);

function App() {
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(''); 
  const [chartData, setChartData] = useState(null); // New state for chart data

  const handleGetData = async () => {
    setLoading(true);
    setMessage(''); 
    try {
      const res = await axios.get('http://127.0.0.1:8000/get_data');
      setResponse(res.data);
      setMessage(res.data.message);
      // setMessage('Data successfully read!'); 
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSummarize = async () => {
    setLoading(true);
    setMessage(''); 
    try {
      const res = await axios.get('http://127.0.0.1:8000/summarize');
      setResponse(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleVisualize = async () => {
    setLoading(true);
    setMessage(''); 
    try {
      const res = await axios.get('http://127.0.0.1:8000/visualize');
      const data = res.data;

      // Get the top 10 categories
      const sortedCategories = Object.entries(data)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 10);

      const labels = sortedCategories.map(([category]) => category);
      const values = sortedCategories.map(([, value]) => value);
      const total = values.reduce((acc, value) => acc + value, 0);
      const percentages = values.map(value => (value / total) * 100);

      // Prepare chart data
      setChartData({
        labels,
        datasets: [
          {
            label: 'Top 10 Categories',
            data: percentages,
            backgroundColor: [
              '#FF6384',
              '#36A2EB',
              '#FFCE56',
              '#FF9F40',
              '#FF6384',
              '#4BC0C0',
              '#9966FF',
              '#FFCD56',
              '#C9CBCF',
              '#36A2EB',
            ],
          },
        ],
      });

      setResponse(data);
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
        <button className="custom-button" onClick={handleVisualize} disabled={loading}>
          Visualize
        </button>
      </div>
      {loading && (
        <div className="loading-bar-container">
          <div className="loading-bar"></div>
        </div>
      )}
      {message && ( 
        <div className="message-container">
          <p>{message}</p>
        </div>
      )}
      {response && !chartData && (
        <div className="response-container">
          <h2>Summary of Interests:</h2>
          <p>{JSON.stringify(response, null, 2)}</p>
        </div>
      )}
      {chartData && (
        <div className="chart-container">
          <h2>Top 10 Categories</h2>
          <Pie data={chartData} />
        </div>
      )}
    </div>
  );
}

export default App;
