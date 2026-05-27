// src/components/common/EmptyState.jsx
// État vide avec illustration SVG sobre et bouton d'action
import { FolderOpen } from 'lucide-react';

export default function EmptyState({
  title = 'Aucune donnée',
  description = '',
  action,
  actionLabel,
  icon,
}) {
  const IconComponent = icon || FolderOpen;

  return (
    <div className="card p-12 text-center animate-fade-in">
      {/* Illustration SVG sobre */}
      <div className="w-20 h-20 mx-auto mb-5 rounded-2xl bg-primary-50 flex items-center justify-center">
        <IconComponent size={36} className="text-primary-300" />
      </div>

      <h3 className="text-base font-semibold text-text-primary mb-2">
        {title}
      </h3>

      {description && (
        <p className="text-sm text-text-muted max-w-sm mx-auto mb-5 leading-relaxed">
          {description}
        </p>
      )}

      {action && actionLabel && (
        <button className="btn btn-primary" onClick={action}>
          {actionLabel}
        </button>
      )}
    </div>
  );
}
