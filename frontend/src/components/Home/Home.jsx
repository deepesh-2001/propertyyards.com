import React, { useState, useEffect } from 'react'
import { useAuthStore } from '../../stores/authStore'
import { FiArrowRight, FiHome, FiBox, FiPenTool, FiUsers, FiTrendingUp, FiDollarSign, FiShield, FiCheck, FiStar } from 'react-icons/fi'
import './Home.css'

const FEATURES = [
  {
    icon: <FiHome size={32} />,
    title: 'Property Listings',
    description: 'Browse thousands of verified properties with detailed information, photos, and virtual tours.',
    color: '#3b82f6',
    gradient: 'from-blue-500 to-blue-600'
  },
  {
    icon: <FiPenTool size={32} />,
    title: 'Whiteboard',
    description: 'Design floor plans, sketch property layouts, and collaborate in real-time with our interactive canvas.',
    color: '#8b5cf6',
    gradient: 'from-purple-500 to-purple-600'
  },
  {
    icon: <FiBox size={32} />,
    title: '3D Structure',
    description: 'Transform 2D images into immersive 3D models. Visualize properties like never before.',
    color: '#f59e0b',
    gradient: 'from-amber-500 to-orange-500'
  },
  {
    icon: <FiUsers size={32} />,
    title: 'Referral Program',
    description: 'Earn up to 2% commission by referring buyers. Track earnings and manage referrals easily.',
    color: '#22c55e',
    gradient: 'from-green-500 to-emerald-500'
  },
  {
    icon: <FiTrendingUp size={32} />,
    title: 'Analytics',
    description: 'Powerful insights with PDF/Excel exports. Track performance, conversions, and revenue.',
    color: '#ec4899',
    gradient: 'from-pink-500 to-rose-500'
  },
  {
    icon: <FiDollarSign size={32} />,
    title: 'Dynamic Pricing',
    description: 'Smart pricing engine with discounts, multipliers, and real-time market adjustments.',
    color: '#14b8a6',
    gradient: 'from-teal-500 to-cyan-500'
  }
]

const TESTIMONIALS = [
  {
    name: 'Sarah Johnson',
    role: 'Property Investor',
    content: 'The 3D structure feature is a game-changer! I can now visualize properties before visiting.',
    avatar: 'SJ',
    rating: 5
  },
  {
    name: 'Michael Chen',
    role: 'Real Estate Agent',
    content: 'The referral program helped me earn an extra $15,000 last quarter. Highly recommended!',
    avatar: 'MC',
    rating: 5
  },
  {
    name: 'Emily Rodriguez',
    role: 'Home Buyer',
    content: 'Found my dream home in just 2 weeks. The whiteboard tool helped me plan renovations.',
    avatar: 'ER',
    rating: 5
  }
]

const STATS = [
  { value: '10K+', label: 'Properties Listed' },
  { value: '5K+', label: 'Happy Users' },
  { value: '$2M+', label: 'Referral Earnings' },
  { value: '99.9%', label: 'Uptime' }
]

