// src/components/common/StatusBadge.jsx
// Badge coloré affichant le statut d'un dossier — Version candidat (opaque)
// Les statuts internes sont masqués au candidat via un mapping sécurisé.
import {
  FileEdit, Loader, AlertCircle,
  XCircle, Clock, CheckCircle, Ban
} from 'lucide-react';

/**
 * Mapping INTERNE → label candidat.
 * Le candidat ne doit JAMAIS voir les statuts techniques bruts.
 * - SUSPECT est affiché comme "En cours d'examen" (identique à EN_TRAITEMENT).
 * - REJETE_AUTO est affiché comme "Dossier non retenu" (sans mention de rejet automatique).
 */
const STATUS_CONFIG = {
  BROUILLON:      { label: 'Brouillon',             className: 'badge-brouillon',       Icon: FileEdit },
  EN_TRAITEMENT:  { label: 'En cours d\'examen',    className: 'badge-en_traitement',   Icon: Loader },
  INCOMPLET:      { label: 'Incomplet',             className: 'badge-incomplet',       Icon: AlertCircle },
  SUSPECT:        { label: 'En cours d\'examen',    className: 'badge-en_traitement',   Icon: Loader },
  REJETE_AUTO:    { label: 'Dossier non retenu',    className: 'badge-rejete_auto',     Icon: XCircle },
  EN_ATTENTE:     { label: 'En attente de décision',className: 'badge-en_attente',      Icon: Clock },
  PRESELECTIONNE: { label: 'Présélectionné',        className: 'badge-preselectionne',  Icon: CheckCircle },
  REJETE_FINAL:   { label: 'Dossier non retenu',    className: 'badge-rejete_final',    Icon: Ban },
  ADMIS_FINAL:    { label: 'Admis',                 className: 'badge-preselectionne',  Icon: CheckCircle },
  RECALE_FINAL:   { label: 'Recalé',                className: 'badge-rejete_final',    Icon: Ban },
  ABSENT_ECRIT:   { label: 'Absent (écrit)',        className: 'badge-en_attente',      Icon: Clock },
};

export default function StatusBadge({ statut, size = 'md' }) {
  const config = STATUS_CONFIG[statut] || { label: 'En cours de traitement', className: 'badge-en_traitement', Icon: Loader };
  const { Icon } = config;
  const iconSize = size === 'sm' ? 12 : 14;

  return (
    <span className={`badge ${config.className} ${size === 'sm' ? 'text-[11px] px-2 py-0.5' : ''}`}>
      <Icon size={iconSize} />
      {config.label}
    </span>
  );
}
