import type { Incident } from "../api"
import { SeverityBadge } from "./SeverityBadge"

interface Props {
  incidents: Incident[]
  selectedId: string | null
  onSelect: (id: string) => void
}

export function IncidentList({ incidents, selectedId, onSelect }: Props) {
  if (incidents.length === 0) {
    return (
      <p className="p-4 text-sm text-neutral-500 dark:text-neutral-400">
        No incidents yet. The poller checks provider status pages every few minutes.
      </p>
    )
  }

  return (
    <ul className="divide-y divide-neutral-200 dark:divide-neutral-800">
      {incidents.map((incident) => (
        <li key={incident.id}>
          <button
            onClick={() => onSelect(incident.id)}
            className={`block w-full px-4 py-3 text-left transition hover:bg-neutral-50 dark:hover:bg-neutral-900 ${
              selectedId === incident.id ? "bg-neutral-100 dark:bg-neutral-900" : ""
            }`}
          >
            <div className="flex items-center justify-between gap-2">
              <span className="text-xs font-semibold uppercase tracking-wide text-neutral-400">
                {incident.provider_slug}
              </span>
              <SeverityBadge severity={incident.triage_severity} />
            </div>
            <p className="mt-1 truncate text-sm font-medium text-neutral-900 dark:text-neutral-100">
              {incident.title}
            </p>
            <p className="mt-0.5 text-xs text-neutral-500 dark:text-neutral-400">
              {incident.status}
              {!incident.pipeline_processed && " · pipeline pending"}
            </p>
          </button>
        </li>
      ))}
    </ul>
  )
}
