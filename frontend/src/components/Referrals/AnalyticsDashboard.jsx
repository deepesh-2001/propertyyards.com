import React, { useState, useEffect, useRef } from 'react'
import { useReferralStore } from '../../stores/referralStore'
import { useAuthStore } from '../../stores/authStore'
import { useAccessControl, canViewAnalytics, canExportData } from '../../utils/accessControl'
import { FiDownload, FiFileText, FiFile, FiTrendingUp, FiUsers, FiDollarSign, FiPercent, FiBarChart2 } from 'react-icons/fi'
import { Bar, Line, Doughnut } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import './AnalyticsDashboard.css'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

const TIME_RANGES = [
  { value: '7d', label: 'Last 7 Days' },
  { value: '30d', label: 'Last 30 Days' },
  { value: '90d', label: 'Last 90 Days' },
  { value: '1y', label: 'Last Year' },
  { value: 'all', label: 'All Time' }
]

export function AnalyticsDashboard() {
  const user = useAuthStore((state) => state.user)
  const userRole = user?.role || 'external'
  const access = useAccessControl(userRole)

  const { referrals, calculateAnalytics, getExportData } = useReferralStore()
  const [timeRange, setTimeRange] = useState('30d')
  const [analytics, setAnalytics] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')
  const chartsRef = useRef(null)

  useEffect(() => {
    if (canViewAnalytics(userRole)) {
      const data = calculateAnalytics(timeRange)
      setAnalytics(data)
    }
  }, [timeRange, referrals, userRole])

  // Check access
  if (!canViewAnalytics(userRole)) {
    return (
      <div className="analytics-dashboard">
        <div className="access-denied">
          <FiBarChart2 size={64} />
          <h2>Access Denied</h2>
          <p>You do not have permission to view analytics. Please contact your administrator.</p>
        </div>
      </div>
    )
  }

  const handleExportPDF = () => {
    if (!canExportData(userRole)) {
      alert('You do not have permission to export data')
      return
    }

    // Generate PDF report (simplified version - prints the page)
    const printWindow = window.open('', '_blank')
    const reportHTML = `
      <html>
        <head>
          <title>Referral Analytics Report</title>
          <style>
            body { font-family: Arial, sans-serif; padding: 40px; }
            h1 { color: #1e293b; }
            .stat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 30px 0; }
            .stat-box { background: #f8fafc; padding: 20px; border-radius: 8px; text-align: center; }
            .stat-value { font-size: 32px; font-weight: bold; color: #3b82f6; }
            .stat-label { color: #64748b; margin-top: 8px; }
            table { width: 100%; border-collapse: collapse; margin-top: 30px; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #e2e8f0; }
            th { background: #f1f5f9; font-weight: 600; }
            .footer { margin-top: 40px; color: #94a3b8; font-size: 12px; }
          </style>
        </head>
        <body>
          <h1>Referral Analytics Report</h1>
          <p>Generated on: ${new Date().toLocaleString()}</p>
          <p>Time Range: ${TIME_RANGES.find(t => t.value === timeRange)?.label}</p>

          <div class="stat-grid">
            <div class="stat-box">
              <div class="stat-value">${analytics?.totalReferrals || 0}</div>
              <div class="stat-label">Total Referrals</div>
            </div>
            <div class="stat-box">
              <div class="stat-value">$${(analytics?.totalEarnings || 0).toLocaleString()}</div>
              <div class="stat-label">Total Earnings</div>
            </div>
            <div class="stat-box">
              <div class="stat-value">${analytics?.conversionRate || 0}%</div>
              <div class="stat-label">Conversion Rate</div>
            </div>
          </div>

          <h2>Top Referrers</h2>
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Referrals</th>
                <th>Converted</th>
                <th>Earnings</th>
              </tr>
            </thead>
            <tbody>
              ${analytics?.topReferrers?.map(r => `
                <tr>
                  <td>${r.name}</td>
                  <td>${r.totalReferrals}</td>
                  <td>${r.converted}</td>
                  <td>$${r.earnings.toLocaleString()}</td>
                </tr>
              `).join('') || '<tr><td colspan="4">No data</td></tr>'}
            </tbody>
          </table>

          <div class="footer">
            PropertyYards.com - Confidential Report
          </div>
        </body>
      </html>
    `
    printWindow.document.write(reportHTML)
    printWindow.document.close()
    printWindow.print()
  }

  const handleExportExcel = () => {
    if (!canExportData(userRole)) {
      alert('You do not have permission to export data')
      return
    }

    const data = getExportData('excel', {})
    if (data.length === 0) {
      alert('No data to export')
      return
    }

    // Convert to CSV for Excel
    const headers = Object.keys(data[0])
    const csvContent = [
      headers.join('\t'), // Use tabs for Excel
      ...data.map(row => headers.map(h => {
        const val = row[h] || ''
        // Escape quotes and wrap in quotes if contains comma or newline
        if (typeof val === 'string' && (val.includes(',') || val.includes('\n'))) {
          return `"${val.replace(/"/g, '""')}"`
        }
        return val
      }).join('\t'))
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'application/vnd.ms-excel' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `referral-analytics-${new Date().toISOString().split('T')[0]}.xls`
    link.click()
  }

  const handleExportJSON = () => {
    if (!canExportData(userRole)) {
      alert('You do not have permission to export data')
      return
    }

    const data = {
      generatedAt: new Date().toISOString(),
      timeRange,
      analytics,
      referrals: getExportData('json', {})
    }

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `referral-data-${new Date().toISOString().split('T')[0]}.json`
    link.click()
  }

  // Chart data preparation
  const monthlyChartData = {
    labels: analytics?.monthlyData?.map(d => d.month) || [],
    datasets: [
      {
        label: 'Referrals',
        data: analytics?.monthlyData?.map(d => d.referrals) || [],
        backgroundColor: 'rgba(59, 130, 246, 0.5)',
        borderColor: '#3b82f6',
        borderWidth: 2,
        tension: 0.4
      },
      {
        label: 'Converted',
        data: analytics?.monthlyData?.map(d => d.converted) || [],
        backgroundColor: 'rgba(34, 197, 94, 0.5)',
        borderColor: '#22c55e',
        borderWidth: 2,
        tension: 0.4
      }
    ]
  }

  const earningsChartData = {
    labels: analytics?.monthlyData?.map(d => d.month) || [],
    datasets: [
      {
        label: 'Earnings ($)',
        data: analytics?.monthlyData?.map(d => d.earnings) || [],
        backgroundColor: 'rgba(245, 158, 11, 0.2)',
        borderColor: '#f59e0b',
        borderWidth: 2,
        fill: true,
        tension: 0.4
      }
    ]
  }

  const statusChartData = {
    labels: ['Pending', 'Approved', 'Rejected', 'Converted'],
    datasets: [
      {
        data: [
          analytics?.pendingReferrals || 0,
          analytics?.approvedReferrals || 0,
          analytics?.rejectedReferrals || 0,
          analytics?.convertedReferrals || 0
        ],
        backgroundColor: [
          '#f59e0b',
          '#22c55e',
          '#ef4444',
          '#3b82f6'
        ],
        borderWidth: 0
      }
    ]
  }

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom'
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.05)'
        }
      },
      x: {
        grid: {
          display: false
        }
      }
    }
  }

  return (
    <div className="analytics-dashboard">
      <div className="analytics-header">
        <div>
          <h1>📊 Referral Analytics</h1>
          <p>Track performance and earnings from referrals</p>
        </div>
        <div className="analytics-actions">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="time-range-select"
          >
            {TIME_RANGES.map(range => (
              <option key={range.value} value={range.value}>{range.label}</option>
            ))}
          </select>

          {canExportData(userRole) && (
            <div className="export-buttons">
              <button className="btn-export" onClick={handleExportPDF}>
                <FiFileText /> PDF
              </button>
              <button className="btn-export" onClick={handleExportExcel}>
                <FiFile /> Excel
              </button>
              <button className="btn-export" onClick={handleExportJSON}>
                <FiDownload /> JSON
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Stats Overview */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon blue">
            <FiUsers />
          </div>
          <div className="stat-info">
            <span className="stat-value">{analytics?.totalReferrals || 0}</span>
            <span className="stat-label">Total Referrals</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon green">
            <FiDollarSign />
          </div>
          <div className="stat-info">
            <span className="stat-value">${(analytics?.totalEarnings || 0).toLocaleString()}</span>
            <span className="stat-label">Total Earnings</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon purple">
            <FiPercent />
          </div>
          <div className="stat-info">
            <span className="stat-value">{analytics?.conversionRate || 0}%</span>
            <span className="stat-label">Conversion Rate</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon orange">
            <FiTrendingUp />
          </div>
          <div className="stat-info">
            <span className="stat-value">${(analytics?.averageEarnings || 0).toLocaleString()}</span>
            <span className="stat-label">Avg. Earnings</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="analytics-tabs">
        <button
          className={activeTab === 'overview' ? 'active' : ''}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={activeTab === 'trends' ? 'active' : ''}
          onClick={() => setActiveTab('trends')}
        >
          Trends
        </button>
        <button
          className={activeTab === 'referrers' ? 'active' : ''}
          onClick={() => setActiveTab('referrers')}
        >
          Top Referrers
        </button>
        <button
          className={activeTab === 'recent' ? 'active' : ''}
          onClick={() => setActiveTab('recent')}
        >
          Recent Activity
        </button>
      </div>

      {/* Tab Content */}
      <div className="tab-content" ref={chartsRef}>
        {activeTab === 'overview' && (
          <div className="overview-grid">
            <div className="chart-container">
              <h3>Referral Status Distribution</h3>
              <div className="chart-wrapper small">
                <Doughnut data={statusChartData} options={{ ...chartOptions, cutout: '60%' }} />
              </div>
              <div className="status-legend">
                <div className="legend-item">
                  <span className="dot" style={{ backgroundColor: '#f59e0b' }}></span>
                  <span>Pending ({analytics?.pendingReferrals || 0})</span>
                </div>
                <div className="legend-item">
                  <span className="dot" style={{ backgroundColor: '#22c55e' }}></span>
                  <span>Approved ({analytics?.approvedReferrals || 0})</span>
                </div>
                <div className="legend-item">
                  <span className="dot" style={{ backgroundColor: '#ef4444' }}></span>
                  <span>Rejected ({analytics?.rejectedReferrals || 0})</span>
                </div>
                <div className="legend-item">
                  <span className="dot" style={{ backgroundColor: '#3b82f6' }}></span>
                  <span>Converted ({analytics?.convertedReferrals || 0})</span>
                </div>
              </div>
            </div>

            <div className="chart-container wide">
              <h3>Monthly Performance</h3>
              <div className="chart-wrapper">
                <Bar data={monthlyChartData} options={chartOptions} />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'trends' && (
          <div className="chart-container">
            <h3>Earnings Trend</h3>
            <div className="chart-wrapper large">
              <Line data={earningsChartData} options={chartOptions} />
            </div>
          </div>
        )}

        {activeTab === 'referrers' && (
          <div className="top-referrers">
            <h3>Top 10 Referrers</h3>
            <div className="referrers-table-container">
              <table className="referrers-table">
                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Total Referrals</th>
                    <th>Converted</th>
                    <th>Conversion Rate</th>
                    <th>Earnings</th>
                  </tr>
                </thead>
                <tbody>
                  {analytics?.topReferrers?.map((referrer, index) => (
                    <tr key={referrer.email}>
                      <td className="rank">#{index + 1}</td>
                      <td className="name">{referrer.name}</td>
                      <td className="email">{referrer.email}</td>
                      <td>{referrer.totalReferrals}</td>
                      <td>{referrer.converted}</td>
                      <td>
                        <span className="conversion-rate">
                          {referrer.totalReferrals > 0
                            ? Math.round((referrer.converted / referrer.totalReferrals) * 100)
                            : 0}%
                        </span>
                      </td>
                      <td className="earnings">${referrer.earnings.toLocaleString()}</td>
                    </tr>
                  )) || (
                    <tr>
                      <td colSpan="7" className="no-data">No referrers data available</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'recent' && (
          <div className="recent-activity">
            <h3>Recent Referrals</h3>
            <div className="activity-list">
              {analytics?.recentReferrals?.map(referral => (
                <div key={referral.id} className={`activity-item ${referral.status}`}>
                  <div className="activity-icon">
                    {referral.status === 'converted' && <FiDollarSign />}
                    {referral.status === 'approved' && <FiCheck />}
                    {referral.status === 'pending' && <FiTrendingUp />}
                    {referral.status === 'rejected' && <FiX />}
                  </div>
                  <div className="activity-content">
                    <p className="activity-title">
                      <strong>{referral.referrerName}</strong> referred <strong>{referral.buyerName}</strong>
                    </p>
                    <p className="activity-detail">
                      Property: {referral.propertyTitle} | Potential: ${referral.potentialEarnings?.toLocaleString()}
                    </p>
                    <span className="activity-time">{new Date(referral.createdAt).toLocaleString()}</span>
                  </div>
                  <span
                    className="activity-status"
                    style={{ backgroundColor: STATUS_COLORS[referral.status] + '20', color: STATUS_COLORS[referral.status] }}
                  >
                    {STATUS_LABELS[referral.status]}
                  </span>
                </div>
              )) || (
                <p className="no-data">No recent activity</p>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Access Info */}
      <div className="access-info-footer">
        <p>
          <strong>Your Access Level:</strong> {userRole} | 
          {canExportData(userRole) ? ' Export enabled' : ' Export restricted'} | 
          {canViewAnalytics(userRole) ? ' Full analytics access' : ' Limited analytics'}
        </p>
      </div>
    </div>
  )
}

// Status colors for charts
const STATUS_COLORS = {
  pending: '#f59e0b',
  approved: '#22c55e',
  rejected: '#ef4444',
  converted: '#3b82f6'
}

const STATUS_LABELS = {
  pending: 'Pending',
  approved: 'Approved',
  rejected: 'Rejected',
  converted: 'Converted'
}

// Icons
const FiCheck = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="20 6 9 17 4 12"></polyline>
  </svg>
)

const FiX = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="18" y1="6" x2="6" y2="18"></line>
    <line x1="6" y1="6" x2="18" y2="18"></line>
  </svg>
)

export default AnalyticsDashboard
