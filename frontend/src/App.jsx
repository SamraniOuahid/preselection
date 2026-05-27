// src/App.jsx
// Routes complètes avec React Router — ENSA BM Présélection
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

// Layouts
import LandingLayout from './layouts/LandingLayout';
import PublicLayout from './layouts/PublicLayout';
import DashboardLayout from './layouts/DashboardLayout';

// Pages publiques
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';

// Pages candidat
import MesDossiers from './pages/candidat/MesDossiers';
import CandidaturePage from './pages/candidat/CandidaturePage';
import SuiviDossierPage from './pages/candidat/SuiviDossierPage';
import ProfilPage from './pages/candidat/ProfilPage';
import ModifierDossierPage from './pages/candidat/ModifierDossierPage';

// Pages responsable / admin
import DashboardPage from './pages/responsable/DashboardPage';
import DossiersPage from './pages/responsable/DossiersPage';
import DetailDossierPage from './pages/responsable/DetailDossierPage';

// Pages admin existantes (conservées)
import GestionFilieres from './pages/admin/GestionFilieres';
import ConfigScoring from './pages/admin/ConfigScoring';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              fontSize: '14px',
              borderRadius: '8px',
              padding: '12px 16px',
            },
          }}
        />

        <Routes>
          {/* ── Landing page publique ── */}
          <Route element={<LandingLayout />}>
            <Route path="/" element={<LandingPage />} />
          </Route>

          {/* ── Auth (login / register) ── */}
          <Route element={<PublicLayout />}>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
          </Route>

          {/* ── Routes protégées (dashboard layout) ── */}
          <Route element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }>
            {/* Candidat */}
            <Route path="/mes-dossiers" element={
              <ProtectedRoute roles={['CANDIDAT']}>
                <MesDossiers />
              </ProtectedRoute>
            } />
            <Route path="/nouveau-dossier" element={
              <ProtectedRoute roles={['CANDIDAT']}>
                <CandidaturePage />
              </ProtectedRoute>
            } />
            <Route path="/profil" element={
              <ProtectedRoute roles={['CANDIDAT']}>
                <ProfilPage />
              </ProtectedRoute>
            } />
            <Route path="/dossier/:id" element={
              <ProtectedRoute roles={['CANDIDAT']}>
                <SuiviDossierPage />
              </ProtectedRoute>
            } />
            <Route path="/dossier/:id/modifier" element={
              <ProtectedRoute roles={['CANDIDAT']}>
                <ModifierDossierPage />
              </ProtectedRoute>
            } />

            {/* Responsable / Admin */}
            <Route path="/dashboard" element={
              <ProtectedRoute roles={['RESPONSABLE', 'ADMIN']}>
                <DashboardPage />
              </ProtectedRoute>
            } />
            <Route path="/dossiers" element={
              <ProtectedRoute roles={['RESPONSABLE', 'ADMIN']}>
                <DossiersPage />
              </ProtectedRoute>
            } />
            <Route path="/admin/dossier/:id" element={
              <ProtectedRoute roles={['RESPONSABLE', 'ADMIN']}>
                <DetailDossierPage />
              </ProtectedRoute>
            } />
            <Route path="/filieres" element={
              <ProtectedRoute roles={['ADMIN']}>
                <GestionFilieres />
              </ProtectedRoute>
            } />
            <Route path="/config-scoring" element={
              <ProtectedRoute roles={['ADMIN']}>
                <ConfigScoring />
              </ProtectedRoute>
            } />
          </Route>

          {/* Redirect par défaut */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
