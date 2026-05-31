// src/pages/candidat/ResultatEcritPage.jsx
// Page visible par le candidat pour consulter son résultat d'épreuve écrite
import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import API from '../../api/axios';
import { CheckCircle, XCircle, AlertCircle, Trophy, ArrowRight, Download } from 'lucide-react';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';

export default function ResultatEcritPage() {
  const { user } = useAuth();
  const [resultats, setResultats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchResultats();
  }, []);

  const fetchResultats = async () => {
    try {
      // Fetch all dossiers for the current candidate
      const { data } = await API.get('/dossiers/');
      const dossiersData = data.results || data;

      // Filter dossiers that have final statuses (post-exam) and are officially published
      const dossiersAvecResultat = dossiersData.filter((d) =>
        ['ADMIS_FINAL', 'RECALE_FINAL', 'ABSENT_ECRIT'].includes(d.statut) &&
        d.statut_epreuve === 'RESULTATS_PUBLIES'
      );

      setResultats(dossiersAvecResultat);
    } catch (err) {
      setError("Impossible de charger vos résultats.");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20">
        <div className="spinner" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto mt-12 p-6 bg-red-50 rounded-xl border border-red-100 text-center text-red-700">
        {error}
      </div>
    );
  }

  if (resultats.length === 0) {
    return (
      <div className="max-w-2xl mx-auto mt-12 text-center">
        <div className="bg-white rounded-2xl p-12 shadow-sm border border-gray-100">
          <AlertCircle className="mx-auto h-16 w-16 text-gray-300 mb-4" />
          <h2 className="text-xl font-bold text-gray-900 mb-2">
            Aucun résultat disponible
          </h2>
          <p className="text-gray-500 text-sm">
            Les résultats de l'épreuve écrite n'ont pas encore été publiés,
            ou vous n'avez pas participé à une épreuve.
          </p>
          <Link
            to="/mes-dossiers"
            className="inline-flex items-center gap-2 mt-6 text-blue-600 font-medium text-sm hover:text-blue-800"
          >
            Voir mes dossiers <ArrowRight size={16} />
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-8 pb-12">
      <div>
        <h1 className="text-2xl font-black text-gray-900 tracking-tight">
          Résultats d'épreuve écrite
        </h1>
        <p className="text-gray-500 text-sm mt-1">
          Consultez le résultat de vos épreuves écrites ci-dessous.
        </p>
      </div>

      {resultats.map((dossier) => (
        <ResultCard key={dossier.id} dossier={dossier} />
      ))}
    </div>
  );
}

