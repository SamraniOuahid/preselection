// src/pages/admin/ResultatsEpreuvePage.jsx
import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getEpreuveDetail, updateNoteEcrite, exportResultats } from '../../api/epreuves';
import { ArrowLeft, Search, Download, Edit2, Check, X } from 'lucide-react';
import DataTable from '../../components/common/DataTable';
import toast from 'react-hot-toast';

export default function ResultatsEpreuvePage() {
  const { id } = useParams();
  const [epreuve, setEpreuve] = useState(null);
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('ALL');
  const [search, setSearch] = useState('');
  
  const [editingNoteId, setEditingNoteId] = useState(null);
  const [editValue, setEditValue] = useState('');

  useEffect(() => {
    fetchData();
  }, [id]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const epData = await getEpreuveDetail(id);
      setEpreuve(epData);
      setNotes(epData.notes || []);
    } catch (error) {
      toast.error('Erreur lors du chargement des résultats');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveNote = async (noteId) => {
    try {
       const val = editValue === '' ? null : parseFloat(editValue);
       await updateNoteEcrite(noteId, val);
       toast.success('Note modifiée');
       setEditingNoteId(null);
       fetchData(); // reload pour avoir le classement à jour
    } catch (e) {
       toast.error('Erreur lors de la modification');
    }
  };

  if (loading) return <div className="flex justify-center p-12"><div className="spinner"></div></div>;
  if (!epreuve) return <div>Épreuve non trouvée.</div>;

  const filteredNotes = notes.filter(n => {
    if (filter !== 'ALL' && n.resultat !== filter) return false;
    if (search) {
       const term = search.toLowerCase();
       const info = n.dossier_info;
       return info.candidat_nom.toLowerCase().includes(term) ||
              info.candidat_prenom.toLowerCase().includes(term) ||
              info.candidat_cin.toLowerCase().includes(term);
    }
    return true;
  });

  const ResultBadge = ({ res }) => {
     if (res === 'ADMIS') return <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs font-bold">ADMIS</span>;
     if (res === 'RECALE') return <span className="bg-red-100 text-red-800 px-2 py-1 rounded text-xs font-bold">RECALÉ</span>;
     if (res === 'ABSENT') return <span className="bg-gray-200 text-gray-700 px-2 py-1 rounded text-xs font-bold">ABSENT</span>;
     return <span>{res}</span>;
  };

  const columns = [
    { key: 'rang_final', label: 'Rang', render: (val) => val ? <span className="font-bold text-gray-500">#{val}</span> : '-' },
    { key: 'cin', label: 'CIN', render: (_, n) => <span className="font-mono text-gray-600">{n.dossier_info.candidat_cin}</span> },
    { key: 'nom', label: 'Candidat', render: (_, n) => <div className="font-medium text-gray-900">{n.dossier_info.candidat_nom} {n.dossier_info.candidat_prenom}</div> },
    { key: 'score_dossier', label: 'Score Dossier', render: (_, n) => <span className="text-gray-500">{n.dossier_info.score_dossier}</span> },
    { key: 'note', label: 'Note Écrite', render: (val, n) => {
       if (editingNoteId === n.id) {
          return (
             <div className="flex items-center gap-1">
                <input 
                   type="number" min="0" max={epreuve.note_sur} step="0.25"
                   className="w-20 p-1 text-sm border rounded"
                   value={editValue}
                   onChange={e => setEditValue(e.target.value)}
                   autoFocus
                />
                <button onClick={() => handleSaveNote(n.id)} className="p-1 text-green-600 hover:bg-green-50 rounded"><Check size={16}/></button>
                <button onClick={() => setEditingNoteId(null)} className="p-1 text-red-600 hover:bg-red-50 rounded"><X size={16}/></button>
             </div>
          );
       }
       return (
          <div className="flex items-center justify-between group">
             <span className="font-bold text-gray-900">{val !== null ? val : '-'}</span>
             {epreuve.statut !== 'RESULTATS_PUBLIES' && (
                <button 
                   onClick={() => { setEditingNoteId(n.id); setEditValue(val === null ? '' : val); }}
                   className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-blue-600 transition-opacity"
                >
                   <Edit2 size={14}/>
                </button>
             )}
          </div>
       );
    }},
    { key: 'resultat', label: 'Résultat', render: (val) => <ResultBadge res={val}/> },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <Link to={`/admin/epreuves/${id}`} className="text-gray-500 hover:text-blue-600 flex items-center gap-1 text-sm font-medium mb-3 transition-colors w-max">
            <ArrowLeft size={16} /> Retour aux détails
          </Link>
          <h1 className="text-2xl font-black text-gray-900">Résultats Détaillés</h1>
          <p className="text-gray-500 text-sm mt-1">{epreuve.nom}</p>
        </div>
        <button onClick={() => exportResultats(id)} className="bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded-xl text-sm font-semibold hover:bg-gray-50 transition-colors flex items-center gap-2">
           <Download size={16}/> Export Excel
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden flex flex-col h-[600px]">
         <div className="p-4 border-b border-gray-100 flex flex-col sm:flex-row justify-between items-center gap-4 bg-gray-50/50">
            <div className="flex bg-gray-200/50 p-1 rounded-lg">
               {['ALL', 'ADMIS', 'RECALE', 'ABSENT'].map(f => (
                  <button 
                     key={f}
                     onClick={() => setFilter(f)}
                     className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${filter === f ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                  >
                     {f === 'ALL' ? 'Tous' : f === 'RECALE' ? 'Recalés' : f.charAt(0) + f.slice(1).toLowerCase()}
                  </button>
               ))}
            </div>
            
            <div className="relative w-full sm:w-64">
               <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
               <input 
                  type="text" 
                  placeholder="Rechercher nom, CIN..." 
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 bg-white border-gray-200 rounded-lg text-sm focus:ring-blue-500 focus:border-blue-500"
               />
            </div>
         </div>

         <div className="flex-1 overflow-auto">
            <DataTable 
               columns={columns} 
               data={filteredNotes} 
               keyField="id" 
               emptyMessage="Aucun résultat trouvé."
            />
         </div>
      </div>
    </div>
  );
}
