import React, { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { STRINGS, LANGUAGES } from './strings'

const I18nContext = createContext({
  lang: 'en',
  setLang: () => {},
  t: (k) => k,
  languages: LANGUAGES,
})

export function I18nProvider({ children }) {
  const [lang, setLangState] = useState(() => localStorage.getItem('app_lang') || 'en')

  const setLang = useCallback((next) => {
    setLangState(next)
    localStorage.setItem('app_lang', next)
    document.documentElement.lang = next
  }, [])

  useEffect(() => {
    document.documentElement.lang = lang
  }, [lang])

  const t = useCallback(
    (key, fallback) => STRINGS[lang]?.[key] ?? STRINGS.en[key] ?? fallback ?? key,
    [lang]
  )

  return (
    <I18nContext.Provider value={{ lang, setLang, t, languages: LANGUAGES }}>
      {children}
    </I18nContext.Provider>
  )
}

export function useI18n() {
  return useContext(I18nContext)
}
