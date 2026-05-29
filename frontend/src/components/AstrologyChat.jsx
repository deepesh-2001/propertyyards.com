import React, { useState, useEffect } from 'react';
import axios from 'axios';

const AstrologyChat = ({ userId }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [birthChart, setBirthChart] = useState(null);
  const [showBirthChartForm, setShowBirthChartForm] = useState(false);
  const [dailyPrediction, setDailyPrediction] = useState(null);
  const [weeklyPredictions, setWeeklyPredictions] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('general');

  useEffect(() => {
    // Initialize with welcome message
    setMessages([
      {
        id: 'welcome',
        type: 'bot',
        text: "🌟 Welcome to PropertyYards Astrology! I'm your AI astrologer. I can provide insights on career, relationships, health, finance, and more based on Vedic astrology. To get personalized predictions, please create your birth chart first.",
        timestamp: new Date()
      }
    ]);
    
    // Load daily prediction
    loadDailyPrediction();
  }, []);

  const loadDailyPrediction = async () => {
    try {
      const response = await axios.get('/api/astrology/daily-prediction');
      setDailyPrediction(response.data.data);
    } catch (error) {
      console.error('Failed to load daily prediction:', error);
    }
  };

  const loadWeeklyPredictions = async () => {
    try {
      const response = await axios.get('/api/astrology/weekly-predictions');
      setWeeklyPredictions(response.data.data);
    } catch (error) {
      console.error('Failed to load weekly predictions:', error);
    }
  };

  const createBirthChart = async (birthData) => {
    try {
      const response = await axios.post('/api/astrology/birth-chart', birthData);
      setBirthChart(response.data.data);
      setShowBirthChartForm(false);
      
      // Add success message
      setMessages(prev => [...prev, {
        id: `chart_${Date.now()}`,
        type: 'bot',
        text: `✅ Birth chart created successfully! Your Sun sign is ${response.data.data.sun_sign}, Moon sign is ${response.data.data.moon_sign}, and Ascendant is ${response.data.data.ascendant}. How can I help you today?`,
        timestamp: new Date()
      }]);
      
      // Load insights
      loadInsights();
    } catch (error) {
      console.error('Failed to create birth chart:', error);
      setMessages(prev => [...prev, {
        id: `error_${Date.now()}`,
        type: 'bot',
        text: "❌ Sorry, I couldn't create your birth chart. Please check your details and try again.",
        timestamp: new Date()
      }]);
    }
  };

  const loadInsights = async () => {
    try {
      const response = await axios.post('/api/astrology/insights', {
        categories: ['career', 'relationship', 'health', 'finance']
      });
      
      if (response.data.data.insights.length > 0) {
        const insights = response.data.data.insights;
        setMessages(prev => [...prev, {
          id: `insights_${Date.now()}`,
          type: 'bot',
          text: `🔮 Here are your key insights:\n\n${insights.map(insight => 
            `**${insight.title}**: ${insight.prediction}\n*Confidence: ${Math.round(insight.confidence * 100)}%*\n${insight.recommendations.length > 0 ? `\n💡 ${insight.recommendations[0]}` : ''}`
          ).join('\n\n')}`,
          timestamp: new Date()
        }]);
      }
    } catch (error) {
      console.error('Failed to load insights:', error);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = {
      id: `user_${Date.now()}`,
      type: 'user',
      text: inputMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await axios.post('/api/astrology/chat', {
        message: inputMessage,
        context: selectedCategory
      });

      const botMessage = {
        id: `bot_${Date.now()}`,
        type: 'bot',
        text: response.data.data.message,
        category: response.data.data.category,
        confidence: response.data.data.confidence,
        followUpQuestions: response.data.data.follow_up_questions,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Failed to send message:', error);
      setMessages(prev => [...prev, {
        id: `error_${Date.now()}`,
        type: 'bot',
        text: "Sorry, I'm having trouble connecting. Please try again in a moment.",
        timestamp: new Date()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const getCategoryColor = (category) => {
    const colors = {
      career: '#3b82f6',
      relationship: '#ec4899',
      health: '#10b981',
      finance: '#f59e0b',
      general: '#6b7280'
    };
    return colors[category] || colors.general;
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="astrology-chat">
      <div className="chat-header">
        <h3>🌟 Astrology AI Assistant</h3>
        <div className="header-actions">
          <button
            onClick={() => setShowBirthChartForm(!showBirthChartForm)}
            className="btn btn-primary"
          >
            {birthChart ? 'Update Birth Chart' : 'Create Birth Chart'}
          </button>
          <button
            onClick={loadWeeklyPredictions}
            className="btn btn-secondary"
          >
            Weekly Predictions
          </button>
        </div>
      </div>

      <div className="chat-content">
        {/* Birth Chart Form */}
        {showBirthChartForm && (
          <div className="birth-chart-form">
            <h4>Create Your Birth Chart</h4>
            <form onSubmit={(e) => {
              e.preventDefault();
              const formData = new FormData(e.target);
              createBirthChart({
                name: formData.get('name'),
                birth_date: formData.get('birth_date'),
                birth_time: formData.get('birth_time'),
                birth_place: formData.get('birth_place'),
                latitude: parseFloat(formData.get('latitude')) || 28.6139,
                longitude: parseFloat(formData.get('longitude')) || 77.2090,
                timezone: formData.get('timezone')
              });
            }}>
              <div className="form-row">
                <label>
                  Name:
                  <input type="text" name="name" required />
                </label>
                <label>
                  Birth Date:
                  <input type="date" name="birth_date" required />
                </label>
              </div>
              <div className="form-row">
                <label>
                  Birth Time:
                  <input type="time" name="birth_time" defaultValue="12:00" />
                </label>
                <label>
                  Birth Place:
                  <input type="text" name="birth_place" required />
                </label>
              </div>
              <div className="form-row">
                <label>
                  Latitude:
                  <input type="number" name="latitude" step="0.0001" defaultValue="28.6139" />
                </label>
                <label>
                  Longitude:
                  <input type="number" name="longitude" step="0.0001" defaultValue="77.2090" />
                </label>
              </div>
              <div className="form-row">
                <label>
                  Timezone:
                  <select name="timezone" defaultValue="Asia/Kolkata">
                    <option value="Asia/Kolkata">Asia/Kolkata</option>
                    <option value="UTC">UTC</option>
                    <option value="America/New_York">America/New_York</option>
                    <option value="Europe/London">Europe/London</option>
                  </select>
                </label>
              </div>
              <button type="submit" className="btn btn-success">Create Chart</button>
            </form>
          </div>
        )}

        {/* Daily Prediction Card */}
        {dailyPrediction && (
          <div className="daily-prediction-card">
            <h4>🌅 Daily Prediction - {dailyPrediction.day}</h4>
            <div className="prediction-content">
              <p><strong>Overall:</strong> {dailyPrediction.overall_rating}</p>
              <p><strong>Lucky Color:</strong> <span className="color-badge" style={{ backgroundColor: dailyPrediction.lucky_color.toLowerCase() }}>{dailyPrediction.lucky_color}</span></p>
              <p><strong>Lucky Number:</strong> {dailyPrediction.lucky_number}</p>
              <p><strong>Mantra:</strong> {dailyPrediction.mantra}</p>
            </div>
          </div>
        )}

        {/* Weekly Predictions */}
        {weeklyPredictions && (
          <div className="weekly-predictions-card">
            <h4>📅 Weekly Predictions</h4>
            <p>{weeklyPredictions.week_summary}</p>
            <div className="weekly-grid">
              {weeklyPredictions.predictions.map((pred, index) => (
                <div key={index} className="day-prediction">
                  <strong>{pred.day}:</strong> {pred.overall_rating}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Birth Chart Summary */}
        {birthChart && (
          <div className="birth-chart-summary">
            <h4>🪐 Your Birth Chart</h4>
            <div className="chart-summary">
              <div className="chart-info">
                <span><strong>Sun:</strong> {birthChart.sun_sign}</span>
                <span><strong>Moon:</strong> {birthChart.moon_sign}</span>
                <span><strong>Ascendant:</strong> {birthChart.ascendant}</span>
                <span><strong>Dasha:</strong> {birthChart.dasha_period}</span>
              </div>
            </div>
          </div>
        )}

        {/* Messages */}
        <div className="messages-container">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`message ${message.type}`}
              style={message.type === 'bot' && message.category ? { borderLeftColor: getCategoryColor(message.category) } : {}}
            >
              <div className="message-content">
                <div className="message-text">{message.text}</div>
                {message.followUpQuestions && (
                  <div className="follow-up-questions">
                    <p>You might also ask:</p>
                    {message.followUpQuestions.map((question, index) => (
                      <button
                        key={index}
                        onClick={() => setInputMessage(question)}
                        className="follow-up-btn"
                      >
                        {question}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              <div className="message-time">{formatTime(message.timestamp)}</div>
            </div>
          ))}
          
          {isLoading && (
            <div className="message bot">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="chat-input">
          <div className="input-container">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about your career, relationships, health, or any life guidance..."
              rows={2}
              className="message-input"
            />
            <button
              onClick={sendMessage}
              disabled={!inputMessage.trim() || isLoading}
              className="send-button"
            >
              {isLoading ? '...' : 'Send'}
            </button>
          </div>
        </div>
      </div>

      <style jsx>{`
        .astrology-chat {
          display: flex;
          flex-direction: column;
          height: 600px;
          border: 1px solid #e5e7eb;
          border-radius: 12px;
          overflow: hidden;
          font-family: Arial, sans-serif;
        }

        .chat-header {
          padding: 16px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .chat-header h3 {
          margin: 0;
          font-size: 18px;
        }

        .header-actions {
          display: flex;
          gap: 8px;
        }

        .btn {
          padding: 6px 12px;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          font-size: 12px;
          transition: all 0.2s;
        }

        .btn-primary { background: #3b82f6; color: white; }
        .btn-secondary { background: #6b7280; color: white; }
        .btn-success { background: #10b981; color: white; }

        .btn:hover {
          transform: translateY(-1px);
          box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }

        .chat-content {
          flex: 1;
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }

        .birth-chart-form {
          padding: 16px;
          background: #f8fafc;
          border-bottom: 1px solid #e5e7eb;
        }

        .birth-chart-form h4 {
          margin: 0 0 12px 0;
          color: #374151;
        }

        .form-row {
          display: flex;
          gap: 12px;
          margin-bottom: 12px;
        }

        .form-row label {
          flex: 1;
          display: flex;
          flex-direction: column;
          font-size: 14px;
          color: #374151;
        }

        .form-row input, .form-row select {
          margin-top: 4px;
          padding: 8px;
          border: 1px solid #d1d5db;
          border-radius: 4px;
          font-size: 14px;
        }

        .daily-prediction-card, .weekly-predictions-card {
          padding: 12px 16px;
          background: #fef3c7;
          border-bottom: 1px solid #f59e0b;
        }

        .daily-prediction-card h4, .weekly-predictions-card h4 {
          margin: 0 0 8px 0;
          font-size: 14px;
          color: #92400e;
        }

        .prediction-content p {
          margin: 4px 0;
          font-size: 13px;
          color: #78350f;
        }

        .color-badge {
          display: inline-block;
          padding: 2px 8px;
          border-radius: 12px;
          color: white;
          font-size: 11px;
        }

        .weekly-grid {
          display: grid;
          grid-template-columns: repeat(7, 1fr);
          gap: 4px;
          margin-top: 8px;
        }

        .day-prediction {
          font-size: 11px;
          text-align: center;
          color: #78350f;
        }

        .birth-chart-summary {
          padding: 12px 16px;
          background: #ede9fe;
          border-bottom: 1px solid #6366f1;
        }

        .birth-chart-summary h4 {
          margin: 0 0 8px 0;
          font-size: 14px;
          color: #4338ca;
        }

        .chart-summary {
          display: flex;
          flex-wrap: wrap;
          gap: 12px;
        }

        .chart-info span {
          font-size: 13px;
          color: #4c1d95;
        }

        .messages-container {
          flex: 1;
          overflow-y: auto;
          padding: 16px;
          background: white;
        }

        .message {
          margin-bottom: 16px;
          max-width: 80%;
          padding: 12px 16px;
          border-radius: 12px;
          position: relative;
        }

        .message.user {
          align-self: flex-end;
          background: #3b82f6;
          color: white;
          border-bottom-right-radius: 4px;
        }

        .message.bot {
          align-self: flex-start;
          background: #f3f4f6;
          color: #374151;
          border-bottom-left-radius: 4px;
          border-left: 4px solid #6b7280;
        }

        .message-text {
          margin-bottom: 4px;
          line-height: 1.4;
          white-space: pre-wrap;
        }

        .follow-up-questions {
          margin-top: 8px;
          padding-top: 8px;
          border-top: 1px solid rgba(0, 0, 0, 0.1);
        }

        .follow-up-questions p {
          margin: 0 0 8px 0;
          font-size: 12px;
          font-style: italic;
          color: #6b7280;
        }

        .follow-up-btn {
          display: block;
          width: 100%;
          padding: 6px 8px;
          margin: 4px 0;
          border: 1px solid #d1d5db;
          border-radius: 4px;
          background: white;
          color: #374151;
          cursor: pointer;
          font-size: 12px;
          text-align: left;
        }

        .follow-up-btn:hover {
          background: #f9fafb;
        }

        .message-time {
          font-size: 11px;
          color: #9ca3af;
          text-align: right;
        }

        .message.user .message-time {
          color: rgba(255, 255, 255, 0.7);
        }

        .typing-indicator {
          display: flex;
          gap: 4px;
          padding: 8px 0;
        }

        .typing-indicator span {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #9ca3af;
          animation: typing 1.4s infinite ease-in-out;
        }

        .typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
        .typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

        @keyframes typing {
          0%, 80%, 100% { transform: scale(0); }
          40% { transform: scale(1); }
        }

        .chat-input {
          padding: 16px;
          background: white;
          border-top: 1px solid #e5e7eb;
        }

        .input-container {
          display: flex;
          gap: 8px;
        }

        .message-input {
          flex: 1;
          padding: 12px;
          border: 1px solid #d1d5db;
          border-radius: 8px;
          resize: none;
          font-family: inherit;
          font-size: 14px;
        }

        .message-input:focus {
          outline: none;
          border-color: #3b82f6;
        }

        .send-button {
          padding: 12px 20px;
          background: #3b82f6;
          color: white;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          font-size: 14px;
          font-weight: 500;
        }

        .send-button:hover:not(:disabled) {
          background: #2563eb;
        }

        .send-button:disabled {
          background: #9ca3af;
          cursor: not-allowed;
        }
      `}</style>
    </div>
  );
};

export default AstrologyChat;
