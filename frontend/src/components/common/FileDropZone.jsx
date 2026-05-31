// src/components/common/FileDropZone.jsx
// Zone de drop réutilisable avec états : vide, chargement, uploadé, erreur
import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, CheckCircle, AlertCircle, X, FileText, Image } from 'lucide-react';

export default function FileDropZone({
  label,
  accept,
  maxSize = 10 * 1024 * 1024,
  onFileSelected,
  onFileSelect,
  file,
  onRemove,
  error: externalError,
  hint,
}) {

  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    if (rejectedFiles.length > 0) {
      return;
    }
    if (acceptedFiles.length > 0) {
      onFileSelected?.(acceptedFiles[0]);
      onFileSelect?.(acceptedFiles[0]);
    }
  }, [onFileSelected, onFileSelect]);

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept: accept || {
      'application/pdf': ['.pdf'],
      'image/*': ['.png', '.jpg', '.jpeg'],
    },
    maxFiles: 1,
    maxSize,
  });

  const hasFile = !!file;
  const hasError = externalError || fileRejections.length > 0;
  const rejectionMessage = fileRejections[0]?.errors[0]?.message;

  // Déterminer l'icône du type de fichier
  const getFileIcon = () => {
    if (!file) return null;
    if (file.type?.startsWith('image/')) return <Image size={18} className="text-primary-500" />;
    return <FileText size={18} className="text-primary-500" />;
  };

  return (
    <div>
      {label && <label className="label">{label}</label>}

      {/* Zone uploadée — afficher le fichier */}
      {hasFile ? (
        <div className={`
          rounded-lg border-2 p-4 transition-all duration-200
          ${hasError ? 'border-danger-500 bg-danger-50' : 'border-success-500 bg-success-50'}
        `}>
          <div className="flex items-center gap-3">
            <div className={`
              w-10 h-10 rounded-lg flex items-center justify-center
              ${hasError ? 'bg-danger-100' : 'bg-success-100'}
            `}>
              {hasError ? <AlertCircle size={20} className="text-danger-500" /> : <CheckCircle size={20} className="text-success-500" />}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                {getFileIcon()}
                <span className="text-sm font-medium truncate">{file.name}</span>
              </div>
              <span className="text-xs text-text-muted">
                {(file.size / 1024).toFixed(0)} Ko
              </span>
            </div>
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); onRemove?.(); }}
              className="p-1.5 rounded-md hover:bg-white/50 text-text-muted hover:text-danger-500 transition-colors"
              aria-label="Supprimer le fichier"
            >
              <X size={16} />
            </button>
          </div>
        </div>
      ) : (
        /* Zone de drop vide */
        <div
          {...getRootProps()}
          className={`
            rounded-lg border-2 border-dashed p-6 text-center cursor-pointer
            transition-all duration-200
            ${isDragActive
              ? 'border-primary-500 bg-primary-50'
              : hasError
                ? 'border-danger-500 bg-danger-50'
                : 'border-border bg-white hover:border-primary-300 hover:bg-primary-50/30'
            }
          `}
        >
          <input {...getInputProps()} />
          <div className={`
            w-10 h-10 rounded-lg flex items-center justify-center mx-auto mb-3
            ${isDragActive ? 'bg-primary-100' : 'bg-gray-100'}
          `}>
            <Upload size={20} className={isDragActive ? 'text-primary-500' : 'text-text-muted'} />
          </div>
          <p className="text-sm font-medium text-text-secondary">
            {isDragActive
              ? 'Déposez le fichier ici...'
              : 'Glissez-déposez ou cliquez pour sélectionner'}
          </p>
          {hint && (
            <p className="text-xs text-text-muted mt-1">{hint}</p>
          )}
        </div>
      )}

      {/* Message d'erreur */}
      {(hasError || rejectionMessage) && (
        <p className="error-text mt-1">
          {externalError || rejectionMessage || 'Fichier invalide'}
        </p>
      )}
    </div>
  );
}