export function Home() {
  const [isVisible, setIsVisible] = useState({})
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 })
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          setIsVisible((prev) => ({
            ...prev,
            [entry.target.id]: entry.isIntersecting
          }))
        })
      },
      { threshold: 0.1, rootMargin: '0px 0px -50px 0px' }
    )

    document.querySelectorAll('.animate-on-scroll').forEach((el) => {
      observer.observe(el)
    })

    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    const handleMouseMove = (e) => {
      setMousePosition({ x: e.clientX, y: e.clientY })
    }
    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [])

  return (
    <div className="home-container">
      {/* Animated Background */}
      <div className="animated-background">
        <div className="gradient-orb orb-1" />
        <div className="gradient-orb orb-2" />
        <div className="gradient-orb orb-3" />
        <div 
          className="mouse-glow"
          style={{
            left: mousePosition.x,
            top: mousePosition.y
          }}
        />
      </div>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <div className="hero-badge">
            <span className="badge-pulse" />
            <span>New: 3D Structure Generator</span>
          </div>
          
          <h1 className="hero-title">
            <span className="gradient-text">Discover</span> Your
            <br />
            Perfect <span className="gradient-text">Property</span>
          </h1>
          
          <p className="hero-subtitle">
            The most advanced real estate platform with AI-powered tools,
            <br />
            3D visualization, and earning opportunities.
          </p>
          
          <div className="hero-actions">
            {isAuthenticated ? (
              <a href="/properties" className="btn-primary btn-glow">
                Explore Properties <FiArrowRight />
              </a>
            ) : (
              <>
                <a href="/register" className="btn-primary btn-glow">
                  Get Started Free <FiArrowRight />
                </a>
                <a href="/submit-referral" className="btn-secondary">
                  Submit Referral
                </a>
              </>
            )}
          </div>

          <div className="hero-stats">
            {STATS.map((stat, index) => (
              <div 
                key={index} 
                className="stat-item"
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <span className="stat-value">{stat.value}</span>
                <span className="stat-label">{stat.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Floating Cards */}
        <div className="floating-cards">
          <div className="float-card card-1">
            <FiHome size={24} />
            <span>2,400+</span>
            <small>New Listings</small>
          </div>
          <div className="float-card card-2">
            <FiDollarSign size={24} />
            <span>$50K</span>
            <small>Avg. Savings</small>
          </div>
          <div className="float-card card-3">
            <FiUsers size={24} />
            <span>4.9</span>
            <small>User Rating</small>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="features-section animate-on-scroll">
        <div className="section-header">
          <span className="section-tag">Features</span>
          <h2 className="section-title">Everything You Need</h2>
          <p className="section-subtitle">
            Powerful tools designed for buyers, sellers, and agents
          </p>
        </div>

        <div className={`features-grid ${isVisible['features'] ? 'visible' : ''}`}>
          {FEATURES.map((feature, index) => (
            <div 
              key={index} 
              className="feature-card"
              style={{ 
                animationDelay: `${index * 0.1}s`,
                '--card-color': feature.color 
              }}
            >
              <div 
                className="feature-icon"
                style={{ background: `linear-gradient(135deg, ${feature.color}20, ${feature.color}10)` }}
              >
                <div style={{ color: feature.color }}>
                  {feature.icon}
                </div>
              </div>
              <h3>{feature.title}</h3>
              <p>{feature.description}</p>
              <div className="feature-shine" />
            </div>
          ))}
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="how-it-works animate-on-scroll">
        <div className="section-header">
          <span className="section-tag">How It Works</span>
          <h2 className="section-title">Simple Steps to Success</h2>
        </div>

        <div className={`steps-container ${isVisible['how-it-works'] ? 'visible' : ''}`}>
          <div className="step-line" />
          
          {[
            { step: 1, title: 'Browse', desc: 'Search properties with advanced filters', icon: <FiHome /> },
            { step: 2, title: 'Visualize', desc: 'Use 3D & Whiteboard tools', icon: <FiBox /> },
            { step: 3, title: 'Connect', desc: 'Contact agents & schedule visits', icon: <FiUsers /> },
            { step: 4, title: 'Earn', desc: 'Refer friends & earn commission', icon: <FiDollarSign /> }
          ].map((item, index) => (
            <div 
              key={index} 
              className="step-item"
              style={{ animationDelay: `${index * 0.2}s` }}
            >
              <div className="step-number">{item.step}</div>
              <div className="step-icon">{item.icon}</div>
              <h4>{item.title}</h4>
              <p>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Testimonials */}
      <section id="testimonials" className="testimonials-section animate-on-scroll">
        <div className="section-header">
          <span className="section-tag">Testimonials</span>
          <h2 className="section-title">Loved by Thousands</h2>
        </div>

        <div className={`testimonials-grid ${isVisible['testimonials'] ? 'visible' : ''}`}>
          {TESTIMONIALS.map((testimonial, index) => (
            <div key={index} className="testimonial-card">
              <div className="testimonial-stars">
                {[...Array(testimonial.rating)].map((_, i) => (
                  <FiStar key={i} className="star-filled" />
                ))}
              </div>
              <p className="testimonial-content">"{testimonial.content}"</p>
              <div className="testimonial-author">
                <div className="author-avatar">{testimonial.avatar}</div>
                <div className="author-info">
                  <span className="author-name">{testimonial.name}</span>
                  <span className="author-role">{testimonial.role}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section animate-on-scroll">
        <div className="cta-content">
          <h2>Ready to Find Your Dream Home?</h2>
          <p>Join thousands of satisfied users and start your property journey today.</p>
          <div className="cta-actions">
            {isAuthenticated ? (
              <a href="/properties" className="btn-primary btn-large btn-glow">
                Start Exploring <FiArrowRight />
              </a>
            ) : (
              <>
                <a href="/register" className="btn-primary btn-large btn-glow">
                  Create Free Account
                </a>
                <span className="cta-or">or</span>
                <a href="/submit-referral" className="btn-outline btn-large">
                  Submit a Referral
                </a>
              </>
            )}
          </div>
          <div className="cta-trust">
            <span><FiCheck /> No credit card required</span>
            <span><FiCheck /> Free forever plan</span>
            <span><FiCheck /> Cancel anytime</span>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="home-footer">
        <div className="footer-content">
          <div className="footer-brand">
            <h3>🏠 PropertyYards</h3>
            <p>Making real estate simple, visual, and rewarding.</p>
          </div>
          <div className="footer-links">
            <div className="footer-column">
              <h4>Product</h4>
              <a href="/properties">Properties</a>
              <a href="/whiteboard">Whiteboard</a>
              <a href="/3d-structure">3D Structure</a>
              <a href="/referrals">Referrals</a>
            </div>
            <div className="footer-column">
              <h4>Company</h4>
              <a href="#">About Us</a>
              <a href="#">Careers</a>
              <a href="#">Blog</a>
              <a href="#">Contact</a>
            </div>
            <div className="footer-column">
              <h4>Legal</h4>
              <a href="#">Privacy</a>
              <a href="#">Terms</a>
              <a href="#">Security</a>
            </div>
          </div>
        </div>
        <div className="footer-bottom">
          <p>© 2026 PropertyYards. All rights reserved.</p>
          <div className="footer-social">
            <span>Made with ❤️ by PropertyYards Team</span>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default Home
