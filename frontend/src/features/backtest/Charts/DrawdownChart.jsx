import { memo, useMemo } from 'react'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { useTheme } from '@/context/ThemeContext'
import { formatDate } from '@/lib/format'

function DrawdownChart({ data }) {
  const { darkMode } = useTheme()
  const chartData = useMemo(
    () =>
      (data || []).map((d) => ({
        date: d.date,
        'Drawdown %': parseFloat(d.drawdown?.toFixed(2) || 0),
      })),
    [data],
  )

  if (!data || data.length === 0) {
    return (
      <div className="card text-center py-12 text-gray-500 dark:text-gray-400">
        No data to display
      </div>
    )
  }

  const gridStroke = darkMode ? '#374151' : '#e5e7eb'
  const tickColor = darkMode ? '#9ca3af' : '#374151'
  const tooltipStyle = {
    backgroundColor: darkMode ? '#1f2937' : '#fff',
    borderRadius: '8px',
    border: `1px solid ${gridStroke}`,
    color: darkMode ? '#f3f4f6' : '#111827',
  }

  return (
    <div className="card">
      <h3 className="section-title">Drawdown (%)</h3>
      <ResponsiveContainer width="100%" height={280}>
        <AreaChart data={chartData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
          <defs>
            <linearGradient id="colorDrawdown" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
          <XAxis
            dataKey="date"
            tickFormatter={formatDate}
            tick={{ fontSize: 12, fill: tickColor }}
            interval={Math.floor(chartData.length / 8)}
          />
          <YAxis
            tickFormatter={(v) => `${v.toFixed(0)}%`}
            tick={{ fontSize: 12, fill: tickColor }}
          />
          <Tooltip
            formatter={(value) => `${value.toFixed(2)}%`}
            labelFormatter={(label) => formatDate(label)}
            contentStyle={tooltipStyle}
          />
          <Area
            type="monotone"
            dataKey="Drawdown %"
            stroke="#ef4444"
            fill="url(#colorDrawdown)"
            strokeWidth={2}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

export default memo(DrawdownChart)
