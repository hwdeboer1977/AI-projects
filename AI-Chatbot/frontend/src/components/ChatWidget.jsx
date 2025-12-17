import React, { useState, useRef, useEffect } from "react";

function ChatWidget() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hi there! 👋 Welcome to Bolder Outdoor. I'm here to help with any questions about your order, our products, shipping, returns, or anything else. What can I help you with today?",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = { role: "user", content: input.trim() };
    const newMessages = [...messages, userMessage];

    setMessages(newMessages);
    setInput("");
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          messages: newMessages.map(({ role, content }) => ({ role, content })),
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to get response");
      }

      const data = await response.json();

      setMessages([
        ...newMessages,
        { role: "assistant", content: data.message },
      ]);
    } catch (err) {
      console.error("Chat error:", err);
      setError(err.message || "Something went wrong. Please try again.");
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(e);
    }
  };

  const quickActions = [
    "Where's my order?",
    "How do I return an item?",
    "What's your shipping cost?",
    "Recommend a tent for beginners",
  ];

  const handleQuickAction = (action) => {
    setInput(action);
    inputRef.current?.focus();
  };

  return (
    <div className="chat-widget">
      {/* Messages Area */}
      <div className="messages-container">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`message ${
              message.role === "user" ? "message-user" : "message-assistant"
            }`}
          >
            {message.role === "assistant" && (
              <div className="message-avatar">
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 40 40"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path d="M20 4L32 12V28L20 36L8 28V12L20 4Z" fill="#2D5A3D" />
                  <path
                    d="M20 8L28 13V27L20 32L12 27V13L20 8Z"
                    fill="#4A7C59"
                  />
                  <path
                    d="M20 12L24 14.5V25.5L20 28L16 25.5V14.5L20 12Z"
                    fill="#8FBC8F"
                  />
                </svg>
              </div>
            )}
            <div className="message-content">
              <p>{message.content}</p>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="message message-assistant">
            <div className="message-avatar">
              <svg
                width="20"
                height="20"
                viewBox="0 0 40 40"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path d="M20 4L32 12V28L20 36L8 28V12L20 4Z" fill="#2D5A3D" />
                <path d="M20 8L28 13V27L20 32L12 27V13L20 8Z" fill="#4A7C59" />
                <path
                  d="M20 12L24 14.5V25.5L20 28L16 25.5V14.5L20 12Z"
                  fill="#8FBC8F"
                />
              </svg>
            </div>
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="error-message">
            <p>⚠️ {error}</p>
            <button onClick={() => setError(null)}>Dismiss</button>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Actions - only show at start */}
      {messages.length === 1 && (
        <div className="quick-actions">
          {quickActions.map((action, index) => (
            <button
              key={index}
              className="quick-action-btn"
              onClick={() => handleQuickAction(action)}
            >
              {action}
            </button>
          ))}
        </div>
      )}

      {/* Input Area */}
      <form className="input-container" onSubmit={sendMessage}>
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message..."
          disabled={isLoading}
          className="message-input"
        />
        <button
          type="submit"
          disabled={!input.trim() || isLoading}
          className="send-button"
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M22 2L11 13"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M22 2L15 22L11 13L2 9L22 2Z"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
      </form>
    </div>
  );
}

export default ChatWidget;
