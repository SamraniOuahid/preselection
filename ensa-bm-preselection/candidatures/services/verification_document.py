# candidatures/services/verification_document.py
"""
Service de vérification d'authenticité des documents — ENSA BM
Vérifie à 4 niveaux : structure, métadonnées, cohérence, manipulation.
"""
from __future__ import annotations
import hashlib, io, logging, mimetypes, os, re
from collections import Counter
from decimal import Decimal
from typing import Any

import pdfplumber
from PIL import Image
from django.conf import settings

try:
    import magic as python_magic
except ImportError:
    python_magic = None

try:
    import pytesseract
except ImportError:
    pytesseract = None

from candidatures.models import Document, Dossier, NoteMatiere

logger = logging.getLogger(__name__)

# Outils de falsification connus
OUTILS_RETOUCHE = ['photoshop', 'gimp', 'paint.net', 'canva', 'inkscape']
OUTILS_EDITEUR = ['microsoft word', 'libreoffice writer', 'google docs', 'wondershare']
OUTILS_PDF = ['smallpdf', 'ilovepdf', 'pdf24']

POIDS_TYPE = {'RELEVE': 0.40, 'DIPLOME': 0.30, 'CIN': 0.20, 'PHOTO': 0.10}


def _get_file_path(document: Document) -> str | None:
    try:
        return document.fichier.path
    except Exception:
        return None


def _read_file_bytes(document: Document) -> bytes | None:
    try:
        document.fichier.seek(0)
        return document.fichier.read()
    except Exception:
        return None


def _detect_real_mime(file_path: str) -> str:
    if python_magic:
        try:
            return python_magic.from_file(file_path, mime=True)
        except Exception:
            pass
    guessed, _ = mimetypes.guess_type(file_path)
    return guessed or 'application/octet-stream'


# ═══════════════════════════════════════════════
# NIVEAU 1 — Vérification structurelle
# ═══════════════════════════════════════════════
def verifier_structure(document: Document) -> dict:
    alertes, penalite = [], 0.0
    file_path = _get_file_path(document)

    # Fichier existe ?
    if not file_path or not os.path.exists(file_path):
        return {'penalite': 1.0, 'alertes': ['CRITIQUE: Fichier manquant sur le disque']}

    taille = os.path.getsize(file_path)
    taille_ko = taille / 1024

    if taille_ko < 10:
        penalite += 0.4
        alertes.append(f'Fichier trop petit ({taille_ko:.1f} Ko) — probablement vide')
    if taille_ko > 5120:
        penalite += 0.1
        alertes.append(f'Fichier volumineux ({taille_ko:.0f} Ko)')

    # Vérification MIME
    real_mime = _detect_real_mime(file_path)
    if document.mime_type and real_mime != document.mime_type:
        penalite += 0.3
        alertes.append(f'MIME déclaré ({document.mime_type}) ≠ réel ({real_mime})')

    # Vérification intégrité
    contenu = _read_file_bytes(document)
    if contenu:
        if real_mime == 'application/pdf':
            try:
                with pdfplumber.open(io.BytesIO(contenu)) as pdf:
                    _ = len(pdf.pages)
            except Exception:
                penalite += 0.5
                alertes.append('PDF corrompu — impossible à ouvrir')
        elif real_mime and real_mime.startswith('image/'):
            try:
                Image.open(io.BytesIO(contenu)).verify()
            except Exception:
                penalite += 0.5
                alertes.append('Image corrompue')

    return {'penalite': penalite, 'alertes': alertes}


