import React, { useState, useRef, useEffect, Suspense } from 'react'
import { Canvas, useFrame, useLoader } from '@react-three/fiber'
import { OrbitControls, PerspectiveCamera, Environment, Grid, Box, Sphere, Cylinder, Text } from '@react-three/drei'
import { FiUpload, FiBox, FiLayers, FiTrash2, FiDownload, FiSave, FiEye, FiRotateCcw } from 'react-icons/fi'
import { useCacheStore } from '../../stores/cacheStore'
import * as THREE from 'three'
import './Structure3D.css'

// Test images for 3D generation
const TEST_IMAGES = [
  {
    id: 'house-elevation',
    name: 'House Elevation',
    type: 'house',
    src: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjQwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNDAwIiBoZWlnaHQ9IjQwMCIgZmlsbD0iIzg3Y2VlYiIvPjxwb2x5Z29uIHBvaW50cz0iMjAwLDUwIDgwLDE4MCAzMjAsMTgwIiBmaWxsPSIjOGI0NTEzIi8+PHJlY3QgeD0iODAiIHk9IjE4MCIgd2lkdGg9IjI0MCIgaGVpZ2h0PSIxODAiIGZpbGw9IiNmZmYiIHN0cm9rZT0iIzMzMyIgc3Ryb2tlLXdpZHRoPSIzIi8+PHJlY3QgeD0iMTIwIiB5PSIyMjAiIHdpZHRoPSI2MCIgaGVpZ2h0PSI4MCIgZmlsbD0iIzY2YjJmZiIgc3Ryb2tlPSIjMzMzIi8+PHJlY3QgeD0iMjIwIiB5PSIyMjAiIHdpZHRoPSI2MCIgaGVpZ2h0PSI4MCIgZmlsbD0iIzY2YjJmZiIgc3Ryb2tlPSIjMzMzIi8+PHJlY3QgeD0iMTgwIiB5PSIzMDAiIHdpZHRoPSI0MCIgaGVpZ2h0PSI2MCIgZmlsbD0iIzhiNDUxMyIgc3Ryb2tlPSIjMzMzIi8+PC9zdmc+'
  },
  {
    id: 'apartment-building',
    name: 'Apartment Building',
    type: 'apartment',
    src: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjUwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNDAwIiBoZWlnaHQ9IjUwMCIgZmlsbD0iI2Y1ZjVmNSIvPjxyZWN0IHg9IjgwIiB5PSI1MCIgd2lkdGg9IjI0MCIgaGVpZ2h0PSI0MDAiIGZpbGw9IiNkZGRkZGQiIHN0cm9rZT0iIzk5OSIgc3Ryb2tlLXdpZHRoPSIzIi8+PHJlY3QgeD0iMTAwIiB5PSI4MCIgd2lkdGg9IjYwIiBoZWlnaHQ9IjUwIiBmaWxsPSIjYmFkZmZmIiBzdHJva2U9IiM2NjYiLz48cmVjdCB4PSIxODAiIHk9IjgwIiB3aWR0aD0iNjAiIGhlaWdodD0iNTAiIGZpbGw9IiNiYWRmZmYiIHN0cm9rZT0iIzY2NiIvPjxyZWN0IHg9IjI2MCIgeT0iODAiIHdpZHRoPSI2MCIgaGVpZ2h0PSI1MCIgZmlsbD0iI2JhZGZmZiIgc3Ryb2tlPSIjNjY2Ii8+PHJlY3QgeD0iMTAwIiB5PSIxNjAiIHdpZHRoPSI2MCIgaGVpZ2h0PSI1MCIgZmlsbD0iI2JhZGZmZiIgc3Ryb2tlPSIjNjY2Ii8+PHJlY3QgeD0iMTgwIiB5PSIxNjAiIHdpZHRoPSI2MCIgaGVpZ2h0PSI1MCIgZmlsbD0iI2JhZGZmZiIgc3Ryb2tlPSIjNjY2Ii8+PHJlY3QgeD0iMjYwIiB5PSIxNjAiIHdpZHRoPSI2MCIgaGVpZ2h0PSI1MCIgZmlsbD0iI2JhZGZmZiIgc3Ryb2tlPSIjNjY2Ii8+PHJlY3QgeD0iMTAwIiB5PSIyNDAiIHdpZHRoPSI2MCIgaGVpZ2h0PSI1MCIgZmlsbD0iI2JhZGZmZiIgc3Ryb2tlPSIjNjY2Ii8+PHJlY3QgeD0iMTgwIiB5PSIyNDAiIHdpZHRoPSI2MCIgaGVpZ2h0PSI1MCIgZmlsbD0iI2JhZGZmZiIgc3Ryb2tlPSIjNjY2Ii8+PHJlY3QgeD0iMjYwIiB5PSIyNDAiIHdpZHRoPSI2MCIgaGVpZ2h0PSI1MCIgZmlsbD0iI2JhZGZmZiIgc3Ryb2tlPSIjNjY2Ii8+PHJlY3QgeD0iMTgwIiB5PSIzNDAiIHdpZHRoPSI0MCIgaGVpZ2h0PSI2MCIgZmlsbD0iIzhhNTQyMyIgc3Ryb2tlPSIjMzMzIi8+PC9zdmc+'
  },
  {
    id: 'modern-villa',
    name: 'Modern Villa',
    type: 'villa',
    src: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgZmlsbD0iI2YwZjBmMCIvPjxyZWN0IHg9IjUwIiB5PSIxMDAiIHdpZHRoPSIzMDAiIGhlaWdodD0iMTgwIiBmaWxsPSIjZmZmIiBzdHJva2U9IiMzMzMiIHN0cm9rZS13aWR0aD0iNCIvPjxyZWN0IHg9IjgwIiB5PSIxMzAiIHdpZHRoPSIxMDAiIGhlaWdodD0iODAiIGZpbGw9IiMwMDYzMzMiIHN0cm9rZT0iIzMzMyIvPjxyZWN0IHg9IjIyMCIgeT0iMTMwIiB3aWR0aD0iMTAwIiBoZWlnaHQ9IjgwIiBmaWxsPSIjMDA2MzMzIiBzdHJva2U9IiMzMzMiLz48bGluZSB4MT0iNTAiIHkxPSIxMDAiIHgyPSIyMDAiIHkyPSI1MCIgc3Ryb2tlPSIjMzMzIiBzdHJva2Utd2lkdGg9IjMiLz48bGluZSB4MT0iMzUwIiB5MT0iMTAwIiB4Mj0iMjAwIiB5Mj0iNTAiIHN0cm9rZT0iIzMzMyIgc3Ryb2tlLXdpZHRoPSIzIi8+PC9zdmc+'
  },
  {
    id: 'simple-cube',
    name: 'Cube Test',
    type: 'cube',
    src: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2Y1ZjVmNSIvPjxyZWN0IHg9IjUwIiB5PSI1MCIgd2lkdGg9IjEwMCIgaGVpZ2h0PSIxMDAiIGZpbGw9IiM2MzY2ZjEiIHN0cm9rZT0iIzMzMyIgc3Ryb2tlLXdpZHRoPSIzIi8+PHRleHQgeD0iMTAwIiB5PSIxMTAiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZpbGw9IndoaXRlIiBmb250LXNpemU9IjE0IiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiI+Q1VCRTwvdGV4dD48L3N2Zz4='
  }
]

