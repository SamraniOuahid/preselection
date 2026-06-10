// src/pages/admin/EpreuveOralePage.jsx
import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Link } from 'react-router-dom';
import { getEpreuvesOral, createEpreuveOral } from '../../api/oral';
import API from '../../api/axios';
import { Plus, Calendar, MapPin, Mic2, Upload } from 'lucide-react';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ImportAdmisOralModal from '../../components/admin/ImportAdmisOralModal';
import toast from 'react-hot-toast';

export default function EpreuveOralePage() {
  const [epreuves, setEpreuves] = useState([]);
  const [filieres, setFilieres] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [newEpreuve, setNewEpreuve] = useState({ filiere: '', nom: '', date_oral: '', heure_debut: '', lieu: '', duree_minutes: 20 });
  const [autoFilled, setAutoFilled] = useState({ date: false, lieu: false });
  const [submitting, setSubmitting] = useState(false);
  // Import modal
  const [importTarget, setImportTarget] = useState(null); // epreuve object

  useEffect(() => {
    fetchData();
    API.get('/filieres/').then(r => setFilieres(r.data.results || r.data)).catch(() => {});
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const data = await getEpreuvesOral();
      setEpreuves(data.results || data);
    } catch (error) {
      toast.error('Erreur de chargement des épreuves');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await createEpreuveOral(newEpreuve);
      toast.success('Épreuve orale créée');
      setShowModal(false);
      fetchData();
    } catch (err) {
      toast.error('Erreur lors de la création');
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (statut) => {
    switch(statut) {
      case 'PLANIFIEE': return <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full font-medium">Planifiée</span>;
      case 'EN_COURS': return <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full font-medium">En cours</span>;
      case 'TERMINEE': return <span className="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded-full font-medium">Terminée</span>;
      case 'RESULTATS_PUBLIES': return <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full font-medium">Résultats publiés</span>;
      default: return null;
    }
  };

  return (
    <div className="ensa-page animate-fade-in">
      <div className="ensa-page-header">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="ensa-page-title flex items-center gap-2">
              <Mic2 className="text-primary-600" /> Gestion des Épreuves Orales
            </h1>
            <p className="ensa-page-subtitle">Planification et gestion des entretiens d'admission</p>
          </div>
          <button onClick={() => setShowModal(true)} className="btn btn-primary">
            <Plus size={16} /> Planifier un oral
          </button>
        </div>
      </div>

      <div className="card">
        {loading ? (
          <LoadingSpinner size="lg" text="Chargement..." className="py-20" />
        ) : (
          <div className="ensa-table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Filière</th>
                  <th>Nom de l'épreuve</th>
                  <th>Date & Lieu</th>
                  <th className="text-center">Convoqués</th>
                  <th className="text-center">Acceptés/Refusés</th>
                  <th>Statut</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {epreuves.length > 0 ? epreuves.map((ep) => (
                  <tr key={ep.id}>
                    <td className="font-bold text-primary-700">{ep.filiere_code}</td>
                    <td className="font-medium text-gray-800">{ep.nom}</td>
                    <td>
                      <div className="flex flex-col gap-1 text-sm text-gray-600">
                        <div className="flex items-center gap-1"><Calendar size={14} /> {ep.date_oral || 'Non définie'}</div>
                        <div className="flex items-center gap-1"><MapPin size={14} /> {ep.lieu || 'Non défini'}</div>
                      </div>
                    </td>
                    <td className="text-center font-semibold text-gray-700">{ep.nb_convoques}</td>
                    <td className="text-center">
                      <span className="text-green-600 font-bold">{ep.nb_acceptes}</span> / <span className="text-red-600 font-bold">{ep.nb_refuses}</span>
                    </td>
                    <td>{getStatusBadge(ep.statut)}</td>
                    <td>
                      <div className="flex items-center gap-2">
                        <Link to={`/admin/epreuves-oral/${ep.id}`} className="text-blue-600 hover:underline font-semibold text-sm">
                          Gérer →
                        </Link>
                        <button
                          onClick={() => setImportTarget(ep)}
                          title="Importer admis à l'oral"
                          className="inline-flex items-center gap-1 px-2 py-1 text-xs font-semibold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 rounded-lg transition-colors"
                        >
                          <Upload size={12} /> Import
                        </button>
                      </div>
                    </td>
                  </tr>
                )) : (
                  <tr><td colSpan="7" className="text-center py-8 text-gray-500">Aucune épreuve orale trouvée.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showModal && createPortal(
        <div
          className="fixed inset-0 z-[9999] flex items-center justify-center p-4"
          style={{ backgroundColor: 'rgba(0,0,0,0.55)' }}
          onClick={(e) => { if (e.target === e.currentTarget) setShowModal(false); }}
        >
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md p-6 overflow-y-auto" style={{ maxHeight: '90vh' }}>
            <h3 className="text-lg font-bold mb-4">Planifier une épreuve orale</h3>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="label">Filière</label>
                <select
                  className="input"
                  value={newEpreuve.filiere}
                  onChange={e => {
                    const selectedId = e.target.value;
                    const selectedFiliere = filieres.find(f => f.id === selectedId);
                    const updates = { filiere: selectedId };
                    const filled = { date: false, lieu: false };

                    if (selectedFiliere?.date_oral) {
                      const d = new Date(selectedFiliere.date_oral);
                      // Format date as YYYY-MM-DD for input[type=date]
                      updates.date_oral = d.toISOString().slice(0, 10);
                      // Format time as HH:MM for input[type=time]
                      updates.heure_debut = d.toTimeString().slice(0, 5);
                      filled.date = true;
                    }
                    if (selectedFiliere?.lieu_oral) {
                      updates.lieu = selectedFiliere.lieu_oral;
                      filled.lieu = true;
                    } else {
                      updates.lieu = 'Salle des conférences — ENSA BM';
                    }

                    setNewEpreuve(prev => ({ ...prev, ...updates }));
                    setAutoFilled(filled);
                  }}
                  required
                >
                  <option value="">Sélectionner une filière</option>
                  {filieres.map(f => <option key={f.id} value={f.id}>{f.nom} ({f.code})</option>)}
                </select>
              </div>
              <div>
                <label className="label">Nom de l'épreuve</label>
                <input type="text" className="input" value={newEpreuve.nom} onChange={e => setNewEpreuve({...newEpreuve, nom: e.target.value})} placeholder="Ex: Entretien oral - TDI Bac+2 - 2025" required />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="label mb-0">Date de l'oral</label>
                    {autoFilled.date && (
                      <span className="text-[10px] font-semibold px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded">
                        ✦ Filière
                      </span>
                    )}
                  </div>
                  <input
                    type="date"
                    className={`input ${autoFilled.date ? 'border-blue-300 bg-blue-50/40' : ''}`}
                    value={newEpreuve.date_oral}
                    onChange={e => { setNewEpreuve({...newEpreuve, date_oral: e.target.value}); setAutoFilled(p => ({...p, date: false})); }}
                    required
                  />
                </div>
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="label mb-0">Heure de début</label>
                    {autoFilled.date && (
                      <span className="text-[10px] font-semibold px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded">
                        ✦ Filière
                      </span>
                    )}
                  </div>
                  <input
                    type="time"
                    className={`input ${autoFilled.date ? 'border-blue-300 bg-blue-50/40' : ''}`}
                    value={newEpreuve.heure_debut}
                    onChange={e => { setNewEpreuve({...newEpreuve, heure_debut: e.target.value}); setAutoFilled(p => ({...p, date: false})); }}
                    required
                  />
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="label mb-0">Lieu</label>
                  {autoFilled.lieu && (
                    <span className="text-[10px] font-semibold px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded">
                      ✦ Filière
                    </span>
                  )}
                </div>
                <input
                  type="text"
                  className={`input ${autoFilled.lieu ? 'border-blue-300 bg-blue-50/40' : ''}`}
                  value={newEpreuve.lieu}
                  placeholder="Ex: Salle des conférences — ENSA BM"
                  onChange={e => { setNewEpreuve({...newEpreuve, lieu: e.target.value}); setAutoFilled(p => ({...p, lieu: false})); }}
                  required
                />
              </div>
              <div>
                <label className="label">Durée par candidat (min)</label>
                <input type="number" className="input" value={newEpreuve.duree_minutes} onChange={e => setNewEpreuve({...newEpreuve, duree_minutes: e.target.value})} min="5" max="60" required />
              </div>
              <div className="flex justify-end gap-2 mt-6">
                <button type="button" onClick={() => setShowModal(false)} className="btn btn-outline">Annuler</button>
                <button type="submit" disabled={submitting} className="btn btn-primary">{submitting ? 'Création...' : 'Créer'}</button>
              </div>
            </form>
          </div>
        </div>,
        document.body
      )}
      <ImportAdmisOralModal
        epreuve={importTarget}
        isOpen={!!importTarget}
        onClose={() => setImportTarget(null)}
        onImportDone={fetchData}
      />

    </div>
  );
}
