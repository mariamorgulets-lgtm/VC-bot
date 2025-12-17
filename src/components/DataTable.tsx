import { ChevronDown, ChevronRight, CheckCircle, Calendar } from 'lucide-react'
import { useState } from 'react'

interface Transaction {
  id: string
  time: string
  card: string
  driver: string
  station: string
  liters: number
  price: number
  deviation: number
  risk: 'Low' | 'Medium' | 'High'
  reviewed: boolean
  details?: {
    vehicle: string
    route: string
    previousTransactions: number
    timeline: Array<{ time: string; event: string }>
  }
}

const mockTransactions: Transaction[] = [
  {
    id: '1',
    time: '14:32',
    card: '****1234',
    driver: 'Иванов И.И.',
    station: 'АЗС #42',
    liters: 45.2,
    price: 2850,
    deviation: 12.5,
    risk: 'High',
    reviewed: false,
    details: {
      vehicle: 'ГАЗ-3302 (А123БВ)',
      route: 'Москва → Санкт-Петербург',
      previousTransactions: 12,
      timeline: [
        { time: '14:30', event: 'Transaction initiated' },
        { time: '14:31', event: 'Payment processed' },
        { time: '14:32', event: 'Fuel dispensed' },
        { time: '14:33', event: 'Anomaly detected' },
      ],
    },
  },
  {
    id: '2',
    time: '13:15',
    card: '****5678',
    driver: 'Петров П.П.',
    station: 'АЗС #18',
    liters: 38.7,
    price: 2450,
    deviation: -2.1,
    risk: 'Low',
    reviewed: true,
  },
  {
    id: '3',
    time: '12:45',
    card: '****9012',
    driver: 'Сидоров С.С.',
    station: 'АЗС #7',
    liters: 52.3,
    price: 3100,
    deviation: 18.3,
    risk: 'High',
    reviewed: false,
    details: {
      vehicle: 'КАМАЗ-65117 (В456ГД)',
      route: 'Казань → Уфа',
      previousTransactions: 8,
      timeline: [
        { time: '12:43', event: 'Transaction initiated' },
        { time: '12:44', event: 'Payment processed' },
        { time: '12:45', event: 'Fuel dispensed' },
        { time: '12:46', event: 'Anomaly detected' },
      ],
    },
  },
]

export default function DataTable() {
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set())
  const [dateRange, setDateRange] = useState('Today')
  const [region, setRegion] = useState('All')
  const [riskFilter, setRiskFilter] = useState('All')

  const toggleRow = (id: string) => {
    const newExpanded = new Set(expandedRows)
    if (newExpanded.has(id)) {
      newExpanded.delete(id)
    } else {
      newExpanded.add(id)
    }
    setExpandedRows(newExpanded)
  }

  const markAsReviewed = (id: string) => {
    // Simulate audit log entry
    console.log(`Transaction ${id} marked as reviewed. Audit log entry created.`)
    alert(`Transaction ${id} marked as reviewed. Audit log entry created.`)
  }

  const filteredTransactions = mockTransactions.filter((t) => {
    if (riskFilter !== 'All' && t.risk !== riskFilter) return false
    return true
  })

  return (
    <div className="bg-white rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Transactions / Anomalies</h3>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 border border-gray-300 rounded-lg px-3 py-1.5">
            <Calendar className="w-4 h-4 text-gray-400" />
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              className="text-sm border-none outline-none bg-transparent"
            >
              <option>Today</option>
              <option>Last 7 days</option>
              <option>Last 30 days</option>
              <option>Custom range</option>
            </select>
          </div>
          <select
            value={region}
            onChange={(e) => setRegion(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm"
          >
            <option>All Regions</option>
            <option>Moscow</option>
            <option>St. Petersburg</option>
            <option>Kazan</option>
          </select>
          <select
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm"
          >
            <option>All Risk Levels</option>
            <option>Low</option>
            <option>Medium</option>
            <option>High</option>
          </select>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 uppercase">Time</th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 uppercase">Card</th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 uppercase">Driver</th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 uppercase">Station</th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 uppercase">Liters</th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 uppercase">Price</th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 uppercase">Deviation</th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 uppercase">Risk</th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredTransactions.map((transaction) => {
              const isExpanded = expandedRows.has(transaction.id)
              return (
                <>
                  <tr
                    key={transaction.id}
                    className="border-b border-gray-100 hover:bg-gray-50 transition-colors cursor-pointer"
                    onClick={() => toggleRow(transaction.id)}
                  >
                    <td className="py-3 px-4 text-sm">{transaction.time}</td>
                    <td className="py-3 px-4 text-sm font-mono">{transaction.card}</td>
                    <td className="py-3 px-4 text-sm">{transaction.driver}</td>
                    <td className="py-3 px-4 text-sm">{transaction.station}</td>
                    <td className="py-3 px-4 text-sm">{transaction.liters}L</td>
                    <td className="py-3 px-4 text-sm">₽{transaction.price.toLocaleString()}</td>
                    <td className="py-3 px-4 text-sm">
                      <span
                        className={`font-medium ${
                          transaction.deviation > 0 ? 'text-danger' : 'text-accent'
                        }`}
                      >
                        {transaction.deviation > 0 ? '+' : ''}
                        {transaction.deviation}%
                      </span>
                    </td>
                    <td className="py-3 px-4 text-sm">
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-medium ${
                          transaction.risk === 'High'
                            ? 'bg-danger/10 text-danger'
                            : transaction.risk === 'Medium'
                            ? 'bg-yellow-100 text-yellow-700'
                            : 'bg-accent/10 text-accent'
                        }`}
                      >
                        {transaction.risk}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-sm">
                      <div className="flex items-center gap-2">
                        {isExpanded ? (
                          <ChevronDown className="w-4 h-4 text-gray-400" />
                        ) : (
                          <ChevronRight className="w-4 h-4 text-gray-400" />
                        )}
                        {!transaction.reviewed && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              markAsReviewed(transaction.id)
                            }}
                            className="text-xs text-primary hover:text-primary/80 font-medium"
                          >
                            Mark as reviewed
                          </button>
                        )}
                        {transaction.reviewed && (
                          <CheckCircle className="w-4 h-4 text-accent" />
                        )}
                      </div>
                    </td>
                  </tr>
                  {isExpanded && transaction.details && (
                    <tr>
                      <td colSpan={9} className="py-4 px-4 bg-gray-50">
                        <div className="grid grid-cols-2 gap-4 mb-4">
                          <div>
                            <p className="text-xs text-gray-500 mb-1">Vehicle</p>
                            <p className="text-sm font-medium">{transaction.details.vehicle}</p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500 mb-1">Route</p>
                            <p className="text-sm font-medium">{transaction.details.route}</p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500 mb-1">Previous Transactions</p>
                            <p className="text-sm font-medium">{transaction.details.previousTransactions}</p>
                          </div>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500 mb-2 font-semibold">Timeline</p>
                          <div className="space-y-2">
                            {transaction.details.timeline.map((item, idx) => (
                              <div key={idx} className="flex items-center gap-3 text-sm">
                                <span className="text-gray-400 font-mono text-xs">{item.time}</span>
                                <span className="text-gray-600">{item.event}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

