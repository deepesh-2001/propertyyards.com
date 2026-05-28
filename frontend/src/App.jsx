import React, { useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Analytics } from '@vercel/analytics/react'
import { useAuthStore } from './stores/authStore'
import { Login, Register } from './components/Auth/Auth'
import { PropertyList, PropertySearch } from './components/Properties/Properties'
import { Whiteboard } from './components/Whiteboard/Whiteboard'
import { Structure3D } from './components/Structure3D/Structure3D'
import { TestFeatures } from './components/TestFeatures/TestFeatures'
import { ReferralManagement, AnalyticsDashboard, ExternalReferralForm } from './components/Referrals'
import { PricingAdmin } from './components/PricingAdmin'
import { Home } from './components/Home'
import { SecurityCacheTesting } from './components/AdminPanel'
import { SEODashboard } from './components/SEODashboard'
import { TestCenter } from './components/TestCenter'
import { AlertCenter, AlertContainer } from './components/AlertCenter'
import './App.css'

function ProtectedRoute({ children, isAuthenticated }) {
  return isAuthenticated ? children : <Navigate to="/login" />
}

function App() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const user = useAuthStore((state) => state.user)

  useEffect(() => {
    // Check if user has token in localStorage on mount
    const token = localStorage.getItem('access_token')
    if (token && !isAuthenticated) {
      // Could validate token here
    }
  }, [])

  return (
    <Router>
      <div className="App">
        {isAuthenticated && <Navigation user={user} />}
        <AlertContainer />
        <Analytics />
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/submit-referral" element={<ExternalReferralForm />} />

          {/* Protected Routes */}
          <Route
            path="/properties"
            element={
              <ProtectedRoute isAuthenticated={isAuthenticated}>
                <PropertyList />
              </ProtectedRoute>
            }
          />
          <Route
            path="/search"
            element={
              <ProtectedRoute isAuthenticated={isAuthenticated}>
                <PropertySearch />
              </ProtectedRoute>
            }
          />
          <Route
            path="/whiteboard"
            element={
              <ProtectedRoute isAuthenticated={isAuthenticated}>
                <Whiteboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/3d-structure"
            element={
              <ProtectedRoute isAuthenticated={isAuthenticated}>
                <Structure3D />
              </ProtectedRoute>
            }
          />
          <Route
            path="/test-features"
            element={
              <ProtectedRoute isAuthenticated={isAuthenticated}>
                <TestFeatures />
              </ProtectedRoute>
            }
          />
          <Route
            path="/referrals"
            element={
              <ProtectedRoute isAuthenticated={isAuthenticated}>
                <ReferralManagement />
              </ProtectedRoute>
            }
          />
          <Route
            path="/analytics"
            element={
              <ProtectedRoute isAuthenticated={isAuthenticated}>
                <AnalyticsDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/pricing"
            element={
              <ProtectedRoute isAuthenticated={isAuthenticated}>
                <PricingAdmin />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <ProtectedRoute isAuthenticated={isAuthenticated}>
                <SecurityCacheTesting />
              </ProtectedRoute>
            }
          />
          <Route
            path="/seo"
            element={
              <ProtectedRoute isAuthenticated={isAuthenticated}>
                <SEODashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/test-center"
            element={
              <ProtectedRoute isAuthenticated={isAuthenticated}>
                <TestCenter />
              </ProtectedRoute>
            }
          />
          <Route
            path="/alerts"
            element={
              <ProtectedRoute isAuthenticated={isAuthenticated}>
                <AlertCenter />
              </ProtectedRoute>
            }
          />

          {/* Default Route */}
          <Route
            path="/dashboard"
            element={
              isAuthenticated ? (
                <Navigate to="/properties" />
              ) : (
                <Navigate to="/login" />
              )
            }
          />

          {/* 404 */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </div>
    </Router>
  )
}

function Navigation({ user }) {
  const logout = useAuthStore((state) => state.logout)

  const handleLogout = async () => {
    await logout()
    window.location.href = '/login'
  }

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <div className="navbar-brand">
          <h1>🏠 Housing Platform</h1>
        </div>

        <div className="navbar-menu">
          <a href="/" className="nav-link">
            Home
          </a>
          <a href="/properties" className="nav-link">
            Properties
          </a>
          <a href="/search" className="nav-link">
            Search
          </a>
          <a href="/whiteboard" className="nav-link">
            Whiteboard
          </a>
          <a href="/3d-structure" className="nav-link">
            3D Structure
          </a>
          <a href="/test-features" className="nav-link">
            Test
          </a>
          <a href="/test-center" className="nav-link">
            Test Center
          </a>
          <a href="/referrals" className="nav-link">
            Referrals
          </a>
          <a href="/analytics" className="nav-link">
            Analytics
          </a>
          <a href="/alerts" className="nav-link">
            Alerts
          </a>
          {user?.role === 'admin' && (
            <>
              <a href="/pricing" className="nav-link">
                Pricing
              </a>
              <a href="/seo" className="nav-link">
                SEO
              </a>
              <a href="/admin" className="nav-link">
                Admin
              </a>
            </>
          )}
          {user && (
            <div className="user-info">
              <span>{user.first_name}</span>
              <span className="role-badge">{user.role}</span>
            </div>
          )}
          <button onClick={handleLogout} className="btn-logout">
            Logout
          </button>
        </div>
      </div>
    </nav>
  )
}

function NotFound() {
  return (
    <div className="not-found">
      <h1>404 - Page Not Found</h1>
      <p>
        Sorry, the page you're looking for doesn't exist. <a href="/">Go Home</a>
      </p>
    </div>
  )
}

export default App