# ═══════════════════════════════════════════════
# NIVEAU 2 — Analyse métadonnées PDF
# ═══════════════════════════════════════════════
def verifier_metadonnees_pdf(document: Document) -> dict:
    alertes, penalite = [], 0.0
    contenu = _read_file_bytes(document)
    if not contenu:
        return {'penalite': 0.0, 'alertes': []}

    try:
        with pdfplumber.open(io.BytesIO(contenu)) as pdf:
            meta = pdf.metadata or {}
    except Exception:
        return {'penalite': 0.1, 'alertes': ['Métadonnées PDF illisibles']}

    if not meta:
        penalite += 0.10
        alertes.append('Aucune métadonnée dans le PDF')
        return {'penalite': penalite, 'alertes': alertes}

    creator = str(meta.get('Creator', '') or '').lower()
    producer = str(meta.get('Producer', '') or '').lower()
    combined = creator + ' ' + producer

    for outil in OUTILS_RETOUCHE:
        if outil in combined:
            penalite += 0.35
            alertes.append(f'Outil de retouche image détecté: {outil}')
            break
    else:
        for outil in OUTILS_EDITEUR:
            if outil in combined:
                penalite += 0.20
                alertes.append(f'Éditeur de texte grand public détecté: {outil}')
                break
        else:
            for outil in OUTILS_PDF:
                if outil in combined:
                    penalite += 0.10
                    alertes.append(f'Outil édition PDF détecté: {outil}')
                    break

    creation = str(meta.get('CreationDate', '') or '')
    modification = str(meta.get('ModDate', '') or '')
    if creation and modification and creation != modification:
        penalite += 0.20
        alertes.append('Document modifié après création (dates différentes)')

    # Vérifier titre incohérent
    title = str(meta.get('Title', '') or '').lower()
    if title and document.dossier:
        nom_candidat = document.dossier.candidat.nom.lower()
        prenom_candidat = document.dossier.candidat.prenom.lower()
        # Si le titre contient un nom mais PAS celui du candidat
        if len(title) > 5 and nom_candidat not in title and any(c.isalpha() for c in title):
            pass  # Note: pas de pénalité automatique, juste observation

    return {'penalite': penalite, 'alertes': alertes}


# ═══════════════════════════════════════════════
# NIVEAU 3 — Cohérence textuelle (OCR)
# ═══════════════════════════════════════════════
def _ocr_image(img: Image.Image, lang: str = 'fra+ara') -> str:
    if not pytesseract:
        return ''
    try:
        # Tenter d'abord la détection automatique standard (PSM 3)
        txt = pytesseract.image_to_string(img, lang=lang)
        if not txt or len(txt.strip()) < 50:
            # Fallback en PSM 6 (considérer l'image comme un bloc de texte uniforme, utile pour les cartes d'identité/diplômes)
            txt = pytesseract.image_to_string(img, lang=lang, config='--psm 6')
        return txt
    except Exception:
        return ''


def _extraire_texte(document: Document) -> str:
    contenu = _read_file_bytes(document)
    if not contenu:
        return ''
    file_path = _get_file_path(document)
    real_mime = _detect_real_mime(file_path) if file_path else ''

    texte = ''
    if real_mime == 'application/pdf':
        try:
            with pdfplumber.open(io.BytesIO(contenu)) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        texte += t + '\n'
        except Exception:
            pass

    if not texte.strip() and pytesseract:
        try:
            if real_mime and real_mime.startswith('image/'):
                img = Image.open(io.BytesIO(contenu))
                texte = _ocr_image(img, lang='fra+ara')
            elif real_mime == 'application/pdf':
                try:
                    from pdf2image import convert_from_bytes
                    images = convert_from_bytes(contenu, dpi=200)
                    for img in images:
                        texte += _ocr_image(img, lang='fra+ara') + '\n'
                except ImportError:
                    pass
        except Exception:
            pass

    return texte.strip()


def _match_name(name: str, text_lower: str) -> bool:
    if not name:
        return True
    name_lower = name.lower().strip()
    if name_lower in text_lower:
        return True
    
    # Nettoyage des caractères non-alphanumériques pour éviter les soucis de ponctuation/accents
    name_clean = re.sub(r'[^a-z0-9]', '', name_lower)
    text_clean = re.sub(r'[^a-z0-9]', '', text_lower)
    if name_clean in text_clean:
        return True
        
    # Gestion des noms composés : toutes les parties doivent être présentes
    words = name_lower.split()
    if len(words) > 1:
        if all(w in text_lower for w in words):
            return True
            
    # Substitutions classiques de l'OCR pour les noms
    substitutions = {'o': '0', 'i': '1', 'l': '1', 's': '5', 'g': '9', 'z': '2'}
    name_sub = name_clean
    text_sub = text_clean
    for k, v in substitutions.items():
        name_sub = name_sub.replace(k, v)
        text_sub = text_sub.replace(k, v)
    if name_sub in text_sub:
        return True
        
    return False


