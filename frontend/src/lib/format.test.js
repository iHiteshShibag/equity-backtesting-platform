import { describe, expect, it } from 'vitest'
import { formatDate, formatDateTime, formatINR } from './format'

describe('formatDate', () => {
  it('formats an ISO date with the default pattern', () => {
    expect(formatDate('2024-03-15')).toBe('Mar 24')
  })

  it('accepts a custom pattern', () => {
    expect(formatDate('2024-03-15', 'yyyy-MM-dd')).toBe('2024-03-15')
  })

  it('returns an empty string for a falsy input', () => {
    expect(formatDate(null)).toBe('')
    expect(formatDate(undefined)).toBe('')
    expect(formatDate('')).toBe('')
  })

  it('falls back to the raw string when parsing fails', () => {
    expect(formatDate('not-a-date')).toBe('not-a-date')
  })
})

describe('formatDateTime', () => {
  it('returns an em dash for a falsy input', () => {
    expect(formatDateTime(null)).toBe('—')
    expect(formatDateTime(undefined)).toBe('—')
  })

  it('formats a real ISO timestamp', () => {
    const result = formatDateTime('2024-03-15T10:30:00Z')
    expect(result).not.toBe('—')
    expect(typeof result).toBe('string')
  })
})

describe('formatINR', () => {
  it('formats a positive number with the rupee symbol and Indian grouping', () => {
    expect(formatINR(1234567)).toBe('₹12,34,567')
  })

  it('treats a falsy value as zero', () => {
    expect(formatINR(0)).toBe('₹0')
    expect(formatINR(null)).toBe('₹0')
    expect(formatINR(undefined)).toBe('₹0')
  })
})
