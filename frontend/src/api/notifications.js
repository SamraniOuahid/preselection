// src/api/notifications.js
import API from './axios';

/**
 * Récupérer les notifications de l'utilisateur connecté
 */
export const getMesNotifications = () =>
  API.get('/notifications/mes-notifications/').then((r) => r.data);

/**
 * Récupérer le nombre de notifications non lues
 */
export const getNonLuesCount = () =>
  API.get('/notifications/non-lues/').then((r) => r.data);

/**
 * Marquer une notification spécifique comme lue
 */
export const marquerLue = (id) =>
  API.post(`/notifications/${id}/marquer-lue/`).then((r) => r.data);

/**
 * Marquer toutes les notifications comme lues
 */
export const marquerToutesLues = () =>
  API.post('/notifications/marquer-toutes-lues/').then((r) => r.data);

/**
 * Renvoyer une notification (utile pour le débogage/test)
 */
export const renvoyerNotification = (id) =>
  API.post(`/notifications/${id}/renvoyer/`).then((r) => r.data);