function ResultCard({ dossier }) {
  const statut = dossier.statut;

  if (statut === 'ADMIS_FINAL') {
    return (
      <div className="bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50 rounded-2xl border border-green-200 shadow-sm overflow-hidden">
        {/* Success banner */}
        <div className="bg-green-600 px-6 py-4 flex items-center gap-3">
          <div className="bg-white/20 p-2 rounded-full">
            <Trophy className="text-white" size={24} />
          </div>
          <div>
            <h2 className="text-white font-bold text-lg">
              Félicitations ! Vous êtes admis(e) à l'écrit
            </h2>
            <p className="text-green-100 text-sm">
              {dossier.filiere_nom || dossier.filiere?.nom}
            </p>
          </div>
        </div>

        <div className="p-6 space-y-5">
          {/* Animated check */}
          <div className="flex justify-center py-4">
            <div className="relative">
              <div className="absolute inset-0 bg-green-400/20 rounded-full animate-ping" />
              <CheckCircle className="relative text-green-600" size={64} />
            </div>
          </div>

          {/* Result details */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-white/80 p-4 rounded-xl text-center border border-green-100">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                Note épreuve
              </div>
              <div className="text-2xl font-black text-gray-900">
                {dossier.note_ecrite != null
                  ? parseFloat(dossier.note_ecrite).toFixed(2)
                  : '—'}
              </div>
              <div className="text-xs text-gray-400">/{dossier.note_sur || 20}</div>
            </div>

            <div className="bg-white/80 p-4 rounded-xl text-center border border-green-100">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                Rang final
              </div>
              <div className="text-2xl font-black text-gray-900">
                {dossier.rang_final ? `${dossier.rang_final}ème` : '—'}
              </div>
            </div>

            <div className="bg-white/80 p-4 rounded-xl text-center border border-green-100">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                Score global
              </div>
              <div className="text-2xl font-black text-gray-900">
                {dossier.score_final != null
                  ? parseFloat(dossier.score_final).toFixed(2)
                  : '—'}
              </div>
              <div className="text-xs text-gray-400">/20</div>
            </div>
          </div>

          {/* Next steps - Oral exam details */}
          <div className="bg-white/60 p-5 rounded-xl border border-green-100 space-y-4">
            <h3 className="font-bold text-green-800 text-base">📋 Convocation — Épreuve Orale</h3>
            
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="bg-blue-50 p-3 rounded-lg border border-blue-100 text-center">
                <div className="text-xs font-semibold text-blue-400 uppercase mb-1">📅 Date</div>
                <div className="text-sm font-bold text-blue-900">
                  {dossier.date_oral 
                    ? new Date(dossier.date_oral).toLocaleDateString('fr-FR', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
                    : 'À préciser'}
                </div>
              </div>
              <div className="bg-purple-50 p-3 rounded-lg border border-purple-100 text-center">
                <div className="text-xs font-semibold text-purple-400 uppercase mb-1">⏰ Heure</div>
                <div className="text-sm font-bold text-purple-900">
                  {dossier.heure_oral || '09:00'}
                </div>
              </div>
              <div className="bg-amber-50 p-3 rounded-lg border border-amber-100 text-center">
                <div className="text-xs font-semibold text-amber-500 uppercase mb-1">📍 Lieu</div>
                <div className="text-sm font-bold text-amber-900">
                  {dossier.lieu_oral || 'ENSA Béni Mellal'}
                </div>
              </div>
            </div>

            <p className="text-xs text-red-600 font-semibold text-center">
              ⚠️ Toute absence non justifiée sera considérée comme un désistement définitif.
            </p>

            <div className="bg-green-50 p-3 rounded-lg border border-green-200 text-sm text-gray-600">
              <p className="font-semibold text-green-800 mb-1">Documents à présenter :</p>
              <ul className="list-disc list-inside space-y-0.5 text-xs">
                <li>Convocation imprimée (téléchargeable ci-dessous)</li>
                <li>Carte d'identité nationale (CIN) originale</li>
                <li>Copie certifiée conforme du baccalauréat</li>
              </ul>
            </div>

            <button
              onClick={async () => {
                try {
                  const response = await API.get(`/notifications/convocation/${dossier.id}/`, {
                    responseType: 'blob'
                  });
                  const url = window.URL.createObjectURL(new Blob([response.data]));
                  const link = document.createElement('a');
                  link.href = url;
                  link.setAttribute('download', `convocation_oral_ENSA_BM_${dossier.id}.pdf`);
                  document.body.appendChild(link);
                  link.click();
                  link.remove();
                  window.URL.revokeObjectURL(url);
                  toast.success('Convocation téléchargée !');
                } catch (err) {
                  toast.error('Erreur lors du téléchargement');
                }
              }}
              className="w-full bg-gradient-to-r from-green-600 to-emerald-600 text-white py-3 rounded-xl font-bold text-sm hover:from-green-700 hover:to-emerald-700 transition-all shadow-md shadow-green-200 flex items-center justify-center gap-2"
            >
              <Download size={18} /> Télécharger ma convocation (PDF)
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (statut === 'RECALE_FINAL') {
    return (
      <div className="bg-gradient-to-br from-red-50 via-rose-50 to-pink-50 rounded-2xl border border-red-200 shadow-sm overflow-hidden">
        <div className="bg-red-600/90 px-6 py-4">
          <h2 className="text-white font-bold text-lg">
            Résultat de l'épreuve écrite
          </h2>
          <p className="text-red-100 text-sm">
            {dossier.filiere_nom || dossier.filiere?.nom}
          </p>
        </div>

        <div className="p-6 space-y-5">
          <div className="flex justify-center py-3">
            <XCircle className="text-red-400" size={56} />
          </div>

          <p className="text-center text-gray-700 text-sm max-w-md mx-auto leading-relaxed">
            Nous avons le regret de vous informer que votre résultat à
            l'épreuve écrite ne vous permet pas d'accéder au cycle demandé
            cette année.
          </p>

          <div className="grid grid-cols-2 gap-4 max-w-sm mx-auto">
            <div className="bg-white/80 p-4 rounded-xl text-center border border-red-100">
              <div className="text-xs font-semibold text-gray-500 uppercase mb-1">
                Note obtenue
              </div>
              <div className="text-xl font-black text-red-700">
                {dossier.note_ecrite != null
                  ? parseFloat(dossier.note_ecrite).toFixed(2)
                  : '—'}
              </div>
              <div className="text-xs text-gray-400">/{dossier.note_sur || 20}</div>
            </div>
            <div className="bg-white/80 p-4 rounded-xl text-center border border-red-100">
              <div className="text-xs font-semibold text-gray-500 uppercase mb-1">
                Seuil requis
              </div>
              <div className="text-xl font-black text-gray-600">
                {dossier.seuil_admission != null
                  ? parseFloat(dossier.seuil_admission).toFixed(2)
                  : '—'}
              </div>
              <div className="text-xs text-gray-400">/{dossier.note_sur || 20}</div>
            </div>
          </div>

          <div className="bg-white/60 p-4 rounded-xl border border-red-100 text-center">
            <p className="text-sm text-gray-600 leading-relaxed">
              Vous pouvez tenter à nouveau votre chance lors de la prochaine
              session. L'ENSA Béni Mellal vous souhaite bonne continuation
              dans vos études.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // ABSENT
  return (
    <div className="bg-gray-50 rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
      <div className="bg-gray-500 px-6 py-4">
        <h2 className="text-white font-bold text-lg">Épreuve écrite</h2>
        <p className="text-gray-200 text-sm">
          {dossier.filiere_nom || dossier.filiere?.nom}
        </p>
      </div>

      <div className="p-6 text-center space-y-4">
        <AlertCircle className="mx-auto text-gray-400" size={56} />
        <h3 className="font-bold text-gray-800 text-lg">
          Vous étiez absent(e) à l'épreuve
        </h3>
        <p className="text-sm text-gray-500 max-w-md mx-auto leading-relaxed">
          Aucune note n'a été enregistrée pour vous lors de cette épreuve
          écrite. Si vous pensez qu'il s'agit d'une erreur, veuillez
          contacter le service de scolarité.
        </p>
      </div>
    </div>
  );
}
