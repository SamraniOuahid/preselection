// src/pages/auth/VerifyEmailPage.jsx
import { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import API from '../../api/axios';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const uid = searchParams.get('uid');
  const token = searchParams.get('token');
  
  const [status, setStatus] = useState('loading'); // 'loading', 'success', 'error'
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (!uid || !token) {
      setStatus('error');
      setMessage("Lien de vérification invalide ou incomplet.");
      return;
    }

    const verifyEmail = async () => {
      try {
        const { data } = await API.post('/auth/verify-email-confirm/', { uid, token });
        setStatus('success');
        setMessage(data.message || "Votre compte a été vérifié avec succès. Vous pouvez maintenant vous connecter.");
      } catch (err) {
        setStatus('error');
        setMessage(err.response?.data?.error || "Le lien de vérification est invalide ou a expiré.");
      }
    };

    verifyEmail();
  }, [uid, token]);

  return (
    <div className="w-full max-w-md mx-auto animate-fade-in pt-12">
      <div className="bg-white p-8 rounded-xl border border-gray-100 shadow-sm text-center">
        
        {status === 'loading' && (
          <div className="flex flex-col items-center space-y-4">
            <Loader2 className="w-12 h-12 text-primary-600 animate-spin" />
            <h2 className="text-xl font-bold text-gray-900 font-display">Vérification en cours</h2>
            <p className="text-gray-500 text-sm">Veuillez patienter pendant que nous vérifions votre compte...</p>
          </div>
        )}

        {status === 'success' && (
          <div className="flex flex-col items-center space-y-4 animate-fade-in">
            <div className="w-16 h-16 bg-success-50 rounded-full flex items-center justify-center text-success-500 mb-2">
              <CheckCircle size={32} />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 font-display">Compte vérifié !</h2>
            <p className="text-gray-600 text-sm">{message}</p>
            <div className="pt-4 w-full">
              <Link to="/login" className="btn btn-primary w-full">
                Se connecter à mon compte
              </Link>
            </div>
          </div>
        )}

        {status === 'error' && (
          <div className="flex flex-col items-center space-y-4 animate-fade-in">
            <div className="w-16 h-16 bg-danger-50 rounded-full flex items-center justify-center text-danger-500 mb-2">
              <XCircle size={32} />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 font-display">Échec de la vérification</h2>
            <p className="text-danger-600 text-sm">{message}</p>
            <div className="pt-4 w-full space-y-3">
              <Link to="/login" className="btn btn-outline w-full">
                Retour à la connexion
              </Link>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
