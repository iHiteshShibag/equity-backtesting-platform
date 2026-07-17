export default function ErrorBanner({ message }) {
  if (!message) return null
  return (
    <div
      role="alert"
      className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-300 text-sm"
    >
      {message}
    </div>
  )
}
