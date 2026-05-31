// src/api/epreuves.js
import API from './axios';

/**
 * Récupérer la liste des épreuves
 */
export const getEpreuves = (params = {}) =>
  API.get('/epreuves/', { params }).then((r) => r.data);

/**
 * Récupérer une épreuve spécifique avec ses notes
 */
export const getEpreuveDetail = (id) =>
  API.get(`/epreuves/${id}/`).then((r) => r.data);

/**
 * Créer une nouvelle épreuve
 */
export const createEpreuve = (payload) =>
  API.post('/epreuves/', payload).then((r) => r.data);

/**
 * Mettre à jour une épreuve
 */
export const updateEpreuve = (id, payload) =>
  API.put(`/epreuves/${id}/`, payload).then((r) => r.data);

/**
 * Supprimer une épreuve
 */
export const deleteEpreuve = (id) =>
  API.delete(`/epreuves/${id}/`).then((r) => r.data);

/**
 * Prévisualiser un fichier Excel avant import
 */
export const previsualiserExcel = (id, formData) =>
  API.post(`/epreuves/${id}/previsualiser_excel/`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((r) => r.data);

/**
 * Importer définitivement les notes depuis Excel
 */
export const importerNotesExcel = (id, formData) =>
  API.post(`/epreuves/${id}/importer_notes/`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((r) => r.data);

/**
 * Simuler un changement de seuil (sans l'appliquer)
 */
export const simulerSeuil = (id, seuil) =>
  API.get(`/epreuves/${id}/simuler_seuil/`, { params: { seuil } }).then((r) => r.data);

/**
 * Appliquer un nouveau seuil d'admission
 */
export const changerSeuil = (id, seuil) =>
  API.post(`/epreuves/${id}/changer_seuil/`, { seuil }).then((r) => r.data);

/**
 * Récupérer les statistiques de l'épreuve (distribution, etc.)
 */
export const getEpreuveStats = (id) =>
  API.get(`/epreuves/${id}/statistiques/`).then((r) => r.data);

/**
 * Publier les résultats (irréversible)
 */
export const publierResultats = (id) =>
  API.post(`/epreuves/${id}/publier_resultats/`).then((r) => r.data);

/**
 * Modifier la note d'un candidat manuellement (correction)
 */
export const updateNoteEcrite = (noteId, note) =>
  API.patch(`/notes-ecrites/${noteId}/`, { note }).then((r) => r.data);

/**
 * Télécharger le fichier Excel de template
 */
export const downloadTemplate = async () => {
  const response = await API.get('/epreuves/template_excel/', { responseType: 'blob' });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', 'template_notes.xlsx');
  document.body.appendChild(link);
  link.click();
  link.remove();
};

/**
 * Exporter les résultats (Admis, Recalés, Stats)
 */
export const exportResultats = async (id) => {
  const response = await API.get(`/epreuves/${id}/exporter_resultats/`, { responseType: 'blob' });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `resultats_epreuve_${id}.xlsx`); // Le serveur donne le vrai nom, mais fallback
  document.body.appendChild(link);
  link.click();
  link.remove();
};
