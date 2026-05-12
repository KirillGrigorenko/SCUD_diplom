'use client';

import { usePathname } from 'next/navigation';
import Topbar from './Topbar';

const NO_TOPBAR = ['/login', '/'];

export default function TopbarWrapper() {
  const pathname = usePathname();
  if (NO_TOPBAR.includes(pathname)) return null;
  return <Topbar />;
}
