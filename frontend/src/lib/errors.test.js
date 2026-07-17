import { describe, expect, it } from 'vitest'
import { getErrorMessage } from './errors'

describe('getErrorMessage', () => {
  it('prefers the API-provided detail message', () => {
    const err = { response: { data: { detail: 'Invalid credentials' } }, message: 'Request failed' }
    expect(getErrorMessage(err)).toBe('Invalid credentials')
  })

  it('falls back to the error message when there is no API detail', () => {
    const err = { message: 'Network Error' }
    expect(getErrorMessage(err)).toBe('Network Error')
  })

  it('falls back to the provided default when nothing else is available', () => {
    expect(getErrorMessage({}, 'Custom fallback')).toBe('Custom fallback')
  })

  it('uses the built-in default fallback when none is provided', () => {
    expect(getErrorMessage({})).toBe('Something went wrong')
  })

  it('handles a null/undefined error without throwing', () => {
    expect(getErrorMessage(null)).toBe('Something went wrong')
    expect(getErrorMessage(undefined)).toBe('Something went wrong')
  })
})
