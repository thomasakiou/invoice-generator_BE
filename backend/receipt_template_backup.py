import os
from datetime import datetime, date
from models import ReceiptData, InvoiceItem, CompanyDetails, SignatureInfo

# Import ReportLab for PDF generation
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing, Rect

def format_number(number):
    """Format number with comma separators (e.g., 1,000.00)"""
    return f"{number:,.2f}"

def get_pdf_safe_currency_symbol(currency_symbol):
    """Convert Unicode currency symbols to PDF-safe alternatives"""
    symbol_map = {
        '$': '$', '£': 'GBP', '¥': 'JPY', '€': 'EUR',
        '₦': 'NGN', '₹': 'INR', '₩': 'KRW', '₽': 'RUB', '₣': 'CHF',
        'kr': 'kr', 'R$': 'BRL', 'R': 'ZAR',
    }
    return symbol_map.get(currency_symbol, currency_symbol)

def generate_receipt_pdf_with_temp_files(buffer, receipt_data, logo_path=None, signature_path=None):
    """Generate PDF receipt with selected template"""
    template = receipt_data.template or "classic"
    
    if template == "modern":
        return generate_modern_receipt(buffer, receipt_data, logo_path, signature_path)
    elif template == "minimal":
        return generate_minimal_receipt(buffer, receipt_data, logo_path, signature_path)
    elif template == "thermal":
        return generate_thermal_receipt(buffer, receipt_data, logo_path, signature_path)

    else:
        return generate_classic_receipt(buffer, receipt_data, logo_path, signature_path)

