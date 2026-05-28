import React, { useRef, useState, useEffect, useCallback } from 'react'
import { FiPenTool, FiSquare, FiCircle, FiArrowRight, FiTrash2, FiDownload, FiSave, FiFolder, FiImage } from 'react-icons/fi'
import { useCacheStore } from '../../stores/cacheStore'
import './Whiteboard.css'

// Test data for demonstration
const TEST_WHITEboards = [
  {
    id: 'test-floor-plan-1',
    name: 'Sample 2BHK Floor Plan',
    data: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAwIiBoZWlnaHQ9IjYwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iODAwIiBoZWlnaHQ9IjYwMCIgZmlsbD0iI2Y5ZmFmYiIgc3Ryb2tlPSIjZTJhODdmIiBzdHJva2Utd2lkdGg9IjIiLz48cmVjdCB4PSI1MCIgeT0iNTAiIHdpZHRoPSIzMDAiIGhlaWdodD0iMjUwIiBmaWxsPSIjZGZlNmViIiBzdHJva2U9IiM2YjcyODAiIHN0cm9rZS13aWR0aD0iMiIvPjx0ZXh0IHg9IjIwMCIgeT0iMTgwIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LXNpemU9IjE4IiBmaWxsPSIjMzc0MTUxIj5MaXZpbmcgUm9vbTwvdGV4dD48cmVjdCB4PSIzNzAiIHk9IjUwIiB3aWR0aD0iMjAwIiBoZWlnaHQ9IjE1MCIgZmlsbD0iI2RiZTJmNyIgc3Ryb2tlPSIjNmI3MjgwIiBzdHJva2Utd2lkdGg9IjIiLz48dGV4dCB4PSI0NzAiIHk9IjEzMCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC1zaXplPSIxNiIgZmlsbD0iIzM3NDE1MSI+S2l0Y2hlbjwvdGV4dD48cmVjdCB4PSIzNzAiIHk9IjIyMCIgd2lkdGg9IjE4MCIgaGVpZ2h0PSIyMDAiIGZpbGw9IiNkZmU2ZWIiIHN0cm9rZT0iIzZiNzI4MCIgc3Ryb2tlLXdpZHRoPSIyIi8+PHRleHQgeD0iNDYwIiB5PSIzMzAiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZvbnQtc2l6ZT0iMTYiIGZpbGw9IiMzNzQxNTEiPk1hc3RlciBCZWQ8L3RleHQ+PHJlY3QgeD0iNTgwIiB5PSIyMjAiIHdpZHRoPSIyMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjZGZlNmViIiBzdHJva2U9IiM2YjcyODAiIHN0cm9rZS13aWR0aD0iMiIvPjx0ZXh0IHg9IjY4MCIgeT0iMzMwIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LXNpemU9IjE2IiBmaWxsPSIjMzc0MTUxIj5CZWQgUm9vbSAyPC90ZXh0Pjwvc3ZnPg=='
  },
  {
    id: 'test-layout-1',
    name: 'Garden Layout',
    data: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAwIiBoZWlnaHQ9IjYwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iODAwIiBoZWlnaHQ9IjYwMCIgZmlsbD0iI2YwZmRmNCIgc3Ryb2tlPSIjODRjYzE2IiBzdHJva2Utd2lkdGg9IjMiLz48Y2lyY2xlIGN4PSIyMDAiIGN5PSIyMDAiIHI9IjgwIiBmaWxsPSIjYmJmN2QwIiBzdHJva2U9IiM0NDhkMTgiIHN0cm9rZS13aWR0aD0iMiIvPjx0ZXh0IHg9IjIwMCIgeT0iMjA1IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LXNpemU9IjE0IiBmaWxsPSIjMjJiYzMzIj5UcmVlPC90ZXh0PjxjaXJjbGUgY3g9IjQwMCIgY3k9IjMwMCIgcj0iNjAiIGZpbGw9IiNiYmY3ZDAiIHN0cm9rZT0iIzQ0OGQxOCIgc3Ryb2tlLXdpZHRoPSIyIi8+PHRleHQgeD0iNDAwIiB5PSIzMDUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiMyMmJjMzMiPlRyZWU8L3RleHQ+PGNpcmNsZSBjeD0iNjAwIiBjeT0iMjAwIiByPSI3MCIgZmlsbD0iI2JiZjdkMCIgc3Ryb2tlPSIjNDQ4ZDE4IiBzdHJva2Utd2lkdGg9IjIiLz48dGV4dCB4PSI2MDAiIHk9IjIwNSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzIyYmMzMyI+VHJlZTwvdGV4dD48cmVjdCB4PSIzMDAiIHk9IjQwMCIgd2lkdGg9IjIwMCIgaGVpZ2h0PSIxMDAiIGZpbGw9IiNmZWUwYTAiIHN0cm9rZT0iI2Q5N2EwMCIgc3Ryb2tlLXdpZHRoPSIyIi8+PHRleHQgeD0iNDAwIiB5PSI0NTUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiM5MjQwMDAiPlBhdGlvPC90ZXh0Pjwvc3ZnPg=='
  }
]

