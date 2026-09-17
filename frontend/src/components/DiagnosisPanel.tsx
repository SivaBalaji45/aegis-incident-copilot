import { useState } from "react"
import type { Diagnosis } from "../api"

interface Props {
  diagnosis: Diagnosis
  onReview: (diagnosisId: string, approve: boolean, notes?: string) => Promise<void>
}

const STATUS_STYLES: Record<string, string> = {
  pending_review: "border-blue-300 dark:border-blue-800",
  needs_human_review: "border-amber-300 dark:border-amber-800",
  approved: "border-green-300 dark:border-green-800",
  rejected: "border-red-300 dark:border-red-800",
}

export function DiagnosisPanel({ diagnosis, onReview }: Props) {
  const [notes, setNotes] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const canReview = diagnosis.status === "pending_review" || diagnosis.status === "needs_human_review"

  const handle = async (approve: boolean) => {
    setSubmitting(true)
    try {
      await onReview(diagnosis.id, approve, notes || undefined)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div
      className={`rounded-lg border p-4 ${STATUS_STYLES[diagnosis.status] ?? "border-neutral-300 dark:border-neutral-700"}`}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wide text-neutral-500">
          {diagnosis.status.replace(/_/g, " ")}
        </span>
        {diagnosis.groundedness_score !== null && (
          <span className="text-xs text-neutral-500">
            groundedness {diagnosis.groundedness_score.toFixed(2)} · {diagnosis.critic_iterations}{" "}
            critic pass{diagnosis.critic_iterations === 1 ? "" : "es"}
          </span>
        )}
      </div>

      <p className="mt-2 text-sm text-neutral-900 dark:text-neutral-100">{diagnosis.hypothesis}</p>
      <p className="mt-1 text-xs text-neutral-500">confidence {diagnosis.confidence.toFixed(2)}</p>

      {diagnosis.citations.length > 0 && (
        <div className="mt-3 space-y-1.5">
          {diagnosis.citations.map((c, i) => (
            <blockquote
              key={i}
              className="border-l-2 border-neutral-300 pl-2 text-xs italic text-neutral-600 dark:border-neutral-700 dark:text-neutral-400"
            >
              "{c.quote}" — {c.source_name}
            </blockquote>
          ))}
        </div>
      )}

      {diagnosis.draft_external_update && (
        <div className="mt-3 rounded bg-neutral-50 p-2.5 text-xs dark:bg-neutral-900">
          <p className="font-semibold text-neutral-600 dark:text-neutral-300">Draft external update</p>
          <p className="mt-1 text-neutral-700 dark:text-neutral-300">{diagnosis.draft_external_update}</p>
        </div>
      )}

      {diagnosis.draft_internal_checklist.length > 0 && (
        <div className="mt-2">
          <p className="text-xs font-semibold text-neutral-600 dark:text-neutral-300">
            Internal remediation checklist
          </p>
          <ul className="mt-1 list-disc pl-4 text-xs text-neutral-700 dark:text-neutral-300">
            {diagnosis.draft_internal_checklist.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ul>
        </div>
      )}

      {canReview ? (
        <div className="mt-3 space-y-2">
          <input
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Reviewer notes (optional)"
            className="w-full rounded border border-neutral-300 px-2 py-1 text-xs dark:border-neutral-700 dark:bg-neutral-900"
          />
          <div className="flex gap-2">
            <button
              disabled={submitting}
              onClick={() => handle(true)}
              className="rounded bg-green-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-green-700 disabled:opacity-50"
            >
              Approve
            </button>
            <button
              disabled={submitting}
              onClick={() => handle(false)}
              className="rounded bg-red-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-700 disabled:opacity-50"
            >
              Reject
            </button>
          </div>
        </div>
      ) : (
        diagnosis.reviewed_by && (
          <p className="mt-3 text-xs text-neutral-500">reviewed by {diagnosis.reviewed_by}</p>
        )
      )}
    </div>
  )
}
