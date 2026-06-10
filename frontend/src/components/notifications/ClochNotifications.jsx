// src/components/notifications/ClochNotifications.jsx
import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Bell, CheckCircle, XCircle, FileText, AlertTriangle, Paperclip, Check
} from 'lucide-react';
import {
  getMesNotifications, getNonLuesCount, marquerLue, marquerToutesLues
} from '../../api/notifications';
import { getDossiers } from '../../api/dossiers';

const TYPE_ICONS = {
  PRESELECTION: { Icon: CheckCircle, color: 'text-success-500 bg-success-50 border-success-100' },
  REJET_AUTO: { Icon: XCircle, color: 'text-danger-500 bg-danger-50 border-danger-100' },
  REJET_MANUEL: { Icon: XCircle, color: 'text-danger-700 bg-danger-50 border-danger-100' },
  SOUMISSION: { Icon: FileText, color: 'text-primary-500 bg-primary-50 border-primary-100' },
  INCOMPLET: { Icon: AlertTriangle, color: 'text-warning-500 bg-warning-50 border-warning-100' },
  COMPLEMENT: { Icon: Paperclip, color: 'text-warning-600 bg-warning-50 border-warning-100' },
};

const formatRelativeTime = (dateStr) => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now - date;
  if (diffMs < 0) return "À l'instant";
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return "À l'instant";
  if (diffMins < 60) return `Il y a ${diffMins} min`;
  if (diffHours < 24) return `Il y a ${diffHours} h`;
  if (diffDays === 1) return "Hier";
  return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
};

export default function ClochNotifications() {
  const [count, setCount] = useState(0);
  const [notifications, setNotifications] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);
  const navigate = useNavigate();

  const fetchUnreadCount = useCallback(() => {
    getNonLuesCount()
      .then(({ count }) => setCount(count))
      .catch((err) => { /* console.error('[WS] Erreur chargement badge:', err) */ });
  }, []);

  const loadNotifications = useCallback(() => {
    getMesNotifications()
      .then((data) => {
        // DRF generics.ListAPIView might return pagination wrapper or direct array.
        // Usually, Django Rest Framework PageNumberPagination returns { results: [...] } or direct list if not paginated.
        const list = Array.isArray(data) ? data : data?.results || [];
        setNotifications(list.slice(0, 10));
      })
      .catch((err) => { /* console.error('[WS] Erreur chargement list notif:', err) */ });
  }, []);

  // Sync au montage + Polling toutes les 60 secondes
  useEffect(() => {
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 60000);
    return () => clearInterval(interval);
  }, [fetchUnreadCount]);

  // Charger la liste quand le dropdown s'ouvre
  useEffect(() => {
    if (isOpen) {
      loadNotifications();
      fetchUnreadCount();
    }
  }, [isOpen, loadNotifications, fetchUnreadCount]);

  // Gérer le clic extérieur pour fermer le dropdown
  useEffect(() => {
    const handleOutsideClick = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleOutsideClick);
    return () => document.removeEventListener('mousedown', handleOutsideClick);
  }, []);

  const handleToggle = () => setIsOpen((prev) => !prev);

  const handleMarkAllRead = async (e) => {
    e.stopPropagation();
    try {
      await marquerToutesLues();
      setCount(0);
      setNotifications((prev) => prev.map((n) => ({ ...n, lue: true })));
    } catch (err) {
      // console.error(err);
    }
  };

  const handleItemClick = async (item) => {
    setIsOpen(false);
    
    // Marquer comme lu si ce n'est pas déjà le cas
    if (!item.lue) {
      try {
        await marquerLue(item.id);
        fetchUnreadCount();
      } catch (err) {
        // console.error(err);
      }
    }

    // Si la notification concerne un dossier, on redirige
    const dossierTypes = ['SOUMISSION', 'REJET_AUTO', 'REJET_MANUEL', 'PRESELECTION', 'INCOMPLET', 'COMPLEMENT'];
    if (dossierTypes.includes(item.type_notif)) {
      try {
        const dossiers = await getDossiers();
        if (dossiers && dossiers.length > 0) {
          // Utilise le dossier le plus récent
          navigate(`/dossier/${dossiers[0].id}`);
        }
      } catch (err) {
        // console.error('Erreur redirection dossier:', err);
      }
    } else {
      navigate('/candidat/notifications');
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bouton cloche */}
      <button
        onClick={handleToggle}
        className="p-2 rounded-full hover:bg-gray-100 text-text-muted transition-colors relative flex items-center justify-center"
        aria-label="Notifications"
      >
        <Bell size={20} className={count > 0 ? 'text-primary-600 animate-swing' : ''} />
        {count > 0 && (
          <span className="absolute top-1 right-1 w-5 h-5 rounded-full bg-danger-500 text-white text-[10px] font-bold flex items-center justify-center border border-white">
            {count > 9 ? '9+' : count}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-white rounded-xl shadow-xl border border-border overflow-hidden z-50 animate-scale-up">
          {/* Header */}
          <div className="px-4 py-3 bg-gray-50 border-b border-border flex items-center justify-between">
            <span className="text-sm font-bold text-text-primary">Mes notifications</span>
            {count > 0 && (
              <button
                onClick={handleMarkAllRead}
                className="text-xs font-semibold text-primary-600 hover:text-primary-700 flex items-center gap-1 transition-colors"
              >
                <Check size={14} /> Tout marquer lu
              </button>
            )}
          </div>

          {/* Liste */}
          <div className="max-h-96 overflow-y-auto divide-y divide-border">
            {notifications.length === 0 ? (
              <div className="p-8 text-center text-text-muted">
                <Bell size={24} className="mx-auto mb-2 text-gray-300" />
                <p className="text-xs">Aucune notification pour le moment</p>
              </div>
            ) : (
              notifications.map((item) => {
                const config = TYPE_ICONS[item.type_notif] || { Icon: Bell, color: 'text-gray-500 bg-gray-50' };
                const { Icon, color } = config;
                return (
                  <div
                    key={item.id}
                    onClick={() => handleItemClick(item)}
                    className={`p-4 flex gap-3 hover:bg-gray-50 cursor-pointer transition-all duration-150 ${
                      !item.lue ? 'bg-primary-50/20' : ''
                    }`}
                  >
                    {/* Icône du type */}
                    <div className={`w-8 h-8 rounded-lg border flex items-center justify-center flex-shrink-0 ${color}`}>
                      <Icon size={16} />
                    </div>

                    {/* Contenu */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <p className={`text-xs text-text-primary leading-snug truncate-2-lines ${!item.lue ? 'font-bold text-gray-900' : 'text-gray-600'}`}>
                          {item.sujet}
                        </p>
                        {!item.lue && (
                          <span className="w-2 h-2 rounded-full bg-primary-600 mt-1 flex-shrink-0" />
                        )}
                      </div>
                      <p className="text-[10px] text-text-muted mt-1">
                        {formatRelativeTime(item.envoyee_le)}
                      </p>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Footer */}
          <Link
            to="/candidat/notifications"
            onClick={() => setIsOpen(false)}
            className="block text-center py-2.5 bg-gray-50 text-xs font-semibold text-primary-600 hover:bg-gray-100 hover:text-primary-700 transition-colors border-t border-border no-underline"
          >
            Voir toutes les notifications →
          </Link>
        </div>
      )}
    </div>
  );
}
