// src/pages/responsable/DossiersPage.jsx
// Liste et gestion des dossiers avec filtres, tri et export
import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import API from '../../api/axios';
import StatusBadge from '../../components/common/StatusBadge';
import EmptyState from '../../components/common/EmptyState';
import {
  Search, Download, AlertTriangle, ArrowRight,
  ChevronLeft, ChevronRight, FolderOpen,
  Shield, ShieldAlert, ShieldCheck
} from 'lucide-react';

const STATUTS = [
  { value: '', label: 'Tous les statuts' },
  { value: 'EN_ATTENTE', label: 'En attente' },
  { value: 'PRESELECTIONNE', label: 'Présélectionné' },
  { value: 'SUSPECT', label: 'Suspect' },
  { value: 'REJETE_AUTO', label: 'Rejeté (auto)' },
  { value: 'REJETE_FINAL', label: 'Rejeté (final)' },
  { value: 'INCOMPLET', label: 'Incomplet' },
  { value: 'BROUILLON', label: 'Brouillon' },
  { value: 'EN_TRAITEMENT', label: 'En traitement' },
];

export default function DossiersPage() {
  const [searchParams] = useSearchParams();
  const [dossiers, setDossiers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterStatut, setFilterStatut] = useState(searchParams.get('statut') || '');
  const [suspectOnly, setSuspectOnly] = useState(searchParams.get('suspect') === 'true');
  const [nonVerifiesMassar, setNonVerifiesMassar] = useState(false);
  const [sortBy, setSortBy] = useState('date');
  const [exporting, setExporting] = useState(false);
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const fetchDossiers = () => {
    setLoading(true);
    const params = new URLSearchParams();
    if (filterStatut) params.append('statut', filterStatut);
    if (search) params.append('search', search);
    if (suspectOnly) params.append('is_suspect', 'true');
    if (sortBy) params.append('ordering', sortBy === 'score_desc' ? '-score' : sortBy === 'score_asc' ? 'score' : sortBy === 'nom' ? 'candidat__nom' : '-date_soumission');

    API.get(`/dossiers/?${params.toString()}`)
      .then(({ data }) => setDossiers(data.results || data))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchDossiers();
  }, [filterStatut, suspectOnly, sortBy]); // eslint-disable-line

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    fetchDossiers();
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      const response = await API.get('/dossiers/export/', { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'preselectionnes.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch { /* silently fail */ }
    finally { setExporting(false); }
  };

  // Filtrage local supplémentaire pour "Non vérifiés Massar"
  const dossiersFiltrés = dossiers.filter((d) => {
    if (nonVerifiesMassar) {
      const isEnAttenteOuPreselectionne = ['EN_ATTENTE', 'PRESELECTIONNE'].includes(d.statut);
      return !d.massar_verifie && isEnAttenteOuPreselectionne;
    }
    return true;
  });

  // Pagination locale
  const totalPages = Math.ceil(dossiersFiltrés.length / pageSize);
  const paginatedData = dossiersFiltrés.slice((page - 1) * pageSize, page * pageSize);

  return (
    <div className="ensa-page animate-fade-in">
      <div className="ensa-page-header">
        <div className="ensa-page-header-row">
          <div>
            <h1 className="ensa-page-title">Gestion des Dossiers</h1>
            <p className="ensa-page-subtitle">{dossiersFiltrés.length} dossier{dossiersFiltrés.length !== 1 ? 's' : ''}</p>
          </div>
          <button onClick={handleExport} className="btn btn-outline btn-sm" disabled={exporting}>
            <Download size={14} /> {exporting ? 'Export...' : 'Exporter Excel'}
          </button>
        </div>
      </div>

      {/* Barre de filtres */}
      <div className="ensa-card" style={{ padding: '16px', marginBottom: '20px', position: 'sticky', top: '64px', zIndex: 20 }}>
        <div className="flex flex-wrap gap-3 items-center">
          <form onSubmit={handleSearch} className="flex-1 min-w-[200px] relative">
            <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-text-muted" />
            <input className="input pl-10" placeholder="Rechercher par nom, prénom ou CIN..."
              value={search} onChange={(e) => setSearch(e.target.value)} />
          </form>

          <select className="input w-auto min-w-[180px]" value={filterStatut} onChange={(e) => { setFilterStatut(e.target.value); setPage(1); }}>
            {STATUTS.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
          </select>

          <select className="input w-auto min-w-[160px]" value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
            <option value="date">Tri: Date (récent)</option>
            <option value="score_desc">Tri: Score desc.</option>
            <option value="score_asc">Tri: Score asc.</option>
            <option value="nom">Tri: Nom</option>
          </select>

          <label className="flex items-center gap-2 text-sm text-text-secondary cursor-pointer whitespace-nowrap">
            <input type="checkbox" checked={suspectOnly} onChange={(e) => { setSuspectOnly(e.target.checked); setPage(1); }}
              className="w-4 h-4 accent-suspect-500" />
            <AlertTriangle size={14} className="text-suspect-500" /> Suspects
          </label>

          <label className="flex items-center gap-2 text-sm text-text-secondary cursor-pointer whitespace-nowrap">
            <input type="checkbox" checked={nonVerifiesMassar} onChange={(e) => { setNonVerifiesMassar(e.target.checked); setPage(1); }}
              className="w-4 h-4 accent-primary-500" />
            <ShieldAlert size={14} className="text-primary-600" /> Non vérifiés Massar
          </label>
        </div>
      </div>

      {/* Tableau */}
      {loading ? (
        <div className="skeleton h-96 rounded-xl" />
      ) : dossiersFiltrés.length === 0 ? (
        <EmptyState title="Aucun dossier trouvé" description="Essayez de modifier vos filtres de recherche." icon={FolderOpen} />
      ) : (
        <>
          <div className="ensa-card">
            <div className="ensa-table-wrap" style={{ border: 'none', borderRadius: 0 }}>
              <table className="table">
                <thead>
                  <tr>
                    <th className="w-12">#</th>
                    <th>Candidat</th>
                    <th>CIN</th>
                    <th>Filière</th>
                    <th>Moy.</th>
                    <th>Score</th>
                    <th>Rang</th>
                    <th>Statut</th>
                    <th>Authenticité</th>
                    <th>Vérification</th>
                    <th>Date</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedData.map((d, i) => (
                    <tr key={d.id} className="group">
                      <td className="text-text-muted text-xs font-mono">{(page - 1) * pageSize + i + 1}</td>
                      <td className="font-medium text-sm">{d.candidat_nom}</td>
                      <td className="font-mono text-xs text-text-secondary">{d.candidat_cin || '—'}</td>
                      <td><span className="font-mono text-xs bg-primary-50 text-primary-600 px-2 py-0.5 rounded">{d.filiere_code}</span></td>
                      <td className="font-mono text-sm">{d.moyenne_generale ? `${d.moyenne_generale}` : '—'}</td>
                      <td className="font-mono font-semibold text-sm text-primary-700">{d.score ?? '—'}</td>
                      <td className="font-mono font-semibold text-sm">{d.classement ? `#${d.classement}` : '—'}</td>
                      <td><StatusBadge statut={d.statut} size="sm" /></td>
                      
                      {/* Colonne Authenticité */}
                      <td>
                        {d.score_authenticite != null ? (
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                              <div
                                className="h-full rounded-full"
                                style={{
                                  width: `${Math.round(d.score_authenticite * 100)}%`,
                                  backgroundColor:
                                    d.score_authenticite >= 0.8
                                      ? '#27AE60'
                                      : d.score_authenticite >= 0.6
                                      ? '#F39C12'
                                      : '#C0392B',
                                }}
                              />
                            </div>
                            <span className="font-mono text-[11px] font-semibold text-text-primary">
                              {Math.round(d.score_authenticite * 100)}%
                            </span>
                          </div>
                        ) : (
                          <span className="px-2 py-0.5 rounded bg-gray-100 text-gray-500 text-[10px]">Non analysé</span>
                        )}
                      </td>

                      {/* Colonne Vérification (Suspect / Massar) */}
                      <td className="text-center">
                        {d.is_suspect ? (
                          <span className="inline-flex items-center gap-1 text-red-600 font-semibold text-xs" title="Dossier suspect">
                            <ShieldAlert size={16} />
                            Suspect
                          </span>
                        ) : d.massar_verifie ? (
                          <span className="inline-flex items-center gap-1 text-green-600 font-semibold text-xs" title="Vérifié via Massar">
                            <ShieldCheck size={16} />
                            Massar
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-gray-400 text-xs" title="Non vérifié">
                            <Shield size={16} />
                            —
                          </span>
                        )}
                      </td>

                      <td className="text-xs text-text-muted whitespace-nowrap">
                        {d.date_soumission ? new Date(d.date_soumission).toLocaleDateString('fr-FR') : '—'}
                      </td>
                      <td>
                        <Link to={`/admin/dossier/${d.id}`} className="btn btn-ghost btn-sm text-primary-500 opacity-0 group-hover:opacity-100 transition-opacity">
                          Voir <ArrowRight size={12} />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <span className="text-sm text-text-muted">
                Affichage de {(page - 1) * pageSize + 1} à {Math.min(page * pageSize, dossiersFiltrés.length)} sur {dossiersFiltrés.length} dossiers
              </span>
              <div className="flex items-center gap-1">
                <button className="btn btn-ghost btn-sm" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>
                  <ChevronLeft size={16} />
                </button>
                {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                  let p;
                  if (totalPages <= 5) p = i + 1;
                  else if (page <= 3) p = i + 1;
                  else if (page >= totalPages - 2) p = totalPages - 4 + i;
                  else p = page - 2 + i;
                  return (
                    <button key={p} className={`btn btn-sm ${page === p ? 'btn-primary' : 'btn-ghost'}`} onClick={() => setPage(p)}>
                      {p}
                    </button>
                  );
                })}
                <button className="btn btn-ghost btn-sm" onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}>
                  <ChevronRight size={16} />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
