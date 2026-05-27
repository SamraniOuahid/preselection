// src/pages/auth/LoginPage.jsx
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Mail, Lock, Eye, EyeOff, LogIn, ArrowRight } from 'lucide-react';
import AlertBanner from '../../components/common/AlertBanner';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [serverError, setServerError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const { register, handleSubmit, formState: { errors } } = useForm();

  const onSubmit = async (data) => {
    setServerError('');
    setLoading(true);
    try {
      const user = await login(data.email, data.password);
      if (user.role === 'CANDIDAT') navigate('/mes-dossiers');
      else navigate('/dashboard');
    } catch (err) {
      if (!err.response) {
        setServerError(
          'Impossible de joindre le serveur. Vérifiez que le backend tourne sur http://localhost:8000 et le frontend via npm run dev.'
        );
      } else if (err.response.data?.detail) {
        setServerError(err.response.data.detail);
      } else if (typeof err.response.data === 'object') {
        const messages = Object.entries(err.response.data)
          .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
          .join(' | ');
        setServerError(messages || 'Email ou mot de passe incorrect.');
      } else {
        setServerError('Email ou mot de passe incorrect.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ensa-auth-page animate-fade-in">
      <h2 className="ensa-auth-title">Connexion à votre espace</h2>
      <p className="ensa-auth-subtitle">Accédez à votre dossier de présélection</p>

      {serverError && (
        <AlertBanner variant="error" className="mb-5">{serverError}</AlertBanner>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="ensa-auth-form">
        <div className="ensa-auth-field">
          <label className="label" htmlFor="login-email">Adresse email</label>
          <div className="ensa-input-icon-wrap">
            <Mail size={16} className="ensa-input-icon" />
            <input
              id="login-email"
              type="email"
              className={`input ${errors.email ? 'input-error' : ''}`}
              placeholder="votre.email@exemple.com"
              {...register('email', {
                required: "L'email est obligatoire",
                pattern: { value: /^\S+@\S+$/i, message: 'Email invalide' },
              })}
            />
          </div>
          {errors.email && <p className="error-text">{errors.email.message}</p>}
        </div>

        <div className="ensa-auth-field">
          <div className="ensa-auth-field-row">
            <label className="label mb-0" htmlFor="login-password">Mot de passe</label>
            <a href="#" className="ensa-auth-forgot">Mot de passe oublié ?</a>
          </div>
          <div className="ensa-input-icon-wrap">
            <Lock size={16} className="ensa-input-icon" />
            <input
              id="login-password"
              type={showPassword ? 'text' : 'password'}
              className={`input ensa-input-right ${errors.password ? 'input-error' : ''}`}
              placeholder="••••••••"
              {...register('password', { required: 'Le mot de passe est obligatoire' })}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="ensa-input-toggle"
              aria-label={showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'}
            >
              {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
          {errors.password && <p className="error-text">{errors.password.message}</p>}
        </div>

        <button type="submit" className="btn btn-primary btn-lg w-full" disabled={loading}>
          {loading ? (
            <>
              <span className="ensa-spinner" />
              Connexion...
            </>
          ) : (
            <>
              <LogIn size={18} />
              Se connecter
            </>
          )}
        </button>
      </form>

      <div className="ensa-auth-separator">
        <div className="ensa-auth-separator-line" />
        <span className="ensa-auth-separator-text">Pas encore de compte ?</span>
        <div className="ensa-auth-separator-line" />
      </div>

      <Link to="/register" className="btn btn-outline w-full">
        Créer un compte
        <ArrowRight size={16} />
      </Link>
    </div>
  );
}
