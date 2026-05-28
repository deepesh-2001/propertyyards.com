import React, { useState, useEffect } from 'react'
import { useSEOStore } from '../../stores/seoStore'
import { useAuthStore } from '../../stores/authStore'
import { 
  FiSearch, FiTrendingUp, FiBarChart2, FiGlobe, FiZap,
  FiCheckCircle, FiAlertTriangle, FiActivity, FiTarget,
  FiCpu, FiAward, FiEye, FiDownload, FiRefreshCw, FiRobot
} from 'react-icons/fi'
import './SEODashboard.css'

const ENGINES = [
  { name: 'Google', icon: '🔍', color: '#4285f4' },
  { name: 'Bing', icon: '🔎', color: '#008373' },
  { name: 'Yahoo', icon: '🌐', color: '#6001d2' }
]

export function SEODashboard() {
  const user = useAuthStore((state) => state.user)
  const userRole = user?.role || 'external'
  
  const {
    seoScore,
    rankings,
    siteHealth,
    pageAnalysis,
    keywords,
    aiRecommendations,
    optimizationHistory,
    isAnalyzing,
    isOptimizing,
    runAIAnalysis,
    autoOptimize,
    updateRankings,
    generateReport,
    getCompetitorAnalysis
  } = useSEOStore()

  const [activeTab, setActiveTab] = useState('overview')
  const [competitors, setCompetitors] = useState([])
  const [newKeyword, setNewKeyword] = useState('')
  const [showOptimizationModal, setShowOptimizationModal] = useState(false)
  const [lastOptimization, setLastOptimization] = useState(null)

  // Check access - Admin and Manager only
  const hasAccess = ['admin', 'manager'].includes(userRole)

  useEffect(() => {
    if (hasAccess) {
      loadCompetitors()
    }
  }, [hasAccess])

  const loadCompetitors = async () => {
    const data = await getCompetitorAnalysis()
    setCompetitors(data)
  }

  const handleOptimize = async () => {
    const result = await autoOptimize()
    setLastOptimization(result)
    setShowOptimizationModal(true)
  }

  const handleExportReport = () => {
    const report = generateReport()
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `seo-report-${new Date().toISOString().split('T')[0]}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  if (!hasAccess) {
    return (
      <div className="seo-dashboard">
        <div className="access-denied">
          <FiSearch size={64} />
          <h2>Access Denied</h2>
          <p>SEO Dashboard requires Admin or Manager privileges.</p>
        </div>
      </div>
    )
  }

  // Overview Tab
  const OverviewTab = () => (
    <div className="seo-overview">
      {/* SEO Score Card */}
      <div className="score-section">
        <div className="main-score-card">
          <div className="score-circle-large" style={{ '--score': seoScore }}>
            <svg viewBox="0 0 36 36" className="circular-chart">
              <path
                className="circle-bg"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                className="circle"
                strokeDasharray={`${seoScore}, 100`}
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
            </svg>
            <div className="score-content">
              <span className="score-number">{seoScore}</span>
              <span className="score-label">SEO Score</span>
            </div>
          </div>
          <div className="score-actions">
            <button 
              className="btn-ai-analyze"
              onClick={runAIAnalysis}
              disabled={isAnalyzing}
            >
              <FiRobot />
              {isAnalyzing ? 'AI Analyzing...' : 'Run AI Analysis'}
            </button>
            <button 
              className="btn-ai-optimize"
              onClick={handleOptimize}
              disabled={isOptimizing}
            >
              <FiZap />
              {isOptimizing ? 'AI Optimizing...' : 'Auto-Optimize with AI'}
            </button>
          </div>
        </div>

        {/* Site Health */}
        <div className="health-cards">
          {Object.entries(siteHealth).map(([key, value]) => (
            <div key={key} className="health-mini-card">
              <div className="health-mini-bar">
                <div className="health-fill" style={{ width: `${value}%` }} />
              </div>
              <span className="health-name">{key.replace(/([A-Z])/g, ' $1').trim()}</span>
              <span className="health-score">{value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Rankings */}
      <div className="rankings-section">
        <h3>Search Engine Rankings</h3>
        <div className="rankings-grid">
          {ENGINES.map((engine, idx) => {
            const rankData = rankings[engine.name.toLowerCase()]
            return (
              <div key={engine.name} className="ranking-card">
                <div className="engine-header">
                  <span className="engine-icon" style={{ color: engine.color }}>{engine.icon}</span>
                  <span className="engine-name">{engine.name}</span>
                </div>
                <div className="rank-position">
                  <span className="position">#{rankData.position}</span>
                  <span className={`change ${rankData.change > 0 ? 'up' : 'down'}`}>
                    {rankData.change > 0 ? '↑' : '↓'} {Math.abs(rankData.change)}
                  </span>
                </div>
                <div className="rank-keywords">
                  <FiTarget /> {rankData.keywords} keywords tracked
                </div>
              </div>
            )
          })}
        </div>
        <button className="btn-refresh-rankings" onClick={updateRankings}>
          <FiRefreshCw /> Refresh Rankings
        </button>
      </div>
    </div>
  )

  // Keywords Tab
  const KeywordsTab = () => (
    <div className="keywords-section">
      <div className="keywords-header">
        <h3>Keyword Rankings</h3>
        <div className="keyword-add">
          <input 
            type="text" 
            placeholder="Add new keyword to track..."
            value={newKeyword}
            onChange={(e) => setNewKeyword(e.target.value)}
          />
          <button onClick={() => { setNewKeyword(''); }}>
            <FiSearch /> Track
          </button>
        </div>
      </div>
      
      <div className="keywords-table">
        <div className="keywords-header-row">
          <span>Keyword</span>
          <span>Search Volume</span>
          <span>Difficulty</span>
          <span>Current Rank</span>
          <span>Target</span>
          <span>Progress</span>
        </div>
        {keywords.map((kw, idx) => (
          <div key={idx} className="keyword-row">
            <span className="kw-term">{kw.term}</span>
            <span className="kw-volume">{kw.volume.toLocaleString()}</span>
            <span className={`kw-difficulty ${kw.difficulty > 60 ? 'hard' : kw.difficulty > 40 ? 'medium' : 'easy'}`}>
              {kw.difficulty}%
            </span>
            <span className={`kw-rank ${kw.currentRank <= 3 ? 'top' : kw.currentRank <= 10 ? 'good' : ''}`}>
              #{kw.currentRank}
            </span>
            <span className="kw-target">#{kw.target}</span>
            <div className="kw-progress">
              <div 
                className="progress-bar" 
                style={{ width: `${Math.max(0, 100 - (kw.currentRank * 5))}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  )

  // Analysis Tab
  const AnalysisTab = () => (
    <div className="analysis-section">
      <h3>AI SEO Analysis</h3>
      
      <div className="issues-list">
        {pageAnalysis.length === 0 ? (
          <p className="no-data">Run AI Analysis to see detailed SEO issues and recommendations</p>
        ) : (
          pageAnalysis.map((issue, idx) => (
            <div key={idx} className={`issue-card ${issue.type}`}>
              <div className="issue-icon">
                {issue.type === 'critical' && <FiAlertTriangle />}
                {issue.type === 'warning' && <FiActivity />}
                {issue.type === 'info' && <FiEye />}
              </div>
              <div className="issue-content">
                <h4>{issue.issue}</h4>
                <span className="issue-impact">Impact: {issue.impact}</span>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="ai-recommendations">
        <h4>AI-Powered Recommendations</h4>
        <div className="recommendations-list">
          {aiRecommendations.length === 0 ? (
            <p>Run AI Analysis to get personalized recommendations</p>
          ) : (
            aiRecommendations.map((rec, idx) => (
              <div key={idx} className="recommendation-item">
                <FiCheckCircle className="rec-icon" />
                <span>{rec}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )

  // Competitors Tab
  const CompetitorsTab = () => (
    <div className="competitors-section">
      <h3>Competitor Analysis</h3>
      <div className="competitors-chart">
        {competitors.map((comp, idx) => (
          <div key={idx} className="competitor-bar">
            <div className="comp-name">{comp.name}</div>
            <div className="comp-bar-container">
              <div 
                className={`comp-bar ${comp.name === 'Your Site' ? 'yours' : ''}`}
                style={{ width: `${(comp.domainAuthority / 100) * 100}%` }}
              />
            </div>
            <div className="comp-stats">
              <span className="comp-da">DA: {comp.domainAuthority}</span>
              <span className="comp-backlinks">{comp.backlinks.toLocaleString()} backlinks</span>
            </div>
          </div>
        ))}
      </div>
      
      <div className="competitor-insights">
        <h4>AI Insights</h4>
        <ul>
          <li>Your site ranks #4 in domain authority among competitors</li>
          <li>Top opportunity: Increase backlinks by 5x to match industry leaders</li>
          <li>Unique advantage: Leading in "3D property view" niche keyword</li>
          <li>Recommendation: Focus on long-tail keywords with lower competition</li>
        </ul>
      </div>
    </div>
  )

  // History Tab
  const HistoryTab = () => (
    <div className="history-section">
      <h3>Optimization History</h3>
      {optimizationHistory.length === 0 ? (
        <p className="no-data">No optimizations performed yet. Run Auto-Optimize to see history.</p>
      ) : (
        <div className="history-timeline">
          {optimizationHistory.map((hist, idx) => (
            <div key={idx} className="history-item">
              <div className="history-date">
                {new Date(hist.date).toLocaleDateString()}
              </div>
              <div className="history-changes">
                {hist.optimizations.map((opt, i) => (
                  <div key={i} className="change-item">
                    <FiCheckCircle /> {opt.action} <span className="improvement">{opt.improvement}</span>
                  </div>
                ))}
              </div>
              <div className="history-score">
                <span className="before">{hist.scoreBefore}</span>
                <span className="arrow">→</span>
                <span className="after">{hist.scoreAfter}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )

  return (
    <div className="seo-dashboard">
      <div className="seo-header">
        <div className="header-title">
          <FiSearch className="header-icon" />
          <div>
            <h1>AI SEO Dashboard</h1>
            <p>AI-powered SEO optimization and ranking analysis</p>
          </div>
        </div>
        <div className="header-actions">
          <button className="btn-export" onClick={handleExportReport}>
            <FiDownload /> Export Report
          </button>
        </div>
      </div>

      <div className="seo-tabs">
        <button className={activeTab === 'overview' ? 'active' : ''} onClick={() => setActiveTab('overview')}>
          <FiBarChart2 /> Overview
        </button>
        <button className={activeTab === 'keywords' ? 'active' : ''} onClick={() => setActiveTab('keywords')}>
          <FiTarget /> Keywords
        </button>
        <button className={activeTab === 'analysis' ? 'active' : ''} onClick={() => setActiveTab('analysis')}>
          <FiActivity /> AI Analysis
        </button>
        <button className={activeTab === 'competitors' ? 'active' : ''} onClick={() => setActiveTab('competitors')}>
          <FiGlobe /> Competitors
        </button>
        <button className={activeTab === 'history' ? 'active' : ''} onClick={() => setActiveTab('history')}>
          <FiTrendingUp /> History
        </button>
      </div>

      <div className="seo-content">
        {activeTab === 'overview' && <OverviewTab />}
        {activeTab === 'keywords' && <KeywordsTab />}
        {activeTab === 'analysis' && <AnalysisTab />}
        {activeTab === 'competitors' && <CompetitorsTab />}
        {activeTab === 'history' && <HistoryTab />}
      </div>

      {/* Optimization Modal */}
      {showOptimizationModal && lastOptimization && (
        <div className="modal-overlay" onClick={() => setShowOptimizationModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>✨ AI Optimization Complete!</h2>
            <div className="optimization-results">
              {lastOptimization.map((opt, idx) => (
                <div key={idx} className="opt-item">
                  <FiCheckCircle className="opt-icon" />
                  <span className="opt-action">{opt.action}</span>
                  <span className="opt-improvement">{opt.improvement}</span>
                </div>
              ))}
            </div>
            <button className="btn-close-modal" onClick={() => setShowOptimizationModal(false)}>
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default SEODashboard
