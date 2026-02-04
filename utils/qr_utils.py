"""
Utility Functions - QR Code Generation and Validation
"""

import uuid
import qrcode
import io
import base64
import os
from urllib.parse import urlparse, parse_qs

def _build_qr_text(qr_data: str) -> str:
    base_url = (os.getenv('APP_BASE_URL') or '').rstrip('/')
    if not base_url:
        return qr_data

    try:
        parts = qr_data.split('-')
        if len(parts) >= 7 and parts[2] == 'EVT':
            event_id = int(parts[3])
            return f"{base_url}/organizer/scan/{event_id}?code={qr_data}"
    except Exception:
        pass
    return qr_data


def _generate_qr_image(qr_text: str) -> str:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_text)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()


def generate_qr_code(registration_id, event_id, student_id):
    """
    Generate unique QR code for event registration
    Returns: unique QR string and base64 image data
    """
    # Create unique QR code data with UUID
    qr_data = f"REG-{registration_id}-EVT-{event_id}-STU-{student_id}-{uuid.uuid4().hex[:8]}"
    qr_text = _build_qr_text(qr_data)
    img_str = _generate_qr_image(qr_text)
    
    return qr_data, img_str


def generate_qr_image(qr_data: str) -> str:
    """Generate a base64 QR image from stored QR data."""
    qr_text = _build_qr_text(qr_data)
    return _generate_qr_image(qr_text)


def validate_qr_code(qr_data):
    """
    Validate and extract information from QR code
    Returns: dict with registration_id, event_id, student_id or None if invalid
    """
    try:
        if qr_data and isinstance(qr_data, str) and qr_data.startswith(('http://', 'https://')):
            parsed = urlparse(qr_data)
            params = parse_qs(parsed.query)
            if 'code' in params and params['code']:
                qr_data = params['code'][0]

        parts = qr_data.split('-')
        if len(parts) >= 7 and parts[0] == 'REG' and parts[2] == 'EVT' and parts[4] == 'STU':
            return {
                'registration_id': int(parts[1]),
                'event_id': int(parts[3]),
                'student_id': int(parts[5])
            }
    except:
        pass
    return None
