// src/pages/candidat/SuiviDossierPage.jsx
// Suivi du dossier candidat — Version sécurisée (aucune fuite de données internes)
import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import API from '../../api/axios';
import StatusBadge from '../../components/common/StatusBadge';
import { formatDiplome } from '../../utils/diplome';
import AlertBanner from '../../components/common/AlertBanner';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import {
  ArrowLeft, Trophy, Hash, FileText, GraduationCap,
  CheckCircle, Upload, Mail, User, Pencil, Download
} from 'lucide-react';
import toast from 'react-hot-toast';

const EDITABLE_STATUTS = ['BROUILLON', 'INCOMPLET'];

/**
 * Descriptions des statuts affichées au candidat.
 * Aucune mention d'IA, d'OCR, d'algorithme ou de traitement automatique.
 * Le statut SUSPECT est volontairement absent : il est masqué côté candidat
 * et affiché comme EN_TRAITEMENT par le StatusBadge.
 */
const STATUT_DESC = {
  BROUILLON: 'Votre dossier est en cours de rédaction. Complétez-le et soumettez-le.',
  EN_TRAITEMENT: 'Votre dossier est en cours d\'examen par la commission pédagogique.',
  INCOMPLET: 'Des informations manquent dans votre dossier. Veuillez le compléter.',
  SUSPECT: 'Votre dossier est en cours d\'examen par la commission pédagogique.',
  REJETE_AUTO: 'Votre dossier n\'a pas été retenu. Consultez le motif ci-dessous.',
  EN_ATTENTE: 'Votre dossier a été examiné. En attente de la décision de la commission.',
  PRESELECTIONNE: 'Félicitations ! Vous êtes présélectionné pour la suite du concours.',
  REJETE_FINAL: 'Votre dossier n\'a pas été retenu. Consultez le motif ci-dessous.',
  ADMIS_FINAL: 'Félicitations ! Vous êtes admis(e) à poursuivre le concours.',
  CONVOQUE_ORAL: 'Vous êtes convoqué(e) à l\'entretien oral. Consultez votre convocation.',
  ORAL_ACCEPTE: 'Félicitations ! Vous êtes accepté(e) suite à l\'entretien oral.',
  ORAL_REFUSE: 'Votre candidature n\'a pas été retenue après l\'entretien oral.',
  INSCRIT: 'Vous êtes officiellement inscrit(e) à l\'ENSA BM.',
};