def _match_cin(cin: str, text: str) -> bool:
    if not cin:
        return True
    text_lower = text.lower()
    cin_lower = cin.lower().strip()
    
    # Correspondance exacte
    if cin_lower in text_lower:
        return True
        
    # Nettoyage
    cin_clean = re.sub(r'[^a-z0-9]', '', cin_lower)
    text_clean = re.sub(r'[^a-z0-9]', '', text_lower)
    if cin_clean in text_clean:
        return True
        
    # Extraction de la partie numérique (ex: 133713 dans ID133713)
    digits = re.sub(r'\D', '', cin_lower)
    if len(digits) >= 5:
        if digits in text_clean:
            return True
            
    # Substitutions courantes de l'OCR pour les lettres de préfixe de la CIN (ex: I -> 1 ou l, D -> 0 ou O)
    prefix = re.sub(r'\d', '', cin_lower)
    if prefix:
        pattern = ''
        for char in prefix:
            if char in ['i', 'l', '1']:
                pattern += r'[i1l|/]'
            elif char in ['d', 'o', '0']:
                pattern += r'[d0o]'
            else:
                pattern += re.escape(char)
        pattern += r'\s*' + re.escape(digits)
        if re.search(pattern, text_lower):
            return True
            
    return False


def _match_establishment(est_decl: str, text: str) -> bool:
    if not est_decl:
        return True
    text_lower = text.lower()
    est_lower = est_decl.lower().strip()
    
    if est_lower in text_lower:
        return True
        
    # Dictionnaire d'abréviations courantes des établissements au Maroc
    abbrevs = {
        'est': ['ecole superieure de technologie', 'école supérieure de technologie'],
        'fst': ['faculte des sciences et techniques', 'faculté des sciences et techniques'],
        'ensa': ['ecole nationale des sciences appliquees', 'école nationale des sciences appliquées'],
        'ensam': ['ecole nationale superieure d\'arts et metiers', 'école nationale supérieure d\'arts et métiers'],
        'fs': ['faculte des sciences', 'faculté des sciences'],
        'fsjes': ['faculte des sciences juridiques', 'faculté des sciences juridiques'],
        'flsh': ['faculte des lettres', 'faculté des lettres'],
        'bts': ['brevet de technicien superieur', 'brevet de technicien supérieur'],
        'cpge': ['classes preparatoires', 'classes préparatoires'],
    }
    
    # Fonction de nettoyage et suppression des accents
    def clean_text(s: str) -> str:
        s = s.replace('é', 'e').replace('è', 'e').replace('à', 'a').replace('â', 'a').replace('ï', 'i').replace('ç', 'c')
        s = re.sub(r'[^a-z0-9]', '', s)
        return s
        
    cleaned_text = clean_text(text_lower)
    cleaned_est = clean_text(est_lower)
    if cleaned_est in cleaned_text:
        return True
        
    # Vérification des formes développées pour les abréviations déclarées
    words = est_lower.split()
    expanded_options = [words]
    for i, w in enumerate(words):
        if w in abbrevs:
            new_options = []
            for opt in expanded_options:
                for replacement in abbrevs[w]:
                    new_opt = list(opt)
                    new_opt[i] = replacement
                    new_options.append(new_opt)
            expanded_options.extend(new_options)
            
    for opt in expanded_options:
        joined = ' '.join(opt)
        if clean_text(joined) in cleaned_text:
            return True
            
    return False


