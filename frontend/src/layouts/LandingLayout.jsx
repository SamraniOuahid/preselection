// src/layouts/LandingLayout.jsx
// Layout avec barre info + Navbar publique et Footer pour la landing page
import { Outlet } from 'react-router-dom';
import Navbar from '../components/layout/Navbar';
import Footer from '../components/layout/Footer';

export default function LandingLayout() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      {/* pt-[96px] = 32px top bar + 64px navbar */}
      <main className="flex-1 pt-[96px]">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}
