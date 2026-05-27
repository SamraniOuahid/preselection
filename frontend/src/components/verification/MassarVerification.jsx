// src/components/verification/MassarVerification.jsx
// Composant carte pour la vérification Massar manuelle
import { useState } from 'react';
import PropTypes from 'prop-types';
import { AlertTriangle, CheckCircle, Loader } from 'lucide-react';
import { marquerMassarVerifie } from '../../api/dossiers';
import toast from 'react-hot-toast';

export default function MassarVerification({
  dossierId,
  massarVerifie,
  cne,
  codeMassar,
  onVerifie,
}) {
  const [loading, setLoading] = useState(false);

  const handleConfirmerMassar = async () => {
    setLoading(true);
    try {
      await marquerMassarVerifie(dossierId);
      toast.success('Dossier marqué comme vérifié via Massar avec succès !');
      if (onVerifie) {
        onVerifie();
      }
    } catch (err) {
      toast.error(err.response?.data?.error || "Erreur lors de la validation Massar.");
    } finally {
      setLoading(false);
    }
  };

  if (!massarVerifie) {
    return (
      <div
        className="rounded-xl p-5 border flex flex-col md:flex-row md:items-center justify-between gap-4 transition-all duration-200"
        style={{
          background: 'rgba(254, 249, 231, 0.6)',
          borderColor: '#F9E79F',
        }}
      >
        <div className="flex items-start gap-4">
          <div
            className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"
            style={{ background: '#FEF9E7' }}
          >
            <AlertTriangle size={20} className="text-warning-600" style={{ color: '#F39C12' }} />
          </div>
          <div>
            <h4 className="text-sm font-bold text-text-primary" style={{ color: '#784212' }}>
              Vérification Massar en attente
            </h4>
            <p className="text-xs text-text-secondary mt-1 max-w-xl">
              Connectez-vous à votre espace Massar pour confirmer les informations académiques de ce candidat.
            </p>
            <div className="flex flex-wrap gap-4 mt-3">
              {cne && (
                <div className="bg-white/80 border border-amber-200/50 px-2.5 py-1 rounded text-xs">
                  <span className="text-text-muted">CNE : </span>
                  <span className="font-mono font-bold text-gray-700">{cne}</span>
                </div>
              )}
              {codeMassar && (
                <div className="bg-white/80 border border-amber-200/50 px-2.5 py-1 rounded text-xs">
                  <span className="text-text-muted">Code Massar : </span>
                  <span className="font-mono font-bold text-gray-700">{codeMassar}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        <button
          onClick={handleConfirmerMassar}
          disabled={loading}
          className="btn btn-primary btn-sm flex items-center gap-2 whitespace-nowrap self-start md:self-center"
          style={{ backgroundColor: '#2E86C1' }}
        >
          {loading ? (
            <Loader size={14} className="animate-spin" />
          ) : (
            <CheckCircle size={14} />
          )}
          Marquer comme vérifié via Massar
        </button>
      </div>
    );
  }

  return (
    <div
      className="rounded-xl p-5 border flex items-start gap-4 transition-all duration-200"
      style={{
        background: 'rgba(234, 250, 241, 0.6)',
        borderColor: '#A9DFBF',
      }}
    >
      <div
        className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0"
        style={{ background: '#EAFAF1' }}
      >
        <CheckCircle size={20} style={{ color: '#27AE60' }} />
      </div>
      <div>
        <h4 className="text-sm font-bold" style={{ color: '#1E8449' }}>
          Vérifié via Massar ✓
        </h4>
        <p className="text-xs mt-1" style={{ color: '#27AE60' }}>
          Les informations académiques ont été confirmées manuellement via le portail Massar.
        </p>
      </div>
    </div>
  );
}

MassarVerification.propTypes = {
  dossierId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  massarVerifie: PropTypes.bool.isRequired,
  cne: PropTypes.string,
  codeMassar: PropTypes.string,
  onVerifie: PropTypes.func.isRequired,
};
