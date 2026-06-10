// src/pages/admin/DetailEpreuvePage.jsx
import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getEpreuveDetail, getEpreuveStats, publierResultats, exportResultats, downloadTemplate } from '../../api/epreuves';
import SeuilSlider from '../../components/epreuve/SeuilSlider';
import ImportExcelWizard from '../../components/epreuve/ImportExcelWizard';
import DistributionChart from '../../components/epreuve/DistributionChart';
import ConfirmModal from '../../components/common/ConfirmModal';
import StatusBadge from '../../components/common/StatusBadge';
import { ArrowLeft, Users, Download, Megaphone, FileSpreadsheet } from 'lucide-react';
import toast from 'react-hot-toast';
import API from '../../api/axios';

export default function DetailEpreuvePage() {
  const { id } = useParams();
  const [epreuve, setEpreuve] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isPublishModalOpen, setIsPublishModalOpen] = useState(false);
  const [publishing, setPublishing] = useState(false);

  useEffect(() => {
    fetchData();
  }, [id]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const epData = await getEpreuveDetail(id);
      setEpreuve(epData);
      if (epData.statut !== 'NON_COMMENCEE') {
         const stData = await getEpreuveStats(id);
         setStats(stData);
      }
    } catch (error) {
      toast.error('Erreur lors du chargement des détails de l\'épreuve');
    } finally {
      setLoading(false);
    }
  };

  const handlePublish = async () => {
    setPublishing(true);
    try {
      await publierResultats(id);
      toast.success('Les résultats ont été publiés et les candidats notifiés.');
      setIsPublishModalOpen(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.error || 'Erreur lors de la publication');
    } finally {
      setPublishing(false);
    }
  };

  if (loading) return <div className="flex justify-center p-12"><div className="spinner"></div></div>;
  if (!epreuve) return <div>Épreuve non trouvée.</div>;

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* HEADER */}
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
        <div>
          <Link to="/admin/epreuves" className="text-gray-500 hover:text-blue-600 flex items-center gap-1 text-sm font-medium mb-3 transition-colors w-max">
            <ArrowLeft size={16} /> Retour aux épreuves
          </Link>
          <div className="flex items-center gap-3">
             <h1 className="text-3xl font-black text-gray-900 tracking-tight">{epreuve.nom}</h1>
             <span className="bg-gray-100 text-gray-600 px-3 py-1 rounded-full text-sm font-bold border border-gray-200">{epreuve.filiere_code}</span>
          </div>
          <p className="text-gray-500 text-sm mt-1">{epreuve.filiere_nom}</p>
        </div>
        <div className="flex items-center gap-3">
           <Link to={`/admin/epreuves/${id}/resultats`} className="bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded-xl text-sm font-semibold hover:bg-gray-50 transition-colors">
              Liste détaillée
           </Link>
           {stats && (
             <button onClick={() => exportResultats(id)} className="bg-green-600 text-white px-4 py-2 rounded-xl text-sm font-semibold hover:bg-green-700 transition-colors flex items-center gap-2 shadow-sm shadow-green-200">
               <Download size={16}/> Exporter Excel
             </button>
           )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
         {/* ZONE GAUCHE (40%) */}
         <div className="lg:col-span-4 space-y-6">
            
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
               <div className="flex justify-between items-center mb-4">
                  <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider">Informations</h3>
               </div>
               <div className="space-y-3">
                  <div className="flex justify-between border-b border-gray-50 pb-2">
                     <span className="text-gray-500 text-sm">Date & Heure Écrit</span>
                     <span className="font-semibold text-blue-900 text-sm">{epreuve.date_ecrit ? new Date(epreuve.date_ecrit).toLocaleString('fr-FR') : '-'}</span>
                  </div>
                  <div className="flex justify-between border-b border-gray-50 pb-2">
                     <span className="text-gray-500 text-sm">Date & Heure Oral</span>
                     <span className="font-semibold text-purple-900 text-sm">{epreuve.date_oral ? new Date(epreuve.date_oral).toLocaleString('fr-FR') : '-'}</span>
                  </div>
                  <div className="flex justify-between border-b border-gray-50 pb-2">
                     <span className="text-gray-500 text-sm">Lieu Oral</span>
                     <span className="font-semibold text-gray-900 text-sm">{epreuve.lieu_oral || '-'}</span>
                  </div>
                  <div className="flex justify-between border-b border-gray-50 pb-2">
                     <span className="text-gray-500 text-sm">Notée sur</span>
                     <span className="font-medium text-gray-900 text-sm">{parseFloat(epreuve.note_sur)} points</span>
                  </div>
                  <div className="flex justify-between border-b border-gray-50 pb-2">
                     <span className="text-gray-500 text-sm">Coefficient final</span>
                     <span className="font-medium text-gray-900 text-sm">x {parseFloat(epreuve.coefficient)}</span>
                  </div>
                  <div className="flex justify-between pt-1 items-center">
                     <span className="text-gray-500 text-sm">Statut actuel</span>
                     <StatusBadge statut={epreuve.statut} />
                  </div>
               </div>
            </div>

            {epreuve.statut === 'NOTES_IMPORTEES' && (
               <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-6 rounded-xl border border-blue-100 shadow-sm relative overflow-hidden">
                  <div className="absolute -right-4 -top-4 opacity-10"><Megaphone size={100}/></div>
                  <h3 className="text-lg font-bold text-blue-900 mb-2 relative z-10">Publier les résultats</h3>
                  <p className="text-sm text-blue-800/80 mb-5 relative z-10">
                     Les notes sont importées et le seuil est validé. Vous pouvez maintenant notifier les candidats de leurs résultats.
                  </p>
                  <button 
                     onClick={() => setIsPublishModalOpen(true)}
                     className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2.5 rounded-lg shadow-sm transition-colors relative z-10 flex justify-center items-center gap-2"
                  >
                     <Megaphone size={18}/> Publier et notifier
                  </button>
               </div>
            )}

            {epreuve.statut !== 'NON_COMMENCEE' && (
               <SeuilSlider 
                  epreuveId={epreuve.id} 
                  seuilActuel={epreuve.seuil_admission} 
                  noteSur={epreuve.note_sur} 
                  onSeuilChanged={(res) => {
                     setEpreuve({...epreuve, seuil_admission: res.nouveau_seuil});
                     fetchData();
                  }}
                  disabled={epreuve.statut === 'RESULTATS_PUBLIES'}
               />
            )}
         </div>

         {/* ZONE DROITE (60%) */}
         <div className="lg:col-span-8 space-y-6">
            
            {epreuve.statut === 'NON_COMMENCEE' && (
               <ImportExcelWizard 
                  epreuveId={epreuve.id} 
                  onImportSuccess={fetchData}
               />
            )}

            {epreuve.statut !== 'NON_COMMENCEE' && stats && (
               <div className="space-y-6">
                  {/* Stats Cards */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                     <div className="bg-white p-4 rounded-xl border border-gray-100 shadow-sm text-center">
                        <div className="text-2xl font-black text-gray-900">{stats.total_candidats}</div>
                        <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mt-1">Total</div>
                     </div>
                     <div className="bg-green-50 p-4 rounded-xl border border-green-100 shadow-sm text-center">
                        <div className="text-2xl font-black text-green-700">{stats.nb_admis}</div>
                        <div className="text-xs font-semibold text-green-600/80 uppercase tracking-wide mt-1">Admis ({stats.taux_admission}%)</div>
                     </div>
                     <div className="bg-red-50 p-4 rounded-xl border border-red-100 shadow-sm text-center">
                        <div className="text-2xl font-black text-red-700">{stats.nb_recales}</div>
                        <div className="text-xs font-semibold text-red-600/80 uppercase tracking-wide mt-1">Recalés</div>
                     </div>
                     <div className="bg-gray-50 p-4 rounded-xl border border-gray-200 shadow-sm text-center">
                        <div className="text-2xl font-black text-gray-600">{stats.nb_absents}</div>
                        <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mt-1">Absents</div>
                     </div>
                  </div>

                  {/* Chart */}
                  <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                     <h3 className="text-lg font-bold text-gray-900 mb-6 flex items-center justify-between">
                        Distribution des notes
                        <div className="text-sm font-medium text-gray-500 flex gap-4">
                           <span className="flex items-center gap-1"><div className="w-3 h-3 bg-red-400 rounded-sm"></div> Min: {stats.note_min}</span>
                           <span className="flex items-center gap-1"><div className="w-3 h-3 bg-yellow-400 rounded-sm"></div> Moy: {stats.note_moyenne}</span>
                           <span className="flex items-center gap-1"><div className="w-3 h-3 bg-green-400 rounded-sm"></div> Max: {stats.note_max}</span>
                        </div>
                     </h3>
                     <DistributionChart data={stats.distribution} seuil={epreuve.seuil_admission} />
                  </div>
                  
                  {epreuve.statut === 'NOTES_IMPORTEES' && (
                     <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm flex items-center justify-between">
                        <div>
                           <h4 className="font-bold text-gray-800 flex items-center gap-2"><FileSpreadsheet size={18} className="text-blue-600"/> Réimporter des notes</h4>
                           <p className="text-sm text-gray-500 mt-1">Un nouvel import écrasera les notes existantes des candidats concernés.</p>
                        </div>
                        <ImportExcelWizard epreuveId={epreuve.id} onImportSuccess={fetchData} /> 
                     </div>
                  )}
               </div>
            )}

            {epreuve.statut === 'NON_COMMENCEE' && (
               <div className="text-center mt-8">
                  <button onClick={downloadTemplate} className="text-blue-600 hover:text-blue-800 text-sm font-medium flex items-center justify-center gap-2 mx-auto transition-colors">
                     <FileSpreadsheet size={16}/> Télécharger le modèle Excel
                  </button>
               </div>
            )}
         </div>
      </div>

      <ConfirmModal
        isOpen={isPublishModalOpen}
        onClose={() => setIsPublishModalOpen(false)}
        onConfirm={handlePublish}
        title="Publier les résultats finaux"
        message="Attention : cette action est irréversible. Un e-mail sera envoyé immédiatement à tous les candidats de cette épreuve pour leur annoncer s'ils sont admis ou recalés. Confirmez-vous la publication ?"
        confirmText="Oui, publier et notifier"
        cancelText="Annuler"
        isDanger={false} // Bien que sérieux, c'est une action métier positive
      />
    </div>
  );
}
