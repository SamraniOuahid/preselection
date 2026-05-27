// src/layouts/DashboardLayout.jsx
// Layout du dashboard avec sidebar et topbar
import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from '../components/layout/Sidebar';
import TopBar from '../components/layout/TopBar';

export default function DashboardLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-surface">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="flex-1 flex flex-col ensa-main-content transition-[margin] duration-300">
        <TopBar onMenuToggle={() => setSidebarOpen(!sidebarOpen)} />

        <main className="flex-1 w-full max-w-[1400px] mx-auto px-4 py-5 sm:px-6 sm:py-6 lg:px-8 lg:py-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
