import React from 'react';

const ButtonContainer = ({ loading, handleGetData, handleSummarize, handleVisualize }) => {
  return (
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
  );
};

export default ButtonContainer;
