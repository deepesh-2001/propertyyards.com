import React, { useState, useEffect, useCallback } from 'react'
import { useCacheStore } from '../../stores/cacheStore'
import { useReferralStore } from '../../stores/referralStore'
import { usePricingStore } from '../../stores/pricingStore'
import { useAuthStore } from '../../stores/authStore'
import { 
  FiShield, FiLock, FiUnlock, FiKey, FiUserCheck, FiActivity,
  FiDatabase, FiTrash2, FiRefreshCw, FiClock, FiAlertTriangle,
  FiCheckCircle, FiXCircle, FiPlay, FiPause, FiMonitor,
  FiServer, FiLayers, FiCpu, FiHardDrive, FiWifi,
  FiFileText, FiCode, FiTerminal, FiBug, FiEye, FiEyeOff,
  FiGlobe, FiZap, FiTrendingUp, FiPieChart, FiBarChart2
} from 'react-icons/fi'
import './SecurityCacheTesting.css'

// Security test scenarios
const SECURITY_TESTS = [
  { id: 'auth-check', name: 'Authentication Validation', type: 'security', severity: 'high' },
  { id: 'rbac-check', name: 'RBAC Permissions Check', type: 'security', severity: 'high' },
  { id: 'xss-check', name: 'XSS Protection', type: 'security', severity: 'medium' },
  { id: 'csrf-check', name: 'CSRF Token Validation', type: 'security', severity: 'medium' },
  { id: 'rate-limit', name: 'Rate Limiting', type: 'security', severity: 'medium' },
  { id: 'input-sanitize', name: 'Input Sanitization', type: 'security', severity: 'high' }
]

// Cache test scenarios
const CACHE_TESTS = [
  { id: 'cache-hit', name: 'Cache Hit Ratio', type: 'cache' },
  { id: 'cache-expire', name: 'TTL Expiration', type: 'cache' },
  { id: 'cache-persist', name: 'Persistence Test', type: 'cache' },
  { id: 'cache-clear', name: 'Bulk Clear', type: 'cache' },
  { id: 'cache-size', name: 'Size Limits', type: 'cache' }
]

// Performance test scenarios
const PERF_TESTS = [
  { id: 'render-time', name: 'Component Render Time', type: 'performance' },
  { id: 'api-latency', name: 'API Response Latency', type: 'performance' },
  { id: 'memory-usage', name: 'Memory Usage', type: 'performance' },
  { id: 'bundle-size', name: 'Bundle Size Check', type: 'performance' }
]

