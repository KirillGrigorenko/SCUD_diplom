interface StatusPillProps {
  status: string;
}

const STATUS_TEXT: Record<string, string> = {
  active: 'Активен',
  blocked: 'Заблокирован',
  fired: 'Уволен',
};

const STATUS_CLASSES: Record<string, string> = {
  active: 'bg-emerald-500/15 text-emerald-300 ring-1 ring-emerald-500/20',
  blocked: 'bg-amber-500/15 text-amber-300 ring-1 ring-amber-500/20',
  fired: 'bg-rose-500/15 text-rose-300 ring-1 ring-rose-500/20',
};

export default function StatusPill({ status }: StatusPillProps) {
  const label = STATUS_TEXT[status] ?? 'Неизвестно';
  const classes = STATUS_CLASSES[status] ?? 'bg-slate-500/15 text-slate-200 ring-1 ring-slate-500/20';

  return <span className={`inline-flex rounded-full px-4 py-2 text-sm font-semibold ${classes}`}>{label}</span>;
}
