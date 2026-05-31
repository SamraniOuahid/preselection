// src/layouts/DashboardLayout.jsx
// Layout du dashboard avec sidebar et topbar
import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from '../components/layout/Sidebar';
import TopBar from '../components/layout/TopBar';

export default function DashboardLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden bg-surface">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="flex-1 flex flex-col lg:ml-64 overflow-hidden transition-[margin] duration-300">
        <TopBar onMenuToggle={() => setSidebarOpen(!sidebarOpen)} />

        <main className="flex-1 overflow-auto w-full max-w-[1400px] mx-auto p-4 sm:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
