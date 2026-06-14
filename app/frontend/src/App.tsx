import { useEffect, useState } from 'react'
import Sidebar from './components/Sidebar'
import Header from './components/Header'
import AuthModal from './components/AuthModal'
import { useStore } from './store'
import Dashboard from './pages/Dashboard'
import DataAndProfile from './pages/DataAndProfile'
import Transactions from './pages/Transactions'
import AnalyticsView from './pages/AnalyticsView'
import DebtAnalysis from './pages/DebtAnalysis'
import SavingsPlanner from './pages/SavingsPlanner'
import BudgetAnalysis from './pages/BudgetAnalysis'
import InvestmentAdvisor from './pages/InvestmentAdvisor'
import PortfolioOptimizer from './pages/PortfolioOptimizer'
import IndiaFinance from './pages/IndiaFinance'
import Goals from './pages/Goals'
import Coach from './pages/Coach'

export default function App() {
  const { view, init, error } = useStore()
  const [authOpen, setAuthOpen] = useState(false)
  useEffect(() => {
    init()
  }, [init])

  const page = {
    dashboard: <Dashboard />,
    data: <DataAndProfile />,
    transactions: <Transactions />,
    analytics: <AnalyticsView />,
    debt: <DebtAnalysis />,
    savings: <SavingsPlanner />,
    budget: <BudgetAnalysis />,
    investment: <InvestmentAdvisor />,
    portfolio: <PortfolioOptimizer />,
    india: <IndiaFinance />,
    goals: <Goals />,
    coach: <Coach />,
  }[view]

  return (
    <div className="flex h-full">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Header onSignIn={() => setAuthOpen(true)} />
        {error && (
          <div className="bg-rose-50 text-rose-700 text-sm px-8 py-2 border-b border-rose-200">
            {error}
          </div>
        )}
        <main className="flex-1 overflow-y-auto p-8">{page}</main>
      </div>
      {authOpen && <AuthModal onClose={() => setAuthOpen(false)} />}
    </div>
  )
}
