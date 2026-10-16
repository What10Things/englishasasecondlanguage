"""Passenger entry point for the EFL by Level Flask application."""

import os
import sys
import json
import re
from pathlib import Path

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
if APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)

# Provisioned separately over verified FTPS; never part of the source/release bundle.
payment_file = Path(APP_ROOT) / 'storage' / 'payment-config.json'
if payment_file.is_file():
    config = json.loads(payment_file.read_text())
    key = config.get('secret_key', '')
    if not re.fullmatch(r'(sk|rk)_live_[A-Za-z0-9]+', key):
        raise RuntimeError('Invalid production payment configuration')
    os.environ['EFL_STRIPE_SECRET_KEY'] = key
    os.environ['EFL_SALES_ENABLED'] = '1' if config.get('sales_enabled') is True else '0'

from app import app as application  # noqa: E402
