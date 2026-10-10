import 'bootstrap/dist/css/bootstrap.min.css';
import './styles.css';
import type { Metadata } from 'next';
export const metadata: Metadata = { title: 'Carewell | Clinic appointments', description: 'Book and manage clinic appointments and billing.' };
export default function RootLayout({ children }: { children: React.ReactNode }) { return <html lang="en"><body>{children}</body></html>; }
