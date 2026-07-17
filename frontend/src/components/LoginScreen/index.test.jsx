import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import LoginScreen from './index'
import { useAuth } from '@/context/AuthContext'

vi.mock('@/context/AuthContext', () => ({
  useAuth: vi.fn(),
}))

describe('LoginScreen', () => {
  let login

  beforeEach(() => {
    login = vi.fn()
    useAuth.mockReturnValue({ login })
  })

  it('submits the entered email and password', async () => {
    login.mockResolvedValueOnce(undefined)
    const user = userEvent.setup()
    render(<LoginScreen />)

    await user.type(screen.getByLabelText(/email/i), 'trader@example.com')
    await user.type(screen.getByLabelText(/password/i), 'super-secret')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => expect(login).toHaveBeenCalledWith('trader@example.com', 'super-secret'))
  })

  it('shows an invalid-credentials message on a 401', async () => {
    login.mockRejectedValueOnce({ response: { status: 401 } })
    const user = userEvent.setup()
    render(<LoginScreen />)

    await user.type(screen.getByLabelText(/email/i), 'trader@example.com')
    await user.type(screen.getByLabelText(/password/i), 'wrong-password')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    expect(await screen.findByText(/invalid email or password/i)).toBeInTheDocument()
  })

  it('shows a generic message on a non-401 failure', async () => {
    login.mockRejectedValueOnce(new Error('network down'))
    const user = userEvent.setup()
    render(<LoginScreen />)

    await user.type(screen.getByLabelText(/email/i), 'trader@example.com')
    await user.type(screen.getByLabelText(/password/i), 'super-secret')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    expect(await screen.findByText(/unable to sign in/i)).toBeInTheDocument()
  })

  it('disables the submit button while signing in', async () => {
    let resolveLogin
    const pending = new Promise((resolve) => { resolveLogin = resolve })
    login.mockReturnValueOnce(pending)
    const user = userEvent.setup()
    render(<LoginScreen />)

    await user.type(screen.getByLabelText(/email/i), 'trader@example.com')
    await user.type(screen.getByLabelText(/password/i), 'super-secret')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    expect(screen.getByRole('button', { name: /signing in/i })).toBeDisabled()

    await act(async () => {
      resolveLogin()
      await pending
    })
  })
})
