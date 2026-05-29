import { createContext, useContext, useState, useCallback } from 'react'
import { t, LANGUAGES } from '../i18n/translations'

const LangContext = createContext(null)

function detectBrowserLang() {
  const nav = navigator.language || navigator.languages?.[0] || 'en'
  const code = nav.split('-')[0].toLowerCase()
  const supported = LANGUAGES.map(l => l.code)
  return supported.includes(code) ? code : 'en'
}

export function LangProvider({ children }) {
  const [lang, setLang] = useState(
    () => localStorage.getItem('py_lang') || detectBrowserLang()
  )

  const switchLang = useCallback((code) => {
    setLang(code)
    localStorage.setItem('py_lang', code)
    document.documentElement.lang = code
  }, [])

  const tr = (key) => t[lang]?.[key] ?? t['en']?.[key] ?? key

  return (
    <LangContext.Provider value={{ lang, switchLang, tr, LANGUAGES }}>
      {children}
    </LangContext.Provider>
  )
}

export const useLang = () => useContext(LangContext)
