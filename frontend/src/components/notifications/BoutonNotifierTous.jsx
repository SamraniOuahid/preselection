// src/components/notifications/BoutonNotifierTous.jsx
// Bouton d'envoi de notifications en masse avec badge et modal intégré

import { useState, useEffect } from 'react';
import { Bell } from 'lucide-react';
import API from '../../api/axios';
import NotifierTousModal from './NotifierTousModal';

export default function BoutonNotifierTous({
  filiereId = null,
  filiereNom = '',
  variant = 'default',
  onSuccess,
}) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [nonNotifies, setNonNotifies] = useState(0);

  // Récupérer le nombre de non-notifiés au montage
  useEffect(() => {
    const params = filiereId ? `?filiere_id=${filiereId}` : '';
    API.get(`/notifications/previsualiser/${params}`)
      .then(({ data }) => {
        setNonNotifies(data.stats?.a_notifier || 0);
      })
      .catch(() => {});
  }, [filiereId]);

  const handleSuccess = () => {
    setNonNotifies(0);
    if (onSuccess) onSuccess();
  };

  return (
    <>
      <button
        onClick={() => setIsModalOpen(true)}
        className="btn btn-sm relative flex items-center gap-2"
        style={{
          background: variant === 'outline' ? 'transparent' : '#1B3A6B',
          color: variant === 'outline' ? '#1B3A6B' : '#fff',
          border: variant === 'outline' ? '1px solid #1B3A6B' : 'none',
        }}
      >
        <Bell size={15} />
        <span>Notifier tous les présélectionnés</span>

        {/* Badge rouge si candidats non notifiés */}
        {nonNotifies > 0 && (
          <span
            className="absolute -top-1.5 -right-1.5 min-w-[18px] h-[18px] flex items-center justify-center rounded-full text-[10px] font-bold text-white px-1"
            style={{ background: '#C0392B' }}
          >
            {nonNotifies > 99 ? '99+' : nonNotifies}
          </span>
        )}
      </button>

      <NotifierTousModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={handleSuccess}
        filiereId={filiereId}
        filiereNom={filiereNom}
      />
    </>
  );
}
