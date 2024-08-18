import React from 'react';

const ResponseDisplay = ({ response }) => {
  return (
    <div className="response-container">
      <h2>Summary of Interests:</h2>
      <p>{JSON.stringify(response, null, 2)}</p>
    </div>
  );
};

export default ResponseDisplay;
