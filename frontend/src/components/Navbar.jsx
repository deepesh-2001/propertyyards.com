import { useState, useRef, useEffect } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { useLang } from '../context/LangContext'
import { useBreakpoint } from '../hooks/useBreakpoint'
import { useTimeGreeting } from '../hooks/useTimeGreeting'

export default function Navbar() {
  const { user, logout, isLoggedIn } = useAuth()
  const { toast }            = useToast()
  const { lang, switchLang, tr, LANGUAGES } = useLang()
  const { isMobile, isTablet } = useBreakpoint()
  const greetKey             = useTimeGreeting()
  const nav                  = useNavigate()
  const loc                  = useLocation()

  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const [langMenuOpen, setLangMenuOpen] = useState(false)
  const [mobileOpen,   setMobileOpen]   = useState(false)

  const userRef = useRef()
  const langRef = useRef()

  useEffect(() => {
    const handler = e => {
      if (userRef.current && !userRef.current.contains(e.target)) setUserMenuOpen(false)
      if (langRef.current && !langRef.current.contains(e.target)) setLangMenuOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  useEffect(() => { setMobileOpen(false) }, [loc.pathname])

  const handleLogout = async () => {
    setUserMenuOpen(false)
    setMobileOpen(false)
    await logout()
    toast(tr('logout') + ' ✓', 'info')
    nav('/')
  }

  const currentLang = LANGUAGES.find(l => l.code === lang)
  const compact = isMobile || isTablet

  return (
    <>
      <nav style={s.nav}>
        <div style={s.inner}>
          {/* Brand */}
          <Link to="/" style={s.brand}>
            <span style={s.brandIcon}>🏠</span>
            {!isMobile && <span>{tr('brand')}</span>}
          </Link>

          {/* Desktop links */}
          {!compact && (
            <div style={s.links}>
              <NavLink to="/?type=sale" active={loc.search.includes('sale')}>{tr('buy')}</NavLink>
              <NavLink to="/?type=rent" active={loc.search.includes('rent')}>{tr('rent')}</NavLink>
              <NavLink to="/brokers"    active={loc.pathname === '/brokers'}>{tr('brokers')}</NavLink>
              <NavLink to="/finance"    active={loc.pathname === '/finance'}>{tr('finance')}</NavLink>
              <NavLink to="/news"       active={loc.pathname === '/news'}>📰 News</NavLink>
              <NavLink to="/about"      active={loc.pathname === '/about'}>About</NavLink>
              <NavLink to="/contact"    active={loc.pathname === '/contact'}>Contact</NavLink>
            </div>
          )}

          {/* Right side */}
          <div style={s.rightGroup}>
            {/* Greeting (desktop only) */}
            {!compact && isLoggedIn && (
              <span style={s.greeting}>{tr(greetKey)}</span>
            )}

            {/* Language switcher */}
            <div ref={langRef} style={{ position: 'relative' }}>
              <button onClick={() => setLangMenuOpen(o => !o)} style={s.langBtn} title="Change Language">
                <span>{currentLang?.flag}</span>
                {!isMobile && <span style={{ fontSize: 12, fontWeight: 600 }}>{currentLang?.label}</span>}
                <span style={{ fontSize: 10, opacity: 0.7 }}>▾</span>
              </button>
              {langMenuOpen && (
                <div style={s.dropdown} className="fade-in">
                  {LANGUAGES.map(l => (
                    <button key={l.code} onClick={() => { switchLang(l.code); setLangMenuOpen(false) }}
                      style={{ ...s.dropItem, ...(lang === l.code ? s.dropItemActive : {}), width: '100%', textAlign: 'left', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 10 }}>
                      <span>{l.flag}</span>
                      <span>{l.label}</span>
                      {lang === l.code && <span style={{ marginLeft: 'auto', color: '#1a56db' }}>✓</span>}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Desktop auth */}
            {!compact && (
              isLoggedIn ? (
                <>
                  <Link to="/post-property" style={s.postBtn}>{tr('postProperty')}</Link>
                  <div ref={userRef} style={{ position: 'relative' }}>
                    <button onClick={() => setUserMenuOpen(o => !o)} style={s.avatar}>
                      <span style={s.avatarLetter}>{(user?.first_name || user?.email || 'U')[0].toUpperCase()}</span>
                      <span style={s.avatarName}>{user?.first_name || user?.email?.split('@')[0]}</span>
                      <span style={{ opacity: 0.7, fontSize: 10 }}>▾</span>
                    </button>
                    {userMenuOpen && (
                      <div style={{ ...s.dropdown, minWidth: 220 }} className="fade-in">
                        <div style={s.dropHeader}>
                          <div style={s.dropEmail}>{user?.email}</div>
                          <div style={s.dropRole}>{user?.role}</div>
                        </div>
                        <Link to="/dashboard"     onClick={() => setUserMenuOpen(false)} style={s.dropItem}>📊 {tr('dashboard')}</Link>
                        <Link to="/post-property" onClick={() => setUserMenuOpen(false)} style={s.dropItem}>➕ {tr('postProperty')}</Link>
                        <div style={s.dropDivider} />
                        <button onClick={handleLogout} style={s.dropLogout}>🚪 {tr('logout')}</button>
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <>
                  <Link to="/login"    style={s.loginLink}>{tr('login')}</Link>
                  <Link to="/register" style={s.postBtn}>{tr('register')}</Link>
                </>
              )
            )}

            {/* Hamburger (mobile/tablet) */}
            {compact && (
              <button onClick={() => setMobileOpen(o => !o)} style={s.hamburger} aria-label="Menu">
                {mobileOpen ? '✕' : '☰'}
              </button>
            )}
          </div>
        </div>
      </nav>

      {/* Mobile drawer */}
      {compact && mobileOpen && (
        <div style={s.drawer} className="fade-in">
          {isLoggedIn && (
            <div style={s.drawerUser}>
              <div style={s.drawerAvatar}>{(user?.first_name || user?.email || 'U')[0].toUpperCase()}</div>
              <div>
                <div style={{ fontWeight: 700, fontSize: 15 }}>{user?.first_name || user?.email?.split('@')[0]}</div>
                <div style={{ fontSize: 12, color: '#64748b', textTransform: 'capitalize' }}>{tr(greetKey)} · {user?.role}</div>
              </div>
            </div>
          )}
          <DrawerLink to="/?type=sale"   label={tr('buy')} />
          <DrawerLink to="/?type=rent"   label={tr('rent')} />
          <DrawerLink to="/brokers"      label={tr('brokers')} />
          <DrawerLink to="/finance"      label={`💰 ${tr('finance')}`} />
          <DrawerLink to="/news"         label="📰 News & Insights" />
          <DrawerLink to="/about"        label="🏢 About Us" />
          <DrawerLink to="/contact"      label="📞 Contact Us" />
          {isLoggedIn ? (
            <>
              <DrawerLink to="/dashboard"     label={`📊 ${tr('dashboard')}`} />
              <DrawerLink to="/post-property" label={`➕ ${tr('postProperty')}`} />
              <button onClick={handleLogout} style={s.drawerLogout}>🚪 {tr('logout')}</button>
            </>
          ) : (
            <>
              <DrawerLink to="/login"    label={tr('login')} />
              <DrawerLink to="/register" label={tr('register')} highlight />
            </>
          )}
        </div>
      )}
    </>
  )
}

function NavLink({ to, active, children }) {
  return <Link to={to} style={{ ...s.link, ...(active ? s.linkActive : {}) }}>{children}</Link>
}

function DrawerLink({ to, label, highlight }) {
  return (
    <Link to={to} style={{ ...s.drawerLink, ...(highlight ? s.drawerHighlight : {}) }}>{label}</Link>
  )
}

const s = {
  nav:          { background: 'rgba(15,23,42,0.97)', backdropFilter: 'blur(12px)', position: 'sticky', top: 0, zIndex: 300, borderBottom: '1px solid rgba(255,255,255,0.08)', boxShadow: '0 1px 20px rgba(0,0,0,0.3)' },
  inner:        { maxWidth: 1240, margin: '0 auto', padding: '0 1rem', height: 60, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 },
  brand:        { display: 'flex', alignItems: 'center', gap: 8, textDecoration: 'none', color: '#fff', fontWeight: 800, fontSize: 18, letterSpacing: '-0.5px', flexShrink: 0 },
  brandIcon:    { fontSize: 22 },
  links:        { display: 'flex', alignItems: 'center', gap: 2, flex: 1, justifyContent: 'center' },
  link:         { color: 'rgba(255,255,255,0.72)', textDecoration: 'none', fontSize: 14, fontWeight: 500, padding: '6px 14px', borderRadius: 8, transition: 'all 0.15s' },
  linkActive:   { color: '#fff', background: 'rgba(255,255,255,0.1)' },
  rightGroup:   { display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 },
  greeting:     { fontSize: 12, color: 'rgba(255,255,255,0.55)', fontWeight: 500, padding: '0 4px' },
  langBtn:      { display: 'flex', alignItems: 'center', gap: 5, background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.15)', borderRadius: 20, padding: '5px 10px', cursor: 'pointer', color: '#fff', fontSize: 13, transition: 'all 0.15s' },
  loginLink:    { color: 'rgba(255,255,255,0.8)', textDecoration: 'none', fontSize: 14, fontWeight: 600, padding: '7px 14px', borderRadius: 8 },
  postBtn:      { background: 'linear-gradient(135deg, #1a56db, #2563eb)', color: '#fff', textDecoration: 'none', fontSize: 13, fontWeight: 700, padding: '8px 16px', borderRadius: 10, border: 'none', cursor: 'pointer', boxShadow: '0 2px 8px rgba(26,86,219,0.4)', whiteSpace: 'nowrap' },
  avatar:       { display: 'flex', alignItems: 'center', gap: 7, background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.15)', borderRadius: 24, padding: '4px 12px 4px 5px', cursor: 'pointer', color: '#fff', transition: 'all 0.2s' },
  avatarLetter: { width: 26, height: 26, borderRadius: '50%', background: 'linear-gradient(135deg, #1a56db, #7c3aed)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: 13 },
  avatarName:   { fontSize: 13, fontWeight: 600 },
  hamburger:    { background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 8, padding: '7px 12px', color: '#fff', fontSize: 18, cursor: 'pointer', lineHeight: 1 },
  dropdown:     { position: 'absolute', right: 0, top: 'calc(100% + 8px)', background: '#fff', borderRadius: 14, border: '1px solid #e2e8f0', boxShadow: '0 8px 32px rgba(0,0,0,0.15)', minWidth: 180, overflow: 'hidden', zIndex: 400 },
  dropHeader:   { padding: '12px 16px', background: '#f8fafc', borderBottom: '1px solid #e2e8f0' },
  dropEmail:    { fontSize: 13, fontWeight: 600, color: '#0f172a' },
  dropRole:     { fontSize: 11, color: '#64748b', textTransform: 'capitalize', marginTop: 2 },
  dropItem:     { display: 'block', padding: '10px 16px', fontSize: 14, color: '#0f172a', textDecoration: 'none', background: 'none', transition: 'background 0.1s' },
  dropItemActive:{ background: '#eff6ff' },
  dropDivider:  { height: 1, background: '#e2e8f0', margin: '4px 0' },
  dropLogout:   { display: 'block', width: '100%', textAlign: 'left', padding: '10px 16px', fontSize: 14, color: '#dc2626', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 600 },
  drawer:       { position: 'fixed', top: 60, left: 0, right: 0, background: '#0f172a', borderBottom: '1px solid rgba(255,255,255,0.1)', zIndex: 250, padding: '12px 0 20px', boxShadow: '0 8px 24px rgba(0,0,0,0.4)' },
  drawerUser:   { display: 'flex', alignItems: 'center', gap: 12, padding: '12px 20px 16px', borderBottom: '1px solid rgba(255,255,255,0.08)', marginBottom: 8, color: '#fff' },
  drawerAvatar: { width: 40, height: 40, borderRadius: '50%', background: 'linear-gradient(135deg,#1a56db,#7c3aed)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: 18, color: '#fff', flexShrink: 0 },
  drawerLink:   { display: 'block', padding: '13px 24px', color: 'rgba(255,255,255,0.85)', textDecoration: 'none', fontSize: 16, fontWeight: 500, borderBottom: '1px solid rgba(255,255,255,0.05)' },
  drawerHighlight:{ color: '#60a5fa', fontWeight: 700 },
  drawerLogout: { display: 'block', width: '100%', textAlign: 'left', padding: '13px 24px', fontSize: 16, color: '#f87171', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 600, borderTop: '1px solid rgba(255,255,255,0.08)', marginTop: 4 },
}