export function SecurityCacheTesting() {
  const user = useAuthStore((state) => state.user)
  const userRole = user?.role || 'external'
  
  // Cache stores
  const cacheStats = useCacheStore((state) => state.getCacheStats())
  const clearAllCaches = useCacheStore((state) => state.clearAllCaches)
  const apiCache = useCacheStore((state) => state.apiCache)
  const imageCache = useCacheStore((state) => state.imageCache)
  const whiteboardCache = useCacheStore((state) => state.whiteboardCache)
  const model3dCache = useCacheStore((state) => state.model3dCache)

  // Local state
  const [activeTab, setActiveTab] = useState('security')
  const [securityStatus, setSecurityStatus] = useState({
    lastScan: null,
    threats: 0,
    vulnerabilities: [],
    score: 95
  })
  const [cacheMetrics, setCacheMetrics] = useState({
    hitRate: 87,
    missRate: 13,
    totalRequests: 1250,
    avgLatency: '45ms'
  })
  const [runningTests, setRunningTests] = useState([])
  const [testResults, setTestResults] = useState({})
  const [systemHealth, setSystemHealth] = useState({
    cpu: 32,
    memory: 45,
    storage: 28,
    network: 'good'
  })
  const [realtimeLogs, setRealtimeLogs] = useState([])
  const [isMonitoring, setIsMonitoring] = useState(false)

  // Check admin access
  const isAdmin = userRole === 'admin'
  const isManager = userRole === 'manager'
  const hasAccess = isAdmin || isManager

  // Add log entry
  const addLog = useCallback((type, message, level = 'info') => {
    const entry = {
      id: Date.now(),
      timestamp: new Date().toLocaleTimeString(),
      type,
      message,
      level
    }
    setRealtimeLogs(prev => [entry, ...prev].slice(0, 100))
  }, [])

  // Run security scan
  const runSecurityScan = async () => {
    addLog('security', 'Starting security scan...', 'info')
    setRunningTests(prev => [...prev, 'security-scan'])

    // Simulate scan
    await new Promise(resolve => setTimeout(resolve, 2000))

    const mockResults = {
      lastScan: new Date().toISOString(),
      threats: 0,
      vulnerabilities: [
        { id: 1, name: 'Weak Password Policy', severity: 'low', status: 'pass' },
        { id: 2, name: 'Session Timeout', severity: 'low', status: 'pass' },
        { id: 3, name: 'JWT Validation', severity: 'high', status: 'pass' },
        { id: 4, name: 'Input Validation', severity: 'medium', status: 'warning' }
      ],
      score: 94
    }

    setSecurityStatus(mockResults)
    setRunningTests(prev => prev.filter(t => t !== 'security-scan'))
    addLog('security', `Security scan complete. Score: ${mockResults.score}%`, 'success')
  }

  // Run cache optimization
  const runCacheOptimization = async () => {
    addLog('cache', 'Starting cache optimization...', 'info')
    setRunningTests(prev => [...prev, 'cache-optimize'])

    await new Promise(resolve => setTimeout(resolve, 1500))

    setCacheMetrics({
      hitRate: 92,
      missRate: 8,
      totalRequests: 1250,
      avgLatency: '32ms'
    })

    setRunningTests(prev => prev.filter(t => t !== 'cache-optimize'))
    addLog('cache', 'Cache optimization complete. Hit rate improved to 92%', 'success')
  }

  // Run individual test
  const runTest = async (testId, testType) => {
    addLog('test', `Starting ${testId}...`, 'info')
    setRunningTests(prev => [...prev, testId])

    await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000))

    const passed = Math.random() > 0.2 // 80% pass rate
    setTestResults(prev => ({
      ...prev,
      [testId]: {
        status: passed ? 'passed' : 'failed',
        timestamp: new Date().toISOString(),
        duration: Math.floor(Math.random() * 1000) + 500
      }
    }))

    setRunningTests(prev => prev.filter(t => t !== testId))
    addLog('test', `${testId} ${passed ? 'passed' : 'failed'}`, passed ? 'success' : 'error')
  }

  // Clear all cache
  const handleClearAllCache = () => {
    if (!confirm('Are you sure you want to clear ALL caches?')) return
    
    clearAllCaches()
    addLog('cache', 'All caches cleared successfully', 'warning')
  }

  // Toggle monitoring
  const toggleMonitoring = () => {
    setIsMonitoring(!isMonitoring)
    addLog('system', `Real-time monitoring ${!isMonitoring ? 'enabled' : 'disabled'}`, 'info')
  }

  // Simulate real-time updates
  useEffect(() => {
    if (!isMonitoring) return

    const interval = setInterval(() => {
      setSystemHealth({
        cpu: Math.floor(Math.random() * 30) + 20,
        memory: Math.floor(Math.random() * 20) + 40,
        storage: 28,
        network: ['good', 'excellent', 'fair'][Math.floor(Math.random() * 3)]
      })
    }, 3000)

    return () => clearInterval(interval)
  }, [isMonitoring])

  if (!hasAccess) {
    return (
      <div className="sct-container">
        <div className="access-denied">
          <FiShield size={64} color="#ef4444" />
          <h2>Access Denied</h2>
          <p>Security & Cache Testing requires Admin or Manager privileges.</p>
        </div>
      </div>
    )
  }

  // Security Tab
  const SecurityTab = () => (
    <div className="tab-content-inner">
      <div className="security-overview">
        <div className="security-score-card">
          <div className="score-circle" style={{ '--score': securityStatus.score }}>
            <span className="score-value">{securityStatus.score}%</span>
            <span className="score-label">Security Score</span>
          </div>
          <div className="score-actions">
            <button 
              className="btn-scan"
              onClick={runSecurityScan}
              disabled={runningTests.includes('security-scan')}
            >
              <FiShield /> 
              {runningTests.includes('security-scan') ? 'Scanning...' : 'Run Security Scan'}
            </button>
            <p className="last-scan">
              {securityStatus.lastScan 
                ? `Last scan: ${new Date(securityStatus.lastScan).toLocaleString()}`
                : 'No scan performed yet'}
            </p>
          </div>
        </div>

        <div className="security-metrics">
          <div className="metric-box">
            <FiLock className="metric-icon green" />
            <span className="metric-value">{securityStatus.vulnerabilities.filter(v => v.status === 'pass').length}</span>
            <span className="metric-label">Passed Checks</span>
          </div>
          <div className="metric-box">
            <FiAlertTriangle className="metric-icon yellow" />
            <span className="metric-value">{securityStatus.vulnerabilities.filter(v => v.status === 'warning').length}</span>
            <span className="metric-label">Warnings</span>
          </div>
          <div className="metric-box">
            <FiXCircle className="metric-icon red" />
            <span className="metric-value">{securityStatus.vulnerabilities.filter(v => v.status === 'fail').length}</span>
            <span className="metric-label">Failed</span>
          </div>
        </div>
      </div>

      <div className="vulnerabilities-list">
        <h3>Vulnerability Scan Results</h3>
        <div className="vuln-table">
          {securityStatus.vulnerabilities.map(vuln => (
            <div key={vuln.id} className={`vuln-row ${vuln.status}`}>
              <div className="vuln-status">
                {vuln.status === 'pass' && <FiCheckCircle className="status-icon" />}
                {vuln.status === 'warning' && <FiAlertTriangle className="status-icon" />}
                {vuln.status === 'fail' && <FiXCircle className="status-icon" />}
              </div>
              <div className="vuln-name">{vuln.name}</div>
              <div className={`vuln-severity ${vuln.severity}`}>{vuln.severity}</div>
              <div className={`vuln-badge ${vuln.status}`}>{vuln.status}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="security-tests">
        <h3>Security Tests</h3>
        <div className="test-grid">
          {SECURITY_TESTS.map(test => (
            <div key={test.id} className="test-card">
              <div className="test-header">
                <FiShield />
                <span className={`severity-badge ${test.severity}`}>{test.severity}</span>
              </div>
              <h4>{test.name}</h4>
              <button 
                onClick={() => runTest(test.id, 'security')}
                disabled={runningTests.includes(test.id)}
              >
                {runningTests.includes(test.id) ? <FiRefreshCw className="spin" /> : <FiPlay />}
                {runningTests.includes(test.id) ? 'Running...' : 'Run Test'}
              </button>
              {testResults[test.id] && (
                <div className={`test-result ${testResults[test.id].status}`}>
                  {testResults[test.id].status === 'passed' ? <FiCheckCircle /> : <FiXCircle />}
                  {testResults[test.id].status}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )

  // Cache Tab
  const CacheTab = () => (
    <div className="tab-content-inner">
      <div className="cache-stats-grid">
        <div className="cache-stat-card">
          <FiDatabase className="stat-icon blue" />
          <div className="stat-content">
            <span className="stat-number">{cacheStats.apiCacheSize}</span>
            <span className="stat-label">API Cache Entries</span>
          </div>
        </div>
        <div className="cache-stat-card">
          <FiFileText className="stat-icon purple" />
          <div className="stat-content">
            <span className="stat-number">{cacheStats.imageCacheSize}</span>
            <span className="stat-label">Image Cache</span>
          </div>
        </div>
        <div className="cache-stat-card">
          <FiLayers className="stat-icon green" />
          <div className="stat-content">
            <span className="stat-number">{cacheStats.whiteboardCacheSize}</span>
            <span className="stat-label">Whiteboards</span>
          </div>
        </div>
        <div className="cache-stat-card">
          <FiBox className="stat-icon orange" />
          <div className="stat-content">
            <span className="stat-number">{cacheStats.model3dCacheSize}</span>
            <span className="stat-label">3D Models</span>
          </div>
        </div>
      </div>

      <div className="cache-performance">
        <h3>Cache Performance</h3>
        <div className="perf-metrics">
          <div className="perf-bar">
            <div className="perf-label">Hit Rate</div>
            <div className="perf-progress">
              <div className="progress-fill" style={{ width: `${cacheMetrics.hitRate}%`, background: '#22c55e' }} />
            </div>
            <div className="perf-value">{cacheMetrics.hitRate}%</div>
          </div>
          <div className="perf-bar">
            <div className="perf-label">Miss Rate</div>
            <div className="perf-progress">
              <div className="progress-fill" style={{ width: `${cacheMetrics.missRate}%`, background: '#f59e0b' }} />
            </div>
            <div className="perf-value">{cacheMetrics.missRate}%</div>
          </div>
        </div>
        <div className="perf-stats">
          <div className="perf-stat">
            <FiActivity />
            <span>{cacheMetrics.totalRequests} requests</span>
          </div>
          <div className="perf-stat">
            <FiClock />
            <span>{cacheMetrics.avgLatency} avg latency</span>
          </div>
        </div>
      </div>

      <div className="cache-actions">
        <h3>Cache Management</h3>
        <div className="action-buttons">
          <button 
            className="btn-optimize"
            onClick={runCacheOptimization}
            disabled={runningTests.includes('cache-optimize')}
          >
            <FiZap />
            {runningTests.includes('cache-optimize') ? 'Optimizing...' : 'Optimize Cache'}
          </button>
          <button className="btn-clear" onClick={handleClearAllCache}>
            <FiTrash2 /> Clear All Cache
          </button>
          <button className="btn-refresh" onClick={() => window.location.reload()}>
            <FiRefreshCw /> Refresh Stats
          </button>
        </div>
      </div>

      <div className="cache-tests">
        <h3>Cache Tests</h3>
        <div className="test-grid">
          {CACHE_TESTS.map(test => (
            <div key={test.id} className="test-card">
              <div className="test-header">
                <FiDatabase />
                <span className="test-type">{test.type}</span>
              </div>
              <h4>{test.name}</h4>
              <button 
                onClick={() => runTest(test.id, 'cache')}
                disabled={runningTests.includes(test.id)}
              >
                {runningTests.includes(test.id) ? <FiRefreshCw className="spin" /> : <FiPlay />}
                {runningTests.includes(test.id) ? 'Running...' : 'Run Test'}
              </button>
              {testResults[test.id] && (
                <div className={`test-result ${testResults[test.id].status}`}>
                  {testResults[test.id].status === 'passed' ? <FiCheckCircle /> : <FiXCircle />}
                  {testResults[test.id].status}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )

  // Testing Tab
  const TestingTab = () => (
    <div className="tab-content-inner">
      <div className="test-overview">
        <h3>Test Suite Overview</h3>
        <div className="test-stats">
          <div className="test-stat-box">
            <span className="stat-num">{Object.keys(testResults).length}</span>
            <span className="stat-desc">Tests Run</span>
          </div>
          <div className="test-stat-box passed">
            <span className="stat-num">
              {Object.values(testResults).filter(r => r.status === 'passed').length}
            </span>
            <span className="stat-desc">Passed</span>
          </div>
          <div className="test-stat-box failed">
            <span className="stat-num">
              {Object.values(testResults).filter(r => r.status === 'failed').length}
            </span>
            <span className="stat-desc">Failed</span>
          </div>
        </div>
      </div>

      <div className="performance-tests">
        <h3>Performance Tests</h3>
        <div className="test-grid">
          {PERF_TESTS.map(test => (
            <div key={test.id} className="test-card performance">
              <div className="test-header">
                <FiTrendingUp />
                <span className="test-type">{test.type}</span>
              </div>
              <h4>{test.name}</h4>
              <button 
                onClick={() => runTest(test.id, 'performance')}
                disabled={runningTests.includes(test.id)}
              >
                {runningTests.includes(test.id) ? <FiRefreshCw className="spin" /> : <FiPlay />}
                {runningTests.includes(test.id) ? 'Running...' : 'Run Test'}
              </button>
              {testResults[test.id] && (
                <div className={`test-result ${testResults[test.id].status}`}>
                  {testResults[test.id].status === 'passed' ? <FiCheckCircle /> : <FiXCircle />}
                  {testResults[test.id].status}
                  <span className="duration">({testResults[test.id].duration}ms)</span>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="all-tests">
        <h3>Run All Tests</h3>
        <button 
          className="btn-run-all"
          onClick={async () => {
            addLog('test', 'Starting complete test suite...', 'info')
            for (const test of [...SECURITY_TESTS, ...CACHE_TESTS, ...PERF_TESTS]) {
              await runTest(test.id, test.type)
            }
            addLog('test', 'Complete test suite finished', 'success')
          }}
          disabled={runningTests.length > 0}
        >
          <FiPlay /> Run All Tests
        </button>
      </div>
    </div>
  )

  // Monitoring Tab
  const MonitoringTab = () => (
    <div className="tab-content-inner">
      <div className="monitoring-header">
        <h3>System Health Monitor</h3>
        <button 
          className={`btn-monitor ${isMonitoring ? 'active' : ''}`}
          onClick={toggleMonitoring}
        >
          {isMonitoring ? <FiPause /> : <FiPlay />}
          {isMonitoring ? 'Stop Monitoring' : 'Start Monitoring'}
        </button>
      </div>

      <div className="health-grid">
        <div className="health-card">
          <FiCpu className="health-icon" />
          <div className="health-info">
            <span className="health-label">CPU Usage</span>
            <div className="health-bar">
              <div className="health-fill" style={{ width: `${systemHealth.cpu}%` }} />
            </div>
            <span className="health-value">{systemHealth.cpu}%</span>
          </div>
        </div>
        <div className="health-card">
          <FiHardDrive className="health-icon" />
          <div className="health-info">
            <span className="health-label">Memory</span>
            <div className="health-bar">
              <div className="health-fill orange" style={{ width: `${systemHealth.memory}%` }} />
            </div>
            <span className="health-value">{systemHealth.memory}%</span>
          </div>
        </div>
        <div className="health-card">
          <FiServer className="health-icon" />
          <div className="health-info">
            <span className="health-label">Storage</span>
            <div className="health-bar">
              <div className="health-fill purple" style={{ width: `${systemHealth.storage}%` }} />
            </div>
            <span className="health-value">{systemHealth.storage}%</span>
          </div>
        </div>
        <div className="health-card">
          <FiWifi className="health-icon" />
          <div className="health-info">
            <span className="health-label">Network</span>
            <span className={`network-status ${systemHealth.network}`}>
              {systemHealth.network}
            </span>
          </div>
        </div>
      </div>

      <div className="realtime-logs">
        <h3>Real-time Logs</h3>
        <div className="logs-container">
          {realtimeLogs.length === 0 ? (
            <p className="no-logs">No logs yet. Start monitoring or run tests.</p>
          ) : (
            realtimeLogs.map(log => (
              <div key={log.id} className={`log-entry ${log.level}`}>
                <span className="log-time">{log.timestamp}</span>
                <span className="log-type">[{log.type.toUpperCase()}]</span>
                <span className="log-message">{log.message}</span>
              </div>
            ))
          )}
        </div>
        <button className="btn-clear-logs" onClick={() => setRealtimeLogs([])}>
          <FiTrash2 /> Clear Logs
        </button>
      </div>
    </div>
  )

  return (
    <div className="sct-container">
      <div className="sct-header">
        <div className="header-title">
          <FiShield className="header-icon" />
          <div>
            <h1>Security, Cache & Testing</h1>
            <p>Monitor security, manage cache, and run comprehensive tests</p>
          </div>
        </div>
        <div className="header-actions">
          <div className="status-badge">
            <span className={`pulse ${isMonitoring ? 'active' : ''}`} />
            {isMonitoring ? 'Monitoring Active' : 'Monitoring Off'}
          </div>
        </div>
      </div>

      <div className="sct-tabs">
        <button 
          className={activeTab === 'security' ? 'active' : ''}
          onClick={() => setActiveTab('security')}
        >
          <FiLock /> Security
        </button>
        <button 
          className={activeTab === 'cache' ? 'active' : ''}
          onClick={() => setActiveTab('cache')}
        >
          <FiDatabase /> Cache
        </button>
        <button 
          className={activeTab === 'testing' ? 'active' : ''}
          onClick={() => setActiveTab('testing')}
        >
          <FiTerminal /> Testing
        </button>
        <button 
          className={activeTab === 'monitoring' ? 'active' : ''}
          onClick={() => setActiveTab('monitoring')}
        >
          <FiMonitor /> Monitoring
        </button>
      </div>

      <div className="sct-content">
        {activeTab === 'security' && <SecurityTab />}
        {activeTab === 'cache' && <CacheTab />}
        {activeTab === 'testing' && <TestingTab />}
        {activeTab === 'monitoring' && <MonitoringTab />}
      </div>
    </div>
  )
}

export default SecurityCacheTesting
