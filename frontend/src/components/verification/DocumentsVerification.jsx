// src/components/verification/DocumentsVerification.jsx
// Tableau de statut de vérification par document (qualité OCR, conformité)
import PropTypes from 'prop-types';
import { FileText, Award, CreditCard, User } from 'lucide-react';

/* ── Icônes par type de document ─────────────────────────── */
const TYPE_ICONS = {
  RELEVE:  FileText,
  DIPLOME: Award,
  CIN:     CreditCard,
  PHOTO:   User,
};

/* ── Labels lisibles pour les types ──────────────────────── */
const TYPE_LABELS = {
  RELEVE:  'Relevé de notes',
  DIPLOME: 'Diplôme',
  CIN:     'Carte d\'identité',
  PHOTO:   'Photo d\'identité',
};

/* ── Configuration couleurs par seuil de qualité ─────────── */
const getQualiteConfig = (score) => {
  if (score >= 0.80) return { color: '#27AE60', bg: '#EAFAF1', label: 'Conforme', badgeBg: '#27AE60' };
  if (score >= 0.60) return { color: '#F39C12', bg: '#FEF9E7', label: 'À vérifier', badgeBg: '#F39C12' };
  return { color: '#C0392B', bg: '#FDEDEC', label: 'Suspect', badgeBg: '#C0392B' };
};

export default function DocumentsVerification({ documents = [] }) {
  if (!documents || documents.length === 0) {
    return (
      <div className="text-center py-8 text-sm text-text-muted">
        Aucun document analysé
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="table w-full">
        <thead>
          <tr>
            <th className="text-left">Type document</th>
            <th className="text-left">Nom fichier</th>
            <th className="text-right">Taille</th>
            <th className="text-left" style={{ minWidth: '180px' }}>Score qualité</th>
            <th className="text-center">Statut</th>
          </tr>
        </thead>
        <tbody>
          {documents.map((doc, index) => {
            const Icon = TYPE_ICONS[doc.type] || FileText;
            const qualite = getQualiteConfig(doc.qualite_ocr);
            const scorePercent = Math.round(doc.qualite_ocr * 100);

            return (
              <tr key={index} className="group transition-all duration-200 hover:bg-gray-50/50">
                {/* Type document avec icône */}
                <td>
                  <div className="flex items-center gap-2.5">
                    <div
                      className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                      style={{ background: qualite.bg }}
                    >
                      <Icon size={16} style={{ color: qualite.color }} />
                    </div>
                    <span className="text-sm font-medium">
                      {TYPE_LABELS[doc.type] || doc.type}
                    </span>
                  </div>
                </td>

                {/* Nom fichier */}
                <td className="text-xs text-text-secondary font-mono max-w-[200px] truncate">
                  {doc.nom_fichier || '—'}
                </td>

                {/* Taille */}
                <td className="text-right text-xs text-text-muted font-mono whitespace-nowrap">
                  {doc.taille_ko ? `${doc.taille_ko} Ko` : '—'}
                </td>

                {/* Barre de progression score qualité */}
                <td>
                  <div className="flex items-center gap-3">
                    <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-500 ease-out"
                        style={{
                          width: `${scorePercent}%`,
                          backgroundColor: qualite.color,
                        }}
                      />
                    </div>
                    <span
                      className="text-xs font-semibold font-mono w-10 text-right"
                      style={{ color: qualite.color }}
                    >
                      {scorePercent}%
                    </span>
                  </div>
                </td>

                {/* Badge statut */}
                <td className="text-center">
                  <span
                    className="inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-semibold text-white"
                    style={{ backgroundColor: qualite.badgeBg }}
                  >
                    {qualite.label}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

DocumentsVerification.propTypes = {
  documents: PropTypes.arrayOf(
    PropTypes.shape({
      type: PropTypes.string.isRequired,
      qualite_ocr: PropTypes.number.isRequired,
      nom_fichier: PropTypes.string,
      taille_ko: PropTypes.number,
    })
  ).isRequired,
};
