import { TrendingUp, TrendingDown, DollarSign, Activity, AlertTriangle, Users } from 'lucide-react'
import { useState } from 'react'

interface KPICardProps {
  title: string
  value: string
  delta: number
  icon: React.ReactNode
  onClick: () => void
}

function KPICard({ title, value, delta, icon, onClick }: KPICardProps) {
  const isPositive = delta >= 0

  return (
    <div
      onClick={onClick}
      className="bg-white rounded-xl p-4.5 cursor-pointer hover:shadow-lg transition-shadow border border-gray-100"
      style={{ height: '120px', padding: '18px' }}
    >
      <div className="flex items-start justify-between mb-2">
        <span className="text-xs font-medium text-gray-600">{title}</span>
        <div className="text-gray-400">{icon}</div>
      </div>
      <div className="text-3xl font-bold text-gray-900 mb-2" style={{ fontSize: '28px' }}>
        {value}
      </div>
      <div className="flex items-center gap-1">
        <div
          className={`px-2 py-0.5 rounded-full text-xs font-medium flex items-center gap-1 ${
            isPositive
              ? 'bg-accent/10 text-accent'
              : 'bg-danger/10 text-danger'
          }`}
        >
          {isPositive ? (
            <TrendingUp className="w-3 h-3" />
          ) : (
            <TrendingDown className="w-3 h-3" />
          )}
          {Math.abs(delta)}%
        </div>
        <span className="text-xs text-gray-500">vs last period</span>
      </div>
    </div>
  )
}

export default function KPICards() {
  const [selectedKPI, setSelectedKPI] = useState<string | null>(null)

  const kpis = [
    {
      id: 'revenue',
      title: 'Total Revenue',
      value: '₽12.4M',
      delta: 12.5,
      icon: <DollarSign className="w-5 h-5" />,
    },
    {
      id: 'transactions',
      title: 'Transactions',
      value: '8,234',
      delta: -3.2,
      icon: <Activity className="w-5 h-5" />,
    },
    {
      id: 'anomalies',
      title: 'Anomalies',
      value: '47',
      delta: 8.1,
      icon: <AlertTriangle className="w-5 h-5" />,
    },
    {
      id: 'active_drivers',
      title: 'Active Drivers',
      value: '1,234',
      delta: 5.7,
      icon: <Users className="w-5 h-5" />,
    },
  ]

  return (
    <>
      <div className="grid grid-cols-4 gap-5" style={{ gap: '20px' }}>
        {kpis.map((kpi) => (
          <KPICard
            key={kpi.id}
            title={kpi.title}
            value={kpi.value}
            delta={kpi.delta}
            icon={kpi.icon}
            onClick={() => setSelectedKPI(kpi.id)}
          />
        ))}
      </div>

      {selectedKPI && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setSelectedKPI(null)}>
          <div className="bg-white rounded-xl p-6 max-w-2xl w-full mx-4" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-xl font-semibold mb-4">Drill-down Report: {kpis.find(k => k.id === selectedKPI)?.title}</h3>
            <p className="text-gray-600 mb-4">Detailed analysis and metrics for this KPI...</p>
            <button
              onClick={() => setSelectedKPI(null)}
              className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </>
  )
}



