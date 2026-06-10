// src/layouts/PublicLayout.jsx
// Layout deux colonnes pour les pages d'authentification — style ENSA BM
import { useState, useEffect } from 'react';
import { Outlet, Link } from 'react-router-dom';

/* ── Hook : compteur animé pour les stats ── */
function useCounter(end, duration = 1500) {
  const [count, setCount] = useState(0);
  useEffect(() => {
    let t0 = null;
    const step = (ts) => {
      if (!t0) t0 = ts;
      const p = Math.min((ts - t0) / duration, 1);
      setCount(Math.floor(p * end));
      if (p < 1) requestAnimationFrame(step);
    };
    const frame = requestAnimationFrame(step);
    return () => cancelAnimationFrame(frame);
  }, [end, duration]);
  return count;
}

const SLIDES = [
  {
    img: '/hero-slide-1.png',
    title: "Portail Officiel de Présélection",
    desc: "Plateforme dédiée à la présélection des candidats pour les cycles Ingénieur Bac+2 et Bac+3. Déposez votre dossier en ligne et suivez son avancement en temps réel."
  },
  {
    img: '/hero-slide-2.png',
    title: "Présélection Intelligente & Automatisée",
    desc: "Analyse intelligente de votre dossier pour un traitement rapide, équitable et transparent de votre candidature."
  },
  {
    img: '/hero-slide-3.png',
    title: "ENSA Béni Mellal — Excellence en Ingénierie",
    desc: "Rejoignez l'une des meilleures écoles d'ingénieurs du Maroc. Des formations de haut niveau adaptées aux défis technologiques de demain."
  }
];

export default function PublicLayout() {
  const [current, setCurrent] = useState(0);

  // Auto-rotation des slides toutes les 6 secondes
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrent((c) => (c + 1) % SLIDES.length);
    }, 6000);
    return () => clearInterval(timer);
  }, []);

  // Valeurs des compteurs
  const filieresCount = useCounter(6, 1200);
  const placesCount = useCounter(180, 1500);
  const satisfactionCount = useCounter(95, 1500);

  return (
    <div className="min-h-screen flex flex-col lg:flex-row">
      {/* Colonne gauche — Branding ENSA avec Slider Dynamique */}
      <div className="hidden lg:flex lg:w-[45%] xl:w-[42%] relative overflow-hidden flex-col justify-between p-10">
        
        {/* Slides d'arrière-plan animés (comme sur la page d'accueil) */}
        {SLIDES.map((slide, i) => (
          <div key={i} className={`ensa-hero-slide ${i === current ? 'is-active' : ''}`}>
            <img src={slide.img} alt="" className="ensa-hero-slide-img" loading={i === 0 ? 'eager' : 'lazy'} />
            <div className="ensa-hero-slide-overlay" />
          </div>
        ))}

        {/* Logo ENSA réel */}
        <div className="relative z-10">
          <Link to="/" className="flex items-center gap-3 no-underline mb-12 group">
            <img 
              src="/ensa_logo.png" 
              alt="ENSA BM" 
              className="h-16 w-auto object-contain bg-white p-1.5 rounded-xl shadow-md transition-transform duration-300 group-hover:scale-105" 
            />
          </Link>
        </div>

        {/* Description & Contenus interactifs */}
        <div className="relative z-10 max-w-md">
          {/* Dots indicateurs interactifs de slide */}
          <div className="flex gap-2 mb-6">
            {SLIDES.map((_, i) => (
              <button
                key={i}
                className={`h-1.5 rounded-full transition-all duration-300 ${
                  i === current ? 'bg-white w-6' : 'bg-white/30 hover:bg-white/50'
                }`}
                onClick={() => setCurrent(i)}
                aria-label={`Slide ${i + 1}`}
                style={{ border: 'none', cursor: 'pointer', padding: 0 }}
              />
            ))}
          </div>

          <h2 
            className="text-white text-2xl font-bold leading-snug mb-4 font-display animate-fade-in" 
            key={`t-${current}`}
          >
            {SLIDES[current].title}
          </h2>
          <p 
            className="text-white/60 text-sm leading-relaxed mb-8 animate-fade-in" 
            style={{ animationDelay: '0.1s' }} 
            key={`s-${current}`}
          >
            {SLIDES[current].desc}
          </p>

          {/* Statistiques rapides animées */}
          <div className="flex gap-10 mb-8 border-t border-white/10 pt-6">
            <div className="transition-transform duration-300 hover:scale-105">
              <div className="text-white font-bold text-2xl font-display">{filieresCount}</div>
              <div className="text-white/40 text-xs mt-0.5">Filières</div>
            </div>
            <div className="transition-transform duration-300 hover:scale-105">
              <div className="text-white font-bold text-2xl font-display">{placesCount}+</div>
              <div className="text-white/40 text-xs mt-0.5">Places</div>
            </div>
            <div className="transition-transform duration-300 hover:scale-105">
              <div className="text-white font-bold text-2xl font-display">{satisfactionCount}%</div>
              <div className="text-white/40 text-xs mt-0.5">Satisfaction</div>
            </div>
          </div>

          {/* Barre décorative marocaine */}
          <div className="flex items-center gap-2">
            <div className="w-8 h-1 rounded-full bg-[#006233]/60" />
            <div className="w-8 h-1 rounded-full bg-[#C1272D]/60" />
            <div className="w-12 h-1 rounded-full bg-white/20" />
          </div>
        </div>

        {/* Footer branding */}
        <div className="relative z-10 text-white/25 text-xs">
          © {new Date().getFullYear()} ENSA Béni Mellal — Tous droits réservés
        </div>
      </div>

      {/* Colonne droite — Formulaire avec transitions fluides */}
      <div className="flex-1 flex flex-col justify-center items-center px-5 py-8 sm:px-8 sm:py-10 bg-surface">
        {/* Logo mobile */}
        <div className="lg:hidden mb-8 text-center animate-fade-in">
          <Link to="/" className="flex items-center justify-center gap-3 no-underline mb-2">
            <img src="/ensa_logo.png" alt="ENSA BM" className="h-12 w-auto object-contain bg-white p-1 rounded-md shadow-sm" />
          </Link>
        </div>

        <div className="w-full max-w-[440px]">
          <div className="card p-7 sm:p-8 md:p-10 transition-all duration-300">
            <Outlet />
          </div>

          {/* Lien retour */}
          <div className="text-center mt-5 animate-fade-in" style={{ animationDelay: '0.4s' }}>
            <Link to="/" className="text-sm text-text-muted hover:text-primary-700 no-underline transition-all duration-200 inline-flex items-center gap-1 hover:gap-2">
              <span>← Retour à l'accueil</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
