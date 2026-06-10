// src/pages/candidat/ModifierDossierPage.jsx
import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import API from '../../api/axios';
import AlertBanner from '../../components/common/AlertBanner';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import { ArrowLeft, Save, Send, Plus, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';
import SemestreForm from '../../components/candidat/SemestreForm';

const EDITABLE = ['BROUILLON', 'INCOMPLET'];

/**
 * Détermine si un diplôme stocké est un "Autre" (saisie libre).
 * Format attendu : "Autre: [intitulé]"
 */
function parseAutreDiplome(valeur) {
  if (!valeur) return { isAutre: false, texte: '' };
  if (valeur.toLowerCase().startsWith('autre:')) {
    return { isAutre: true, texte: valeur.replace(/^autre:\s*/i, '').trim() };
  }
  if (valeur.toLowerCase() === 'autre') {
    return { isAutre: true, texte: '' };
  }
  return { isAutre: false, texte: '' };
}

export default function ModifierDossierPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [dossier, setDossier] = useState(null);
  const [filiere, setFiliere] = useState(null);
  const [notesSemestres, setNotesSemestres] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const { register, handleSubmit, reset, watch, setValue, formState: { errors } } = useForm();
  const watchedDiplome = watch('diplome_obtenu');

  useEffect(() => {
    API.get(`/dossiers/${id}/`)
      .then(async ({ data }) => {
        if (!EDITABLE.includes(data.statut)) {
          setError('Ce dossier ne peut plus être modifié.');
          setDossier(data);
        } else {
          setDossier(data);

          // Récupérer les diplômes de la filière
          try {
            const { data: filiereData } = await API.get(`/filieres/${data.filiere_id || data.filiere}/`);
            setFiliere(filiereData);
          } catch {
            /* filière non critique */
          }

          // Résoudre la valeur du champ diplome
          const { isAutre, texte } = parseAutreDiplome(data.diplome_obtenu);
          reset({
            diplome_obtenu: isAutre ? 'Autre' : (data.diplome_obtenu || ''),
            diplome_obtenu_autre: texte,
            etablissement_origine: data.etablissement_origine,
            annee_obtention: data.annee_obtention,
            mention: data.mention || '',
            moyenne_generale: data.moyenne_generale,
            code_massar: data.code_massar || '',
            cne: data.cne || '',
          });
          setNotesSemestres(
            data.notes_semestres?.length
              ? data.notes_semestres.map(n => ({ ...n, moyenne: String(n.moyenne) }))
              : []
          );
        }
      })
      .catch(() => setError('Dossier introuvable.'))
      .finally(() => setLoading(false));
  }, [id, reset]);

  const updateNoteSemestre = (i, field, val) => {
    const u = [...notesSemestres];
    u[i][field] = val;
    setNotesSemestres(u);
  };

  const savePayload = (data) => ({
    filiere: dossier.filiere_id || dossier.filiere,
    diplome_obtenu: data.diplome_obtenu === 'Autre'
      ? `Autre: ${data.diplome_obtenu_autre}`
      : data.diplome_obtenu,
    etablissement_origine: data.etablissement_origine,
    annee_obtention: parseInt(data.annee_obtention, 10),
    mention: data.mention || '',
    moyenne_generale: parseFloat(data.moyenne_generale),
    code_massar: data.code_massar,
    cne: data.cne,
    notes_semestres: notesSemestres.map(n => ({ ...n, moyenne: parseFloat(n.moyenne) })),
  });

  const onSave = async (data) => {
    if (notesSemestres.some(n => !n.moyenne)) { setError('Veuillez remplir toutes les moyennes semestrielles.'); return; }
    if (notesSemestres.some(n => parseFloat(n.moyenne) < 10 || parseFloat(n.moyenne) > 20)) { setError('Les moyennes doivent être comprises entre 10 et 20.'); return; }
    
    setSaving(true);
    setError('');
    try {
      await API.put(`/dossiers/${id}/`, savePayload(data));
      toast.success('Dossier enregistré');
      navigate(`/dossier/${id}`);
    } catch (err) {
      setError(err.response?.data?.error || 'Erreur lors de la sauvegarde.');
    } finally {
      setSaving(false);
    }
  };

  const onSoumettre = async (data) => {
    if (notesSemestres.some(n => !n.moyenne)) { setError('Veuillez remplir toutes les moyennes semestrielles.'); return; }
    if (notesSemestres.some(n => parseFloat(n.moyenne) < 10 || parseFloat(n.moyenne) > 20)) { setError('Les moyennes doivent être comprises entre 10 et 20.'); return; }
    
    setSaving(true);
    setError('');
    try {
      await API.put(`/dossiers/${id}/`, savePayload(data));
      await API.post(`/dossiers/${id}/soumettre/`);
      toast.success('Dossier soumis');
      navigate(`/dossier/${id}`);
    } catch (err) {
      setError(err.response?.data?.message || err.response?.data?.error || 'Erreur à la soumission.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <LoadingSpinner size="lg" text="Chargement..." className="py-20" />;

  if (!dossier && error) {
    return (
      <div className="ensa-page ensa-page-narrow">
        <AlertBanner variant="error">{error}</AlertBanner>
        <Link to="/mes-dossiers" className="btn btn-outline ensa-mt-4"><ArrowLeft size={16} /> Retour</Link>
      </div>
    );
  }

  if (error && !EDITABLE.includes(dossier?.statut)) {
    return (
      <div className="ensa-page ensa-page-narrow animate-fade-in">
        <AlertBanner variant="warning" title="Modification impossible">
          {error} Les dossiers soumis (en attente, présélectionnés, rejetés) sont en lecture seule.
        </AlertBanner>
        <Link to={`/dossier/${id}`} className="btn btn-primary ensa-mt-4"><ArrowLeft size={16} /> Voir le dossier</Link>
      </div>
    );
  }

  const diplomesAcceptes = filiere?.diplomes_acceptes || [];

  return (
    <div className="ensa-page ensa-page-narrow animate-fade-in">
      <div className="ensa-page-header">
        <nav className="ensa-breadcrumb">
          <Link to={`/dossier/${id}`}><ArrowLeft size={14} /> Retour au dossier</Link>
        </nav>
        <h1 className="ensa-page-title">Modifier le dossier</h1>
        <p className="ensa-page-subtitle">{dossier.filiere_nom} ({dossier.filiere_code})</p>
      </div>

      {error && <AlertBanner variant="error" className="ensa-mb-5">{error}</AlertBanner>}

      <form onSubmit={handleSubmit(onSave)} className="ensa-form-section ensa-mb-5">
        <h2 className="ensa-section-title">Informations académiques</h2>
        <div className="ensa-form-grid">
          <div>
            <label className="label">Diplôme obtenu</label>
            <select
              className={`input ${errors.diplome_obtenu ? 'input-error' : ''}`}
              {...register('diplome_obtenu', { required: 'Obligatoire' })}
            >
              <option value="">— Choisir un diplôme —</option>
              {diplomesAcceptes.map((da) => (
                <option key={da.id} value={da.nom_diplome}>{da.nom_diplome}</option>
              ))}
              <option value="Autre">Autre diplôme (saisie libre)</option>
            </select>
            {errors.diplome_obtenu && <p className="error-text">{errors.diplome_obtenu.message}</p>}
          </div>

          <div>
            <label className="label">Établissement</label>
            <input className={`input ${errors.etablissement_origine ? 'input-error' : ''}`} {...register('etablissement_origine', { required: true })} />
          </div>

          <div>
            <label className="label">Année</label>
            <input type="number" className="input" {...register('annee_obtention', { required: true })} />
          </div>

          <div>
            <label className="label">Mention</label>
            <select className="input" {...register('mention')}>
              <option value="">—</option>
              <option value="TB">Très Bien</option>
              <option value="B">Bien</option>
              <option value="AB">Assez Bien</option>
              <option value="P">Passable</option>
            </select>
          </div>

          <div>
            <label className="label">Moyenne /20</label>
            <input type="number" step="0.01" min="0" max="20" className="input font-mono" {...register('moyenne_generale', { required: true })} />
          </div>

          <div>
            <label className="label">Code Massar</label>
            <input className={`input font-mono ${errors.code_massar ? 'input-error' : ''}`} placeholder="R123456789" {...register('code_massar', { required: 'Obligatoire' })} />
            {errors.code_massar && <p className="error-text">{errors.code_massar.message}</p>}
          </div>

          <div>
            <label className="label">CNE</label>
            <input className={`input font-mono ${errors.cne ? 'input-error' : ''}`} placeholder="1234567890" {...register('cne', { required: 'Obligatoire' })} />
            {errors.cne && <p className="error-text">{errors.cne.message}</p>}
          </div>
        </div>

        {/* Champ libre si "Autre" est sélectionné */}
        {watchedDiplome === 'Autre' && (
          <div className="mt-4">
            <label className="label">Précisez l'intitulé de votre diplôme</label>
            <input
              className={`input ${errors.diplome_obtenu_autre ? 'input-error' : ''}`}
              placeholder="Ex: DUT Chimie"
              {...register('diplome_obtenu_autre', { required: 'Obligatoire pour les diplômes non répertoriés' })}
            />
            {errors.diplome_obtenu_autre && <p className="error-text">{errors.diplome_obtenu_autre.message}</p>}
            <p className="text-[11px] text-amber-600 mt-1 font-medium">
              ⚠️ Note : Un diplôme hors liste officielle peut faire l'objet d'une pondération réduite.
            </p>
          </div>
        )}

        <div className="ensa-mt-4">
          <div className="ensa-page-header-row ensa-mb-4">
            <h3 className="ensa-section-title" style={{ marginBottom: 0 }}>Résultats par semestre</h3>
          </div>
          <SemestreForm notesSemestres={notesSemestres} onUpdateNote={updateNoteSemestre} />
        </div>

        <div className="ensa-step-nav">
          <Link to={`/dossier/${id}`} className="btn btn-outline">Annuler</Link>
          <div className="ensa-flex ensa-gap-2">
            <button type="submit" className="btn btn-primary" disabled={saving}>
              <Save size={16} /> {saving ? 'Enregistrement...' : 'Enregistrer'}
            </button>
            {['BROUILLON', 'INCOMPLET'].includes(dossier.statut) && (
              <button type="button" className="btn btn-success" disabled={saving} onClick={handleSubmit(onSoumettre)}>
                <Send size={16} /> Enregistrer et soumettre
              </button>
            )}
          </div>
        </div>
      </form>
    </div>
  );
}
