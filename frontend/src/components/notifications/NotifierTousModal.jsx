// src/components/notifications/NotifierTousModal.jsx
// Modal de notification en masse avec 4 phases : CHARGEMENT → CONFIRMATION → ENVOI → RESULTAT

import { useState, useEffect, useRef } from 'react';
import {
  X, Bell, CheckCircle, XCircle, MinusCircle,
  AlertTriangle, Loader2, Send, Download, RefreshCw, Mail,
} from 'lucide-react';
import API from '../../api/axios';
import { useNotificationWebSocket } from '../../hooks/useNotificationWebSocket';

const PHASES = {
  CHARGEMENT: 'CHARGEMENT',
  CONFIRMATION: 'CONFIRMATION',
  ENVOI: 'ENVOI',
  RESULTAT: 'RESULTAT',
};

export default function NotifierTousModal({
  isOpen,
  onClose,
  onSuccess,
  filiereId = null,
  filiereNom = '',
}) {
  const [phase, setPhase] = useState(PHASES.CHARGEMENT);
  const [stats, setStats] = useState(null);
  const [apercuEmail, setApercuEmail] = useState(null);
  const [taskId, setTaskId] = useState(null);
  const [erreur, setErreur] = useState(null);
  const [showEchecs, setShowEchecs] = useState(false);
  const listRef = useRef(null);

  // Hook WebSocket
  const ws = useNotificationWebSocket(taskId);

  // Auto-scroll de la liste de progression
  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [ws.progression.length]);

  // Transition vers RESULTAT quand l'envoi est terminé
  useEffect(() => {
    if (ws.termine && ws.resultat) {
      setPhase(PHASES.RESULTAT);
    }
  }, [ws.termine, ws.resultat]);

  // Charger les stats à l'ouverture
  useEffect(() => {
    if (!isOpen) return;
    setPhase(PHASES.CHARGEMENT);
    setTaskId(null);
    setErreur(null);
    setShowEchecs(false);

    const params = filiereId ? `?filiere_id=${filiereId}` : '';
    API.get(`/notifications/previsualiser/${params}`)
      .then(({ data }) => {
        setStats(data.stats);
        setApercuEmail(data.apercu_email);
        setPhase(PHASES.CONFIRMATION);
      })
      .catch((err) => {
        setErreur(err.response?.data?.detail || 'Erreur lors du chargement des données.');
        setPhase(PHASES.CONFIRMATION);
      });
  }, [isOpen, filiereId]);

  // Lancer l'envoi
  const lancerEnvoi = async () => {
    try {
      setErreur(null);
      const payload = filiereId ? { filiere_id: filiereId } : {};
      const { data } = await API.post('/notifications/notifier-tous/', payload);
      setTaskId(data.task_id);
      setPhase(PHASES.ENVOI);
    } catch (err) {
      setErreur(err.response?.data?.detail || "Erreur lors du lancement de l'envoi.");
    }
  };

  // Export CSV des résultats
  const exporterCSV = () => {
    const items = ws.progression || [];
    const header = 'Candidat,Email,Statut,Erreur\n';
    const rows = items.map((item) =>
      `"${item.candidat}","${item.email}","${item.statut}","${item.erreur || ''}"`
    ).join('\n');
    const blob = new Blob([header + rows], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `rapport_notifications_${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  if (!isOpen) return null;

  // Compteurs live
  const envoyesCount = ws.progression.filter((p) => p.statut === 'ENVOYE').length;
  const echecsCount = ws.progression.filter((p) => p.statut === 'ECHEC').length;
  const ignoresCount = ws.progression.filter((p) => p.statut === 'IGNORE').length;

  const canClose = phase !== PHASES.ENVOI;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-[3px]"
        onClick={canClose ? onClose : undefined}
      />

      {/* Modal */}
      <div
        className="card relative z-10 w-full animate-scale-in"
        style={{ maxWidth: '640px', maxHeight: '85vh', display: 'flex', flexDirection: 'column' }}
      >
        {/* ── Header ─────────────────────────────────────────── */}
        <div className="flex items-center justify-between p-5 border-b border-border">
          <div className="flex items-center gap-3">
            <div
              className="w-10 h-10 rounded-lg flex items-center justify-center"
              style={{ background: '#EBF5FB' }}
            >
              <Bell size={20} style={{ color: '#1B3A6B' }} />
            </div>
            <div>
              <h3 className="text-base font-bold text-text-primary">
                {phase === PHASES.ENVOI
                  ? `Envoi en cours... ${ws.current} / ${ws.total}`
                  : phase === PHASES.RESULTAT
                  ? 'Envoi terminé'
                  : 'Notifier les présélectionnés'}
              </h3>
              {filiereNom && (
                <p className="text-xs text-text-muted mt-0.5">
                  Filière : <span className="font-semibold">{filiereNom}</span>
                </p>
              )}
            </div>
          </div>
          {canClose && (
            <button
              onClick={onClose}
              className="p-1.5 rounded-md hover:bg-gray-100 text-text-muted transition-colors"
              aria-label="Fermer"
            >
              <X size={18} />
            </button>
          )}
        </div>

        {/* ── Body ────────────────────────────────────────────── */}
        <div className="p-5 overflow-y-auto flex-1">

          {/* PHASE 1 : CHARGEMENT */}
          {phase === PHASES.CHARGEMENT && (
            <div className="flex flex-col items-center justify-center py-12 gap-3">
              <Loader2 size={36} className="animate-spin" style={{ color: '#1B3A6B' }} />
              <p className="text-sm text-text-secondary">Calcul des destinataires...</p>
            </div>
          )}

          {/* PHASE 2 : CONFIRMATION */}
          {phase === PHASES.CONFIRMATION && (
            <div className="space-y-5">
              {erreur && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
                  {erreur}
                </div>
              )}

              {stats && (
                <div className="grid grid-cols-3 gap-3">
                  <div className="bg-blue-50 rounded-lg p-4 text-center">
                    <p className="text-2xl font-bold font-mono" style={{ color: '#1B3A6B' }}>
                      {stats.a_notifier}
                    </p>
                    <p className="text-xs text-text-muted mt-1">À notifier</p>
                  </div>
                  <div className="bg-green-50 rounded-lg p-4 text-center">
                    <p className="text-2xl font-bold font-mono text-green-600">
                      {stats.deja_notifies}
                    </p>
                    <p className="text-xs text-text-muted mt-1">Déjà notifiés (24h)</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4 text-center">
                    <p className="text-2xl font-bold font-mono text-gray-600">
                      {stats.total}
                    </p>
                    <p className="text-xs text-text-muted mt-1">Total présélectionnés</p>
                  </div>
                </div>
              )}

              {/* Aperçu email */}
              {apercuEmail && (
                <div>
                  <p className="text-sm font-semibold text-text-secondary mb-2 flex items-center gap-1.5">
                    <Mail size={14} /> Aperçu de l'email
                  </p>
                  <div className="border border-border rounded-lg overflow-hidden">
                    <div
                      className="bg-gray-50 px-3 py-2 text-xs font-medium text-text-secondary border-b border-border"
                    >
                      Sujet : {apercuEmail.sujet}
                    </div>
                    <div
                      className="p-3 text-xs max-h-40 overflow-y-auto"
                      style={{ fontSize: '11px' }}
                      dangerouslySetInnerHTML={{ __html: apercuEmail.apercu_html }}
                    />
                  </div>
                </div>
              )}

              {stats?.a_notifier === 0 && (
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-700 flex items-center gap-2">
                  <AlertTriangle size={16} />
                  Tous les présélectionnés ont déjà été notifiés dans les 24 dernières heures.
                </div>
              )}
            </div>
          )}

          {/* PHASE 3 : ENVOI EN COURS */}
          {phase === PHASES.ENVOI && (
            <div className="space-y-5">
              <p className="text-xs text-text-muted text-center font-medium" style={{ color: '#C0392B' }}>
                ⚠ Ne pas fermer cette fenêtre pendant l'envoi
              </p>

              {/* Barre de progression */}
              <div className="flex items-center gap-3">
                <div className="flex-1 h-4 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-300"
                    style={{
                      width: `${ws.pourcentage}%`,
                      background: ws.pourcentage >= 100
                        ? 'linear-gradient(90deg, #27AE60, #2ECC71)'
                        : 'linear-gradient(90deg, #1B3A6B, #2E86C1)',
                    }}
                  />
                </div>
                <span className="text-sm font-bold font-mono min-w-[3.5rem] text-right" style={{ color: '#1B3A6B' }}>
                  {ws.pourcentage}%
                </span>
              </div>

              {/* Compteurs temps réel */}
              <div className="grid grid-cols-3 gap-3">
                <div className="flex items-center gap-2 bg-green-50 rounded-lg px-3 py-2.5">
                  <CheckCircle size={16} className="text-green-600 shrink-0" />
                  <div>
                    <p className="text-lg font-bold font-mono text-green-700">{envoyesCount}</p>
                    <p className="text-[10px] text-green-600">Envoyés</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 bg-red-50 rounded-lg px-3 py-2.5">
                  <XCircle size={16} className="text-red-600 shrink-0" />
                  <div>
                    <p className="text-lg font-bold font-mono text-red-700">{echecsCount}</p>
                    <p className="text-[10px] text-red-600">Échecs</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 bg-gray-50 rounded-lg px-3 py-2.5">
                  <MinusCircle size={16} className="text-gray-500 shrink-0" />
                  <div>
                    <p className="text-lg font-bold font-mono text-gray-700">{ignoresCount}</p>
                    <p className="text-[10px] text-gray-500">Ignorés</p>
                  </div>
                </div>
              </div>

              {/* Erreur WebSocket */}
              {ws.erreurWs && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-center justify-between">
                  <p className="text-sm text-red-700">
                    Connexion perdue — les envois continuent en arrière-plan.
                  </p>
                  <button
                    onClick={ws.reconnecter}
                    className="btn btn-sm text-red-700 border-red-300 hover:bg-red-100 flex items-center gap-1.5"
                  >
                    <RefreshCw size={14} /> Reconnecter
                  </button>
                </div>
              )}

              {/* Liste de progression (scroll) */}
              <div
                ref={listRef}
                className="border border-border rounded-lg overflow-y-auto"
                style={{ maxHeight: '250px' }}
              >
                {ws.progression.length === 0 ? (
                  <div className="py-6 text-center text-sm text-text-muted">
                    En attente des premiers résultats...
                  </div>
                ) : (
                  <div className="divide-y divide-border">
                    {ws.progression.map((item, idx) => (
                      <div
                        key={idx}
                        className="flex items-center gap-3 px-3 py-2 text-sm hover:bg-gray-50/50"
                      >
                        {/* Icône statut */}
                        {item.statut === 'ENVOYE' && (
                          <CheckCircle size={14} className="text-green-500 shrink-0" />
                        )}
                        {item.statut === 'ECHEC' && (
                          <XCircle size={14} className="text-red-500 shrink-0" />
                        )}
                        {item.statut === 'IGNORE' && (
                          <MinusCircle size={14} className="text-gray-400 shrink-0" />
                        )}

                        {/* Nom + email */}
                        <div className="flex-1 min-w-0">
                          <span className="font-medium text-text-primary truncate block text-xs">
                            {item.candidat}
                          </span>
                          <span className="text-[10px] text-text-muted truncate block">
                            {item.email}
                          </span>
                        </div>

                        {/* Badge statut */}
                        <span
                          className="text-[10px] font-bold px-2 py-0.5 rounded-full shrink-0"
                          style={{
                            background:
                              item.statut === 'ENVOYE'
                                ? '#EAFAF1'
                                : item.statut === 'ECHEC'
                                ? '#FDEDEC'
                                : '#F4F6F7',
                            color:
                              item.statut === 'ENVOYE'
                                ? '#27AE60'
                                : item.statut === 'ECHEC'
                                ? '#C0392B'
                                : '#95A5A6',
                          }}
                        >
                          {item.statut}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* PHASE 4 : RESULTAT */}
          {phase === PHASES.RESULTAT && ws.resultat && (
            <div className="space-y-5">
              {/* Icône + message principal */}
              <div className="flex flex-col items-center py-4">
                {ws.resultat.echecs === 0 ? (
                  <>
                    <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mb-3 animate-scale-in">
                      <CheckCircle size={32} className="text-green-600" />
                    </div>
                    <h4 className="text-lg font-bold text-green-700">
                      Toutes les notifications ont été envoyées !
                    </h4>
                    <p className="text-sm text-text-muted mt-1">
                      {ws.resultat.envoyes} email{ws.resultat.envoyes > 1 ? 's' : ''} envoyé{ws.resultat.envoyes > 1 ? 's' : ''} avec succès
                    </p>
                  </>
                ) : ws.resultat.envoyes > 0 ? (
                  <>
                    <div className="w-16 h-16 rounded-full bg-amber-100 flex items-center justify-center mb-3 animate-scale-in">
                      <AlertTriangle size={32} className="text-amber-600" />
                    </div>
                    <h4 className="text-lg font-bold text-amber-700">
                      Envoi terminé avec des erreurs
                    </h4>
                    <p className="text-sm text-text-muted mt-1">
                      {ws.resultat.envoyes} envoyé{ws.resultat.envoyes > 1 ? 's' : ''}, {ws.resultat.echecs} échec{ws.resultat.echecs > 1 ? 's' : ''}
                    </p>
                  </>
                ) : (
                  <>
                    <div className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center mb-3 animate-scale-in">
                      <XCircle size={32} className="text-red-600" />
                    </div>
                    <h4 className="text-lg font-bold text-red-700">
                      Erreur lors de l'envoi
                    </h4>
                    <p className="text-sm text-text-muted mt-1">
                      Aucun email n'a pu être envoyé. Vérifiez la configuration SMTP.
                    </p>
                  </>
                )}
              </div>

              {/* Résumé chiffré */}
              <div className="grid grid-cols-4 gap-2">
                {[
                  { label: 'Total', value: ws.resultat.total, color: '#1B3A6B', bg: '#EBF5FB' },
                  { label: 'Envoyés', value: ws.resultat.envoyes, color: '#27AE60', bg: '#EAFAF1' },
                  { label: 'Échecs', value: ws.resultat.echecs, color: '#C0392B', bg: '#FDEDEC' },
                  { label: 'Ignorés', value: ws.resultat.ignores, color: '#95A5A6', bg: '#F4F6F7' },
                ].map((s) => (
                  <div key={s.label} className="rounded-lg p-3 text-center" style={{ background: s.bg }}>
                    <p className="text-xl font-bold font-mono" style={{ color: s.color }}>{s.value}</p>
                    <p className="text-[10px] font-medium" style={{ color: s.color }}>{s.label}</p>
                  </div>
                ))}
              </div>

              {/* Détails des échecs (dépliable) */}
              {ws.resultat.echecs > 0 && (
                <div>
                  <button
                    onClick={() => setShowEchecs(!showEchecs)}
                    className="text-sm font-medium text-red-600 hover:text-red-700 flex items-center gap-1"
                  >
                    {showEchecs ? '▾' : '▸'} Voir les {ws.resultat.echecs} échec{ws.resultat.echecs > 1 ? 's' : ''}
                  </button>
                  {showEchecs && (
                    <div className="mt-2 border border-red-200 rounded-lg overflow-hidden">
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="bg-red-50">
                            <th className="text-left px-3 py-2 font-semibold text-red-700">Candidat</th>
                            <th className="text-left px-3 py-2 font-semibold text-red-700">Email</th>
                            <th className="text-left px-3 py-2 font-semibold text-red-700">Erreur</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(ws.resultat.details_echecs || []).map((e, idx) => (
                            <tr key={idx} className="border-t border-red-100">
                              <td className="px-3 py-2">{e.candidat}</td>
                              <td className="px-3 py-2 text-text-muted">{e.email}</td>
                              <td className="px-3 py-2 text-red-600">{e.erreur}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* ── Footer ───────────────────────────────────────────── */}
        <div className="flex items-center justify-end gap-3 p-5 border-t border-border">
          {phase === PHASES.CONFIRMATION && (
            <>
              <button className="btn btn-outline btn-sm" onClick={onClose}>
                Annuler
              </button>
              <button
                className="btn btn-sm"
                style={{ background: '#1B3A6B', color: '#fff' }}
                onClick={lancerEnvoi}
                disabled={!stats || stats.a_notifier === 0}
              >
                <Send size={14} /> Confirmer l'envoi
              </button>
            </>
          )}

          {phase === PHASES.ENVOI && (
            <p className="text-xs text-text-muted flex-1 text-center">
              <Loader2 size={14} className="inline animate-spin mr-1" />
              Traitement en cours...
            </p>
          )}

          {phase === PHASES.RESULTAT && (
            <>
              <button
                className="btn btn-outline btn-sm flex items-center gap-1.5"
                onClick={exporterCSV}
              >
                <Download size={14} /> Exporter le rapport
              </button>
              <button
                className="btn btn-sm"
                style={{ background: '#1B3A6B', color: '#fff' }}
                onClick={() => {
                  if (onSuccess) onSuccess();
                  onClose();
                }}
              >
                Fermer
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