// Test images for background
const TEST_IMAGES = [
  {
    id: 'floor-plan-template',
    name: 'Floor Plan Template',
    src: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAwIiBoZWlnaHQ9IjYwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iODAwIiBoZWlnaHQ9IjYwMCIgZmlsbD0iI2Y4ZmFmYyIgc3Ryb2tlPSIjZTVlN2ViIiBzdHJva2Utd2lkdGg9IjIiLz48Z3JpZCBzdHJva2U9IiNkMWRkZWIiIHN0cm9rZS13aWR0aD0iMSIvPjxsaW5lIHgxPSIwIiB5MT0iNTAiIHgyPSI4MDAiIHkyPSI1MCIvPjxsaW5lIHgxPSIwIiB5MT0iMTAwIiB4Mj0iODAwIiB5Mj0iMTAwIi8+PGxpbmUgeDE9IjAiIHkxPSIxNTAiIHgyPSI4MDAiIHkyPSIxNTAiLz48bGluZSB4MT0iMCIgeTE9IjIwMCIgeDI9IjgwMCIgeTI9IjIwMCIvPjxsaW5lIHgxPSIwIiB5MT0iMjUwIiB4Mj0iODAwIiB5Mj0iMjUwIi8+PGxpbmUgeDE9IjAiIHkxPSIzMDAiIHgyPSI4MDAiIHkyPSIzMDAiLz48bGluZSB4MT0iMCIgeTE9IjM1MCIgeDI9IjgwMCIgeTI9IjM1MCIvPjxsaW5lIHgxPSIwIiB5MT0iNDAwIiB4Mj0iODAwIiB5Mj0iNDAwIi8+PGxpbmUgeDE9IjAiIHkxPSI0NTAiIHgyPSI4MDAiIHkyPSI0NTAiLz48bGluZSB4MT0iMCIgeTE9IjUwMCIgeDI9IjgwMCIgeTI9IjUwMCIvPjxsaW5lIHgxPSIwIiB5MT0iNTUwIiB4Mj0iODAwIiB5Mj0iNTUwIi8+PGxpbmUgeDE9IjUwIiB5MT0iMCIgeDI9IjUwIiB5Mj0iNjAwIi8+PGxpbmUgeDE9IjEwMCIgeTE9IjAiIHgyPSIxMDAiIHkyPSI2MDAiLz48bGluZSB4MT0iMTUwIiB5MT0iMCIgeDI9IjE1MCIgeTI9IjYwMCIvPjxsaW5lIHgxPSIyMDAiIHkxPSIwIiB4Mj0iMjAwIiB5Mj0iNjAwIi8+PGxpbmUgeDE9IjI1MCIgeTE9IjAiIHgyPSIyNTAiIHkyPSI2MDAiLz48bGluZSB4MT0iMzAwIiB5MT0iMCIgeDI9IjMwMCIgeTI9IjYwMCIvPjxsaW5lIHgxPSIzNTAiIHkxPSIwIiB4Mj0iMzUwIiB5Mj0iNjAwIi8+PGxpbmUgeDE9IjQwMCIgeTE9IjAiIHgyPSI0MDAiIHkyPSI2MDAiLz48bGluZSB4MT0iNDUwIiB5MT0iMCIgeDI9IjQ1MCIgeTI9IjYwMCIvPjxsaW5lIHgxPSI1MDAiIHkxPSIwIiB4Mj0iNTAwIiB5Mj0iNjAwIi8+PGxpbmUgeDE9IjU1MCIgeTE9IjAiIHgyPSI1NTAiIHkyPSI2MDAiLz48bGluZSB4MT0iNjAwIiB5MT0iMCIgeDI9IjYwMCIgeTI9IjYwMCIvPjxsaW5lIHgxPSI2NTAiIHkxPSIwIiB4Mj0iNjUwIiB5Mj0iNjAwIi8+PGxpbmUgeDE9IjcwMCIgeTE9IjAiIHgyPSI3MDAiIHkyPSI2MDAiLz48bGluZSB4MT0iNzUwIiB5MT0iMCIgeDI9Ijc1MCIgeTI9IjYwMCIvPjx0ZXh0IHg9IjQwMCIgeT0iMzAwIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LXNpemU9IjI0IiBmaWxsPSIjOWNhM2FmIiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiI+Rmxvb3IgUGxhbiBUZW1wbGF0ZTwvdGV4dD48L3N2Zz4='
  },
  {
    id: 'property-layout',
    name: 'Property Layout',
    src: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAwIiBoZWlnaHQ9IjYwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iODAwIiBoZWlnaHQ9IjYwMCIgZmlsbD0iI2Y1ZjVmNSIgc3Ryb2tlPSIjY2NjIiBzdHJva2Utd2lkdGg9IjIiLz48cmVjdCB4PSIxMDAiIHk9IjEwMCIgd2lkdGg9IjYwMCIgaGVpZ2h0PSI0MDAiIGZpbGw9IiNmZmYiIHN0cm9rZT0iIzk5OSIgc3Ryb2tlLXdpZHRoPSIzIi8+PHJlY3QgeD0iMTUwIiB5PSIxNTAiIHdpZHRoPSIyMDAiIGhlaWdodD0iMTUwIiBmaWxsPSIjZTZmM2ZmIiBzdHJva2U9IiM2YjcyODAiLz48dGV4dCB4PSIyNTAiIHk9IjIyNSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzM3NDE1MSI+Um9vbSAxPC90ZXh0PjxyZWN0IHg9IjQwMCIgeT0iMTUwIiB3aWR0aD0iMjAwIiBoZWlnaHQ9IjE1MCIgZmlsbD0iI2YxZjVmOSIgc3Ryb2tlPSIjNmI3MjgwIi8+PHRleHQgeD0iNTAwIiB5PSIyMjUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiMzNzQxNTEiPlJvb20gMjwvdGV4dD48cmVjdCB4PSIzMDAiIHk9IjMyMCIgd2lkdGg9IjMwMCIgaGVpZ2h0PSIxMjAiIGZpbGw9IiNmZmZiZTYiIHN0cm9rZT0iIzZiNzI4MCIvPjx0ZXh0IHg9IjQ1MCIgeT0iMzkwIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LXNpemU9IjE0IiBmaWxsPSIjMzc0MTUxIj5MaXZpbmcgQXJlYTwvdGV4dD48L3N2Zz4='
  }
]