def verifier_coherence_texte(document: Document) -> dict:
    alertes, penalite = [], 0.0
    texte = _extraire_texte(document)
    if not texte:
        alertes.append('Aucun texte extractible du document')
        return {'penalite': 0.3, 'alertes': alertes}

    texte_lower = texte.lower()
    dossier = document.dossier
    candidat = dossier.candidat

    # Vérifications communes à tous les types de documents
    if not _match_name(candidat.nom, texte_lower):
        penalite += 0.30
        alertes.append(f'Nom du candidat ({candidat.nom}) absent du document')
    if not _match_name(candidat.prenom, texte_lower):
        penalite += 0.20
        alertes.append(f'Prénom du candidat ({candidat.prenom}) absent du document')
    cin = candidat.user.cin
    if cin and not _match_cin(cin, texte):
        penalite += 0.25
        alertes.append('CIN du candidat absent du document')

    type_doc = document.type_doc

    if type_doc == 'RELEVE':
        if dossier.annee_obtention and str(dossier.annee_obtention) not in texte:
            penalite += 0.10
            alertes.append('Année d\'obtention absente du relevé')
        if dossier.etablissement_origine and not _match_establishment(dossier.etablissement_origine, texte):
            penalite += 0.15
            alertes.append('Établissement d\'origine absent du relevé')

        # Vérifier notes déclarées vs texte (tolérance ±0.5 point)
        notes = NoteMatiere.objects.filter(dossier=dossier)
        if notes.exists():
            # Extraire tous les nombres réels du document (ex: 13.53, 14, 16.5)
            numbers = []
            for m in re.finditer(r'\b(\d{1,2})(?:[.,](\d{1,3}))?\b', texte):
                integer_part = m.group(1)
                decimal_part = m.group(2)
                if decimal_part:
                    val_str = f'{integer_part}.{decimal_part}'
                else:
                    val_str = integer_part
                try:
                    num_val = float(val_str)
                    if 0.0 <= num_val <= 20.0:
                        numbers.append(num_val)
                except ValueError:
                    pass

            confirmees = 0
            for note in notes:
                if note.note_declaree is not None:
                    val = float(note.note_declaree)
                    matched = False
                    for num_val in numbers:
                        if abs(num_val - val) <= 0.5:
                            matched = True
                            break
                    if matched:
                        confirmees += 1
            ratio = confirmees / notes.count() if notes.count() > 0 else 1
            if ratio < 0.6:
                penalite += 0.25
                alertes.append(f'Seulement {ratio*100:.0f}% des notes confirmées dans le texte')

        # Mention
        mentions_re = r'(?:très\s*bien|bien|assez\s*bien|passable|\bTB\b|\bAB\b|\b[BP]\b)'
        if not re.search(mentions_re, texte, re.IGNORECASE):
            penalite += 0.05
            alertes.append('Mention absente du relevé')

        # Notes impossibles (>20 ou <0)
        for m in re.finditer(r'(\d{1,2}[.,]\d{1,2})\s*/?\s*20', texte):
            val = float(m.group(1).replace(',', '.'))
            if val > 20 or val < 0:
                penalite += 0.30
                alertes.append(f'Note impossible détectée: {val}')
                break

        # Répétition suspecte de la même note
        all_notes = re.findall(r'(\d{1,2}[.,]\d{1,2})\s*/?\s*(?:20)?', texte)
        if all_notes:
            counter = Counter(all_notes)
            for val, count in counter.most_common(3):
                if count > 3:
                    penalite += 0.15
                    alertes.append(f'Note {val} répétée {count} fois (suspect)')
                    break

    elif type_doc == 'DIPLOME':
        if dossier.etablissement_origine and not _match_establishment(dossier.etablissement_origine, texte):
            penalite += 0.15
            alertes.append('Établissement absent du diplôme')
        
        # Liste de motifs réguliers robustes pour l'intitulé du diplôme
        diplomes_patterns = [
            r'\bdut\b', r'dipl[oô]me\s+universitaire\s+de\s+technologie',
            r'\bbts\b', r'brevet\s+de\s+technicien\s+sup[eé]rieur',
            r'\blicence\b', r'\blst\b', r'\blf\b',
            r'\bdeug\b', r'\bdeust\b',
            r'\bmaster\b',
            r'\bbaccalaur[eé]at\b', r'\bbac\b'
        ]
        has_diplome_title = any(re.search(pat, texte_lower) for pat in diplomes_patterns)
        if not has_diplome_title:
            penalite += 0.20
            alertes.append('Intitulé du diplôme non détecté')
            
        if dossier.annee_obtention and str(dossier.annee_obtention) not in texte:
            penalite += 0.10
            alertes.append('Année d\'obtention absente du diplôme')

    elif type_doc == 'CIN':
        if not _match_cin(cin, texte):
            penalite += 0.35
            alertes.append('Numéro CIN non détecté par OCR')
        if not _match_name(candidat.nom, texte_lower) and not _match_name(candidat.prenom, texte_lower):
            penalite += 0.20
            alertes.append('Nom/prénom non détectés sur la CIN')

        # Dimensions CIN
        contenu = _read_file_bytes(document)
        if contenu:
            try:
                img = Image.open(io.BytesIO(contenu))
                w, h = img.size
                if w > 0 and h > 0:
                    ratio = max(w, h) / min(w, h)
                    if ratio < 1.3 or ratio > 1.8:
                        penalite += 0.20
                        alertes.append(f'Ratio CIN suspect: {ratio:.3f} (attendu ~1.585)')
                    if w < 600 or h < 400:
                        penalite += 0.20
                        alertes.append(f'Résolution CIN insuffisante: {w}x{h}')
            except Exception:
                pass

    return {'penalite': penalite, 'alertes': alertes}


