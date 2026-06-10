# candidatures/services/invitation_pdf.py
"""
Génération de convocations PDF téléchargeables pour les candidats.

Deux types de convocation :
  1. Convocation à l'épreuve écrite (après présélection)
  2. Convocation à l'épreuve orale (après admission à l'écrit)

Chaque PDF contient :
  - Logo ENSA Béni Mellal
  - En-tête officiel
  - Informations personnelles du candidat (nom, prénom, CIN, CNE)
  - Filière ciblée
  - Détails de l'épreuve (date, heure, lieu)
  - Instructions et documents requis
  - Signature institutionnelle

Le score n'est PAS inclus dans les convocations.
"""

import io
import os
from datetime import date

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image,
    HRFlowable, Frame, PageTemplate, BaseDocTemplate
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ── Constantes ─────────────────────────────────────────────────────

ENSA_BLEU   = colors.HexColor('#1B3A6B')
ENSA_OR     = colors.HexColor('#C8A951')
ENSA_GRIS   = colors.HexColor('#6B7280')
ENSA_VERT   = colors.HexColor('#27AE60')
BLANC       = colors.white
NOIR        = colors.black

LOGO_PATH   = os.path.join(settings.BASE_DIR, 'static', 'images', 'ensa_logo.png')

MOIS_FR = [
    '', 'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
    'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'
]

JOURS_FR = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']


def _format_date_fr(d):
    """Formate une date en français : Lundi 15 juin 2026."""
    if not d:
        return 'Date à confirmer'
    return f"{JOURS_FR[d.weekday()]} {d.day} {MOIS_FR[d.month]} {d.year}"


def _format_date_courte(d):
    """Formate une date courte : 15/06/2026."""
    if not d:
        return '—'
    return d.strftime('%d/%m/%Y')


def _get_styles():
    """Crée et retourne les styles de paragraphe pour le PDF."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        'ENSATitre',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=ENSA_BLEU,
        alignment=TA_CENTER,
        spaceAfter=6,
    ))

    styles.add(ParagraphStyle(
        'ENSASousTitre',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        textColor=ENSA_GRIS,
        alignment=TA_CENTER,
        spaceAfter=20,
    ))

    styles.add(ParagraphStyle(
        'ENSASection',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        textColor=ENSA_BLEU,
        spaceBefore=16,
        spaceAfter=8,
        borderPadding=(0, 0, 4, 0),
    ))

    styles.add(ParagraphStyle(
        'ENSACorps',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=15,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
    ))

    styles.add(ParagraphStyle(
        'ENSACorpsBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=15,
        spaceAfter=6,
    ))

    styles.add(ParagraphStyle(
        'ENSANote',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        textColor=ENSA_GRIS,
        alignment=TA_CENTER,
        spaceBefore=12,
        spaceAfter=4,
    ))

    styles.add(ParagraphStyle(
        'ENSASignature',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        alignment=TA_RIGHT,
        spaceBefore=30,
    ))

    styles.add(ParagraphStyle(
        'ENSAPied',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        textColor=ENSA_GRIS,
        alignment=TA_CENTER,
    ))

    return styles


def _build_header(elements, styles, titre_convocation):
    """Construit l'en-tête avec le logo et le titre."""
    # Logo
    if os.path.exists(LOGO_PATH):
        logo = Image(LOGO_PATH, width=5 * cm, height=5 * cm * 0.4)
        logo.hAlign = 'CENTER'
        elements.append(logo)
        elements.append(Spacer(1, 4 * mm))

    # Nom de l'école
    elements.append(Paragraph(
        "École Nationale des Sciences Appliquées",
        styles['ENSATitre']
    ))
    elements.append(Paragraph(
        "Béni Mellal — Université Sultan Moulay Slimane",
        styles['ENSASousTitre']
    ))

    # Ligne décorative
    elements.append(HRFlowable(
        width="80%", thickness=2, color=ENSA_OR,
        spaceAfter=10, spaceBefore=0, hAlign='CENTER'
    ))

    # Titre du document
    elements.append(Paragraph(titre_convocation, ParagraphStyle(
        'ConvocTitre',
        fontName='Helvetica-Bold',
        fontSize=15,
        textColor=BLANC,
        alignment=TA_CENTER,
        backColor=ENSA_BLEU,
        borderPadding=(10, 10, 10, 10),
        spaceAfter=16,
    )))