const TOOLS = {
  pen: 'pen',
  rectangle: 'rectangle',
  circle: 'circle',
  line: 'line',
  eraser: 'eraser'
}

const COLORS = ['#000000', '#ef4444', '#22c55e', '#3b82f6', '#f59e0b', '#8b5cf6', '#ec4899', '#ffffff']

export function Whiteboard() {
  const canvasRef = useRef(null)
  const [isDrawing, setIsDrawing] = useState(false)
  const [tool, setTool] = useState(TOOLS.pen)
  const [color, setColor] = useState('#000000')
  const [brushSize, setBrushSize] = useState(3)
  const [startPos, setStartPos] = useState(null)
  const [snapshot, setSnapshot] = useState(null)
  const [backgroundImage, setBackgroundImage] = useState(null)
  const [savedWhiteboards, setSavedWhiteboards] = useState([])
  const [currentName, setCurrentName] = useState('Untitled')
  const [showGallery, setShowGallery] = useState(false)
  const [currentId, setCurrentId] = useState(null)

  const { saveWhiteboard, getWhiteboard, getAllWhiteboards, deleteWhiteboard } = useCacheStore()

  // Load saved whiteboards on mount
  useEffect(() => {
    const all = getAllWhiteboards()
    setSavedWhiteboards(all)
  }, [])

  // Initialize canvas
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    ctx.lineCap = 'round'
    ctx.lineJoin = 'round'
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    // Load test data if available
    const testData = TEST_WHITEboards[0]
    if (testData) {
      const img = new Image()
      img.onload = () => {
        ctx.drawImage(img, 0, 0)
      }
      img.src = testData.data
    }
  }, [])

  const getCanvasCoordinates = (e) => {
    const canvas = canvasRef.current
    const rect = canvas.getBoundingClientRect()
    const scaleX = canvas.width / rect.width
    const scaleY = canvas.height / rect.height
    return {
      x: (e.clientX - rect.left) * scaleX,
      y: (e.clientY - rect.top) * scaleY
    }
  }

  const startDrawing = useCallback((e) => {
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    const coords = getCanvasCoordinates(e)

    setIsDrawing(true)
    setStartPos(coords)

    if (tool === TOOLS.pen || tool === TOOLS.eraser) {
      ctx.beginPath()
      ctx.moveTo(coords.x, coords.y)
      ctx.strokeStyle = tool === TOOLS.eraser ? '#ffffff' : color
      ctx.lineWidth = tool === TOOLS.eraser ? brushSize * 3 : brushSize
    } else {
      // Save snapshot for shapes
      setSnapshot(ctx.getImageData(0, 0, canvas.width, canvas.height))
    }
  }, [tool, color, brushSize])

  const draw = useCallback((e) => {
    if (!isDrawing) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    const coords = getCanvasCoordinates(e)

    if (tool === TOOLS.pen || tool === TOOLS.eraser) {
      ctx.lineTo(coords.x, coords.y)
      ctx.stroke()
    } else if (snapshot) {
      // Restore snapshot for shapes preview
      ctx.putImageData(snapshot, 0, 0)
      ctx.strokeStyle = color
      ctx.lineWidth = brushSize
      ctx.fillStyle = color + '33' // Add transparency

      const width = coords.x - startPos.x
      const height = coords.y - startPos.y

      ctx.beginPath()
      if (tool === TOOLS.rectangle) {
        ctx.rect(startPos.x, startPos.y, width, height)
        ctx.fill()
        ctx.stroke()
      } else if (tool === TOOLS.circle) {
        const radius = Math.sqrt(width * width + height * height)
        ctx.arc(startPos.x, startPos.y, radius, 0, 2 * Math.PI)
        ctx.fill()
        ctx.stroke()
      } else if (tool === TOOLS.line) {
        ctx.moveTo(startPos.x, startPos.y)
        ctx.lineTo(coords.x, coords.y)
        ctx.stroke()
      }
    }
  }, [isDrawing, tool, color, brushSize, startPos, snapshot])

  const stopDrawing = useCallback(() => {
    setIsDrawing(false)
    setSnapshot(null)
  }, [])

  const clearCanvas = () => {
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, canvas.width, canvas.height)
    if (backgroundImage) {
      const img = new Image()
      img.onload = () => {
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
      }
      img.src = backgroundImage
    }
  }

  const saveCurrent = () => {
    const canvas = canvasRef.current
    const data = canvas.toDataURL()
    const id = currentId || `whiteboard-${Date.now()}`
    saveWhiteboard(id, { name: currentName, data })
    setCurrentId(id)
    setSavedWhiteboards(getAllWhiteboards())
    alert('Whiteboard saved!')
  }

  const loadWhiteboard = (id) => {
    const cached = getWhiteboard(id)
    if (cached && cached.data) {
      const canvas = canvasRef.current
      const ctx = canvas.getContext('2d')
      const img = new Image()
      img.onload = () => {
        ctx.clearRect(0, 0, canvas.width, canvas.height)
        ctx.drawImage(img, 0, 0)
      }
      img.src = cached.data.data
      setCurrentName(cached.data.name)
      setCurrentId(id)
      setShowGallery(false)
    }
  }

  const loadTestWhiteboard = (testData) => {
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    const img = new Image()
    img.onload = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      ctx.drawImage(img, 0, 0)
    }
    img.src = testData.data
    setCurrentName(testData.name)
    setCurrentId(null)
  }

  const loadBackgroundImage = (src) => {
    setBackgroundImage(src)
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    const img = new Image()
    img.onload = () => {
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
    }
    img.src = src
  }

  const downloadCanvas = () => {
    const canvas = canvasRef.current
    const link = document.createElement('a')
    link.download = `${currentName.replace(/\s+/g, '-').toLowerCase()}.png`
    link.href = canvas.toDataURL()
    link.click()
  }

  const handleDelete = (id, e) => {
    e.stopPropagation()
    deleteWhiteboard(id)
    setSavedWhiteboards(getAllWhiteboards())
  }

  return (
    <div className="whiteboard-container">
      <div className="whiteboard-header">
        <h1>🏗️ Whiteboard</h1>
        <div className="whiteboard-name">
          <input
            type="text"
            value={currentName}
            onChange={(e) => setCurrentName(e.target.value)}
            placeholder="Whiteboard name"
          />
        </div>
        <div className="whiteboard-actions">
          <button onClick={() => setShowGallery(!showGallery)} className="btn-icon">
            <FiFolder /> Gallery
          </button>
          <button onClick={saveCurrent} className="btn-icon btn-primary">
            <FiSave /> Save
          </button>
          <button onClick={downloadCanvas} className="btn-icon">
            <FiDownload /> Export
          </button>
          <button onClick={clearCanvas} className="btn-icon btn-danger">
            <FiTrash2 /> Clear
          </button>
        </div>
      </div>

      {showGallery && (
        <div className="whiteboard-gallery">
          <h3>📁 Saved Whiteboards</h3>
          {savedWhiteboards.length === 0 ? (
            <p className="no-saved">No saved whiteboards yet</p>
          ) : (
            <div className="gallery-grid">
              {savedWhiteboards.map((item) => (
                <div key={item.id} className="gallery-item" onClick={() => loadWhiteboard(item.id)}>
                  <img src={item.data?.data} alt={item.data?.name} />
                  <span>{item.data?.name}</span>
                  <button
                    className="delete-btn"
                    onClick={(e) => handleDelete(item.id, e)}
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}

          <h3>🎨 Sample Templates</h3>
          <div className="gallery-grid">
            {TEST_WHITEboards.map((item) => (
              <div key={item.id} className="gallery-item" onClick={() => loadTestWhiteboard(item)}>
                <img src={item.data} alt={item.name} />
                <span>{item.name}</span>
              </div>
            ))}
          </div>

          <h3>🖼️ Background Templates</h3>
          <div className="gallery-grid">
            {TEST_IMAGES.map((item) => (
              <div key={item.id} className="gallery-item" onClick={() => loadBackgroundImage(item.src)}>
                <img src={item.src} alt={item.name} />
                <span>{item.name}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="whiteboard-toolbar">
        <div className="tool-group">
          <button
            className={`tool-btn ${tool === TOOLS.pen ? 'active' : ''}`}
            onClick={() => setTool(TOOLS.pen)}
            title="Pen"
          >
            <FiPenTool />
          </button>
          <button
            className={`tool-btn ${tool === TOOLS.rectangle ? 'active' : ''}`}
            onClick={() => setTool(TOOLS.rectangle)}
            title="Rectangle"
          >
            <FiSquare />
          </button>
          <button
            className={`tool-btn ${tool === TOOLS.circle ? 'active' : ''}`}
            onClick={() => setTool(TOOLS.circle)}
            title="Circle"
          >
            <FiCircle />
          </button>
          <button
            className={`tool-btn ${tool === TOOLS.line ? 'active' : ''}`}
            onClick={() => setTool(TOOLS.line)}
            title="Line"
          >
            <FiArrowRight />
          </button>
          <button
            className={`tool-btn ${tool === TOOLS.eraser ? 'active' : ''}`}
            onClick={() => setTool(TOOLS.eraser)}
            title="Eraser"
          >
            <FiTrash2 />
          </button>
        </div>

        <div className="tool-group">
          {COLORS.map((c) => (
            <button
              key={c}
              className={`color-btn ${color === c ? 'active' : ''}`}
              style={{ backgroundColor: c, border: c === '#ffffff' ? '1px solid #ccc' : 'none' }}
              onClick={() => setColor(c)}
            />
          ))}
        </div>

        <div className="tool-group">
          <label>Brush: {brushSize}px</label>
          <input
            type="range"
            min="1"
            max="50"
            value={brushSize}
            onChange={(e) => setBrushSize(Number(e.target.value))}
          />
        </div>
      </div>

      <div className="whiteboard-canvas-wrapper">
        <canvas
          ref={canvasRef}
          width={1200}
          height={700}
          onMouseDown={startDrawing}
          onMouseMove={draw}
          onMouseUp={stopDrawing}
          onMouseLeave={stopDrawing}
          className="whiteboard-canvas"
        />
      </div>

      <div className="whiteboard-help">
        <p>
          <strong>Tip:</strong> Select a tool and draw on the canvas. Use the Gallery to load templates or saved whiteboards.
          <strong> Test data available:</strong> 2 sample floor plans and 2 background templates.
        </p>
      </div>
    </div>
  )
}

export default Whiteboard
