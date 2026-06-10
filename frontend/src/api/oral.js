// src/api/oral.js
import API from './axios';

/**
 * Récupérer la liste des épreuves orales
 */
export const getEpreuvesOral = (params = {}) =>
  API.get('/epreuves-oral/', { params }).then((r) => r.data);

/**
 * Récupérer une épreuve orale spécifique
 */
export const getEpreuveOralDetail = (id) =>
  API.get(`/epreuves-oral/${id}/`).then((r) => r.data);

/**
 * Créer une épreuve orale
 */
export const createEpreuveOral = (payload) =>
  API.post('/epreuves-oral/', payload).then((r) => r.data);

/**
 * Mettre à jour une épreuve orale
 */
export const updateEpreuveOral = (id, payload) =>
  API.patch(`/epreuves-oral/${id}/`, payload).then((r) => r.data);

/**
 * Supprimer une épreuve orale
 */
export const deleteEpreuveOral = (id) =>
  API.delete(`/epreuves-oral/${id}/`).then((r) => r.data);

/**
 * Convoquer automatiquement tous les admis
 */
export const convoquerAdmis = (id) =>
  API.post(`/epreuves-oral/${id}/convoquer_admis/`).then((r) => r.data);

/**
 * Obtenir la liste de passage
 */
export const getListePassage = (id) =>
  API.get(`/epreuves-oral/${id}/liste_passage/`).then((r) => r.data);

/**
 * Enregistrer la décision pour un candidat
 */
export const enregistrerDecision = (id, payload) =>
  API.post(`/epreuves-oral/${id}/enregistrer_decision/`, payload).then((r) => r.data);

/**
 * Inscrire définitivement les candidats acceptés
 */
export const inscrireAcceptes = (id) =>
  API.post(`/epreuves-oral/${id}/inscrire_acceptes/`).then((r) => r.data);

/**
 * Obtenir les statistiques
 */
export const getStatistiquesOral = (id) =>
  API.get(`/epreuves-oral/${id}/statistiques/`).then((r) => r.data);

/**
 * Télécharger le PDF de convocation
 */
export const downloadConvocationPdf = async (convocationId) => {
  const response = await API.get(`/convocations/${convocationId}/telecharger_pdf/`, { responseType: 'blob' });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `Convocation_Oral_ENSA_BM.pdf`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

/**
 * Obtenir ma convocation (Candidat)
 */
export const getMaConvocation = () =>
  API.get('/convocations/ma_convocation/').then((r) => r.data);

/**
 * Importer les admis à l'oral depuis un fichier Excel/CSV
 */
export const importerAdmisOral = (epreuveId, fichier) => {
  const formData = new FormData();
  formData.append('fichier', fichier);
  return API.post(`/epreuves-oral/${epreuveId}/importer-admis-oral/`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((r) => r.data);
};
