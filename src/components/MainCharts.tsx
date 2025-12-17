import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { AlertTriangle, Lightbulb, ArrowRight, Search } from 'lucide-react'
import { useState } from 'react'

const chartData = [
  { date: 'Mon', volume: 1200, revenue: 2400, margin: 1800 },
  { date: 'Tue', volume: 1900, revenue: 3800, margin: 2900 },
  { date: 'Wed', volume: 1500, revenue: 3000, margin: 2200 },
  { date: 'Thu', volume: 2100, revenue: 4200, margin: 3200 },
  { date: 'Fri', volume: 1800, revenue: 3600, margin: 2700 },
  { date: 'Sat', volume: 1600, revenue: 3200, margin: 2400 },
  { date: 'Sun', volume: 1400, revenue: 2800, margin: 2100 },
]

const aiInsights = [
  {
    id: 1,
    icon: <AlertTriangle className="w-5 h-5 text-danger" />,
    title: 'Unusual fuel consumption pattern detected',
    text: 'Station #42 shows 15% higher consumption than average. Possible leak or meter issue. Recommend inspection within 24h.',
    action: 'Investigate',
  },
  {
    id: 2,
    icon: <Lightbulb className="w-5 h-5 text-accent" />,
    title: 'Optimize route for Fleet A',
    text: 'AI suggests rerouting 3 vehicles through Station #18 to save 8% on fuel costs. Estimated savings: ₽45,000/month.',
    action: 'Apply',
  },
  {
    id: 3,
    icon: <Search className="w-5 h-5 text-primary" />,
    title: 'Price anomaly detected',
    text: 'Station #7 pricing 5% below market average. Verify supplier contract and consider bulk purchase opportunity.',
    action: 'Investigate',
  },
]

export default function MainCharts() {
  const [period, setPeriod] = useState<'Day' | 'Week' | 'Month'>('Week')

  const handleApplyRecommendation = (id: number) => {
    // Simulate workflow initiation
    alert(`Workflow initiated for recommendation #${id}. Task created in Jira / Email sent to manager.`)
  }

  return (
    <div className="flex gap-5" style={{ gap: '20px' }}>
      {/* Left: Line Chart - 2/3 width */}
      <div className="bg-white rounded-xl p-6 flex-1" style={{ flex: '2' }}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Volume / Revenue / Margin</h3>
          <div className="flex items-center gap-2 bg-gray-100 rounded-lg p-1">
            {(['Day', 'Week', 'Month'] as const).map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                  period === p
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                {p}
              </button>
            ))}
          </div>
        </div>
        <div style={{ width: '760px', height: '320px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="date" stroke="#6b7280" />
              <YAxis stroke="#6b7280" />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="volume"
                stroke="#0B5FFF"
                strokeWidth={2}
                name="Volume (L)"
                dot={{ r: 4 }}
              />
              <Line
                type="monotone"
                dataKey="revenue"
                stroke="#00A86B"
                strokeWidth={2}
                name="Revenue (₽)"
                dot={{ r: 4 }}
              />
              <Line
                type="monotone"
                dataKey="margin"
                stroke="#E53E3E"
                strokeWidth={2}
                name="Margin (₽)"
                dot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Right: AI Insights - 1/3 width */}
      <div className="bg-white rounded-xl p-6" style={{ flex: '1', width: '380px' }}>
        <h3 className="text-lg font-semibold mb-4">AI Insights</h3>
        <div className="space-y-4">
          {aiInsights.map((insight) => (
            <div
              key={insight.id}
              className="border border-gray-200 rounded-lg p-4 hover:border-primary transition-colors"
            >
              <div className="flex items-start gap-3 mb-2">
                <div className="mt-0.5">{insight.icon}</div>
                <div className="flex-1">
                  <h4 className="font-semibold text-sm mb-2">{insight.title}</h4>
                  <p className="text-xs text-gray-600 leading-relaxed mb-3" style={{ lineHeight: '1.5' }}>
                    {insight.text}
                  </p>
                  <button
                    onClick={() => handleApplyRecommendation(insight.id)}
                    className="flex items-center gap-1 text-xs font-medium text-primary hover:text-primary/80 transition-colors"
                  >
                    {insight.action}
                    <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

