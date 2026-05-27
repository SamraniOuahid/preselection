// src/components/layout/Footer.jsx
// Footer institutionnel multi-colonnes — style site officiel ENSA BM
import { ExternalLink, Mail, MapPin, Phone, Globe } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Footer() {
  return (
    <footer className="ensa-footer">
      <div className="ensa-footer-inner">
        <div className="ensa-footer-grid">
          {/* Col 1 — Logo & Description */}
          <div className="ensa-footer-col">
            <div className="ensa-footer-brand">
              <img src="/ensa_logo.png" alt="ENSA BM" className="ensa-footer-logo" />
              <div>
                <div className="ensa-footer-brand-name">ENSA Béni Mellal</div>
                <div className="ensa-footer-brand-uni">Université Sultan Moulay Slimane</div>
              </div>
            </div>
            <p className="ensa-footer-desc">
              Portail officiel de présélection des candidats pour les cycles Ingénieur
              de l'École Nationale des Sciences Appliquées de Béni Mellal.
            </p>
          </div>

          {/* Col 2 — Liens rapides */}
          <div className="ensa-footer-col">
            <h4 className="ensa-footer-heading">Liens rapides</h4>
            <ul className="ensa-footer-links">
              <li><Link to="/">Accueil</Link></li>
              <li><a href="/#filieres">Filières</a></li>
              <li><a href="/#processus">Comment postuler</a></li>
              <li><a href="/#faq">FAQ</a></li>
              <li><Link to="/login">Mon compte</Link></li>
            </ul>
          </div>

          {/* Col 3 — Liens institutionnels */}
          <div className="ensa-footer-col">
            <h4 className="ensa-footer-heading">Liens institutionnels</h4>
            <ul className="ensa-footer-links">
              <li>
                <a href="https://ensabm.usms.ac.ma/" target="_blank" rel="noopener noreferrer">
                  <ExternalLink size={12} /> Site officiel ENSA BM
                </a>
              </li>
              <li>
                <a href="https://www.usms.ac.ma" target="_blank" rel="noopener noreferrer">
                  <ExternalLink size={12} /> Université USMS
                </a>
              </li>
              <li>
                <a href="https://www.enssup.gov.ma" target="_blank" rel="noopener noreferrer">
                  <ExternalLink size={12} /> Ministère de l'Enseignement Supérieur
                </a>
              </li>
            </ul>
          </div>

          {/* Col 4 — Contact */}
          <div className="ensa-footer-col">
            <h4 className="ensa-footer-heading">Contact scolarité</h4>
            <ul className="ensa-footer-contact">
              <li>
                <MapPin size={14} />
                <span>Avenue Moulay Ismaïl, BP 77, Béni Mellal, Maroc</span>
              </li>
              <li>
                <Phone size={14} />
                <span>+212 5 23 48 11 52</span>
              </li>
              <li>
                <Mail size={14} />
                <span>ensabm.contact@usms.ma</span>
              </li>
              <li>
                <Globe size={14} />
                <a href="https://ensabm.usms.ac.ma/" target="_blank" rel="noopener noreferrer">
                  ensabm.usms.ac.ma
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Copyright */}
        <div className="ensa-footer-bottom">
          <span className="ensa-footer-copy">
            © 2025 ENSA Béni Mellal — Université Sultan Moulay Slimane — Tous droits réservés
          </span>
          <div className="ensa-footer-morocco">
            <div className="ensa-morocco-bar" style={{ background: '#006233' }} />
            <div className="ensa-morocco-bar" style={{ background: '#C1272D' }} />
          </div>
        </div>
      </div>
    </footer>
  );
}
