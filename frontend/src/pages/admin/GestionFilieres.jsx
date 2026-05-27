// src/pages/admin/GestionFilieres.jsx
// Gestion des filières — style officiel ENSA BM
import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import API from '../../api/axios';
import EmptyState from '../../components/common/EmptyState';
import { 
  Plus, Edit2, Lock, Unlock, GraduationCap, Users, 
  FolderOpen, Settings, AlertTriangle, FileText, CheckCircle
} from 'lucide-react';

export default function GestionFilieres() {
  const [filieres, setFilieres] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);

  const { register, handleSubmit, reset, setValue, formState: { errors } } = useForm();

  const fetchFilieres = () => {
    setLoading(true);
    API.get('/filieres/')
      .then(({ data }) => setFilieres(data.results || data))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchFilieres(); }, []);

  const onSubmit = async (data) => {
    try {
      const diplomes_acceptes = data.diplomes_str
        ? data.diplomes_str.split(',').map(s => s.trim()).filter(Boolean).map(name => ({ nom_diplome: name, is_active: true }))
        : [];

      const payload = {
        nom: data.nom,
        code: data.code,
        niveau: data.niveau,
        description: data.description,
        places_disponibles: parseInt(data.places_disponibles),
        diplomes_acceptes,
      };

      if (editing) {
        await API.put(`/filieres/${editing}/`, payload);
      } else {
        await API.post('/filieres/', payload);
      }
      reset();
      setShowForm(false);
      setEditing(null);
      fetchFilieres();
    } catch (err) {
      alert('Erreur: ' + JSON.stringify(err.response?.data || 'Erreur inconnue'));
    }
  };

  const startEdit = (f) => {
    setEditing(f.id);
    setShowForm(true);
    setValue('nom', f.nom);
    setValue('code', f.code);
    setValue('niveau', f.niveau);
    setValue('description', f.description);
    setValue('places_disponibles', f.places_disponibles);
    
    const diplomesStr = f.diplomes_acceptes?.map(da => da.nom_diplome).join(', ') || '';
    setValue('diplomes_str', diplomesStr);
  };

  const toggleStatus = async (id) => {
    try {
      await API.post(`/filieres/${id}/toggle_status/`);
      fetchFilieres();
    } catch (err) {
      alert("Erreur lors de la modification de l'état.");
    }
  };

  const handleAddDiploma = async (filiereId, nomDiplome) => {
    try {
      await API.post(`/filieres/${filiereId}/ajouter_diplome/`, {
        nom_diplome: nomDiplome,
        is_active: true
      });
      fetchFilieres();
    } catch (err) {
      alert("Erreur lors de l'ajout du diplôme.");
    }
  };

  const handleRemoveDiploma = async (filiereId, diplomeId) => {
    if (!confirm("Retirer ce diplôme de la liste des diplômes admis ?")) return;
    try {
      await API.post(`/filieres/${filiereId}/retirer_diplome/`, {
        diplome_id: diplomeId
      });
      fetchFilieres();
    } catch (err) {
      alert("Erreur lors du retrait du diplôme.");
    }
  };

  const cancelForm = () => {
    setShowForm(false);
    setEditing(null);
    reset();
  };

  return (
    <div className="ensa-page ensa-page-narrow animate-fade-in">
      {/* Page Header */}
      <div className="ensa-page-header">
        <div className="ensa-page-header-row">
          <div>
            <h1 className="ensa-page-title">Gestion des Filières</h1>
            <p className="ensa-page-subtitle">
              {filieres.length} filière{filieres.length !== 1 ? 's' : ''} configurée{filieres.length !== 1 ? 's' : ''} pour la présélection
            </p>
          </div>
          <button className="btn btn-primary" onClick={() => { cancelForm(); setShowForm(true); }}>
            <Plus size={16} /> 
            <span>Nouvelle Filière</span>
          </button>
        </div>
      </div>

      {/* Formulaire ajout/édition */}
      {showForm && (
        <div className="ensa-form-section animate-fade-in mb-6">
          <h3 className="ensa-form-section-title border-b border-border pb-3 mb-4">
            {editing ? (
              <>
                <Edit2 size={18} className="text-primary-500" /> 
                <span>Modifier la filière</span>
              </>
            ) : (
              <>
                <Plus size={18} className="text-primary-500" /> 
                <span>Nouvelle filière d'études</span>
              </>
            )}
          </h3>
          <form onSubmit={handleSubmit(onSubmit)} className="ensa-form-grid">
            <div>
              <label className="label" htmlFor="filiere-nom">Nom complet de la filière</label>
              <input 
                id="filiere-nom"
                className={`input ${errors.nom ? 'input-error' : ''}`} 
                placeholder="Ex: Génie Informatique" 
                {...register('nom', { required: 'Obligatoire' })} 
              />
              {errors.nom && <p className="error-text">{errors.nom.message}</p>}
            </div>
            
            <div>
              <label className="label" htmlFor="filiere-code">Code de la filière</label>
              <input 
                id="filiere-code"
                className={`input font-mono ${errors.code ? 'input-error' : ''}`} 
                placeholder="Ex: GI" 
                {...register('code', { required: 'Obligatoire' })} 
              />
              {errors.code && <p className="error-text">{errors.code.message}</p>}
            </div>
            
            <div>
              <label className="label" htmlFor="filiere-niveau">Niveau d'accès requis</label>
              <select 
                id="filiere-niveau"
                className="input" 
                {...register('niveau', { required: 'Obligatoire' })}
              >
                <option value="">— Choisir le niveau —</option>
                <option value="BAC2">Bac+2 (DUT, BTS, DEUG...)</option>
                <option value="BAC3">Bac+3 (Licence...)</option>
              </select>
            </div>
            
            <div>
              <label className="label" htmlFor="filiere-places">Nombre de places disponibles</label>
              <input 
                id="filiere-places"
                type="number" 
                className="input font-mono" 
                placeholder="Ex: 30" 
                {...register('places_disponibles', { required: 'Obligatoire', min: 1 })} 
              />
            </div>
            <div className="sm:col-span-2">
              <label className="label" htmlFor="filiere-diplomes">Diplômes admis (séparés par des virgules)</label>
              <input 
                id="filiere-diplomes"
                className="input" 
                placeholder="Ex: DUT Informatique, DUT Réseaux et Télécommunications, BTS Informatique" 
                {...register('diplomes_str')} 
              />
              <p className="text-[11px] text-text-muted mt-1">Saisissez les intitulés exacts ou simplifiés des diplômes éligibles à cette filière.</p>
            </div>

            <div className="sm:col-span-2">
              <label className="label" htmlFor="filiere-desc">Description et prérequis</label>
              <textarea 
                id="filiere-desc"
                className="input" 
                rows={3} 
                placeholder="Description succincte de la filière..." 
                {...register('description')} 
              />
            </div>
            
            <div className="sm:col-span-2 flex gap-3 justify-end mt-4">
              <button type="button" className="btn btn-outline" onClick={cancelForm}>
                Annuler
              </button>
              <button type="submit" className="btn btn-primary">
                {editing ? 'Enregistrer les modifications' : 'Créer la filière'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Liste des filières */}
      {loading ? (
        <div className="space-y-4">
          <div className="skeleton h-24 w-full rounded-xl" />
          <div className="skeleton h-24 w-full rounded-xl" />
          <div className="skeleton h-24 w-full rounded-xl" />
        </div>
      ) : filieres.length === 0 ? (
        <EmptyState
          title="Aucune filière configurée"
          description="Créez votre première filière d'études pour ouvrir les candidatures aux concours d'accès."
          icon={GraduationCap}
          action={() => setShowForm(true)}
          actionLabel="Créer une filière"
        />
      ) : (
        <div className="stagger grid gap-4">
          {filieres.map((f) => (
            <div key={f.id} className="ensa-dossier-card">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div className="flex-1">
                  <div className="flex flex-wrap items-center gap-3 mb-2.5">
                    <h3 className="text-sm font-bold text-text-primary">{f.nom}</h3>
                    <span className="font-mono text-xs px-2.5 py-0.5 rounded bg-primary-50 text-primary-500 font-semibold">
                      {f.code}
                    </span>
                    <span className={`badge ${f.is_active ? 'badge-preselectionne' : 'badge-rejete_auto'} text-[10px]`}>
                      {f.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-text-secondary">
                    <span className="flex items-center gap-1">
                      <GraduationCap size={13} className="text-text-muted" />
                      <span>{f.niveau === 'BAC2' ? 'Bac+2' : 'Bac+3'}</span>
                    </span>
                    <span className="flex items-center gap-1">
                      <Users size={13} className="text-text-muted" />
                      <span>{f.places_disponibles} places</span>
                    </span>
                    <span className="flex items-center gap-1">
                      <FolderOpen size={13} className="text-text-muted" />
                      <span className="font-mono">{f.candidatures_count}</span> candidature{f.candidatures_count !== 1 ? 's' : ''}
                    </span>
                  </div>
                  
                  {/* Diplômes acceptés */}
                  <div className="mt-4 pt-3 border-t border-gray-100">
                    <div className="text-[11px] font-bold text-[#1B3A6B] mb-2 uppercase tracking-wide flex items-center gap-1.5">
                      <GraduationCap size={13} />
                      Diplômes admis ({f.diplomes_acceptes?.length || 0}) :
                    </div>
                    <div className="flex flex-wrap gap-2 items-center">
                      {f.diplomes_acceptes?.map((da) => (
                        <span key={da.id} className="inline-flex items-center gap-1 text-[11px] font-semibold bg-blue-50 text-[#1B3A6B] px-2.5 py-1 rounded-full border border-blue-100">
                          {da.nom_diplome}
                          <button
                            type="button"
                            onClick={() => handleRemoveDiploma(f.id, da.id)}
                            className="w-3.5 h-3.5 rounded-full hover:bg-blue-100 flex items-center justify-center text-[#1B3A6B] font-bold text-[10px] ml-1 transition-colors"
                          >
                            ×
                          </button>
                        </span>
                      ))}
                      
                      {/* Formulaire rapide pour ajouter un diplôme */}
                      <form
                        onSubmit={(e) => {
                          e.preventDefault();
                          const val = e.target.diplome.value.trim();
                          if (val) {
                            handleAddDiploma(f.id, val);
                            e.target.reset();
                          }
                        }}
                        className="flex items-center gap-1.5 ml-2"
                      >
                        <input
                          name="diplome"
                          type="text"
                          placeholder="Ajouter un diplôme..."
                          className="input px-2.5 py-1 text-xs w-48 h-[28px] min-h-[28px] bg-gray-50 border-gray-200"
                        />
                        <button type="submit" className="btn btn-primary px-3 h-[28px] min-h-[28px] text-[11px] flex items-center justify-center">
                          Ajouter
                        </button>
                      </form>
                    </div>
                  </div>
                </div>
                
                {/* Actions */}
                <div className="flex gap-2 self-end sm:self-center">
                  <button 
                    className="btn btn-ghost btn-sm text-primary-600 hover:bg-primary-50 rounded-lg p-2" 
                    onClick={() => startEdit(f)} 
                    title="Modifier la filière"
                  >
                    <Edit2 size={16} />
                  </button>
                  <button 
                    className={`btn btn-sm ${f.is_active ? 'btn-outline-danger' : 'btn-outline'} h-[36px] px-3.5`}
                    onClick={() => toggleStatus(f.id)} 
                    title={f.is_active ? 'Désactiver la filière' : 'Activer la filière'}
                  >
                    {f.is_active ? <Lock size={14} /> : <Unlock size={14} />}
                    <span>{f.is_active ? 'Désactiver' : 'Activer'}</span>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
