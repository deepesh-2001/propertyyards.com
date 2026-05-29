import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { user, logout, isLoggedIn } = useAuth()
  const nav = useNavigate()

  const handleLogout = async () => {
    await logout()
    nav('/')
  }

  return (
    <nav style={s.nav}>
      <Link to="/" style={s.brand}>🏠 PropertyYards</Link>
      <div style={s.links}>
        <Link to="/?type=sale" style={s.link}>Buy</Link>
        <Link to="/?type=rent" style={s.link}>Rent</Link>
        <Link to="/brokers" style={s.link}>Brokers</Link>
        {isLoggedIn ? (
          <>
            <Link to="/dashboard" style={s.link}>Dashboard</Link>
            <Link to="/post-property" style={s.btn}>+ Post Property</Link>
            <span style={s.userBadge}>
              {user.email.split('@')[0]}
              <button onClick={handleLogout} style={s.logoutBtn}>Logout</button>
            </span>
          </>
        ) : (
          <>
            <Link to="/login" style={s.link}>Login</Link>
            <Link to="/register" style={s.btn}>Register Free</Link>
          </>
        )}
      </div>
    </nav>
  )
}

const s = {
  nav:       { background: '#1a56db', padding: '0 2rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: 62, position: 'sticky', top: 0, zIndex: 100, boxShadow: '0 2px 12px rgba(0,0,0,0.15)' },
  brand:     { color: '#fff', fontWeight: 800, fontSize: 22, textDecoration: 'none', letterSpacing: '-0.5px' },
  links:     { display: 'flex', alignItems: 'center', gap: 8 },
  link:      { color: '#fff', textDecoration: 'none', fontSize: 15, padding: '6px 12px', borderRadius: 6, opacity: 0.9 },
  btn:       { background: '#fff', color: '#1a56db', padding: '7px 18px', borderRadius: 8, fontWeight: 700, textDecoration: 'none', fontSize: 14, marginLeft: 8 },
  userBadge: { color: '#fff', fontSize: 14, display: 'flex', alignItems: 'center', gap: 10, marginLeft: 8, background: 'rgba(255,255,255,0.15)', padding: '5px 14px', borderRadius: 20 },
  logoutBtn: { background: 'none', border: 'none', color: '#fecaca', cursor: 'pointer', fontSize: 13, padding: 0 },
}