// 3D House Component
function House3D({ color = '#ffffff', wireframe = false }) {
  const groupRef = useRef()

  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.5) * 0.1
    }
  })

  return (
    <group ref={groupRef}>
      {/* Main house body */}
      <Box args={[2, 1.5, 2]} position={[0, 0.75, 0]}>
        <meshStandardMaterial color={color} wireframe={wireframe} />
      </Box>

      {/* Roof */}
      <group position={[0, 1.5, 0]}>
        {/* Pyramid roof using 4 triangular prisms */}
        <mesh position={[0, 0.5, 0]} rotation={[0, Math.PI / 4, 0]}>
          <coneGeometry args={[1.8, 1, 4]} />
          <meshStandardMaterial color='#8b4513' wireframe={wireframe} />
        </mesh>
      </group>

      {/* Door */}
      <Box args={[0.4, 0.8, 0.1]} position={[0, 0.4, 1.05]}>
        <meshStandardMaterial color='#654321' />
      </Box>

      {/* Windows */}
      <Box args={[0.5, 0.5, 0.1]} position={[-0.6, 1, 1.05]}>
        <meshStandardMaterial color='#87ceeb' />
      </Box>
      <Box args={[0.5, 0.5, 0.1]} position={[0.6, 1, 1.05]}>
        <meshStandardMaterial color='#87ceeb' />
      </Box>
      <Box args={[0.5, 0.5, 0.1]} position={[-0.6, 1, -1.05]}>
        <meshStandardMaterial color='#87ceeb' />
      </Box>
      <Box args={[0.5, 0.5, 0.1]} position={[0.6, 1, -1.05]}>
        <meshStandardMaterial color='#87ceeb' />
      </Box>

      {/* Chimney */}
      <Box args={[0.3, 0.8, 0.3]} position={[0.7, 2, -0.5]}>
        <meshStandardMaterial color='#666666' />
      </Box>
    </group>
  )
}

