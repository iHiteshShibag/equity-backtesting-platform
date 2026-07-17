import { format, parseISO } from 'date-fns'

export function formatDate(dateStr, pattern = 'MMM yy') {
  if (!dateStr) return ''
  try {
    return format(parseISO(dateStr), pattern)
  } catch {
    return dateStr
  }
}

export function formatDateTime(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString()
}

export function formatINR(value) {
  return `₹${(value || 0).toLocaleString('en-IN')}`
}
