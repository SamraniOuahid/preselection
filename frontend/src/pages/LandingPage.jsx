// src/pages/LandingPage.jsx
// Page d'accueil publique — Style site officiel ENSA BM
import { useState, useEffect, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  UserPlus, FileText, Upload, Award, Calendar,
  ChevronRight, ChevronLeft, ChevronDown, GraduationCap, Users,
  FileCheck, Camera, CreditCard, BookOpen, ArrowRight,
  CheckCircle2, Sparkles, ClipboardList, HelpCircle
} from 'lucide-react';

/* ── Hook : intersection observer ── */
function useInView(opts = {}) {
  const ref = useRef(null);
  const [inView, setInView] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(([e]) => {
      if (e.isIntersecting) { setInView(true); obs.unobserve(el); }
    }, { threshold: 0.15, ...opts });
    obs.observe(el);
    return () => obs.disconnect();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  return [ref, inView];
}

/* ── Hook : compteur animé ── */
function useCounter(end, duration = 2000, start = false) {
  const [count, setCount] = useState(0);
  useEffect(() => {
    if (!start) return;
    let t0 = null;
    const step = (ts) => {
      if (!t0) t0 = ts;
      const p = Math.min((ts - t0) / duration, 1);
      setCount(Math.floor(p * end));
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [start, end, duration]);
  return count;
}

/* ── Données ── */
const SLIDES = [
  {
    img: '/hero-slide-1.png',
    tag: 'Concours',
    title: "Concours d'Accès au Cycle Ingénieur",
    subtitle: 'Session 2025 — Déposez votre candidature en ligne',
  },
  {
    img: '/hero-slide-2.png',
    tag: 'Présélection',
    title: 'Présélection rigoureuse et transparente',
    subtitle: 'Votre dossier est étudié par la commission pédagogique de l\'ENSA',
  },
  {
    img: '/hero-slide-3.png',
    tag: 'Excellence',
    title: 'ENSA Béni Mellal — Excellence en Ingénierie',
    subtitle: "Rejoignez l'une des meilleures écoles d'ingénieurs du Maroc",
  },
];

const SERVICES = [
  { Icon: UserPlus, title: 'Espace Candidat', desc: 'Créez votre compte et gérez votre dossier', to: '/register', color: '#2E86C1' },
  { Icon: ClipboardList, title: 'Suivi de Dossier', desc: 'Suivez l\'état de votre candidature en temps réel', to: '/login', color: '#27AE60' },
  { Icon: GraduationCap, title: 'Filières Disponibles', desc: 'Consultez les filières ouvertes au concours', href: '#filieres', color: '#8E44AD' },
  { Icon: HelpCircle, title: 'Aide & FAQ', desc: 'Trouvez les réponses à vos questions', href: '#faq', color: '#E67E22' },
];

const ETAPES = [
  { num: 1, label: 'Inscription en ligne', desc: 'Créez votre compte candidat en quelques clics', Icon: UserPlus, color: '#2E86C1' },
  { num: 2, label: 'Dépôt des pièces justificatives', desc: 'Saisissez vos informations et joignez vos documents officiels (PDF)', Icon: Upload, color: '#8E44AD' },
  { num: 3, label: 'Étude du dossier', desc: 'Votre dossier est examiné par nos services pédagogiques', Icon: FileText, color: '#27AE60' },
  { num: 4, label: 'Publication des résultats', desc: 'Consultez les résultats de présélection en ligne', Icon: Award, color: '#C0392B' },
];

const FILIERES = [
  { code: 'G2ER', nom: "Génie Électrique et Énergies Renouvelables", coordinateur: "Coordinateur : Pr. OULCAID MOSTAPHA", places: 30, ouvert: true },
  { code: 'IAA', nom: "Industries Agroalimentaires", coordinateur: "Coordinateur : Pr. ROKNI YAHYA", places: 30, ouvert: true },
  { code: 'IACS', nom: "Intelligence Artificielle et Cybersécurité", coordinateur: "Coordinateur : Pr. GOUSKIR MOHAMED", places: 35, ouvert: true },
  { code: 'TDI', nom: "Transformation Digitale Industrielle", coordinateur: "Coordinateur : Pr. OUANAN HAMID", places: 40, ouvert: true },
];

const ANNONCES = [
  {
    date: '15 Mai 2025', cat: 'Concours',
    title: "Ouverture des inscriptions — Session 2025",
    excerpt: "Les inscriptions au concours d'accès au cycle ingénieur sont ouvertes du 15 mai au 30 juin 2025.",
  },
  {
    date: '10 Mai 2025', cat: 'Information',
    title: 'Documents requis pour la candidature',
    excerpt: 'Préparez votre diplôme, relevés de notes, CIN et photo avant de soumettre votre dossier.',
  },
  {
    date: '01 Mai 2025', cat: 'Résultats',
    title: 'Calendrier de publication des résultats',
    excerpt: 'Les résultats de présélection seront publiés progressivement à partir de juillet 2025.',
  },
];

const DOCUMENTS = [
  { label: 'Diplôme ou attestation de réussite', format: 'PDF', maxSize: '5 Mo', conseil: 'Scan couleur lisible', Icon: GraduationCap },
  { label: 'Relevé de notes complet', format: 'PDF', maxSize: '5 Mo', conseil: 'Toutes les années concernées', Icon: BookOpen },
  { label: 'CIN (recto-verso)', format: 'PDF ou Image', maxSize: '5 Mo', conseil: 'Scan ou photo nette', Icon: CreditCard },
  { label: "Photo d'identité", format: 'JPG, PNG', maxSize: '2 Mo', conseil: 'Fond blanc, récente', Icon: Camera },
];

/* ── Hero Slider ── */
function HeroSlider() {
  const [current, setCurrent] = useState(0);
  const timerRef = useRef(null);

  const goTo = useCallback((i) => setCurrent(i), []);
  const next = useCallback(() => setCurrent((c) => (c + 1) % SLIDES.length), []);
  const prev = useCallback(() => setCurrent((c) => (c - 1 + SLIDES.length) % SLIDES.length), []);

  useEffect(() => {
    timerRef.current = setInterval(next, 6000);
    return () => clearInterval(timerRef.current);
  }, [next]);

  const resetTimer = () => {
    clearInterval(timerRef.current);
    timerRef.current = setInterval(next, 6000);
  };

  return (
    <section className="ensa-hero">
      {SLIDES.map((slide, i) => (
        <div key={i} className={`ensa-hero-slide ${i === current ? 'is-active' : ''}`}>
          <img src={slide.img} alt="" className="ensa-hero-slide-img" loading={i === 0 ? 'eager' : 'lazy'} />
          <div className="ensa-hero-slide-overlay" />
        </div>
      ))}

      <div className="ensa-hero-content">
        <div className="ensa-hero-tag">{SLIDES[current].tag}</div>
        <h1 className="ensa-hero-title" key={`t-${current}`}>{SLIDES[current].title}</h1>
        <p className="ensa-hero-subtitle" key={`s-${current}`}>{SLIDES[current].subtitle}</p>
        <div className="ensa-hero-actions">
          <Link to="/register" className="ensa-hero-btn-primary">
            <span>Commencer ma candidature</span>
            <ArrowRight size={18} />
          </Link>
          <a href="#filieres" className="ensa-hero-btn-secondary">
            <span>Consulter les filières</span>
            <ChevronRight size={18} />
          </a>
        </div>
      </div>

      {/* Arrows */}
      <button className="ensa-hero-arrow ensa-hero-arrow-left" onClick={() => { prev(); resetTimer(); }} aria-label="Précédent">
        <ChevronLeft size={24} />
      </button>
      <button className="ensa-hero-arrow ensa-hero-arrow-right" onClick={() => { next(); resetTimer(); }} aria-label="Suivant">
        <ChevronRight size={24} />
      </button>

      {/* Dots */}
      <div className="ensa-hero-dots">
        {SLIDES.map((_, i) => (
          <button
            key={i}
            className={`ensa-hero-dot ${i === current ? 'is-active' : ''}`}
            onClick={() => { goTo(i); resetTimer(); }}
            aria-label={`Slide ${i + 1}`}
          />
        ))}
      </div>

      {/* Session Banner */}
      <div className="ensa-hero-session">
        <Calendar size={16} />
        <div>
          <span className="ensa-hero-session-label">Session 2025</span>
          <span className="ensa-hero-session-date">Du 15 mai au 30 juin 2025</span>
        </div>
        <div className="ensa-hero-session-pulse" />
      </div>
    </section>
  );
}

/* ── Section Services ── */
function ServicesSection() {
  const [ref, inView] = useInView();
  return (
    <section className="ensa-services" ref={ref}>
      <div className="ensa-container">
        <div className="ensa-services-header">
          <h2 className="ensa-services-title">Nos Services</h2>
          <Link to="/register" className="ensa-services-more">
            Voir plus de services <ChevronRight size={16} />
          </Link>
        </div>
        <div className={`ensa-services-grid ${inView ? 'is-visible' : ''}`}>
          {SERVICES.map((s, i) => {
            const Wrapper = s.to ? Link : 'a';
            const props = s.to ? { to: s.to } : { href: s.href };
            return (
              <Wrapper key={i} {...props} className="ensa-service-card" style={{ animationDelay: `${i * 0.1}s`, '--accent': s.color }}>
                <div className="ensa-service-icon" style={{ background: s.color }}>
                  <s.Icon size={24} strokeWidth={2} />
                </div>
                <h3 className="ensa-service-name">{s.title}</h3>
                <p className="ensa-service-desc">{s.desc}</p>
              </Wrapper>
            );
          })}
        </div>
      </div>
    </section>
  );
}

/* ── Section Processus (Timeline) ── */
function ProcessSection() {
  const [ref, inView] = useInView();
  return (
    <section id="processus" className="ensa-section ensa-section-white">
      <div ref={ref} className="ensa-container">
        <div className="ensa-section-header">
          <span className="ensa-badge-section">Comment ça marche</span>
          <h2 className="ensa-section-title">Déposez votre candidature en <span className="ensa-text-gradient">4 étapes simples</span></h2>
          <p className="ensa-section-desc">Un processus entièrement dématérialisé, rapide et transparent</p>
        </div>
        <div className={`ensa-timeline ${inView ? 'is-visible' : ''}`}>
          {ETAPES.map((e, i) => (
            <div key={e.num} className="ensa-timeline-item" style={{ animationDelay: `${i * 0.15}s` }}>
              <div className="ensa-timeline-marker" style={{ background: e.color }}>
                <e.Icon size={20} strokeWidth={2} />
              </div>
              <div className="ensa-timeline-connector" />
              <div className="ensa-timeline-content">
                <span className="ensa-timeline-step">Étape {e.num}</span>
                <h3 className="ensa-timeline-label">{e.label}</h3>
                <p className="ensa-timeline-desc">{e.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function FiliereColumn({ title, icon, data, accent }) {
  return (
    <div className="ensa-filiere-col">
      <div className="ensa-filiere-col-header" style={{ '--col-accent': accent }}>
        <div className="ensa-filiere-col-icon">{icon}</div>
        <div>
          <h3 className="ensa-filiere-col-title">{title}</h3>
          <p className="ensa-filiere-col-places">{data.reduce((s, f) => s + f.places, 0)} places au total</p>
        </div>
      </div>
      <div className="ensa-filiere-list">
        {data.map((f, i) => (
          <div key={f.code} className="ensa-filiere-card" style={{ animationDelay: `${i * 0.08}s` }}>
            <div className="ensa-filiere-info">
              <span className="ensa-filiere-code" style={{ color: accent, background: accent + '15' }}>{f.code}</span>
              <div>
                <div className="ensa-filiere-name">{f.nom}</div>
                {f.coordinateur && <div className="text-xs text-text-secondary mt-1">{f.coordinateur}</div>}
                <div className="ensa-filiere-meta mt-2">
                  <Users size={12} /><span>{f.places} places</span>
                  <span className={`ensa-filiere-status ${f.ouvert ? 'is-open' : 'is-closed'}`}>
                    {f.ouvert ? '● Ouvert' : '● Fermé'}
                  </span>
                </div>
              </div>
            </div>
            {f.ouvert && (
              <Link to="/register" className="ensa-filiere-cta" style={{ color: accent, background: accent + '12' }}>
                Postuler <ArrowRight size={14} />
              </Link>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Section Filières ── */
function FilieresSection() {
  const [ref, inView] = useInView();
  const col1 = FILIERES.slice(0, 2);
  const col2 = FILIERES.slice(2, 4);

  return (
    <section id="filieres" className="ensa-section ensa-section-gray">
      <div ref={ref} className="ensa-container">
        <div className="ensa-section-header">
          <span className="ensa-badge-section">Formations</span>
          <h2 className="ensa-section-title">Filières <span className="ensa-text-gradient">disponibles</span></h2>
          <p className="ensa-section-desc">Quatre filières spécialisées de 3 ans, accessibles à l'issue du cycle préparatoire ou par admission parallèle.</p>
        </div>
        <div className={`ensa-filieres-grid ${inView ? 'is-visible' : ''}`}>
          <FiliereColumn title="Cycle Ingénieur" icon={<GraduationCap size={20} />} data={col1} accent="#2E86C1" />
          <FiliereColumn title="Cycle Ingénieur" icon={<GraduationCap size={20} />} data={col2} accent="#8E44AD" />
        </div>
      </div>
    </section>
  );
}

/* ── Section Annonces ── */
function AnnoncesSection() {
  const [ref, inView] = useInView();
  return (
    <section id="annonces" className="ensa-section ensa-section-white">
      <div ref={ref} className="ensa-container">
        <div className="ensa-section-header">
          <span className="ensa-badge-section">Actualités</span>
          <h2 className="ensa-section-title">Annonces <span className="ensa-text-gradient">Importantes</span></h2>
          <p className="ensa-section-desc">Restez informé des dernières nouvelles du concours</p>
        </div>
        <div className={`ensa-annonces-grid ${inView ? 'is-visible' : ''}`}>
          {ANNONCES.map((a, i) => (
            <div key={i} className="ensa-annonce-card" style={{ animationDelay: `${i * 0.1}s` }}>
              <div className="ensa-annonce-top">
                <span className="ensa-annonce-cat">{a.cat}</span>
                <span className="ensa-annonce-date">{a.date}</span>
              </div>
              <h3 className="ensa-annonce-title">{a.title}</h3>
              <p className="ensa-annonce-excerpt">{a.excerpt}</p>
              <a href="#" className="ensa-annonce-link">
                En savoir plus <ArrowRight size={14} />
              </a>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function StatItem({ value, suffix, label, inView }) {
  const count = useCounter(value, 2000, inView);
  return (
    <div className="ensa-stat-item">
      <div className="ensa-stat-number">{count}{suffix}</div>
      <div className="ensa-stat-label">{label}</div>
    </div>
  );
}

/* ── Section Statistiques ── */
function StatsSection() {
  const [ref, inView] = useInView();
  const stats = [
    { value: 731, suffix: '+', label: 'Étudiants' },
    { value: 35, suffix: '', label: 'Professeurs' },
    { value: 10, suffix: '', label: 'Personnels' },
    { value: 4, suffix: '', label: 'Formations' },
    { value: 2, suffix: '', label: 'Laboratoires' },
  ];
  return (
    <section className="ensa-stats" ref={ref}>
      <div className="ensa-stats-overlay" />
      <div className="ensa-container" style={{ position: 'relative', zIndex: 1, textAlign: 'center', marginBottom: '40px' }}>
        <h2 className="ensa-section-title" style={{ color: '#fff' }}>
          ENSABM en <span style={{ background: 'linear-gradient(135deg, #6DD5FA 0%, #FFFFFF 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>chiffres</span>
        </h2>
        <p className="ensa-section-desc" style={{ color: 'rgba(255,255,255,0.8)' }}>
          L'École Nationale des Sciences Appliquées de Béni Mellal en quelques données clés.<br />
          <span style={{ display: 'inline-block', marginTop: '12px', fontSize: '13px', fontWeight: 'bold', padding: '6px 16px', background: 'rgba(255,255,255,0.1)', borderRadius: '100px', border: '1px solid rgba(255,255,255,0.2)' }}>
            Année académique 2024–2025
          </span>
        </p>
      </div>
      <div className="ensa-container ensa-stats-inner">
        {stats.map((s, i) => (
          <StatItem key={i} value={s.value} suffix={s.suffix} label={s.label} inView={inView} />
        ))}
      </div>
    </section>
  );
}

/* ── Section Documents ── */
function DocumentsSection() {
  const [ref, inView] = useInView();
  return (
    <section id="documents" className="ensa-section ensa-section-gray">
      <div ref={ref} className="ensa-container">
        <div className="ensa-section-header">
          <span className="ensa-badge-section">Préparation</span>
          <h2 className="ensa-section-title">Documents <span className="ensa-text-gradient">requis</span></h2>
          <p className="ensa-section-desc">Préparez ces documents avant de commencer votre candidature</p>
        </div>
        <div className={`ensa-docs-grid ${inView ? 'is-visible' : ''}`}>
          {DOCUMENTS.map((doc, i) => (
            <div key={doc.label} className="ensa-doc-card" style={{ animationDelay: `${i * 0.1}s` }}>
              <div className="ensa-doc-icon"><doc.Icon size={24} strokeWidth={1.8} /></div>
              <h3 className="ensa-doc-title">{doc.label}</h3>
              <div className="ensa-doc-details">
                <div className="ensa-doc-detail"><FileCheck size={13} /><span>Format : {doc.format}</span></div>
                <div className="ensa-doc-detail"><Upload size={13} /><span>Max : {doc.maxSize}</span></div>
              </div>
              <div className="ensa-doc-tip"><CheckCircle2 size={13} /><span>{doc.conseil}</span></div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ── FAQ ── */
function FaqSection() {
  const [openFaq, setOpenFaq] = useState(null);
  const [ref, inView] = useInView();
  const faqs = [
    { q: 'Quels sont les diplômes acceptés pour le cycle Bac+2 ?', a: 'Les candidats titulaires d\'un DUT, BTS, DEUG, DEUST ou diplôme équivalent Bac+2 dans les domaines scientifiques et techniques sont éligibles.' },
    { q: 'Comment fonctionne la présélection ?', a: 'Les dossiers sont examinés par la commission pédagogique de l\'ENSA sur la base des critères académiques définis dans le règlement du concours. Chaque dossier est évalué selon le parcours, les notes obtenues et la conformité des pièces fournies.' },
    { q: 'Puis-je modifier mon dossier après soumission ?', a: 'Non, une fois le dossier soumis, il ne peut plus être modifié. Assurez-vous de bien vérifier toutes les informations avant la soumission finale.' },
    { q: 'Quand seront publiés les résultats ?', a: 'Les résultats de présélection sont publiés progressivement. Vous recevrez une notification par email dès que votre dossier est traité.' },
    { q: 'Quels formats de documents sont acceptés ?', a: 'Les diplômes et relevés doivent être en PDF. La CIN peut être en PDF ou image (JPG, PNG). La photo d\'identité en JPG ou PNG. Max 5 Mo par document.' },
  ];

  return (
    <section id="faq" className="ensa-section ensa-section-white">
      <div ref={ref} className="ensa-container" style={{ maxWidth: 800 }}>
        <div className="ensa-section-header">
          <span className="ensa-badge-section">Aide</span>
          <h2 className="ensa-section-title">Questions <span className="ensa-text-gradient">fréquentes</span></h2>
          <p className="ensa-section-desc">Tout ce que vous devez savoir avant de postuler</p>
        </div>
        <div className={`ensa-faq-list ${inView ? 'is-visible' : ''}`}>
          {faqs.map((faq, i) => (
            <div key={i} className={`ensa-faq-item ${openFaq === i ? 'is-open' : ''}`}>
              <button className="ensa-faq-trigger" onClick={() => setOpenFaq(openFaq === i ? null : i)}>
                <span className="ensa-faq-question">{faq.q}</span>
                <ChevronDown size={18} className={`ensa-faq-chevron ${openFaq === i ? 'is-rotated' : ''}`} />
              </button>
              <div className={`ensa-faq-content ${openFaq === i ? 'is-open' : ''}`}>
                <p className="ensa-faq-answer">{faq.a}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ── CTA Final ── */
function CtaSection() {
  return (
    <section className="ensa-cta">
      <div className="ensa-cta-bg" />
      <div className="ensa-cta-content">
        <div className="ensa-cta-badge"><Sparkles size={14} /><span>Session 2025 ouverte</span></div>
        <h2 className="ensa-cta-title">Prêt à rejoindre l'ENSA Béni Mellal ?</h2>
        <p className="ensa-cta-desc">
          Créez votre compte et déposez votre dossier de candidature en quelques minutes.
          <br />Le processus est entièrement en ligne, rapide et sécurisé.
        </p>
        <div className="ensa-cta-actions">
          <Link to="/register" className="ensa-cta-btn-main"><span>Commencer ma candidature</span><ArrowRight size={18} /></Link>
          <Link to="/login" className="ensa-cta-btn-login">J'ai déjà un compte</Link>
        </div>
      </div>
    </section>
  );
}

/* ══════════ COMPOSANT PRINCIPAL ══════════ */
export default function LandingPage() {
  return (
    <div className="ensa-landing">
      <HeroSlider />
      <ServicesSection />
      <ProcessSection />
      <FilieresSection />
      <AnnoncesSection />
      <StatsSection />
      <DocumentsSection />
      <FaqSection />
      <CtaSection />
    </div>
  );
}
