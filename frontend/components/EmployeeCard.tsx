import Link from 'next/link';
import StatusPill from './StatusPill';

interface EmployeeCardProps {
  employee: {
    id: number;
    full_name: string;
    hire_date: string;
    status: string;
    photo_url: string;
    position?: string;
    department?: string;
  };
}

export default function EmployeeCard({ employee }: EmployeeCardProps) {
  return (
    <Link
      href={`/employees/${employee.id}`}
      className="group block overflow-hidden rounded-[2rem] border border-slate-700 bg-slate-950/80 p-6 shadow-lg shadow-slate-950/30 transition hover:-translate-y-1 hover:border-sky-500"
    >
      <div className="flex items-center gap-4">
        <img
          src={employee.photo_url}
          alt={employee.full_name}
          className="h-20 w-20 rounded-3xl object-cover ring-1 ring-slate-700"
        />
        <div className="flex-1">
          <h3 className="text-xl font-semibold text-white">{employee.full_name}</h3>
          <p className="mt-2 text-sm text-slate-400">Нанят: {employee.hire_date}</p>
          {employee.position || employee.department ? (
            <p className="mt-2 text-sm text-slate-300">
              {employee.position ?? 'Позиция неизвестна'}
              {employee.department ? ` • ${employee.department}` : ''}
            </p>
          ) : null}
        </div>
      </div>

      <div className="mt-5 flex items-center justify-between gap-4">
        <StatusPill status={employee.status} />
        <span className="text-sm text-slate-400 transition group-hover:text-slate-200">Подробнее →</span>
      </div>
    </Link>
  );
}
