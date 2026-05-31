// src/pages/responsable/DashboardPage.jsx
// Dashboard responsable avec KPI, graphiques Recharts — style ENSA BM
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import API from '../../api/axios';
import StatusBadge from '../../components/common/StatusBadge';
import BoutonNotifierTous from '../../components/notifications/BoutonNotifierTous';
import { Users, Clock, CheckCircle, XCircle, AlertTriangle, ArrowRight, TrendingUp, ShieldAlert } from 'lucide-react';

const COLORS_STATUT = {
  BROUILLON: '#95A5A6',
  EN_TRAITEMENT: '#2E86C1',
  INCOMPLET: '#E67E22',
  SUSPECT: '#784212',
  REJETE_AUTO: '#C0392B',
  EN_ATTENTE: '#F39C12',
  PRESELECTIONNE: '#27AE60',
  REJETE_FINAL: '#922B21',
};

const LABELS_STATUT = {
  BROUILLON: 'Brouillon',
  EN_TRAITEMENT: 'En traitement',
  INCOMPLET: 'Incomplet',
  SUSPECT: 'Suspect',
  REJETE_AUTO: 'Rejeté (auto)',
  EN_ATTENTE: 'En attente',
  PRESELECTIONNE: 'Présélectionné',
  REJETE_FINAL: 'Rejeté (final)',
};

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [suspectsList, setSuspectsList] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Appel conjoint des statistiques globales et de la liste des suspects
    Promise.all([
      API.get('/dashboard/stats/').then((r) => r.data),
      API.get('/dossiers/?is_suspect=true').then((r) => r.data),
    ])
      .then(([statsData, dossiersData]) => {
        setStats(statsData);
        
        // Filtrer les dossiers suspects non traités (SUSPECT ou EN_ATTENTE ou EN_TRAITEMENT)
        const dossiersList = dossiersData.results || dossiersData;
        const nonTraites = (dossiersList || [])
          .filter((d) => ['SUSPECT', 'EN_ATTENTE', 'EN_TRAITEMENT'].includes(d.statut))
          .slice(0, 5);
        setSuspectsList(nonTraites);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-5">
        <div className="ensa-kpi-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="skeleton h-28 rounded-xl" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
          <div className="skeleton h-72 rounded-xl lg:col-span-3" />
          <div className="skeleton h-72 rounded-xl lg:col-span-2" />
        </div>
        <div className="skeleton h-64 rounded-xl w-full" />
      </div>
    );
  }

  if (!stats) return null;

  const pieData = (stats.par_statut || []).map((s) => ({
    name: LABELS_STATUT[s.statut] || s.statut,
    value: s.count,
    color: COLORS_STATUT[s.statut] || '#D5D8DC',
  }));

  const barData = (stats.par_filiere || []).map((f) => ({
    name: f.filiere__nom || f.filiere__code || f.filiere_nom || '—',
    candidatures: f.count,
  }));

  const kpis = [
    { label: 'Total candidatures', value: stats.global.total, Icon: Users, color: '#1B3A6B', bg: '#EBF5FB' },
    { label: 'En attente', value: stats.global.en_attente, Icon: Clock, color: '#E67E22', bg: '#FEF9E7' },
    { label: 'Présélectionnés', value: stats.global.preselectionnes, Icon: CheckCircle, color: '#27AE60', bg: '#EAFAF1' },
    { label: 'Rejetés', value: stats.global.rejetes, Icon: XCircle, color: '#C0392B', bg: '#FDEDEC' },
    {
      label: 'Suspects à vérifier',
      value: stats.global.suspects,
      Icon: ShieldAlert,
      color: '#784212',
      bg: '#FDF2E9',
      link: '/dossiers?suspect=true',
    },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="ensa-page-header">
        <div className="ensa-page-header-row">
          <div>
            <h1 className="ensa-page-title">Dashboard</h1>
            <p className="ensa-page-subtitle">Vue d'ensemble de la présélection</p>
          </div>
          <div className="flex items-center gap-3">
            <BoutonNotifierTous />
            <Link to="/dossiers" className="btn btn-primary btn-sm">
              <TrendingUp size={16} /> Voir tous les dossiers
            </Link>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {kpis.map((kpi) => {
          const { Icon } = kpi;
          const CardWrapper = kpi.link ? Link : 'div';
          const wrapperProps = kpi.link
            ? {
                to: kpi.link,
                className: 'ensa-kpi-card hover:shadow-md transition-all duration-200 block no-underline',
              }
            : { className: 'ensa-kpi-card' };
          return (
            <CardWrapper
              key={kpi.label}
              {...wrapperProps}
              style={{ '--kpi-color': kpi.color, cursor: kpi.link ? 'pointer' : 'default' }}
            >
              <div className="ensa-kpi-top">
                <div>
                  <p className="ensa-kpi-label">{kpi.label}</p>
                  <p className="ensa-kpi-value font-mono" style={{ color: kpi.color }}>
                    {kpi.value}
                  </p>
                </div>
                <div className="ensa-kpi-icon" style={{ background: kpi.bg }}>
                  <Icon size={20} style={{ color: kpi.color }} />
                </div>
              </div>
            </CardWrapper>
          );
        })}
      </div>

      {/* Suspects alert */}
      {stats.global.suspects > 0 && (
        <div className="ensa-alert ensa-alert-warning">
          <div className="ensa-alert-content">
            <div className="ensa-alert-icon" style={{ background: '#FDEBD0' }}>
              <AlertTriangle size={18} className="text-warning-600" />
            </div>
            <div>
              <span className="text-sm font-semibold" style={{ color: '#784212' }}>
                {stats.global.suspects} dossier(s) suspect(s)
              </span>
              <p className="text-xs" style={{ color: '#B9770E' }}>
                Nécessitent une vérification manuelle
              </p>
            </div>
          </div>
          <Link to="/dossiers?suspect=true" className="btn btn-sm btn-outline-warning">
            Vérifier <ArrowRight size={14} />
          </Link>
        </div>
      )}

      {/* Graphiques */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="ensa-card lg:col-span-2">
          <div className="ensa-card-header">
            <h3 className="ensa-card-title">Candidatures par filière</h3>
          </div>
          <div className="ensa-card-body">
            {barData.length > 0 ? (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={barData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#EBEDEF" />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="candidatures" fill="#1B3A6B" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-64 flex items-center justify-center text-text-muted text-sm">Aucune donnée</div>
            )}
          </div>
        </div>

        <div className="ensa-card lg:col-span-1">
          <div className="ensa-card-header">
            <h3 className="ensa-card-title">Répartition par statut</h3>
          </div>
          <div className="ensa-card-body">
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={pieData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={85}
                    innerRadius={45}
                    labelLine={false}
                    label={({ percent }) => `${(percent * 100).toFixed(0)}%`}
                  >
                    {pieData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend iconSize={8} wrapperStyle={{ fontSize: '11px' }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-64 flex items-center justify-center text-text-muted text-sm">Aucune donnée</div>
            )}
          </div>
        </div>
      </div>

      {/* Derniers dossiers */}
      <div className="ensa-card">
        <div className="ensa-card-header">
          <h3 className="ensa-card-title">Derniers dossiers soumis</h3>
          <Link
            to="/dossiers"
            className="text-xs text-primary-500 hover:text-primary-700 font-medium no-underline flex items-center gap-1"
          >
            Voir tous <ArrowRight size={12} />
          </Link>
        </div>
        <div
          className="ensa-table-wrap"
          style={{ border: 'none', borderRadius: 0, borderTop: '1px solid #e5e7eb' }}
        >
          <table className="table">
            <thead>
              <tr>
                <th>Candidat</th>
                <th>Filière</th>
                <th>Score</th>
                <th>Statut</th>
                <th className="text-center">Authenticité</th>
                <th>Date</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {(stats.derniers_dossiers || []).slice(0, 10).map((d) => (
                <tr key={d.id}>
                  <td className="font-medium text-sm">{d.candidat_nom}</td>
                  <td>
                    <span className="font-mono text-xs bg-primary-50 text-primary-600 px-2 py-0.5 rounded">
                      {d.filiere_code}
                    </span>
                  </td>
                  <td className="font-mono font-semibold text-primary-700">{d.score ?? '—'}</td>
                  <td>
                    <StatusBadge statut={d.statut} size="sm" />
                  </td>

                  {/* Mini-badge score authenticité */}
                  <td className="text-center">
                    {d.score_authenticite != null ? (
                      <span
                        className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold text-white font-mono"
                        style={{
                          backgroundColor:
                            d.score_authenticite >= 0.8
                              ? '#27AE60'
                              : d.score_authenticite >= 0.6
                              ? '#F39C12'
                              : '#C0392B',
                        }}
                      >
                        {Math.round(d.score_authenticite * 100)}%
                      </span>
                    ) : (
                      <span className="text-[10px] text-gray-400 font-medium bg-gray-50 px-2 py-0.5 rounded">
                        —
                      </span>
                    )}
                  </td>

                  <td className="text-xs text-text-muted">
                    {d.date_soumission ? new Date(d.date_soumission).toLocaleDateString('fr-FR') : '—'}
                  </td>
                  <td>
                    <Link to={`/admin/dossier/${d.id}`} className="btn btn-ghost btn-sm text-primary-500">
                      Voir <ArrowRight size={12} />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Alertes système */}
      <div className="ensa-card mt-6">
        <div className="ensa-card-header flex items-center justify-between">
          <h3 className="ensa-card-title flex items-center gap-2">
            <ShieldAlert size={16} className="text-[#784212]" />
            Alertes système — Dossiers suspects à examiner
          </h3>
          <span className="badge bg-amber-100 text-amber-800 text-xs font-semibold px-2 py-0.5 rounded">
            {suspectsList.length} en attente
          </span>
        </div>
        <div
          className="ensa-table-wrap"
          style={{ border: 'none', borderRadius: 0, borderTop: '1px solid #e5e7eb' }}
        >
          {suspectsList.length > 0 ? (
            <table className="table">
              <thead>
                <tr>
                  <th>Candidat</th>
                  <th>Filière</th>
                  <th className="text-center">Score d'Authenticité</th>
                  <th>Statut</th>
                  <th>Date Soumission</th>
                  <th className="text-right">Action</th>
                </tr>
              </thead>
              <tbody>
                {suspectsList.map((d) => (
                  <tr key={d.id} className="hover:bg-amber-50/10">
                    <td className="font-medium text-sm flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-red-600 animate-pulse" />
                      {d.candidat_nom}
                    </td>
                    <td>
                      <span className="font-mono text-xs bg-primary-50 text-primary-600 px-2 py-0.5 rounded">
                        {d.filiere_code}
                      </span>
                    </td>
                    <td className="text-center">
                      {d.score_authenticite != null ? (
                        <span
                          className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold text-white font-mono"
                          style={{
                            backgroundColor:
                              d.score_authenticite >= 0.8
                                ? '#27AE60'
                                : d.score_authenticite >= 0.6
                                ? '#F39C12'
                                : '#C0392B',
                          }}
                        >
                          {Math.round(d.score_authenticite * 100)}%
                        </span>
                      ) : (
                        <span className="text-[10px] text-gray-400">Non analysé</span>
                      )}
                    </td>
                    <td>
                      <StatusBadge statut={d.statut} size="sm" />
                    </td>
                    <td className="text-xs text-text-muted">
                      {d.date_soumission ? new Date(d.date_soumission).toLocaleDateString('fr-FR') : '—'}
                    </td>
                    <td className="text-right">
                      <Link
                        to={`/admin/dossier/${d.id}?tab=verification`}
                        className="btn btn-primary btn-sm flex items-center gap-1.5 inline-flex"
                        style={{ backgroundColor: '#2E86C1' }}
                      >
                        Examiner <ArrowRight size={12} />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="py-8 text-center text-sm text-text-muted">
              Aucun dossier suspect non traité à signaler. Excellent travail !
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
