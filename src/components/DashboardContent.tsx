import KPICards from './KPICards'
import MainCharts from './MainCharts'
import DataTable from './DataTable'

interface DashboardContentProps {
  selectedView: string
}

export default function DashboardContent({ selectedView }: DashboardContentProps) {
  if (selectedView !== 'Overview') {
    return (
      <div className="flex-1 p-6">
        <h2 className="text-2xl font-semibold mb-4">{selectedView}</h2>
        <p className="text-gray-600">Content for {selectedView} view</p>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto bg-neutral p-6" style={{ width: '1160px' }}>
      <div className="space-y-6">
        {/* Row 1: KPI Cards */}
        <KPICards />

        {/* Row 2: Main Charts */}
        <MainCharts />

        {/* Row 3: Tables */}
        <DataTable />
      </div>
    </div>
  )
}



