import { useState } from 'react'
import { useAuth } from '@/context/AuthContext'
import { getErrorMessage } from '@/lib/errors'
import ErrorBanner from '@/components/ErrorBanner'

const inputCls =
  'w-full px-3 py-2 rounded-lg border text-sm border-gray-300 dark:bg-zinc-900 dark:border-white/10 dark:text-white'

export default function ProfileView() {
  const { user, isAdmin, updateProfile, changePassword } = useAuth()

  const [fullName, setFullName] = useState(user?.name || '')
  const [savingName, setSavingName] = useState(false)
  const [nameError, setNameError] = useState(null)
  const [nameSaved, setNameSaved] = useState(false)

  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [changingPassword, setChangingPassword] = useState(false)
  const [passwordError, setPasswordError] = useState(null)
  const [passwordSaved, setPasswordSaved] = useState(false)

  const handleSaveName = async (e) => {
    e.preventDefault()
    setSavingName(true)
    setNameError(null)
    setNameSaved(false)
    try {
      await updateProfile({ full_name: fullName.trim() })
      setNameSaved(true)
      setTimeout(() => setNameSaved(false), 3000)
    } catch (err) {
      setNameError(getErrorMessage(err, 'Failed to update name'))
    } finally {
      setSavingName(false)
    }
  }

  const handleChangePassword = async (e) => {
    e.preventDefault()
    setChangingPassword(true)
    setPasswordError(null)
    setPasswordSaved(false)
    try {
      await changePassword(currentPassword, newPassword)
      setCurrentPassword('')
      setNewPassword('')
      setPasswordSaved(true)
      setTimeout(() => setPasswordSaved(false), 3000)
    } catch (err) {
      setPasswordError(getErrorMessage(err, 'Failed to change password'))
    } finally {
      setChangingPassword(false)
    }
  }

  return (
    <div className="space-y-6 max-w-xl">
      <div className="card">
        <h3 className="section-title">Account Details</h3>
        <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-sm">
          <dt className="text-gray-500 dark:text-gray-400">Email</dt>
          <dd className="text-gray-900 dark:text-white">{user?.email}</dd>
          <dt className="text-gray-500 dark:text-gray-400">Role</dt>
          <dd>
            <span
              className={`inline-block text-[10px] font-bold uppercase tracking-wide px-1.5 py-0.5 rounded ${
                isAdmin ? 'text-green-400 bg-green-500/10' : 'text-gray-400 bg-gray-500/10'
              }`}
            >
              {user?.role}
            </span>
          </dd>
        </dl>
      </div>

      <div className="card">
        <h3 className="section-title">Display Name</h3>
        <ErrorBanner message={nameError} />
        <form onSubmit={handleSaveName} className="flex items-end gap-3">
          <div className="flex-1">
            <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Full name</label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Your name"
              className={inputCls}
            />
          </div>
          <button
            type="submit"
            disabled={savingName}
            className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium disabled:opacity-50"
          >
            {savingName ? 'Saving…' : 'Save'}
          </button>
        </form>
        {nameSaved && <p className="text-sm text-emerald-500 mt-2">Name updated.</p>}
      </div>

      <div className="card">
        <h3 className="section-title">Change Password</h3>
        <ErrorBanner message={passwordError} />
        <form onSubmit={handleChangePassword} className="space-y-3">
          <div>
            <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">
              Current password
            </label>
            <input
              type="password"
              required
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className={inputCls}
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">
              New password
            </label>
            <input
              type="password"
              required
              minLength={8}
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className={inputCls}
            />
          </div>
          <button
            type="submit"
            disabled={changingPassword}
            className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium disabled:opacity-50"
          >
            {changingPassword ? 'Updating…' : 'Update Password'}
          </button>
        </form>
        {passwordSaved && <p className="text-sm text-emerald-500 mt-2">Password updated.</p>}
      </div>
    </div>
  )
}
