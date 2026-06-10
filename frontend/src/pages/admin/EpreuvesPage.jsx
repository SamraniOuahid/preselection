// src/pages/admin/EpreuvesPage.jsx
import { useState, useEffect } from 'react';
import { getEpreuves, createEpreuve } from '../../api/epreuves';
import { useNavigate, Link } from 'react-router-dom';
import { Plus, Search, Calendar, Users, GraduationCap, ArrowRight, Settings2 } from 'lucide-react';
import API from '../../api/axios';
import toast from 'react-hot-toast';

export default function EpreuvesPage() {
  const [epreuves, setEpreuves] = useState([]);
  const [filieres, setFilieres] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [filterStatut, setFilterStatut] = useState('');
  
  const navigate = useNavigate();

  useEffect(() => {
    fetchData();
    API.get('/filieres/').then(r => setFilieres(r.data.results || r.data));
  }, [filterStatut]);

  const fetchData = () => {
    setLoading(true);
    getEpreuves(filterStatut ? { statut: filterStatut } : {})
      .then((data) => {
        const list = data.results || data;
        setEpreuves(Array.isArray(list) ? list : []);
      })
      .catch(() => toast.error('Erreur lors du chargement des épreuves'))
      .finally(() => setLoading(false));
  };

  const StatutBadge = ({ statut }) => {
    const configs = {
      'NON_COMMENCEE': { bg: 'bg-gray-100', text: 'text-gray-700', label: 'Non commencée' },
      'EN_COURS': { bg: 'bg-blue-100', text: 'text-blue-700', label: 'En cours' },
      'NOTES_IMPORTEES': { bg: 'bg-yellow-100', text: 'text-yellow-700', label: 'Notes importées' },
      'RESULTATS_PUBLIES': { bg: 'bg-green-100', text: 'text-green-700', label: 'Résultats publiés' },
    };
    const c = configs[statut] || configs['NON_COMMENCEE'];
    return (
      <span className={`px-2.5 py-1 text-xs font-medium rounded-full ${c.bg} ${c.text}`}>
        {c.label}
      </span>
    );
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-gray-900 tracking-tight">Épreuves Écrites</h1>
          <p className="text-gray-500 text-sm mt-1">Gestion des notes et des résultats d'admission</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2.5 rounded-xl text-sm font-semibold transition-colors flex items-center gap-2 shadow-sm shadow-blue-200"
        >
          <Plus size={18} />
          Créer une épreuve
        </button>
      </div>

      <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex gap-4 items-center">
         <div className="text-sm font-semibold text-gray-700 flex items-center gap-2">
            <Search size={16}/> Filtrer par statut
         </div>
         <select 
            value={filterStatut}
            onChange={(e) => setFilterStatut(e.target.value)}
            className="text-sm border-gray-200 rounded-lg focus:ring-blue-500 focus:border-blue-500"
         >
            <option value="">Tous les statuts</option>
            <option value="NON_COMMENCEE">Non commencée</option>
            <option value="EN_COURS">En cours</option>
            <option value="NOTES_IMPORTEES">Notes importées</option>
            <option value="RESULTATS_PUBLIES">Résultats publiés</option>
         </select>
      </div>

      {loading ? (
        <div className="flex justify-center p-12"><div className="spinner"></div></div>
      ) : epreuves.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-100 p-12 text-center">
           <GraduationCap className="mx-auto h-12 w-12 text-gray-300 mb-3" />
           <h3 className="text-lg font-medium text-gray-900">Aucune épreuve trouvée</h3>
           <p className="mt-1 text-gray-500 text-sm">Créez une nouvelle épreuve pour commencer la gestion des résultats.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {epreuves.map((ep) => (
            <div key={ep.id} className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow overflow-hidden flex flex-col">
              <div className="p-5 border-b border-gray-100">
                <div className="flex justify-between items-start mb-3">
                  <StatutBadge statut={ep.statut} />
                  <span className="text-xs font-bold text-gray-400 bg-gray-50 px-2 py-1 rounded">{ep.filiere_code}</span>
                </div>
                <h3 className="text-lg font-bold text-gray-900 leading-tight mb-1">{ep.nom}</h3>
                <p className="text-sm text-gray-500">{ep.filiere_nom}</p>
              </div>
              
              <div className="p-5 bg-gray-50/50 flex-1 space-y-3">
                <div className="flex items-center gap-3 text-sm text-gray-600">
                  <Calendar size={16} className="text-blue-500" />
                  <span>Écrit : <span className="font-semibold text-gray-900">{ep.date_ecrit ? new Date(ep.date_ecrit).toLocaleString('fr-FR') : 'Non définie'}</span></span>
                </div>
                <div className="flex items-center gap-3 text-sm text-gray-600">
                  <Calendar size={16} className="text-purple-500" />
                  <span>Oral : <span className="font-semibold text-gray-900">{ep.date_oral ? new Date(ep.date_oral).toLocaleString('fr-FR') : 'Non définie'}</span></span>
                </div>
                <div className="flex items-center gap-3 text-sm text-gray-600">
                  <Settings2 size={16} className="text-gray-400" />
                  Seuil actuel: <span className="font-bold text-gray-900">{parseFloat(ep.seuil_admission).toFixed(2)} / {parseFloat(ep.note_sur)}</span>
                </div>
                {(ep.nb_admis > 0 || ep.nb_recales > 0) && (
                   <div className="flex items-center gap-3 text-sm text-gray-600">
                     <Users size={16} className="text-gray-400" />
                     <span className="font-medium text-green-600">{ep.nb_admis} Admis</span>
                     <span className="text-gray-300">•</span>
                     <span className="font-medium text-red-600">{ep.nb_recales} Recalés</span>
                   </div>
                )}
              </div>

              <div className="p-4 border-t border-gray-100 bg-white grid grid-cols-2 gap-2">
                 <Link to={`/admin/epreuves/${ep.id}/resultats`} className="flex items-center justify-center py-2 text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-lg transition-colors">
                    Liste complète
                 </Link>
                 <Link to={`/admin/epreuves/${ep.id}`} className="flex items-center justify-center py-2 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded-lg transition-colors gap-1">
                    Gérer <ArrowRight size={16} />
                 </Link>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <CreateEpreuveModal 
           filieres={filieres} 
           onClose={() => setShowCreateModal(false)} 
           onSuccess={(newEp) => {
              setShowCreateModal(false);
              fetchData();
              navigate(`/admin/epreuves/${newEp.id}`);
           }}
        />
      )}
    </div>
  );
}

function CreateEpreuveModal({ filieres, onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    nom: '',
    filiere: '',
    note_sur: 20,
    coefficient: 1,
    seuil_admission: 10
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const data = await createEpreuve(formData);
      toast.success('Épreuve créée');
      onSuccess(data);
    } catch (err) {
      toast.error('Erreur de création');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-gray-900/50 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden">
        <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
          <h2 className="text-xl font-bold text-gray-900">Nouvelle épreuve</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">×</button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Filière</label>
            <select required value={formData.filiere} onChange={e => setFormData({...formData, filiere: e.target.value})} className="w-full rounded-lg border-gray-300">
              <option value="">Sélectionner une filière</option>
              {filieres.map(f => <option key={f.id} value={f.id}>{f.nom}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Nom de l'épreuve</label>
            <input required type="text" placeholder="Ex: Épreuve Écrite 2025" value={formData.nom} onChange={e => setFormData({...formData, nom: e.target.value})} className="w-full rounded-lg border-gray-300" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
               <label className="block text-sm font-semibold text-gray-700 mb-1">Notée sur</label>
               <input type="number" required min="1" value={formData.note_sur} onChange={e => setFormData({...formData, note_sur: e.target.value})} className="w-full rounded-lg border-gray-300" />
            </div>
            <div>
               <label className="block text-sm font-semibold text-gray-700 mb-1">Coefficient</label>
               <input type="number" required step="0.01" min="0" value={formData.coefficient} onChange={e => setFormData({...formData, coefficient: e.target.value})} className="w-full rounded-lg border-gray-300" />
            </div>
          </div>
          
          <div className="pt-4 flex justify-end gap-3 border-t border-gray-100">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">Annuler</button>
            <button type="submit" disabled={loading} className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 flex items-center gap-2">
              {loading && <span className="animate-spin leading-none">⟳</span>} Créer
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