export default function SuiviDossierPage() {
  const { id } = useParams();
  const [dossier, setDossier] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    API.get(`/dossiers/${id}/`)
      .then(({ data }) => setDossier(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id]);

  const handleDownloadConvocationEcrit = async () => {
    try {
      const response = await API.get(`/dossiers/${id}/convocation_ecrit/`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `convocation_ecrit_ENSA_BM_${id}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success('Convocation écrite téléchargée avec succès !');
    } catch (err) {
      toast.error('Erreur lors du téléchargement de la convocation.');
    }
  };

  const handleDownloadConvocationOral = async () => {
    try {
      const response = await API.get(`/dossiers/${id}/convocation_oral/`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `convocation_oral_ENSA_BM_${id}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success('Convocation orale téléchargée avec succès !');
    } catch (err) {
      toast.error('Erreur lors du téléchargement de la convocation.');
    }
  };

  if (loading) return <LoadingSpinner size="lg" text="Chargement du dossier..." className="py-20" />;

  if (!dossier) {
    return (
      <div className="ensa-empty">
        <div className="ensa-empty-icon">
          <FileText size={28} />
        </div>
        <h3 className="ensa-empty-title">Dossier introuvable</h3>
        <p className="ensa-empty-desc mb-4">Ce dossier n'existe pas ou vous n'y avez pas accès.</p>
        <Link to="/mes-dossiers" className="btn btn-primary"><ArrowLeft size={16} /> Retour</Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <div className="ensa-page-header">
        <nav className="ensa-breadcrumb">
          <Link to="/mes-dossiers"><ArrowLeft size={14} /> Mes dossiers</Link>
          <span>/</span>
          <span className="ensa-breadcrumb-current">Suivi du dossier</span>
        </nav>
        <div className="ensa-page-header-row">
          <div>
            <h1 className="ensa-page-title">
              Mon dossier — {dossier.filiere_nom}
            </h1>
            <p className="ensa-page-subtitle">
              {dossier.filiere_code} — Soumis le {dossier.date_soumission ? new Date(dossier.date_soumission).toLocaleDateString('fr-FR') : 'N/A'}
            </p>
          </div>
          <div className="flex gap-2 flex-wrap">
            <Link to="/profil" className="btn btn-outline btn-sm">
              <User size={14} /> Mon profil
            </Link>
            {EDITABLE_STATUTS.includes(dossier.statut) && (
              <Link to={`/dossier/${id}/modifier`} className="btn btn-primary btn-sm">
                <Pencil size={14} /> Modifier le dossier
              </Link>
            )}
            <StatusBadge statut={dossier.statut} />
          </div>
        </div>
      </div>

      {!EDITABLE_STATUTS.includes(dossier.statut) && (
        <AlertBanner variant="info">
          Ce dossier est en lecture seule. Pour modifier vos coordonnées personnelles, utilisez{' '}
          <Link to="/profil" className="ensa-link">Mon profil</Link>.
        </AlertBanner>
      )}

      {dossier.statut === 'PRESELECTIONNE' && (
        <AlertBanner variant="success" title="Présélection">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex-1">
              <p className="font-semibold text-success-800">🎉 Félicitations ! Vous êtes présélectionné(e) pour passer l'épreuve écrite.</p>
              <p className="text-sm text-success-700 mt-1">Vous pouvez dès à présent télécharger votre convocation officielle.</p>
            </div>
            <button
              onClick={handleDownloadConvocationEcrit}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-bold text-white bg-success-600 hover:bg-success-700 rounded-lg transition-colors shadow-sm cursor-pointer"
            >
              <Download size={14} /> Télécharger ma convocation (PDF)
            </button>
          </div>
        </AlertBanner>
      )}

      {dossier.statut === 'ADMIS_FINAL' && (
        <AlertBanner variant="success" title="Admission Écrit">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex-1">
              <p className="font-semibold text-success-800">🎉 Félicitations ! Vous êtes admis(e) à l'épreuve écrite.</p>
              <p className="text-sm text-success-700 mt-1">Vous êtes convoqué(e) à passer l'épreuve orale d'admission.</p>
            </div>
            <button
              onClick={handleDownloadConvocationOral}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-bold text-white bg-success-600 hover:bg-success-700 rounded-lg transition-colors shadow-sm cursor-pointer"
            >
              <Download size={14} /> Télécharger ma convocation orale (PDF)
            </button>
          </div>
        </AlertBanner>
      )}

      {dossier.statut === 'CONVOQUE_ORAL' && (
        <AlertBanner variant="info" title="Convocation Orale">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex-1">
              <p className="font-semibold text-blue-800">📅 Vous êtes convoqué(e) à l'entretien oral.</p>
              <p className="text-sm text-blue-700 mt-1">Consultez votre convocation pour les détails et téléchargez-la.</p>
            </div>
            <Link to="/candidat/convocation" className="inline-flex items-center gap-2 px-4 py-2 text-sm font-bold text-white bg-[#1B3A6B] hover:bg-[#142D52] rounded-lg transition-colors shadow-sm">
              <Download size={14} /> Voir ma convocation
            </Link>
          </div>
        </AlertBanner>
      )}

      {dossier.statut === 'ORAL_ACCEPTE' && (
        <AlertBanner variant="success" title="Admission Définitive">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex-1">
              <p className="font-semibold text-success-800">🎓 Félicitations ! Vous avez été accepté(e) à l'ENSA Béni Mellal suite à votre entretien.</p>
              <p className="text-sm text-success-700 mt-1">Veuillez vous présenter au service scolarité pour finaliser votre inscription.</p>
            </div>
          </div>
        </AlertBanner>
      )}

      {dossier.statut === 'INSCRIT' && (
        <div className="bg-[#059669] text-white rounded-xl p-6 shadow-md mb-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center">
              <CheckCircle size={24} />
            </div>
            <div>
              <h3 className="text-lg font-bold">Inscription Finalisée</h3>
              <p className="opacity-90">✅ Vous êtes officiellement inscrit(e) à l'ENSA Béni Mellal — {dossier.filiere_nom}</p>
            </div>
          </div>
        </div>
      )}

      {(dossier.statut === 'REJETE_AUTO' || dossier.statut === 'REJETE_FINAL' || dossier.statut === 'ORAL_REFUSE') && (
        <AlertBanner variant="error" title="Candidature non retenue">
          Votre candidature n'a pas été retenue cette année. Nous vous souhaitons beaucoup de succès dans vos projets futurs.
        </AlertBanner>
      )}

      {dossier.statut === 'INCOMPLET' && (
        <AlertBanner variant="warning" title="Dossier incomplet">
          ⚠️ Votre dossier est incomplet. Veuillez compléter les documents manquants.
        </AlertBanner>
      )}

      {/* Carte statut principale — Pas de score, pas de is_suspect, pas de données internes */}
      <div className="ensa-card">
        <div className="ensa-card-body">
        <div className="flex flex-col lg:flex-row items-start lg:items-center gap-6">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <StatusBadge statut={dossier.statut} />
            </div>
            <p className="text-sm text-text-secondary leading-relaxed">
              {STATUT_DESC[dossier.statut] || 'Votre dossier est en cours de traitement.'}
            </p>

            {/* Classement — affiché uniquement si disponible */}
            {dossier.classement && (
              <div className="flex items-center gap-4 mt-4 pt-4 border-t border-border">
                <div className="flex items-center gap-2">
                  <Trophy size={16} className="text-warning-500" />
                  <span className="text-sm font-semibold">Classé {dossier.classement}<sup>ème</sup></span>
                </div>
                <div className="flex items-center gap-2 text-sm text-text-muted">
                  <Hash size={14} />
                  <span>sur {dossier.total_candidats || '—'} candidats</span>
                </div>
              </div>
            )}
          </div>
        </div>
        </div>
      </div>

      {/* Motif de rejet — Le motif provient du backend et ne mentionne pas l'automatisation */}
      {dossier.motif_rejet && (
        <AlertBanner variant="error" title="Motif">
          {dossier.motif_rejet}
          <div className="mt-2">
            <a href="mailto:scolarite@ensabm.ac.ma" className="inline-flex items-center gap-1 text-xs font-medium underline">
              <Mail size={12} /> Contactez la scolarité
            </a>
          </div>
        </AlertBanner>
      )}

      {/* Informations académiques */}
      <div className="ensa-card">
        <div className="ensa-card-body">
        <h3 className="text-sm font-semibold text-text-secondary mb-4 flex items-center gap-2">
          <GraduationCap size={16} /> Informations académiques
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
          <div><span className="text-text-muted text-xs">Diplôme</span><div className="font-medium mt-0.5">{formatDiplome(dossier.diplome_obtenu)}</div></div>
          <div><span className="text-text-muted text-xs">Établissement</span><div className="font-medium mt-0.5">{dossier.etablissement_origine}</div></div>
          <div><span className="text-text-muted text-xs">Année</span><div className="font-medium mt-0.5">{dossier.annee_obtention}</div></div>
          <div><span className="text-text-muted text-xs">Mention</span><div className="font-medium mt-0.5">{dossier.mention || '—'}</div></div>
          <div><span className="text-text-muted text-xs">Moyenne</span><div className="font-medium font-mono mt-0.5">{dossier.moyenne_generale}/20</div></div>
        </div>
        </div>
      </div>

      {/* Résultats semestriels */}
      {dossier.notes_semestres?.length > 0 && (
        <div className="ensa-card">
          <div className="ensa-card-body" style={{ paddingBottom: 0 }}>
            <h3 className="text-sm font-semibold text-text-secondary mb-4 flex items-center gap-2">
              <FileText size={16} /> Résultats semestriels
            </h3>
          </div>
          <div className="ensa-table-wrap" style={{ border: 'none', borderRadius: 0, borderTop: '1px solid #e5e7eb' }}>
            <table className="table">
              <thead>
                <tr><th>Semestre</th><th>Moyenne</th><th>Session</th><th>Mention</th></tr>
              </thead>
              <tbody>
                {dossier.notes_semestres.map((n) => (
                  <tr key={n.id}>
                    <td className="font-bold text-primary-700">{n.semestre}</td>
                    <td className="font-mono">{n.moyenne != null ? `${n.moyenne}/20` : '—'}</td>
                    <td>{n.session_label || (n.session === 'NORMALE' ? 'Normale' : 'Rattrapage')}</td>
                    <td>{n.mention_label || n.mention}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Documents */}
      {dossier.documents?.length > 0 && (
        <div className="ensa-card">
          <div className="ensa-card-body">
          <h3 className="text-sm font-semibold text-text-secondary mb-4 flex items-center gap-2">
            <Upload size={16} /> Documents soumis
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {dossier.documents.map((doc) => (
              <div key={doc.id} className="flex items-center gap-3 p-3 rounded-lg border border-border">
                <div className="w-10 h-10 rounded-lg bg-primary-50 flex items-center justify-center">
                  <FileText size={18} className="text-primary-500" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate">{doc.type_doc}</div>
                  <div className="text-xs text-text-muted">{doc.taille_ko} Ko — {new Date(doc.date_upload || '').toLocaleDateString('fr-FR')}</div>
                </div>
                <CheckCircle size={16} className="text-success-500 flex-shrink-0" />
              </div>
            ))}
          </div>
          </div>
        </div>
      )}
    </div>
  );
}