def generate_classic_receipt(buffer, receipt_data, logo_path=None, signature_path=None):
    """Classic receipt template matching URL design"""
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, leftMargin=0.5*inch, rightMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    story = []
    
    # Colors matching URL template
    header_blue = colors.HexColor('#2563eb')
    text_black = colors.black
    light_blue = colors.HexColor('#eff6ff')
    
    # Header with blue background
    header_data = [['RECEIPT']]
    header_table = Table(header_data, colWidths=[7*inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), header_blue),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.white),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 24),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 15),
        ('BOTTOMPADDING', (0,0), (-1,-1), 15),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 20))
    
    # Company info and receipt details side by side
    payment_date_str = receipt_data.payment_date.strftime('%m/%d/%Y') if receipt_data.payment_date else date.today().strftime('%m/%d/%Y')
    
    # Left column - Company info
    company_info = []
    if receipt_data.company.name:
        company_info.append(f"<font size='14'><b>{receipt_data.company.name}</b></font>")
    if receipt_data.company.services:
        company_info.append(f"<font size='10' color='gray'>{receipt_data.company.services}</font>")
        company_info.append("")  # Add empty line for spacing
    if receipt_data.company.address:
        company_info.append(receipt_data.company.address)
    if receipt_data.company.phone:
        company_info.append(f"Phone: {receipt_data.company.phone}")
    if receipt_data.company.email:
        company_info.append(f"Email: {receipt_data.company.email}")
    
    company_style = ParagraphStyle('CompanyInfo', parent=styles['Normal'], fontSize=10, textColor=text_black, spaceAfter=3)
    company_para = Paragraph('<br/>'.join(company_info), company_style)
    
    # Right column - Receipt details
    receipt_info = [
        f"<b>Receipt #:</b> {receipt_data.receipt_number}",
        f"<b>Date:</b> {payment_date_str}",
        f"<b>Payment Method:</b> {receipt_data.payment_method.replace('_', ' ').title()}"
    ]
    receipt_style = ParagraphStyle('ReceiptInfo', parent=styles['Normal'], fontSize=10, textColor=text_black, alignment=2, spaceAfter=3)
    receipt_para = Paragraph('<br/>'.join(receipt_info), receipt_style)
    
    info_table = Table([[company_para, receipt_para]], colWidths=[3.5*inch, 3.5*inch])
    info_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(info_table)
    story.append(Spacer(1, 25))
    
    # Bill To section
    if receipt_data.customer_name:
        bill_to_style = ParagraphStyle('BillTo', parent=styles['Normal'], fontSize=12, fontName='Helvetica-Bold', textColor=text_black, spaceAfter=8)
        story.append(Paragraph("BILL TO:", bill_to_style))
        
        customer_info = receipt_data.customer_name
        if receipt_data.customer_address:
            customer_info += f"<br/>{receipt_data.customer_address}"
        
        customer_style = ParagraphStyle('Customer', parent=styles['Normal'], fontSize=10, textColor=text_black, spaceAfter=20)
        story.append(Paragraph(customer_info, customer_style))
    
    # Items table - dynamic rows based on items
    currency_display = get_pdf_safe_currency_symbol(receipt_data.currency_symbol)
    items_data = [['S/No', 'DESCRIPTION', 'QTY', f'UNIT PRICE ({currency_display})', f'TOTAL ({currency_display})']]
    
    currency_symbol = get_pdf_safe_currency_symbol(receipt_data.currency_symbol)
    
    # Check if there are any valid items
    valid_items = [item for item in receipt_data.items if item.description and item.quantity > 0]
    
    if valid_items:
        # Add only actual items with serial numbers
        for i, item in enumerate(valid_items, 1):
            qty_display = str(int(item.quantity)) if item.quantity.is_integer() else str(item.quantity)
            items_data.append([
                str(i),
                item.description,
                qty_display,
                format_number(item.unit_price),
                format_number(item.quantity * item.unit_price)
            ])
    else:
        # No items - fill with 10 empty rows
        for i in range(10):
            items_data.append(['', '', '', '', ''])
    
    items_table = Table(items_data, colWidths=[0.4*inch, 2.4*inch, 0.6*inch, 1.5*inch, 1.6*inch])
    items_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0,0), (-1,0), header_blue),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('ALIGN', (0,0), (-1,0), 'LEFT'),
        # Data rows
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 9),
        ('ALIGN', (0,1), (0,-1), 'CENTER'),  # S/No center
        ('ALIGN', (1,1), (1,-1), 'LEFT'),    # Description left
        ('ALIGN', (2,1), (-1,-1), 'LEFT'),   # QTY, Price, Total left
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, light_blue]),
        # Borders
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        # Padding
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    
    story.append(items_table)
    story.append(Spacer(1, 15))
    
    # Totals section in box - only show if items exist
    has_items = any(item.description and item.quantity > 0 for item in receipt_data.items)
    
    if has_items:
        totals_data = []
        
        if receipt_data.discount_amount and receipt_data.discount_amount > 0:
            totals_data.append(['Subtotal:', f"{currency_symbol}{format_number(receipt_data.subtotal)}"])
            totals_data.append([f'Discount ({receipt_data.discount_rate}%):', f"-{currency_symbol}{format_number(receipt_data.discount_amount)}"])
        
        if receipt_data.tax_amount and receipt_data.tax_amount > 0:
            if not totals_data:
                totals_data.append(['Subtotal:', f"{currency_symbol}{format_number(receipt_data.subtotal)}"])
            totals_data.append([f'Tax ({receipt_data.tax_rate}%):', f"{currency_symbol}{format_number(receipt_data.tax_amount)}"])
        
        totals_data.append(['TOTAL:', f"{currency_symbol}{format_number(receipt_data.total)}"])
        
        totals_table = Table(totals_data, colWidths=[4.8*inch, 2.2*inch])
        totals_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-2), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-2), 10),
            ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,-1), (-1,-1), 12),
            ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
            ('BACKGROUND', (0,-1), (-1,-1), light_blue),
            ('BOX', (0,0), (-1,-1), 1, colors.grey),
            ('LINEABOVE', (0,-1), (-1,-1), 2, header_blue),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ]))
        
        story.append(totals_table)
        story.append(Spacer(1, 25))
    else:
        # Empty totals section
        empty_totals = Table([['TOTAL:', '']], colWidths=[4.8*inch, 2.2*inch])
        empty_totals.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 12),
            ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
            ('BACKGROUND', (0,0), (-1,-1), light_blue),
            ('BOX', (0,0), (-1,-1), 1, colors.grey),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ]))
        story.append(empty_totals)
        story.append(Spacer(1, 25))
    
    # Thank you message
    # thank_style = ParagraphStyle('ThankYou', parent=styles['Normal'], fontSize=12, fontName='Helvetica-Bold', alignment=1, textColor=header_blue, spaceAfter=20)
    # story.append(Paragraph("Thank you for your business!", thank_style))
    
    # Comments
    if receipt_data.comments:
        comment_style = ParagraphStyle('Comments', parent=styles['Normal'], fontSize=9, alignment=1, textColor=colors.grey, spaceAfter=20)
        story.append(Paragraph(receipt_data.comments, comment_style))
    
    # Signature section without boxes
    story.append(Spacer(1, 30))
    
    sig_line_style = ParagraphStyle('SigLine', parent=styles['Normal'], fontSize=10, textColor=colors.black, alignment=1)
    sig_label_style = ParagraphStyle('SigLabel', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold', textColor=header_blue, alignment=1, spaceBefore=8)
    
    # Create signature lines with fixed space
    seller_sig = []
    # Fixed space for signature image
    if signature_path and os.path.exists(signature_path):
        try:
            seller_sig.append(Image(signature_path, width=80, height=30))
        except:
            seller_sig.append(Spacer(1, 30))
    else:
        seller_sig.append(Spacer(1, 30))
    
    seller_sig.append(Paragraph('_' * 25, sig_line_style))
    seller_sig.append(Paragraph('Authorized Signature', sig_label_style))
    if receipt_data.signature and receipt_data.signature.user_name:
        name_style = ParagraphStyle('SigName', parent=styles['Normal'], fontSize=9, textColor=colors.grey, alignment=1, spaceBefore=3)
        seller_sig.append(Paragraph(receipt_data.signature.user_name, name_style))
    
    customer_sig = [Spacer(1, 30), Paragraph('_' * 25, sig_line_style), Paragraph('Customer Signature', sig_label_style)]
    
    sig_table = Table([[seller_sig, customer_sig]], colWidths=[3.5*inch, 3.5*inch])
    sig_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(sig_table)
    
    doc.build(story)
    return buffer

def generate_modern_receipt(buffer, receipt_data, logo_path=None, signature_path=None):
    """Modern receipt template matching URL design"""
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, leftMargin=0.5*inch, rightMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    story = []
    
    # Modern colors - clean and professional
    dark_gray = colors.HexColor('#2d3748')
    light_gray = colors.HexColor('#f7fafc')
    accent_blue = colors.HexColor('#3182ce')
    
    # Header with logo and company info
    logo_cell = []
    if logo_path and os.path.exists(logo_path):
        try:
            logo_img = Image(logo_path, width=60, height=60)
            logo_cell.append(logo_img)
        except:
            logo_cell.append(Paragraph('', styles['Normal']))
    else:
        logo_cell.append(Paragraph('', styles['Normal']))
    
    # Company info with different font sizes
    company_info = []
    if receipt_data.company.name:
        company_info.append(f"<font size='16'><b>{receipt_data.company.name}</b></font>")
    if receipt_data.company.services:
        company_info.append(f"<font size='10' color='gray'>{receipt_data.company.services}</font>")
        company_info.append("")  # Add empty line for spacing
    if receipt_data.company.address:
        company_info.append(f"<font size='9'>{receipt_data.company.address}</font>")
    if receipt_data.company.phone:
        company_info.append(f"<font size='9'>Phone: {receipt_data.company.phone}</font>")
    if receipt_data.company.email:
        company_info.append(f"<font size='9'>Email: {receipt_data.company.email}</font>")
    
    company_style = ParagraphStyle('ModernCompanyInfo', parent=styles['Normal'], fontSize=12, textColor=dark_gray, spaceAfter=3, alignment=2)
    company_para = Paragraph('<br/>'.join(company_info), company_style)
    
    header_table = Table([[logo_cell, company_para]], colWidths=[1*inch, 6*inch])
    header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('ALIGN', (0,0), (0,0), 'LEFT'), ('ALIGN', (1,0), (1,0), 'RIGHT')]))
    story.append(header_table)
    story.append(Spacer(1, 20))
    
    # Receipt title - clean and simple
    title_style = ParagraphStyle('ModernTitle', parent=styles['Title'], fontSize=18, alignment=1, textColor=dark_gray, fontName='Helvetica-Bold', spaceAfter=25)
    story.append(Paragraph("RECEIPT", title_style))
    
    # Receipt details in clean layout
    payment_date_str = receipt_data.payment_date.strftime('%B %d, %Y') if receipt_data.payment_date else date.today().strftime('%B %d, %Y')
    
    details_info = [
        f"Receipt Number: {receipt_data.receipt_number}",
        f"Date: {payment_date_str}",
        f"Payment Method: {receipt_data.payment_method.replace('_', ' ').title()}"
    ]
    
    details_style = ParagraphStyle('ModernDetails', parent=styles['Normal'], fontSize=11, textColor=dark_gray, spaceAfter=4, alignment=1)
    for detail in details_info:
        story.append(Paragraph(detail, details_style))
    
    story.append(Spacer(1, 20))
    
    # Bill To section
    if receipt_data.customer_name:
        bill_to_style = ParagraphStyle('ModernBillTo', parent=styles['Normal'], fontSize=12, fontName='Helvetica-Bold', textColor=dark_gray, spaceAfter=8)
        story.append(Paragraph("BILL TO:", bill_to_style))
        
        customer_info = receipt_data.customer_name
        if receipt_data.customer_address:
            customer_info += f"<br/>{receipt_data.customer_address}"
        
        customer_style = ParagraphStyle('ModernCustomer', parent=styles['Normal'], fontSize=10, textColor=dark_gray, spaceAfter=25)
        story.append(Paragraph(customer_info, customer_style))
    
    # Items table with S/No column
    currency_display = get_pdf_safe_currency_symbol(receipt_data.currency_symbol)
    items_data = [['S/NO', 'DESCRIPTION', 'QTY', f'UNIT PRICE ({currency_display})', f'TOTAL ({currency_display})']]
    
    currency_symbol = get_pdf_safe_currency_symbol(receipt_data.currency_symbol)
    
    # Check if there are any valid items
    valid_items = [item for item in receipt_data.items if item.description and item.quantity > 0]
    
    if valid_items:
        for i, item in enumerate(valid_items, 1):
            qty_display = str(int(item.quantity)) if item.quantity.is_integer() else str(item.quantity)
            items_data.append([
                str(i),
                item.description,
                qty_display,
                f"{currency_symbol}{format_number(item.unit_price)}",
                f"{currency_symbol}{format_number(item.quantity * item.unit_price)}"
            ])
    else:
        # Add 5 empty rows for modern template
        for i in range(5):
            items_data.append(['', '', '', '', ''])
    
    items_table = Table(items_data, colWidths=[0.4*inch, 2.4*inch, 0.6*inch, 1.5*inch, 1.6*inch])
    items_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0,0), (-1,0), dark_gray),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 11),
        ('ALIGN', (0,0), (-1,0), 'LEFT'),
        # Data rows
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 10),
        ('ALIGN', (0,1), (0,-1), 'CENTER'),  # S/No center
        ('ALIGN', (1,1), (1,-1), 'LEFT'),    # Description left
        ('ALIGN', (2,1), (-1,-1), 'CENTER'), # QTY, Price, Total center
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, light_gray]),
        # Clean borders
        ('LINEBELOW', (0,0), (-1,0), 2, dark_gray),
        ('LINEBELOW', (0,1), (-1,-1), 0.5, colors.lightgrey),
        # Padding
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    
    story.append(items_table)
    story.append(Spacer(1, 20))
    
    # Totals section - clean and professional
    has_items = any(item.description and item.quantity > 0 for item in receipt_data.items)
    
    if has_items:
        totals_data = []
        
        if receipt_data.discount_amount and receipt_data.discount_amount > 0:
            totals_data.append(['Subtotal:', f"{currency_symbol}{format_number(receipt_data.subtotal)}"])
            totals_data.append([f'Discount ({receipt_data.discount_rate}%):', f"-{currency_symbol}{format_number(receipt_data.discount_amount)}"])
        
        if receipt_data.tax_amount and receipt_data.tax_amount > 0:
            if not totals_data:
                totals_data.append(['Subtotal:', f"{currency_symbol}{format_number(receipt_data.subtotal)}"])
            totals_data.append([f'Tax ({receipt_data.tax_rate}%):', f"{currency_symbol}{format_number(receipt_data.tax_amount)}"])
        
        totals_data.append(['TOTAL:', f"{currency_symbol}{format_number(receipt_data.total)}"])
        
        totals_table = Table(totals_data, colWidths=[4.8*inch, 2.2*inch])
        totals_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-2), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-2), 11),
            ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,-1), (-1,-1), 14),
            ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
            ('LINEABOVE', (0,-1), (-1,-1), 2, dark_gray),
            ('TEXTCOLOR', (0,-1), (-1,-1), dark_gray),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ]))
        
        story.append(totals_table)
    else:
        # Empty total
        empty_total = Table([['TOTAL:', '']], colWidths=[4.8*inch, 2.2*inch])
        empty_total.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 14),
            ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
            ('LINEABOVE', (0,0), (-1,-1), 2, dark_gray),
            ('TEXTCOLOR', (0,0), (-1,-1), dark_gray),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(empty_total)
    
    story.append(Spacer(1, 30))
    
    # Thank you message
    # thank_style = ParagraphStyle('ModernThank', parent=styles['Normal'], fontSize=14, fontName='Helvetica-Bold', alignment=1, textColor=accent_blue, spaceAfter=20)
    # story.append(Paragraph("Thank you for your business!", thank_style))
    
    # Comments
    if receipt_data.comments:
        comment_style = ParagraphStyle('ModernComment', parent=styles['Normal'], fontSize=10, alignment=1, textColor=colors.grey, spaceAfter=25)
        story.append(Paragraph(receipt_data.comments, comment_style))
    
    # Signature section - clean lines
    story.append(Spacer(1, 20))
    
    sig_line_style = ParagraphStyle('ModernSigLine', parent=styles['Normal'], fontSize=10, textColor=colors.black, alignment=1)
    sig_label_style = ParagraphStyle('ModernSigLabel', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold', textColor=dark_gray, alignment=1, spaceBefore=8)
    
    # Seller signature (left) with fixed space
    seller_sig = []
    # Fixed space for signature image
    if signature_path and os.path.exists(signature_path):
        try:
            seller_sig.append(Image(signature_path, width=80, height=30))
        except:
            seller_sig.append(Spacer(1, 30))
    else:
        seller_sig.append(Spacer(1, 30))
    
    seller_sig.append(Paragraph('_' * 25, sig_line_style))
    seller_sig.append(Paragraph('Authorized Signature', sig_label_style))
    if receipt_data.signature and receipt_data.signature.user_name:
        name_style = ParagraphStyle('ModernSigName', parent=styles['Normal'], fontSize=9, textColor=colors.grey, alignment=1, spaceBefore=3)
        seller_sig.append(Paragraph(receipt_data.signature.user_name, name_style))
    
    # Customer signature (right) with fixed space
    customer_sig = [Spacer(1, 30), Paragraph('_' * 25, sig_line_style), Paragraph('Customer Signature', sig_label_style)]
    
    sig_table = Table([[seller_sig, customer_sig]], colWidths=[3.5*inch, 3.5*inch])
    sig_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(sig_table)
    
    doc.build(story)
    return buffer

def generate_minimal_receipt(buffer, receipt_data, logo_path=None, signature_path=None):
    """Minimal receipt template based on URL design"""
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.8*inch, leftMargin=0.8*inch, rightMargin=0.8*inch, bottomMargin=0.8*inch)
    styles = getSampleStyleSheet()
    story = []
    
    # Colors from the URL design
    dark_text = colors.HexColor('#2d3748')
    light_gray = colors.HexColor('#f7fafc')
    border_gray = colors.HexColor('#e2e8f0')
    
    # Header with logo and company info side by side
    logo_cell = []
    if logo_path and os.path.exists(logo_path):
        try:
            logo_img = Image(logo_path, width=50, height=50)
            logo_cell.append(logo_img)
        except:
            logo_cell.append(Paragraph('', styles['Normal']))
    else:
        logo_cell.append(Paragraph('', styles['Normal']))
    
    # Company info - right aligned
    company_info = []
    if receipt_data.company.name:
        company_info.append(f"<font size='18'><b>{receipt_data.company.name}</b></font>")
    if receipt_data.company.services:
        company_info.append(f"<font size='10' color='gray'>{receipt_data.company.services}</font>")
        company_info.append("")  # Add empty line for spacing
    if receipt_data.company.address:
        company_info.append(receipt_data.company.address)
    if receipt_data.company.phone:
        company_info.append(f"Phone: {receipt_data.company.phone}")
    if receipt_data.company.email:
        company_info.append(f"Email: {receipt_data.company.email}")
    
    company_style = ParagraphStyle('MinimalCompany', parent=styles['Normal'], fontSize=10, textColor=dark_text, alignment=2, spaceAfter=3)
    company_para = Paragraph('<br/>'.join(company_info), company_style)
    
    header_table = Table([[logo_cell, company_para]], colWidths=[1*inch, 5.5*inch])
    header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(header_table)
    story.append(Spacer(1, 30))
    
    # Receipt title - large and bold
    title_style = ParagraphStyle('MinimalTitle', parent=styles['Normal'], fontSize=24, fontName='Helvetica-Bold', alignment=0, textColor=dark_text, spaceAfter=20)
    story.append(Paragraph("Receipt", title_style))
    
    # Receipt details and customer info in two columns
    payment_date_str = receipt_data.payment_date.strftime('%B %d, %Y') if receipt_data.payment_date else date.today().strftime('%B %d, %Y')
    
    # Left column - Receipt details
    receipt_details = [
        f"<b>Receipt #:</b> {receipt_data.receipt_number}",
        f"<b>Date:</b> {payment_date_str}",
        f"<b>Payment Method:</b> {receipt_data.payment_method.replace('_', ' ').title()}"
    ]
    details_style = ParagraphStyle('MinimalDetails', parent=styles['Normal'], fontSize=10, textColor=dark_text, spaceAfter=3)
    details_para = Paragraph('<br/>'.join(receipt_details), details_style)
    
    # Right column - Customer info
    customer_info = []
    if receipt_data.customer_name:
        customer_info.append(f"<b>Bill To:</b>")
        customer_info.append(receipt_data.customer_name)
        if receipt_data.customer_address:
            customer_info.append(receipt_data.customer_address)
    
    customer_style = ParagraphStyle('MinimalCustomer', parent=styles['Normal'], fontSize=10, textColor=dark_text, alignment=2, spaceAfter=3)
    customer_para = Paragraph('<br/>'.join(customer_info), customer_style)
    
    info_table = Table([[details_para, customer_para]], colWidths=[3.25*inch, 3.25*inch])
    info_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(info_table)
    story.append(Spacer(1, 30))
    
    # Items table - clean and minimal with S/No
    currency_display = get_pdf_safe_currency_symbol(receipt_data.currency_symbol)
    items_data = [['S/No', 'Description', 'Qty', f'Rate ({currency_display})', f'Amount ({currency_display})']]
    
    currency_symbol = get_pdf_safe_currency_symbol(receipt_data.currency_symbol)
    
    # Check if there are any valid items
    valid_items = [item for item in receipt_data.items if item.description and item.quantity > 0]
    
    if valid_items:
        for i, item in enumerate(valid_items, 1):
            qty_display = str(int(item.quantity)) if item.quantity.is_integer() else str(item.quantity)
            items_data.append([
                str(i),
                item.description,
                qty_display,
                f"{currency_symbol}{format_number(item.unit_price)}",
                f"{currency_symbol}{format_number(item.quantity * item.unit_price)}"
            ])
    else:
        # Add 3 empty rows for minimal template
        for i in range(3):
            items_data.append(['', '', '', '', ''])
    
    items_table = Table(items_data, colWidths=[0.4*inch, 2.2*inch, 0.7*inch, 1.4*inch, 1.8*inch])
    items_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0,0), (-1,0), light_gray),
        ('TEXTCOLOR', (0,0), (-1,0), dark_text),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('ALIGN', (0,0), (0,0), 'CENTER'),  # S/No center
        ('ALIGN', (1,0), (1,0), 'LEFT'),    # Description left
        ('ALIGN', (2,0), (-1,0), 'CENTER'), # Qty, Rate, Amount center
        # Data rows
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 10),
        ('ALIGN', (0,1), (0,-1), 'CENTER'),  # S/No center
        ('ALIGN', (1,1), (1,-1), 'LEFT'),    # Description left
        ('ALIGN', (2,1), (-1,-1), 'CENTER'), # Qty, Rate, Amount center
        # Clean borders
        ('LINEBELOW', (0,0), (-1,0), 1, border_gray),
        ('LINEBELOW', (0,1), (-1,-1), 0.5, border_gray),
        # Padding
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    
    story.append(items_table)
    story.append(Spacer(1, 20))
    
    # Total section - right aligned
    has_items = any(item.description and item.quantity > 0 for item in receipt_data.items)
    
    if has_items:
        total_data = [[f"Total: {currency_symbol} {format_number(receipt_data.total)}"]]
    else:
        total_data = [["Total: "]]
    
    total_table = Table(total_data, colWidths=[6.5*inch])
    total_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (0,0), 14),
        ('ALIGN', (0,0), (0,0), 'RIGHT'),
        ('TEXTCOLOR', (0,0), (0,0), dark_text),
        ('LINEABOVE', (0,0), (0,0), 1, border_gray),
        ('TOPPADDING', (0,0), (0,0), 10),
        ('BOTTOMPADDING', (0,0), (0,0), 10),
    ]))
    story.append(total_table)
    
    story.append(Spacer(1, 30))
    
    # Comments
    if receipt_data.comments:
        comment_style = ParagraphStyle('MinimalComment', parent=styles['Normal'], fontSize=10, textColor=dark_text, spaceAfter=20)
        story.append(Paragraph(receipt_data.comments, comment_style))
    
    # Signature section - minimal lines
    story.append(Spacer(1, 40))
    
    sig_line_style = ParagraphStyle('MinimalSigLine', parent=styles['Normal'], fontSize=10, textColor=dark_text, alignment=1)
    sig_label_style = ParagraphStyle('MinimalSigLabel', parent=styles['Normal'], fontSize=9, textColor=dark_text, alignment=1, spaceBefore=5)
    
    # Seller signature (left) with fixed space
    seller_sig = []
    # Fixed space for signature image
    if signature_path and os.path.exists(signature_path):
        try:
            seller_sig.append(Image(signature_path, width=80, height=30))
        except:
            seller_sig.append(Spacer(1, 30))
    else:
        seller_sig.append(Spacer(1, 30))
    
    seller_sig.append(Paragraph('_' * 20, sig_line_style))
    seller_sig.append(Paragraph('Authorized Signature', sig_label_style))
    if receipt_data.signature and receipt_data.signature.user_name:
        name_style = ParagraphStyle('MinimalSigName', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=1, spaceBefore=2)
        seller_sig.append(Paragraph(receipt_data.signature.user_name, name_style))
    
    # Customer signature (right) with fixed space
    customer_sig = [Spacer(1, 30), Paragraph('_' * 20, sig_line_style), Paragraph('Customer Signature', sig_label_style)]
    
    sig_table = Table([[seller_sig, customer_sig]], colWidths=[3.25*inch, 3.25*inch])
    sig_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(sig_table)
    
    doc.build(story)
    return buffer

