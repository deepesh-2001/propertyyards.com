import { useState, useEffect } from 'react'

const BREAKPOINTS = { mobile: 640, tablet: 1024 }

function getDevice(w) {
  if (w < BREAKPOINTS.mobile)  return 'mobile'
  if (w < BREAKPOINTS.tablet)  return 'tablet'
  return 'desktop'
}

export function useBreakpoint() {
  const [device, setDevice] = useState(() => getDevice(window.innerWidth))
  const [width,  setWidth]  = useState(() => window.innerWidth)

  useEffect(() => {
    const handler = () => {
      const w = window.innerWidth
      setWidth(w)
      setDevice(getDevice(w))
    }
    window.addEventListener('resize', handler)
    return () => window.removeEventListener('resize', handler)
  }, [])

  return {
    device,
    width,
    isMobile:  device === 'mobile',
    isTablet:  device === 'tablet',
    isDesktop: device === 'desktop',
  }
}
