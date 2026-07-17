import { createContext, useContext, useEffect, useState } from 'react'

const ThemeContext = createContext(null)

function getInitialDarkMode() {
  if (typeof window === 'undefined') return false
  const stored = window.localStorage.getItem('theme:dark')
  if (stored !== null) return stored === '1'
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ?? false
}

export function ThemeProvider({ children }) {
  const [darkMode, setDarkMode] = useState(getInitialDarkMode)

  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode)
    window.localStorage.setItem('theme:dark', darkMode ? '1' : '0')
  }, [darkMode])

  const toggleDarkMode = () => setDarkMode((v) => !v)

  return (
    <ThemeContext.Provider value={{ darkMode, toggleDarkMode }}>{children}</ThemeContext.Provider>
  )
}

export function useTheme() {
  return useContext(ThemeContext)
}