// 3D Apartment Building
function Apartment3D({ color = '#dddddd', wireframe = false }) {
  const groupRef = useRef()

  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.3) * 0.05
    }
  })

  return (
    <group ref={groupRef}>
      {/* Main building */}
      <Box args={[2, 4, 1.5]} position={[0, 2, 0]}>
        <meshStandardMaterial color={color} wireframe={wireframe} />
      </Box>

      {/* Windows - 4 floors, 3 windows per floor */}
      {[0, 1, 2, 3].map((floor) => (
        <group key={floor}>
          {[-0.6, 0, 0.6].map((x, i) => (
            <Box
              key={i}
              args={[0.3, 0.4, 0.05]}
              position={[x, 3.2 - floor * 0.9, 0.78]}
            >
              <meshStandardMaterial color='#badfff' />
            </Box>
          ))}
        </group>
      ))}

      {/* Entrance */}
      <Box args={[0.5, 0.8, 0.05]} position={[0, 0.4, 0.78]}>
        <meshStandardMaterial color='#8a5423' />
      </Box>
    </group>
  )
}

// 3D Villa
function Villa3D({ color = '#ffffff', wireframe = false }) {
  const groupRef = useRef()

  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.4) * 0.08
    }
  })

  return (
    <group ref={groupRef}>
      {/* Main structure - L shape */}
      <Box args={[2.5, 1.2, 1.5]} position={[-0.5, 0.6, 0]}>
        <meshStandardMaterial color={color} wireframe={wireframe} />
      </Box>
      <Box args={[1, 1.2, 1.5]} position={[1, 0.6, 0.5]}>
        <meshStandardMaterial color={color} wireframe={wireframe} />
      </Box>

      {/* Large windows */}
      <Box args={[1.8, 0.8, 0.05]} position={[-0.5, 0.8, 0.78]}>
        <meshStandardMaterial color='#006333' />
      </Box>
      <Box args={[0.7, 0.8, 0.05]} position={[1, 0.8, 1.28]}>
        <meshStandardMaterial color='#006333' />
      </Box>

      {/* Slanted roof */}
      <mesh position={[-0.5, 1.4, 0]} rotation={[0, 0, 0.2]}>
        <boxGeometry args={[2.7, 0.2, 1.7]} />
        <meshStandardMaterial color='#333333' />
      </mesh>
      <mesh position={[1, 1.4, 0.5]} rotation={[0, 0, -0.2]}>
        <boxGeometry args={[1.2, 0.2, 1.7]} />
        <meshStandardMaterial color='#333333' />
      </mesh>

      {/* Pool */}
      <Box args={[1.5, 0.1, 2]} position={[1.5, 0.05, -1]}>
        <meshStandardMaterial color='#4fc3f7' transparent opacity={0.8} />
      </Box>
    </group>
  )
}

// 3D Cube (for testing)
function Cube3D({ color = '#6366f1', wireframe = false }) {
  const meshRef = useRef()

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.x = state.clock.elapsedTime * 0.5
      meshRef.current.rotation.y = state.clock.elapsedTime * 0.3
    }
  })

  return (
    <Box ref={meshRef} args={[1.5, 1.5, 1.5]} position={[0, 0.75, 0]}>
      <meshStandardMaterial color={color} wireframe={wireframe} />
    </Box>
  )
}

// Scene Component
function Scene({ modelType, wireframe, color }) {
  const ModelComponent = {
    house: House3D,
    apartment: Apartment3D,
    villa: Villa3D,
    cube: Cube3D
  }[modelType] || House3D

  return (
    <>
      <PerspectiveCamera makeDefault position={[5, 5, 5]} />
      <OrbitControls enablePan={true} enableZoom={true} enableRotate={true} />
      <ambientLight intensity={0.5} />
      <directionalLight position={[10, 10, 5]} intensity={1} />
      <pointLight position={[-10, -10, -10]} intensity={0.5} />

      <ModelComponent wireframe={wireframe} color={color} />

      <Grid
        args={[20, 20]}
        position={[0, 0, 0]}
        cellSize={1}
        cellThickness={0.5}
        cellColor='#6b7280'
        sectionSize={5}
        sectionThickness={1}
        sectionColor='#9ca3af'
        fadeDistance={25}
        fadeStrength={1}
        followCamera={false}
        infiniteGrid={true}
      />

      {/* Ground plane */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.01, 0]}>
        <planeGeometry args={[20, 20]} />
        <meshStandardMaterial color='#f3f4f6' />
      </mesh>
    </>
  )
}

