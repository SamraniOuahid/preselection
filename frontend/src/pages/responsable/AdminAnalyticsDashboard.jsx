// src/pages/responsable/AdminAnalyticsDashboard.jsx
// Tableau de bord Analytics & Data Science — ENSA Béni Mellal
import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, ComposedChart, Line, ScatterChart, Scatter,
  ZAxis, AreaChart, Area,
} from 'recharts';
import API from '../../api/axios';
import {
  Users, FileCheck, TrendingUp, ShieldAlert, AlertTriangle,
  BarChart3, PieChartIcon, Target, Crosshair, Activity,
  ArrowUpRight, ArrowDownRight, Percent, XCircle, RefreshCw,
} from 'lucide-react';

/* ── Palettes ── */
const BRAND = { navy: '#0D1F3C', blue: '#2E86C1', sky: '#5DADE2', teal: '#1ABC9C' };
const DIPLOME_COLORS = ['#2E86C1','#1ABC9C','#E74C3C','#F39C12','#8E44AD','#27AE60','#D35400','#7F8C8D'];
const STATUT_COLORS = {
  BROUILLON:'#95A5A6', EN_TRAITEMENT:'#2E86C1', INCOMPLET:'#E67E22',
  SUSPECT:'#784212', REJETE_AUTO:'#C0392B', EN_ATTENTE:'#F39C12',
  PRESELECTIONNE:'#27AE60', REJETE_FINAL:'#922B21', ADMIS_FINAL:'#1ABC9C',
  RECALE_FINAL:'#C0392B', ABSENT_ECRIT:'#7F8C8D',
};
const STATUT_LABELS = {
  BROUILLON:'Brouillon', EN_TRAITEMENT:'En traitement', INCOMPLET:'Incomplet',
  SUSPECT:'Suspect', REJETE_AUTO:'Rejeté (auto)', EN_ATTENTE:'En attente',
  PRESELECTIONNE:'Présélectionné', REJETE_FINAL:'Rejeté (final)',
  ADMIS_FINAL:'Admis', RECALE_FINAL:'Recalé', ABSENT_ECRIT:'Absent',
};

/* ── Tooltip customisé ── */
const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: 'rgba(13,31,60,0.95)', backdropFilter: 'blur(8px)',
      borderRadius: 10, padding: '10px 14px', border: '1px solid rgba(255,255,255,0.1)',
      boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
    }}>
      {label && <p style={{ color: '#fff', fontSize: 12, fontWeight: 600, marginBottom: 4 }}>{label}</p>}
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color || '#5DADE2', fontSize: 11, margin: '2px 0' }}>
          {p.name}: <strong>{typeof p.value === 'number' ? p.value.toLocaleString('fr-FR') : p.value}</strong>
        </p>
      ))}
    </div>
  );
};

