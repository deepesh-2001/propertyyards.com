import React from 'react'
import { FiGlobe } from 'react-icons/fi'
import { useI18n } from '../../i18n/I18nContext'
import './LanguageSwitcher.css'

export function LanguageSwitcher() {
  const { lang, setLang, languages } = useI18n()
  return (
    <label className="lang-switcher" title="Change language">
      <FiGlobe />
      <select value={lang} onChange={(e) => setLang(e.target.value)}>
        {languages.map((l) => (
          <option key={l.code} value={l.code}>
            {l.label}
          </option>
        ))}
      </select>
    </label>
  )
}

export default LanguageSwitcher
