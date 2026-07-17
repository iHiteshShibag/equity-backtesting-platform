import { useMemo, useState } from 'react'
import { useAuth } from '@/context/AuthContext'
import OrganizationCard from '@/features/orgs/OrganizationCard'
import { listUsers, createUser, updateUser, deleteUser } from './api'
import { useAsyncList } from '@/hooks/useAsyncList'
import { getErrorMessage } from '@/lib/errors'
import ErrorBanner from '@/components/ErrorBanner'

const emptyForm = { email: '', password: '', full_name: '', role: 'member' }
const selectCls =
  'px-3 py-2 rounded-lg border text-sm border-gray-300 dark:bg-zinc-900 dark:border-white/10 dark:text-white'

export default function UserAdminView() {
  const { user: currentUser } = useAuth()
  const {
    data: users,
    loading,
    error,
    setError,
    reload,
  } = useAsyncList(listUsers, {
    fallbackError: 'Failed to load users',
  })
  const [form, setForm] = useState(emptyForm)
  const [submitting, setSubmitting] = useState(false)
  const [roleFilter, setRoleFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')

  const handleCreate = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      await createUser(form)
      setForm(emptyForm)
      await reload()
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to create user'))
    } finally {
      setSubmitting(false)
    }
  }

  const handleRoleToggle = async (u) => {
    try {
      await updateUser(u.id, { role: u.role === 'admin' ? 'member' : 'admin' })
      await reload()
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to update role'))
    }
  }

  const handleActiveToggle = async (u) => {
    try {
      await updateUser(u.id, { is_active: !u.is_active })
      await reload()
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to update user'))
    }
  }

  const handleDelete = async (u) => {
    if (!window.confirm(`Delete ${u.email}? This cannot be undone.`)) return
    try {
      await deleteUser(u.id)
      await reload()
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to delete user'))
    }
  }

  const visibleUsers = useMemo(() => {
    return (users || [])
      .filter((u) => roleFilter === 'all' || u.role === roleFilter)
      .filter(
        (u) => statusFilter === 'all' || (statusFilter === 'active' ? u.is_active : !u.is_active),
      )
  }, [users, roleFilter, statusFilter])

  return (
    <div className="space-y-6">
      <ErrorBanner message={error} />

      <OrganizationCard />

      <div className="card">
        <h3 className="section-title">Add User</h3>
        <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-5 gap-3 items-end">
          <input
            type="email"
            required
            placeholder="Email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            className={selectCls}
          />
          <input
            type="text"
            placeholder="Full name"
            value={form.full_name}
            onChange={(e) => setForm({ ...form, full_name: e.target.value })}
            className={selectCls}
          />
          <input
            type="password"
            required
            minLength={8}
            placeholder="Password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            className={selectCls}
          />
          <select
            value={form.role}
            onChange={(e) => setForm({ ...form, role: e.target.value })}
            className={selectCls}
          >
            <option value="member">Member</option>
            <option value="admin">Admin</option>
          </select>
          <button
            type="submit"
            disabled={submitting}
            className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium disabled:opacity-50"
          >
            {submitting ? 'Adding…' : 'Add User'}
          </button>
        </form>
      </div>

      <div className="card">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <h3 className="section-title">Users</h3>
          <div className="flex gap-2">
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className={selectCls}
            >
              <option value="all">All roles</option>
              <option value="member">Member</option>
              <option value="admin">Admin</option>
            </select>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className={selectCls}
            >
              <option value="all">All statuses</option>
              <option value="active">Active</option>
              <option value="deactivated">Deactivated</option>
            </select>
          </div>
        </div>
        {loading ? (
          <p className="text-gray-500 dark:text-gray-400">Loading…</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left border-b border-gray-200 text-gray-500 dark:border-white/10 dark:text-gray-400">
                  <th className="py-2 pr-4">Name</th>
                  <th className="py-2 pr-4">Email</th>
                  <th className="py-2 pr-4">Role</th>
                  <th className="py-2 pr-4">Status</th>
                  <th className="py-2 pr-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {visibleUsers.map((u) => {
                  const isSelf = u.id === currentUser?.id
                  return (
                    <tr key={u.id} className="border-b border-gray-100 dark:border-white/5">
                      <td className="py-2 pr-4 font-medium">{u.full_name || '—'}</td>
                      <td className="py-2 pr-4">{u.email}</td>
                      <td className="py-2 pr-4">
                        <span
                          className={`inline-block text-[10px] font-bold uppercase tracking-wide px-1.5 py-0.5 rounded ${
                            u.role === 'admin'
                              ? 'text-green-400 bg-green-500/10'
                              : 'text-gray-400 bg-gray-500/10'
                          }`}
                        >
                          {u.role}
                        </span>
                      </td>
                      <td className="py-2 pr-4">{u.is_active ? 'Active' : 'Deactivated'}</td>
                      <td className="py-2 pr-4 text-right space-x-2 whitespace-nowrap">
                        <button
                          disabled={isSelf}
                          onClick={() => handleRoleToggle(u)}
                          title={isSelf ? "You can't change your own role" : 'Toggle role'}
                          className="text-emerald-500 hover:underline disabled:opacity-30 disabled:no-underline"
                        >
                          {u.role === 'admin' ? 'Make member' : 'Make admin'}
                        </button>
                        <button
                          disabled={isSelf}
                          onClick={() => handleActiveToggle(u)}
                          title={isSelf ? "You can't deactivate yourself" : 'Toggle active'}
                          className="text-amber-500 hover:underline disabled:opacity-30 disabled:no-underline"
                        >
                          {u.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                        <button
                          disabled={isSelf}
                          onClick={() => handleDelete(u)}
                          title={isSelf ? "You can't delete yourself" : 'Delete user'}
                          className="text-red-500 hover:underline disabled:opacity-30 disabled:no-underline"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
