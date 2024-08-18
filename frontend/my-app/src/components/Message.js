import React from 'react';

const Message = ({ message }) => {
  return (
    <div className="message-container">
      <p>{message}</p>
    </div>
  );
};

export default Message;
