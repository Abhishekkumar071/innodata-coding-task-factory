
import { useState } from 'react'
import PipelineRunner from './features/pipeline/PipelineRunner'
import VariationsTable from './features/variations/VariationsTable'
import TaskInspector from './features/task-inspector/TaskInspector'

type ActivePage = 'pipeline' | 'variations' | 'inspector'

const navigation = [
  {
    id: 'pipeline' as ActivePage,
    label: 'Pipeline Runner',
    number: '01',
    description: 'Configure and monitor task generation',
  },
  {
    id: 'variations' as ActivePage,
    label: 'Variations',
    number: '02',
    description: 'Explore generated coding tasks',
  },
  {
    id: 'inspector' as ActivePage,
    label: 'Task Inspector',
    number: '03',
    description: 'Inspect task files and validation',
  },
]

function App() {
  const [activePage, setActivePage] = useState<ActivePage>('pipeline')

  const currentPage = navigation.find(
    (item) => item.id === activePage
  )!

  const renderPage = () => {
    switch (activePage) {
      case 'pipeline':
        return <PipelineRunner />
      case 'variations':
        return <VariationsTable />
      case 'inspector':
        return <TaskInspector />
    }
  }

  return (
    <div className="min-h-screen bg-[#080d18] text-slate-100">
      <div className="flex min-h-screen">

        {/* Sidebar */}
        <aside className="hidden w-[260px] shrink-0 border-r border-white/[0.07] bg-[#0c1322] lg:flex lg:flex-col">

          <div className="border-b border-white/[0.07] px-6 py-7">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-lg font-bold shadow-lg shadow-blue-600/20">
                C
              </div>
              <div>
                <h1 className="text-base font-bold tracking-tight text-white">
                  Coding Task
                </h1>
                <p className="text-xs font-medium text-slate-500">
                  FACTORY CONTROL ROOM
                </p>
              </div>
            </div>
          </div>

          <div className="px-4 pt-8">
            <p className="mb-3 px-3 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">
              Workspace
            </p>

            <nav className="space-y-2">
              {navigation.map((item) => {
                const isActive = activePage === item.id

                return (
                  <button
                    key={item.id}
                    onClick={() => setActivePage(item.id)}
                    className={`group flex w-full items-center gap-3 rounded-xl border px-3 py-3 text-left transition-all duration-200 ${
                      isActive
                        ? 'border-blue-500/20 bg-blue-500/10 text-white'
                        : 'border-transparent text-slate-400 hover:border-white/[0.06] hover:bg-white/[0.04] hover:text-white'
                    }`}
                  >
                    <span
                      className={`flex h-9 w-9 items-center justify-center rounded-lg text-xs font-bold ${
                        isActive
                          ? 'bg-blue-500 text-white'
                          : 'bg-slate-800 text-slate-400 group-hover:bg-slate-700'
                      }`}
                    >
                      {item.number}
                    </span>

                    <span className="min-w-0 flex-1">
                      <span className="block text-sm font-semibold">
                        {item.label}
                      </span>
                      <span className="mt-1 block text-[11px] text-slate-500">
                        {item.description}
                      </span>
                    </span>

                    {isActive && (
                      <span className="h-2 w-2 rounded-full bg-blue-400" />
                    )}
                  </button>
                )
              })}
            </nav>
          </div>

          <div className="mt-auto border-t border-white/[0.07] p-5">
            <div className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-4">
              <p className="text-xs font-semibold text-slate-300">
                Innodata Hackathon
              </p>
              <p className="mt-1 text-[11px] text-slate-500">
                Coding Task Factory · Track 1
              </p>
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="min-w-0 flex-1">

          {/* Top Header */}
          <header className="sticky top-0 z-20 border-b border-white/[0.07] bg-[#0b1220]/95 backdrop-blur-xl">
            <div className="flex flex-wrap items-center justify-between gap-4 px-5 py-4 sm:px-8">

              <div>
                <div className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-emerald-400" />
                  <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">
                    INNODATA / CODING TASK FACTORY
                  </p>
                </div>

                <h2 className="mt-2 text-xl font-bold tracking-tight text-white sm:text-2xl">
                  Control Room
                </h2>
              </div>

              <div className="flex items-center gap-3">
                <span className="rounded-full border border-amber-400/20 bg-amber-400/[0.08] px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-amber-300">
                  Mock Preview
                </span>

                <div className="hidden h-9 w-9 items-center justify-center rounded-full border border-white/10 bg-slate-800 text-xs font-bold text-slate-300 sm:flex">
                  CT
                </div>
              </div>
            </div>

            {/* Mobile Navigation */}
            <nav className="flex gap-2 overflow-x-auto border-t border-white/[0.05] px-5 py-3 lg:hidden">
              {navigation.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setActivePage(item.id)}
                  className={`shrink-0 rounded-lg px-4 py-2 text-xs font-semibold transition ${
                    activePage === item.id
                      ? 'bg-blue-600 text-white'
                      : 'bg-white/[0.04] text-slate-400 hover:bg-white/[0.08]'
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </nav>
          </header>

          {/* Page Content */}
          <div className="mx-auto w-full max-w-[1600px] px-5 py-8 sm:px-8 sm:py-10">

            <div className="mb-8">
              <p className="text-xs font-medium text-blue-400">
                WORKSPACE / {currentPage.number}
              </p>

              <h3 className="mt-2 text-2xl font-bold tracking-tight text-white sm:text-3xl">
                {currentPage.label}
              </h3>

              <p className="mt-2 text-sm text-slate-400">
                {currentPage.description}
              </p>
            </div>

            <div className="animate-in fade-in duration-300">
              {renderPage()}
            </div>

            <footer className="mt-12 border-t border-white/[0.06] pt-5">
              <p className="text-center text-[11px] text-slate-600">
                INNODATA · CODING TASK FACTORY
              </p>
            </footer>
          </div>
        </main>
      </div>
    </div>
  )
}

export default App
