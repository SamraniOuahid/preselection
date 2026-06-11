// src/pages/responsable/DetailDossierPage.jsx
// Détail d'un dossier (vue responsable) — layout 3 colonnes
import { useState, useEffect, useCallback } from 'react';
import { useParams, Link, useSearchParams } from 'react-router-dom';
import API from '../../api/axios';
import StatusBadge from '../../components/common/StatusBadge';
import ScoreGauge from '../../components/common/ScoreGauge';
import AlertBanner from '../../components/common/AlertBanner';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import RapportVerificationPanel from '../../components/verification/RapportVerificationPanel';
import {
  ArrowLeft, User, Mail, Phone, Calendar, GraduationCap,
  Trophy, FileText, Upload, CheckCircle, AlertTriangle,
  XCircle, MessageSquare, Eye, ShieldCheck, Download
} from 'lucide-react';
import { formatDiplome, isDiplomeAutre } from '../../utils/diplome';
import { inscrireAcceptes } from '../../api/oral';

export default function DetailDossierPage() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const [dossier, setDossier] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState(searchParams.get('tab') || 'notes');
  const [commentaire, setCommentaire] = useState('');
  const [actionLoading, setActionLoading] = useState('');

  const rafraichirDossier = useCallback(() => {
    return API.get(`/dossiers/${id}/`)
      .then(({ data }) => setDossier(data))
      .catch(() => {});
  }, [id]);

  useEffect(() => {
    setLoading(true);
    rafraichirDossier().finally(() => setLoading(false));
  }, [rafraichirDossier]);

  const handleAction = async (action) => {
    if (action === 'rejeter' && !commentaire.trim()) {
      alert('Le commentaire est obligatoire pour rejeter un dossier.');
      return;
    }
    setActionLoading(action);
    try {
      await API.post(`/dossiers/${id}/${action}/`, { commentaire });
      await rafraichirDossier();
      setCommentaire('');
    } catch (err) {
      alert(err.response?.data?.error || "Erreur lors de l'action");
    } finally {
      setActionLoading('');
    }
  };

  const handleDownloadPDF = async (convocationId) => {
    if (!convocationId) {
      alert("Erreur: ID de convocation introuvable.");
      return;
    }
    try {
      const response = await API.get(`/convocations/${convocationId}/telecharger_pdf/`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Convocation_${dossier.candidat?.nom || 'Candidat'}_ENSA_BM.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert("Erreur lors du téléchargement de la convocation.");
    }
  };

  if (loading) return <LoadingSpinner size="lg" text="Chargement..." className="py-20" />;

  if (!dossier) {
    return (
      <div className="card p-12 text-center">
        <p className="text-text-muted mb-4">Dossier introuvable.</p>
        <Link to="/dossiers" className="btn btn-outline"><ArrowLeft size={16} /> Retour</Link>
      </div>
    );
  }

  const canValidate = ['EN_ATTENTE', 'SUSPECT'].includes(dossier.statut);

  return (
    <div className="ensa-page animate-fade-in">
      <div className="ensa-page-header">
        <nav className="ensa-breadcrumb">
          <Link to="/dashboard">Dashboard</Link>
          <span>/</span>
          <Link to="/dossiers">Dossiers</Link>
          <span>/</span>
          <span className="ensa-breadcrumb-current">{dossier.candidat?.prenom} {dossier.candidat?.nom}</span>
        </nav>
        <div className="ensa-page-header-row">
          <div>
            <h1 className="ensa-page-title ensa-flex-center ensa-gap-3" style={{ flexWrap: 'wrap' }}>
              {dossier.candidat?.prenom} {dossier.candidat?.nom}
              <StatusBadge statut={dossier.statut} />
              {dossier.is_suspect && <span className="badge badge-suspect"><AlertTriangle size={12} /> Suspect</span>}
            </h1>
            <p className="ensa-page-subtitle">{dossier.filiere_nom} ({dossier.filiere_code})</p>
          </div>

          {canValidate && (
            <div className="ensa-flex ensa-gap-2">
              <button className="btn btn-success btn-sm" onClick={() => handleAction('valider')} disabled={!!actionLoading}>
                {actionLoading === 'valider' ? <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <CheckCircle size={14} />}
                Présélectionner
              </button>
              {dossier.motif_rejet && (
                <button className="btn btn-danger btn-sm" onClick={() => handleAction('rejeter_auto')} disabled={!!actionLoading}>
                  {actionLoading === 'rejeter_auto' ? <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <XCircle size={14} />}
                  Confirmer le rejet (auto)
                </button>
              )}
              <button className="btn btn-outline-danger btn-sm" onClick={() => handleAction('rejeter')} disabled={!!actionLoading}>
                {actionLoading === 'rejeter' ? <span className="w-4 h-4 border-2 border-danger-300 border-t-danger-600 rounded-full animate-spin" /> : <XCircle size={14} />}
                Rejeter {dossier.motif_rejet ? '(manuel)' : ''}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Alertes */}
      {dossier.is_suspect && (
        <AlertBanner variant="warning" title="Dossier suspect — Vérification manuelle requise" className="mb-5">
          ⚠ Ce dossier a été marqué comme suspect par le système de vérification automatique. Une vérification manuelle est recommandée avant toute décision.
        </AlertBanner>
      )}
      {['EN_ATTENTE', 'SUSPECT'].includes(dossier.statut) && dossier.motif_rejet && (
        <AlertBanner variant="warning" title="Rejet automatique recommandé par le système" className="mb-5">
          ⚠ Ce dossier ne remplit pas les critères d'éligibilité et est proposé pour rejet automatique.
          <div className="mt-1 font-semibold">Motif détecté : {dossier.motif_rejet}</div>
        </AlertBanner>
      )}
      {dossier.statut === 'ORAL_ACCEPTE' && (
        <AlertBanner variant="success" title="Candidat Accepté" className="mb-5">
          Ce candidat a été accepté suite à l'entretien oral. Il peut être inscrit définitivement.
        </AlertBanner>
      )}

      {dossier.statut === 'CONVOQUE_ORAL' && (
        <AlertBanner variant="info" title="Candidat Convoqué" className="mb-5">
          Ce candidat est convoqué à l'entretien oral.
        </AlertBanner>
      )}

      {!['EN_ATTENTE', 'SUSPECT'].includes(dossier.statut) && dossier.motif_rejet && (
        <AlertBanner variant="error" title="Motif de rejet" className="mb-5">{dossier.motif_rejet}</AlertBanner>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Colonne gauche — Infos candidat (3/12 = 25%) */}
        <div className="lg:col-span-3 flex flex-col gap-6">
          {/* Photo placeholder + infos */}
          <div className="card p-5">
            <div className="flex flex-col items-center mb-4">
              <div className="w-20 h-20 rounded-full bg-primary-50 flex items-center justify-center text-2xl font-bold text-primary-700 mb-3">
                {dossier.candidat?.prenom?.[0]}{dossier.candidat?.nom?.[0]}
              </div>
              <h3 className="text-sm font-bold text-text-primary">{dossier.candidat?.prenom} {dossier.candidat?.nom}</h3>
            </div>
            <div className="space-y-3 text-sm">
              {[
                { Icon: User, label: 'CIN', value: dossier.candidat?.user_cin, mono: true },
                { Icon: Mail, label: 'Email', value: dossier.candidat?.user_email },
                { Icon: Phone, label: 'Téléphone', value: dossier.candidat?.telephone || '—' },
                { Icon: Calendar, label: 'Naissance', value: dossier.candidat?.date_naissance || '—' },
                { Icon: GraduationCap, label: 'Diplôme', value: formatDiplome(dossier.diplome_obtenu), extraBadge: isDiplomeAutre(dossier.diplome_obtenu) },
                { Icon: GraduationCap, label: 'Établissement', value: dossier.etablissement_origine },
              ].map(({ Icon, label, value, mono, extraBadge }) => (
                <div key={label} className="flex items-start gap-2">
                  <Icon size={14} className="text-text-muted mt-0.5 flex-shrink-0" />
                  <div>
                    <span className="text-text-muted text-xs">{label}</span>
                    <div className={`font-medium text-sm ${mono ? 'font-mono' : ''}`}>
                      {value || '—'}
                      {extraBadge && (
                        <span className="ml-1.5 text-[10px] font-semibold bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-full">
                          hors liste
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Score */}
          <div className="card p-5 flex flex-col items-center">
            <ScoreGauge score={dossier.score ? parseFloat(dossier.score) : 0} label="Score final" />
            {dossier.classement && (
              <div className="flex items-center gap-2 mt-3 text-sm">
                <Trophy size={14} className="text-warning-500" />
                <span className="font-semibold">#{dossier.classement}</span>
                <span className="text-text-muted">dans la filière</span>
              </div>
            )}
          </div>
        </div>

        {/* Colonne centrale — Notes, Vérification et Documents (5/12 = 41.7%) */}
        <div className="lg:col-span-5 flex flex-col gap-6">
          {/* Onglets */}
          <div className="flex border-b border-border mb-0 overflow-x-auto">
            {[
              { key: 'infos', label: 'Informations', Icon: User },
              { key: 'notes', label: 'Notes', Icon: FileText },
              { key: 'verification', label: 'Vérification', Icon: ShieldCheck },
              { key: 'documents', label: 'Documents', Icon: Upload },
            ].map(({ key, label, Icon }) => (
              <button
                key={key}
                onClick={() => setActiveTab(key)}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                  activeTab === key
                    ? 'border-primary-700 text-primary-700'
                    : 'border-transparent text-text-muted hover:text-text-primary'
                }`}
              >
                <Icon size={15} /> {label}
              </button>
            ))}
          </div>

          {/* Onglet Informations */}
          {activeTab === 'infos' && (
            <div className="card rounded-t-none border-t-0 p-5 space-y-4">
              <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wide">
                Informations Personnelles & Académiques
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {[
                  { label: 'Nom', value: dossier.candidat?.nom },
                  { label: 'Prénom', value: dossier.candidat?.prenom },
                  { label: 'CIN', value: dossier.candidat?.user_cin },
                  { label: 'CNE / Code Massar', value: dossier.candidat?.cne || dossier.candidat?.code_massar || '—' },
                  { label: 'Email', value: dossier.candidat?.user_email },
                  { label: 'Téléphone', value: dossier.candidat?.telephone },
                  { label: 'Date de naissance', value: dossier.candidat?.date_naissance },
                  { label: 'Diplôme obtenu', value: formatDiplome(dossier.diplome_obtenu), isAutre: isDiplomeAutre(dossier.diplome_obtenu) },
                  { label: 'Établissement', value: dossier.etablissement_origine },
                  { label: 'Mention', value: dossier.mention || '—' },
                  { label: 'Année obtention', value: dossier.annee_obtention },
                ].map((item) => (
                  <div key={item.label} className="border-b border-gray-50 pb-2">
                    <span className="text-xs text-text-muted">{item.label}</span>
                    <p className="text-sm font-medium text-text-primary mt-0.5">
                      {item.value || '—'}
                      {item.isAutre && (
                        <span className="ml-1.5 text-[10px] font-semibold bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-full">
                          hors liste
                        </span>
                      )}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Onglet Notes */}
          {activeTab === 'notes' && (
            <div className="card rounded-t-none border-t-0 p-5">
              {dossier.notes_semestres?.length > 0 ? (
                <>
                  <div className="table-container">
                    <table className="table">
                      <thead>
                        <tr><th>Semestre</th><th>Moyenne</th><th>Session</th><th>Mention</th></tr>
                      </thead>
                      <tbody>
                        {dossier.notes_semestres.map((n) => (
                          <tr key={n.id}>
                            <td className="font-bold text-primary-700 text-sm">{n.semestre}</td>
                            <td className="font-mono text-sm">{n.moyenne != null ? `${n.moyenne}` : '—'}</td>
                            <td className="text-sm">{n.session_label || (n.session === 'NORMALE' ? 'Normale' : 'Rattrapage')}</td>
                            <td className="text-sm">{n.mention_label || n.mention}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  {dossier.score_confiance_ocr != null && (
                    <div className="mt-3 text-xs text-text-muted flex items-center gap-2">
                      Confiance documents :
                      <span className={`font-mono font-semibold ${dossier.score_confiance_ocr >= 0.8 ? 'text-success-600' : 'text-warning-600'}`}>
                        {(dossier.score_confiance_ocr * 100).toFixed(0)}%
                      </span>
                    </div>
                  )}
                </>
              ) : (
                <p className="text-sm text-text-muted py-6 text-center">Aucune note enregistrée</p>
              )}
            </div>
          )}

          {/* Onglet Vérification */}
          {activeTab === 'verification' && (
            <div className="card rounded-t-none border-t-0 p-5 bg-gray-50/30">
              <RapportVerificationPanel
                dossierId={dossier.id}
                dossier={dossier}
                onUpdate={rafraichirDossier}
              />
            </div>
          )}

          {/* Onglet Documents */}
          {activeTab === 'documents' && (
            <div className="card rounded-t-none border-t-0 p-5">
              {dossier.documents?.length > 0 ? (
                <div className="space-y-3">
                  {dossier.documents.map((doc) => (
                    <a key={doc.id} href={doc.fichier} target="_blank" rel="noreferrer"
                      className="flex items-center gap-3 p-3 rounded-lg border border-border hover:border-primary-200 hover:bg-primary-50/30 transition-all no-underline text-inherit font-normal">
                      <div className="w-10 h-10 rounded-lg bg-primary-50 flex items-center justify-center">
                        <FileText size={18} className="text-primary-500" />
                      </div>
                      <div className="flex-1">
                        <div className="text-sm font-medium">{doc.type_doc}</div>
                        <div className="text-xs text-text-muted">{doc.taille_ko} Ko</div>
                      </div>
                      <Eye size={16} className="text-text-muted" />
                    </a>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-text-muted py-6 text-center">Aucun document</p>
              )}
            </div>
          )}
        </div>

        {/* Colonne droite — Actions (4/12 = 33.3%) */}
        <div className="lg:col-span-4 flex flex-col gap-6">
          {/* Scores rapides */}
          <div className="card p-4">
            <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wide mb-3">Métriques</h3>
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: 'Score', value: dossier.score ?? '—', color: 'text-primary-700' },
                { label: 'Rang', value: dossier.classement ? `#${dossier.classement}` : '—', color: 'text-warning-600' },
                { label: 'Moyenne', value: dossier.moyenne_generale ?? '—', color: 'text-primary-500' },
                { label: 'OCR', value: dossier.score_confiance_ocr ? `${(dossier.score_confiance_ocr * 100).toFixed(0)}%` : '—', color: dossier.score_confiance_ocr >= 0.8 ? 'text-success-600' : 'text-warning-600' },
              ].map(({ label, value, color }) => (
                <div key={label} className="text-center p-2 bg-surface rounded-lg">
                  <div className={`text-lg font-bold font-mono ${color}`}>{value}</div>
                  <div className="text-[10px] text-text-muted mt-0.5">{label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Zone action responsable */}
          {canValidate && (
            <div className="card p-5">
              <h3 className="text-sm font-semibold text-text-primary mb-3 flex items-center gap-2">
                <MessageSquare size={15} /> Décision
              </h3>
              <div className="mb-4">
                <label className="label">Commentaire</label>
                <textarea
                  className="input"
                  rows={3}
                  placeholder={dossier.motif_rejet ? "Commentaire facultatif pour rejet auto / obligatoire pour rejet manuel..." : "Commentaire (obligatoire pour le rejet)..."}
                  value={commentaire}
                  onChange={(e) => setCommentaire(e.target.value)}
                  style={{ resize: 'vertical' }}
                />
              </div>
              <div className="flex flex-col gap-2">
                <button className="btn btn-success btn-sm w-full" onClick={() => handleAction('valider')} disabled={!!actionLoading}>
                  <CheckCircle size={14} /> Présélectionner
                </button>
                {dossier.motif_rejet && (
                  <button className="btn btn-danger btn-sm w-full" onClick={() => handleAction('rejeter_auto')} disabled={!!actionLoading}>
                    <XCircle size={14} /> Confirmer le rejet automatique
                  </button>
                )}
                <button className="btn btn-outline-danger btn-sm w-full" onClick={() => handleAction('rejeter')} disabled={!!actionLoading}>
                  <XCircle size={14} /> Rejeter {dossier.motif_rejet ? 'manuellement' : ''}
                </button>
              </div>
            </div>
          )}

          {/* Action Oral */}
          {dossier.statut === 'CONVOQUE_ORAL' && (
            <div className="card p-5">
               <h3 className="text-sm font-semibold text-text-primary mb-3 flex items-center gap-2">
                <Calendar size={15} /> Entretien Oral
              </h3>
              <button className="btn w-full flex justify-center gap-2 bg-[#1B3A6B] text-white hover:bg-[#142D52]" onClick={() => handleDownloadPDF(dossier.convocations_oral?.[0]?.id)}>
                <Download size={16} /> Télécharger convocation
              </button>
            </div>
          )}

          {dossier.statut === 'ORAL_ACCEPTE' && (
            <div className="card p-5">
               <h3 className="text-sm font-semibold text-text-primary mb-3 flex items-center gap-2">
                <CheckCircle size={15} /> Inscription Définitive
              </h3>
              <button className="btn btn-success w-full flex justify-center gap-2" onClick={async () => {
                if (window.confirm("Inscrire ce candidat définitivement ?")) {
                   try {
                     await inscrireAcceptes(dossier.convocations_oral[0].epreuve_oral);
                     rafraichirDossier();
                   } catch(e) {}
                }
              }}>
                <CheckCircle size={16} /> Inscrire définitivement
              </button>
            </div>
          )}

          {/* Info filière */}
          <div className="card p-4">
            <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wide mb-3">Filière</h3>
            <div className="flex items-center gap-2 mb-2">
              <span className="font-mono text-xs font-bold text-primary-500 bg-primary-50 px-2 py-0.5 rounded">{dossier.filiere_code}</span>
              <span className="text-sm font-medium">{dossier.filiere_nom}</span>
            </div>
            <div className="text-xs text-text-muted">
              Année: {dossier.annee_obtention} — Mention: {dossier.mention || '—'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
