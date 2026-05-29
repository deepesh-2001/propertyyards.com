import React, { useState, useEffect } from 'react';
import axios from 'axios';

const PropertyLayoutDesigner = ({ propertyId, onLayoutUpdate }) => {
  const [rooms, setRooms] = useState([]);
  const [selectedRoom, setSelectedRoom] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [roomTypes, setRoomTypes] = useState([]);
  const [vastuDirections, setVastuDirections] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [showGrid, setShowGrid] = useState(true);
  const [scale, setScale] = useState(1);

  // Container dimensions
  const containerWidth = 600;
  const containerHeight = 400;

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      const [roomTypesRes, directionsRes, templatesRes] = await Promise.all([
        axios.get('/api/property-layout/room-types'),
        axios.get('/api/property-layout/vastu-directions'),
        axios.get('/api/property-layout/templates')
      ]);

      setRoomTypes(roomTypesRes.data.data);
      setVastuDirections(directionsRes.data.data);
      setTemplates(templatesRes.data.data);
    } catch (error) {
      console.error('Failed to load initial data:', error);
    }
  };

  const addRoom = (roomType) => {
    const newRoom = {
      id: `room_${Date.now()}`,
      name: `${roomType.replace('_', ' ').title()} ${rooms.length + 1}`,
      room_type: roomType,
      x: Math.random() * 60 + 10,
      y: Math.random() * 60 + 10,
      width: 20,
      height: 20,
      area_sqft: 100
    };
    setRooms([...rooms, newRoom]);
    setSelectedRoom(newRoom);
  };

  const updateRoom = (roomId, updates) => {
    setRooms(rooms.map(room => 
      room.id === roomId ? { ...room, ...updates } : room
    ));
    if (selectedRoom && selectedRoom.id === roomId) {
      setSelectedRoom({ ...selectedRoom, ...updates });
    }
  };

  const deleteRoom = (roomId) => {
    setRooms(rooms.filter(room => room.id !== roomId));
    if (selectedRoom && selectedRoom.id === roomId) {
      setSelectedRoom(null);
    }
  };

  const analyzeLayout = async () => {
    if (rooms.length === 0) return;

    setIsAnalyzing(true);
    try {
      const response = await axios.post('/api/property-layout/analyze', {
        rooms: rooms,
        total_width: 100,
        total_height: 100
      });

      setAnalysis(response.data.data);
      onLayoutUpdate && onLayoutUpdate(response.data.data);
    } catch (error) {
      console.error('Analysis failed:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const applyTemplate = async (templateName) => {
    try {
      const response = await axios.post('/api/property-layout/apply-template', {
        template_name: templateName,
        total_area: 1000
      });

      const templateRooms = response.data.data.rooms.map((room, index) => ({
        id: `template_room_${index}`,
        name: room.room_type.replace('_', ' ').title(),
        room_type: room.room_type,
        x: room.position.x,
        y: room.position.y,
        width: room.position.width,
        height: room.position.height,
        area_sqft: room.area_sqft
      }));

      setRooms(templateRooms);
      setAnalysis(null);
    } catch (error) {
      console.error('Failed to apply template:', error);
    }
  };

  const getRoomColor = (roomType) => {
    const colors = {
      living_room: '#3b82f6',
      bedroom: '#10b981',
      kitchen: '#f59e0b',
      bathroom: '#8b5cf6',
      puja_room: '#ef4444',
      study_room: '#06b6d4',
      dining_room: '#ec4899',
      store_room: '#6b7280',
      balcony: '#84cc16',
      garden: '#22c55e',
      garage: '#f97316',
      stairs: '#a855f7'
    };
    return colors[roomType] || '#6b7280';
  };

  const getComplianceColor = (score) => {
    if (score >= 0.9) return '#10b981';
    if (score >= 0.8) return '#3b82f6';
    if (score >= 0.6) return '#f59e0b';
    if (score >= 0.4) return '#ef4444';
    return '#7c2d12';
  };

  const handleRoomClick = (room, event) => {
    event.stopPropagation();
    setSelectedRoom(room);
  };

  const handleContainerClick = () => {
    setSelectedRoom(null);
  };

  return (
    <div className="property-layout-designer">
      <div className="layout-header">
        <h3>Property Layout Designer</h3>
        <div className="layout-controls">
          <button
            onClick={() => setShowGrid(!showGrid)}
            className={`btn ${showGrid ? 'btn-primary' : 'btn-secondary'}`}
          >
            {showGrid ? 'Hide Grid' : 'Show Grid'}
          </button>
          <button
            onClick={analyzeLayout}
            disabled={rooms.length === 0 || isAnalyzing}
            className="btn btn-success"
          >
            {isAnalyzing ? 'Analyzing...' : 'Analyze Vastu'}
          </button>
        </div>
      </div>

      <div className="layout-content">
        <div className="layout-sidebar">
          <div className="room-types">
            <h4>Add Rooms</h4>
            <div className="room-type-grid">
              {roomTypes.map(type => (
                <button
                  key={type.value}
                  onClick={() => addRoom(type.value)}
                  className="room-type-btn"
                  style={{ backgroundColor: getRoomColor(type.value) }}
                >
                  {type.label}
                </button>
              ))}
            </div>
          </div>

          <div className="templates">
            <h4>Templates</h4>
            <div className="template-list">
              {Object.entries(templates).map(([key, template]) => (
                <button
                  key={key}
                  onClick={() => applyTemplate(key)}
                  className="template-btn"
                >
                  {template.name}
                  <small>{template.total_area} sqft</small>
                </button>
              ))}
            </div>
          </div>

          {selectedRoom && (
            <div className="room-editor">
              <h4>Edit Room</h4>
              <div className="room-form">
                <label>
                  Name:
                  <input
                    type="text"
                    value={selectedRoom.name}
                    onChange={(e) => updateRoom(selectedRoom.id, { name: e.target.value })}
                  />
                </label>
                <label>
                  Type:
                  <select
                    value={selectedRoom.room_type}
                    onChange={(e) => updateRoom(selectedRoom.id, { room_type: e.target.value })}
                  >
                    {roomTypes.map(type => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Area (sqft):
                  <input
                    type="number"
                    value={selectedRoom.area_sqft}
                    onChange={(e) => updateRoom(selectedRoom.id, { area_sqft: parseFloat(e.target.value) })}
                  />
                </label>
                <label>
                  Position X (%):
                  <input
                    type="range"
                    min="0"
                    max="80"
                    value={selectedRoom.x}
                    onChange={(e) => updateRoom(selectedRoom.id, { x: parseFloat(e.target.value) })}
                  />
                  <span>{selectedRoom.x.toFixed(1)}%</span>
                </label>
                <label>
                  Position Y (%):
                  <input
                    type="range"
                    min="0"
                    max="80"
                    value={selectedRoom.y}
                    onChange={(e) => updateRoom(selectedRoom.id, { y: parseFloat(e.target.value) })}
                  />
                  <span>{selectedRoom.y.toFixed(1)}%</span>
                </label>
                <label>
                  Width (%):
                  <input
                    type="range"
                    min="10"
                    max="40"
                    value={selectedRoom.width}
                    onChange={(e) => updateRoom(selectedRoom.id, { width: parseFloat(e.target.value) })}
                  />
                  <span>{selectedRoom.width.toFixed(1)}%</span>
                </label>
                <label>
                  Height (%):
                  <input
                    type="range"
                    min="10"
                    max="40"
                    value={selectedRoom.height}
                    onChange={(e) => updateRoom(selectedRoom.id, { height: parseFloat(e.target.value) })}
                  />
                  <span>{selectedRoom.height.toFixed(1)}%</span>
                </label>
                <button
                  onClick={() => deleteRoom(selectedRoom.id)}
                  className="btn btn-danger"
                >
                  Delete Room
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="layout-main">
          <div className="layout-canvas">
            <div
              className="layout-container"
              style={{
                width: containerWidth,
                height: containerHeight,
                position: 'relative',
                border: '2px solid #374151',
                backgroundColor: '#f9fafb'
              }}
              onClick={handleContainerClick}
            >
              {showGrid && (
                <div className="grid-overlay">
                  {[...Array(10)].map((_, i) => (
                    <div key={`h-${i}`} className="grid-line-horizontal" style={{ top: `${i * 10}%` }} />
                  ))}
                  {[...Array(10)].map((_, i) => (
                    <div key={`v-${i}`} className="grid-line-vertical" style={{ left: `${i * 10}%` }} />
                  ))}
                </div>
              )}

              {rooms.map(room => (
                <div
                  key={room.id}
                  className={`room ${selectedRoom?.id === room.id ? 'selected' : ''}`}
                  style={{
                    position: 'absolute',
                    left: `${room.x}%`,
                    top: `${room.y}%`,
                    width: `${room.width}%`,
                    height: `${room.height}%`,
                    backgroundColor: getRoomColor(room.room_type),
                    border: selectedRoom?.id === room.id ? '3px solid #1f2937' : '1px solid #6b7280',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                    fontSize: '12px',
                    fontWeight: 'bold',
                    textShadow: '1px 1px 2px rgba(0,0,0,0.7)',
                    borderRadius: '4px',
                    transition: 'all 0.2s'
                  }}
                  onClick={(e) => handleRoomClick(room, e)}
                >
                  <div style={{ textAlign: 'center' }}>
                    <div>{room.name}</div>
                    <small>{room.area_sqft} sqft</small>
                  </div>
                </div>
              ))}

              {/* Direction Labels */}
              <div className="direction-labels">
                <div className="direction-label" style={{ top: '5px', left: '50%', transform: 'translateX(-50%)' }}>North</div>
                <div className="direction-label" style={{ bottom: '5px', left: '50%', transform: 'translateX(-50%)' }}>South</div>
                <div className="direction-label" style={{ left: '5px', top: '50%', transform: 'translateY(-50%)' }}>West</div>
                <div className="direction-label" style={{ right: '5px', top: '50%', transform: 'translateY(-50%)' }}>East</div>
              </div>
            </div>
          </div>

          {analysis && (
            <div className="analysis-results">
              <h4>Vastu Analysis Results</h4>
              <div className="analysis-score">
                <div className="score-circle" style={{ borderColor: getComplianceColor(analysis.overall_score) }}>
                  <div className="score-value" style={{ color: getComplianceColor(analysis.overall_score) }}>
                    {(analysis.overall_score * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="score-label">
                  <strong>{analysis.vastu_compliance.toUpperCase()}</strong>
                </div>
              </div>

              {analysis.recommendations.length > 0 && (
                <div className="recommendations">
                  <h5>Recommendations:</h5>
                  <ul>
                    {analysis.recommendations.map((rec, index) => (
                      <li key={index}>{rec}</li>
                    ))}
                  </ul>
                </div>
              )}

              {analysis.violations.length > 0 && (
                <div className="violations">
                  <h5>Vastu Violations:</h5>
                  <ul>
                    {analysis.violations.map((violation, index) => (
                      <li key={index} className="violation-item">{violation}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <style jsx>{`
        .property-layout-designer {
          padding: 20px;
          font-family: Arial, sans-serif;
        }

        .layout-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }

        .layout-controls {
          display: flex;
          gap: 10px;
        }

        .btn {
          padding: 8px 16px;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
        }

        .btn-primary { background-color: #3b82f6; color: white; }
        .btn-secondary { background-color: #6b7280; color: white; }
        .btn-success { background-color: #10b981; color: white; }
        .btn-danger { background-color: #ef4444; color: white; }

        .layout-content {
          display: flex;
          gap: 20px;
        }

        .layout-sidebar {
          width: 300px;
          flex-shrink: 0;
        }

        .room-types, .templates, .room-editor {
          margin-bottom: 20px;
          padding: 15px;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
        }

        .room-type-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 8px;
          margin-top: 10px;
        }

        .room-type-btn {
          padding: 8px;
          border: none;
          border-radius: 4px;
          color: white;
          cursor: pointer;
          font-size: 12px;
        }

        .template-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
          margin-top: 10px;
        }

        .template-btn {
          padding: 10px;
          border: 1px solid #e5e7eb;
          border-radius: 4px;
          background: white;
          cursor: pointer;
          text-align: left;
        }

        .template-btn small {
          display: block;
          color: #6b7280;
          font-size: 11px;
        }

        .room-form {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .room-form label {
          display: flex;
          flex-direction: column;
          font-size: 14px;
        }

        .room-form input, .room-form select {
          margin-top: 4px;
          padding: 6px;
          border: 1px solid #d1d5db;
          border-radius: 4px;
        }

        .layout-main {
          flex: 1;
        }

        .layout-canvas {
          margin-bottom: 20px;
        }

        .grid-overlay {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          pointer-events: none;
        }

        .grid-line-horizontal, .grid-line-vertical {
          position: absolute;
          background-color: rgba(0, 0, 0, 0.1);
        }

        .grid-line-horizontal {
          left: 0;
          right: 0;
          height: 1px;
        }

        .grid-line-vertical {
          top: 0;
          bottom: 0;
          width: 1px;
        }

        .room:hover {
          transform: scale(1.02);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }

        .room.selected {
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.5);
        }

        .direction-labels {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          pointer-events: none;
        }

        .direction-label {
          position: absolute;
          font-size: 12px;
          font-weight: bold;
          color: #374151;
        }

        .analysis-results {
          padding: 20px;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          background: white;
        }

        .analysis-score {
          display: flex;
          align-items: center;
          gap: 20px;
          margin-bottom: 20px;
        }

        .score-circle {
          width: 80px;
          height: 80px;
          border: 4px solid #10b981;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .score-value {
          font-size: 18px;
          font-weight: bold;
        }

        .recommendations, .violations {
          margin-top: 15px;
        }

        .recommendations ul, .violations ul {
          margin: 10px 0;
          padding-left: 20px;
        }

        .violation-item {
          color: #ef4444;
          font-weight: bold;
        }
      `}</style>
    </div>
  );
};

export default PropertyLayoutDesigner;
