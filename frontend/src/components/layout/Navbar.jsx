// src/components/layout/Navbar.jsx
// Navigation institutionnelle style site officiel ENSA BM
import { useState, useEffect, useRef } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, Phone, Mail, Globe, ChevronDown } from 'lucide-react';

/* ── Barre d'information supérieure ── */
function TopInfoBar() {
  return (
    <div className="ensa-top-bar">
      <div className="ensa-top-bar-inner">
        <div className="ensa-top-bar-left">
          <a href="tel:+212523481152" className="ensa-top-bar-item">
            <Phone size={12} />
            <span>(+212) 523 48 11 52</span>
          </a>
          <a href="https://ensabm.usms.ac.ma/" target="_blank" rel="noopener noreferrer" className="ensa-top-bar-item">
            <Globe size={12} />
            <span>ensabm.usms.ac.ma</span>
          </a>
          <a href="mailto:ensabm.contact@usms.ma" className="ensa-top-bar-item">
            <Mail size={12} />
            <span>ensabm.contact@usms.ma</span>
          </a>
        </div>
      </div>
    </div>
  );
}

/* ── Menu Dropdown ── */
function NavDropdown({ label, items, isOpen, onToggle, onClose }) {
  const ref = useRef(null);

  useEffect(() => {
    function handleClickOutside(e) {
      if (ref.current && !ref.current.contains(e.target)) onClose();
    }
    if (isOpen) document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen, onClose]);

  return (
    <div ref={ref} className="ensa-nav-dropdown">
      <button
        className={`ensa-nav-link ${isOpen ? 'is-active' : ''}`}
        onClick={onToggle}
        aria-expanded={isOpen}
      >
        <span>{label}</span>
        <ChevronDown size={14} className={`ensa-nav-chevron ${isOpen ? 'is-open' : ''}`} />
      </button>
      {isOpen && (
        <div className="ensa-dropdown-menu">
          {items.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="ensa-dropdown-item"
              onClick={onClose}
            >
              {item.label}
            </a>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [openDropdown, setOpenDropdown] = useState(null);
  const [scrolled, setScrolled] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  // Fermer le mobile menu à chaque navigation
  useEffect(() => {
    setMobileOpen(false);
    setOpenDropdown(null);
  }, [location]);

  const preselectItems = [
    { label: 'Filières disponibles', href: '/#filieres' },
    { label: 'Comment postuler', href: '/#processus' },
    { label: 'Documents requis', href: '/#documents' },
    { label: 'Annonces', href: '/#annonces' },
  ];

  return (
    <>
      <TopInfoBar />
      <header className={`ensa-navbar ${scrolled ? 'is-scrolled' : ''}`}>
        <div className="ensa-navbar-inner">
          {/* Logo */}
          <Link to="/" className="ensa-logo">
            <img src="/ensa_logo.png" alt="ENSA Béni Mellal" className="ensa-logo-img" />
            <div className="ensa-logo-text">
              <span className="ensa-logo-name">ENSA Béni Mellal</span>
              <span className="ensa-logo-sub">Portail de Présélection</span>
            </div>
          </Link>

          {/* Navigation desktop */}
          <nav className="ensa-nav-desktop">
            <a
              href="/"
              className={`ensa-nav-link ${location.pathname === '/' ? 'is-active' : ''}`}
            >
              ACCUEIL
            </a>

            <NavDropdown
              label="PRÉSÉLECTION"
              items={preselectItems}
              isOpen={openDropdown === 'preselection'}
              onToggle={() => setOpenDropdown(openDropdown === 'preselection' ? null : 'preselection')}
              onClose={() => setOpenDropdown(null)}
            />

            <a href="/#faq" className="ensa-nav-link">FAQ</a>

            <a
              href="https://ensabm.usms.ac.ma/"
              target="_blank"
              rel="noopener noreferrer"
              className="ensa-nav-link"
            >
              SITE OFFICIEL
            </a>
          </nav>

          {/* CTA Buttons */}
          <div className="ensa-nav-actions">
            <Link to="/login" className="ensa-nav-btn-outline">
              Se connecter
            </Link>
            <Link to="/register" className="ensa-nav-btn-primary">
              Déposer un dossier
            </Link>
          </div>

          {/* Mobile hamburger */}
          <button
            className="ensa-mobile-toggle"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Menu"
          >
            {mobileOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>

        {/* Menu mobile */}
        {mobileOpen && (
          <div className="ensa-mobile-menu">
            <a href="/" className="ensa-mobile-link" onClick={() => setMobileOpen(false)}>
              ACCUEIL
            </a>
            <div className="ensa-mobile-group">
              <div className="ensa-mobile-group-title">PRÉSÉLECTION</div>
              {preselectItems.map((item) => (
                <a
                  key={item.href}
                  href={item.href}
                  className="ensa-mobile-sublink"
                  onClick={() => setMobileOpen(false)}
                >
                  {item.label}
                </a>
              ))}
            </div>
            <a href="/#faq" className="ensa-mobile-link" onClick={() => setMobileOpen(false)}>
              FAQ
            </a>
            <a
              href="https://ensabm.usms.ac.ma/"
              target="_blank"
              rel="noopener noreferrer"
              className="ensa-mobile-link"
              onClick={() => setMobileOpen(false)}
            >
              SITE OFFICIEL
            </a>
            <div className="ensa-mobile-actions">
              <Link to="/login" className="ensa-nav-btn-outline w-full" onClick={() => setMobileOpen(false)}>
                Se connecter
              </Link>
              <Link to="/register" className="ensa-nav-btn-primary w-full" onClick={() => setMobileOpen(false)}>
                Déposer un dossier
              </Link>
            </div>
          </div>
        )}
      </header>
    </>
  );
}
