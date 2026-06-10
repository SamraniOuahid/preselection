// src/components/candidat/SemestreForm.jsx
import React from 'react';

/**
 * Détermine la mention associée à une moyenne semestrielle.
 * Barème :
 * - 10.00 à 11.99 ➔ Passable ('PASSABLE')
 * - 12.00 à 13.99 ➔ Assez Bien ('ASSEZ_BIEN')
 * - 14.00 à 15.99 ➔ Bien ('BIEN')
 * - 16.00 à 20.00 ➔ Très Bien ('TRES_BIEN')
 */
export function getMentionByNote(note) {
  const n = parseFloat(note);
  if (isNaN(n) || n < 10 || n > 20) return '';
  if (n >= 16) return 'TRES_BIEN';
  if (n >= 14) return 'BIEN';
  if (n >= 12) return 'ASSEZ_BIEN';
  return 'PASSABLE';
}

export function getMentionLabel(mentionCode) {
  switch (mentionCode) {
    case 'TRES_BIEN': return 'Très Bien';
    case 'BIEN': return 'Bien';
    case 'ASSEZ_BIEN': return 'Assez Bien';
    case 'PASSABLE': return 'Passable';
    default: return '—';
  }
}

export default function SemestreForm({ notesSemestres, onUpdateNote }) {
  return (
    <div className="ensa-notes-list space-y-4">
      {notesSemestres.map((note, i) => {
        const mention = getMentionByNote(note.moyenne);
        const isError = note.moyenne !== '' && (parseFloat(note.moyenne) < 10 || parseFloat(note.moyenne) > 20);

        return (
          <div key={i} className="ensa-note-row" style={{ display: 'grid', gridTemplateColumns: '80px 1fr 1fr 1fr', gap: '10px', alignItems: 'start' }}>
            <div className="font-bold text-primary-700 bg-primary-50 text-center py-2.5 rounded-lg border border-primary-100 flex items-center justify-center h-[42px] mt-6">
              {note.semestre}
            </div>
            
            <div>
              <label className="text-xs font-semibold text-text-muted mb-1.5 block">Moyenne /20</label>
              <input 
                type="number" 
                step="0.01" 
                min="10" 
                max="20" 
                className={`input font-mono w-full ${isError ? 'border-danger-500 focus:border-danger-500 focus:ring-danger-200 bg-danger-50' : ''}`}
                placeholder="Ex: 14.50" 
                value={note.moyenne} 
                onChange={(e) => {
                  let val = e.target.value;
                  onUpdateNote(i, 'moyenne', val);
                  const newMention = getMentionByNote(val);
                  if (newMention) {
                    onUpdateNote(i, 'mention', newMention);
                  }
                }} 
              />
              {isError && (
                <p className="text-[10px] text-danger-600 mt-1 font-medium">La moyenne doit être entre 10 et 20.</p>
              )}
            </div>

            <div>
              <label className="text-xs font-semibold text-text-muted mb-1.5 block">Session</label>
              <select 
                className="input w-full" 
                value={note.session} 
                onChange={(e) => onUpdateNote(i, 'session', e.target.value)}
              >
                <option value="NORMALE">Normale</option>
                <option value="RATTRAPAGE">Rattrapage</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-text-muted mb-1.5 block">Mention</label>
              {/* Badge "Read-Only" grisé et stylisé pour la mention */}
              <div className="w-full h-[42px] px-3 bg-gray-100 border border-gray-200 text-gray-500 rounded-lg text-sm font-medium flex items-center justify-center cursor-not-allowed select-none">
                {getMentionLabel(mention)}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
