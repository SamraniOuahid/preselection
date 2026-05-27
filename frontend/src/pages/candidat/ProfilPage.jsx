// src/pages/candidat/ProfilPage.jsx
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useAuth } from '../../context/AuthContext';
import API from '../../api/axios';
import AlertBanner from '../../components/common/AlertBanner';
import { User, Phone, MapPin, Calendar, Lock, Save } from 'lucide-react';
import toast from 'react-hot-toast';

export default function ProfilPage() {
  const { user, updateUser } = useAuth();
  const profil = user?.profil;
  const [serverError, setServerError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [pwdLoading, setPwdLoading] = useState(false);

  const { register, handleSubmit, formState: { errors } } = useForm({
    defaultValues: {
      nom: profil?.nom || '',
      prenom: profil?.prenom || '',
      telephone: profil?.telephone || '',
      adresse: profil?.adresse || '',
      date_naissance: profil?.date_naissance || '',
    },
  });

  const pwdForm = useForm();

  const onSaveProfil = async (data) => {
    setServerError('');
    setSuccess('');
    setLoading(true);
    try {
      const { data: updated } = await API.put('/auth/me/', data);
      updateUser(updated);
      setSuccess('Profil mis à jour avec succès.');
      toast.success('Profil enregistré');
    } catch (err) {
      const msg = err.response?.data?.error
        || Object.values(err.response?.data || {}).flat().join(' ')
        || 'Erreur lors de la mise à jour.';
      setServerError(typeof msg === 'string' ? msg : 'Erreur lors de la mise à jour.');
    } finally {
      setLoading(false);
    }
  };

  const onChangePassword = async (data) => {
    if (data.new_password !== data.new_password_confirm) {
      pwdForm.setError('new_password_confirm', { message: 'Les mots de passe ne correspondent pas.' });
      return;
    }
    setPwdLoading(true);
    try {
      await API.post('/auth/change-password/', {
        old_password: data.old_password,
        new_password: data.new_password,
      });
      toast.success('Mot de passe modifié');
      pwdForm.reset();
    } catch (err) {
      const d = err.response?.data;
      toast.error(d?.old_password?.[0] || d?.new_password?.[0] || d?.detail || 'Erreur mot de passe');
    } finally {
      setPwdLoading(false);
    }
  };

  if (!profil) {
    return (
      <div className="ensa-page animate-fade-in">
        <AlertBanner variant="warning">Seuls les candidats ont un profil modifiable.</AlertBanner>
      </div>
    );
  }

  return (
    <div className="ensa-page ensa-page-narrow animate-fade-in">
      <div className="ensa-page-header">
        <h1 className="ensa-page-title">Mon profil</h1>
        <p className="ensa-page-subtitle">
          Modifiez vos informations personnelles. L&apos;email ({user.email}) et le CIN ({user.cin}) ne sont pas modifiables ici.
        </p>
      </div>

      {serverError && <AlertBanner variant="error" className="ensa-mb-5">{serverError}</AlertBanner>}
      {success && <AlertBanner variant="success" className="ensa-mb-5">{success}</AlertBanner>}

      <form onSubmit={handleSubmit(onSaveProfil)} className="ensa-form-section ensa-mb-5">
        <h2 className="ensa-section-title ensa-flex-center ensa-gap-2">
          <User size={18} /> Informations personnelles
        </h2>

        <div className="ensa-form-grid">
          <div>
            <label className="label">Nom</label>
            <input className={`input ${errors.nom ? 'input-error' : ''}`} {...register('nom', { required: 'Obligatoire' })} />
            {errors.nom && <p className="error-text">{errors.nom.message}</p>}
          </div>
          <div>
            <label className="label">Prénom</label>
            <input className={`input ${errors.prenom ? 'input-error' : ''}`} {...register('prenom', { required: 'Obligatoire' })} />
            {errors.prenom && <p className="error-text">{errors.prenom.message}</p>}
          </div>
          <div>
            <label className="label">Téléphone</label>
            <div className="ensa-input-icon-wrap">
              <Phone size={16} className="ensa-input-icon" />
              <input className="input" placeholder="06XXXXXXXX" {...register('telephone')} />
            </div>
          </div>
          <div>
            <label className="label">Date de naissance</label>
            <div className="ensa-input-icon-wrap">
              <Calendar size={16} className="ensa-input-icon" />
              <input type="date" className="input" {...register('date_naissance')} />
            </div>
          </div>
        </div>
        <div className="ensa-mt-4">
          <label className="label">Adresse</label>
          <div className="ensa-input-icon-wrap">
            <MapPin size={16} className="ensa-input-icon" style={{ top: 14, transform: 'none' }} />
            <textarea className="input" rows={3} placeholder="Ville, adresse complète..." {...register('adresse')} />
          </div>
        </div>

        <div className="ensa-mt-4">
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? <span className="ensa-spinner" /> : <Save size={16} />}
            Enregistrer le profil
          </button>
        </div>
      </form>

      <form onSubmit={pwdForm.handleSubmit(onChangePassword)} className="ensa-form-section">
        <h2 className="ensa-section-title ensa-flex-center ensa-gap-2">
          <Lock size={18} /> Changer le mot de passe
        </h2>
        <div className="ensa-auth-form">
          <div>
            <label className="label">Ancien mot de passe</label>
            <input type="password" className="input" {...pwdForm.register('old_password', { required: true })} />
          </div>
          <div className="ensa-form-grid">
            <div>
              <label className="label">Nouveau mot de passe</label>
              <input type="password" className="input" {...pwdForm.register('new_password', { required: true, minLength: 8 })} />
            </div>
            <div>
              <label className="label">Confirmer</label>
              <input type="password" className="input" {...pwdForm.register('new_password_confirm', { required: true })} />
              {pwdForm.formState.errors.new_password_confirm && (
                <p className="error-text">{pwdForm.formState.errors.new_password_confirm.message}</p>
              )}
            </div>
          </div>
          <button type="submit" className="btn btn-outline" disabled={pwdLoading}>
            {pwdLoading ? <span className="ensa-spinner ensa-spinner-dark" /> : <Lock size={16} />}
            Mettre à jour le mot de passe
          </button>
        </div>
      </form>
    </div>
  );
}