/* ── KPI Card ── */
function KpiCard({ label, value, icon: Icon, color, bg, suffix, trend, alert }) {
  return (
    <div className="ensa-analytics-kpi" style={{ '--kpi-accent': color }}>
      <div className="ensa-analytics-kpi-inner">
        <div style={{ flex: 1 }}>
          <p className="ensa-analytics-kpi-label">{label}</p>
          <p className="ensa-analytics-kpi-value" style={{ color }}>
            {typeof value === 'number' ? value.toLocaleString('fr-FR') : value}
            {suffix && <span className="ensa-analytics-kpi-suffix">{suffix}</span>}
          </p>
          {trend !== undefined && (
            <span className="ensa-analytics-kpi-trend" style={{ color: trend >= 0 ? '#27AE60' : '#C0392B' }}>
              {trend >= 0 ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
              {Math.abs(trend)}%
            </span>
          )}
        </div>
        <div className="ensa-analytics-kpi-icon" style={{ background: bg }}>
          <Icon size={22} style={{ color }} />
        </div>
      </div>
      {alert && <div className="ensa-analytics-kpi-alert">{alert}</div>}
    </div>
  );
}

/* ── Section wrapper ── */
function Section({ title, icon: Icon, children, className = '', badge }) {
  return (
    <div className={`ensa-analytics-section ${className}`}>
      <div className="ensa-analytics-section-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {Icon && <div className="ensa-analytics-section-icon"><Icon size={16} /></div>}
          <h3 className="ensa-analytics-section-title">{title}</h3>
        </div>
        {badge && <span className="ensa-analytics-badge">{badge}</span>}
      </div>
      <div className="ensa-analytics-section-body">{children}</div>
    </div>
  );
}

/* ── Main Component ── */
export default function AdminAnalyticsDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = () => {
    setLoading(true);
    setError(null);
    API.get('/admin/analytics/stats/')
      .then(r => setData(r.data))
      .catch(() => setError('Impossible de charger les données analytiques.'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, []);

  /* ── Loading skeleton ── */
  if (loading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
          {[1,2,3,4,5].map(i => <div key={i} className="skeleton h-28 rounded-2xl" />)}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {[1,2,3,4].map(i => <div key={i} className="skeleton h-72 rounded-2xl" />)}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-4">
        <AlertTriangle size={48} className="text-warning-500" />
        <p className="text-sm text-text-secondary">{error}</p>
        <button onClick={fetchData} className="btn btn-primary btn-sm">
          <RefreshCw size={14} /> Réessayer
        </button>
      </div>
    );
  }

  if (!data) return null;

  const { kpis, entonnoir, par_diplome, par_etablissement, competitivite, fraude_scatter, croissance, par_statut } = data;

  /* ── Pie data for statuts ── */
  const statutPieData = (par_statut || []).map(s => ({
    name: STATUT_LABELS[s.statut] || s.statut, value: s.count,
    color: STATUT_COLORS[s.statut] || '#D5D8DC',
  }));

  return (
    <div className="ensa-analytics-dashboard animate-fade-in">
      {/* ── Header ── */}
      <div className="ensa-page-header">
        <div className="ensa-page-header-row">
          <div>
            <h1 className="ensa-page-title" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <Activity size={24} className="text-primary-500" />
              Analytics & Data Science
            </h1>
            <p className="ensa-page-subtitle">
              Tableau de bord stratégique — Présélection ENSA Béni Mellal {new Date().getFullYear()}
            </p>
          </div>
          <button onClick={fetchData} className="btn btn-outline btn-sm" title="Actualiser">
            <RefreshCw size={14} /> Actualiser
          </button>
        </div>
      </div>

      {/* ═══ 1. KPIs Flash ═══ */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4 stagger">
        <KpiCard label="Total Inscriptions" value={kpis.total_inscriptions}
          icon={Users} color="#1B3A6B" bg="#EBF5FB" />
        <KpiCard label="Dossiers Complets" value={kpis.dossiers_complets}
          icon={FileCheck} color="#2E86C1" bg="#D6EAF8" />
        <KpiCard label="Taux de Complétion" value={kpis.taux_completion}
          icon={Percent} color="#27AE60" bg="#EAFAF1" suffix="%" />
        <KpiCard label="Rejets Automatiques" value={kpis.rejets_auto}
          icon={XCircle} color="#C0392B" bg="#FDEDEC" />
        <KpiCard label="Alertes Fraudes" value={kpis.alertes_fraudes}
          icon={ShieldAlert} color="#E74C3C" bg="#FDEDEC"
          alert={kpis.alertes_fraudes > 0 ? `${kpis.alertes_fraudes} suspect(s) à vérifier` : null} />
      </div>

      {/* ═══ 2. Entonnoir de Recrutement + Croissance ═══ */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
        <Section title="Entonnoir de Recrutement" icon={Target} className="lg:col-span-3"
          badge="Pipeline">
          {entonnoir && entonnoir.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={entonnoir} layout="vertical" barCategoryGap="28%"
                margin={{ left: 20, right: 30, top: 10, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#EBEDEF" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 11, fill: '#5D6D7E' }} />
                <YAxis type="category" dataKey="etape" width={140}
                  tick={{ fontSize: 12, fill: '#1A1A2E', fontWeight: 600 }} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="valeur" radius={[0, 8, 8, 0]} name="Candidats">
                  {entonnoir.map((_, i) => (
                    <Cell key={i} fill={['#1B3A6B','#2E86C1','#5DADE2','#1ABC9C'][i] || '#2E86C1'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : <EmptyState />}
        </Section>

        <Section title="Croissance des Inscriptions" icon={TrendingUp} className="lg:col-span-2"
          badge="Temporel">
          {croissance && croissance.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={croissance} margin={{ left: 0, right: 10, top: 10, bottom: 10 }}>
                <defs>
                  <linearGradient id="gradCroissance" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2E86C1" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#2E86C1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#EBEDEF" />
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#5D6D7E' }} />
                <YAxis tick={{ fontSize: 11, fill: '#5D6D7E' }} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="cumul" name="Cumul" stroke="#1B3A6B"
                  fill="url(#gradCroissance)" strokeWidth={2} />
                <Line type="monotone" dataKey="inscriptions" name="Par jour"
                  stroke="#1ABC9C" strokeWidth={2} dot={{ r: 3, fill: '#1ABC9C' }} />
              </AreaChart>
            </ResponsiveContainer>
          ) : <EmptyState />}
        </Section>
      </div>

      {/* ═══ 3. Cartographie des Origines ═══ */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
        <Section title="Répartition par Diplôme" icon={PieChartIcon} className="lg:col-span-2"
          badge="Donut">
          {par_diplome && par_diplome.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={par_diplome} dataKey="value" nameKey="name"
                  cx="50%" cy="50%" outerRadius={95} innerRadius={55}
                  paddingAngle={3} stroke="none"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  labelLine={{ stroke: '#95A5A6', strokeWidth: 1 }}>
                  {par_diplome.map((_, i) => (
                    <Cell key={i} fill={DIPLOME_COLORS[i % DIPLOME_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          ) : <EmptyState />}
        </Section>

        <Section title="Top Établissements d'Origine" icon={BarChart3} className="lg:col-span-3"
          badge="Classement">
          {par_etablissement && par_etablissement.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={par_etablissement} margin={{ left: 10, right: 20, top: 10, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#EBEDEF" />
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#5D6D7E' }} angle={-20} textAnchor="end" height={60} />
                <YAxis tick={{ fontSize: 11, fill: '#5D6D7E' }} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="candidats" name="Candidats" radius={[6, 6, 0, 0]}>
                  {par_etablissement.map((_, i) => (
                    <Cell key={i} fill={i === 0 ? '#1B3A6B' : i === 1 ? '#2E86C1' : '#5DADE2'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : <EmptyState />}
        </Section>
      </div>

      {/* ═══ 4. Compétitivité par Filière ═══ */}
      <Section title="Compétitivité par Filière" icon={BarChart3} badge="Barres + Ligne">
        {competitivite && competitivite.length > 0 ? (
          <ResponsiveContainer width="100%" height={340}>
            <ComposedChart data={competitivite} margin={{ left: 10, right: 20, top: 10, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#EBEDEF" />
              <XAxis dataKey="filiere" tick={{ fontSize: 12, fill: '#1A1A2E', fontWeight: 600 }} />
              <YAxis yAxisId="left" tick={{ fontSize: 11, fill: '#5D6D7E' }} label={{ value: 'Candidats', angle: -90, position: 'insideLeft', style: { fontSize: 11, fill: '#5D6D7E' } }} />
              <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11, fill: '#E74C3C' }}
                label={{ value: 'Ratio', angle: 90, position: 'insideRight', style: { fontSize: 11, fill: '#E74C3C' } }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar yAxisId="left" dataKey="candidats" name="Candidats" fill="#1B3A6B"
                radius={[6, 6, 0, 0]} barSize={40} />
              <Bar yAxisId="left" dataKey="places" name="Places" fill="#D6EAF8"
                radius={[6, 6, 0, 0]} barSize={40} />
              <Line yAxisId="right" type="monotone" dataKey="ratio" name="Ratio sélectivité"
                stroke="#E74C3C" strokeWidth={3} dot={{ r: 5, fill: '#E74C3C', stroke: '#fff', strokeWidth: 2 }} />
            </ComposedChart>
          </ResponsiveContainer>
        ) : <EmptyState />}
      </Section>

      {/* ═══ 5. Scatter Fraude + Statuts Donut ═══ */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
        <Section title="Corrélation Notes — Détection de Fraudes" icon={Crosshair}
          className="lg:col-span-3" badge="Scatter Plot">
          {fraude_scatter && fraude_scatter.length > 0 ? (
            <div>
              <p style={{ fontSize: 11, color: '#5D6D7E', marginBottom: 8, lineHeight: 1.5 }}>
                <strong>Axe X</strong> : Note déclarée par le candidat —
                <strong> Axe Y</strong> : Note extraite par OCR.
                Les points sur la <span style={{ color: '#27AE60', fontWeight: 700 }}>diagonale</span> sont
                conformes. Les <span style={{ color: '#E74C3C', fontWeight: 700 }}>points isolés</span> signalent
                une fraude potentielle.
              </p>
              <ResponsiveContainer width="100%" height={320}>
                <ScatterChart margin={{ left: 10, right: 20, top: 10, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#EBEDEF" />
                  <XAxis type="number" dataKey="note_declaree" name="Note déclarée"
                    domain={[0, 20]} tick={{ fontSize: 11, fill: '#5D6D7E' }}
                    label={{ value: 'Note déclarée', position: 'insideBottom', offset: -5, style: { fontSize: 11, fill: '#5D6D7E' } }} />
                  <YAxis type="number" dataKey="note_extraite" name="Note extraite (OCR)"
                    domain={[0, 20]} tick={{ fontSize: 11, fill: '#5D6D7E' }}
                    label={{ value: 'Note OCR', angle: -90, position: 'insideLeft', style: { fontSize: 11, fill: '#5D6D7E' } }} />
                  <ZAxis type="number" dataKey="ecart" range={[30, 200]} name="Écart" />
                  <Tooltip content={<CustomTooltip />} />
                  <Scatter name="Conformes" data={fraude_scatter.filter(d => !d.is_suspect)}
                    fill="#27AE60" opacity={0.7} />
                  <Scatter name="Suspects" data={fraude_scatter.filter(d => d.is_suspect)}
                    fill="#E74C3C" opacity={0.85} shape="diamond" />
                  {/* Diagonale de référence via line */}
                </ScatterChart>
              </ResponsiveContainer>
              <div style={{ display: 'flex', gap: 20, justifyContent: 'center', marginTop: 8 }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: '#5D6D7E' }}>
                  <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#27AE60', display: 'inline-block' }} />
                  Conformes
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: '#5D6D7E' }}>
                  <span style={{ width: 10, height: 10, background: '#E74C3C', display: 'inline-block', transform: 'rotate(45deg)' }} />
                  Suspects (écart &gt; 0.5)
                </span>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Crosshair size={36} className="text-text-muted mb-3" style={{ opacity: 0.4 }} />
              <p className="text-sm text-text-muted">Aucune donnée de corrélation disponible.</p>
              <p className="text-xs text-text-muted mt-1">Les données apparaîtront après l'extraction OCR des relevés.</p>
            </div>
          )}
        </Section>

        <Section title="Répartition par Statut" icon={PieChartIcon} className="lg:col-span-2"
          badge="Vue globale">
          {statutPieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={320}>
              <PieChart>
                <Pie data={statutPieData} dataKey="value" nameKey="name"
                  cx="50%" cy="50%" outerRadius={90} innerRadius={50}
                  paddingAngle={2} stroke="none"
                  label={({ percent }) => `${(percent * 100).toFixed(0)}%`}>
                  {statutPieData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend iconSize={8} wrapperStyle={{ fontSize: 11 }} />
              </PieChart>
            </ResponsiveContainer>
          ) : <EmptyState />}
        </Section>
      </div>

      {/* Footer timestamp */}
      <div style={{ textAlign: 'center', padding: '16px 0', fontSize: 11, color: '#95A5A6' }}>
        Dernière actualisation : {new Date().toLocaleString('fr-FR')} — ENSA Béni Mellal — Module Analytics
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center" style={{ opacity: 0.5 }}>
      <BarChart3 size={32} className="text-text-muted mb-2" />
      <p className="text-sm text-text-muted">Aucune donnée disponible</p>
    </div>
  );
}