// Main Component
export function Structure3D() {
  const [selectedImage, setSelectedImage] = useState(null)
  const [generatedModel, setGeneratedModel] = useState(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [wireframe, setWireframe] = useState(false)
  const [modelColor, setModelColor] = useState('#ffffff')
  const [savedModels, setSavedModels] = useState([])
  const [showGallery, setShowGallery] = useState(false)
  const [currentModelName, setCurrentModelName] = useState('')
  const fileInputRef = useRef()

  const { save3DModel, get3DModel, getAll3DModels, delete3DModel } = useCacheStore()

  useEffect(() => {
    const all = getAll3DModels()
    setSavedModels(all)
  }, [])

  const handleImageUpload = (e) => {
    const file = e.target.files[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (event) => {
      const newImage = {
        id: `upload-${Date.now()}`,
        name: file.name,
        type: 'house',
        src: event.target.result
      }
      setSelectedImage(newImage)
      generateModel(newImage)
    }
    reader.readAsDataURL(file)
  }

  const selectTestImage = (image) => {
    setSelectedImage(image)
    generateModel(image)
  }

  const generateModel = (image) => {
    setIsGenerating(true)
    setCurrentModelName(`Generated from ${image.name}`)

    // Simulate AI processing delay
    setTimeout(() => {
      const modelData = {
        type: image.type || 'house',
        imageId: image.id,
        imageName: image.name,
        generatedAt: new Date().toISOString(),
        parameters: {
          width: 10,
          height: image.type === 'apartment' ? 16 : 8,
          depth: 10,
          rooms: image.type === 'apartment' ? 12 : 5,
          floors: image.type === 'apartment' ? 4 : 1
        }
      }
      setGeneratedModel(modelData)
      setIsGenerating(false)
    }, 1500)
  }

  const saveCurrentModel = () => {
    if (!generatedModel) return

    const id = `model-${Date.now()}`
    const modelData = {
      ...generatedModel,
      name: currentModelName || `Model ${savedModels.length + 1}`
    }

    save3DModel(id, modelData)
    setSavedModels(getAll3DModels())
    alert('3D Model saved to cache!')
  }

  const loadSavedModel = (id) => {
    const cached = get3DModel(id)
    if (cached) {
      setGeneratedModel(cached)
      setCurrentModelName(cached.name)
      const testImage = TEST_IMAGES.find(img => img.type === cached.type)
      if (testImage) {
        setSelectedImage(testImage)
      }
    }
  }

  const exportModel = () => {
    if (!generatedModel) return

    const dataStr = JSON.stringify(generatedModel, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${currentModelName.replace(/\s+/g, '-').toLowerCase()}.json`
    link.click()
    URL.revokeObjectURL(url)
  }

  const handleDelete = (id, e) => {
    e.stopPropagation()
    delete3DModel(id)
    setSavedModels(getAll3DModels())
  }

  const clearAll = () => {
    setSelectedImage(null)
    setGeneratedModel(null)
    setCurrentModelName('')
  }

  return (
    <div className="structure-3d-container">
      <div className="structure-3d-header">
        <h1>🏠 3D Structure Generator</h1>
        <p>Upload an image or select a template to generate a 3D model</p>
      </div>

      <div className="structure-3d-toolbar">
        <div className="toolbar-section">
          <input
            type="file"
            accept="image/*"
            ref={fileInputRef}
            onChange={handleImageUpload}
            style={{ display: 'none' }}
          />
          <button
            className="btn-action btn-primary"
            onClick={() => fileInputRef.current?.click()}
          >
            <FiUpload /> Upload Image
          </button>

          <button
            className="btn-action"
            onClick={() => setShowGallery(!showGallery)}
          >
            <FiLayers /> Templates
          </button>

          {generatedModel && (
            <>
              <button className="btn-action btn-success" onClick={saveCurrentModel}>
                <FiSave /> Save Model
              </button>
              <button className="btn-action" onClick={exportModel}>
                <FiDownload /> Export JSON
              </button>
              <button className="btn-action btn-danger" onClick={clearAll}>
                <FiTrash2 /> Clear
              </button>
            </>
          )}
        </div>

        {generatedModel && (
          <div className="toolbar-section">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={wireframe}
                onChange={(e) => setWireframe(e.target.checked)}
              />
              <FiBox /> Wireframe
            </label>

            <div className="color-picker">
              <label>Color:</label>
              <input
                type="color"
                value={modelColor}
                onChange={(e) => setModelColor(e.target.value)}
              />
            </div>
          </div>
        )}
      </div>

      {showGallery && (
        <div className="templates-gallery">
          <h3>🖼️ Sample Templates (Click to Generate)</h3>
          <div className="templates-grid">
            {TEST_IMAGES.map((image) => (
              <div
                key={image.id}
                className={`template-item ${selectedImage?.id === image.id ? 'selected' : ''}`}
                onClick={() => selectTestImage(image)}
              >
                <img src={image.src} alt={image.name} />
                <span>{image.name}</span>
                <small>{image.type}</small>
              </div>
            ))}
          </div>

          {savedModels.length > 0 && (
            <>
              <h3>💾 Saved Models</h3>
              <div className="templates-grid">
                {savedModels.map((model) => (
                  <div
                    key={model.id}
                    className="template-item saved-model"
                    onClick={() => loadSavedModel(model.id)}
                  >
                    <div className="model-icon"><FiBox size={40} /></div>
                    <span>{model.data?.name}</span>
                    <small>{model.data?.type} • {new Date(model.timestamp).toLocaleDateString()}</small>
                    <button
                      className="delete-model-btn"
                      onClick={(e) => handleDelete(model.id, e)}
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      <div className="structure-3d-content">
        {selectedImage && (
          <div className="image-preview-panel">
            <h4>📷 Source Image</h4>
            <img src={selectedImage.src} alt={selectedImage.name} />
            <div className="image-info">
              <p><strong>Name:</strong> {selectedImage.name}</p>
              <p><strong>Type:</strong> {selectedImage.type || 'house'}</p>
            </div>
          </div>
        )}

        <div className={`canvas-panel ${!selectedImage ? 'empty' : ''}`}>
          {isGenerating ? (
            <div className="generating-overlay">
              <div className="spinner"></div>
              <p>Generating 3D Structure...</p>
              <small>Analyzing image and building model</small>
            </div>
          ) : generatedModel ? (
            <>
              <div className="canvas-header">
                <input
                  type="text"
                  value={currentModelName}
                  onChange={(e) => setCurrentModelName(e.target.value)}
                  placeholder="Model name"
                  className="model-name-input"
                />
                <div className="model-stats">
                  <span><strong>Type:</strong> {generatedModel.type}</span>
                  <span><strong>Rooms:</strong> {generatedModel.parameters.rooms}</span>
                  <span><strong>Floors:</strong> {generatedModel.parameters.floors}</span>
                </div>
              </div>
              <div className="canvas-3d">
                <Canvas shadows camera={{ position: [8, 8, 8], fov: 45 }}>
                  <Suspense fallback={null}>
                    <Scene
                      modelType={generatedModel.type}
                      wireframe={wireframe}
                      color={modelColor}
                    />
                  </Suspense>
                </Canvas>
              </div>
              <div className="canvas-controls">
                <p><FiEye /> Left click to rotate • Right click to pan • Scroll to zoom</p>
              </div>
            </>
          ) : (
            <div className="empty-state">
              <FiBox size={64} color="#cbd5e1" />
              <h3>No 3D Model Generated</h3>
              <p>Upload an image or select a template to get started</p>
              <div className="test-buttons">
                <button className="btn-action btn-primary" onClick={() => selectTestImage(TEST_IMAGES[0])}>
                  Try House Demo
                </button>
                <button className="btn-action btn-primary" onClick={() => selectTestImage(TEST_IMAGES[1])}>
                  Try Apartment Demo
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="structure-3d-info">
        <h4>ℹ️ How it works</h4>
        <ul>
          <li>Upload a building elevation image or select a template</li>
          <li>The system analyzes the image to determine structure type</li>
          <li>A 3D model is generated based on the detected architecture</li>
          <li>Models are cached for quick access later</li>
          <li>Export JSON data for use in other applications</li>
        </ul>
        <p className="test-note">
          <strong>Test Mode:</strong> 4 sample templates available. All generated models are saved to local cache.
        </p>
      </div>
    </div>
  )
}

export default Structure3D
