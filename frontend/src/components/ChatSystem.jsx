import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

const ChatSystem = ({ userId, userName }) => {
  const [chats, setChats] = useState([]);
  const [selectedChat, setSelectedChat] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [users, setUsers] = useState([]);
  const [showCreateChat, setShowCreateChat] = useState(false);
  const [showUserList, setShowUserList] = useState(false);
  const [typingUsers, setTypingUsers] = useState([]);
  const [onlineUsers, setOnlineUsers] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [showSearch, setShowSearch] = useState(false);
  const [unreadCounts, setUnreadCounts] = useState({});
  const [ws, setWs] = useState(null);
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  
  // WebSocket connection
  useEffect(() => {
    if (userId) {
      connectWebSocket();
    }
    
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [userId]);
  
  const connectWebSocket = () => {
    try {
      const websocket = new WebSocket(`ws://localhost:8000/api/chat/ws/${userId}`);
      
      websocket.onopen = () => {
        console.log('WebSocket connected');
        setWs(websocket);
      };
      
      websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      };
      
      websocket.onclose = () => {
        console.log('WebSocket disconnected');
        // Attempt to reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
      };
      
      websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  };
  
  const handleWebSocketMessage = (data) => {
    switch (data.type) {
      case 'new_message':
        if (selectedChat && selectedChat.id === data.data.chat_id) {
          setMessages(prev => [...prev, data.data]);
        }
        updateChatLastMessage(data.data.chat_id, data.data);
        break;
        
      case 'typing_indicator':
        setTypingUsers(data.data.typing_users || []);
        break;
        
      case 'new_chat':
        setChats(prev => [data.data, ...prev]);
        break;
        
      case 'participant_added':
        updateChatParticipants(data.data.chat_id, data.data.participants);
        break;
        
      case 'participant_removed':
        updateChatParticipants(data.data.chat_id, data.data.participants);
        break;
        
      case 'message_edited':
        updateMessage(data.data.message_id, data.data);
        break;
        
      case 'message_deleted':
        removeMessage(data.data.message_id);
        break;
        
      case 'reaction_added':
        updateMessageReaction(data.data.message_id, data.data.reaction, data.data.user_id, true);
        break;
        
      case 'reaction_removed':
        updateMessageReaction(data.data.message_id, data.data.reaction, data.data.user_id, false);
        break;
        
      default:
        console.log('Unknown WebSocket message type:', data.type);
    }
  };
  
  // Load initial data
  useEffect(() => {
    loadChats();
    loadUsers();
  }, []);
  
  const loadChats = async () => {
    try {
      const response = await axios.get('/api/chat/rooms');
      setChats(response.data.data);
      
      // Update unread counts
      const counts = {};
      response.data.data.forEach(chat => {
        counts[chat.id] = chat.unread_count || 0;
      });
      setUnreadCounts(counts);
    } catch (error) {
      console.error('Failed to load chats:', error);
    }
  };
  
  const loadUsers = async () => {
    try {
      const response = await axios.get('/api/chat/users');
      setUsers(response.data.data);
      setOnlineUsers(response.data.data.filter(user => user.is_online).map(user => user.id));
    } catch (error) {
      console.error('Failed to load users:', error);
    }
  };
  
  const loadMessages = async (chatId) => {
    try {
      const response = await axios.get(`/api/chat/rooms/${chatId}/messages`);
      setMessages(response.data.data);
      scrollToBottom();
    } catch (error) {
      console.error('Failed to load messages:', error);
    }
  };
  
  const sendMessage = async () => {
    if (!newMessage.trim() || !selectedChat) return;
    
    try {
      const response = await axios.post('/api/chat/send', {
        chat_id: selectedChat.id,
        content: newMessage,
        message_type: 'text'
      });
      
      setNewMessage('');
      if (ws) {
        ws.send(JSON.stringify({ type: 'ping' }));
      }
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };
  
  const createChat = async (chatData) => {
    try {
      const response = await axios.post('/api/chat/rooms', chatData);
      setShowCreateChat(false);
      loadChats();
    } catch (error) {
      console.error('Failed to create chat:', error);
    }
  };
  
  const searchMessages = async (query) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }
    
    try {
      const response = await axios.post('/api/chat/search', { query });
      setSearchResults(response.data.data);
    } catch (error) {
      console.error('Failed to search messages:', error);
    }
  };
  
  const handleChatSelect = (chat) => {
    setSelectedChat(chat);
    loadMessages(chat.id);
    setShowSearch(false);
    setSearchResults([]);
    setSearchQuery('');
    
    // Mark messages as read
    if (unreadCounts[chat.id] > 0) {
      setUnreadCounts(prev => ({ ...prev, [chat.id]: 0 }));
    }
  };
  
  const handleTyping = () => {
    if (ws && selectedChat) {
      ws.send(JSON.stringify({
        type: 'typing',
        chat_id: selectedChat.id
      }));
    }
  };
  
  const addReaction = async (messageId, reaction) => {
    try {
      await axios.post(`/api/chat/messages/${messageId}/react`, {
        message_id: messageId,
        reaction
      });
    } catch (error) {
      console.error('Failed to add reaction:', error);
    }
  };
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  const updateChatLastMessage = (chatId, message) => {
    setChats(prev => prev.map(chat => 
      chat.id === chatId 
        ? { ...chat, last_message: message }
        : chat
    ));
  };
  
  const updateChatParticipants = (chatId, participants) => {
    setChats(prev => prev.map(chat => 
      chat.id === chatId 
        ? { ...chat, participants }
        : chat
    ));
  };
  
  const updateMessage = (messageId, updates) => {
    setMessages(prev => prev.map(msg => 
      msg.id === messageId 
        ? { ...msg, ...updates }
        : msg
    ));
  };
  
  const removeMessage = (messageId) => {
    setMessages(prev => prev.filter(msg => msg.id !== messageId));
  };
  
  const updateMessageReaction = (messageId, reaction, userId, isAdd) => {
    setMessages(prev => prev.map(msg => {
      if (msg.id === messageId) {
        const reactions = { ...msg.reactions };
        if (isAdd) {
          if (!reactions[reaction]) reactions[reaction] = [];
          reactions[reaction].push(userId);
        } else {
          if (reactions[reaction]) {
            reactions[reaction] = reactions[reaction].filter(id => id !== userId);
            if (reactions[reaction].length === 0) delete reactions[reaction];
          }
        }
        return { ...msg, reactions };
      }
      return msg;
    }));
  };
  
  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };
  
  const getChatTypeIcon = (type) => {
    const icons = {
      'team': '👥',
      'client': '👤',
      'vendor': '🏢',
      'support': '🎧',
      'group': '👨‍👩‍👧‍👦',
      'direct': '💬'
    };
    return icons[type] || '💬';
  };
  
  return (
    <div className="chat-system">
      <div className="chat-sidebar">
        <div className="chat-header">
          <h3>💬 Chats</h3>
          <div className="header-actions">
            <button onClick={() => setShowCreateChat(true)} className="btn btn-primary">
              ➕ New Chat
            </button>
            <button onClick={() => setShowUserList(true)} className="btn btn-secondary">
              👥 Users
            </button>
          </div>
        </div>
        
        <div className="chat-search">
          <input
            type="text"
            placeholder="Search messages..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              searchMessages(e.target.value);
              setShowSearch(true);
            }}
            className="search-input"
          />
        </div>
        
        <div className="chat-list">
          {showSearch && searchResults.length > 0 ? (
            <div className="search-results">
              <h4>Search Results</h4>
              {searchResults.map(result => (
                <div key={result.id} className="search-result-item">
                  <div className="result-header">
                    <strong>{result.chat_name}</strong>
                    <span className="result-time">{formatTime(result.timestamp)}</span>
                  </div>
                  <div className="result-content">
                    <strong>{result.sender_name}:</strong> {result.content}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            chats.map(chat => (
              <div
                key={chat.id}
                className={`chat-item ${selectedChat?.id === chat.id ? 'selected' : ''}`}
                onClick={() => handleChatSelect(chat)}
              >
                <div className="chat-item-header">
                  <span className="chat-type-icon">{getChatTypeIcon(chat.chat_type)}</span>
                  <span className="chat-name">{chat.name}</span>
                  {unreadCounts[chat.id] > 0 && (
                    <span className="unread-badge">{unreadCounts[chat.id]}</span>
                  )}
                </div>
                <div className="chat-item-preview">
                  {chat.last_message && (
                    <>
                      <span className="last-sender">{chat.last_message.sender_name}:</span>
                      <span className="last-message">{chat.last_message.content}</span>
                    </>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
      
      <div className="chat-main">
        {selectedChat ? (
          <>
            <div className="chat-header-main">
              <div className="chat-info">
                <span className="chat-type-icon">{getChatTypeIcon(selectedChat.chat_type)}</span>
                <h4>{selectedChat.name}</h4>
                <span className="participant-count">
                  {selectedChat.participants.length} participants
                </span>
              </div>
              <div className="chat-actions">
                <button className="btn btn-secondary">ℹ️ Info</button>
              </div>
            </div>
            
            <div className="messages-container">
              {messages.map(message => (
                <div
                  key={message.id}
                  className={`message ${message.sender_id === userId ? 'sent' : 'received'}`}
                >
                  <div className="message-header">
                    <span className="sender-name">{message.sender_name}</span>
                    <span className="message-time">{formatTime(message.timestamp)}</span>
                    {message.edited && <span className="edited-indicator">(edited)</span>}
                  </div>
                  <div className="message-content">{message.content}</div>
                  
                  {message.reactions && Object.keys(message.reactions).length > 0 && (
                    <div className="message-reactions">
                      {Object.entries(message.reactions).map(([reaction, users]) => (
                        <button
                          key={reaction}
                          className="reaction-btn"
                          onClick={() => addReaction(message.id, reaction)}
                        >
                          {reaction} {users.length}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              
              {typingUsers.length > 0 && (
                <div className="typing-indicator">
                  <span>{typingUsers.join(', ')} is typing...</span>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
            
            <div className="message-input-container">
              <div className="input-actions">
                <button className="btn btn-secondary">📎</button>
                <button className="btn btn-secondary">😊</button>
              </div>
              <input
                ref={inputRef}
                type="text"
                placeholder="Type a message..."
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    sendMessage();
                  } else {
                    handleTyping();
                  }
                }}
                className="message-input"
              />
              <button
                onClick={sendMessage}
                disabled={!newMessage.trim()}
                className="send-button"
              >
                Send
              </button>
            </div>
          </>
        ) : (
          <div className="chat-empty">
            <div className="empty-content">
              <h3>Welcome to PropertyYards Chat</h3>
              <p>Select a chat to start messaging or create a new conversation</p>
              <div className="empty-actions">
                <button onClick={() => setShowCreateChat(true)} className="btn btn-primary">
                  Create New Chat
                </button>
                <button onClick={() => setShowUserList(true)} className="btn btn-secondary">
                  Browse Users
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
      
      {/* Create Chat Modal */}
      {showCreateChat && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>Create New Chat</h3>
              <button onClick={() => setShowCreateChat(false)} className="close-btn">✖️</button>
            </div>
            <div className="modal-body">
              <CreateChatForm
                users={users}
                onSubmit={createChat}
                onCancel={() => setShowCreateChat(false)}
              />
            </div>
          </div>
        </div>
      )}
      
      {/* User List Modal */}
      {showUserList && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>Chat Users</h3>
              <button onClick={() => setShowUserList(false)} className="close-btn">✖️</button>
            </div>
            <div className="modal-body">
              <UserList users={users} onlineUsers={onlineUsers} />
            </div>
          </div>
        </div>
      )}
      
      <style jsx>{`
        .chat-system {
          display: flex;
          height: 600px;
          border: 1px solid #e5e7eb;
          border-radius: 12px;
          overflow: hidden;
          font-family: Arial, sans-serif;
        }
        
        .chat-sidebar {
          width: 350px;
          border-right: 1px solid #e5e7eb;
          display: flex;
          flex-direction: column;
        }
        
        .chat-header {
          padding: 16px;
          border-bottom: 1px solid #e5e7eb;
          background: #f9fafb;
        }
        
        .chat-header h3 {
          margin: 0 0 12px 0;
          color: #374151;
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
        
        .btn:hover {
          transform: translateY(-1px);
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .chat-search {
          padding: 12px;
          border-bottom: 1px solid #e5e7eb;
        }
        
        .search-input {
          width: 100%;
          padding: 8px;
          border: 1px solid #d1d5db;
          border-radius: 6px;
          font-size: 14px;
        }
        
        .chat-list {
          flex: 1;
          overflow-y: auto;
        }
        
        .chat-item {
          padding: 12px 16px;
          border-bottom: 1px solid #f3f4f6;
          cursor: pointer;
          transition: background-color 0.2s;
        }
        
        .chat-item:hover {
          background: #f9fafb;
        }
        
        .chat-item.selected {
          background: #dbeafe;
          border-left: 3px solid #3b82f6;
        }
        
        .chat-item-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 4px;
        }
        
        .chat-type-icon {
          font-size: 16px;
        }
        
        .chat-name {
          flex: 1;
          font-weight: 500;
          color: #374151;
        }
        
        .unread-badge {
          background: #ef4444;
          color: white;
          border-radius: 10px;
          padding: 2px 6px;
          font-size: 11px;
          font-weight: bold;
        }
        
        .chat-item-preview {
          font-size: 12px;
          color: #6b7280;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        
        .last-sender {
          font-weight: 500;
          margin-right: 4px;
        }
        
        .search-results {
          padding: 12px;
        }
        
        .search-result-item {
          padding: 8px;
          border-bottom: 1px solid #f3f4f6;
        }
        
        .result-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 4px;
        }
        
        .result-time {
          font-size: 11px;
          color: #6b7280;
        }
        
        .result-content {
          font-size: 12px;
          color: #374151;
        }
        
        .chat-main {
          flex: 1;
          display: flex;
          flex-direction: column;
        }
        
        .chat-header-main {
          padding: 16px;
          border-bottom: 1px solid #e5e7eb;
          background: white;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        
        .chat-info {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        
        .chat-info h4 {
          margin: 0;
          color: #374151;
        }
        
        .participant-count {
          font-size: 12px;
          color: #6b7280;
        }
        
        .messages-container {
          flex: 1;
          overflow-y: auto;
          padding: 16px;
          background: #fafafa;
        }
        
        .message {
          margin-bottom: 16px;
          max-width: 70%;
        }
        
        .message.sent {
          align-self: flex-end;
          margin-left: auto;
        }
        
        .message.received {
          align-self: flex-start;
        }
        
        .message-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 4px;
          font-size: 12px;
          color: #6b7280;
        }
        
        .sender-name {
          font-weight: 500;
        }
        
        .message-time {
          font-size: 11px;
        }
        
        .edited-indicator {
          font-style: italic;
          font-size: 10px;
        }
        
        .message-content {
          padding: 8px 12px;
          border-radius: 8px;
          background: white;
          box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
          line-height: 1.4;
        }
        
        .message.sent .message-content {
          background: #3b82f6;
          color: white;
        }
        
        .message-reactions {
          display: flex;
          gap: 4px;
          margin-top: 4px;
        }
        
        .reaction-btn {
          padding: 2px 6px;
          border: 1px solid #e5e7eb;
          border-radius: 12px;
          background: white;
          cursor: pointer;
          font-size: 12px;
        }
        
        .reaction-btn:hover {
          background: #f3f4f6;
        }
        
        .typing-indicator {
          font-style: italic;
          color: #6b7280;
          font-size: 12px;
          margin-bottom: 8px;
        }
        
        .message-input-container {
          padding: 16px;
          border-top: 1px solid #e5e7eb;
          background: white;
          display: flex;
          gap: 8px;
          align-items: center;
        }
        
        .input-actions {
          display: flex;
          gap: 4px;
        }
        
        .message-input {
          flex: 1;
          padding: 8px 12px;
          border: 1px solid #d1d5db;
          border-radius: 20px;
          font-size: 14px;
        }
        
        .message-input:focus {
          outline: none;
          border-color: #3b82f6;
        }
        
        .send-button {
          padding: 8px 16px;
          background: #3b82f6;
          color: white;
          border: none;
          border-radius: 20px;
          cursor: pointer;
          font-size: 14px;
        }
        
        .send-button:hover:not(:disabled) {
          background: #2563eb;
        }
        
        .send-button:disabled {
          background: #9ca3af;
          cursor: not-allowed;
        }
        
        .chat-empty {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #fafafa;
        }
        
        .empty-content {
          text-align: center;
          color: #6b7280;
        }
        
        .empty-content h3 {
          margin: 0 0 8px 0;
          color: #374151;
        }
        
        .empty-actions {
          display: flex;
          gap: 8px;
          justify-content: center;
          margin-top: 16px;
        }
        
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }
        
        .modal {
          background: white;
          border-radius: 8px;
          width: 90%;
          max-width: 500px;
          max-height: 80vh;
          overflow: hidden;
        }
        
        .modal-header {
          padding: 16px;
          border-bottom: 1px solid #e5e7eb;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        
        .modal-header h3 {
          margin: 0;
          color: #374151;
        }
        
        .close-btn {
          background: none;
          border: none;
          font-size: 16px;
          cursor: pointer;
          color: #6b7280;
        }
        
        .modal-body {
          padding: 16px;
          overflow-y: auto;
          max-height: 60vh;
        }
      `}</style>
    </div>
  );
};

// Helper Components
const CreateChatForm = ({ users, onSubmit, onCancel }) => {
  const [name, setName] = useState('');
  const [chatType, setChatType] = useState('team');
  const [participants, setParticipants] = useState([]);
  
  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({
      name,
      chat_type: chatType,
      participants
    });
  };
  
  const toggleParticipant = (userId) => {
    setParticipants(prev => 
      prev.includes(userId) 
        ? prev.filter(id => id !== userId)
        : [...prev, userId]
    );
  };
  
  return (
    <form onSubmit={handleSubmit}>
      <div className="form-group">
        <label>Chat Name:</label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
      </div>
      
      <div className="form-group">
        <label>Chat Type:</label>
        <select value={chatType} onChange={(e) => setChatType(e.target.value)}>
          <option value="team">Team</option>
          <option value="client">Client</option>
          <option value="vendor">Vendor</option>
          <option value="support">Support</option>
          <option value="group">Group</option>
        </select>
      </div>
      
      <div className="form-group">
        <label>Participants:</label>
        <div className="participant-list">
          {users.map(user => (
            <label key={user.id} className="participant-item">
              <input
                type="checkbox"
                checked={participants.includes(user.id)}
                onChange={() => toggleParticipant(user.id)}
              />
              <span className="participant-info">
                <span className="participant-avatar">{user.avatar}</span>
                <span className="participant-name">{user.name}</span>
                <span className="participant-role">{user.role}</span>
              </span>
            </label>
          ))}
        </div>
      </div>
      
      <div className="form-actions">
        <button type="button" onClick={onCancel} className="btn btn-secondary">
          Cancel
        </button>
        <button type="submit" className="btn btn-primary">
          Create Chat
        </button>
      </div>
    </form>
  );
};

const UserList = ({ users, onlineUsers }) => {
  return (
    <div className="user-list">
      {users.map(user => (
        <div key={user.id} className="user-item">
          <div className="user-avatar">
            <span>{user.avatar}</span>
            <div className={`online-indicator ${onlineUsers.includes(user.id) ? 'online' : 'offline'}`} />
          </div>
          <div className="user-info">
            <div className="user-name">{user.name}</div>
            <div className="user-details">
              <span className="user-role">{user.role}</span>
              <span className="user-status">
                {onlineUsers.includes(user.id) ? 'Online' : 'Offline'}
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default ChatSystem;
