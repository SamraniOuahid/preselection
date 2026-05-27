// src/components/common/AlertBanner.jsx
// Bannière d'alerte sobre avec variantes info/success/warning/error
import { Info, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';

const VARIANTS = {
  info: {
    bg: 'bg-primary-50',
    border: 'border-primary-100',
    text: 'text-primary-700',
    Icon: Info,
  },
  success: {
    bg: 'bg-success-50',
    border: 'border-success-100',
    text: 'text-success-700',
    Icon: CheckCircle,
  },
  warning: {
    bg: 'bg-warning-50',
    border: 'border-warning-100',
    text: 'text-warning-700',
    Icon: AlertTriangle,
  },
  error: {
    bg: 'bg-danger-50',
    border: 'border-danger-100',
    text: 'text-danger-700',
    Icon: XCircle,
  },
};

export default function AlertBanner({ variant = 'info', title, children, className = '' }) {
  const config = VARIANTS[variant] || VARIANTS.info;
  const { Icon } = config;

  return (
    <div className={`
      rounded-lg border p-4 flex gap-3
      ${config.bg} ${config.border} ${className}
    `}>
      <Icon size={18} className={`${config.text} mt-0.5 flex-shrink-0`} />
      <div className="flex-1 min-w-0">
        {title && (
          <div className={`text-sm font-semibold mb-1 ${config.text}`}>{title}</div>
        )}
        <div className={`text-sm ${config.text} opacity-90`}>{children}</div>
      </div>
    </div>
  );
}
