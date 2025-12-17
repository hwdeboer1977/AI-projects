import React from "react";
import ChatWidget from "./components/ChatWidget";

function App() {
  return (
    <div className="app">
      {/* Hero Section */}
      <header className="hero">
        <div className="hero-content">
          <div className="logo">
            <svg
              width="40"
              height="40"
              viewBox="0 0 40 40"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M20 4L32 12V28L20 36L8 28V12L20 4Z"
                fill="#2D5A3D"
                stroke="#1a3d28"
                strokeWidth="2"
              />
              <path d="M20 8L28 13V27L20 32L12 27V13L20 8Z" fill="#4A7C59" />
              <path
                d="M20 12L24 14.5V25.5L20 28L16 25.5V14.5L20 12Z"
                fill="#8FBC8F"
              />
            </svg>
            <span className="logo-text">Bolder Outdoor</span>
          </div>
          <h1>How can we help you today?</h1>
          <p>Get instant answers about orders, products, shipping, and more.</p>
        </div>
        <div className="hero-decoration">
          <div className="mountain mountain-1"></div>
          <div className="mountain mountain-2"></div>
          <div className="mountain mountain-3"></div>
        </div>
      </header>

      {/* Chat Widget */}
      <main className="chat-container">
        <ChatWidget />
      </main>

      {/* Footer */}
      <footer className="footer">
        <p>
          Need more help? Email us at{" "}
          <a href="mailto:support@bolderoutdoor.nl">support@bolderoutdoor.nl</a>{" "}
          or call <a href="tel:+31201234567">+31 20 123 4567</a>
        </p>
        <p className="footer-hours">Mon-Fri 9:00-17:30 CET</p>
      </footer>
    </div>
  );
}

export default App;
