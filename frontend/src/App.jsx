import { Routes, Route } from 'react-router-dom'
import { LangProvider } from './context/LangContext'
import { AuthProvider } from './context/AuthContext'
import { ToastProvider } from './context/ToastContext'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import Home from './pages/Home'
import PropertyDetail from './pages/PropertyDetail'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import PostProperty from './pages/PostProperty'
import Brokers from './pages/Brokers'
import Finance from './pages/Finance'
import About from './pages/About'
import News from './pages/News'
import Contact from './pages/Contact'
import Wishlist from './pages/Wishlist'
import Compare from './pages/Compare'
import NewProjects from './pages/NewProjects'
import LocalityInsights from './pages/LocalityInsights'
import CRM from './pages/CRM'
import AITools from './pages/AITools'
import Analytics from './pages/Analytics'
import AdminPortal from './pages/AdminPortal'
import Payments from './pages/Payments'
import Rewards from './pages/Rewards'
import Notifications from './pages/Notifications'
import SocialMedia from './pages/SocialMedia'
import Feedback from './pages/Feedback'
import DemoTour from './components/DemoTour'

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
        <Route path="/finance"       element={<Finance />} />
        <Route path="/about"         element={<About />} />
        <Route path="/news"          element={<News />} />
        <Route path="/contact"       element={<Contact />} />
        <Route path="/wishlist"      element={<Wishlist />} />
        <Route path="/compare"       element={<Compare />} />
        <Route path="/new-projects"  element={<NewProjects />} />
        <Route path="/locality"      element={<LocalityInsights />} />
        <Route path="/crm"           element={<CRM />} />
        <Route path="/ai-tools"      element={<AITools />} />
        <Route path="/analytics"     element={<Analytics />} />
        <Route path="/admin"         element={<AdminPortal />} />
        <Route path="/payments"      element={<Payments />} />
        <Route path="/rewards"       element={<Rewards />} />
        <Route path="/notifications" element={<Notifications />} />
        <Route path="/social-media"  element={<SocialMedia />} />
        <Route path="/feedback"      element={<Feedback />} />
      </Routes>
      <Footer />
      <DemoTour />
    </AuthProvider>
    </ToastProvider>
    </LangProvider>
  )
}

export default App
