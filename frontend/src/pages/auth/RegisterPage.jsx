// src/pages/auth/RegisterPage.jsx
// Inscription en 2 étapes avec stepper visuel et validation
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  Mail, Lock, Eye, EyeOff, CreditCard, User, Phone,
  Calendar, ArrowLeft, ArrowRight, Check, UserPlus
} from 'lucide-react';
import AlertBanner from '../../components/common/AlertBanner';

export default function RegisterPage() {
  const { register: registerUser } = useAuth();
  const navigate = useNavigate();
  const [serverError, setServerError] = useState('');
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const { register, handleSubmit, watch, formState: { errors }, trigger } = useForm({
    mode: 'onChange',
  });

  const password = watch('password', '');

  // Règles de validation visuelles du mot de passe
  const passwordRules = [
    { label: 'Minimum 8 caractères', valid: password.length >= 8 },
    { label: 'Au moins une majuscule', valid: /[A-Z]/.test(password) },
    { label: 'Au moins un chiffre', valid: /[0-9]/.test(password) },
  ];

  // Valider l'étape 1 avant de passer à l'étape 2
  const handleNextStep = async () => {
    const valid = await trigger(['email', 'cin', 'password', 'password_confirm']);
    if (valid) setStep(2);
  };

  const onSubmit = async (data) => {
    setServerError('');
    setLoading(true);
    try {
      await registerUser(data);
      navigate('/mes-dossiers');
    } catch (err) {
      const errors = err.response?.data;
      if (typeof errors === 'object') {
        const messages = Object.entries(errors)
          .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
          .join(' | ');
        setServerError(messages);
      } else {
        setServerError("Erreur lors de l'inscription. Veuillez réessayer.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold text-center text-text-primary font-display">Créer un compte</h2>
        <p className="text-center text-sm text-text-muted mt-1.5">Inscription en 2 étapes simples</p>
      </div>

      <div className="ensa-stepper">
        {[
          { num: 1, label: 'Compte' },
          { num: 2, label: 'Informations' },
        ].map((s, i) => (
          <div key={s.num} className="flex items-center flex-1">
            <div className="flex items-center gap-2 flex-1">
              <div className={`
                w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-200
                ${step > s.num ? 'bg-success-500 text-white'
                  : step === s.num ? 'bg-primary-700 text-white'
                  : 'bg-gray-100 text-text-muted'}
              `}>
                {step > s.num ? <Check size={14} /> : s.num}
              </div>
              <span className={`text-xs font-medium ${
                step >= s.num ? 'text-text-primary' : 'text-text-muted'
              }`}>
                {s.label}
              </span>
            </div>
            {i === 0 && (
              <div className={`w-12 h-0.5 mx-2 rounded ${step > 1 ? 'bg-success-500' : 'bg-gray-200'}`} />
            )}
          </div>
        ))}
      </div>

      {serverError && (
        <AlertBanner variant="error">{serverError}</AlertBanner>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* ── Étape 1 : Compte ── */}
        {step === 1 && (
          <div className="flex flex-col gap-4 animate-fade-in">
            {/* Email */}
            <div className="animate-fade-in" style={{ animationDelay: '0.15s' }}>
              <label className="label" htmlFor="reg-email">Adresse email</label>
              <div className="relative">
                <Mail size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-text-muted" />
                <input
                  id="reg-email"
                  type="email"
                  className={`input input-with-icon-left ${errors.email ? 'input-error' : ''} transition-all duration-200 focus:scale-[1.01]`}
                  placeholder="votre.email@exemple.com"
                  {...register('email', {
                    required: "L'email est obligatoire",
                    pattern: { value: /^\S+@\S+$/i, message: 'Email invalide' },
                  })}
                />
              </div>
              {errors.email && <p className="error-text">{errors.email.message}</p>}
            </div>

            {/* CIN */}
            <div className="animate-fade-in" style={{ animationDelay: '0.2s' }}>
              <label className="label" htmlFor="reg-cin">CIN (Carte d'Identité Nationale)</label>
              <div className="relative">
                <CreditCard size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-text-muted" />
                <input
                  id="reg-cin"
                  className={`input input-with-icon-left font-mono ${errors.cin ? 'input-error' : ''} transition-all duration-200 focus:scale-[1.01]`}
                  placeholder="BJ123456"
                  {...register('cin', {
                    required: 'Le CIN est obligatoire',
                    pattern: {
                      value: /^[A-Z]{1,2}\d{5,6}$/,
                      message: 'Format CIN invalide (ex: BJ123456)',
                    },
                  })}
                />
              </div>
              {errors.cin && <p className="error-text">{errors.cin.message}</p>}
            </div>

            {/* Mot de passe */}
            <div className="animate-fade-in" style={{ animationDelay: '0.25s' }}>
              <label className="label" htmlFor="reg-password">Mot de passe</label>
              <div className="relative">
                <Lock size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-text-muted" />
                <input
                  id="reg-password"
                  type={showPassword ? 'text' : 'password'}
                  className={`input input-with-icon-left input-with-icon-right ${errors.password ? 'input-error' : ''} transition-all duration-200 focus:scale-[1.01]`}
                  placeholder="••••••••"
                  {...register('password', {
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
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary transition-colors"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              {errors.password && <p className="error-text">{errors.password.message}</p>}

              {/* Règles visuelles */}
              {password && (
                <div className="mt-2 space-y-1 animate-fade-in">
                  {passwordRules.map((rule) => (
                    <div key={rule.label} className={`flex items-center gap-2 text-xs ${
                      rule.valid ? 'text-success-600' : 'text-text-muted'
                    }`}>
                      <Check size={12} className={rule.valid ? 'text-success-500' : 'text-gray-300'} />
                      {rule.label}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Confirmer mot de passe */}
            <div className="animate-fade-in" style={{ animationDelay: '0.3s' }}>
              <label className="label" htmlFor="reg-confirm">Confirmer le mot de passe</label>
              <div className="relative">
                <Lock size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-text-muted" />
                <input
                  id="reg-confirm"
                  type={showConfirm ? 'text' : 'password'}
                  className={`input input-with-icon-left input-with-icon-right ${errors.password_confirm ? 'input-error' : ''} transition-all duration-200 focus:scale-[1.01]`}
                  placeholder="••••••••"
                  {...register('password_confirm', {
                    required: 'Obligatoire',
                    validate: (val) => val === password || 'Les mots de passe ne correspondent pas',
                  })}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirm(!showConfirm)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary transition-colors"
                >
                  {showConfirm ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              {errors.password_confirm && <p className="error-text">{errors.password_confirm.message}</p>}
            </div>

            <div className="animate-fade-in" style={{ animationDelay: '0.35s' }}>
              <button
                type="button"
                className="btn btn-primary btn-lg w-full mt-2 transition-transform duration-200 active:scale-95"
                onClick={handleNextStep}
              >
                Suivant
                <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}

        {/* ── Étape 2 : Informations personnelles ── */}
        {step === 2 && (
          <div className="flex flex-col gap-4 animate-fade-in">
            {/* Nom + Prénom */}
            <div className="grid grid-cols-2 gap-3 animate-fade-in" style={{ animationDelay: '0.15s' }}>
              <div>
                <label className="label" htmlFor="reg-nom">Nom</label>
                <div className="relative">
                  <User size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-text-muted" />
                  <input
                    id="reg-nom"
                    className={`input input-with-icon-left ${errors.nom ? 'input-error' : ''} transition-all duration-200 focus:scale-[1.01]`}
                    placeholder="SAMRANI"
                    {...register('nom', { required: 'Obligatoire' })}
                  />
                </div>
                {errors.nom && <p className="error-text">{errors.nom.message}</p>}
              </div>
              <div>
                <label className="label" htmlFor="reg-prenom">Prénom</label>
                <div className="relative">
                  <User size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-text-muted" />
                  <input
                    id="reg-prenom"
                    className={`input input-with-icon-left ${errors.prenom ? 'input-error' : ''} transition-all duration-200 focus:scale-[1.01]`}
                    placeholder="Ouahid"
                    {...register('prenom', { required: 'Obligatoire' })}
                  />
                </div>
                {errors.prenom && <p className="error-text">{errors.prenom.message}</p>}
              </div>
            </div>

            {/* Téléphone */}
            <div className="animate-fade-in" style={{ animationDelay: '0.2s' }}>
              <label className="label" htmlFor="reg-tel">Téléphone</label>
              <div className="relative">
                <Phone size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-text-muted" />
                <input
                  id="reg-tel"
                  type="tel"
                  className={`input input-with-icon-left ${errors.telephone ? 'input-error' : ''} transition-all duration-200 focus:scale-[1.01]`}
                  placeholder="06 12 34 56 78"
                  {...register('telephone', {
                    required: 'Obligatoire',
                    pattern: {
                      value: /^0[5-7]\d{8}$/,
                      message: 'Numéro marocain invalide (06/07/05 + 8 chiffres)',
                    },
                  })}
                />
              </div>
              {errors.telephone && <p className="error-text">{errors.telephone.message}</p>}
            </div>

            {/* Date de naissance */}
            <div className="animate-fade-in" style={{ animationDelay: '0.25s' }}>
              <label className="label" htmlFor="reg-dob">Date de naissance</label>
              <div className="relative">
                <Calendar size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-text-muted" />
                <input
                  id="reg-dob"
                  type="date"
                  className={`input input-with-icon-left ${errors.date_naissance ? 'input-error' : ''} transition-all duration-200 focus:scale-[1.01]`}
                  {...register('date_naissance', { required: 'Obligatoire' })}
                />
              </div>
              {errors.date_naissance && <p className="error-text">{errors.date_naissance.message}</p>}
            </div>

            {/* Boutons */}
            <div className="flex gap-3 mt-2 animate-fade-in" style={{ animationDelay: '0.3s' }}>
              <button
                type="button"
                className="btn btn-outline flex-1 transition-transform duration-200 active:scale-95"
                onClick={() => setStep(1)}
              >
                <ArrowLeft size={16} />
                Précédent
              </button>
              <button
                type="submit"
                className="btn btn-primary btn-lg flex-1 transition-transform duration-200 active:scale-95"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Inscription...
                  </>
                ) : (
                  <>
                    <UserPlus size={18} />
                    S'inscrire
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </form>

      {/* Lien connexion */}
      <div className="text-center mt-5 animate-fade-in" style={{ animationDelay: '0.4s' }}>
        <span className="text-sm text-text-muted">Déjà un compte ? </span>
        <Link to="/login" className="text-sm text-primary-500 hover:text-primary-700 font-medium no-underline transition-colors">
          Se connecter
        </Link>
      </div>
    </div>
  );
}
