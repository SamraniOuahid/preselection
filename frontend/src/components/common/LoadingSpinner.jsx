// src/components/common/LoadingSpinner.jsx
// Spinner de chargement sobre et réutilisable

export default function LoadingSpinner({ size = 'md', text, className = '' }) {
  const sizes = {
    sm: 'w-5 h-5 border-2',
    md: 'w-8 h-8 border-[3px]',
    lg: 'w-12 h-12 border-[3px]',
  };

  return (
    <div className={`flex flex-col items-center justify-center gap-3 ${className}`}>
      <div
        className={`
          ${sizes[size]}
          border-primary-100 border-t-primary-700
          rounded-full animate-spin
        `}
      />
      {text && (
        <span className="text-sm text-text-muted font-medium">{text}</span>
      )}
    </div>
  );
}
