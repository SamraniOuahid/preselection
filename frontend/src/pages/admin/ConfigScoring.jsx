// src/pages/admin/ConfigScoring.jsx
// Configuration du scoring et des règles de rejet — Style ENSA BM
import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import API from '../../api/axios';
import EmptyState from '../../components/common/EmptyState';
import AlertBanner from '../../components/common/AlertBanner';
import {
  Scale, ShieldAlert, Plus, Trash2, Play, Pause,
  GraduationCap, Settings, AlertTriangle, CheckCircle2
} from 'lucide-react';

export default function ConfigScoring() {
  const [filieres, setFilieres] = useState([]);
  const [selectedFiliere, setSelectedFiliere] = useState('');
  const [configs, setConfigs] = useState([]);
  const [regles, setRegles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState('scoring'); // scoring | regles

  const { register, handleSubmit, reset } = useForm();
  const { register: regRegles, handleSubmit: handleSubmitRegles, reset: resetRegles } = useForm();

  useEffect(() => {
    API.get('/filieres/')
      .then(({ data }) => setFilieres(data.results || data))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!selectedFiliere) return;
    setLoading(true);
    Promise.all([
      API.get(`/scoring/config/?filiere=${selectedFiliere}`),
      API.get(`/scoring/regles/?filiere=${selectedFiliere}`),
    ])
      .then(([configRes, reglesRes]) => {
        setConfigs(configRes.data.results || configRes.data);
        setRegles(reglesRes.data.results || reglesRes.data);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [selectedFiliere]);

  const addConfig = async (data) => {
    try {
      await API.post('/scoring/config/', {
        filiere: selectedFiliere,
        matiere: data.matiere,
        poids: parseFloat(data.poids),
        bonus_mention: { TB: 2.0, B: 1.0, AB: 0.5, P: 0.0 },
      });
      reset();
      // Refresh
      const { data: updated } = await API.get(`/scoring/config/?filiere=${selectedFiliere}`);
      setConfigs(updated.results || updated);
    } catch (err) {
      alert('Erreur: ' + JSON.stringify(err.response?.data || err.message));
    }
  };

  const deleteConfig = async (id) => {
    if (!confirm('Supprimer cette configuration ?')) return;
    try {
      await API.delete(`/scoring/config/${id}/`);
      setConfigs(configs.filter((c) => c.id !== id));
    } catch (err) {
      alert('Erreur lors de la suppression.');
    }
  };

  const addRegle = async (data) => {
    try {
      let parametre = {};
      if (data.type_regle === 'MOYENNE_INSUFFISANTE') {
        parametre = { seuil: parseFloat(data.seuil || 10) };
      } else if (data.type_regle === 'NOTE_ELIMINATOIRE') {
        parametre = { matiere: data.param_matiere || '', seuil: parseFloat(data.seuil || 5) };
      }
      await API.post('/scoring/regles/', {
        filiere: selectedFiliere,
        type_regle: data.type_regle,
        message_rejet: data.message_rejet,
        parametre,
      });
      resetRegles();
      const { data: updated } = await API.get(`/scoring/regles/?filiere=${selectedFiliere}`);
      setRegles(updated.results || updated);
    } catch (err) {
      alert('Erreur: ' + JSON.stringify(err.response?.data || err.message));
    }
  };

  const toggleRegle = async (id) => {
    try {
      await API.post(`/scoring/regles/${id}/toggle/`);
      const { data: updated } = await API.get(`/scoring/regles/?filiere=${selectedFiliere}`);
      setRegles(updated.results || updated);
    } catch (err) {
      alert("Erreur lors de la modification de l'état.");
    }
  };

  const totalPoids = configs.reduce((sum, c) => sum + parseFloat(c.poids || 0), 0);

  return (
    <div className="ensa-page ensa-page-narrow animate-fade-in">
      {/* Page Header */}
      <div className="ensa-page-header">
        <div className="ensa-page-header-row">
          <div>
            <h1 className="ensa-page-title">Configuration Scoring & Règles</h1>
            <p className="ensa-page-subtitle">Paramétrez les coefficients de calcul et les critères de rejet par filière</p>
          </div>
        </div>
      </div>

      {/* Sélection filière */}
      <div className="ensa-card mb-6">
        <div className="ensa-card-body">
          <label className="label" htmlFor="select-filiere">Filière d'études</label>
          <div className="relative max-w-md">
            <select
              id="select-filiere"
              className="input pr-10"
              value={selectedFiliere}
              onChange={(e) => setSelectedFiliere(e.target.value)}
            >
              <option value="">— Sélectionner une filière —</option>
              {filieres.map((f) => (
                <option key={f.id} value={f.id}>{f.nom} ({f.code})</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* État vide si aucune filière n'est sélectionnée */}
      {!selectedFiliere && (
        <EmptyState
          title="Aucune filière sélectionnée"
          description="Sélectionnez une filière ci-dessus pour configurer ses coefficients de matières et ses critères d'évaluation."
          icon={GraduationCap}
        />
      )}

      {/* Contenu principal de la configuration */}
      {selectedFiliere && !loading && (
        <>
          {/* Tabs */}
          <div className="ensa-tabs mb-6">
            {[
              { key: 'scoring', label: 'Coefficients', icon: Scale, count: configs.length },
              { key: 'regles', label: 'Règles de rejet', icon: ShieldAlert, count: regles.length },
            ].map((t) => {
              const TabIcon = t.icon;
              return (
                <button
                  key={t.key}
                  className={`ensa-tab ${tab === t.key ? 'is-active' : ''}`}
                  onClick={() => setTab(t.key)}
                >
                  <TabIcon size={16} />
                  <span>{t.label}</span>
                  <span className="font-mono text-xs px-2 py-0.5 rounded bg-surface text-text-secondary ml-1">
                    {t.count}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Tab Content: Scoring / Coefficients */}
          {tab === 'scoring' && (
            <div className="space-y-6">
              {/* Alert indicator pour le total des coefficients */}
              <AlertBanner
                variant={totalPoids === 100 ? 'success' : 'warning'}
                className="mb-4"
              >
                Total des poids configurés : <span className="font-mono font-bold">{totalPoids}%</span>. 
                {totalPoids !== 100 
                  ? ' Attention, le total des coefficients doit être exactement égal à 100% pour que le scoring soit actif.' 
                  : ' La somme des coefficients est correcte (100%).'
                }
              </AlertBanner>

              {/* List of existing configurations */}
              {configs.length > 0 ? (
                <div className="ensa-config-list">
                  {configs.map((c) => (
                    <div key={c.id} className="ensa-config-item">
                      <div className="ensa-config-item-info">
                        <Scale size={16} className="text-primary-500" />
                        <span className="ensa-config-item-name">{c.matiere}</span>
                        <span className="ensa-config-item-detail font-mono bg-primary-50 text-primary-700 px-2.5 py-0.5 rounded text-xs font-semibold">
                          Poids : {c.poids}%
                        </span>
                      </div>
                      <button 
                        className="btn btn-ghost btn-sm text-danger-500 hover:text-danger-700 hover:bg-danger-50 rounded-lg p-1.5"
                        onClick={() => deleteConfig(c.id)}
                        title="Supprimer cette matière"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState
                  title="Aucune matière configurée"
                  description="Ajoutez des matières et des coefficients ci-dessous pour lancer le scoring automatique."
                  icon={Scale}
                />
              )}

              {/* Add coefficient form */}
              <form onSubmit={handleSubmit(addConfig)} className="ensa-card p-5">
                <div className="flex flex-col sm:flex-row gap-4 items-end">
                  <div className="flex-1 w-full">
                    <label className="label" htmlFor="coeff-matiere">Matière / Module</label>
                    <input 
                      id="coeff-matiere"
                      className="input" 
                      placeholder="Ex: Mathématiques, Informatique, Langues..." 
                      {...register('matiere', { required: true })} 
                    />
                  </div>
                  <div className="w-full sm:w-32">
                    <label className="label" htmlFor="coeff-poids">Coefficient (%)</label>
                    <input 
                      id="coeff-poids"
                      type="number" 
                      className="input font-mono" 
                      placeholder="Ex: 30" 
                      {...register('poids', { required: true, min: 1, max: 100 })} 
                    />
                  </div>
                  <button type="submit" className="btn btn-primary w-full sm:w-auto h-[42px] px-5">
                    <Plus size={16} />
                    <span>Ajouter</span>
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Tab Content: Règles de rejet */}
          {tab === 'regles' && (
            <div className="space-y-6">
              {/* List of existing rules */}
              {regles.length > 0 ? (
                <div className="ensa-config-list">
                  {regles.map((r) => (
                    <div key={r.id} className="ensa-rule-item">
                      <div className="ensa-rule-info">
                        <div className="ensa-rule-header">
                          <span className="ensa-rule-type font-mono">{r.type_regle}</span>
                          <span className={`badge ${r.is_active ? 'badge-preselectionne' : 'badge-rejete_auto'} text-[10px]`}>
                            {r.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </div>
                        <div className="ensa-rule-msg">{r.message_rejet}</div>
                      </div>
                      <button 
                        className={`btn btn-sm ${r.is_active ? 'btn-outline' : 'btn-primary'} h-9 px-3`}
                        onClick={() => toggleRegle(r.id)}
                        title={r.is_active ? 'Suspendre la règle' : 'Activer la règle'}
                      >
                        {r.is_active ? <Pause size={14} /> : <Play size={14} />}
                        <span>{r.is_active ? 'Suspendre' : 'Activer'}</span>
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState
                  title="Aucune règle de rejet configurée"
                  description="Ajoutez des règles de rejet automatique ci-dessous (ex: moyenne minimale académique, note éliminatoire...)."
                  icon={ShieldAlert}
                />
              )}

              {/* Add rule form */}
              <form onSubmit={handleSubmitRegles(addRegle)} className="ensa-card p-6">
                <h3 className="text-sm font-semibold text-text-primary mb-4 flex items-center gap-2 border-b border-border pb-3">
                  <ShieldAlert size={16} className="text-primary-500" />
                  <span>Nouvelle règle de rejet automatique</span>
                </h3>
                
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="label" htmlFor="rule-type">Type de condition</label>
                    <select id="rule-type" className="input" {...regRegles('type_regle', { required: true })}>
                      <option value="">— Choisir un type —</option>
                      <option value="DOUBLON_CIN">Doublon sur le CIN</option>
                      <option value="DOCUMENT_MANQUANT">Un ou plusieurs documents manquants</option>
                      <option value="DIPLOME_INVALIDE">Diplôme invalide / non éligible</option>
                      <option value="ETABLISSEMENT_INVALIDE">Établissement non éligible</option>
                      <option value="MOYENNE_INSUFFISANTE">Moyenne générale insuffisante</option>
                      <option value="NOTE_ELIMINATOIRE">Note de matière éliminatoire</option>
                      <option value="DATE_INCOHERENTE">Date de naissance/diplôme incohérente</option>
                    </select>
                  </div>
                  <div>
                    <label className="label" htmlFor="rule-seuil">Seuil de validation (si applicable)</label>
                    <input 
                      id="rule-seuil"
                      type="number" 
                      step="0.01" 
                      className="input font-mono" 
                      placeholder="Ex: 12.00" 
                      {...regRegles('seuil')} 
                    />
                  </div>
                  <div className="sm:col-span-2">
                    <label className="label" htmlFor="rule-msg">Message explicatif de rejet (affiché au candidat)</label>
                    <input 
                      id="rule-msg"
                      className="input" 
                      placeholder="Ex: Votre dossier a été rejeté car votre moyenne générale est inférieure à la note minimale requise." 
                      {...regRegles('message_rejet', { required: true })} 
                    />
                  </div>
                </div>
                
                <div className="flex justify-end mt-6">
                  <button type="submit" className="btn btn-primary h-[42px] px-5">
                    <Plus size={16} />
                    <span>Ajouter la règle</span>
                  </button>
                </div>
              </form>
            </div>
          )}
        </>
      )}

      {/* Skeleton loader en cours de chargement */}
      {selectedFiliere && loading && (
        <div className="space-y-4">
          <div className="skeleton h-12 w-full rounded-xl" />
          <div className="skeleton h-32 w-full rounded-xl" />
          <div className="skeleton h-48 w-full rounded-xl" />
        </div>
      )}
    </div>
  );
}
