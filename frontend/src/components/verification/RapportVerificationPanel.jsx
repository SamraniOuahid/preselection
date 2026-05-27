// src/components/verification/RapportVerificationPanel.jsx
// Panneau complet qui orchestre tous les composants de vérification
import { useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import { ShieldCheck, ShieldAlert, RefreshCw } from 'lucide-react';
import { getRapportVerification } from '../../api/dossiers';
import ScoreAuthenticite from './ScoreAuthenticite';
import AlertesVerification from './AlertesVerification';
import DocumentsVerification from './DocumentsVerification';
import MassarVerification from './MassarVerification';

export default function RapportVerificationPanel({ dossierId, dossier, onUpdate }) {
  const [rapport, setRapport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchRapport = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getRapportVerification(dossierId);
      setRapport(data);
    } catch (err) {
      setError("Impossible de charger le rapport de vérification automatique.");
    } finally {
      setLoading(false);
    }
  }, [dossierId]);

  useEffect(() => {
    fetchRapport();
  }, [fetchRapport]);

  // Déterminer le niveau et la recommandation d'authentification
  const getAuthenticiteNiveau = (score) => {
    if (score >= 0.80) return 'ELEVE';
    if (score >= 0.60) return 'MOYEN';
    if (score >= 0.40) return 'FAIBLE';
    return 'CRITIQUE';
  };

  const getRecommandation = (score, isSuspect) => {
    if (score < 0.40) return 'REJETER';
    if (score >= 0.80) return 'VALIDER';
    return 'VERIF_MANUELLE';
  };

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        {/* Header Skeleton */}
        <div className="h-16 bg-gray-200 rounded-xl w-full" />
        
        {/* Core metrics row Skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-10 gap-6">
          <div className="md:col-span-3 h-64 bg-gray-200 rounded-xl" />
          <div className="md:col-span-7 h-64 bg-gray-200 rounded-xl" />
        </div>

        {/* Documents table Skeleton */}
        <div className="h-48 bg-gray-200 rounded-xl w-full" />

        {/* Massar Card Skeleton */}
        <div className="h-28 bg-gray-200 rounded-xl w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="card p-8 text-center flex flex-col items-center justify-center gap-4 border border-red-100 bg-red-50/20">
        <ShieldAlert className="text-red-500" size={48} />
        <div>
          <p className="text-sm font-semibold text-red-800">{error}</p>
          <p className="text-xs text-red-500 mt-1">Veuillez vérifier votre connexion ou réactualiser la page.</p>
        </div>
        <button
          onClick={fetchRapport}
          className="btn btn-outline-danger btn-sm flex items-center gap-2 mt-2"
        >
          <RefreshCw size={14} /> Réessayer
        </button>
      </div>
    );
  }

  if (!rapport) return null;

  const scoreAuth = rapport.score_authenticite ?? 0;
  const niveau = getAuthenticiteNiveau(scoreAuth);
  // Si le dossier est suspect (is_suspect ou score bas), on recommande la vérification manuelle ou rejet
  const recommandation = getRecommandation(scoreAuth, dossier.is_suspect);

  // Date actuelle formatée ou date du rapport si disponible
  const dateAnalyse = new Date().toLocaleDateString('fr-FR', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });

  return (
    <div className="space-y-6">
      {/* ── HEADER PANEL ──────────────────────────────────────── */}
      <div className="ensa-card p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-gradient-to-r from-slate-50 to-blue-50/20 border-l-4 border-l-[#1B3A6B]">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-[#EBF5FB] flex items-center justify-center text-[#1B3A6B]">
            <ShieldCheck size={22} />
          </div>
          <div>
            <h3 className="text-sm font-bold text-[#1B3A6B]">
              Rapport de Vérification Automatique
            </h3>
            <p className="text-[11px] text-text-muted mt-0.5">
              Analyse effectuée le {dateAnalyse}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs font-semibold px-2.5 py-1 rounded bg-[#EBF5FB] text-[#2E86C1] self-start sm:self-center">
          <span className="w-2 h-2 rounded-full bg-[#2E86C1]" />
          Statut : {rapport.massar_verifie ? 'Vérifié Massar' : 'Massar en attente'}
        </div>
      </div>

      {/* ── ROW: SCORE & ALERTS ────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-10 gap-6">
        {/* Score d'authenticité (30%) */}
        <div className="ensa-card p-5 md:col-span-3 flex items-center justify-center bg-white">
          <ScoreAuthenticite
            score={scoreAuth}
            niveau={niveau}
            recommandation={recommandation}
          />
        </div>

        {/* Liste des alertes détectées (70%) */}
        <div className="ensa-card p-5 md:col-span-7 bg-white">
          <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wide mb-4">
            Alertes système & anomalies
          </h4>
          <AlertesVerification
            alertes={rapport.alertes}
            niveau={niveau}
          />
        </div>
      </div>

      {/* ── SECTION: DOCUMENTS VERIFICATION ────────────────────── */}
      <div className="ensa-card p-5 bg-white">
        <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wide mb-4">
          Statut de conformité des pièces justificatives
        </h4>
        <DocumentsVerification
          documents={rapport.par_document || []}
        />
      </div>

      {/* ── SECTION: MASSAR MANUAL VERIFICATION ───────────────── */}
      <MassarVerification
        dossierId={dossierId}
        massarVerifie={rapport.massar_verifie ?? dossier.massar_verifie ?? false}
        cne={dossier.candidat?.cne || dossier.cne}
        codeMassar={dossier.candidat?.code_massar || dossier.code_massar}
        onVerifie={() => {
          // Rafraîchir localement le rapport et notifier le parent
          fetchRapport();
          if (onUpdate) {
            onUpdate();
          }
        }}
      />
    </div>
  );
}

RapportVerificationPanel.propTypes = {
  dossierId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  dossier: PropTypes.object.isRequired,
  onUpdate: PropTypes.func.isRequired,
};
