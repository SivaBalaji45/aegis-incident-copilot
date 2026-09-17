import { useEffect, useState } from "react"
import { api, type Diagnosis, type Incident } from "./api"
import { IncidentList } from "./components/IncidentList"
import { DiagnosisPanel } from "./components/DiagnosisPanel"

const REVIEWER = "sivabalajiadigopula@gmail.com"

export default function App() {
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [diagnoses, setDiagnoses] = useState<Diagnosis[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .listIncidents()
      .then((data) => {
        setIncidents(data)
        setError(null)
      })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (!selectedId) return
    api
      .listDiagnoses(selectedId)
      .then(setDiagnoses)
      .catch((e) => setError(String(e)))
  }, [selectedId])

  const handleReview = async (diagnosisId: string, approve: boolean, notes?: string) => {
    const updated = await api.reviewDiagnosis(diagnosisId, REVIEWER, approve, notes)
    setDiagnoses((prev) => prev.map((d) => (d.id === updated.id ? updated : d)))
  }

  const selected = incidents.find((i) => i.id === selectedId) ?? null

  return (
    <div className="min-h-screen bg-white text-neutral-900 dark:bg-neutral-950 dark:text-neutral-100">
      <header className="border-b border-neutral-200 px-6 py-4 dark:border-neutral-800">
        <h1 className="text-lg font-semibold">Aegis Incident Copilot</h1>
        <p className="text-xs text-neutral-500">
          Every draft below was checked by a critic agent against retrieved evidence before it
          reached this screen — nothing publishes without your approval.
        </p>
      </header>

      {error && (
        <div className="mx-6 mt-4 rounded border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-800 dark:bg-red-950/40 dark:text-red-300">
          {error.includes("Failed to fetch") || error.includes("502")
            ? "Can't reach the API. Is the backend running (uvicorn aegis.api.main:app)?"
            : error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-[320px_1fr]">
        <aside className="border-r border-neutral-200 dark:border-neutral-800">
          {loading ? (
            <p className="p-4 text-sm text-neutral-500">Loading incidents…</p>
          ) : (
            <IncidentList incidents={incidents} selectedId={selectedId} onSelect={setSelectedId} />
          )}
        </aside>

        <main className="p-6">
          {!selected && (
            <p className="text-sm text-neutral-500">Select an incident to review its diagnoses.</p>
          )}

          {selected && (
            <div>
              <h2 className="text-base font-semibold">{selected.title}</h2>
              <p className="mt-1 text-xs text-neutral-500">
                {selected.provider_slug} · {selected.status}
                {selected.url && (
                  <>
                    {" · "}
                    <a
                      href={selected.url}
                      target="_blank"
                      rel="noreferrer"
                      className="underline hover:text-neutral-700 dark:hover:text-neutral-300"
                    >
                      source
                    </a>
                  </>
                )}
              </p>

              <div className="mt-4 space-y-3">
                {diagnoses.length === 0 && (
                  <p className="text-sm text-neutral-500">
                    No diagnosis run yet for this incident (pipeline may still be processing).
                  </p>
                )}
                {diagnoses.map((d) => (
                  <DiagnosisPanel key={d.id} diagnosis={d} onReview={handleReview} />
                ))}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
