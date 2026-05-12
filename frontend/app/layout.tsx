import type { Metadata } from 'next';
import './globals.css';
import TopbarWrapper from '../components/TopbarWrapper';

export const metadata: Metadata = {
  title: 'СКУД',
  description: 'Система контроля доступа',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body>
        <TopbarWrapper />
        {children}
      </body>
    </html>
  );
}
