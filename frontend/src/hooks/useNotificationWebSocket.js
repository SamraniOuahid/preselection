// src/hooks/useNotificationWebSocket.js
// Hook React pour la connexion WebSocket et le suivi de progression des notifications

import { useState, useEffect, useRef, useCallback } from 'react';
import { getStoredTokens } from '../api/axios';

export function useNotificationWebSocket(taskId) {
  const [etat, setEtat] = useState({
    connecte: false,
    progression: [],       // liste de tous les envois
    current: 0,
    total: 0,
    pourcentage: 0,
    termine: false,
    resultat: null,        // { envoyes, echecs, ignores, total, details_echecs }
    erreurWs: null,
  });
  const wsRef = useRef(null);
  const pingRef = useRef(null);
  const tentativesRef = useRef(0);

  const connecter = useCallback(() => {
    if (!taskId) return;

    const tokens = getStoredTokens();
    const token = tokens?.access || '';
    
    // console.log('[WS] Token récupéré:', token ? 'OK' : 'NULL');

    const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsHost = window.location.hostname || 'localhost';
    const wsUrl = `${wsProtocol}://${wsHost}:8000/ws/notifications/${taskId}/?token=${token}`;
    
    // console.log('[WS] URL:', wsUrl);

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      // console.log('[WS] Connecté');
      tentativesRef.current = 0;
      setEtat((prev) => ({ ...prev, connecte: true, erreurWs: null }));
      // Ping toutes les 30s pour garder la connexion active
      pingRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }));
        }
      }, 30000);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'progress') {
        setEtat((prev) => ({
          ...prev,
          current: data.current,
          total: data.total,
          pourcentage: data.pourcentage,
          progression: [
            ...prev.progression,
            {
              candidat: data.candidat,
              email: data.email,
              statut: data.statut,
              erreur: data.erreur,
            },
          ],
        }));
      }

      if (data.type === 'termine') {
        clearInterval(pingRef.current);
        setEtat((prev) => ({
          ...prev,
          termine: true,
          connecte: false,
          resultat: {
            envoyes: data.envoyes,
            echecs: data.echecs,
            ignores: data.ignores,
            total: data.total,
            details_echecs: data.details_echecs || [],
          },
        }));
      }
    };

    ws.onerror = (err) => {
      // console.error('[WS] Erreur détectée:', err);
      setEtat((prev) => ({
        ...prev,
        erreurWs: 'Connexion WebSocket perdue.',
        connecte: false,
      }));
    };

    ws.onclose = (event) => {
      clearInterval(pingRef.current);
      // console.log('[WS] Connexion fermée avec le code:', event.code);
      if (event.code === 4001) {
        // console.error('[WS] Rejeté: token invalide ou rôle insuffisant');
        setEtat((prev) => ({
          ...prev,
          erreurWs: 'Session expirée — veuillez vous reconnecter.',
          connecte: false,
        }));
      } else if (event.code !== 1000) {
        if (tentativesRef.current < 3) {
          tentativesRef.current += 1;
          // console.log(`[WS] Reconnexion automatique tentative ${tentativesRef.current}/3 dans 2 secondes...`);
          setTimeout(() => {
            connecter();
          }, 2000);
        }
      } else {
        setEtat((prev) => ({ ...prev, connecte: false }));
      }
    };
  }, [taskId]);

  // Connexion automatique quand taskId change
  useEffect(() => {
    if (taskId) connecter();
    return () => {
      clearInterval(pingRef.current);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [taskId, connecter]);

  // Fonction de reconnexion exposée
  const reconnecter = useCallback(() => {
    if (wsRef.current) wsRef.current.close();
    setEtat((prev) => ({ ...prev, erreurWs: null }));
    tentativesRef.current = 0;
    connecter();
  }, [connecter]);

  return { ...etat, reconnecter };
}
