import React from 'react';
import { Pie } from 'react-chartjs-2';

const ChartDisplay = ({ chartData }) => {
  return (
    <div className="chart-container">
      <h2>Top 10 Categories</h2>
      <Pie data={chartData} />
    </div>
  );
};

export default ChartDisplay;
