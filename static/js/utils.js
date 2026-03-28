const DATE_FMT = new Intl.DateTimeFormat(undefined, {
  month: "short", day: "numeric",
  hour: "numeric", minute: "2-digit",
});

export function formatDateTime(isoStr) {
  return DATE_FMT.format(new Date(isoStr));
}

export function timeUntil(isoStr) {
  const diffMs = new Date(isoStr) - Date.now();
  if (diffMs <= 0) return null;
  const mins = Math.floor(diffMs / 60_000);
  if (mins < 60)   return `${mins}m`;
  if (mins < 1440) return `${Math.floor(mins / 60)}h ${mins % 60}m`;
  return `${Math.floor(mins / 1440)}d`;
}
