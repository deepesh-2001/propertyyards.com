import { Routes, Route } from 'react-router-dom'
import { LangProvider } from './context/LangContext'
import { AuthProvider } from './context/AuthContext'
import { ToastProvider } from './context/ToastContext'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import PropertyDetail from './pages/PropertyDetail'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import PostProperty from './pages/PostProperty'
import Brokers from './pages/Brokers'

function App() {
  return (
    <LangProvider>
    <ToastProvider>
    <AuthProvider>
      <Navbar />
      <Routes>
        <Route path="/"              element={<Home />} />
        <Route path="/property/:id"  element={<PropertyDetail />} />
        <Route path="/login"         element={<Login />} />
        <Route path="/register"      element={<Register />} />
        <Route path="/dashboard"     element={<Dashboard />} />
        <Route path="/post-property" element={<PostProperty />} />
        <Route path="/brokers"       element={<Brokers />} />
      </Routes>
    </AuthProvider>
    </ToastProvider>
    </LangProvider>
  )
}

export default App