def generate_thermal_receipt(buffer, receipt_data, logo_path=None, signature_path=None):
    """Thermal printer style receipt"""
    from reportlab.lib.pagesizes import letter
    doc = SimpleDocTemplate(buffer, pagesize=(3*inch, 11*inch), topMargin=0.1*inch, leftMargin=0.1*inch, rightMargin=0.1*inch, bottomMargin=0.1*inch)
    styles = getSampleStyleSheet()
    story = []
    
    # Thermal style - all centered, monospace-like
    thermal_style = ParagraphStyle('Thermal', parent=styles['Normal'], fontSize=8, alignment=1, fontName='Courier', spaceAfter=2)
    thermal_bold = ParagraphStyle('ThermalBold', parent=styles['Normal'], fontSize=9, alignment=1, fontName='Courier-Bold', spaceAfter=3)
    
    # Mini logo at top
    if logo_path and os.path.exists(logo_path):
        try:
            logo_img = Image(logo_path, width=40, height=40)
            logo_table = Table([[logo_img]], colWidths=[2.8*inch])
            logo_table.setStyle(TableStyle([('ALIGN', (0,0), (0,0), 'CENTER')]))
            story.append(logo_table)
            story.append(Spacer(1, 5))
        except:
            pass
    
    if receipt_data.company.name:
        story.append(Paragraph(receipt_data.company.name.upper(), thermal_bold))
    if receipt_data.company.services:
        story.append(Paragraph(receipt_data.company.services.upper(), thermal_style))
        story.append(Spacer(1, 2))
    if receipt_data.company.address:
        story.append(Paragraph(receipt_data.company.address, thermal_style))
    if receipt_data.company.phone:
        story.append(Paragraph(f"Tel: {receipt_data.company.phone}", thermal_style))
    
    story.append(Paragraph("=" * 30, thermal_style))
    story.append(Paragraph("RECEIPT", thermal_bold))
    story.append(Paragraph("=" * 30, thermal_style))
    
    payment_date_str = receipt_data.payment_date.strftime('%Y-%m-%d') if receipt_data.payment_date else date.today().strftime('%Y-%m-%d')
    story.append(Paragraph(f"No: {receipt_data.receipt_number}", thermal_style))
    story.append(Paragraph(f"Date: {payment_date_str}", thermal_style))
    story.append(Paragraph(f"Payment: {receipt_data.payment_method.replace('_', ' ').upper()}", thermal_style))
    
    if receipt_data.customer_name:
        story.append(Paragraph(f"Customer: {receipt_data.customer_name}", thermal_style))
    
    story.append(Paragraph("-" * 30, thermal_style))
    
    currency_symbol = get_pdf_safe_currency_symbol(receipt_data.currency_symbol)
    
    # Check if there are any valid items
    valid_items = [item for item in receipt_data.items if item.description and item.quantity > 0]
    
    if valid_items:
        for item in valid_items:
            qty_display = str(int(item.quantity)) if item.quantity.is_integer() else str(item.quantity)
            story.append(Paragraph(item.description, thermal_style))
            story.append(Paragraph(f"{qty_display} x {format_number(item.unit_price)} = {format_number(item.quantity * item.unit_price)}", thermal_style))
    else:
        story.append(Paragraph("No items", thermal_style))
    
    story.append(Paragraph("-" * 30, thermal_style))
    
    # Only show total if there are items
    if valid_items:
        story.append(Paragraph(f"TOTAL: {currency_symbol} {format_number(receipt_data.total)}", thermal_bold))
    else:
        story.append(Paragraph("TOTAL: ", thermal_bold))
    story.append(Paragraph("=" * 30, thermal_style))
    story.append(Paragraph("THANK YOU!", thermal_bold))
    story.append(Paragraph("", thermal_style))
    story.append(Paragraph("SELLER: ___________", thermal_style))
    story.append(Paragraph("CUSTOMER: _________", thermal_style))
    
    doc.build(story)
    return buffer

