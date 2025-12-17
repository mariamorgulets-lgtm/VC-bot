import { Navigation, Bookmark, MapPin } from 'lucide-react'
import { useState } from 'react'

interface Station {
  id: number
  name: string
  address: string
  price: number
  savings: number
  distance: string
}

const topStations: Station[] = [
  {
    id: 1,
    name: 'АЗС #18',
    address: 'Ленинградское ш., 45 км',
    price: 48.50,
    savings: 8.2,
    distance: '2.3 km',
  },
  {
    id: 2,
    name: 'АЗС #42',
    address: 'МКАД, 78 км',
    price: 49.20,
    savings: 6.5,
    distance: '5.1 km',
  },
  {
    id: 3,
    name: 'АЗС #7',
    address: 'Волоколамское ш., 12 км',
    price: 47.80,
    savings: 9.1,
    distance: '8.7 km',
  },
]

export default function SmartFuelRecommender() {
  const [savedOffers, setSavedOffers] = useState<Set<number>>(new Set())

  const toggleSave = (id: number) => {
    const newSaved = new Set(savedOffers)
    if (newSaved.has(id)) {
      newSaved.delete(id)
    } else {
      newSaved.add(id)
    }
    setSavedOffers(newSaved)
  }

  return (
    <div
      className="fixed bottom-6 right-6 bg-white rounded-xl shadow-2xl border border-gray-200 z-40"
      style={{ width: '360px', height: '220px' }}
    >
      <div className="p-4 h-full flex flex-col">
        <div className="flex items-center justify-between mb-3">
          <h4 className="font-semibold text-sm">Smart Fuel Recommender</h4>
          <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">Demo</span>
        </div>
        <div className="flex-1 overflow-y-auto space-y-2">
          {topStations.map((station) => (
            <div
              key={station.id}
              className="border border-gray-200 rounded-lg p-2 hover:border-primary transition-colors"
            >
              <div className="flex items-start justify-between mb-1">
                <div className="flex-1">
                  <div className="flex items-center gap-1 mb-0.5">
                    <MapPin className="w-3 h-3 text-gray-400" />
                    <span className="text-xs font-semibold">{station.name}</span>
                  </div>
                  <p className="text-xs text-gray-500 mb-1">{station.address}</p>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-gray-900">₽{station.price}/L</span>
                    <span className="text-xs text-accent">Save {station.savings}%</span>
                    <span className="text-xs text-gray-400">• {station.distance}</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2 mt-2">
                <button
                  className="flex-1 flex items-center justify-center gap-1 px-2 py-1 bg-primary text-white text-xs rounded hover:bg-primary/90 transition-colors"
                  onClick={() => alert(`Navigating to ${station.name}...`)}
                >
                  <Navigation className="w-3 h-3" />
                  Navigate
                </button>
                <button
                  onClick={() => toggleSave(station.id)}
                  className={`px-2 py-1 border rounded text-xs transition-colors ${
                    savedOffers.has(station.id)
                      ? 'border-accent text-accent bg-accent/10'
                      : 'border-gray-300 text-gray-600 hover:border-primary hover:text-primary'
                  }`}
                >
                  <Bookmark className="w-3 h-3" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}



