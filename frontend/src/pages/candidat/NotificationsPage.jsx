// src/pages/candidat/NotificationsPage.jsx
import { useState, useEffect, useCallback } from 'react';
import {
  Bell, BellOff, CheckCircle, XCircle, FileText, AlertTriangle, Paperclip, Eye, X, Check, Trophy
} from 'lucide-react';
import { getMesNotifications, marquerLue, marquerToutesLues } from '../../api/notifications';
import LoadingSpinner from '../../components/common/LoadingSpinner';

const FILTER_TYPES = [
  { id: 'ALL', label: 'Tous' },
  { id: 'UNREAD', label: 'Non lus' },
  { id: 'PRESELECTION', label: 'Présélection' },
  { id: 'ADMIS', label: 'Admis' },
  { id: 'REJECT', label: 'Rejets' },
  { id: 'OTHERS', label: 'Autres' },
];

const TYPE_CONFIG = {
  PRESELECTION: {
    Icon: CheckCircle,
    color: 'text-success-600 bg-success-50 border-success-100',
    borderLeft: 'border-l-4 border-l-success-500',
    label: 'Présélection',
  },
  ADMIS_FINAL: {
    Icon: Trophy,
    color: 'text-emerald-600 bg-emerald-50 border-emerald-100',
    borderLeft: 'border-l-4 border-l-emerald-500',
    label: 'Admis — Oral',
  },
  RECALE_FINAL: {
    Icon: XCircle,
    color: 'text-red-600 bg-red-50 border-red-100',
    borderLeft: 'border-l-4 border-l-red-500',
    label: 'Recalé — Écrit',
  },
  ABSENT_ECRIT: {
    Icon: AlertTriangle,
    color: 'text-orange-600 bg-orange-50 border-orange-100',
    borderLeft: 'border-l-4 border-l-orange-500',
    label: 'Absent écrit',
  },
  REJET_AUTO: {
    Icon: XCircle,
    color: 'text-danger-600 bg-danger-50 border-danger-100',
    borderLeft: 'border-l-4 border-l-danger-500',
    label: 'Dossier non retenu',
  },
  REJET_MANUEL: {
    Icon: XCircle,
    color: 'text-danger-700 bg-danger-50 border-danger-100',
    borderLeft: 'border-l-4 border-l-danger-700',
    label: 'Rejet',
  },
  SOUMISSION: {
    Icon: FileText,
    color: 'text-primary-600 bg-primary-50 border-primary-100',
    borderLeft: 'border-l-4 border-l-primary-500',
    label: 'Soumission',
  },
  INCOMPLET: {
    Icon: AlertTriangle,
    color: 'text-warning-600 bg-warning-50 border-warning-100',
    borderLeft: 'border-l-4 border-l-warning-500',
    label: 'Dossier incomplet',
  },
  COMPLEMENT: {
    Icon: Paperclip,
    color: 'text-warning-700 bg-warning-50 border-warning-100',
    borderLeft: 'border-l-4 border-l-warning-600',
    label: 'Complément requis',
  },
};

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState([]);
  const [filteredNotifs, setFilteredNotifs] = useState([]);
  const [activeFilter, setActiveFilter] = useState('ALL');
  const [loading, setLoading] = useState(true);
  const [selectedNotif, setSelectedNotif] = useState(null);

  const loadNotifications = useCallback(async () => {
    try {
      const data = await getMesNotifications();
      const list = Array.isArray(data) ? data : data?.results || [];
      setNotifications(list);
    } catch (err) {
      // console.error('Erreur chargement notifications:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadNotifications();
  }, [loadNotifications]);

  // Appliquer les filtres
  useEffect(() => {
    let result = [...notifications];

    if (activeFilter === 'UNREAD') {
      result = result.filter((n) => !n.lue);
    } else if (activeFilter === 'PRESELECTION') {
      result = result.filter((n) => n.type_notif === 'PRESELECTION');
    } else if (activeFilter === 'ADMIS') {
      result = result.filter((n) => ['ADMIS_FINAL', 'RECALE_FINAL', 'ABSENT_ECRIT'].includes(n.type_notif));
    } else if (activeFilter === 'REJECT') {
      result = result.filter((n) => ['REJET_AUTO', 'REJET_MANUEL'].includes(n.type_notif));
    } else if (activeFilter === 'OTHERS') {
      result = result.filter(
        (n) => !['PRESELECTION', 'REJET_AUTO', 'REJET_MANUEL', 'ADMIS_FINAL', 'RECALE_FINAL', 'ABSENT_ECRIT'].includes(n.type_notif)
      );
    }

    setFilteredNotifs(result);
  }, [notifications, activeFilter]);

  const handleMarkAsRead = async (id) => {
    try {
      await marquerLue(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, lue: true, lue_le: new Date().toISOString() } : n))
      );
    } catch (err) {
      // console.error(err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await marquerToutesLues();
      setNotifications((prev) => prev.map((n) => ({ ...n, lue: true })));
    } catch (err) {
      // console.error(err);
    }
  };

  const handleViewDetail = async (notif) => {
    setSelectedNotif(notif);
    if (!notif.lue) {
      await handleMarkAsRead(notif.id);
    }
  };

  if (loading) {
    return <LoadingSpinner size="lg" text="Chargement de vos notifications..." className="py-20" />;
  }

  const unreadCount = notifications.filter((n) => !n.lue).length;

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <div className="ensa-page-header">
        <div className="ensa-page-header-row">
          <div>
            <h1 className="ensa-page-title flex items-center gap-2">
              <Bell size={24} className="text-primary-600" />
              Mes notifications
            </h1>
            <p className="ensa-page-subtitle">
              Retrouvez ici toutes les communications officielles concernant vos candidatures
            </p>
          </div>
          {unreadCount > 0 && (
            <button
              onClick={handleMarkAllRead}
              className="btn btn-outline btn-sm text-primary-700 border-primary-200 hover:bg-primary-50"
            >
              <Check size={16} /> Tout marquer comme lu
            </button>
          )}
        </div>
      </div>

      {/* Barre de filtres */}
      <div className="flex gap-2 border-b border-border pb-2 overflow-x-auto">
        {FILTER_TYPES.map((filter) => {
          const isActive = activeFilter === filter.id;
          return (
            <button
              key={filter.id}
              onClick={() => setActiveFilter(filter.id)}
              className={`
                px-4 py-2 rounded-lg text-xs font-semibold whitespace-nowrap transition-all duration-150
                ${isActive
                  ? 'bg-primary-600 text-white shadow-sm'
                  : 'bg-white text-text-muted hover:bg-gray-100 hover:text-text-primary border border-border'
                }
              `}
            >
              {filter.label}
              {filter.id === 'UNREAD' && unreadCount > 0 && (
                <span className={`ml-1.5 px-1.5 py-0.5 rounded-full text-[9px] font-bold ${
                  isActive ? 'bg-white text-primary-600' : 'bg-danger-500 text-white'
                }`}>
                  {unreadCount}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Liste des notifications */}
      {filteredNotifs.length === 0 ? (
        <div className="ensa-card p-12 text-center">
          <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4 text-text-muted">
            <BellOff size={24} />
          </div>
          <h3 className="text-sm font-semibold text-text-primary">Aucune notification</h3>
          <p className="text-xs text-text-muted mt-1">
            Vous n'avez pas de notification correspondant à ce critère.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredNotifs.map((item) => {
            const config = TYPE_CONFIG[item.type_notif] || {
              Icon: Bell,
              color: 'text-gray-500 bg-gray-50 border-gray-100',
              borderLeft: 'border-l-4 border-l-gray-300',
              label: 'Notification',
            };
            const { Icon, color, borderLeft, label } = config;

            return (
              <div
                key={item.id}
                className={`
                  ensa-card overflow-hidden hover:shadow-md transition-all duration-200 ${borderLeft} ${
                    !item.lue ? 'bg-primary-50/10' : 'bg-white'
                  }
                `}
              >
                <div className="p-4 sm:p-5 flex flex-col sm:flex-row gap-4 items-start justify-between">
                  <div className="flex gap-4 flex-1 min-w-0">
                    {/* Icône */}
                    <div className={`w-10 h-10 rounded-xl border flex items-center justify-center flex-shrink-0 ${color}`}>
                      <Icon size={20} />
                    </div>

                    {/* Texte */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted bg-gray-100 px-2 py-0.5 rounded">
                          {label}
                        </span>
                        {!item.lue && (
                          <span className="badge badge-error py-0.5 px-1.5 text-[9px]">Non lue</span>
                        )}
                        <span className="text-[10px] text-text-muted">
                          {new Date(item.envoyee_le).toLocaleString('fr-FR')}
                        </span>
                      </div>
                      <h3 className={`text-sm leading-snug truncate-2-lines mb-1 ${
                        !item.lue ? 'font-bold text-gray-900' : 'font-medium text-text-primary'
                      }`}>
                        {item.sujet}
                      </h3>
                      {/* Extrait de contenu (2 lignes max) */}
                      <p className="text-xs text-text-muted truncate-2-lines leading-relaxed">
                        {item.sujet} — Cliquez sur "Voir le détail" pour lire le message complet.
                      </p>
                      {item.erreur && (
                        <p className="text-[10px] text-danger-500 font-mono mt-1 bg-danger-50 px-2 py-1 rounded border border-danger-100 truncate">
                          Erreur SMTP : {item.erreur}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2 self-stretch sm:self-center justify-end items-center">
                    <button
                      onClick={() => handleViewDetail(item)}
                      className="btn btn-ghost btn-sm text-primary-600 hover:bg-primary-50 flex items-center gap-1"
                      title="Voir le détail"
                    >
                      <Eye size={16} /> Voir le détail
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Modal Détail */}
      {selectedNotif && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 backdrop-blur-sm animate-fade-in">
          <div className="bg-white rounded-xl shadow-2xl border border-border w-full max-w-2xl overflow-hidden max-h-[85vh] flex flex-col animate-scale-up">
            {/* Header Modal */}
            <div className="px-6 py-4 bg-gray-50 border-b border-border flex items-center justify-between">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted bg-gray-100 px-2 py-0.5 rounded">
                  {TYPE_CONFIG[selectedNotif.type_notif]?.label || 'Notification'}
                </span>
                <h2 className="text-sm font-bold text-text-primary mt-1">{selectedNotif.sujet}</h2>
              </div>
              <button
                onClick={() => setSelectedNotif(null)}
                className="p-1 rounded hover:bg-gray-200 text-text-muted hover:text-text-primary transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            {/* Contenu Modal */}
            <div className="flex-1 overflow-y-auto p-6 bg-gray-50/50">
              <div
                className="bg-white p-6 rounded-lg border border-border shadow-sm prose max-w-none"
                dangerouslySetInnerHTML={{ __html: selectedNotif.contenu_html }}
              />
            </div>

            {/* Footer Modal */}
            <div className="px-6 py-3 bg-gray-50 border-t border-border flex justify-end">
              <button
                onClick={() => setSelectedNotif(null)}
                className="btn btn-primary btn-sm"
              >
                Fermer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
