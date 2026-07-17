import { saveAs } from 'file-saver'
import * as XLSX from 'xlsx'

export default function ExportButton({ timeseries, rebalanceLogs, metrics }) {
  const exportCSV = () => {
    if (!timeseries || timeseries.length === 0) {
      alert('No data to export')
      return
    }

    const headers = ['Date', 'Portfolio Value', 'Drawdown %']
    const rows = timeseries.map((d) => [d.date, d.portfolio_value, d.drawdown || 0])

    let csv = headers.join(',') + '\n'
    csv += rows.map((r) => r.join(',')).join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    saveAs(blob, `backtest_${new Date().toISOString().split('T')[0]}.csv`)
  }

  const exportExcel = () => {
    const wb = XLSX.utils.book_new()

    // Equity curve sheet
    if (timeseries && timeseries.length > 0) {
      XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(timeseries), 'Equity Curve')
    }

    // Rebalance log sheet
    if (rebalanceLogs && rebalanceLogs.length > 0) {
      XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(rebalanceLogs), 'Rebalance Log')
    }

    // Metrics sheet
    if (metrics && Object.keys(metrics).length > 0) {
      XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet([metrics]), 'Metrics')
    }

    XLSX.writeFile(wb, `backtest_results_${new Date().toISOString().split('T')[0]}.xlsx`)
  }

  return (
    <div className="flex gap-3">
      <button onClick={exportCSV} className="flex-1 btn-secondary">
        📥 Export CSV
      </button>
      <button onClick={exportExcel} className="flex-1 btn-primary">
        📊 Export Excel
      </button>
    </div>
  )
}
