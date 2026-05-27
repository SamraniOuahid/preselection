// src/components/common/StatusBadge.jsx
// Badge coloré affichant le statut d'un dossier avec icône Lucide
import {
  FileEdit, Loader, AlertCircle, Search,
  XCircle, Clock, CheckCircle, Ban
} from 'lucide-react';

const STATUS_CONFIG = {
  BROUILLON:      { label: 'Brouillon',       className: 'badge-brouillon',       Icon: FileEdit },
  EN_TRAITEMENT:  { label: 'En traitement',   className: 'badge-en_traitement',   Icon: Loader },
  INCOMPLET:      { label: 'Incomplet',       className: 'badge-incomplet',       Icon: AlertCircle },
  SUSPECT:        { label: 'Suspect',          className: 'badge-suspect',         Icon: Search },
  REJETE_AUTO:    { label: 'Rejeté (auto)',    className: 'badge-rejete_auto',     Icon: XCircle },
  EN_ATTENTE:     { label: 'En attente',       className: 'badge-en_attente',      Icon: Clock },
  PRESELECTIONNE: { label: 'Présélectionné',   className: 'badge-preselectionne',  Icon: CheckCircle },
  REJETE_FINAL:   { label: 'Rejeté (final)',   className: 'badge-rejete_final',    Icon: Ban },
};

export default function StatusBadge({ statut, size = 'md' }) {
  const config = STATUS_CONFIG[statut] || { label: statut, className: '', Icon: AlertCircle };
  const { Icon } = config;
  const iconSize = size === 'sm' ? 12 : 14;

  return (
    <span className={`badge ${config.className} ${size === 'sm' ? 'text-[11px] px-2 py-0.5' : ''}`}>
      <Icon size={iconSize} />
      {config.label}
    </span>
  );
}
