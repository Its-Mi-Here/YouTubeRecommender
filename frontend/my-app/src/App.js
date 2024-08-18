import React, { useState } from 'react';
import axios from 'axios';
import ButtonContainer from './components/ButtonContainer';
import LoadingBar from './components/LoadingBar';
import Message from './components/Message';
import ResponseDisplay from './components/ResponseDisplay';
import ChartDisplay from './components/ChartDisplay';
import './App.css';

function App() {
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(''); 
  const [chartData, setChartData] = useState(null);

  const handleGetData = async () => {
    setLoading(true);
    setMessage(''); 
    try {
      const res = await axios.get('http://127.0.0.1:8000/get_data');
      setResponse(res.data);
      setMessage('Data successfully read!'); 
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

      const sortedCategories = Object.entries(data)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 10);

      const labels = sortedCategories.map(([category]) => category);
      const values = sortedCategories.map(([, value]) => value);
      const total = values.reduce((acc, value) => acc + value, 0);
      const percentages = values.map(value => (value / total) * 100);

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
      <ButtonContainer 
        loading={loading}
        handleGetData={handleGetData}
        handleSummarize={handleSummarize}
        handleVisualize={handleVisualize}
      />
      {loading && <LoadingBar />}
      {message && <Message message={message} />}
      {response && !chartData && <ResponseDisplay response={response} />}
      {chartData && <ChartDisplay chartData={chartData} />}
    </div>
  );
}

export default App;
