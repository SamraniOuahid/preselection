// src/components/epreuve/ImportExcelWizard.jsx
import { useState } from 'react';
import { Upload, FileSpreadsheet, Eye, CheckCircle, AlertTriangle, ChevronRight, XCircle } from 'lucide-react';
import { previsualiserExcel, importerNotesExcel } from '../../api/epreuves';
import toast from 'react-hot-toast';
import FileDropZone from '../common/FileDropZone';

export default function ImportExcelWizard({ epreuveId, onImportSuccess }) {
  const [step, setStep] = useState(1);
  const [file, setFile] = useState(null);
  const [colCin, setColCin] = useState('A');
  const [colNote, setColNote] = useState('B');
  const [ligneDebut, setLigneDebut] = useState(2);
  
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [rapport, setRapport] = useState(null);

  const columns = Array.from({ length: 10 }, (_, i) => String.fromCharCode(65 + i)); // A to J

  const handlePreview = async () => {
    if (!file) {
      toast.error("Veuillez sélectionner un fichier.");
      return;
    }
    setLoading(true);
    const formData = new FormData();
    formData.append('fichier', file);
    formData.append('colonne_cin', colCin);
    formData.append('colonne_note', colNote);
    formData.append('ligne_debut', ligneDebut);

    try {
      const data = await previsualiserExcel(epreuveId, formData);
      if (data.succes) {
        setPreview(data);
        setStep(2);
      } else {
        toast.error(data.message || "Erreur lors de la prévisualisation");
      }
    } catch (error) {
      toast.error(error.response?.data?.error || "Erreur réseau lors de la prévisualisation");
    } finally {
      setLoading(false);
    }
  };

  const handleImport = async () => {
    setLoading(true);
    const formData = new FormData();
    formData.append('fichier', file);
    formData.append('colonne_cin', colCin);
    formData.append('colonne_note', colNote);
    formData.append('ligne_debut', ligneDebut);

    try {
      const data = await importerNotesExcel(epreuveId, formData);
      setRapport(data);
      setStep(3);
      if (data.succes) {
        toast.success(`${data.importees} notes importées avec succès.`);
        onImportSuccess();
      } else {
         toast.error("L'importation a rencontré des erreurs.");
      }
    } catch (error) {
       if(error.response?.data?.succes !== undefined) {
           setRapport(error.response.data);
           setStep(3);
       } else {
           toast.error(error.response?.data?.error || "Erreur lors de l'importation.");
       }
    } finally {
      setLoading(false);
    }
  };

  const resetWizard = () => {
    setStep(1);
    setFile(null);
    setPreview(null);
    setRapport(null);
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      {/* Stepper Header */}
      <div className="bg-gray-50 p-4 border-b border-gray-100 flex items-center justify-between">
        <h3 className="font-bold text-gray-900 flex items-center gap-2">
          <FileSpreadsheet className="text-green-600" size={20} />
          Assistant d'Import Excel
        </h3>
        <div className="flex items-center gap-2 text-sm">
          <span className={`px-2 py-1 rounded-full ${step >= 1 ? 'bg-blue-100 text-blue-700 font-semibold' : 'text-gray-400'}`}>1. Fichier</span>
          <ChevronRight size={16} className="text-gray-300" />
          <span className={`px-2 py-1 rounded-full ${step >= 2 ? 'bg-blue-100 text-blue-700 font-semibold' : 'text-gray-400'}`}>2. Aperçu</span>
          <ChevronRight size={16} className="text-gray-300" />
          <span className={`px-2 py-1 rounded-full ${step >= 3 ? 'bg-blue-100 text-blue-700 font-semibold' : 'text-gray-400'}`}>3. Résultat</span>
        </div>
      </div>

      <div className="p-6">
        {/* STEP 1: Upload and Config */}
        {step === 1 && (
          <div className="space-y-6">
            <FileDropZone
              file={file}
              onRemove={() => setFile(null)}
              onFileSelect={setFile}
              accept={{
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
                'application/vnd.ms-excel': ['.xls']
              }}
              label="Glissez le fichier Excel ici ou cliquez pour parcourir"
              maxSize={10 * 1024 * 1024}
            />

            <div className="grid grid-cols-3 gap-4 bg-gray-50 p-4 rounded-lg border border-gray-100">
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">Colonne CIN</label>
                <select value={colCin} onChange={(e) => setColCin(e.target.value)} className="w-full text-sm border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500">
                  {columns.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">Colonne Note</label>
                <select value={colNote} onChange={(e) => setColNote(e.target.value)} className="w-full text-sm border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500">
                  {columns.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">Ligne de début</label>
                <input type="number" min="1" value={ligneDebut} onChange={(e) => setLigneDebut(e.target.value)} className="w-full text-sm border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500" />
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={handlePreview}
                disabled={!file || loading}
                className="px-5 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
              >
                {loading ? <span className="animate-spin text-xl leading-none">⟳</span> : <Eye size={18} />}
                Prévisualiser
              </button>
            </div>
          </div>
        )}

        {/* STEP 2: Preview */}
        {step === 2 && preview && (
          <div className="space-y-4">
            <div className="bg-blue-50 text-blue-800 p-3 rounded-lg text-sm border border-blue-100">
              <strong>{preview.total_lignes} lignes de données détectées.</strong> Voici un aperçu des 5 premières lignes. Vérifiez que les colonnes correspondent bien.
            </div>

            <div className="overflow-x-auto border border-gray-200 rounded-lg">
              <table className="min-w-full divide-y divide-gray-200 text-sm">
                <thead className="bg-gray-50">
                  <tr>
                     <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-100 border-r border-gray-200 w-12">#</th>
                    {preview.headers.map((h, i) => (
                      <th key={i} className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider
                        ${String.fromCharCode(65+i) === colCin ? 'bg-yellow-100 text-yellow-800' : ''}
                        ${String.fromCharCode(65+i) === colNote ? 'bg-green-100 text-green-800' : 'text-gray-500'}
                      `}>
                         {String.fromCharCode(65+i)} - {h}
                         {String.fromCharCode(65+i) === colCin && " (CIN)"}
                         {String.fromCharCode(65+i) === colNote && " (Note)"}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {preview.apercu.map((row, i) => (
                    <tr key={i} className="hover:bg-gray-50">
                      <td className="px-3 py-2 text-gray-400 bg-gray-50 border-r border-gray-200">{ligneDebut + i}</td>
                      {row.map((cell, j) => (
                        <td key={j} className={`px-4 py-2 whitespace-nowrap
                           ${String.fromCharCode(65+j) === colCin ? 'font-medium bg-yellow-50' : ''}
                           ${String.fromCharCode(65+j) === colNote ? 'font-bold text-green-700 bg-green-50' : 'text-gray-600'}
                        `}>
                          {cell}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex justify-between pt-4 border-t border-gray-100 mt-6">
              <button onClick={() => setStep(1)} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg font-medium">Retour</button>
              <button onClick={handleImport} disabled={loading} className="px-5 py-2 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 flex items-center gap-2 disabled:opacity-50">
                {loading ? <span className="animate-spin text-xl leading-none">⟳</span> : <Upload size={18} />}
                Lancer l'importation définitive
              </button>
            </div>
          </div>
        )}

        {/* STEP 3: Result */}
        {step === 3 && rapport && (
          <div className="space-y-6">
             <div className={`p-4 rounded-lg border flex items-start gap-4 ${rapport.succes ? 'bg-green-50 border-green-200 text-green-800' : 'bg-red-50 border-red-200 text-red-800'}`}>
                {rapport.succes ? <CheckCircle className="mt-1" size={24} /> : <XCircle className="mt-1" size={24} />}
                <div>
                   <h4 className="font-bold text-lg">{rapport.succes ? "Importation réussie" : "Échec de l'importation"}</h4>
                   <p className="mt-1">
                      {rapport.importees} notes ont été importées sur un total de {rapport.total_lignes} lignes traitées.
                   </p>
                </div>
             </div>

             <div className="grid grid-cols-3 gap-4">
               <div className="bg-gray-50 p-4 rounded-lg text-center border border-gray-100">
                  <div className="text-3xl font-black text-green-600">{rapport.nb_admis}</div>
                  <div className="text-xs text-gray-500 font-medium uppercase mt-1">Nouveaux Admis</div>
               </div>
               <div className="bg-gray-50 p-4 rounded-lg text-center border border-gray-100">
                  <div className="text-3xl font-black text-red-600">{rapport.nb_recales}</div>
                  <div className="text-xs text-gray-500 font-medium uppercase mt-1">Recalés</div>
               </div>
               <div className="bg-gray-50 p-4 rounded-lg text-center border border-gray-100">
                  <div className="text-3xl font-black text-gray-600">{rapport.nb_absents}</div>
                  <div className="text-xs text-gray-500 font-medium uppercase mt-1">Absents</div>
               </div>
             </div>

            {rapport.erreurs && rapport.erreurs.length > 0 && (
              <div className="mt-6">
                <h5 className="font-bold text-red-700 flex items-center gap-2 mb-2">
                   <AlertTriangle size={18} /> {rapport.erreurs.length} Erreurs (lignes ignorées)
                </h5>
                <div className="max-h-48 overflow-y-auto border border-red-200 rounded-lg">
                   <table className="min-w-full text-sm">
                      <thead className="bg-red-50 text-red-800 sticky top-0">
                         <tr>
                            <th className="px-3 py-2 text-left">Ligne</th>
                            <th className="px-3 py-2 text-left">CIN</th>
                            <th className="px-3 py-2 text-left">Valeur</th>
                            <th className="px-3 py-2 text-left">Problème</th>
                         </tr>
                      </thead>
                      <tbody className="divide-y divide-red-100 bg-white">
                         {rapport.erreurs.map((err, idx) => (
                            <tr key={idx}>
                               <td className="px-3 py-2 text-gray-500">#{err.ligne}</td>
                               <td className="px-3 py-2 font-medium">{err.cin || '-'}</td>
                               <td className="px-3 py-2">{err.valeur || '-'}</td>
                               <td className="px-3 py-2 text-red-600">{err.message}</td>
                            </tr>
                         ))}
                      </tbody>
                   </table>
                </div>
              </div>
            )}

            {rapport.non_trouves && rapport.non_trouves.length > 0 && (
              <div className="mt-6">
                <h5 className="font-bold text-yellow-700 flex items-center gap-2 mb-2">
                   <AlertTriangle size={18} /> {rapport.non_trouves.length} CIN non trouvés
                </h5>
                <p className="text-xs text-gray-600 mb-2">Ces candidats n'ont pas de dossier présélectionné dans cette filière.</p>
                <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                   {rapport.non_trouves.map((nt, idx) => (
                      <span key={idx} className="bg-white px-2 py-1 rounded text-xs border border-yellow-300 font-mono text-yellow-800 shadow-sm">
                         L{nt.ligne}: {nt.cin}
                      </span>
                   ))}
                </div>
              </div>
            )}

            <div className="flex justify-center pt-6 border-t border-gray-100 mt-6">
               <button onClick={resetWizard} className="px-6 py-2 bg-gray-900 text-white rounded-lg font-medium hover:bg-black">
                  Fermer
               </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
