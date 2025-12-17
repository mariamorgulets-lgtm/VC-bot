import { Search, Bell, User } from 'lucide-react'

interface HeaderProps {
  environment: 'Prod' | 'Pilot'
  setEnvironment: (env: 'Prod' | 'Pilot') => void
}

export default function Header({ environment, setEnvironment }: HeaderProps) {
  return (
    <header className="bg-white border-b border-gray-200 h-16 flex items-center justify-between px-6 w-full">
      {/* Left: Logo + Title */}
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 bg-primary rounded-lg flex items-center justify-center text-white font-bold text-xl">
          X/Y
        </div>
        <h1 className="text-xl font-semibold text-gray-900">AI Operations Dashboard</h1>
      </div>

      {/* Center: Global Search */}
      <div className="flex-1 flex justify-center">
        <div className="relative" style={{ width: '520px' }}>
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Search..."
            className="w-full h-9 pl-10 pr-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
            style={{ height: '36px' }}
          />
        </div>
      </div>

      {/* Right: Notifications, Profile, Environment Toggle */}
      <div className="flex items-center gap-4">
        <button className="relative p-2 hover:bg-gray-100 rounded-lg transition-colors">
          <Bell className="w-7 h-7 text-gray-600" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-danger rounded-full"></span>
        </button>
        
        <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
          <User className="w-6 h-6 text-primary" />
        </div>

        <div className="flex items-center gap-2 bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setEnvironment('Prod')}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              environment === 'Prod'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Prod
          </button>
          <button
            onClick={() => setEnvironment('Pilot')}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              environment === 'Pilot'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Pilot
          </button>
        </div>
      </div>
    </header>
  )
}



