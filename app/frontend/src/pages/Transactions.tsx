import { useEffect } from 'react'
import { useStore } from '../store'
import { Empty, Pill, money } from '../components/ui'

export default function Transactions() {
  const { transactions, categorization, loadTransactions, categorizeAll, loading } = useStore()

  useEffect(() => { loadTransactions() }, []) // eslint-disable-line

  if (loading.transactions) {
    return <div className="card text-center text-slate-500 text-sm py-10">Loading transactions…</div>
  }

  if (!transactions || transactions.length === 0) {
    return (
      <Empty>No transactions yet — load sample data on Data &amp; Profile.</Empty>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header + categorize button */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h2 className="text-xl font-semibold text-slate-800">
          Transactions
          <span className="ml-2 text-sm font-normal text-slate-500">({transactions.length})</span>
        </h2>
        <button
          className="btn-primary flex items-center gap-2"
          onClick={categorizeAll}
          disabled={!!loading.categorize}
        >
          {loading.categorize && (
            <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          )}
          {loading.categorize ? 'Categorising…' : 'AI categorize all'}
        </button>
      </div>

      {/* Categorization summary */}
      {categorization && (
        <div className="card">
          <div className="flex items-center gap-2 flex-wrap mb-3">
            <Pill tone={categorization.ai_used ? 'green' : 'slate'}>
              {categorization.ai_used ? 'AI' : 'rule-based'}
            </Pill>
            <span className="text-sm text-slate-500">
              {categorization.results?.length ?? 0} transactions categorised
            </span>
          </div>
          {/* Category count chips */}
          {categorization.counts && Object.keys(categorization.counts).length > 0 && (
            <div className="flex flex-wrap gap-2">
              {Object.entries(categorization.counts)
                .sort((a, b) => b[1] - a[1])
                .map(([cat, count]) => (
                  <span
                    key={cat}
                    className="text-xs bg-slate-100 text-slate-600 rounded-full px-2.5 py-0.5"
                  >
                    {cat}: {count}
                  </span>
                ))}
            </div>
          )}
        </div>
      )}

      {/* Transactions table */}
      <div className="card overflow-x-auto p-0">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50">
              <th className="text-left px-4 py-3 font-medium text-slate-600">Date</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600">Description</th>
              <th className="text-right px-4 py-3 font-medium text-slate-600">Amount</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600">Category</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((txn) => (
              <tr key={txn.id} className="border-b border-slate-50 hover:bg-slate-50 transition-colors">
                <td className="px-4 py-2.5 text-slate-500 whitespace-nowrap">{txn.date}</td>
                <td className="px-4 py-2.5 text-slate-700 max-w-xs truncate">{txn.description}</td>
                <td className={`px-4 py-2.5 text-right font-medium whitespace-nowrap ${
                  txn.kind === 'income' ? 'text-emerald-600' : 'text-slate-700'
                }`}>
                  {txn.kind === 'income' ? '+' : ''}{money(txn.amount)}
                </td>
                <td className="px-4 py-2.5">
                  {txn.category ? (
                    <Pill tone="slate">{txn.category}</Pill>
                  ) : (
                    <span className="text-slate-300 text-xs">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
