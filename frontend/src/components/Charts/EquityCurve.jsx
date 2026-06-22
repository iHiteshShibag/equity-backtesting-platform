import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, ReferenceLine
} from 'recharts'
import { format, parseISO } from 'date-fns'

export default function EquityCurve({ data, initialCapital }) {
  if (!data || data.length === 0) {
    return <div className="card text-center py-12 text-gray-500">No data to display</div>
  }

  const chartData = data.map(d => ({
    date: d.date,
    'Portfolio Value': Math.round(d.portfolio_value),
  }))

  const formatYAxis = (value) => `₹${(value / 100000).toFixed(1)}L`
  const formatDate = (dateStr) => {
    try {
      return format(parseISO(dateStr), 'MMM yy')
    } catch {
      return dateStr
    }
  }

  return (
    <div className="card">
      <h3 className="section-title">Equity Curve</h3>
      <ResponsiveContainer width="100%" height={380}>
        <LineChart data={chartData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
          <defs>
            <linearGradient id="colorPortfolio" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#2563eb" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#2563eb" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="date"
            tickFormatter={formatDate}
            tick={{ fontSize: 12 }}
            interval={Math.floor(chartData.length / 8)}
          />
          <YAxis
            tickFormatter={formatYAxis}
            tick={{ fontSize: 12 }}
          />
          <Tooltip
            formatter={(value) => `₹${value.toLocaleString('en-IN')}`}
            labelFormatter={(label) => formatDate(label)}
            contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e5e7eb' }}
          />
          <Legend />
          <ReferenceLine
            y={initialCapital}
            stroke="#9ca3af"
            strokeDasharray="5 5"
            label={{ value: 'Initial Capital', position: 'right', fill: '#6b7280', fontSize: 12 }}
          />
          <Line
            type="monotone"
            dataKey="Portfolio Value"
            stroke="#2563eb"
            dot={false}
            strokeWidth={2}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
