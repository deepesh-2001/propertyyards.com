import React, { useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import { Login, Register } from './components/Auth/Auth'
import { PropertyList, PropertySearch } from './components/Properties/Properties'
import { Whiteboard } from './components/Whiteboard/Whiteboard'
import { Structure3D } from './components/Structure3D/Structure3D'
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
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

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

          {/* Default Route */}
          <Route
            path="/"
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

