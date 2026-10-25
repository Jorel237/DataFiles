import io
import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from pathlib import Path
from django.conf import settings
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

DEFAULT_COORDINATES = {
    'issue_date': (58, 665),
    'download_date': (58, 642),
    'effective_date': (58, 619),
    'valid_from': (305, 665),
    'valid_until': (305, 625),
    'registration': (58, 570),
    'chassis': (58, 535),
    'insured_name': (58, 487),
    'customer_nui': (58, 452),
    'policy_number': (305, 452),
    'occupation': (58, 417),
    'attestation_number': (305, 417),
    'intermediary': (58, 382),
    'vehicle_type': (58, 337),
    'usage': (58, 302),
    'make_model': (58, 267),
    'category': (305, 267),
    'dta': (305, 337),
    'qr': (305, 175, 92),
}

def _date(value):
    return value.strftime('%d/%m/%Y') if value else '—'


def _datetime(value):
    return value.strftime('%d/%m/%Y %H:%M') if value else '—'


def _value(value):
    return '—' if value is None or str(value).strip() == '' else str(value)


def _load_font(template):
    """Return a registered font name for the selected template."""
    if not template.font_file:
        return 'Helvetica'

    font_path = Path(template.font_file.path)
    font_name = f'CertificateFont_{template.pk}'

    if font_name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(font_name, str(font_path)))

    return font_name


def _draw_field(pdf, coordinates, name, value, font_name, size=8):
    x, y = coordinates.get(name, DEFAULT_COORDINATES[name])
    pdf.setFillColor(colors.black)
    pdf.setFont(font_name, size)
    pdf.drawString(x, y, _value(value))


def _create_qr(policy):
    vehicle = policy.vehicle
    payload = (
        f'Immatriculation: {_value(vehicle.license_plate)}\n'
        f'Numero attestation: {_value(policy.attestation_number)}\n'
        f'Debut validite: {_date(policy.effective_date)}\n'
        f'Fin validite: {_date(policy.expiration_date)}\n'
        f'Date emission: {_date(policy.issue_date)}'
    )

    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=2,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    image = qr.make_image(fill_color='black', back_color='white')

    stream = io.BytesIO()
    image.save(stream, format='PNG')
    stream.seek(0)
    return ImageReader(stream)


def generate_vehicle_certificate(policy):
    """Generate a PDF using the template assigned to the policy."""
    template = policy.certificate_template
    if template is None:
        raise ValueError(
            'This policy has no certificate template. Assign an active template first.'
        )
    if not template.active:
        raise ValueError('The selected certificate template is inactive.')
    if not template.background:
        raise ValueError('The selected certificate template has no background.')

    page_width = float(template.page_width)
    page_height = float(template.page_height)
    coordinates = dict(DEFAULT_COORDINATES)
    coordinates.update(template.field_coordinates or {})
    font_name = _load_font(template)

    output = io.BytesIO()
    pdf = canvas.Canvas(output, pagesize=(page_width, page_height))

    # Fixed artwork layer.
    pdf.drawImage(
        template.background.path,
        0,
        0,
        width=page_width,
        height=page_height,
        preserveAspectRatio=False,
        mask='auto',
    )

    customer = policy.customer
    vehicle = policy.vehicle

    _draw_field(pdf, coordinates, 'issue_date', _date(policy.issue_date), font_name)
    _draw_field(pdf, coordinates, 'download_date', _datetime(policy.downloaded_at), font_name)
    _draw_field(pdf, coordinates, 'effective_date', _date(policy.effective_date), font_name)
    _draw_field(pdf, coordinates, 'valid_from', _date(policy.effective_date), font_name, 12)
    _draw_field(pdf, coordinates, 'valid_until', _date(policy.expiration_date), font_name, 12)
    _draw_field(pdf, coordinates, 'registration', vehicle.license_plate, font_name, 12)
    _draw_field(pdf, coordinates, 'chassis', vehicle.chassis_number, font_name)
    _draw_field(pdf, coordinates, 'insured_name', customer.name, font_name)
    _draw_field(pdf, coordinates, 'customer_nui', customer.nui, font_name)
    _draw_field(pdf, coordinates, 'policy_number', policy.policy_number, font_name)
    _draw_field(pdf, coordinates, 'occupation', customer.occupation, font_name)
    _draw_field(pdf, coordinates, 'attestation_number', policy.attestation_number, font_name)
    _draw_field(pdf, coordinates, 'intermediary', policy.intermediary, font_name)
    _draw_field(pdf, coordinates, 'vehicle_type', vehicle.vehicle_type, font_name)
    _draw_field(pdf, coordinates, 'usage', vehicle.usage, font_name)
    _draw_field(pdf, coordinates, 'make_model', vehicle.make_model, font_name)
    _draw_field(pdf, coordinates, 'category', vehicle.category, font_name)
    _draw_field(pdf, coordinates, 'dta', f'{policy.dta:,.0f} FCFA', font_name)

    qr_x, qr_y, qr_size = coordinates.get('qr', DEFAULT_COORDINATES['qr'])
    qr_image = _create_qr(policy)
    pdf.drawImage(
        qr_image,
        qr_x,
        qr_y,
        width=qr_size,
        height=qr_size,
        preserveAspectRatio=True,
        mask='auto',
    )

    pdf.showPage()
    pdf.save()
    output.seek(0)
    return output