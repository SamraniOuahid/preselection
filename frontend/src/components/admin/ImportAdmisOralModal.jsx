// src/components/admin/ImportAdmisOralModal.jsx
import { useState, useRef, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { X, Upload, FileSpreadsheet, CheckCircle, AlertTriangle, Loader2, Info } from 'lucide-react';
import { importerAdmisOral } from '../../api/oral';
import toast from 'react-hot-toast';

/* ── types ──────────────────────────────────────────────────── */
// resultat: { traites, convoques, pdfs_generes, ignores, erreurs[] }

export default function ImportAdmisOralModal({ epreuve, isOpen, onClose, onImportDone }) {
  const [fichier, setFichier] = useState(null);
  const [etat, setEtat] = useState('idle'); // idle | loading | succes | erreur
  const [resultat, setResultat] = useState(null);
  const [erreurServeur, setErreurServeur] = useState('');
  const [isDragOver, setIsDragOver] = useState(false);
  const inputRef = useRef(null);

  /* ── handlers fichier ───────────────────────────────────────── */
  const validerFichier = (f) => {
    if (!f) return false;
    const ext = f.name.split('.').pop().toLowerCase();
    if (!['xlsx', 'xls', 'csv'].includes(ext)) {
      toast.error('Format non supporté. Utilisez .xlsx, .xls ou .csv');
      return false;
    }
    if (f.size > 10 * 1024 * 1024) {
      toast.error('Fichier trop volumineux (max 10 Mo)');
      return false;
    }
    return true;
  };

  const handleFileChange = (e) => {
    const f = e.target.files?.[0];
    if (validerFichier(f)) { setFichier(f); setEtat('idle'); setResultat(null); }
  };

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragOver(false);
    const f = e.dataTransfer.files?.[0];
    if (validerFichier(f)) { setFichier(f); setEtat('idle'); setResultat(null); }
  }, []);

  /* ── import ─────────────────────────────────────────────────── */
  const handleImport = async () => {
    if (!fichier) return;
    setEtat('loading');
    setErreurServeur('');
    try {
      const res = await importerAdmisOral(epreuve.id, fichier);
      setResultat(res);
      setEtat('succes');
      if (res.convoques > 0) {
        toast.success(`${res.convoques} candidat(s) convoqué(s) avec succès`);
        onImportDone?.();
      } else {
        toast.error('Aucun candidat convoqué. Vérifiez les erreurs ci-dessous.');
      }
    } catch (err) {
      const msg = err.response?.data?.error
        || err.response?.data?.detail
        || 'Erreur lors de l\'import.';
      setErreurServeur(msg);
      setEtat('erreur');
    }
  };

  /* ── reset & close ──────────────────────────────────────────── */
  const handleClose = () => {
    setFichier(null);
    setEtat('idle');
    setResultat(null);
    setErreurServeur('');
    onClose();
  };

  if (!isOpen) return null;

  const ext = fichier?.name.split('.').pop().toLowerCase();
  const iconeExt = ext === 'csv' ? '📄' : '📊';

  return createPortal(
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center p-4"
      style={{ backgroundColor: 'rgba(0,0,0,0.6)' }}
      onClick={(e) => { if (e.target === e.currentTarget) handleClose(); }}
    >
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg flex flex-col overflow-hidden">

        {/* ── En-tête ── */}
        <div className="flex justify-between items-center px-6 py-4 border-b bg-gradient-to-r from-[#1B3A6B] to-[#2E86C1]">
          <div className="flex items-center gap-3 text-white">
            <FileSpreadsheet size={22} />
            <div>
              <h2 className="font-bold text-base leading-tight">Importer les admis à l'oral</h2>
              <p className="text-blue-100 text-xs mt-0.5 opacity-90 truncate max-w-[280px]">
                {epreuve?.nom}
              </p>
            </div>
          </div>
          <button onClick={handleClose} className="text-white/70 hover:text-white transition-colors p-1 rounded">
            <X size={20} />
          </button>
        </div>

        {/* ── Corps ── */}
        <div className="p-6 space-y-5">

          {/* Notice colonnes */}
          <div className="flex items-start gap-3 bg-blue-50 border border-blue-100 rounded-xl p-4 text-sm text-blue-800">
            <Info size={16} className="flex-shrink-0 mt-0.5 text-blue-500" />
            <div>
              <p className="font-semibold mb-1">Format du fichier attendu</p>
              <p className="text-blue-700 leading-relaxed">
                Le fichier doit contenir une colonne nommée{' '}
                <code className="bg-blue-100 px-1 rounded font-mono text-xs">cne</code>,{' '}
                <code className="bg-blue-100 px-1 rounded font-mono text-xs">code_massar</code> ou{' '}
                <code className="bg-blue-100 px-1 rounded font-mono text-xs">id</code>{' '}
                (insensible à la casse). La date et le lieu seront repris automatiquement depuis la filière.
              </p>
            </div>
          </div>

          {/* Zone de dépôt */}
          <div
            className={`relative border-2 border-dashed rounded-xl transition-all cursor-pointer
              ${isDragOver ? 'border-blue-500 bg-blue-50' : fichier ? 'border-green-400 bg-green-50' : 'border-gray-300 bg-gray-50 hover:border-blue-400 hover:bg-blue-50'}`}
            onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
            onDragLeave={() => setIsDragOver(false)}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".xlsx,.xls,.csv"
              className="sr-only"
              onChange={handleFileChange}
            />

            <div className="flex flex-col items-center justify-center py-8 px-4 text-center">
              {fichier ? (
                <>
                  <span className="text-4xl mb-2">{iconeExt}</span>
                  <p className="font-semibold text-gray-800 text-sm">{fichier.name}</p>
                  <p className="text-gray-500 text-xs mt-1">
                    {(fichier.size / 1024).toFixed(1)} Ko — Cliquez pour changer
                  </p>
                </>
              ) : (
                <>
                  <Upload size={36} className={`mb-3 ${isDragOver ? 'text-blue-500' : 'text-gray-400'}`} />
                  <p className="font-semibold text-gray-700 text-sm">
                    {isDragOver ? 'Déposez le fichier ici' : 'Glissez-déposez votre fichier'}
                  </p>
                  <p className="text-gray-400 text-xs mt-1">ou cliquez pour sélectionner</p>
                  <p className="text-gray-400 text-xs mt-3">
                    Formats : .xlsx · .xls · .csv — Max 10 Mo
                  </p>
                </>
              )}
            </div>
          </div>

          {/* ── Résultat succès ── */}
          {etat === 'succes' && resultat && (
            <div className="rounded-xl border border-green-200 bg-green-50 p-4 space-y-3">
              <div className="flex items-center gap-2 text-green-800 font-bold text-sm">
                <CheckCircle size={18} className="text-green-600" />
                Import terminé
              </div>
              <div className="grid grid-cols-2 gap-3 text-center text-sm">
                <Stat label="Lignes traitées"   value={resultat.traites}      color="blue" />
                <Stat label="Convoqués"          value={resultat.convoques}    color="green" />
                <Stat label="PDFs générés"       value={resultat.pdfs_generes} color="purple" />
                <Stat label="Ignorés / Erreurs"  value={resultat.ignores}      color="orange" />
              </div>
              {resultat.erreurs?.length > 0 && (
                <details className="mt-2">
                  <summary className="text-xs font-semibold text-orange-700 cursor-pointer hover:underline">
                    ⚠ {resultat.erreurs.length} avertissement(s) — cliquez pour voir
                  </summary>
                  <ul className="mt-2 max-h-40 overflow-y-auto space-y-1">
                    {resultat.erreurs.map((e, i) => (
                      <li key={i} className="text-xs text-orange-800 bg-orange-50 border border-orange-100 rounded px-2 py-1">
                        {e}
                      </li>
                    ))}
                  </ul>
                </details>
              )}
            </div>
          )}

          {/* ── Résultat erreur serveur ── */}
          {etat === 'erreur' && erreurServeur && (
            <div className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
              <AlertTriangle size={18} className="flex-shrink-0 mt-0.5 text-red-500" />
              <div>
                <p className="font-semibold mb-1">Erreur lors de l'import</p>
                <p className="leading-relaxed">{erreurServeur}</p>
              </div>
            </div>
          )}

        </div>

        {/* ── Pied ── */}
        <div className="px-6 py-4 border-t bg-gray-50 flex justify-end gap-3">
          <button
            onClick={handleClose}
            className="px-4 py-2 text-sm font-semibold text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            {etat === 'succes' ? 'Fermer' : 'Annuler'}
          </button>
          {etat !== 'succes' && (
            <button
              onClick={handleImport}
              disabled={!fichier || etat === 'loading'}
              className="px-6 py-2 text-sm font-bold text-white bg-[#1B3A6B] hover:bg-[#142D52] rounded-lg transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 min-w-[160px] justify-center"
            >
              {etat === 'loading' ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Import en cours…
                </>
              ) : (
                <>
                  <Upload size={16} />
                  Lancer l'import
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>,
    document.body
  );
}

/* ── sous-composant Stat ── */
function Stat({ label, value, color }) {
  const colors = {
    blue:   'bg-blue-50   text-blue-700',
    green:  'bg-green-50  text-green-700',
    purple: 'bg-purple-50 text-purple-700',
    orange: 'bg-orange-50 text-orange-700',
  };
  return (
    <div className={`rounded-lg p-3 ${colors[color]}`}>
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-xs font-medium opacity-80 mt-0.5">{label}</div>
    </div>
  );
}
