// src/styles/classes.js
// Classes utilitaires réutilisables pour garantir la cohérence visuelle
// sur l'ensemble du projet ENSA BM Présélection

export const UI = {
  // ── Pages ──
  pageWrapper:    'flex-1 overflow-auto bg-surface',
  pageContent:    'p-6 space-y-6',
  pageTitle:      'text-2xl font-bold text-text-primary font-display',
  pageSubtitle:   'text-sm text-text-secondary mt-1',

  // ── Cards ──
  card:           'bg-white rounded-[14px] border border-border shadow-sm',
  cardHeader:     'px-6 py-5 border-b border-gray-100',
  cardBody:       'p-6',
  cardFooter:     'px-6 py-4 border-t border-gray-100 bg-surface',

  // ── Formulaires ──
  label:          'block text-[13px] font-semibold text-text-secondary mb-1.5',
  input:          'w-full px-3.5 py-2.5 border-[1.5px] border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 transition-all',
  inputError:     'w-full px-3.5 py-2.5 border-[1.5px] border-danger-500 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-danger-500/20',
  errorText:      'text-xs text-danger-500 mt-1',
  helperText:     'text-xs text-text-muted mt-1',

  // ── Boutons ──
  btnPrimary:     'btn btn-primary',
  btnSecondary:   'btn btn-outline',
  btnDanger:      'btn btn-danger',
  btnSuccess:     'btn btn-success',
  btnGhost:       'btn btn-ghost',

  // ── Tableaux ──
  table:          'w-full text-sm text-left',
  tableHeader:    'bg-gray-50/80 border-b-2 border-border',
  tableHeaderCell:'px-4 py-3 font-semibold text-text-secondary text-xs uppercase tracking-wider',
  tableRow:       'border-b border-gray-100 hover:bg-gray-50/50 transition-colors',
  tableCell:      'px-4 py-3 text-text-primary',

  // ── Sections ──
  sectionTitle:   'text-base font-bold text-text-primary mb-4',
  divider:        'border-t border-border my-6',

  // ── États ──
  skeleton:       'animate-pulse bg-gray-200 rounded-xl',
  emptyState:     'flex flex-col items-center justify-center py-16 text-text-muted',

  // ── Breadcrumb ──
  breadcrumb:     'flex items-center gap-2 text-[13px] text-text-secondary mb-2',
  breadcrumbLink: 'hover:text-primary-700 no-underline transition-colors inline-flex items-center gap-1',
  breadcrumbCurrent: 'text-text-primary font-semibold',

  // ── KPI Cards ──
  kpiGrid:        'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4',
  kpiCard:        'bg-white border border-border rounded-[14px] p-5 transition-all duration-200 hover:shadow-md hover:-translate-y-0.5',

  // ── Charts Grid ──
  chartsGrid:     'grid grid-cols-1 lg:grid-cols-5 gap-5',

  // ── Detail Grid (3 col) ──
  detailGrid:     'grid grid-cols-1 lg:grid-cols-12 gap-5',
  detailColLeft:  'lg:col-span-3',
  detailColCenter:'lg:col-span-5',
  detailColRight: 'lg:col-span-4',
};
