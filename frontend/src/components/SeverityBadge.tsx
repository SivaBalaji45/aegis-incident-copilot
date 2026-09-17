const COLORS: Record<string, string> = {
  critical: "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300",
  major: "bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-300",
  minor: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300",
  none: "bg-neutral-100 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400",
}

export function SeverityBadge({ severity }: { severity: string | null }) {
  const key = severity?.toLowerCase() ?? "none"
  const classes = COLORS[key] ?? COLORS.none
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${classes}`}>
      {severity ?? "untriaged"}
    </span>
  )
}
