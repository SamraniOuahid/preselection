// src/components/admin/DecisionModal.jsx
import { useState, useEffect } from 'react';
import { X, CheckCircle, XCircle, UserX, AlertTriangle } from 'lucide-react';
import { enregistrerDecision } from '../../api/oral';
import toast from 'react-hot-toast';

export default function DecisionModal({ convocation, epreuveId, isOpen, onClose, onDecisionSaved }) {
  const [bacVerifie, setBacVerifie] = useState(false);
  const [diplomeVerifie, setDiplomeVerifie] = useState(false);
  const [releveVerifie, setReleveVerifie] = useState(false);
  const [cinVerifie, setCinVerifie] = useState(false);
  const [decision, setDecision] = useState('EN_ATTENTE');
  const [commentaire, setCommentaire] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (convocation && isOpen) {
      setBacVerifie(convocation.bac_verifie || false);
      setDiplomeVerifie(convocation.diplome_verifie || false);
      setReleveVerifie(convocation.releve_notes_verifie || false);
      setCinVerifie(convocation.cin_verifie || false);
      setDecision(convocation.decision || 'EN_ATTENTE');
      setCommentaire(convocation.commentaire_jury || '');
    }
  }, [convocation, isOpen]);

  if (!isOpen || !convocation) return null;

  const documentsIncomplets = !(bacVerifie && diplomeVerifie && releveVerifie && cinVerifie);

  const handleSubmit = async () => {
    if (decision === 'ACCEPTE' && documentsIncomplets) {
      toast.error('Impossible d\'accepter : documents incomplets');
      return;
    }

    setLoading(true);
    try {
      await enregistrerDecision(epreuveId, {
        dossier_id: convocation.dossier,
        decision,
        commentaire,
        bac_verifie: bacVerifie,
        diplome_verifie: diplomeVerifie,
        releve_verifie: releveVerifie,
        cin_verifie: cinVerifie,
      });
      toast.success('Décision enregistrée avec succès');
      onDecisionSaved();
      onClose();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Erreur lors de l\'enregistrement');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex justify-center items-center p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex justify-between items-center p-5 border-b">
          <h3 className="text-lg font-bold text-gray-800">
            Décision — {convocation.candidat_nom} {convocation.candidat_prenom}
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div className="p-5 overflow-y-auto flex-1 space-y-6">
          
          {/* Documents Section */}
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wide">
              Vérification des documents
            </h4>
            <div className="space-y-3 bg-gray-50 p-4 rounded-lg border border-gray-100">
              <label className="flex items-center gap-3 cursor-pointer">
                <input type="checkbox" checked={bacVerifie} onChange={(e) => setBacVerifie(e.target.checked)} className="w-4 h-4 rounded text-blue-600 focus:ring-blue-500" />
                <span className="text-sm font-medium">Baccalauréat (original vérifié)</span>
              </label>
              <label className="flex items-center gap-3 cursor-pointer">
                <input type="checkbox" checked={diplomeVerifie} onChange={(e) => setDiplomeVerifie(e.target.checked)} className="w-4 h-4 rounded text-blue-600 focus:ring-blue-500" />
                <span className="text-sm font-medium">Diplôme (DUT/BTS/Licence) original</span>
              </label>
              <label className="flex items-center gap-3 cursor-pointer">
                <input type="checkbox" checked={releveVerifie} onChange={(e) => setReleveVerifie(e.target.checked)} className="w-4 h-4 rounded text-blue-600 focus:ring-blue-500" />
                <span className="text-sm font-medium">Relevés de notes officiels</span>
              </label>
              <label className="flex items-center gap-3 cursor-pointer">
                <input type="checkbox" checked={cinVerifie} onChange={(e) => setCinVerifie(e.target.checked)} className="w-4 h-4 rounded text-blue-600 focus:ring-blue-500" />
                <span className="text-sm font-medium">CIN originale</span>
              </label>
            </div>

            {documentsIncomplets && (
              <div className="mt-3 bg-orange-50 text-orange-800 p-3 rounded-lg text-xs flex items-start gap-2 border border-orange-100">
                <AlertTriangle size={14} className="mt-0.5 flex-shrink-0 text-orange-600" />
                <p>Document manquant — impossible d'accepter ce candidat sans tous les documents vérifiés.</p>
              </div>
            )}
          </div>

          {/* Decision Section */}
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wide">
              Décision du jury
            </h4>
            <div className="grid grid-cols-3 gap-3">
              <label className={`flex flex-col items-center justify-center p-3 rounded-lg border-2 cursor-pointer transition-all ${decision === 'ACCEPTE' ? 'border-green-500 bg-green-50 text-green-700' : 'border-gray-200 hover:border-gray-300'}`}>
                <input type="radio" name="decision" value="ACCEPTE" checked={decision === 'ACCEPTE'} onChange={() => setDecision('ACCEPTE')} className="sr-only" />
                <CheckCircle size={24} className={decision === 'ACCEPTE' ? 'text-green-600' : 'text-gray-400'} />
                <span className="mt-2 text-sm font-bold">ACCEPTÉ</span>
              </label>
              
              <label className={`flex flex-col items-center justify-center p-3 rounded-lg border-2 cursor-pointer transition-all ${decision === 'REFUSE' ? 'border-red-500 bg-red-50 text-red-700' : 'border-gray-200 hover:border-gray-300'}`}>
                <input type="radio" name="decision" value="REFUSE" checked={decision === 'REFUSE'} onChange={() => setDecision('REFUSE')} className="sr-only" />
                <XCircle size={24} className={decision === 'REFUSE' ? 'text-red-600' : 'text-gray-400'} />
                <span className="mt-2 text-sm font-bold">REFUSÉ</span>
              </label>

              <label className={`flex flex-col items-center justify-center p-3 rounded-lg border-2 cursor-pointer transition-all ${decision === 'ABSENT' ? 'border-gray-800 bg-gray-100 text-gray-900' : 'border-gray-200 hover:border-gray-300'}`}>
                <input type="radio" name="decision" value="ABSENT" checked={decision === 'ABSENT'} onChange={() => setDecision('ABSENT')} className="sr-only" />
                <UserX size={24} className={decision === 'ABSENT' ? 'text-gray-800' : 'text-gray-400'} />
                <span className="mt-2 text-sm font-bold">ABSENT</span>
              </label>
            </div>
          </div>

          {/* Comment Section */}
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-2 uppercase tracking-wide flex justify-between">
              Note interne du jury
              <span className="text-xs text-gray-400 font-normal normal-case">Confidentiel</span>
            </h4>
            <textarea
              className="w-full border border-gray-300 rounded-lg p-3 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              rows={3}
              placeholder="Observations internes — non communiquées au candidat"
              value={commentaire}
              onChange={(e) => setCommentaire(e.target.value)}
            />
          </div>

        </div>

        {/* Footer */}
        <div className="p-5 border-t bg-gray-50 flex justify-end gap-3 rounded-b-xl">
          <button onClick={onClose} className="px-4 py-2 text-sm font-semibold text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
            Annuler
          </button>
          <button 
            onClick={handleSubmit} 
            disabled={loading || (decision === 'ACCEPTE' && documentsIncomplets)}
            className="px-6 py-2 text-sm font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center min-w-[160px]"
          >
            {loading ? <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span> : 'Enregistrer la décision'}
          </button>
        </div>
      </div>
    </div>
  );
}