# ═══════════════════════════════════════════════
# NIVEAU 4 — Détection de manipulation
# ═══════════════════════════════════════════════
def detecter_manipulation(document: Document) -> dict:
    alertes, penalite = [], 0.0
    contenu = _read_file_bytes(document)
    if not contenu:
        return {'penalite': 0.0, 'alertes': []}

    texte = _extraire_texte(document)

    # 1. Caractères spéciaux suspects
    if texte:
        nbsp_count = texte.count('\xa0')
        if nbsp_count > 20:
            penalite += 0.10
            alertes.append(f'{nbsp_count} espaces insécables détectés (copier-coller)')

        non_standard = sum(1 for c in texte if ord(c) > 0x024F and not (0x0600 <= ord(c) <= 0x06FF))
        if non_standard > 10:
            penalite += 0.15
            alertes.append(f'{non_standard} caractères Unicode suspects')

    # 2. Blocs de texte répétés
    if texte:
        lignes = [l.strip() for l in texte.split('\n') if len(l.strip()) > 15]
        if lignes:
            counter = Counter(lignes)
            for ligne, count in counter.most_common(3):
                if count > 2:
                    penalite += 0.20
                    alertes.append(f'Bloc de texte répété {count} fois')
                    break

    # 3. Polices dans le PDF
    file_path = _get_file_path(document)
    real_mime = _detect_real_mime(file_path) if file_path else ''
    if real_mime == 'application/pdf':
        try:
            with pdfplumber.open(io.BytesIO(contenu)) as pdf:
                familles = set()
                for page in pdf.pages:
                    if hasattr(page, 'chars') and page.chars:
                        for char in page.chars:
                            fontname = char.get('fontname', '')
                            if fontname:
                                base = fontname.split('-')[0].split('+')[-1]
                                familles.add(base)
                if len(familles) > 5:
                    penalite += 0.15
                    alertes.append(f'{len(familles)} familles de polices (signe d\'édition)')

                # 5. Document scanné (images uniquement)
                has_text = any(page.extract_text() for page in pdf.pages)
                if not has_text:
                    alertes.append('Document scanné (pas de texte natif)')
        except Exception:
            pass

    # 4. Hash doublon (exclure les documents du même candidat postulant à d'autres filières)
    file_hash = hashlib.md5(contenu).hexdigest()
    doublons = Document.objects.filter(
        fichier__isnull=False
    ).exclude(id=document.id).exclude(dossier__candidat=document.dossier.candidat)

    for autre_doc in doublons:
        try:
            autre_contenu = _read_file_bytes(autre_doc)
            if autre_contenu and hashlib.md5(autre_contenu).hexdigest() == file_hash:
                penalite += 0.40
                alertes.append(f'Fichier identique trouvé dans le dossier {autre_doc.dossier_id}')
                break
        except Exception:
            continue

    return {'penalite': penalite, 'alertes': alertes, 'hash': file_hash}


