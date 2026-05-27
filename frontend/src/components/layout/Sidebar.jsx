// src/components/layout/Sidebar.jsx
// Sidebar du dashboard — style ENSA BM institutionnel
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  LayoutDashboard, FolderOpen, FilePlus, User,
  GraduationCap, Settings, X
} from 'lucide-react';

const candidatLinks = [
  { to: '/mes-dossiers',    icon: FolderOpen,     label: 'Mes Dossiers' },
  { to: '/nouveau-dossier', icon: FilePlus,        label: 'Nouveau Dossier' },
  { to: '/profil',          icon: User,            label: 'Mon Profil' },
];

const staffLinks = [
  { to: '/dashboard',       icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/dossiers',        icon: FolderOpen,      label: 'Dossiers' },
  { to: '/filieres',        icon: GraduationCap,   label: 'Filières' },
  { to: '/config-scoring',  icon: Settings,        label: 'Scoring & Règles' },
];

export default function Sidebar({ isOpen, onClose }) {
  const { user, isCandidat, isStaff } = useAuth();
  const links = isCandidat ? candidatLinks : isStaff ? staffLinks : [];

  return (
    <>
      {/* Overlay mobile */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 bg-black/40 z-40 lg:hidden"
        />
      )}

      <aside
        className={`
          w-[260px] min-h-screen flex flex-col
          fixed left-0 top-0 bottom-0 z-50
          transition-transform duration-300 ease-in-out
          ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
        style={{ background: 'linear-gradient(180deg, #0D1F3C 0%, #142D52 100%)' }}
      >
        {/* Logo ENSA réel */}
        <div className="px-5 py-5 border-b border-white/10 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img src="/ensa_logo.png" alt="ENSA BM" className="h-9 w-auto object-contain rounded-md" />
            <div>
              <div className="text-white font-bold text-sm">ENSA BM</div>
              <div className="text-white/40 text-[10px]">Présélection</div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="lg:hidden p-1 rounded text-white/40 hover:text-white hover:bg-white/10 transition-colors"
            aria-label="Fermer le menu"
          >
            <X size={18} />
          </button>
        </div>

        {/* Section label */}
        <div className="px-5 pt-5 pb-2">
          <span className="text-[10px] font-semibold text-white/30 uppercase tracking-wider">
            {isCandidat ? 'Espace Candidat' : 'Administration'}
          </span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-2 flex flex-col gap-1">
          {links.map((link) => {
            const Icon = link.icon;
            return (
              <NavLink
                key={link.to}
                to={link.to}
                onClick={onClose}
                className={({ isActive }) => `
                  flex items-center gap-3 px-3 py-2.5 rounded-lg
                  text-sm font-medium transition-all duration-200 no-underline
                  ${isActive
                    ? 'bg-white/12 text-white shadow-sm'
                    : 'text-white/55 hover:bg-white/8 hover:text-white/80'
                  }
                `}
              >
                <Icon size={18} />
                {link.label}
              </NavLink>
            );
          })}
        </nav>

        {/* Utilisateur connecté */}
        <div className="px-5 py-4 border-t border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold"
              style={{ background: 'linear-gradient(135deg, #2E86C1, #5DADE2)' }}>
              {user?.profil ? user.profil.prenom[0] : user?.email?.[0]?.toUpperCase() || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-white text-xs font-medium truncate">
                {user?.profil ? `${user.profil.prenom} ${user.profil.nom}` : user?.email}
              </div>
              <div className="text-white/40 text-[10px]">
                {user?.role === 'CANDIDAT' ? 'Candidat' :
                 user?.role === 'RESPONSABLE' ? 'Responsable' : 'Administrateur'}
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-white/10 flex items-center justify-between">
          <span className="text-white/30 text-[10px]">© 2025 ENSA BM</span>
          <div className="flex gap-1">
            <div className="w-3 h-1 rounded-full bg-[#006233]/50" />
            <div className="w-3 h-1 rounded-full bg-[#C1272D]/50" />
          </div>
        </div>
      </aside>
    </>
  );
}
