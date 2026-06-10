# administration/services/generation_pdf.py
# Génération de convocations PDF officielles — ENSA Béni Mellal

import os
import io
import uuid
import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone
from django.core.files.base import ContentFile

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Rect, String

logger = logging.getLogger(__name__)

# ── Couleurs institutionnelles ──
BLEU_ENSA = HexColor('#1B3A6B')
BLEU_CLAIR = HexColor('#2E86C1')
BLEU_BG = HexColor('#EFF6FF')
ORANGE = HexColor('#E67E22')
ORANGE_BG = HexColor('#FFF7ED')
GRIS = HexColor('#6B7280')
GRIS_CLAIR = HexColor('#F3F4F6')
VERT = HexColor('#059669')

# ── Noms des mois en français ──
MOIS_FR = [
    'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
    'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'
]

JOURS_FR = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']


def _format_date_fr(d):
    """Formate une date Python en format français complet."""
    if not d:
        return 'Date à confirmer'
    return f"{JOURS_FR[d.weekday()]} {d.day} {MOIS_FR[d.month - 1]} {d.year}"


def _format_time_fr(t):
    """Formate un TimeField en HH:MM."""
    if not t:
        return '—'
    return t.strftime('%H:%M')


def _generer_qr_code(convocation_id):
    """Génère un QR code avec l'URL de vérification."""
    try:
        import qrcode
        from qrcode.image.pil import PilImage

        url = f"https://ensa-bm.ac.ma/verifier/{convocation_id}"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=4,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)

        from qrcode.image.pil import PilImage
        img = qr.make_image(image_factory=PilImage, fill_color="#1B3A6B", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer
    except ImportError:
        logger.warning("Module qrcode non installé, QR code non généré")
        return None
    except Exception as e:
        logger.error(f"Erreur génération QR code: {e}")
        return None


def generer_convocation_pdf(convocation):
    """
    Génère le PDF de convocation officielle pour un entretien oral.

    Args:
        convocation: Instance de ConvocationOrale

    Returns:
        str: Chemin relatif du fichier PDF généré
    """
    dossier = convocation.dossier
    epreuve = convocation.epreuve_oral
    candidat = dossier.candidat
    filiere = dossier.filiere

    # Numéro unique de convocation
    num_convocation = f"CONV-ORAL-{str(convocation.id)[:8].upper()}"
    annee = datetime.now().year

    # Buffer PDF
    buffer = io.BytesIO()

    # Créer le document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.5 * cm,
        bottomMargin=2 * cm,
    )

    # Styles
    styles = getSampleStyleSheet()

    style_header_institution = ParagraphStyle(
        'HeaderInstitution',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=BLEU_ENSA,
        alignment=TA_CENTER,
        leading=13,
    )

    style_titre = ParagraphStyle(
        'TitreConvocation',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=16,
        textColor=BLEU_ENSA,
        alignment=TA_CENTER,
        spaceAfter=6,
        spaceBefore=10,
    )

    style_sous_titre = ParagraphStyle(
        'SousTitre',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        textColor=BLEU_CLAIR,
        alignment=TA_CENTER,
        spaceAfter=4,
    )

    style_label = ParagraphStyle(
        'Label',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=BLEU_ENSA,
        leading=14,
    )

    style_value = ParagraphStyle(
        'Value',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=black,
        leading=14,
    )

    style_info_box = ParagraphStyle(
        'InfoBox',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=BLEU_ENSA,
        leading=14,
        alignment=TA_LEFT,
    )

    style_warning = ParagraphStyle(
        'Warning',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=HexColor('#DC2626'),
        alignment=TA_CENTER,
        leading=13,
    )

    style_footer = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        textColor=GRIS,
        alignment=TA_CENTER,
        leading=11,
    )

    style_num_convoc = ParagraphStyle(
        'NumConvoc',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        textColor=GRIS,
        alignment=TA_RIGHT,
    )

    # ── Construction du contenu ──
    elements = []

    # Numéro de convocation en haut à droite
    elements.append(Paragraph(f"N° {num_convocation}", style_num_convoc))
    elements.append(Spacer(1, 6))

    # En-tête officiel
    header_lines = [
        "Royaume du Maroc",
        "Ministère de l'Enseignement Supérieur,",
        "de la Recherche Scientifique et de l'Innovation",
        "Université Sultan Moulay Slimane",
        "<b>École Nationale des Sciences Appliquées</b>",
        "<b>de Béni Mellal</b>",
    ]
    for line in header_lines:
        elements.append(Paragraph(line, style_header_institution))

    elements.append(Spacer(1, 8))

    # Ligne de séparation bleue
    sep_data = [['', '', '']]
    sep_table = Table(sep_data, colWidths=[5 * cm, 7 * cm, 5 * cm])
    sep_table.setStyle(TableStyle([
        ('LINEBELOW', (1, 0), (1, 0), 2, BLEU_CLAIR),
    ]))
    elements.append(sep_table)
    elements.append(Spacer(1, 14))

    # Titre principal
    elements.append(Paragraph("CONVOCATION À L'ENTRETIEN ORAL", style_titre))
    elements.append(Paragraph(
        f"Concours d'Accès — Cycle Ingénieur — Session {annee}",
        style_sous_titre
    ))

    elements.append(Spacer(1, 6))

    # Ligne de séparation fine
    sep2_data = [['', '', '']]
    sep2_table = Table(sep2_data, colWidths=[3 * cm, 11 * cm, 3 * cm])
    sep2_table.setStyle(TableStyle([
        ('LINEBELOW', (1, 0), (1, 0), 0.5, GRIS),
    ]))
    elements.append(sep2_table)
    elements.append(Spacer(1, 14))

    # Informations du candidat
    cin = candidat.user.cin if candidat.user else '—'
    cne = dossier.cne or '—'

    info_candidat = [
        ['Monsieur / Madame :', f'{candidat.nom.upper()} {candidat.prenom}'],
        ['CIN :', cin],
        ['CNE :', cne],
        ['Filière demandée :', f'{filiere.nom} ({filiere.code})'],
    ]

    info_table = Table(info_candidat, colWidths=[5 * cm, 12 * cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), BLEU_ENSA),
        ('TEXTCOLOR', (1, 0), (1, -1), black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 14))

    # Encadré bleu — Message de convocation
    msg_convoc = Paragraph(
        "Vous êtes convoqué(e) à passer un entretien oral dans le cadre "
        "du concours d'accès à l'ENSA Béni Mellal.",
        style_info_box
    )

    msg_box_data = [[msg_convoc]]
    msg_box = Table(msg_box_data, colWidths=[15.5 * cm])
    msg_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BLEU_BG),
        ('BOX', (0, 0), (-1, -1), 1, BLEU_CLAIR),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('ROUNDEDCORNERS', (0, 0), (-1, -1), [4, 4, 4, 4]),
    ]))
    elements.append(msg_box)
    elements.append(Spacer(1, 14))

    # Détails de l'épreuve
    date_oral_str = _format_date_fr(filiere.date_oral)
    heure_str = _format_time_fr(convocation.heure_passage)
    numero_passage = convocation.numero_passage or '—'

    details = [
        [Paragraph('<b>Date :</b>', style_label),
         Paragraph(date_oral_str, style_value)],
        [Paragraph('<b>Heure :</b>', style_label),
         Paragraph(heure_str, style_value)],
        [Paragraph('<b>Lieu :</b>', style_label),
         Paragraph(filiere.lieu_oral or '—', style_value)],
        [Paragraph('<b>N° passage :</b>', style_label),
         Paragraph(str(numero_passage), style_value)],
    ]

    details_table = Table(details, colWidths=[4 * cm, 11.5 * cm])
    details_table.setStyle(TableStyle([
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (0, -1), 20),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(details_table)
    elements.append(Spacer(1, 14))

    # Encadré orange — Documents obligatoires
    style_doc_title = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=ORANGE,
        leading=14,
        spaceBefore=0,
        spaceAfter=8,
    )

    style_doc_item = ParagraphStyle(
        'DocItem',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=HexColor('#92400E'),
        leading=14,
        leftIndent=10,
    )

    doc_items = [
        "☐  Baccalauréat (original + copie certifiée conforme)",
        "☐  Diplôme obtenu (DUT/BTS/Licence) — original",
        "☐  Relevés de notes officiels (toutes les années)",
        "☐  CIN originale (recto-verso)",
        "☐  2 photos d'identité récentes",
        "☐  Cette convocation imprimée",
    ]

    doc_elements = [Paragraph("DOCUMENTS À APPORTER IMPÉRATIVEMENT :", style_doc_title)]
    for item in doc_items:
        doc_elements.append(Paragraph(item, style_doc_item))

    # Construire le tableau contenant tous les paragraphes dans une seule cellule
    doc_box_content = []
    for el in doc_elements:
        doc_box_content.append([el])

    doc_inner_table = Table(doc_box_content, colWidths=[14.5 * cm])
    doc_inner_table.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))

    doc_box_data = [[doc_inner_table]]
    doc_box = Table(doc_box_data, colWidths=[15.5 * cm])
    doc_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), ORANGE_BG),
        ('BOX', (0, 0), (-1, -1), 1, ORANGE),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(doc_box)
    elements.append(Spacer(1, 12))

    # Avertissement
    elements.append(Paragraph(
        "IMPORTANT : Tout dossier incomplet entraînera l'exclusion de l'entretien.<br/>"
        "Présentez-vous 15 minutes avant l'heure indiquée.",
        style_warning
    ))
    elements.append(Spacer(1, 20))

    # Pied de page
    elements.append(Paragraph(
        "Service Scolarité — ENSA Béni Mellal",
        style_footer
    ))
    elements.append(Paragraph(
        "Route Beni-Amir, BP 77, Béni Mellal 23000",
        style_footer
    ))
    elements.append(Paragraph(
        "scolarite@ensa.usms.ac.ma",
        style_footer
    ))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        f"© {annee} ENSA BM — USMS",
        style_footer
    ))

    # QR Code
    qr_buffer = _generer_qr_code(convocation.id)
    if qr_buffer:
        elements.append(Spacer(1, 8))
        qr_img = Image(qr_buffer, width=2 * cm, height=2 * cm)
        qr_img.hAlign = 'RIGHT'
        elements.append(qr_img)

    # Générer le PDF
    doc.build(elements)
    buffer.seek(0)

    # Sauvegarder le fichier
    nom_fichier = f"Convocation_Oral_{candidat.nom.upper()}_{candidat.prenom}_{str(convocation.id)[:8]}.pdf"
    chemin_relatif = f"convocations/{nom_fichier}"

    # Sauvegarder via le FileField du modèle
    convocation.convocation_pdf.save(nom_fichier, ContentFile(buffer.read()), save=False)
    convocation.convocation_generee = True
    convocation.date_generation = timezone.now()
    convocation.save()

    logger.info(f"PDF de convocation généré pour {candidat.nom_complet}: {nom_fichier}")

    return chemin_relatif
