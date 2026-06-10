/**
 * src/utils/diplome.js
 * Utilitaires pour formater et analyser les valeurs diplome_obtenu.
 *
 * Convention de stockage backend :
 *   - Diplôme liste officielle : "DEUG SMA"
 *   - Diplôme hors liste      : "Autre: DUT Chimie"
 */

/**
 * Formate une valeur diplome_obtenu pour l'affichage.
 * "Autre: DUT Chimie"  →  "DUT Chimie (hors liste officielle)"
 * "DEUG SMA"           →  "DEUG SMA"
 */
export function formatDiplome(valeur) {
  if (!valeur) return '—';
  const match = valeur.match(/^autre\s*:\s*(.+)$/i);
  if (match) {
    return `${match[1].trim()} (hors liste officielle)`;
  }
  return valeur;
}

/**
 * Retourne true si le diplôme est "hors liste officielle".
 */
export function isDiplomeAutre(valeur) {
  if (!valeur) return false;
  return /^autre/i.test(valeur.trim());
}
