# notifications/pdf_convocation.py
# Génération de la convocation PDF pour l'épreuve orale

import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image
)
from reportlab.lib import colors


# ── Couleurs ENSA ─────────────────────────────────────────────────
BLEU_ENSA = HexColor('#1B3A6B')
BLEU_CLAIR = HexColor('#3B82F6')
GRIS_CLAIR = HexColor('#F3F4F6')
VERT_SUCCES = HexColor('#059669')


def generer_convocation_pdf(dossier):
    """
    Génère un PDF de convocation pour l'épreuve orale.
    Retourne un buffer io.BytesIO contenant le PDF.
    """
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )

    # ── Styles ────────────────────────────────────────────────────
    styles = getSampleStyleSheet()

    style_titre = ParagraphStyle(
        'Titre',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=BLEU_ENSA,
        alignment=TA_CENTER,
        spaceAfter=6,
        fontName='Helvetica-Bold',
    )

    style_soustitre = ParagraphStyle(
        'SousTitre',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=BLEU_CLAIR,
        alignment=TA_CENTER,
        spaceAfter=20,
        fontName='Helvetica',
    )

    style_section = ParagraphStyle(
        'Section',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=BLEU_ENSA,
        spaceBefore=16,
        spaceAfter=8,
        fontName='Helvetica-Bold',
    )

    style_body = ParagraphStyle(
        'Corps',
        parent=styles['Normal'],
        fontSize=10.5,
        leading=16,
        alignment=TA_JUSTIFY,
        fontName='Helvetica',
    )

    style_body_center = ParagraphStyle(
        'CorpsCenter',
        parent=styles['Normal'],
        fontSize=10.5,
        leading=16,
        alignment=TA_CENTER,
        fontName='Helvetica',
    )

    style_footer = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=HexColor('#9CA3AF'),
        alignment=TA_CENTER,
    )

    style_important = ParagraphStyle(
        'Important',
        parent=styles['Normal'],
        fontSize=11,
        textColor=HexColor('#DC2626'),
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceBefore=12,
        spaceAfter=12,
    )

    # ── Données du dossier ────────────────────────────────────────
    candidat = dossier.candidat
    filiere = dossier.filiere
    user = candidat.user

    # Récupérer les infos de l'épreuve
    note_obj = dossier.notes_ecrits.first()
    epreuve = note_obj.epreuve if note_obj else None

    date_oral = epreuve.date_oral if epreuve and epreuve.date_oral else None
    lieu_oral = epreuve.lieu_oral if epreuve else 'ENSA Béni Mellal'
    heure_oral = epreuve.heure_oral if epreuve else '09:00'
    note_ecrite = float(note_obj.note) if note_obj and note_obj.note else None
    note_sur = float(epreuve.note_sur) if epreuve else 20
    rang_final = dossier.rang_final
    score_final = float(dossier.score_final) if dossier.score_final else None

    date_oral_str = date_oral.strftime('%d/%m/%Y') if date_oral else 'À préciser'
    date_oral_full = ''
    if date_oral:
        jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        mois = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin',
                'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']
        date_oral_full = f"{jours[date_oral.weekday()]} {date_oral.day} {mois[date_oral.month - 1]} {date_oral.year}"
    else:
        date_oral_full = 'Date à confirmer'

    now = datetime.now()

    # ── Construction du document ──────────────────────────────────
    elements = []

    # En-tête institutionnel
    header_data = [
        [
            Paragraph("Royaume du Maroc", style_body_center),
            Paragraph("المملكة المغربية", style_body_center),
        ],
        [
            Paragraph("Université Sultan Moulay Slimane", style_body_center),
            Paragraph("جامعة السلطان مولاي سليمان", style_body_center),
        ],
        [
            Paragraph("<b>ENSA Béni Mellal</b>", style_body_center),
            Paragraph("<b>المدرسة الوطنية للعلوم التطبيقية بني ملال</b>", style_body_center),
        ],
    ]
    header_table = Table(header_data, colWidths=[9 * cm, 9 * cm])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 4 * mm))

    # Ligne de séparation
    elements.append(HRFlowable(
        width="100%", thickness=2, color=BLEU_ENSA,
        spaceBefore=2, spaceAfter=8
    ))

    # Titre principal
    elements.append(Paragraph("CONVOCATION", style_titre))
    elements.append(Paragraph(
        f"Épreuve Orale — Concours d'accès {filiere.get_niveau_display()} {now.year}",
        style_soustitre
    ))

    elements.append(HRFlowable(
        width="60%", thickness=1, color=BLEU_CLAIR,
        spaceBefore=4, spaceAfter=16
    ))

    # Référence et date
    ref_data = [[
        Paragraph(f"<b>Réf :</b> ENSA-BM/ORAL/{now.year}/{dossier.id}", style_body),
        Paragraph(f"<b>Béni Mellal, le</b> {now.strftime('%d/%m/%Y')}", style_body),
    ]]
    ref_table = Table(ref_data, colWidths=[9 * cm, 9 * cm])
    ref_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    elements.append(ref_table)
    elements.append(Spacer(1, 12 * mm))

    # Identification du candidat
    elements.append(Paragraph("IDENTIFICATION DU CANDIDAT", style_section))

    candidat_data = [
        ["Nom complet", candidat.nom_complet],
        ["CIN", user.cin or '—'],
        ["Email", user.email],
        ["Filière", filiere.nom],
    ]
    candidat_table = Table(candidat_data, colWidths=[5 * cm, 12 * cm])
    candidat_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), GRIS_CLAIR),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#D1D5DB')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(candidat_table)

    # Résultats épreuve écrite
    elements.append(Paragraph("RÉSULTATS ÉPREUVE ÉCRITE", style_section))

    resultats_data = [
        ["Note obtenue", f"{note_ecrite:.2f}/{note_sur}" if note_ecrite is not None else '—'],
        ["Rang final", f"{rang_final}ème" if rang_final else '—'],
        ["Score global", f"{score_final:.2f}/20" if score_final is not None else '—'],
        ["Décision", "ADMIS(E) — Convoqué(e) à l'oral"],
    ]
    resultats_table = Table(resultats_data, colWidths=[5 * cm, 12 * cm])
    resultats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), GRIS_CLAIR),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#D1D5DB')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        # Dernière ligne en vert
        ('TEXTCOLOR', (1, 3), (1, 3), VERT_SUCCES),
        ('FONTNAME', (1, 3), (1, 3), 'Helvetica-Bold'),
    ]))
    elements.append(resultats_table)

    # Convocation orale
    elements.append(Paragraph("CONVOCATION À L'ÉPREUVE ORALE", style_section))

    convocation_data = [
        ["Date", date_oral_full],
        ["Heure", heure_oral or '09:00'],
        ["Lieu", lieu_oral or 'ENSA Béni Mellal'],
    ]
    convocation_table = Table(convocation_data, colWidths=[5 * cm, 12 * cm])
    convocation_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#EFF6FF')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, BLEU_CLAIR),
        ('TEXTCOLOR', (1, 0), (1, -1), BLEU_ENSA),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(convocation_table)

    # Avertissement
    elements.append(Paragraph(
        "ATTENTION : Toute absence non justifiee sera consideree comme un desistement definitif.",
        style_important
    ))

    # Documents à apporter
    elements.append(Paragraph("DOCUMENTS À PRÉSENTER LE JOUR DE L'ÉPREUVE", style_section))
    docs_list = [
        "La présente convocation (imprimée)",
        "Carte d'identité nationale (CIN) originale",
        "Copie certifiée conforme du baccalauréat",
        "Stylo bleu ou noir",
    ]
    for i, doc_item in enumerate(docs_list, 1):
        elements.append(Paragraph(
            f"&nbsp;&nbsp;&nbsp;{i}. {doc_item}",
            style_body
        ))
    elements.append(Spacer(1, 8 * mm))

    # Consignes
    elements.append(Paragraph("CONSIGNES IMPORTANTES", style_section))
    consignes = [
        "Se présenter au moins <b>30 minutes</b> avant l'heure prévue.",
        "Le port de la tenue décente est obligatoire.",
        "Les téléphones portables doivent être éteints pendant l'épreuve.",
        "Aucun document supplémentaire ne sera autorisé dans la salle d'examen.",
    ]
    for c in consignes:
        elements.append(Paragraph(f"&nbsp;&nbsp;&nbsp;• {c}", style_body))

    elements.append(Spacer(1, 16 * mm))

    # Signature
    signature_data = [[
        Paragraph("", style_body),
        Paragraph(
            "<b>Le Directeur de l'ENSA Béni Mellal</b><br/>"
            "<br/><br/><br/>"
            "<i>Signature et cachet</i>",
            ParagraphStyle('Sig', parent=style_body, alignment=TA_CENTER)
        ),
    ]]
    sig_table = Table(signature_data, colWidths=[9 * cm, 9 * cm])
    elements.append(sig_table)

    # Footer
    elements.append(Spacer(1, 10 * mm))
    elements.append(HRFlowable(
        width="100%", thickness=0.5, color=HexColor('#D1D5DB'),
        spaceBefore=4, spaceAfter=4
    ))
    elements.append(Paragraph(
        f"ENSA Béni Mellal — Avenue Moulay Ismaïl, BP 592 — Béni Mellal, Maroc<br/>"
        f"Document généré automatiquement le {now.strftime('%d/%m/%Y à %H:%M')} — "
        f"Réf : ENSA-BM/ORAL/{now.year}/{dossier.id}",
        style_footer
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer
