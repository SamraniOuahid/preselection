// src/styles/spacing.js
// Système de spacing uniforme pour tout le projet ENSA BM
// Utilisé pour garantir la cohérence des marges et paddings

export const SPACING = {
  // Padding page principale (contenu dans layout)
  PAGE_PADDING:    'px-6 py-6',
  PAGE_PADDING_SM: 'px-4 py-4',   // mobile

  // Container max-width centré
  CONTAINER:       'max-w-7xl mx-auto px-6',
  CONTAINER_SM:    'max-w-7xl mx-auto px-4',

  // Cards
  CARD_PADDING:    'p-6',
  CARD_PADDING_SM: 'p-4',

  // Sections internes
  SECTION_GAP:     'space-y-6',
  SECTION_GAP_SM:  'space-y-4',

  // Grilles
  GRID_GAP:        'gap-6',
  GRID_GAP_SM:     'gap-4',

  // Formulaires
  FORM_GAP:        'space-y-4',
  INPUT_PADDING:   'px-3 py-2',

  // Tableaux
  TABLE_CELL:      'px-4 py-3',
  TABLE_HEADER:    'px-4 py-3',

  // Sidebar
  SIDEBAR_WIDTH:    'w-[260px]',     // 260px
  SIDEBAR_PADDING:  'px-4 py-3',

  // Topbar
  TOPBAR_HEIGHT:    'h-16',
  TOPBAR_PADDING:   'px-6',

  // Page content inside DashboardLayout
  CONTENT_MAX_WIDTH: 'max-w-[1400px]',
  CONTENT_PADDING:   'px-4 py-5 sm:px-6 sm:py-6 lg:px-8 lg:py-8',
};
