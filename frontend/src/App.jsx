// src/App.jsx
// Routes complètes avec React Router — ENSA BM Présélection
import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

// Layouts
import LandingLayout from './layouts/LandingLayout';
import PublicLayout from './layouts/PublicLayout';
import DashboardLayout from './layouts/DashboardLayout';

// Pages publiques (Lazy loaded)
const LandingPage = lazy(() => import('./pages/LandingPage'));
const LoginPage = lazy(() => import('./pages/auth/LoginPage'));
const RegisterPage = lazy(() => import('./pages/auth/RegisterPage'));
const VerifyEmailPage = lazy(() => import('./pages/auth/VerifyEmailPage'));
const ForgotPasswordPage = lazy(() => import('./pages/auth/ForgotPasswordPage'));
const ResetPasswordPage = lazy(() => import('./pages/auth/ResetPasswordPage'));

// Pages candidat (Lazy loaded)
const MesDossiers = lazy(() => import('./pages/candidat/MesDossiers'));
const CandidaturePage = lazy(() => import('./pages/candidat/CandidaturePage'));
const SuiviDossierPage = lazy(() => import('./pages/candidat/SuiviDossierPage'));
const ProfilPage = lazy(() => import('./pages/candidat/ProfilPage'));
const ModifierDossierPage = lazy(() => import('./pages/candidat/ModifierDossierPage'));
const NotificationsPage = lazy(() => import('./pages/candidat/NotificationsPage'));

// Pages responsable / admin (Lazy loaded)
const DashboardPage = lazy(() => import('./pages/responsable/DashboardPage'));
const DossiersPage = lazy(() => import('./pages/responsable/DossiersPage'));
const DetailDossierPage = lazy(() => import('./pages/responsable/DetailDossierPage'));

// Pages admin existantes (Lazy loaded)
const GestionFilieres = lazy(() => import('./pages/admin/GestionFilieres'));
const ConfigScoring = lazy(() => import('./pages/admin/ConfigScoring'));
const AdminAnalyticsDashboard = lazy(() => import('./pages/responsable/AdminAnalyticsDashboard'));

// Pages épreuves écrites (Lazy loaded)
const EpreuvesPage = lazy(() => import('./pages/admin/EpreuvesPage'));
const DetailEpreuvePage = lazy(() => import('./pages/admin/DetailEpreuvePage'));
const ResultatsEpreuvePage = lazy(() => import('./pages/admin/ResultatsEpreuvePage'));
const ResultatEcritPage = lazy(() => import('./pages/candidat/ResultatEcritPage'));

// Pages épreuves orales (Lazy loaded)
const EpreuveOralePage = lazy(() => import('./pages/admin/EpreuveOralePage'));
const DetailEpreuveOralePage = lazy(() => import('./pages/admin/DetailEpreuveOralePage'));
const ConvocationPage = lazy(() => import('./pages/candidat/ConvocationPage'));

const PageLoader = () => (
  <div className="min-h-screen flex flex-col items-center justify-center bg-[#F4F6F9]">
    <div className="spinner mb-4"></div>
    <p className="text-sm font-semibold text-[#5D6D7E]">Chargement de la page...</p>
  </div>
);

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

        <Suspense fallback={<PageLoader />}>
          <Routes>
            {/* ── Landing page publique ── */}
            <Route element={<LandingLayout />}>
              <Route path="/" element={<LandingPage />} />
            </Route>

            {/* ── Auth (login / register) ── */}
            <Route element={<PublicLayout />}>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/verify-email" element={<VerifyEmailPage />} />
              <Route path="/forgot-password" element={<ForgotPasswordPage />} />
              <Route path="/reset-password" element={<ResetPasswordPage />} />
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
              <Route path="/candidat/notifications" element={
                <ProtectedRoute roles={['CANDIDAT']}>
                  <NotificationsPage />
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

              {/* Analytics Dashboard */}
              <Route path="/analytics" element={
                <ProtectedRoute roles={['RESPONSABLE', 'ADMIN']}>
                  <AdminAnalyticsDashboard />
                </ProtectedRoute>
              } />

              {/* Épreuves écrites — Admin / Responsable */}
              <Route path="/admin/epreuves" element={
                <ProtectedRoute roles={['RESPONSABLE', 'ADMIN']}>
                  <EpreuvesPage />
                </ProtectedRoute>
              } />
              <Route path="/admin/epreuves/:id" element={
                <ProtectedRoute roles={['RESPONSABLE', 'ADMIN']}>
                  <DetailEpreuvePage />
                </ProtectedRoute>
              } />
              <Route path="/admin/epreuves/:id/resultats" element={
                <ProtectedRoute roles={['RESPONSABLE', 'ADMIN']}>
                  <ResultatsEpreuvePage />
                </ProtectedRoute>
              } />

              {/* Résultats épreuve écrite — Candidat */}
              <Route path="/candidat/resultats-ecrit" element={
                <ProtectedRoute roles={['CANDIDAT']}>
                  <ResultatEcritPage />
                </ProtectedRoute>
              } />

              {/* Épreuves orales — Admin / Responsable */}
              <Route path="/admin/epreuves-oral" element={
                <ProtectedRoute roles={['RESPONSABLE', 'ADMIN']}>
                  <EpreuveOralePage />
                </ProtectedRoute>
              } />
              <Route path="/admin/epreuves-oral/:id" element={
                <ProtectedRoute roles={['RESPONSABLE', 'ADMIN']}>
                  <DetailEpreuveOralePage />
                </ProtectedRoute>
              } />

              {/* Convocation — Candidat */}
              <Route path="/candidat/convocation" element={
                <ProtectedRoute roles={['CANDIDAT']}>
                  <ConvocationPage />
                </ProtectedRoute>
              } />
            </Route>

            {/* Redirect par défaut */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </AuthProvider>
    </BrowserRouter>
  );
}