def generate_elegant_receipt(buffer, receipt_data, logo_path=None, signature_path=None):
    """Elegant receipt template"""
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.8*inch, leftMargin=0.8*inch, rightMargin=0.8*inch, bottomMargin=0.8*inch)
    styles = getSampleStyleSheet()
    story = []
    
    elegant_purple = colors.HexColor('#6b46c1')
    elegant_gold = colors.HexColor('#d97706')
    elegant_gray = colors.HexColor('#4b5563')
    elegant_light = colors.HexColor('#faf5ff')
    
    # Decorative header
    decorator_style = ParagraphStyle('ElegantDecorator', parent=styles['Normal'], fontSize=14, alignment=1, textColor=elegant_gold)
    story.append(Paragraph("◆ ◇ ◆", decorator_style))
    
    if receipt_data.company.name:
        company_style = ParagraphStyle('ElegantCompany', parent=styles['Normal'], fontSize=20, fontName='Helvetica-Bold', alignment=1, textColor=elegant_purple, spaceAfter=8)
        story.append(Paragraph(receipt_data.company.name, company_style))
    
    if receipt_data.company.address:
        addr_style = ParagraphStyle('ElegantAddr', parent=styles['Normal'], fontSize=9, alignment=1, textColor=elegant_gray, fontName='Helvetica-Oblique', spaceAfter=15)
        story.append(Paragraph(receipt_data.company.address, addr_style))
    
    # Elegant title
    title_style = ParagraphStyle('ElegantTitle', parent=styles['Title'], fontSize=18, alignment=1, textColor=elegant_purple, fontName='Helvetica-Bold', spaceAfter=15)
    story.append(Paragraph("Payment Receipt", title_style))
    
    # Receipt details in elegant box
    payment_date_str = receipt_data.payment_date.strftime('%B %d, %Y') if receipt_data.payment_date else date.today().strftime('%B %d, %Y')
    details_content = f"Receipt No: {receipt_data.receipt_number}<br/>Date: {payment_date_str}<br/>Payment Method: {receipt_data.payment_method.replace('_', ' ').title()}"
    if receipt_data.customer_name:
        details_content += f"<br/>Customer: {receipt_data.customer_name}"
    
    details_style = ParagraphStyle('ElegantDetails', parent=styles['Normal'], fontSize=10, textColor=elegant_gray, alignment=1)
    details_para = Paragraph(details_content, details_style)
    details_table = Table([[details_para]], colWidths=[5*inch])
    details_table.setStyle(TableStyle([('BACKGROUND', (0,0), (0,0), elegant_light), ('BOX', (0,0), (0,0), 1, elegant_purple), ('LEFTPADDING', (0,0), (0,0), 20), ('RIGHTPADDING', (0,0), (0,0), 20), ('TOPPADDING', (0,0), (0,0), 15), ('BOTTOMPADDING', (0,0), (0,0), 15)]))
    story.append(details_table)
    story.append(Spacer(1, 20))
    
    # Elegant items
    if receipt_data.items:
        currency_display = get_pdf_safe_currency_symbol(receipt_data.currency_symbol)
        items_data = [['Description', 'Qty', f'Rate ({currency_display})', f'Amount ({currency_display})']]
        currency_symbol = get_pdf_safe_currency_symbol(receipt_data.currency_symbol)
        for item in receipt_data.items:
            qty_display = str(int(item.quantity)) if item.quantity.is_integer() else str(item.quantity)
            items_data.append([item.description, qty_display, f"{currency_symbol} {format_number(item.unit_price)}", f"{currency_symbol} {format_number(item.quantity * item.unit_price)}"])
        
        items_table = Table(items_data, colWidths=[2.5*inch, 0.8*inch, 1.2*inch, 1.2*inch])
        items_table.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), elegant_purple), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('FONTSIZE', (0,0), (-1,0), 10), ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('ALIGN', (0,1), (0,-1), 'LEFT'), ('FONTNAME', (0,1), (-1,-1), 'Helvetica'), ('FONTSIZE', (0,1), (-1,-1), 9), ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, elegant_light]), ('GRID', (0,0), (-1,-1), 1, elegant_purple), ('LEFTPADDING', (0,0), (-1,-1), 12), ('RIGHTPADDING', (0,0), (-1,-1), 12), ('TOPPADDING', (0,0), (-1,-1), 8), ('BOTTOMPADDING', (0,0), (-1,-1), 8)]))
        story.append(items_table)
        story.append(Spacer(1, 15))
    
    # Elegant total
    total_data = [[f"Total Amount: {currency_symbol} {format_number(receipt_data.total)}"]]
    total_table = Table(total_data, colWidths=[5.8*inch])
    total_table.setStyle(TableStyle([('BACKGROUND', (0,0), (0,0), elegant_purple), ('TEXTCOLOR', (0,0), (0,0), colors.white), ('FONTNAME', (0,0), (0,0), 'Helvetica-Bold'), ('FONTSIZE', (0,0), (0,0), 14), ('ALIGN', (0,0), (0,0), 'CENTER'), ('LEFTPADDING', (0,0), (0,0), 20), ('RIGHTPADDING', (0,0), (0,0), 20), ('TOPPADDING', (0,0), (0,0), 12), ('BOTTOMPADDING', (0,0), (0,0), 12), ('BOX', (0,0), (0,0), 2, elegant_gold)]))
    story.append(total_table)
    
    story.append(Spacer(1, 25))
    story.append(Paragraph("◆ ◇ ◆", decorator_style))
    thank_style = ParagraphStyle('ElegantThank', parent=styles['Normal'], fontSize=12, fontName='Helvetica-Bold', alignment=1, textColor=elegant_purple, spaceAfter=15)
    story.append(Paragraph("Thank you for your patronage", thank_style))
    
    # Dual signature section
    sig_line_style = ParagraphStyle('ElegantSigLine', parent=styles['Normal'], fontSize=10, textColor=elegant_gray, alignment=1)
    sig_label_style = ParagraphStyle('ElegantSigLabel', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold', textColor=elegant_purple, alignment=1, spaceBefore=5)
    
    # Seller signature with fixed space
    seller_sig = []
    # Fixed space for signature image
    if signature_path and os.path.exists(signature_path):
        try:
            seller_sig.append(Image(signature_path, width=80, height=30))
        except:
            seller_sig.append(Spacer(1, 30))
    else:
        seller_sig.append(Spacer(1, 30))
    
    seller_sig.append(Paragraph('_' * 18, sig_line_style))
    seller_sig.append(Paragraph('Authorized By', sig_label_style))
    if receipt_data.signature and receipt_data.signature.user_name:
        seller_sig.append(Paragraph(receipt_data.signature.user_name, ParagraphStyle('ElegantSigName', parent=styles['Normal'], fontSize=9, textColor=elegant_gray, alignment=1, spaceBefore=2)))
    
    # Customer signature with fixed space
    customer_sig = [Spacer(1, 30), Paragraph('_' * 18, sig_line_style), Paragraph('Customer', sig_label_style)]
    
    sig_table = Table([[seller_sig, customer_sig]], colWidths=[2.8*inch, 2.8*inch])
    sig_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(sig_table)
    
    story.append(Spacer(1, 10))
    story.append(Paragraph("◆ ◇ ◆", decorator_style))
    
    doc.build(story)
    return buffer