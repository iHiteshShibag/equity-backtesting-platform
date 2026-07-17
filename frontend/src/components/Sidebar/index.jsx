import { useState, useEffect } from 'react'
import { useAuth } from '@/context/AuthContext'
import { useTheme } from '@/context/ThemeContext'
import {
  DashboardIcon,
  DatabaseIcon,
  SunIcon,
  MoonIcon,
  LogOutIcon,
  PanelLeftCloseIcon,
  UsersIcon,
  BellIcon,
} from '@/components/icons'

const NAV_ITEMS = [
  { key: 'dashboard', label: 'Backtest', icon: DashboardIcon },
  { key: 'strategies', label: 'Saved Strategies', icon: BellIcon },
  { key: 'data', label: 'Data Management', icon: DatabaseIcon },
]

const ADMIN_NAV_ITEMS = [{ key: 'users', label: 'User Admin', icon: UsersIcon }]

function Logo({ size = 32 }) {
  return (
    <div
      className="shrink-0 rounded-lg bg-gradient-to-br from-emerald-500 to-emerald-700 flex items-center justify-center shadow-sm shadow-emerald-900/50"
      style={{ width: size, height: size, fontSize: size * 0.5 }}
    >
      📈
    </div>
  )
}

export default function Sidebar({ activeView, onNavigate }) {
  const { user, logout, isAdmin } = useAuth()
  const { darkMode, toggleDarkMode } = useTheme()
  const navItems = isAdmin ? [...NAV_ITEMS, ...ADMIN_NAV_ITEMS] : NAV_ITEMS
  const [collapsed, setCollapsed] = useState(() => {
    if (typeof window === 'undefined') return false
    return window.localStorage.getItem('sidebar:collapsed') === '1'
  })

  useEffect(() => {
    window.localStorage.setItem('sidebar:collapsed', collapsed ? '1' : '0')
  }, [collapsed])

  return (
    <aside
      className={`shrink-0 h-screen sticky top-0 flex flex-col bg-zinc-900 text-gray-200 border-r border-black/40 transition-all duration-200 ${
        collapsed ? 'w-16' : 'w-64'
      }`}
    >
      {/* Brand */}
      {collapsed ? (
        <button
          onClick={() => setCollapsed(false)}
          title="Expand sidebar"
          aria-label="Expand sidebar"
          className="flex justify-center items-center h-16 hover:opacity-80 transition-opacity"
        >
          <Logo size={28} />
        </button>
      ) : (
        <div className="flex items-center justify-between gap-2.5 px-5 h-16 border-b border-white/10">
          <div className="flex items-center gap-2.5">
            <Logo size={28} />
            <span className="font-bold text-white tracking-tight">EquityBT</span>
          </div>
          <button
            onClick={() => setCollapsed(true)}
            title="Collapse sidebar"
            aria-label="Collapse sidebar"
            className="p-1 text-gray-500 hover:text-white rounded transition-colors"
          >
            <PanelLeftCloseIcon width={18} height={18} />
          </button>
        </div>
      )}

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map(({ key, label, icon: Icon }) => {
          const active = activeView === key
          return (
            <button
              key={key}
              onClick={() => onNavigate(key)}
              title={collapsed ? label : undefined}
              aria-label={label}
              aria-current={active ? 'page' : undefined}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                collapsed ? 'justify-center' : ''
              } ${
                active
                  ? 'bg-emerald-600 text-white shadow-sm shadow-emerald-900/50'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Icon width={18} height={18} />
              {!collapsed && label}
            </button>
          )
        })}
      </nav>

      {/* Footer: user + dark mode + logout */}
      <div className="border-t border-white/10 px-3 py-3">
        {collapsed ? (
          <div className="flex flex-col items-center gap-1.5">
            {user && (
              <button
                onClick={() => onNavigate('profile')}
                title="Your Profile"
                aria-label="Your Profile"
                className="w-8 h-8 rounded-full bg-emerald-600 text-white text-xs font-bold flex items-center justify-center shrink-0 hover:ring-2 hover:ring-emerald-400 transition"
              >
                {user.initials}
              </button>
            )}
            <button
              onClick={toggleDarkMode}
              title={darkMode ? 'Light Mode' : 'Dark Mode'}
              aria-label={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
              className="p-1.5 text-gray-500 hover:text-white rounded-lg transition-colors"
            >
              {darkMode ? <SunIcon width={16} height={16} /> : <MoonIcon width={16} height={16} />}
            </button>
            {user && (
              <button
                onClick={logout}
                title="Log out"
                aria-label="Log out"
                className="p-1.5 text-gray-500 hover:text-red-400 rounded-lg transition-colors"
              >
                <LogOutIcon width={16} height={16} />
              </button>
            )}
          </div>
        ) : (
          <div className="flex items-center gap-3">
            {user && (
              <button
                onClick={() => onNavigate('profile')}
                title="Your Profile"
                aria-label="Your Profile"
                className="flex items-center gap-3 flex-1 min-w-0 text-left rounded-lg hover:bg-white/5 transition p-1 -m-1"
              >
                <div className="w-8 h-8 rounded-full bg-emerald-600 text-white text-xs font-bold flex items-center justify-center shrink-0">
                  {user.initials}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">{user.name}</p>
                  <span
                    className={`inline-block text-[10px] font-bold uppercase tracking-wide px-1.5 py-0.5 rounded ${
                      isAdmin ? 'text-green-400 bg-green-500/10' : 'text-gray-400 bg-gray-500/10'
                    }`}
                  >
                    {user.role}
                  </span>
                </div>
              </button>
            )}
            <button
              onClick={toggleDarkMode}
              title={darkMode ? 'Light Mode' : 'Dark Mode'}
              aria-label={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
              className="p-1.5 text-gray-500 hover:text-white rounded-lg transition-colors shrink-0"
            >
              {darkMode ? <SunIcon width={15} height={15} /> : <MoonIcon width={15} height={15} />}
            </button>
            {user && (
              <button
                onClick={logout}
                title="Log out"
                aria-label="Log out"
                className="p-1.5 text-gray-500 hover:text-red-400 rounded-lg transition-colors shrink-0"
              >
                <LogOutIcon width={15} height={15} />
              </button>
            )}
          </div>
        )}
      </div>
    </aside>
  )
}
