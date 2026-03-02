import React, { useState } from 'react';
import './TextBox.css';

import { API_BASE_URL } from "./services/apiConfig";

const API_ENDPOINT = `${API_BASE_URL}/data`;

type ServerResponse = {
  received?: string;
  status?: string;
  message?: string;
};

const TextBox: React.FC = () => {
  const [text, setText] = useState<string>('');
  const [submissionStatus, setSubmissionStatus] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const handleChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(event.target.value);
  };

  const handleSubmit = async (): Promise<void> => {
    if (!text) {
      setSubmissionStatus(' Textbox is empty! Cannot send.');
      return;
    }

    setIsLoading(true);
    setSubmissionStatus(' Sending data...');

    try {
      const response = await fetch(API_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ userText: text }),
      });

      if (response.ok) {
        const result: ServerResponse = await response.json();
        const serverMessage =
          result.received || result.status || 'Success, but no message';

        setSubmissionStatus(` Server Confirmation: ${serverMessage}`);
      } else {
        const errorData: ServerResponse = await response.json();
        setSubmissionStatus(
          ` Error sending data: ${response.status} - ${
            errorData.message || 'Server error'
          }`
        );
      }
    } catch (error) {
      setSubmissionStatus(' Network error: Could not connect to the endpoint.');
      console.error('Fetch error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="textbox-container">
      <h1>Prova Example</h1>

      <textarea
        placeholder="Type the message to send to the server..."
        value={text}
        onChange={handleChange}
        rows={30}
        cols={60}
        className="text-input"
      />

      <button
        onClick={handleSubmit}
        className="submit-button"
        disabled={isLoading}
      >
        {isLoading ? 'Sending...' : 'Send Text to Server'}
      </button>

      <p style={{ marginTop: '10px', fontWeight: 'bold' }}>
        {submissionStatus}
      </p>

      <hr style={{ marginTop: '20px' }} />
    </div>
  );
};

export default TextBox;

