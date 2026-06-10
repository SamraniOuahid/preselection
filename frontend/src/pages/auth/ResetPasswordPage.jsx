// src/pages/auth/ResetPasswordPage.jsx
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useSearchParams, Link, useNavigate } from 'react-router-dom';
import API from '../../api/axios';
import { Lock, Eye, EyeOff, CheckCircle, ArrowRight } from 'lucide-react';
import AlertBanner from '../../components/common/AlertBanner';

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const uid = searchParams.get('uid');
  const token = searchParams.get('token');
  const navigate = useNavigate();

  const [loading, setLoading] = useState(false);
  const [serverError, setServerError] = useState('');
  const [isSuccess, setIsSuccess] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const { register, handleSubmit, watch, formState: { errors } } = useForm({
    mode: 'onChange',
  });

  const newPassword = watch('new_password', '');

  const onSubmit = async (data) => {
    setServerError('');
    setLoading(true);
    try {
      await API.post('/auth/password-reset-confirm/', {
        uid,
        token,
        new_password: data.new_password
      });
      setIsSuccess(true);
    } catch (err) {
      setServerError(err.response?.data?.error || "Le lien est invalide ou a expiré. Veuillez refaire une demande.");
    } finally {
      setLoading(false);
    }
  };

  if (!uid || !token) {
    return (
      <div className="w-full max-w-md mx-auto pt-12">
        <AlertBanner variant="error">Lien de réinitialisation invalide ou incomplet.</AlertBanner>
        <div className="mt-4 text-center">
          <Link to="/forgot-password" className="text-primary-600 font-medium hover:underline">
            Refaire une demande
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-md mx-auto space-y-6 animate-fade-in pt-8">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-text-primary font-display">Nouveau mot de passe</h2>
        <p className="text-sm text-text-muted mt-1.5">
          Veuillez choisir un nouveau mot de passe sécurisé.
        </p>
      </div>

      {serverError && (
        <AlertBanner variant="error">{serverError}</AlertBanner>
      )}

      {isSuccess ? (
        <div className="bg-white p-8 rounded-xl border border-gray-100 shadow-sm text-center space-y-4 animate-fade-in">
          <div className="w-16 h-16 bg-success-50 rounded-full flex items-center justify-center text-success-500 mx-auto mb-2">
            <CheckCircle size={32} />
          </div>
          <h3 className="text-xl font-bold text-gray-900">Mot de passe modifié !</h3>
          <p className="text-gray-600 text-sm">
            Votre mot de passe a été réinitialisé avec succès. Vous pouvez maintenant vous connecter avec votre nouveau mot de passe.
          </p>
          <div className="pt-4">
            <Link to="/login" className="btn btn-primary w-full justify-center">
              Aller à la connexion <ArrowRight size={16} className="ml-2" />
            </Link>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="animate-fade-in">
            <label className="label" htmlFor="new_password">Nouveau mot de passe</label>
            <div className="relative">
              <Lock size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-text-muted" />
              <input
                id="new_password"
                type={showPassword ? 'text' : 'password'}
                className={`input input-with-icon-left input-with-icon-right ${errors.new_password ? 'input-error' : ''} transition-all duration-200`}
                placeholder="••••••••"
                {...register('new_password', {
                  required: 'Obligatoire',
                  minLength: { value: 8, message: 'Minimum 8 caractères' },
                  pattern: {
                    value: /^(?=.*[A-Z])(?=.*\d)/,
                    message: 'Doit contenir une majuscule et un chiffre',
                  },
                })}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary"
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            {errors.new_password && <p className="error-text">{errors.new_password.message}</p>}
          </div>

          <div className="animate-fade-in" style={{ animationDelay: '0.1s' }}>
            <label className="label" htmlFor="confirm_password">Confirmer le mot de passe</label>
            <div className="relative">
              <Lock size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-text-muted" />
              <input
                id="confirm_password"
                type={showConfirm ? 'text' : 'password'}
                className={`input input-with-icon-left input-with-icon-right ${errors.confirm_password ? 'input-error' : ''} transition-all duration-200`}
                placeholder="••••••••"
                {...register('confirm_password', {
                  required: 'Obligatoire',
                  validate: (val) => val === newPassword || 'Les mots de passe ne correspondent pas',
                })}
              />
              <button
                type="button"
                onClick={() => setShowConfirm(!showConfirm)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary"
              >
                {showConfirm ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            {errors.confirm_password && <p className="error-text">{errors.confirm_password.message}</p>}
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-lg w-full mt-2 transition-transform duration-200 active:scale-95"
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Mise à jour...
              </>
            ) : (
              'Réinitialiser le mot de passe'
            )}
          </button>
        </form>
      )}
    </div>
  );
}
