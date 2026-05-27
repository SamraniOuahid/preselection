// src/components/common/ConfirmModal.jsx
// Modal de confirmation réutilisable avec backdrop et animation
import { AlertTriangle, X } from 'lucide-react';

export default function ConfirmModal({
  isOpen,
  onClose,
  onConfirm,
  title = 'Confirmation',
  message = 'Êtes-vous sûr de vouloir continuer ?',
  confirmLabel = 'Confirmer',
  cancelLabel = 'Annuler',
  variant = 'primary',
  loading = false,
  icon,
}) {
  if (!isOpen) return null;

  const variantClasses = {
    primary: 'btn-primary',
    danger: 'btn-danger',
    success: 'btn-success',
    warning: 'btn-accent',
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-[2px]"
        onClick={!loading ? onClose : undefined}
      />

      {/* Modal */}
      <div className="card p-6 w-full max-w-md relative z-10 animate-scale-in">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={`
              w-10 h-10 rounded-lg flex items-center justify-center
              ${variant === 'danger' ? 'bg-danger-50 text-danger-500'
                : variant === 'warning' ? 'bg-warning-50 text-warning-600'
                : variant === 'success' ? 'bg-success-50 text-success-500'
                : 'bg-primary-50 text-primary-700'}
            `}>
              {icon || <AlertTriangle size={20} />}
            </div>
            <h3 className="text-base font-bold text-text-primary">{title}</h3>
          </div>
          <button
            onClick={onClose}
            disabled={loading}
            className="p-1 rounded-md hover:bg-gray-100 text-text-muted transition-colors"
            aria-label="Fermer"
          >
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <p className="text-sm text-text-secondary mb-6 leading-relaxed">{message}</p>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3">
          <button
            className="btn btn-outline btn-sm"
            onClick={onClose}
            disabled={loading}
          >
            {cancelLabel}
          </button>
          <button
            className={`btn btn-sm ${variantClasses[variant] || 'btn-primary'}`}
            onClick={onConfirm}
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Traitement...
              </>
            ) : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