def _build_info_candidat(elements, styles, dossier):
    """Construit le bloc d'informations personnelles du candidat."""
    elements.append(Paragraph("📋 Informations du Candidat", styles['ENSASection']))

    candidat = dossier.candidat
    user = candidat.user

    data = [
        ['Nom complet', f"{candidat.prenom} {candidat.nom}"],
        ['N° CIN', user.cin or '—'],
        ['CNE / Code Massar', dossier.code_massar or dossier.cne or '—'],
        ['Email', user.email],
        ['Téléphone', candidat.telephone or '—'],
        ['Date de naissance', _format_date_courte(candidat.date_naissance) if candidat.date_naissance else '—'],
    ]

    table = Table(data, colWidths=[5.5 * cm, 11 * cm])
    table.setStyle(TableStyle([
        ('FONTNAME',   (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME',   (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE',   (0, 0), (-1, -1), 10),
        ('TEXTCOLOR',  (0, 0), (0, -1), ENSA_BLEU),
        ('TEXTCOLOR',  (1, 0), (1, -1), NOIR),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LINEBELOW',  (0, 0), (-1, -2), 0.5, colors.HexColor('#E5E7EB')),
        ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F0F4FF')),
    ]))
    elements.append(table)


def _build_info_filiere(elements, styles, filiere):
    """Construit le bloc d'informations de la filière."""
    elements.append(Paragraph("🎓 Filière Ciblée", styles['ENSASection']))

    data = [
        ['Filière', filiere.nom],
        ['Code', filiere.code],
        ['Niveau', filiere.get_niveau_display()],
    ]

    table = Table(data, colWidths=[5.5 * cm, 11 * cm])
    table.setStyle(TableStyle([
        ('FONTNAME',   (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME',   (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE',   (0, 0), (-1, -1), 10),
        ('TEXTCOLOR',  (0, 0), (0, -1), ENSA_BLEU),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW',  (0, 0), (-1, -2), 0.5, colors.HexColor('#E5E7EB')),
        ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(table)


def _build_epreuve_details(elements, styles, titre, date_epr, heure_epr, lieu_epr):
    """Construit le bloc de détails de l'épreuve (écrite ou orale)."""
    elements.append(Paragraph(titre, styles['ENSASection']))

    data = [
        ['📅  Date', _format_date_fr(date_epr)],
        ['⏰  Heure', heure_epr or 'Heure à confirmer'],
        ['📍  Lieu', lieu_epr or 'ENSA Béni Mellal'],
    ]

    table = Table(data, colWidths=[5.5 * cm, 11 * cm])
    table.setStyle(TableStyle([
        ('FONTNAME',    (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME',    (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE',    (0, 0), (-1, -1), 11),
        ('TEXTCOLOR',   (0, 0), (0, -1), ENSA_BLEU),
        ('TEXTCOLOR',   (1, 0), (1, -1), colors.HexColor('#1E40AF')),
        ('TOPPADDING',  (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('BACKGROUND',  (0, 0), (-1, -1), colors.HexColor('#EFF6FF')),
        ('LINEBELOW',   (0, 0), (-1, -2), 0.5, colors.HexColor('#BFDBFE')),
        ('BOX',         (0, 0), (-1, -1), 1, colors.HexColor('#93C5FD')),
        ('VALIGN',      (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(table)


def _build_documents_requis(elements, styles, docs_list):
    """Construit le bloc de documents à présenter."""
    elements.append(Paragraph("📎 Documents à Présenter le Jour de l'Épreuve", styles['ENSASection']))
    for doc in docs_list:
        elements.append(Paragraph(f"  •  {doc}", styles['ENSACorps']))


def _build_footer(elements, styles):
    """Construit la signature et le pied de page."""
    today = date.today()
    date_str = f"{today.day} {MOIS_FR[today.month]} {today.year}"

    elements.append(Paragraph(
        f"Fait à Béni Mellal, le {date_str}",
        styles['ENSASignature']
    ))
    elements.append(Paragraph(
        "<b>Le Directeur de l'ENSA Béni Mellal</b>",
        styles['ENSASignature']
    ))

    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(
        width="100%", thickness=0.5, color=ENSA_GRIS,
        spaceAfter=6, spaceBefore=8
    ))
    elements.append(Paragraph(
        "ENSA Béni Mellal — Université Sultan Moulay Slimane  ·  "
        "BP 77, Ville Nouvelle, Béni Mellal, Maroc  ·  "
        "Tél : +212 523 48 51 12  ·  www.ensabm.ma",
        styles['ENSAPied']
    ))
    elements.append(Paragraph(
        "Ce document est une convocation officielle. Veuillez le présenter le jour de l'épreuve.",
        ParagraphStyle(
            'Avert',
            fontName='Helvetica-Bold',
            fontSize=8,
            textColor=colors.HexColor('#DC2626'),
            alignment=TA_CENTER,
            spaceBefore=4,
        )
    ))


# ── Fonctions publiques ───────────────────────────────────────────


def generer_invitation_ecrit(dossier):
    """
    Génère un PDF de convocation à l'épreuve écrite pour un dossier
    présélectionné.

    Args:
        dossier: Instance du modèle Dossier (statut PRESELECTIONNE).

    Returns:
        io.BytesIO contenant le PDF généré.
    """
    buffer = io.BytesIO()
    styles = _get_styles()
    filiere = dossier.filiere

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title=f"Convocation Épreuve Écrite — {dossier.candidat.nom_complet}",
        author="ENSA Béni Mellal",
    )

    elements = []

    # En-tête
    _build_header(elements, styles, "CONVOCATION À L'ÉPREUVE ÉCRITE")

    # Introduction
    elements.append(Paragraph(
        f"Madame, Monsieur <b>{dossier.candidat.prenom} {dossier.candidat.nom}</b>,",
        styles['ENSACorps']
    ))
    elements.append(Spacer(1, 2 * mm))
    elements.append(Paragraph(
        "Suite à l'examen de votre dossier de candidature, nous avons l'honneur de vous "
        "informer que vous avez été <b>présélectionné(e)</b> pour passer l'épreuve écrite "
        "d'admission à l'ENSA Béni Mellal.",
        styles['ENSACorps']
    ))
    elements.append(Paragraph(
        "Vous êtes prié(e) de vous présenter à la date, l'heure et le lieu indiqués ci-dessous "
        "muni(e) des documents demandés.",
        styles['ENSACorps']
    ))

    # Infos candidat
    _build_info_candidat(elements, styles, dossier)

    # Filière
    _build_info_filiere(elements, styles, filiere)

    # Détails épreuve écrite
    _build_epreuve_details(
        elements, styles,
        "📝 Détails de l'Épreuve Écrite",
        filiere.date_ecrit,
        filiere.date_ecrit.strftime('%H:%M') if filiere.date_ecrit else 'Heure à confirmer',
        filiere.lieu_ecrit,
    )

    # Documents requis
    _build_documents_requis(elements, styles, [
        "Cette convocation imprimée",
        "Carte d'identité nationale (CIN) originale",
        "Copie certifiée conforme du diplôme",
        "Stylos (noir et bleu), calculatrice non programmable",
    ])

    # Avertissement
    elements.append(Spacer(1, 6 * mm))
    elements.append(Paragraph(
        "⚠️ <b>IMPORTANT :</b> Toute absence non justifiée sera considérée comme "
        "un désistement définitif. Veuillez vous présenter au moins <b>30 minutes</b> "
        "avant le début de l'épreuve.",
        ParagraphStyle(
            'Warning',
            fontName='Helvetica',
            fontSize=9.5,
            textColor=colors.HexColor('#DC2626'),
            backColor=colors.HexColor('#FEF2F2'),
            borderPadding=(8, 8, 8, 8),
            alignment=TA_JUSTIFY,
            leading=14,
        )
    ))

    # Signature et pied de page
    _build_footer(elements, styles)

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generer_invitation_oral(dossier):
    """
    Génère un PDF de convocation à l'épreuve orale pour un dossier
    admis à l'épreuve écrite.

    Args:
        dossier: Instance du modèle Dossier (statut ADMIS_FINAL).

    Returns:
        io.BytesIO contenant le PDF généré.
    """
    buffer = io.BytesIO()
    styles = _get_styles()
    filiere = dossier.filiere

    # Chercher les infos de l'épreuve orale depuis l'EpreuveEcrite associée
    from administration.models import EpreuveEcrite
    note_ecrite = dossier.notes_ecrits.first()
    epreuve = note_ecrite.epreuve if note_ecrite else None

    # Données de la filière
    date_oral  = filiere.date_oral
    heure_oral = filiere.date_oral.strftime('%H:%M') if filiere.date_oral else '09:00'
    lieu_oral  = filiere.lieu_oral or 'ENSA Béni Mellal'

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title=f"Convocation Épreuve Orale — {dossier.candidat.nom_complet}",
        author="ENSA Béni Mellal",
    )

    elements = []

    # En-tête
    _build_header(elements, styles, "CONVOCATION À L'ÉPREUVE ORALE")

    # Introduction
    elements.append(Paragraph(
        f"Madame, Monsieur <b>{dossier.candidat.prenom} {dossier.candidat.nom}</b>,",
        styles['ENSACorps']
    ))
    elements.append(Spacer(1, 2 * mm))
    elements.append(Paragraph(
        "Suite aux résultats de l'épreuve écrite, nous avons l'honneur de vous "
        "informer que vous avez été <b>admis(e)</b> et êtes convoqué(e) pour "
        "passer l'épreuve orale d'admission à l'ENSA Béni Mellal.",
        styles['ENSACorps']
    ))
    elements.append(Paragraph(
        "Vous êtes prié(e) de vous présenter à la date, l'heure et le lieu indiqués ci-dessous "
        "muni(e) des documents demandés.",
        styles['ENSACorps']
    ))

    # Infos candidat
    _build_info_candidat(elements, styles, dossier)

    # Filière
    _build_info_filiere(elements, styles, filiere)

    # Détails épreuve orale
    _build_epreuve_details(
        elements, styles,
        "🎤 Détails de l'Épreuve Orale",
        date_oral,
        heure_oral,
        lieu_oral,
    )

    # Documents requis
    _build_documents_requis(elements, styles, [
        "Cette convocation imprimée",
        "Carte d'identité nationale (CIN) originale",
        "Copie certifiée conforme du baccalauréat",
        "Relevés de notes originaux",
    ])

    # Avertissement
    elements.append(Spacer(1, 6 * mm))
    elements.append(Paragraph(
        "⚠️ <b>IMPORTANT :</b> Toute absence non justifiée sera considérée comme "
        "un désistement définitif. Veuillez vous présenter au moins <b>30 minutes</b> "
        "avant le début de l'épreuve.",
        ParagraphStyle(
            'Warning',
            fontName='Helvetica',
            fontSize=9.5,
            textColor=colors.HexColor('#DC2626'),
            backColor=colors.HexColor('#FEF2F2'),
            borderPadding=(8, 8, 8, 8),
            alignment=TA_JUSTIFY,
            leading=14,
        )
    ))

    # Signature et pied de page
    _build_footer(elements, styles)

    doc.build(elements)
    buffer.seek(0)
    return buffer
