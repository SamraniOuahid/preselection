// src/pages/candidat/ConvocationPage.jsx
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Calendar, Clock, MapPin, Hash, Download, ArrowLeft, CheckSquare } from 'lucide-react';
import { getMaConvocation, downloadConvocationPdf } from '../../api/oral';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import toast from 'react-hot-toast';

export default function ConvocationPage() {
  const [convocation, setConvocation] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMaConvocation()
      .then(data => setConvocation(data))
      .catch(err => {
        if (err.response?.status !== 404) {
          toast.error('Erreur lors du chargement de votre convocation');
        }
      })
      .finally(() => setLoading(false));
  }, []);

  const handleDownload = async () => {
    try {
      await downloadConvocationPdf(convocation.id);
      toast.success('Convocation téléchargée avec succès');
    } catch (err) {
      toast.error('Erreur lors du téléchargement');
    }
  };

  if (loading) return <LoadingSpinner size="lg" text="Chargement..." className="py-20" />;

  if (!convocation) {
    return (
      <div className="ensa-page animate-fade-in text-center py-20">
        <h2 className="text-xl font-bold text-gray-800 mb-4">Aucune convocation disponible</h2>
        <p className="text-gray-600 mb-6">Vous n'avez pas de convocation à l'entretien oral pour le moment.</p>
        <Link to="/mes-dossiers" className="btn btn-primary"><ArrowLeft size={16} /> Retour à mes dossiers</Link>
      </div>
    );
  }

  const dateStr = convocation.date_decision ? new Date(convocation.date_decision).toLocaleDateString('fr-FR', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }) : 'Date à confirmer';

  return (
    <div className="ensa-page animate-fade-in max-w-3xl mx-auto">
      <div className="ensa-page-header">
        <nav className="ensa-breadcrumb">
          <Link to="/mes-dossiers"><ArrowLeft size={14} /> Mes dossiers</Link>
          <span>/</span>
          <span className="ensa-breadcrumb-current">Ma Convocation</span>
        </nav>
      </div>

      <div className="bg-gradient-to-br from-[#1B3A6B] to-[#2E86C1] rounded-2xl shadow-xl overflow-hidden relative mb-8">
        <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
          <Calendar size={180} />
        </div>
        
        <div className="p-8 relative z-10 text-white">
          <div className="flex items-center gap-4 mb-6">
            <div className="w-16 h-16 rounded-full bg-white/20 flex items-center justify-center backdrop-blur-sm">
              <Calendar size={32} className="text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">Convocation à l'entretien oral</h1>
              <p className="text-blue-100 mt-1 opacity-90">Concours d'accès — ENSA Béni Mellal</p>
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20 grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div className="flex items-start gap-4">
              <div className="mt-1"><Calendar size={20} className="text-blue-200" /></div>
              <div>
                <p className="text-blue-200 text-sm font-medium">Date</p>
                <p className="font-bold text-lg">{dateStr}</p>
              </div>
            </div>
            
            <div className="flex items-start gap-4">
              <div className="mt-1"><Clock size={20} className="text-blue-200" /></div>
              <div>
                <p className="text-blue-200 text-sm font-medium">Heure</p>
                <p className="font-bold text-lg">{convocation.heure_passage ? convocation.heure_passage.substring(0, 5) : '—'}</p>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <div className="mt-1"><MapPin size={20} className="text-blue-200" /></div>
              <div>
                <p className="text-blue-200 text-sm font-medium">Lieu</p>
                <p className="font-bold text-lg">Salle des conférences — ENSA BM</p>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <div className="mt-1"><Hash size={20} className="text-blue-200" /></div>
              <div>
                <p className="text-blue-200 text-sm font-medium">N° de passage</p>
                <p className="font-bold text-lg">{convocation.numero_passage || '—'}</p>
              </div>
            </div>
          </div>

          <div className="mt-8 flex justify-center">
            <button onClick={handleDownload} className="btn bg-white text-[#1B3A6B] hover:bg-gray-100 border-none shadow-lg px-8 py-3 text-lg font-bold flex items-center gap-3">
              <Download size={20} /> Télécharger ma convocation (PDF)
            </button>
          </div>
        </div>
      </div>

      <div className="bg-[#FFF7ED] border border-[#E67E22] rounded-xl p-6 shadow-sm">
        <h3 className="text-lg font-bold text-[#92400E] flex items-center gap-2 mb-4">
          <CheckSquare size={20} /> Documents à apporter impérativement :
        </h3>
        <ul className="space-y-3">
          {[
            "Baccalauréat (original + copie certifiée)",
            "Diplôme obtenu (original)",
            "Relevés de notes (toutes années)",
            "CIN originale (recto-verso)",
            "2 photos d'identité récentes",
            "Cette convocation imprimée"
          ].map((item, idx) => (
            <li key={idx} className="flex items-start gap-3 text-[#92400E]">
              <div className="w-5 h-5 rounded bg-[#E67E22] text-white flex items-center justify-center flex-shrink-0 mt-0.5">✓</div>
              <span className="font-medium">{item}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="mt-6 text-center text-gray-500 text-sm">
        <p>Présentez-vous 15 minutes avant l'heure indiquée.</p>
        <p>Tout retard ou document manquant peut entraîner l'exclusion de l'entretien.</p>
      </div>
    </div>
  );
}
