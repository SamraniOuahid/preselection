// src/pages/candidat/ModifierDossierPage.jsx
import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import API from '../../api/axios';
import AlertBanner from '../../components/common/AlertBanner';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import { ArrowLeft, Save, Send, Plus, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';

const EDITABLE = ['BROUILLON', 'INCOMPLET'];

export default function ModifierDossierPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [dossier, setDossier] = useState(null);
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const { register, handleSubmit, reset, formState: { errors } } = useForm();

  useEffect(() => {
    API.get(`/dossiers/${id}/`)
      .then(({ data }) => {
        if (!EDITABLE.includes(data.statut)) {
          setError('Ce dossier ne peut plus être modifié.');
          setDossier(data);
        } else {
          setDossier(data);
          reset({
            diplome_obtenu: data.diplome_obtenu,
            etablissement_origine: data.etablissement_origine,
            annee_obtention: data.annee_obtention,
            mention: data.mention || '',
            moyenne_generale: data.moyenne_generale,
          });
          setNotes(
            data.notes?.length
              ? data.notes.map((n) => ({ matiere: n.matiere, note_declaree: String(n.note_declaree) }))
              : [{ matiere: '', note_declaree: '' }]
          );
        }
      })
      .catch(() => setError('Dossier introuvable.'))
      .finally(() => setLoading(false));
  }, [id, reset]);

  const updateNote = (i, field, val) => {
    const u = [...notes];
    u[i][field] = val;
    setNotes(u);
  };

  const savePayload = (data) => ({
    filiere: dossier.filiere_id || dossier.filiere,
    diplome_obtenu: data.diplome_obtenu,
    etablissement_origine: data.etablissement_origine,
    annee_obtention: parseInt(data.annee_obtention, 10),
    mention: data.mention || '',
    moyenne_generale: parseFloat(data.moyenne_generale),
    notes: notes
      .filter((n) => n.matiere && n.note_declaree)
      .map((n) => ({ matiere: n.matiere, note_declaree: parseFloat(n.note_declaree) })),
  });

  const onSave = async (data) => {
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
            <input className={`input ${errors.diplome_obtenu ? 'input-error' : ''}`} {...register('diplome_obtenu', { required: true })} />
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
        </div>

        <div className="ensa-mt-4">
          <div className="ensa-page-header-row ensa-mb-4">
            <h3 className="ensa-section-title" style={{ marginBottom: 0 }}>Notes</h3>
            <button type="button" className="btn btn-outline btn-sm" onClick={() => setNotes([...notes, { matiere: '', note_declaree: '' }])}>
              <Plus size={14} /> Ajouter
            </button>
          </div>
          <div className="ensa-notes-list">
            {notes.map((note, i) => (
              <div key={i} className="ensa-note-row">
                <input className="input" placeholder="Matière" value={note.matiere} onChange={(e) => updateNote(i, 'matiere', e.target.value)} />
                <input type="number" step="0.01" className="input font-mono" placeholder="/20" value={note.note_declaree} onChange={(e) => updateNote(i, 'note_declaree', e.target.value)} />
                {notes.length > 1 && (
                  <button type="button" className="btn btn-ghost btn-sm text-danger-500" onClick={() => setNotes(notes.filter((_, idx) => idx !== i))}>
                    <Trash2 size={14} />
                  </button>
                )}
              </div>
            ))}
          </div>
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
