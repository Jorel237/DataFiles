from reportlab.lib import colors


def draw_watermarks(pdf, page_width, page_height):
    """
    Draw two translucent watermarks:

    1. Straight yellow-gold watermark near the top.
    2. Rotated green watermark across the centre.

    Call this after drawing the background and before drawing dynamic
    certificate fields, logos, legal text, or the QR code.
    """

    # ---------------------------------------------------------
    # Watermark 1: straight yellow-gold text near the top
    # ---------------------------------------------------------
    pdf.saveState()

    if hasattr(pdf, "setFillAlpha"):
        pdf.setFillAlpha(0.18)

    pdf.setFillColor(colors.HexColor("#D4A017"))
    pdf.setFont("Helvetica-Bold", 34)

    pdf.drawCentredString(
        page_width / 2,
        page_height - 125,
        "AUTO",
    )

    pdf.restoreState()

    # ---------------------------------------------------------
    # Watermark 2: rotated green text across the centre
    # ---------------------------------------------------------
    pdf.saveState()

    if hasattr(pdf, "setFillAlpha"):
        pdf.setFillAlpha(0.12)

    pdf.setFillColor(colors.HexColor("#16824B"))
    pdf.setFont("Helvetica-BoldOblique", 52)

    pdf.translate(
        page_width / 2,
        page_height / 2,
    )
    pdf.rotate(35)

    pdf.drawCentredString(
        0,
        0,
        "ASSURANCE",
    )

    pdf.restoreState()
