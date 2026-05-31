// src/pages/candidat/MesDossiers.jsx
// Liste des dossiers du candidat — style ENSA BM
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import API from '../../api/axios';
import StatusBadge from '../../components/common/StatusBadge';
import {
  Plus, Calendar, BarChart3, Trophy, AlertTriangle,
  ArrowRight, FolderOpen
} from 'lucide-react';

export default function MesDossiers() {
  const [dossiers, setDossiers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    API.get('/dossiers/')
      .then(({ data }) => setDossiers(data.results || data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="stagger grid gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="skeleton h-32 rounded-xl" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="ensa-page-header">
        <div className="ensa-page-header-row">
          <div>
            <h1 className="ensa-page-title">Mes Dossiers</h1>
            <p className="ensa-page-subtitle">
              {dossiers.length} dossier{dossiers.length !== 1 ? 's' : ''} de candidature
            </p>
          </div>
          <Link to="/nouveau-dossier" className="btn btn-primary">
            <Plus size={16} /> Nouveau Dossier
          </Link>
        </div>
      </div>

      {/* État vide */}
      {dossiers.length === 0 && (
        <div className="ensa-empty">
          <div className="ensa-empty-icon">
            <FolderOpen size={28} />
          </div>
          <h3 className="ensa-empty-title">Aucun dossier pour le moment</h3>
          <p className="ensa-empty-desc">
            Commencez par créer votre premier dossier de candidature pour intégrer l'ENSA Béni Mellal.
          </p>
          <Link to="/nouveau-dossier" className="btn btn-primary">
            <Plus size={16} /> Créer mon premier dossier
          </Link>
        </div>
      )}

      {/* Liste des dossiers */}
      <div className="ensa-dossier-list stagger">
        {dossiers.map((d) => (
          <Link
            key={d.id}
            to={`/dossier/${d.id}`}
            className="ensa-dossier-card"
          >
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-sm font-semibold text-text-primary">
                    {d.filiere_nom || 'Filière'}
                  </h3>
                  <span className="font-mono text-xs text-primary-500 bg-primary-50 px-2 py-0.5 rounded">
                    {d.filiere_code}
                  </span>
                </div>
                <div className="flex flex-wrap items-center gap-4 text-xs text-text-muted">
                  <span className="flex items-center gap-1">
                    <Calendar size={12} />
                    {d.date_soumission ? new Date(d.date_soumission).toLocaleDateString('fr-FR') : 'Non soumis'}
                  </span>
                  {d.moyenne_generale && (
                    <span className="flex items-center gap-1">
                      <BarChart3 size={12} /> Moyenne: <span className="font-mono font-medium text-text-primary">{d.moyenne_generale}/20</span>
                    </span>
                  )}
                  {d.score && (
                    <span className="flex items-center gap-1">
                      <Trophy size={12} /> Score: <span className="font-mono font-medium text-primary-700">{d.score}</span>
                    </span>
                  )}
                  {d.classement && (
                    <span className="flex items-center gap-1 font-medium text-text-primary">
                      #{d.classement}
                    </span>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="flex flex-col items-end gap-1.5">
                  {['BROUILLON', 'INCOMPLET'].includes(d.statut) && (
                    <Link
                      to={`/dossier/${d.id}/modifier`}
                      className="btn btn-outline btn-sm"
                      onClick={(e) => e.stopPropagation()}
                    >
                      Modifier
                    </Link>
                  )}
                  <StatusBadge statut={d.statut} size="sm" />
                  {d.is_suspect && (
                    <span className="badge badge-suspect text-[10px]">
                      <AlertTriangle size={10} /> Suspect
                    </span>
                  )}
                </div>
                <ArrowRight size={16} className="text-text-muted hidden sm:block" />
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
