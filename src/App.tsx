import { useState } from 'react'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import DashboardContent from './components/DashboardContent'
import SmartFuelRecommender from './components/SmartFuelRecommender'

function App() {
  const [selectedView, setSelectedView] = useState('Overview')
  const [environment, setEnvironment] = useState<'Prod' | 'Pilot'>('Prod')

  return (
    <div className="flex flex-col h-screen overflow-hidden" style={{ width: '1440px', height: '900px' }}>
      <Header environment={environment} setEnvironment={setEnvironment} />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar selectedView={selectedView} setSelectedView={setSelectedView} />
        <DashboardContent selectedView={selectedView} />
        <SmartFuelRecommender />
      </div>
    </div>
  )
}

export default App



