'use client';

import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';

interface Option {
  value: string;
  label: string;
}

interface CustomSelectProps {
  value: string;
  onChange: (value: string) => void;
  options: Option[];
  placeholder?: string;
}

export default function CustomSelect({ value, onChange, options, placeholder = 'Выберите...' }: CustomSelectProps) {
  const [open, setOpen] = useState(false);
  const [rect, setRect] = useState<DOMRect | null>(null);
  const [mounted, setMounted] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const dropdownRef = useRef<HTMLUListElement>(null);

  useEffect(() => { setMounted(true); }, []);

  useEffect(() => {
    if (!open) return;
    function onOutside(e: MouseEvent) {
      if (
        triggerRef.current && !triggerRef.current.contains(e.target as Node) &&
        dropdownRef.current && !dropdownRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', onOutside);
    return () => document.removeEventListener('mousedown', onOutside);
  }, [open]);

  function handleOpen() {
    if (triggerRef.current) {
      setRect(triggerRef.current.getBoundingClientRect());
    }
    setOpen((o) => !o);
  }

  const selected = options.find((o) => o.value === value);

  const dropdown = rect && (
    <ul
      ref={dropdownRef}
      style={{
        position: 'fixed',
        top: rect.bottom + 4,
        left: rect.left,
        width: rect.width,
        zIndex: 9999,
      }}
      className="overflow-hidden rounded-2xl border border-sky-500/25 bg-slate-900 py-1.5 shadow-2xl shadow-black/60"
    >
      {options.map((option) => (
        <li
          key={option.value}
          onMouseDown={(e) => e.preventDefault()}
          onClick={() => { onChange(option.value); setOpen(false); }}
          className={`cursor-pointer px-4 py-2.5 text-sm transition ${
            option.value === value
              ? 'bg-sky-500/15 text-sky-300'
              : 'text-slate-200 hover:bg-slate-800'
          }`}
        >
          {option.label}
        </li>
      ))}
    </ul>
  );

  return (
    <div className="relative">
      <button
        ref={triggerRef}
        type="button"
        onClick={handleOpen}
        className="flex w-full items-center justify-between rounded-2xl border border-slate-700 bg-slate-900/90 px-4 py-3 text-left text-slate-100 outline-none transition focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20"
      >
        <span className={selected && selected.value !== '' ? 'text-slate-100' : 'text-slate-500'}>
          {selected ? selected.label : placeholder}
        </span>
        <svg
          className={`ml-2 h-3 w-3 flex-shrink-0 text-slate-400 transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
          viewBox="0 0 12 8"
          fill="none"
        >
          <path d="M1 1l5 5 5-5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </button>

      {mounted && open && dropdown ? createPortal(dropdown, document.body) : null}
    </div>
  );
}
