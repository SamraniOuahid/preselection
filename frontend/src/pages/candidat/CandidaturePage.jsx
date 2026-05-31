// src/pages/candidat/CandidaturePage.jsx
// Formulaire multi-étapes (5 étapes) pour le dépôt de dossier candidat
import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, Link } from 'react-router-dom';
import API from '../../api/axios';
import StepperBar from '../../components/common/StepperBar';
import FileDropZone from '../../components/common/FileDropZone';
import ConfirmModal from '../../components/common/ConfirmModal';
import AlertBanner from '../../components/common/AlertBanner';
import {
  ChevronLeft, ChevronRight, Send, GraduationCap,
  Users, Plus, Trash2, CheckCircle, Home, FolderOpen, FileText,
  Calendar, MapPin, Clock
} from 'lucide-react';

const STEPS = [
  { label: 'Filière' },
  { label: 'Académique' },
  { label: 'Notes' },
  { label: 'Documents' },
  { label: 'Récapitulatif' },
];

const REQUIRED_DOCS = ['DIPLOME', 'RELEVE', 'CIN', 'PHOTO'];

export default function CandidaturePage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [filieres, setFilieres] = useState([]);
  const [selectedFiliere, setSelectedFiliere] = useState(null);
  const [notes, setNotes] = useState([{ matiere: '', note_declaree: '' }]);
  const [files, setFiles] = useState({ DIPLOME: null, RELEVE: null, CIN: null, PHOTO: null });
  const [certifie, setCertifie] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const { register, formState: { errors }, getValues, trigger } = useForm();

  useEffect(() => {
    API.get('/filieres/').then(({ data }) => {
      const list = data.results || data;
      setFilieres(list.filter((f) => f.is_active));
    });
  }, []);

  const addNote = () => setNotes([...notes, { matiere: '', note_declaree: '' }]);
  const removeNote = (i) => setNotes(notes.filter((_, idx) => idx !== i));
  const updateNote = (i, field, val) => {
    const u = [...notes]; u[i][field] = val; setNotes(u);
  };
  const missingDocs = REQUIRED_DOCS.filter((k) => !files[k]);
  const formatNiveau = (niveau) => (
    niveau === 'BAC2' ? 'Bac+2' : niveau === 'BAC3' ? 'Bac+3' : niveau || '—'
  );

  const goNext = async () => {
    if (step === 1 && !selectedFiliere) { setError('Veuillez sélectionner une filière.'); return; }
    if (step === 2) { const v = await trigger(['diplome_obtenu','etablissement_origine','annee_obtention','moyenne_generale']); if (!v) return; }
    if (step === 3 && notes.filter(n => n.matiere && n.note_declaree).length === 0) { setError('Ajoutez au moins une note.'); return; }
    if (step === 4 && missingDocs.length > 0) { setError('Veuillez uploader tous les documents obligatoires.'); return; }
    setError(''); setStep(Math.min(step + 1, 5));
  };

  const goPrev = () => { setError(''); setStep(Math.max(step - 1, 1)); };

  const onSubmit = async () => {
    setError(''); setLoading(true);
    try {
      if (missingDocs.length > 0) {
        setError('Veuillez uploader tous les documents obligatoires.');
        setShowConfirm(false);
        return;
      }
      const data = getValues();
      const validNotes = notes.filter((n) => n.matiere && n.note_declaree);
      const payload = {
        filiere: selectedFiliere.id,
        diplome_obtenu: data.diplome_obtenu,
        etablissement_origine: data.etablissement_origine,
        annee_obtention: parseInt(data.annee_obtention),
        mention: data.mention || '',
        moyenne_generale: parseFloat(data.moyenne_generale),
        notes: validNotes.map((n) => ({ matiere: n.matiere, note_declaree: parseFloat(n.note_declaree) })),
      };
      const { data: dossier } = await API.post('/dossiers/', payload);
      for (const [type, file] of Object.entries(files)) {
        if (file) {
          const fd = new FormData();
          fd.append('dossier_id', dossier.id); fd.append('type_doc', type); fd.append('fichier', file);
          await API.post('/documents/upload/', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
        }
      }
      await API.post(`/dossiers/${dossier.id}/soumettre/`);
      navigate(`/dossier/${dossier.id}`);
    } catch (err) {
      const msg = err.response?.data?.error || err.response?.data?.detail || 'Erreur lors de la création.';
      setError(typeof msg === 'object' ? JSON.stringify(msg) : msg);
      setShowConfirm(false);
    } finally { setLoading(false); }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <nav className="ensa-breadcrumb mb-4">
        <Link to="/mes-dossiers" className="hover:text-primary-700 no-underline flex items-center gap-1"><Home size={14} /> Accueil</Link>
        <span>/</span>
        <Link to="/mes-dossiers" className="hover:text-primary-700 no-underline"><FolderOpen size={14} className="inline mr-1" />Mon dossier</Link>
        <span>/</span>
        <span className="text-text-primary font-medium">Candidature</span>
      </nav>

      <div><StepperBar steps={STEPS} currentStep={step} /></div>

      {error && <AlertBanner variant="error">{error}</AlertBanner>}

      {/* Étape 1 — Filière */}
      {step === 1 && (
        <div className="ensa-form-section animate-fade-in">
          <h2 className="ensa-section-title">Choix de la filière</h2>
          <p className="ensa-section-desc">Sélectionnez la filière souhaitée</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {filieres.map((f) => {
              const ep = f.epreuve_info;
              return (
                <div key={f.id} onClick={() => setSelectedFiliere(f)}
                  className={`ensa-filiere-option ${selectedFiliere?.id === f.id ? 'is-selected' : ''}`}>
                  <div className="ensa-filiere-option-header">
                    <div className="flex-1 min-w-0">
                      <span className="ensa-dossier-code">{f.code}</span>
                      <h3 className="ensa-filiere-option-meta ensa-text-primary ensa-font-semibold" style={{ marginTop: 8, display: 'block' }}>{f.nom}</h3>
                      <div className="ensa-filiere-option-meta">
                        <span className="badge badge-en_traitement">{formatNiveau(f.niveau)}</span>
                        <span className="ensa-text-muted ensa-text-sm ensa-flex-center ensa-gap-2"><Users size={12} /> {f.places_disponibles || 30} places</span>
                      </div>
                    </div>
                    {selectedFiliere?.id === f.id && <CheckCircle size={20} className="text-primary-500 flex-shrink-0" />}
                  </div>

                  {/* Dates d'épreuves */}
                  {ep ? (
                    <div style={{
                      marginTop: '12px',
                      padding: '10px 12px',
                      background: 'linear-gradient(135deg, #f0f4ff 0%, #e8f0fe 100%)',
                      borderRadius: '10px',
                      border: '1px solid #c7d7f9',
                      fontSize: '12px',
                      display: 'grid',
                      gridTemplateColumns: '1fr 1fr',
                      gap: '8px',
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#1B3A6B' }}>
                        <Calendar size={13} style={{ flexShrink: 0, color: '#3B6FE5' }} />
                        <div>
                          <div style={{ fontWeight: 700, fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#3B6FE5' }}>Épreuve Écrite</div>
                          <div style={{ fontWeight: 600 }}>{ep.date_ecrit || <span style={{ color: '#94a3b8' }}>Non définie</span>}</div>
                        </div>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#1B3A6B' }}>
                        <Calendar size={13} style={{ flexShrink: 0, color: '#7C3AED' }} />
                        <div>
                          <div style={{ fontWeight: 700, fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#7C3AED' }}>Épreuve Orale</div>
                          <div style={{ fontWeight: 600 }}>{ep.date_oral || <span style={{ color: '#94a3b8' }}>Non définie</span>}</div>
                        </div>
                      </div>
                      
                      {/* Détails Écrit / Oral de la filière */}
                      {(ep.heure_ecrit || ep.lieu_ecrit || ep.heure_oral || ep.lieu_oral) && (
                        <div style={{ gridColumn: '1 / -1', borderTop: '1px dashed #c7d7f9', paddingTop: '8px', marginTop: '4px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '11px', color: '#4b5563' }}>
                          {/* Écrit details */}
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                            {ep.heure_ecrit && (
                              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                <Clock size={11} style={{ color: '#3B6FE5' }} />
                                <strong>Heure écit :</strong> {ep.heure_ecrit}
                              </span>
                            )}
                            {ep.lieu_ecrit && (
                              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                <MapPin size={11} style={{ color: '#3B6FE5' }} />
                                <strong>Lieu écrit :</strong> {ep.lieu_ecrit}
                              </span>
                            )}
                          </div>
                          
                          {/* Oral details */}
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                            {ep.heure_oral && (
                              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                <Clock size={11} style={{ color: '#7C3AED' }} />
                                <strong>Heure oral :</strong> {ep.heure_oral}
                              </span>
                            )}
                            {ep.lieu_oral && (
                              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                <MapPin size={11} style={{ color: '#7C3AED' }} />
                                <strong>Lieu oral :</strong> {ep.lieu_oral}
                              </span>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div style={{
                      marginTop: '10px',
                      padding: '8px 12px',
                      background: '#f8f9fa',
                      borderRadius: '8px',
                      border: '1px dashed #d1d5db',
                      fontSize: '12px',
                      color: '#9ca3af',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                    }}>
                      <Calendar size={12} />
                      Dates d'épreuves non encore planifiées
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Étape 2 — Académique */}
      {step === 2 && (
        <div className="ensa-form-section animate-fade-in">
          <h2 className="ensa-section-title">Informations académiques</h2>
          <p className="ensa-section-desc">Renseignez vos diplômes et résultats</p>
          <div className="space-y-4">
            <div className="ensa-form-grid">
              <div>
                <label className="label">Diplôme obtenu</label>
                <input className={`input ${errors.diplome_obtenu ? 'input-error' : ''}`} placeholder="DUT Informatique" {...register('diplome_obtenu', { required: 'Obligatoire' })} />
                {errors.diplome_obtenu && <p className="error-text">{errors.diplome_obtenu.message}</p>}
              </div>
              <div>
                <label className="label">Établissement d'origine</label>
                <input className={`input ${errors.etablissement_origine ? 'input-error' : ''}`} placeholder="EST Béni Mellal" {...register('etablissement_origine', { required: 'Obligatoire' })} />
                {errors.etablissement_origine && <p className="error-text">{errors.etablissement_origine.message}</p>}
              </div>
            </div>
            <div className="ensa-form-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
              <div>
                <label className="label">Année d'obtention</label>
                <select className={`input ${errors.annee_obtention ? 'input-error' : ''}`} {...register('annee_obtention', { required: 'Obligatoire' })}>
                  <option value="">— Année —</option>
                  {Array.from({ length: 6 }, (_, i) => 2025 - i).map(y => <option key={y} value={y}>{y}</option>)}
                </select>
              </div>
              <div>
                <label className="label">Mention</label>
                <select className="input" {...register('mention')}>
                  <option value="">— Aucune —</option>
                  <option value="TB">Très Bien</option>
                  <option value="B">Bien</option>
                  <option value="AB">Assez Bien</option>
                  <option value="P">Passable</option>
                </select>
              </div>
              <div>
                <label className="label">Moyenne générale (/20)</label>
                <input type="number" step="0.01" min="0" max="20" className={`input font-mono ${errors.moyenne_generale ? 'input-error' : ''}`} placeholder="14.50"
                  {...register('moyenne_generale', { required: 'Obligatoire', min: { value: 0, message: 'Min 0' }, max: { value: 20, message: 'Max 20' } })} />
                {errors.moyenne_generale && <p className="error-text">{errors.moyenne_generale.message}</p>}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Étape 3 — Notes */}
      {step === 3 && (
        <div className="ensa-form-section animate-fade-in">
          <div className="ensa-page-header-row ensa-mb-5">
            <div>
              <h2 className="ensa-section-title">Notes par matière</h2>
              <p className="ensa-section-desc" style={{ marginBottom: 0 }}>Saisissez vos notes</p>
            </div>
            <button type="button" className="btn btn-outline btn-sm" onClick={addNote}><Plus size={14} /> Ajouter</button>
          </div>
          <div className="ensa-notes-list">
            {notes.map((note, i) => (
              <div key={i} className="ensa-note-row">
                <input className="input flex-[2]" placeholder="Nom de la matière" value={note.matiere} onChange={(e) => updateNote(i, 'matiere', e.target.value)} />
                <input type="number" step="0.01" min="0" max="20" className="input font-mono flex-1" placeholder="/20" value={note.note_declaree} onChange={(e) => updateNote(i, 'note_declaree', e.target.value)} />
                {notes.length > 1 && <button type="button" className="btn btn-ghost btn-sm text-danger-500" onClick={() => removeNote(i)}><Trash2 size={14} /></button>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Étape 4 — Documents */}
      {step === 4 && (
        <div className="ensa-form-section animate-fade-in">
          <h2 className="ensa-section-title">Documents à joindre</h2>
          <p className="ensa-section-desc">Uploadez vos justificatifs (PDF ou image)</p>
          <div className="ensa-grid-2">
            <FileDropZone label="Diplôme" accept={{ 'application/pdf': ['.pdf'] }} file={files.DIPLOME} onFileSelected={(f) => setFiles({ ...files, DIPLOME: f })} onRemove={() => setFiles({ ...files, DIPLOME: null })} hint="PDF — Max 5 Mo" />
            <FileDropZone label="Relevé de notes" accept={{ 'application/pdf': ['.pdf'] }} file={files.RELEVE} onFileSelected={(f) => setFiles({ ...files, RELEVE: f })} onRemove={() => setFiles({ ...files, RELEVE: null })} hint="PDF — Max 5 Mo" />
            <FileDropZone label="CIN (recto-verso)" file={files.CIN} onFileSelected={(f) => setFiles({ ...files, CIN: f })} onRemove={() => setFiles({ ...files, CIN: null })} hint="PDF ou Image — Max 5 Mo" />
            <FileDropZone label="Photo d'identité" accept={{ 'image/*': ['.png', '.jpg', '.jpeg'] }} file={files.PHOTO} onFileSelected={(f) => setFiles({ ...files, PHOTO: f })} onRemove={() => setFiles({ ...files, PHOTO: null })} hint="JPG, PNG — Max 2 Mo" maxSize={2 * 1024 * 1024} />
          </div>
        </div>
      )}

      {/* Étape 5 — Récapitulatif */}
      {step === 5 && (
        <div className="animate-fade-in ensa-recap-grid">
          <h2 className="ensa-section-title">Récapitulatif</h2>
          <div className="ensa-recap-section">
            <h3 className="ensa-card-section-title"><GraduationCap size={16} /> Filière</h3>
            <div className="flex items-center gap-3">
              <span className="font-mono text-sm font-bold text-primary-500 bg-primary-50 px-3 py-1 rounded">{selectedFiliere?.code}</span>
              <span className="text-sm font-medium">{selectedFiliere?.nom}</span>
            </div>
          </div>
          <div className="ensa-recap-section">
            <h3 className="ensa-card-section-title"><FileText size={16} /> Académique</h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-sm">
              {[['Diplôme', getValues('diplome_obtenu')], ['Établissement', getValues('etablissement_origine')], ['Année', getValues('annee_obtention')], ['Mention', getValues('mention') || '—'], ['Moyenne', `${getValues('moyenne_generale')}/20`]].map(([l, v]) => (
                <div key={l}><span className="text-text-muted text-xs">{l}</span><div className="font-medium mt-0.5">{v || '—'}</div></div>
              ))}
            </div>
          </div>
          <div className="ensa-recap-section">
            <h3 className="ensa-card-section-title">Notes</h3>
            {notes.filter(n => n.matiere && n.note_declaree).map((n, i) => (
              <div key={i} className="ensa-recap-notes-item">
                <span>{n.matiere}</span><span className="font-mono font-semibold text-primary-700">{n.note_declaree}/20</span>
              </div>
            ))}
          </div>
          <div className="ensa-recap-section">
            <h3 className="ensa-card-section-title">Documents</h3>
            <div className="ensa-recap-docs">
              {Object.entries(files).map(([t, f]) => (
                <div key={t} className={`ensa-recap-doc ${f ? 'is-ok' : 'is-missing'}`}>
                  {f ? <CheckCircle size={14} /> : <span className="w-3.5 h-3.5 rounded-full border-2 border-current" />}
                  <span>{t}</span>
                </div>
              ))}
            </div>
          </div>
          <label className="ensa-certif">
            <input type="checkbox" checked={certifie} onChange={(e) => setCertifie(e.target.checked)} />
            <span className="ensa-certif-text">Je certifie que les informations fournies sont exactes et authentiques.</span>
          </label>
        </div>
      )}

      {/* Navigation */}
      <div className="border-t border-border pt-6 mt-6 flex items-center justify-between">
        <button type="button" className="btn btn-outline" onClick={goPrev} disabled={step === 1}><ChevronLeft size={16} /> Précédent</button>
        {step < 5 ? (
          <button type="button" className="btn btn-primary" onClick={goNext}>Suivant <ChevronRight size={16} /></button>
        ) : (
          <button type="button" className="btn btn-primary btn-lg" disabled={!certifie || loading} onClick={() => setShowConfirm(true)}><Send size={16} /> Soumettre</button>
        )}
      </div>

      <ConfirmModal isOpen={showConfirm} onClose={() => setShowConfirm(false)} onConfirm={onSubmit}
        title="Confirmer la soumission" message="Une fois soumis, votre dossier ne pourra plus être modifié. Continuer ?"
        confirmLabel="Soumettre" variant="primary" loading={loading} />
    </div>
  );
}
