import { useState, useRef, useEffect } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

export default function Navbar() {
  const { user, logout, isLoggedIn } = useAuth()
  const { toast }  = useToast()
  const nav        = useNavigate()
  const loc        = useLocation()
  const [open, setOpen] = useState(false)
  const ref        = useRef()

  useEffect(() => {
    const handler = e => { if (ref.current && !ref.current.contains(e.target)) setOpen(false) }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleLogout = async () => {
    setOpen(false)
    await logout()
    toast('Logged out successfully', 'info')
    nav('/')
  }

  const isActive = (path) => loc.pathname === path || loc.search.includes(path.split('?')[1] || '__')

  return (
    <nav style={s.nav}>
      <div style={s.inner}>
        <Link to="/" style={s.brand}>
          <span style={s.brandIcon}>🏠</span>
          <span>PropertyYards</span>
        </Link>

        <div style={s.links}>
          <NavLink to="/?type=sale" active={loc.search.includes('sale')}>Buy</NavLink>
          <NavLink to="/?type=rent" active={loc.search.includes('rent')}>Rent</NavLink>
          <NavLink to="/brokers" active={loc.pathname === '/brokers'}>Brokers</NavLink>

          {isLoggedIn ? (
            <>
              <Link to="/post-property" style={s.postBtn}>+ Post Property</Link>
              <div ref={ref} style={{ position: 'relative' }}>
                <button onClick={() => setOpen(o => !o)} style={s.avatar}>
                  <span style={s.avatarLetter}>{(user?.first_name || user?.email || 'U')[0].toUpperCase()}</span>
                  <span style={s.avatarName}>{user?.first_name || user?.email?.split('@')[0]}</span>
                  <span style={{ opacity: 0.7, fontSize: 11 }}>▾</span>
                </button>
                {open && (
                  <div style={s.dropdown} className="fade-in">
                    <div style={s.dropHeader}>
                      <div style={s.dropEmail}>{user?.email}</div>
                      <div style={s.dropRole}>{user?.role}</div>
                    </div>
                    <DropItem to="/dashboard"     onClick={() => setOpen(false)}>📊 Dashboard</DropItem>
                    <DropItem to="/post-property" onClick={() => setOpen(false)}>➕ Post Property</DropItem>
                    <div style={s.dropDivider} />
                    <button onClick={handleLogout} style={s.dropLogout}>🚪 Logout</button>
                  </div>
                )}
              </div>
            </>
          ) : (
            <>
              <Link to="/login"    style={s.loginLink}>Login</Link>
              <Link to="/register" style={s.postBtn}>Register Free</Link>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}

function NavLink({ to, active, children }) {
  return (
    <Link to={to} style={{ ...s.link, ...(active ? s.linkActive : {}) }}>{children}</Link>
  )
}

function DropItem({ to, onClick, children }) {
  return (
    <Link to={to} onClick={onClick} style={s.dropItem}>{children}</Link>
  )
}

const s = {
  nav:         { background: 'rgba(15,23,42,0.97)', backdropFilter: 'blur(12px)', position: 'sticky', top: 0, zIndex: 200, borderBottom: '1px solid rgba(255,255,255,0.08)', boxShadow: '0 1px 20px rgba(0,0,0,0.25)' },
  inner:       { maxWidth: 1240, margin: '0 auto', padding: '0 1.5rem', height: 64, display: 'flex', alignItems: 'center', justifyContent: 'space-between' },
  brand:       { display: 'flex', alignItems: 'center', gap: 10, textDecoration: 'none', color: '#fff', fontWeight: 800, fontSize: 20, letterSpacing: '-0.5px' },
  brandIcon:   { fontSize: 24 },
  links:       { display: 'flex', alignItems: 'center', gap: 4 },
  link:        { color: 'rgba(255,255,255,0.75)', textDecoration: 'none', fontSize: 14, fontWeight: 500, padding: '6px 14px', borderRadius: 8, transition: 'all 0.15s' },
  linkActive:  { color: '#fff', background: 'rgba(255,255,255,0.1)' },
  loginLink:   { color: 'rgba(255,255,255,0.8)', textDecoration: 'none', fontSize: 14, fontWeight: 600, padding: '7px 16px', borderRadius: 8 },
  postBtn:     { background: 'linear-gradient(135deg, #1a56db, #2563eb)', color: '#fff', textDecoration: 'none', fontSize: 14, fontWeight: 700, padding: '8px 18px', borderRadius: 10, marginLeft: 8, border: 'none', cursor: 'pointer', boxShadow: '0 2px 8px rgba(26,86,219,0.4)', transition: 'all 0.2s' },
  avatar:      { display: 'flex', alignItems: 'center', gap: 8, background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.15)', borderRadius: 24, padding: '5px 14px 5px 6px', cursor: 'pointer', marginLeft: 8, color: '#fff', transition: 'all 0.2s' },
  avatarLetter:{ width: 28, height: 28, borderRadius: '50%', background: 'linear-gradient(135deg, #1a56db, #7c3aed)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: 14 },
  avatarName:  { fontSize: 14, fontWeight: 600 },
  dropdown:    { position: 'absolute', right: 0, top: 'calc(100% + 8px)', background: '#fff', borderRadius: 14, border: '1px solid #e2e8f0', boxShadow: '0 8px 32px rgba(0,0,0,0.15)', minWidth: 220, overflow: 'hidden' },
  dropHeader:  { padding: '14px 16px', background: '#f8fafc', borderBottom: '1px solid #e2e8f0' },
  dropEmail:   { fontSize: 13, fontWeight: 600, color: '#0f172a' },
  dropRole:    { fontSize: 11, color: '#64748b', textTransform: 'capitalize', marginTop: 2 },
  dropItem:    { display: 'block', padding: '10px 16px', fontSize: 14, color: '#0f172a', textDecoration: 'none', transition: 'background 0.15s' },
  dropDivider: { height: 1, background: '#e2e8f0', margin: '4px 0' },
  dropLogout:  { display: 'block', width: '100%', textAlign: 'left', padding: '10px 16px', fontSize: 14, color: '#dc2626', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 600 },
}