# ═══════════════════════════════════════════════
# FONCTION PRINCIPALE
# ═══════════════════════════════════════════════
def analyser_dossier_complet(dossier: Dossier) -> dict[str, Any]:
    """Analyse complète d'authenticité de tous les documents d'un dossier."""
    logger.info("Début vérification authenticité — dossier %s", dossier.id)

    toutes_alertes = []
    scores_par_type: dict[str, dict] = {}
    alertes_critiques = []

    documents = Document.objects.filter(dossier=dossier)

    for doc in documents:
        doc_alertes = []
        total_penalite = 0.0

        # Niveau 1
        r1 = verifier_structure(doc)
        total_penalite += r1['penalite']
        doc_alertes.extend(r1['alertes'])

        # Niveau 2 (PDF uniquement)
        file_path = _get_file_path(doc)
        if file_path and _detect_real_mime(file_path) == 'application/pdf':
            r2 = verifier_metadonnees_pdf(doc)
            total_penalite += r2['penalite']
            doc_alertes.extend(r2['alertes'])

        # Niveau 3
        r3 = verifier_coherence_texte(doc)
        total_penalite += r3['penalite']
        doc_alertes.extend(r3['alertes'])

        # Niveau 4
        r4 = detecter_manipulation(doc)
        total_penalite += r4['penalite']
        doc_alertes.extend(r4['alertes'])

        score_doc = max(0.0, 1.0 - total_penalite)
        doc.qualite_ocr = Decimal(str(round(score_doc, 2)))
        doc.save(update_fields=['qualite_ocr'])

        scores_par_type[doc.type_doc] = {
            'score': round(score_doc, 2),
            'alertes': doc_alertes,
        }
        toutes_alertes.extend([f"[{doc.type_doc}] {a}" for a in doc_alertes])

        # Alertes critiques = pénalité >= 0.30
        for a in doc_alertes:
            if any(k in a.lower() for k in ['critique', 'corrompu', 'identique', 'impossible', 'retouche']):
                alertes_critiques.append(f"[{doc.type_doc}] {a}")

    # Score global pondéré
    score_global = 0.0
    poids_total = 0.0
    for type_doc, poids in POIDS_TYPE.items():
        if type_doc in scores_par_type:
            score_global += scores_par_type[type_doc]['score'] * poids
            poids_total += poids

    if poids_total > 0:
        score_global = round(score_global / poids_total, 2)

    # Niveau de confiance et recommandation
    if score_global >= 0.80:
        niveau = 'ELEVE'
        recommandation = 'VALIDER'
    elif score_global >= 0.60:
        niveau = 'MOYEN'
        recommandation = 'VERIF_MANUELLE'
    elif score_global >= 0.40:
        niveau = 'FAIBLE'
        recommandation = 'VERIF_MANUELLE'
    else:
        niveau = 'CRITIQUE'
        recommandation = 'REJETER'

    # Sauvegarder sur le dossier
    dossier.score_authenticite = Decimal(str(score_global))
    dossier.alertes_verification = toutes_alertes
    if score_global < 0.55:
        dossier.is_suspect = True
    dossier.save(update_fields=['score_authenticite', 'alertes_verification', 'is_suspect'])

    logger.info("Vérification terminée — dossier %s — score=%.2f niveau=%s",
                dossier.id, score_global, niveau)

    return {
        'score_global': score_global,
        'niveau_confiance': niveau,
        'par_document': scores_par_type,
        'alertes_critiques': alertes_critiques,
        'recommandation': recommandation,
    }
