// src/components/layout/TopBar.jsx
// Topbar du dashboard — style ENSA BM institutionnel
import { useAuth } from '../../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { Menu, LogOut, Building2, User } from 'lucide-react';
import ClochNotifications from '../notifications/ClochNotifications';

export default function TopBar({ onMenuToggle, title }) {
  const { user, logout, isCandidat } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <header className="h-16 bg-white border-b border-border flex items-center justify-between px-6 sticky top-0 z-30">
      {/* Gauche */}
      <div className="flex items-center gap-4">
        <button
          onClick={onMenuToggle}
          className="p-2 rounded-md hover:bg-gray-100 text-text-secondary transition-colors lg:hidden"
          aria-label="Menu"
        >
          <Menu size={20} />
        </button>
        <div className="hidden sm:flex items-center gap-2">
          <Building2 size={18} className="text-primary-500" />
          <h1 className="text-base font-bold text-primary-700">
            {title || 'Plateforme de Présélection'}
          </h1>
        </div>
      </div>

      {/* Droite */}
      <div className="flex items-center gap-3">
        {/* Séparateur */}
        <div className="w-px h-8 bg-border hidden sm:block" />

        {/* Info utilisateur */}
        {user && (
          <div className="flex items-center gap-3">
            <div className="text-right hidden sm:block">
              <div className="text-xs font-semibold text-text-primary">
                {user.profil ? `${user.profil.prenom} ${user.profil.nom}` : user.email}
              </div>
              <div className="text-[10px] text-text-muted">
                {user.role === 'CANDIDAT' ? 'Candidat' :
                 user.role === 'RESPONSABLE' ? 'Responsable' : 'Administrateur'}
              </div>
            </div>
            {isCandidat && (
              <Link to="/profil" className="btn btn-ghost btn-sm hidden sm:inline-flex" title="Mon profil">
                <User size={16} /> Profil
              </Link>
            )}
            <div className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold"
              style={{ background: 'linear-gradient(135deg, #1B3A6B, #2E86C1)' }}>
              {user.profil ? user.profil.prenom[0] : user.email[0].toUpperCase()}
            </div>
            
            {/* Cloche de notifications */}
            <ClochNotifications />

            <button
              onClick={handleLogout}
              className="btn btn-ghost btn-sm text-text-muted hover:text-danger-500"
              title="Déconnexion"
            >
              <LogOut size={16} />
              <span className="hidden sm:inline">Déconnexion</span>
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
