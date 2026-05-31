// src/components/epreuve/SeuilSlider.jsx
import { useState, useEffect } from 'react';
import { simulerSeuil, changerSeuil } from '../../api/epreuves';
import toast from 'react-hot-toast';
import { Settings2, CheckCircle2, Info } from 'lucide-react';
import ConfirmModal from '../common/ConfirmModal';

export default function SeuilSlider({ epreuveId, seuilActuel, noteSur, onSeuilChanged, disabled }) {
  const [valeur, setValeur] = useState(parseFloat(seuilActuel));
  const [simulation, setSimulation] = useState(null);
  const [loadingSim, setLoadingSim] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Debounce for simulation
  useEffect(() => {
    if (valeur === parseFloat(seuilActuel) || disabled) {
      setSimulation(null);
      return;
    }
    const timer = setTimeout(() => {
      setLoadingSim(true);
      simulerSeuil(epreuveId, valeur)
        .then((data) => setSimulation(data))
        .catch(() => toast.error('Erreur lors de la simulation'))
        .finally(() => setLoadingSim(false));
    }, 500);

    return () => clearTimeout(timer);
  }, [valeur, epreuveId, seuilActuel, disabled]);

  const handleValider = async () => {
    try {
      const result = await changerSeuil(epreuveId, valeur);
      toast.success('Le seuil a été mis à jour avec succès.');
      onSeuilChanged(result);
      setIsModalOpen(false);
      setSimulation(null);
    } catch (error) {
      toast.error('Erreur lors de la mise à jour du seuil.');
    }
  };

  const pct = (valeur / parseFloat(noteSur)) * 100;
  let colorClass = 'text-green-600';
  let bgClass = 'bg-green-600';
  if (pct < 50) {
    colorClass = 'text-red-600';
    bgClass = 'bg-red-600';
  } else if (pct < 60) {
    colorClass = 'text-orange-500';
    bgClass = 'bg-orange-500';
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
          <Settings2 className="text-blue-600" size={20} />
          Seuil d'admission
        </h3>
        <div className={`text-2xl font-black ${colorClass}`}>
          {valeur.toFixed(2)} <span className="text-sm font-medium text-gray-400">/ {noteSur}</span>
        </div>
      </div>

      <input
        type="range"
        min="0"
        max={noteSur}
        step="0.5"
        value={valeur}
        onChange={(e) => setValeur(parseFloat(e.target.value))}
        disabled={disabled}
        className={`w-full h-2 rounded-lg appearance-none cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed ${bgClass}`}
        style={{
          background: `linear-gradient(to right, currentColor ${pct}%, #E5E7EB ${pct}%)`
        }}
      />
      <div className="flex justify-between text-xs text-gray-400 mt-2">
        <span>0</span>
        <span>{noteSur / 2}</span>
        <span>{noteSur}</span>
      </div>

      {simulation && (
        <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-100">
          <h4 className="text-sm font-semibold text-blue-900 flex items-center gap-2 mb-3">
            <Info size={16} /> Prévisualisation (Simulation)
          </h4>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white p-3 rounded shadow-sm">
              <div className="text-xs text-gray-500">Admis prévus</div>
              <div className="text-lg font-bold text-green-600">
                {simulation.nb_admis_simule}
                <span className={`text-xs ml-2 ${simulation.difference >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                  {simulation.difference > 0 ? '+' : ''}{simulation.difference}
                </span>
              </div>
            </div>
            <div className="bg-white p-3 rounded shadow-sm">
              <div className="text-xs text-gray-500">Recalés prévus</div>
              <div className="text-lg font-bold text-red-600">
                {simulation.nb_recales_simule}
              </div>
            </div>
          </div>

          <button
            onClick={() => setIsModalOpen(true)}
            className="mt-4 w-full flex items-center justify-center gap-2 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium text-sm"
          >
            <CheckCircle2 size={16} />
            Appliquer ce nouveau seuil
          </button>
        </div>
      )}

      {loadingSim && <div className="mt-4 text-xs text-center text-gray-400 animate-pulse">Simulation en cours...</div>}

      <ConfirmModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onConfirm={handleValider}
        title="Confirmer le changement de seuil"
        message={`Vous êtes sur le point de modifier le seuil d'admission de ${seuilActuel} à ${valeur}. Cela recalculera automatiquement le statut d'admission pour tous les candidats de cette épreuve. Voulez-vous continuer ?`}
        confirmText="Appliquer le seuil"
        cancelText="Annuler"
      />
    </div>
  );
}
