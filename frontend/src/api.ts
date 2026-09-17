export interface Incident {
  id: string
  provider_slug: string
  title: string
  url: string | null
  status: string
  impact: string | null
  triage_severity: string | null
  triage_category: string | null
  started_at: string | null
  updated_at: string | null
  pipeline_processed: boolean
}

export interface Citation {
  chunk_id: string
  source_name: string
  quote: string
}

export interface Diagnosis {
  id: string
  incident_id: string
  hypothesis: string
  confidence: number
  citations: Citation[]
  groundedness_score: number | null
  critic_verdict: string | null
  critic_iterations: number
  draft_external_update: string
  draft_internal_checklist: string[]
  status: string
  reviewed_by: string | null
  created_at: string
}

const BASE = "/api"

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText}: ${await res.text()}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  listIncidents: (): Promise<Incident[]> =>
    fetch(`${BASE}/incidents`).then((res) => json<Incident[]>(res)),

  listDiagnoses: (incidentId: string): Promise<Diagnosis[]> =>
    fetch(`${BASE}/incidents/${incidentId}/diagnoses`).then((res) => json<Diagnosis[]>(res)),

  reviewDiagnosis: (
    diagnosisId: string,
    reviewer: string,
    approve: boolean,
    notes?: string,
  ): Promise<Diagnosis> =>
    fetch(`${BASE}/diagnoses/${diagnosisId}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reviewer, approve, notes }),
    }).then((res) => json<Diagnosis>(res)),
}
