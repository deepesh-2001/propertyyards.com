import React, { useState, useEffect } from 'react'
import { useCacheStore } from '../../stores/cacheStore'
import { testWhiteboards, test3DImages, testCacheHelpers } from '../../utils/testData'
import { FiCheck, FiX, FiDatabase, FiSave, FiTrash2, FiRefreshCw } from 'react-icons/fi'
import './TestFeatures.css'

export function TestFeatures() {
  const [testResults, setTestResults] = useState({})
  const [cacheStats, setCacheStats] = useState(null)

  const {
    getCacheStats,
    clearAllCaches,
    saveWhiteboard,
    getWhiteboard,
    getAllWhiteboards,
    deleteWhiteboard,
    save3DModel,
    get3DModel,
    getAll3DModels,
    delete3DModel,
    setApiCache,
    getApiCache
  } = useCacheStore()

  useEffect(() => {
    setCacheStats(getCacheStats())
  }, [])

  const runAllTests = async () => {
    const results = {}

    // Test 1: Cache Store Stats
    try {
      const stats = getCacheStats()
      results.cacheStats = { passed: true, data: stats }
    } catch (e) {
      results.cacheStats = { passed: false, error: e.message }
    }

    // Test 2: Save and Retrieve Whiteboard
    try {
      const testDrawing = testCacheHelpers.generateTestDrawing('Test Whiteboard')
      saveWhiteboard('test-whiteboard-1', testDrawing)
      const retrieved = getWhiteboard('test-whiteboard-1')
      results.whiteboardCache = {
        passed: retrieved?.data?.name === 'Test Whiteboard',
        data: retrieved
      }
    } catch (e) {
      results.whiteboardCache = { passed: false, error: e.message }
    }

    // Test 3: Save and Retrieve 3D Model
    try {
      const testModel = testCacheHelpers.generateTest3DModel('house', 'Test House Model')
      save3DModel('test-model-1', testModel)
      const retrieved = get3DModel('test-model-1')
      results.model3dCache = {
        passed: retrieved?.type === 'house',
        data: retrieved
      }
    } catch (e) {
      results.model3dCache = { passed: false, error: e.message }
    }

    // Test 4: API Cache with TTL
    try {
      setApiCache('test-api-key', { test: 'data' }, 1)
      const cached = getApiCache('test-api-key')
      results.apiCache = {
        passed: cached?.test === 'data',
        data: cached
      }
    } catch (e) {
      results.apiCache = { passed: false, error: e.message }
    }

    // Test 5: List All Whiteboards
    try {
      // Save multiple whiteboards
      testWhiteboards.forEach((wb, idx) => {
        saveWhiteboard(`test-wb-${idx}`, { name: wb.name, data: wb.data })
      })
      const all = getAllWhiteboards()
      results.listWhiteboards = {
        passed: all.length >= 2,
        data: all.length
      }
    } catch (e) {
      results.listWhiteboards = { passed: false, error: e.message }
    }

    // Test 6: List All 3D Models
    try {
      const all = getAll3DModels()
      results.listModels = {
        passed: all.length >= 1,
        data: all.length
      }
    } catch (e) {
      results.listModels = { passed: false, error: e.message }
    }

    setTestResults(results)
    setCacheStats(getCacheStats())
  }

  const handleClearCache = () => {
    if (confirm('Are you sure you want to clear all caches?')) {
      clearAllCaches()
      setTestResults({})
      setCacheStats(getCacheStats())
    }
  }

  const handleCleanupTestData = () => {
    // Delete test entries
    deleteWhiteboard('test-whiteboard-1')
    deleteWhiteboard('test-wb-0')
    deleteWhiteboard('test-wb-1')
    delete3DModel('test-model-1')
    setTestResults({})
    setCacheStats(getCacheStats())
  }

  return (
    <div className="test-features-container">
      <div className="test-header">
        <h1>🧪 Feature Testing Suite</h1>
        <p>Test Whiteboard, 3D Structure, and Cache functionality</p>
      </div>

      <div className="test-actions">
        <button className="btn-test btn-primary" onClick={runAllTests}>
          <FiRefreshCw /> Run All Tests
        </button>
        <button className="btn-test btn-danger" onClick={handleClearCache}>
          <FiTrash2 /> Clear All Cache
        </button>
        <button className="btn-test btn-secondary" onClick={handleCleanupTestData}>
          <FiTrash2 /> Cleanup Test Data
        </button>
      </div>

      {cacheStats && (
        <div className="cache-stats-panel">
          <h3><FiDatabase /> Current Cache Statistics</h3>
          <div className="stats-grid">
            <div className="stat-item">
              <span className="stat-value">{cacheStats.apiCacheSize}</span>
              <span className="stat-label">API Cache</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">{cacheStats.imageCacheSize}</span>
              <span className="stat-label">Image Cache</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">{cacheStats.whiteboardCacheSize}</span>
              <span className="stat-label">Whiteboards</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">{cacheStats.model3dCacheSize}</span>
              <span className="stat-label">3D Models</span>
            </div>
            <div className="stat-item total">
              <span className="stat-value">{(cacheStats.totalSize / 1024).toFixed(2)} KB</span>
              <span className="stat-label">Total Size</span>
            </div>
          </div>
        </div>
      )}

      {Object.keys(testResults).length > 0 && (
        <div className="test-results">
          <h3>Test Results</h3>
          <div className="results-list">
            {Object.entries(testResults).map(([testName, result]) => (
              <div key={testName} className={`test-item ${result.passed ? 'passed' : 'failed'}`}>
                <div className="test-status">
                  {result.passed ? <FiCheck className="icon-pass" /> : <FiX className="icon-fail" />}
                </div>
                <div className="test-info">
                  <span className="test-name">{testName.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}</span>
                  <span className="test-detail">
                    {result.passed
                      ? `Passed ${result.data ? `- Data: ${JSON.stringify(result.data).substring(0, 50)}...` : ''}`
                      : `Failed - ${result.error}`}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="test-data-preview">
        <h3>Available Test Data</h3>

        <div className="preview-section">
          <h4>Whiteboard Templates ({testWhiteboards.length})</h4>
          <div className="preview-grid">
            {testWhiteboards.map((item) => (
              <div key={item.id} className="preview-item">
                <img src={item.data} alt={item.name} />
                <span>{item.name}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="preview-section">
          <h4>3D Structure Images ({test3DImages.length})</h4>
          <div className="preview-grid">
            {test3DImages.map((item) => (
              <div key={item.id} className="preview-item">
                <img src={item.src} alt={item.name} />
                <span>{item.name}</span>
                <small>{item.type}</small>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="feature-links">
        <h3>Quick Links to Features</h3>
        <div className="links-grid">
          <a href="/whiteboard" className="feature-link">
            <span className="icon">🏗️</span>
            <span className="label">Whiteboard</span>
            <small>Drawing & Planning Tool</small>
          </a>
          <a href="/3d-structure" className="feature-link">
            <span className="icon">🏠</span>
            <span className="label">3D Structure</span>
            <small>Image to 3D Generator</small>
          </a>
        </div>
      </div>
    </div>
  )
}

export default TestFeatures
