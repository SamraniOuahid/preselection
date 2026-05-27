// src/components/verification/AlertesVerification.jsx
// Liste des alertes de vérification avec gravité détectée automatiquement
import PropTypes from 'prop-types';
import { useState } from 'react';
import { CheckCircle, AlertCircle, Copy, Check } from 'lucide-react';
import toast from 'react-hot-toast';

/* ── Détection de la gravité selon les mots-clés ─────────── */
const MOTS_CRITIQUE = ['falsif', 'doublon', 'absent', 'non détecté'];
const MOTS_AVERTISSEMENT = ['modifié', 'suspect', 'répétition'];

const detecterGravite = (texte) => {
  const lower = texte.toLowerCase();
  if (MOTS_CRITIQUE.some((mot) => lower.includes(mot))) return 'CRITIQUE';
  if (MOTS_AVERTISSEMENT.some((mot) => lower.includes(mot))) return 'AVERTISSEMENT';
  return 'INFO';
};

/* ── Configuration couleurs par gravité ──────────────────── */
const GRAVITE_CONFIG = {
  CRITIQUE:      { bg: '#FDEDEC', border: '#F5B7B1', text: '#C0392B', badge: '#C0392B' },
  AVERTISSEMENT: { bg: '#FEF9E7', border: '#F9E79F', text: '#B7950B', badge: '#F39C12' },
  INFO:          { bg: '#EBF5FB', border: '#AED6F1', text: '#2E86C1', badge: '#2E86C1' },
};

/* ── Couleur du header selon le niveau global ────────────── */
const HEADER_COLORS = {
  ELEVE:    { bg: '#EAFAF1', border: '#A9DFBF', text: '#1E8449' },
  MOYEN:    { bg: '#FEF9E7', border: '#F9E79F', text: '#B7950B' },
  FAIBLE:   { bg: '#FDEBD0', border: '#F5CBA7', text: '#CA6F1E' },
  CRITIQUE: { bg: '#FDEDEC', border: '#F5B7B1', text: '#922B21' },
};

export default function AlertesVerification({ alertes = [], niveau = 'MOYEN' }) {
  const [copied, setCopied] = useState(false);

  /* ── Aucune anomalie ───────────────────────────────────── */
  if (!alertes || alertes.length === 0) {
    return (
      <div
        className="rounded-xl p-5 flex items-center gap-3 transition-all duration-200"
        style={{ background: '#EAFAF1', border: '1px solid #A9DFBF' }}
      >
        <CheckCircle size={22} style={{ color: '#27AE60' }} />
        <div>
          <p className="text-sm font-semibold" style={{ color: '#1E8449' }}>
            Aucune anomalie détectée
          </p>
          <p className="text-xs mt-0.5" style={{ color: '#27AE60' }}>
            Tous les contrôles automatiques sont conformes.
          </p>
        </div>
      </div>
    );
  }

  const headerColor = HEADER_COLORS[niveau] || HEADER_COLORS.MOYEN;

  /* ── Copier toutes les alertes dans le presse-papier ───── */
  const handleCopy = async () => {
    const texte = alertes.map((a, i) => `${i + 1}. [${detecterGravite(a)}] ${a}`).join('\n');
    try {
      await navigator.clipboard.writeText(texte);
      setCopied(true);
      toast.success('Rapport copié dans le presse-papier');
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error('Impossible de copier le rapport');
    }
  };

  return (
    <div className="rounded-xl overflow-hidden transition-all duration-200" style={{ border: `1px solid ${headerColor.border}` }}>
      {/* Header avec compteur */}
      <div
        className="px-4 py-3 flex items-center justify-between"
        style={{ background: headerColor.bg }}
      >
        <div className="flex items-center gap-2">
          <AlertCircle size={16} style={{ color: headerColor.text }} />
          <span className="text-sm font-semibold" style={{ color: headerColor.text }}>
            {alertes.length} alerte{alertes.length > 1 ? 's' : ''} détectée{alertes.length > 1 ? 's' : ''}
          </span>
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-lg transition-all duration-200 hover:opacity-80"
          style={{
            background: copied ? '#27AE60' : 'white',
            color: copied ? 'white' : headerColor.text,
            border: `1px solid ${copied ? '#27AE60' : headerColor.border}`,
          }}
        >
          {copied ? <Check size={12} /> : <Copy size={12} />}
          {copied ? 'Copié !' : 'Copier le rapport'}
        </button>
      </div>

      {/* Liste des alertes */}
      <div className="divide-y" style={{ borderColor: headerColor.border + '40' }}>
        {alertes.map((alerte, index) => {
          const gravite = detecterGravite(alerte);
          const config = GRAVITE_CONFIG[gravite];
          return (
            <div
              key={index}
              className="px-4 py-3 flex items-start gap-3 transition-all duration-200 hover:bg-gray-50/50"
            >
              <AlertCircle
                size={16}
                className="flex-shrink-0 mt-0.5"
                style={{ color: config.badge }}
              />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-text-primary leading-snug">{alerte}</p>
              </div>
              <span
                className="flex-shrink-0 inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold text-white uppercase tracking-wide"
                style={{ backgroundColor: config.badge }}
              >
                {gravite}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

AlertesVerification.propTypes = {
  alertes: PropTypes.arrayOf(PropTypes.string).isRequired,
  niveau: PropTypes.oneOf(['ELEVE', 'MOYEN', 'FAIBLE', 'CRITIQUE']),
};
