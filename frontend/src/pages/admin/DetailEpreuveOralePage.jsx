// src/pages/admin/DetailEpreuveOralePage.jsx
import { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getEpreuveOralDetail, convoquerAdmis, inscrireAcceptes, getStatistiquesOral } from '../../api/oral';
import DecisionModal from '../../components/admin/DecisionModal';
import ImportAdmisOralModal from '../../components/admin/ImportAdmisOralModal';
import { ArrowLeft, Users, Calendar, MapPin, Clock, Download, CheckCircle, FileText, Check, FileCheck, Ban, UserX, Upload } from 'lucide-react';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import toast from 'react-hot-toast';

export default function DetailEpreuveOralePage() {
  const { id } = useParams();
  const [epreuve, setEpreuve] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [selectedConvocation, setSelectedConvocation] = useState(null);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);

  const fetchEpreuve = useCallback(async () => {
    try {
      const data = await getEpreuveOralDetail(id);
      setEpreuve(data);
      const statData = await getStatistiquesOral(id);
      setStats(statData);
    } catch (err) {
      toast.error('Erreur lors du chargement des détails');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchEpreuve();
  }, [fetchEpreuve]);

  const handleConvoquerAdmis = async () => {
    setActionLoading('convoquer');
    try {
      const res = await convoquerAdmis(id);
      toast.success(`${res.convoques} candidats convoqués. ${res.pdfs_generes} PDFs générés.`);
      fetchEpreuve();
      setShowConfirmModal(false);
    } catch (err) {
      toast.error(err.response?.data?.error || 'Erreur lors de la convocation');
    } finally {
      setActionLoading(null);
    }
  };

  const handleInscrireAcceptes = async () => {
    setActionLoading('inscrire');
    try {
      const res = await inscrireAcceptes(id);
      toast.success(`${res.inscrits} candidats inscrits définitivement.`);
      fetchEpreuve();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Erreur lors de l\'inscription');
    } finally {
      setActionLoading(null);
    }
  };

  const openDecisionModal = (convocation) => {
    setSelectedConvocation(convocation);
  };

  if (loading) return <LoadingSpinner size="lg" text="Chargement..." className="py-20" />;
  if (!epreuve) return <div className="text-center py-20">Épreuve introuvable</div>;

  const totalDecides = epreuve.convocations.filter(c => c.decision !== 'EN_ATTENTE').length;
  const progressPercent = epreuve.nb_convoques > 0 ? (totalDecides / epreuve.nb_convoques) * 100 : 0;
  const tousDecides = epreuve.nb_convoques > 0 && totalDecides === epreuve.nb_convoques;

  const getDecisionBadge = (decision) => {
    switch (decision) {
      case 'EN_ATTENTE': return <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full font-bold">En attente</span>;
      case 'ACCEPTE': return <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full font-bold">Accepté</span>;
      case 'REFUSE': return <span className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded-full font-bold">Refusé</span>;
      case 'ABSENT': return <span className="px-2 py-1 bg-gray-800 text-white text-xs rounded-full font-bold">Absent</span>;
      default: return null;
    }
  };

  return (
    <div className="ensa-page animate-fade-in">
      <div className="ensa-page-header">
        <nav className="ensa-breadcrumb">
          <Link to="/admin/epreuves-oral"><ArrowLeft size={14} /> Épreuves Orales</Link>
          <span>/</span>
          <span className="ensa-breadcrumb-current">{epreuve.nom}</span>
        </nav>
        <div className="flex justify-between items-center mt-2">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{epreuve.nom}</h1>
            <p className="text-gray-500 mt-1">{epreuve.filiere_nom} ({epreuve.filiere_code})</p>
          </div>
          <div>
             <span className={`px-3 py-1 rounded-full text-sm font-bold ${
              epreuve.statut === 'PLANIFIEE' ? 'bg-blue-100 text-blue-800' :
              epreuve.statut === 'EN_COURS' ? 'bg-yellow-100 text-yellow-800' :
              epreuve.statut === 'TERMINEE' ? 'bg-gray-100 text-gray-800' :
              'bg-green-100 text-green-800'
            }`}>
              {epreuve.statut}
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Colonne Gauche (Infos, Actions, Stats) */}
        <div className="lg:col-span-4 space-y-6">
          
          <div className="card p-5">
            <h3 className="text-sm font-bold text-gray-800 mb-4 uppercase">Informations de l'oral</h3>
            <div className="space-y-3 text-sm">
              <div className="flex items-center gap-3"><Calendar size={16} className="text-gray-400"/> <span className="font-semibold">{epreuve.date_oral || 'Date non définie'}</span></div>
              <div className="flex items-center gap-3"><Clock size={16} className="text-gray-400"/> <span className="font-semibold">{epreuve.heure_debut || 'Heure non définie'}</span></div>
              <div className="flex items-center gap-3"><MapPin size={16} className="text-gray-400"/> <span>{epreuve.lieu}</span></div>
              <div className="flex items-center gap-3"><Users size={16} className="text-gray-400"/> <span>{epreuve.duree_minutes} minutes / candidat</span></div>
            </div>
          </div>

          <div className="card p-5">
            <h3 className="text-sm font-bold text-gray-800 mb-4 uppercase">Actions</h3>
            <div className="space-y-3">
              {epreuve.statut === 'PLANIFIEE' && (
                <button onClick={() => setShowConfirmModal(true)} disabled={actionLoading === 'convoquer'} className="w-full btn btn-primary flex justify-center">
                  {actionLoading === 'convoquer' ? 'Génération...' : 'Convoquer tous les admis'}
                </button>
              )}
              
              <button disabled={epreuve.nb_convoques === 0} className="w-full btn btn-outline flex justify-center gap-2">
                <Download size={16}/> Exporter liste de passage
              </button>

              <button
                onClick={() => setShowImportModal(true)}
                className="w-full btn flex justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white border-none shadow-sm"
              >
                <Upload size={16}/> Importer admis (Excel/CSV)
              </button>

              {epreuve.statut === 'EN_COURS' && tousDecides && (
                <button onClick={handleInscrireAcceptes} disabled={actionLoading === 'inscrire'} className="w-full btn btn-success flex justify-center gap-2 mt-4">
                  <CheckCircle size={16}/> Inscrire les candidats acceptés
                </button>
              )}
            </div>
          </div>

          {stats && (
            <div className="card p-5">
              <h3 className="text-sm font-bold text-gray-800 mb-4 uppercase">Statistiques</h3>
              
              <div className="mb-4">
                <div className="flex justify-between text-xs mb-1">
                  <span className="font-bold text-gray-600">Avancement des décisions</span>
                  <span className="font-bold text-blue-600">{Math.round(progressPercent)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${progressPercent}%` }}></div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 text-center">
                <div className="bg-gray-50 p-2 rounded"><div className="text-xl font-bold text-blue-600">{stats.total_convoques}</div><div className="text-xs text-gray-500">Convoqués</div></div>
                <div className="bg-gray-50 p-2 rounded"><div className="text-xl font-bold text-gray-800">{stats.presents}</div><div className="text-xs text-gray-500">Présents</div></div>
                <div className="bg-green-50 p-2 rounded"><div className="text-xl font-bold text-green-600">{stats.acceptes}</div><div className="text-xs text-gray-500">Acceptés</div></div>
                <div className="bg-red-50 p-2 rounded"><div className="text-xl font-bold text-red-600">{stats.refuses}</div><div className="text-xs text-gray-500">Refusés</div></div>
              </div>
              <div className="mt-3 text-center text-sm font-semibold text-gray-700">
                Taux d'acceptation : {stats.taux_acceptation}%
              </div>
            </div>
          )}

        </div>

        {/* Colonne Droite (Liste de passage) */}
        <div className="lg:col-span-8">
          <div className="card h-full">
            <div className="p-5 border-b border-gray-100 flex justify-between items-center">
              <h2 className="text-lg font-bold text-gray-800">Liste de passage — {epreuve.date_oral || ''}</h2>
              <span className="text-sm text-gray-500">{epreuve.convocations.length} candidats</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm whitespace-nowrap">
                <thead className="bg-gray-50 text-gray-600 font-semibold border-b border-gray-200">
                  <tr>
                    <th className="p-3">N°</th>
                    <th className="p-3">Heure</th>
                    <th className="p-3">Candidat</th>
                    <th className="p-3">CIN</th>
                    <th className="p-3 text-center">Score</th>
                    <th className="p-3 text-center">Docs</th>
                    <th className="p-3">Décision</th>
                    <th className="p-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {epreuve.convocations.map((conv) => (
                    <tr key={conv.id} className="hover:bg-gray-50 transition-colors">
                      <td className="p-3 font-bold text-gray-500">{conv.numero_passage}</td>
                      <td className="p-3 font-mono text-blue-800 font-bold bg-blue-50/50">{conv.heure_passage ? conv.heure_passage.substring(0, 5) : '—'}</td>
                      <td className="p-3 font-medium text-gray-900">{conv.candidat_nom} {conv.candidat_prenom}</td>
                      <td className="p-3 text-gray-500 font-mono">{conv.candidat_cin}</td>
                      <td className="p-3 text-center font-bold text-primary-700">{conv.score_dossier}</td>
                      <td className="p-3">
                        <div className="flex gap-1 justify-center">
                          <div title="Baccalauréat" className={`w-5 h-5 rounded flex items-center justify-center ${conv.bac_verifie ? 'bg-green-100 text-green-600' : 'bg-gray-200 text-gray-400'}`}><FileCheck size={12}/></div>
                          <div title="Diplôme" className={`w-5 h-5 rounded flex items-center justify-center ${conv.diplome_verifie ? 'bg-green-100 text-green-600' : 'bg-gray-200 text-gray-400'}`}><GraduationCap size={12} /></div>
                          <div title="Relevés" className={`w-5 h-5 rounded flex items-center justify-center ${conv.releve_notes_verifie ? 'bg-green-100 text-green-600' : 'bg-gray-200 text-gray-400'}`}><FileText size={12}/></div>
                          <div title="CIN" className={`w-5 h-5 rounded flex items-center justify-center ${conv.cin_verifie ? 'bg-green-100 text-green-600' : 'bg-gray-200 text-gray-400'}`}><Check size={12}/></div>
                        </div>
                      </td>
                      <td className="p-3">{getDecisionBadge(conv.decision)}</td>
                      <td className="p-3 text-right">
                        <button 
                          onClick={() => openDecisionModal(conv)} 
                          className="px-3 py-1.5 bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 rounded text-xs font-semibold shadow-sm"
                        >
                          Décision
                        </button>
                      </td>
                    </tr>
                  ))}
                  {epreuve.convocations.length === 0 && (
                    <tr><td colSpan="8" className="p-8 text-center text-gray-500">Aucun candidat convoqué.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

      </div>

      <DecisionModal 
        convocation={selectedConvocation} 
        epreuveId={epreuve.id} 
        isOpen={!!selectedConvocation} 
        onClose={() => setSelectedConvocation(null)} 
        onDecisionSaved={fetchEpreuve}
      />

      <ImportAdmisOralModal
        epreuve={epreuve}
        isOpen={showImportModal}
        onClose={() => setShowImportModal(false)}
        onImportDone={fetchEpreuve}
      />

      {showConfirmModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex justify-center items-center p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-sm p-6 text-center">
            <h3 className="text-lg font-bold mb-2">Convoquer les candidats</h3>
            <p className="text-gray-600 text-sm mb-6">
              Tous les candidats dont le dossier est "Admis définitivement" vont être convoqués. Des créneaux horaires vont être générés ainsi que des PDF.
            </p>
            <div className="flex gap-3 justify-center">
              <button onClick={() => setShowConfirmModal(false)} className="btn btn-outline">Annuler</button>
              <button onClick={handleConvoquerAdmis} disabled={actionLoading === 'convoquer'} className="btn btn-primary">
                {actionLoading === 'convoquer' ? 'En cours...' : 'Confirmer'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Composant icône manquant pour la lisibilité
const GraduationCap = ({size, className}) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>
);
