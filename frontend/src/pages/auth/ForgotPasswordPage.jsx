// src/pages/auth/ForgotPasswordPage.jsx
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Link } from 'react-router-dom';
import API from '../../api/axios';
import { Mail, ArrowLeft, Send, CheckCircle } from 'lucide-react';
import AlertBanner from '../../components/common/AlertBanner';

export default function ForgotPasswordPage() {
  const [loading, setLoading] = useState(false);
  const [serverError, setServerError] = useState('');
  const [isSuccess, setIsSuccess] = useState(false);

  const { register, handleSubmit, formState: { errors } } = useForm({
    mode: 'onChange',
  });

  const onSubmit = async (data) => {
    setServerError('');
    setLoading(true);
    try {
      await API.post('/auth/password-reset/', { email: data.email });
      setIsSuccess(true);
    } catch (err) {
      setServerError(err.response?.data?.error || "Une erreur est survenue. Veuillez réessayer.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto space-y-6 animate-fade-in pt-8">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-text-primary font-display">Mot de passe oublié</h2>
        <p className="text-sm text-text-muted mt-1.5">
          Entrez votre adresse email pour recevoir un lien de réinitialisation.
        </p>
      </div>

      {serverError && (
        <AlertBanner variant="error">{serverError}</AlertBanner>
      )}

      {isSuccess ? (
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm text-center space-y-4 animate-fade-in">
          <div className="w-16 h-16 bg-success-50 rounded-full flex items-center justify-center text-success-500 mx-auto mb-2">
            <CheckCircle size={32} />
          </div>
          <h3 className="text-lg font-bold text-gray-900">E-mail envoyé</h3>
          <p className="text-gray-600 text-sm">
            Si cette adresse correspond à un compte, un lien de réinitialisation a été envoyé. 
            Veuillez vérifier votre boîte de réception (et vos spams).
          </p>
          <div className="pt-4">
            <Link to="/login" className="btn btn-outline w-full justify-center">
              <ArrowLeft size={16} className="mr-2" /> Retour à la connexion
            </Link>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="animate-fade-in">
            <label className="label" htmlFor="reset-email">Adresse email</label>
            <div className="relative">
              <Mail size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-text-muted" />
              <input
                id="reset-email"
                type="email"
                className={`input input-with-icon-left ${errors.email ? 'input-error' : ''} transition-all duration-200`}
                placeholder="votre.email@exemple.com"
                {...register('email', {
                  required: "L'email est obligatoire",
                  pattern: { value: /^\S+@\S+$/i, message: 'Email invalide' },
                })}
              />
            </div>
            {errors.email && <p className="error-text">{errors.email.message}</p>}
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-lg w-full mt-2 transition-transform duration-200 active:scale-95"
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Envoi en cours...
              </>
            ) : (
              <>
                <Send size={18} className="mr-2" />
                Recevoir le lien
              </>
            )}
          </button>

          <div className="text-center mt-6">
            <Link to="/login" className="text-sm text-text-muted hover:text-primary-600 font-medium transition-colors flex items-center justify-center">
              <ArrowLeft size={16} className="mr-1.5" /> Retour à la connexion
            </Link>
          </div>
        </form>
      )}
    </div>
  );
}
