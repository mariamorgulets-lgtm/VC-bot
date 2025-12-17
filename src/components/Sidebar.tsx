import { LayoutDashboard, TrendingUp, Shield, Sparkles, Truck, Settings, HelpCircle } from 'lucide-react'

interface SidebarProps {
  selectedView: string
  setSelectedView: (view: string) => void
}

const menuItems = [
  { id: 'Overview', icon: LayoutDashboard, label: 'Overview' },
  { id: 'KPIs', icon: TrendingUp, label: 'KPIs' },
  { id: 'Fraud', icon: Shield, label: 'Fraud' },
  { id: 'Recommender', icon: Sparkles, label: 'Recommender' },
  { id: 'Fleets', icon: Truck, label: 'Fleets' },
  { id: 'Settings', icon: Settings, label: 'Settings' },
]

export default function Sidebar({ selectedView, setSelectedView }: SidebarProps) {
  return (
    <aside className="bg-white border-r border-gray-200 flex flex-col" style={{ width: '280px' }}>
      <nav className="flex-1 py-4">
        {menuItems.map((item) => {
          const Icon = item.icon
          const isActive = selectedView === item.id
          return (
            <button
              key={item.id}
              onClick={() => setSelectedView(item.id)}
              className={`w-full h-12 flex items-center gap-3 px-6 text-left transition-colors ${
                isActive
                  ? 'bg-primary/10 text-primary border-r-2 border-primary'
                  : 'text-gray-700 hover:bg-gray-50'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span className="font-medium">{item.label}</span>
            </button>
          )
        })}
      </nav>

      <div className="border-t border-gray-200 p-4 space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Pilot Mode</span>
          <label className="relative inline-flex items-center cursor-pointer">
            <input type="checkbox" className="sr-only peer" />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
          </label>
        </div>
        <a
          href="#"
          className="flex items-center gap-2 text-sm text-gray-600 hover:text-primary transition-colors"
        >
          <HelpCircle className="w-4 h-4" />
          <span>Help</span>
        </a>
      </div>
    </aside>
  )
}

