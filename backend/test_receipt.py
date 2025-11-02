#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import ReceiptData, CompanyDetails, InvoiceItem, SignatureInfo
from receipt_template import generate_receipt_pdf_with_temp_files
import io
from datetime import date

# Test data
company = CompanyDetails(
    name="Test Company",
    address="123 Test Street",
    email="test@company.com",
    phone="555-1234"
)

signature = SignatureInfo(
    user_name="John Doe",
    position="Manager"
)

items = [
    InvoiceItem(description="Test Item 1", quantity=2, unit_price=10.0),
    InvoiceItem(description="Test Item 2", quantity=1, unit_price=15.0)
]

receipt_data = ReceiptData(
    receipt_number="REC-001",
    currency="USD",
    currency_symbol="$",
    template="classic",
    company=company,
    customer_name="Test Customer",
    customer_address="456 Customer Ave",
    payment_date=date.today(),
    payment_method="cash",
    items=items,
    subtotal=35.0,
    tax_rate=0,
    tax_amount=0,
    discount_rate=0,
    discount_amount=0,
    total=35.0,
    comments="Test receipt",
    signature=signature
)

try:
    buffer = io.BytesIO()
    generate_receipt_pdf_with_temp_files(buffer, receipt_data)
    print("Receipt PDF generated successfully!")
    print(f"PDF size: {len(buffer.getvalue())} bytes")
except Exception as e:
    print(f"Error generating receipt: {e}")
    import traceback
    traceback.print_exc()