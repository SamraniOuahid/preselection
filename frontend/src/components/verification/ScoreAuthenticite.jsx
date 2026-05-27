// src/components/verification/ScoreAuthenticite.jsx
// Jauge circulaire SVG affichant le score d'authenticité global
import PropTypes from 'prop-types';
import { CheckCircle, AlertTriangle, XCircle } from 'lucide-react';

/* ── Correspondance niveau → couleur ─────────────────────── */
const NIVEAU_COLORS = {
  ELEVE:    '#27AE60',
  MOYEN:    '#F39C12',
  FAIBLE:   '#E67E22',
  CRITIQUE: '#C0392B',
};

/* ── Correspondance recommandation → icône et couleur ────── */
const RECO_CONFIG = {
  VALIDER:        { Icon: CheckCircle,   color: '#27AE60', label: 'Valider' },
  VERIF_MANUELLE: { Icon: AlertTriangle, color: '#F39C12', label: 'Vérification manuelle requise' },
  REJETER:        { Icon: XCircle,       color: '#C0392B', label: 'Rejeter' },
};

export default function ScoreAuthenticite({ score = 0, niveau = 'MOYEN', recommandation = 'VERIF_MANUELLE' }) {
  const percentage = Math.round(score * 100);
  const color = NIVEAU_COLORS[niveau] || '#F39C12';
  const recoConfig = RECO_CONFIG[recommandation] || RECO_CONFIG.VERIF_MANUELLE;
  const { Icon: RecoIcon } = recoConfig;

  /* ── Paramètres de la jauge circulaire SVG ──────────────── */
  const size = 160;
  const strokeWidth = 12;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const dashOffset = circumference - (score * circumference);

  return (
    <div className="flex flex-col items-center gap-4">
      {/* Jauge circulaire */}
      <div className="relative">
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          {/* Cercle de fond */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#EBEDEF"
            strokeWidth={strokeWidth}
          />
          {/* Arc de progression */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
            style={{ transition: 'stroke-dashoffset 0.8s ease-in-out' }}
          />
        </svg>
        {/* Valeur centrale */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span
            className="text-3xl font-bold font-mono"
            style={{ color }}
          >
            {percentage}%
          </span>
          <span className="text-xs text-text-muted mt-0.5">Authenticité</span>
        </div>
      </div>

      {/* Badge niveau coloré */}
      <span
        className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold text-white"
        style={{ backgroundColor: color }}
      >
        {niveau === 'ELEVE' && 'Élevé'}
        {niveau === 'MOYEN' && 'Moyen'}
        {niveau === 'FAIBLE' && 'Faible'}
        {niveau === 'CRITIQUE' && 'Critique'}
      </span>

      {/* Recommandation */}
      <div className="flex items-center gap-2">
        <RecoIcon size={18} style={{ color: recoConfig.color }} />
        <span className="text-sm font-bold" style={{ color: recoConfig.color }}>
          {recoConfig.label}
        </span>
      </div>
    </div>
  );
}

ScoreAuthenticite.propTypes = {
  score: PropTypes.number.isRequired,
  niveau: PropTypes.oneOf(['ELEVE', 'MOYEN', 'FAIBLE', 'CRITIQUE']),
  recommandation: PropTypes.oneOf(['VALIDER', 'VERIF_MANUELLE', 'REJETER']),
};
