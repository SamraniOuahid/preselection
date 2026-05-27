// src/components/common/ScoreGauge.jsx
// Jauge semi-circulaire SVG pour afficher un score sur 20

export default function ScoreGauge({ score, value, max = 20, size = 140, label = 'Score' }) {
  const rawScore = score ?? value ?? 0;
  const normalizedScore = Math.min(Math.max(rawScore, 0), max);
  const percentage = (normalizedScore / max) * 100;

  // Paramètres SVG pour l'arc semi-circulaire
  const strokeWidth = 10;
  const radius = (size - strokeWidth) / 2;
  const cx = size / 2;
  const cy = size / 2;

  // Arc de 180° (semi-cercle, de gauche à droite en passant par le haut)
  const circumference = Math.PI * radius;
  const offset = circumference - (percentage / 100) * circumference;

  // Couleur selon le score
  const getColor = () => {
    if (percentage >= 75) return '#27AE60';
    if (percentage >= 50) return '#2E86C1';
    if (percentage >= 35) return '#F39C12';
    return '#C0392B';
  };

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size / 2 + 16} viewBox={`0 0 ${size} ${size / 2 + 16}`}>
        {/* Arc de fond */}
        <path
          d={`M ${strokeWidth / 2} ${cy} A ${radius} ${radius} 0 0 1 ${size - strokeWidth / 2} ${cy}`}
          fill="none"
          stroke="#EBEDEF"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />
        {/* Arc de progression */}
        <path
          d={`M ${strokeWidth / 2} ${cy} A ${radius} ${radius} 0 0 1 ${size - strokeWidth / 2} ${cy}`}
          fill="none"
          stroke={getColor()}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 0.6s ease' }}
        />
        {/* Valeur centrale */}
        <text
          x={cx}
          y={cy - 4}
          textAnchor="middle"
          fill="var(--color-text-primary)"
          fontSize="22"
          fontWeight="700"
          fontFamily="'JetBrains Mono', monospace"
        >
          {normalizedScore.toFixed(2)}
        </text>
        <text
          x={cx}
          y={cy + 14}
          textAnchor="middle"
          fill="var(--color-text-muted)"
          fontSize="11"
          fontWeight="500"
        >
          / {max}
        </text>
      </svg>
      {label && (
        <span className="text-xs text-text-secondary font-medium mt-1">{label}</span>
      )}
    </div>
  );
}
