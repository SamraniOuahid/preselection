// src/api/dossiers.js
// Appels API pour la gestion des dossiers et la vérification
import API from './axios';

/**
 * Récupérer la liste des dossiers avec filtres optionnels
 */
export const getDossiers = (params = {}) =>
  API.get('/dossiers/', { params }).then((r) => r.data);

/**
 * Récupérer le détail d'un dossier par ID
 */
export const getDossier = (id) =>
  API.get(`/dossiers/${id}/`).then((r) => r.data);

/**
 * Soumettre une action sur un dossier (valider, rejeter, etc.)
 */
export const actionDossier = (id, action, payload = {}) =>
  API.post(`/dossiers/${id}/${action}/`, payload).then((r) => r.data);

/**
 * Exporter les dossiers présélectionnés au format Excel
 */
export const exportDossiers = () =>
  API.get('/dossiers/export/', { responseType: 'blob' });

// ── Vérification automatique ──────────────────────────────

/**
 * Récupérer le rapport de vérification automatique d'un dossier
 * @param {string|number} dossierId - ID du dossier
 * @returns {Promise} Rapport contenant score_authenticite, alertes, par_document, massar_verifie
 */
export const getRapportVerification = (dossierId) =>
  API.get(`/dossiers/${dossierId}/rapport_verification/`).then((r) => r.data);

/**
 * Marquer un dossier comme vérifié via le portail Massar
 * @param {string|number} dossierId - ID du dossier
 * @returns {Promise} Message de confirmation
 */
export const marquerMassarVerifie = (dossierId) =>
  API.post(`/dossiers/${dossierId}/marquer_massar_verifie/`).then((r) => r.data);
