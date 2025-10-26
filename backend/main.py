"""
FastAPI Invoice Generator Backend
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import io
import os
import uuid
from datetime import datetime, date
import aiofiles

# Import ReportLab for PDF generation
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Initialize FastAPI app
app = FastAPI(title="Invoice Generator API", version="1.0.0")

# Add request logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    print(f"🌐 Request: {request.method} {request.url} from {request.client.host}")
    response = await call_next(request)
    print(f"📤 Response: {response.status_code}")
    return response

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the base directory (project root)
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

print(f"Base directory: {BASE_DIR}")
print(f"Frontend directory: {FRONTEND_DIR}")
print(f"Static directory: {STATIC_DIR}")

# Mount static files with absolute paths
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")
app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")

# Pydantic models
class InvoiceItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    
class CompanyDetails(BaseModel):
    name: str
    address: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    
class SignatureInfo(BaseModel):
    user_name: Optional[str] = None
    position: Optional[str] = None
    signature_filename: Optional[str] = None

class InvoiceData(BaseModel):
    invoice_number: str
    currency: str = "USD"
    currency_symbol: str = "$"
    template: str = "classic"  # Template selection: classic, modern, minimal, corporate, elegant
    company: CompanyDetails
    client_name: str
    client_address: Optional[str] = None
    items: List[InvoiceItem]
    subtotal: float
    tax_rate: Optional[float] = None
    tax_amount: Optional[float] = None
    discount_rate: Optional[float] = None
    discount_amount: Optional[float] = None
    total: float
    due_date: Optional[date] = None
    purchase_date: Optional[date] = None
    comments: Optional[str] = None
    signature: Optional[SignatureInfo] = None

# Helper functions
def format_number(number):
    """Format number with comma separators (e.g., 1,000.00)"""
    return f"{number:,.2f}"

def find_logo_image():
    """Find company logo in static directory"""
    logo_dir = "static/logos"
    os.makedirs(logo_dir, exist_ok=True)
    
    try:
        files = os.listdir(logo_dir)
        for filename in files:
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                logo_path = os.path.join(logo_dir, filename)
                return logo_path
    except Exception as e:
        print(f"Error reading logo directory: {e}")
    
    return None

def find_signature_image(signature_filename):
    """Find signature image in static directory"""
    if not signature_filename:
        print("No signature filename provided")
        return None
        
    signature_dir = "static/signatures"
    os.makedirs(signature_dir, exist_ok=True)
    
    signature_path = os.path.join(signature_dir, signature_filename)
    print(f"Looking for signature at: {signature_path}")
    print(f"File exists: {os.path.exists(signature_path)}")
    
    if os.path.exists(signature_path):
        return signature_path
    
    return None

def cleanup_temp_files(logo_path=None, signature_path=None):
    """Clean up temporary image files"""
    files_to_delete = [f for f in [logo_path, signature_path] if f and os.path.exists(f)]
    
    for file_path in files_to_delete:
        try:
            os.remove(file_path)
            print(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            print(f"Failed to clean up {file_path}: {e}")

def generate_invoice_pdf_with_temp_files(buffer, invoice_data: InvoiceData, logo_path=None, signature_path=None):
    """Generate PDF invoice with temporary image files using selected template"""
    
    # Route to the appropriate template based on user selection
    template = invoice_data.template or "classic"
    
    if template == "modern":
        return generate_modern_template(buffer, invoice_data, logo_path, signature_path)
    elif template == "minimal":
        return generate_minimal_template(buffer, invoice_data, logo_path, signature_path)
    elif template == "corporate":
        return generate_corporate_template(buffer, invoice_data, logo_path, signature_path)
    elif template == "elegant":
        return generate_elegant_template(buffer, invoice_data, logo_path, signature_path)
    else:  # default to classic
        return generate_classic_template(buffer, invoice_data, logo_path, signature_path)

def generate_classic_template(buffer, invoice_data: InvoiceData, logo_path=None, signature_path=None):
    """Generate PDF invoice with classic template (original design)"""
    
    # Temporarily replace the find functions to use our provided paths
    original_find_logo = find_logo_image
    original_find_signature = find_signature_image
    
    def temp_find_logo():
        return logo_path
    
    def temp_find_signature(filename):
        return signature_path
    
    # Monkey patch the functions
    globals()['find_logo_image'] = temp_find_logo
    globals()['find_signature_image'] = temp_find_signature
    
    try:
        # Use the existing PDF generation function
        generate_invoice_pdf(buffer, invoice_data)
    finally:
        # Restore original functions
        globals()['find_logo_image'] = original_find_logo
        globals()['find_signature_image'] = original_find_signature

def create_placeholder_box(width, height, text=""):
    """Create an invisible placeholder for missing images (no border or text)"""
    d = Drawing(width, height)
    
    # Create an empty drawing with no visible elements
    # This maintains the spacing but doesn't show anything
    
    return d

def get_pdf_safe_currency_symbol(currency_symbol):
    """Convert Unicode currency symbols to PDF-safe alternatives"""
    
    # Map currency symbols to PDF-safe alternatives
    symbol_map = {
        # Basic symbols that work reliably in ReportLab
        '$': '$',      # USD, CAD, AUD, etc.
        '£': '£',      # British Pound  
        '¥': '¥',      # Japanese Yen/Chinese Yuan
        '€': '€',      # Euro symbol
        
        # Unicode symbols with PDF-safe fallbacks
        '₦': 'NGN',    # Naira symbol - use text fallback for PDF compatibility
        '₹': 'INR',    # Indian Rupee - use text fallback
        '₩': 'KRW',    # Korean Won - use text fallback
        '₽': 'RUB',    # Russian Ruble - use text fallback
        '₣': 'CHF',    # Swiss Franc - use text fallback
        'kr': 'kr',    # Scandinavian currencies
        'R$': 'R$',    # Brazilian Real
        'R': 'R',      # South African Rand
    }
    
    return symbol_map.get(currency_symbol, currency_symbol)

def generate_invoice_pdf(buffer, invoice_data: InvoiceData):
    """Generate PDF invoice with Unicode support"""
    
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        topMargin=0.5*inch, 
        leftMargin=0.5*inch, 
        rightMargin=0.5*inch,
        encoding='utf-8'  # Enable UTF-8 encoding
    )
    styles = getSampleStyleSheet()
    story = []
    
    # Header section with logo and company info
    header_data = []
    header_row = []
    
    # Left column: Logo
    logo_path = find_logo_image()
    if logo_path and os.path.exists(logo_path):
        try:
            logo_img = Image(logo_path)
            logo_img.drawHeight = 0.7*inch  # Smaller logo
            logo_img.drawWidth = 0.7*inch   # Smaller logo
            header_row.append(logo_img)
        except Exception as e:
            print(f"Error loading logo: {e}")
            placeholder = create_placeholder_box(0.7*inch, 0.7*inch)
            header_row.append(placeholder)
    else:
        placeholder = create_placeholder_box(0.7*inch, 0.7*inch)
        header_row.append(placeholder)
    
    # Right column: Company information
    company_style = ParagraphStyle(
        'Company',
        parent=styles['Normal'],
        fontSize=12,
        fontName='Helvetica-Bold',
        alignment=2,  # Right alignment
        spaceAfter=3
    )
    
    company_info = f'<font name="Helvetica-Bold" size="16">{invoice_data.company.name}</font><br/>'
    if invoice_data.company.address:
        company_info += f'<font name="Helvetica" size="9" color="gray">{invoice_data.company.address}</font><br/>'
    if invoice_data.company.email:
        company_info += f'<font name="Helvetica" size="9" color="gray">Email: {invoice_data.company.email}</font><br/>'
    if invoice_data.company.phone:
        company_info += f'<font name="Helvetica" size="9" color="gray">Phone: {invoice_data.company.phone}</font>'
    
    header_row.append(Paragraph(company_info, company_style))
    header_data.append(header_row)
    
    # Create header table with wider company section
    header_table = Table(header_data, colWidths=[1.5*inch, 5.5*inch])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    story.append(header_table)
    
    # Add professional accent bar
    accent_bar = Drawing(7*inch, 4)
    accent_bar.add(Rect(0, 0, 7*inch, 4, fillColor=colors.HexColor('#3498db'), strokeColor=None))
    story.append(accent_bar)
    story.append(Spacer(1, 20))
    
    # Invoice title with color and style
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=28,
        fontName='Helvetica-Bold',
        alignment=1,  # Center alignment
        spaceAfter=20,
        textColor=colors.HexColor('#2c3e50')  # Dark blue-gray color
    )
    story.append(Paragraph("INVOICE", title_style))
    
    # Invoice details section - restructured for left-aligned dates
    details_data = [
        [f"Invoice #: {invoice_data.invoice_number}", f"Date: {invoice_data.purchase_date or date.today()}"],
        ["", f"Due Date: {invoice_data.due_date or 'Not specified'}"]
    ]

    details_table = Table(details_data, colWidths=[3*inch, 4*inch])
    details_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),     # Invoice # left aligned
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),    # Dates moved to right side
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),    # Vertical alignment to top
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),  # Dark blue-gray
        ('TOPPADDING', (0, 0), (-1, -1), 3),    # Reduced padding
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3), # Reduced padding
        ('BOTTOMPADDING', (0, 0), (0, 0), 1),   # Minimal space after first row
        ('TOPPADDING', (0, 1), (-1, 1), 0),     # No top padding for second row
    ]))
    
    story.append(details_table)
    story.append(Spacer(1, 20))
    
    # Bill to section with color accent
    bill_to_style = ParagraphStyle(
        'BillTo',
        parent=styles['Normal'],
        fontSize=13,
        fontName='Helvetica-Bold',
        spaceAfter=10,
        textColor=colors.HexColor('#3498db')  # Professional blue
    )
    
    story.append(Paragraph("BILL TO:", bill_to_style))
    
    client_info = f"<b>{invoice_data.client_name}</b>"
    if invoice_data.client_address:
        client_info += f"<br/>{invoice_data.client_address}"
    
    client_style = ParagraphStyle(
        'Client',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=20
    )
    
    story.append(Paragraph(client_info, client_style))
    
    # Items table with serial numbers
    items_data = [["S/N", "Description", "Quantity", "Unit Price", "Total"]]
    
    # Get PDF-safe currency symbol
    currency_symbol = get_pdf_safe_currency_symbol(invoice_data.currency_symbol)
    
    for index, item in enumerate(invoice_data.items, start=1):
        item_total = item.quantity * item.unit_price
        # Format quantity to remove unnecessary decimals
        quantity_str = str(int(item.quantity)) if item.quantity.is_integer() else str(item.quantity)
        items_data.append([
            str(index),  # Serial number
            item.description,
            quantity_str,
            f"{currency_symbol} {format_number(item.unit_price)}",
            f"{currency_symbol} {format_number(item_total)}"
        ])
    
    # Add subtotal and calculations (with extra empty column for S/N)
    items_data.append(["", "", "", "Subtotal:", f"{currency_symbol} {format_number(invoice_data.subtotal)}"])
    
    if invoice_data.discount_amount and invoice_data.discount_amount > 0:
        items_data.append(["", "", "", f"Discount ({invoice_data.discount_rate}%):", f"-{currency_symbol} {format_number(invoice_data.discount_amount)}"])
    
    if invoice_data.tax_amount and invoice_data.tax_amount > 0:
        items_data.append(["", "", "", f"Tax ({invoice_data.tax_rate}%):", f"{currency_symbol} {format_number(invoice_data.tax_amount)}"])
    
    items_data.append(["", "", "", "TOTAL:", f"{currency_symbol} {format_number(invoice_data.total)}"])
    
    items_table = Table(items_data, colWidths=[0.5*inch, 2.5*inch, 1*inch, 1.5*inch, 1.5*inch])
    items_table.setStyle(TableStyle([
        # Header row with professional blue
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),  # Dark blue-gray
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 15),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 15),
        
        # Data rows with alternating colors
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Serial number center-aligned
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),    # Description left-aligned
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),  # Quantity, prices right-aligned
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        
        # Subtle grid lines
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#34495e')),  # Header border
        ('LINEBELOW', (0, 1), (-1, -2), 0.5, colors.HexColor('#ecf0f1')),  # Light row separators
        
        # Total row styling with accent color
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 13),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#3498db')),  # Professional blue
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ('TOPPADDING', (0, -1), (-1, -1), 12),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 12),
    ]))
    
    story.append(items_table)
    story.append(Spacer(1, 30))
    
    # Comments section
    if invoice_data.comments:
        comments_style = ParagraphStyle(
            'Comments',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=20,
            alignment=0  # Left alignment
        )
        story.append(Paragraph(invoice_data.comments, comments_style))
    
    # Signature section
    if invoice_data.signature and invoice_data.signature.user_name:
        print(f"Processing signature for user: {invoice_data.signature.user_name}")
        print(f"Signature filename: {invoice_data.signature.signature_filename}")
        signature_data = []
        
        # Create signature image or placeholder (smaller size)
        signature_path = find_signature_image(invoice_data.signature.signature_filename)
        if signature_path and os.path.exists(signature_path):
            try:
                print(f"Loading signature image from: {signature_path}")
                sig_img = Image(signature_path)
                sig_img.drawHeight = 0.5*inch
                sig_img.drawWidth = 1.5*inch
                sig_element = sig_img
                print("Signature image loaded successfully")
            except Exception as e:
                print(f"Error loading signature: {e}")
                sig_element = create_placeholder_box(1.5*inch, 0.5*inch)
        else:
            print("No signature path found or file doesn't exist, using placeholder")
            sig_element = create_placeholder_box(1.5*inch, 0.5*inch)
        
        # Create name and position info to go under signature (name in bold)
        sig_info = f"<b>{invoice_data.signature.user_name}</b>"
        if invoice_data.signature.position:
            sig_info += f"<br/>{invoice_data.signature.position}"
        
        sig_style = ParagraphStyle(
            'Signature',
            parent=styles['Normal'],
            fontSize=11,  # Increased from 9 to 11 for bigger text
            alignment=1,  # Center align under signature
            spaceAfter=0
        )
        
        # Add empty cell, then signature column (moved to right)
        signature_data.append(["", sig_element])
        signature_data.append(["", Paragraph(sig_info, sig_style)])
        
        signature_table = Table(signature_data, colWidths=[4.5*inch, 2.5*inch])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),  # Signature image centered
            ('ALIGN', (1, 1), (1, 1), 'CENTER'),  # Name/position centered
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        story.append(signature_table)
    
    # Build PDF
    doc.build(story)

# API Routes

@app.get("/")
async def root():
    """Serve the frontend index.html"""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    print(f"📄 Serving index.html from: {index_path}")
    return FileResponse(index_path)

# Template Functions
def generate_modern_template(buffer, invoice_data: InvoiceData, logo_path=None, signature_path=None):
    """Modern template with clean lines and accent colors"""
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch, 
                          leftMargin=0.75*inch, rightMargin=0.75*inch)
    story = []
    styles = getSampleStyleSheet()
    
    # Modern color scheme
    primary_color = colors.HexColor('#2563eb')  # Modern blue
    accent_color = colors.HexColor('#64748b')   # Slate gray
    light_bg = colors.HexColor('#f8fafc')      # Very light gray
    
    # Header section with logo and invoice title
    header_data = []
    left_content = []
    right_content = []
    
    # Left side - Company info and logo
    if logo_path and os.path.exists(logo_path):
        try:
            logo_img = Image(logo_path, width=60, height=60)
            left_content.append(logo_img)
        except:
            pass
    
    # Company name style - bigger and bolder
    company_name_style = ParagraphStyle(
        'ModernCompanyName',
        parent=styles['Normal'],
        fontSize=16,
        textColor=primary_color,
        fontName='Helvetica-Bold',
        spaceAfter=8
    )
    
    # Company details style - smaller and lighter
    company_details_style = ParagraphStyle(
        'ModernCompanyDetails',
        parent=styles['Normal'],
        fontSize=9,
        textColor=accent_color,
        spaceAfter=3
    )
    
    if invoice_data.company.name:
        left_content.append(Paragraph(invoice_data.company.name, company_name_style))
    if invoice_data.company.address:
        left_content.append(Paragraph(invoice_data.company.address, company_details_style))
    if invoice_data.company.email:
        left_content.append(Paragraph(invoice_data.company.email, company_details_style))
    if invoice_data.company.phone:
        left_content.append(Paragraph(invoice_data.company.phone, company_details_style))
    
    # Right side - Modern invoice title with better formatting
    title_style = ParagraphStyle(
        'ModernTitle',
        parent=styles['Title'],
        fontSize=32,
        alignment=2,  # Right align
        textColor=primary_color,
        fontName='Helvetica-Bold',
        spaceAfter=8
    )
    right_content.append(Paragraph("INVOICE", title_style))
    
    number_style = ParagraphStyle(
        'ModernNumber',
        parent=styles['Normal'],
        fontSize=16,
        alignment=2,
        textColor=primary_color,
        fontName='Helvetica-Bold',
        spaceBefore=5
    )
    right_content.append(Paragraph(f"# {invoice_data.invoice_number}", number_style))
    
    # Create header table
    header_table = Table([[left_content, right_content]], colWidths=[3.5*inch, 3*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (0,0), (0,0), 'LEFT'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    
    story.append(header_table)
    story.append(Spacer(1, 30))
    
    # Client and date info in modern cards
    card_style = ParagraphStyle(
        'ModernCard',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        spaceAfter=4
    )
    
    label_style = ParagraphStyle(
        'ModernLabel',
        parent=styles['Normal'],
        fontSize=9,
        textColor=primary_color,
        fontName='Helvetica-Bold',
        spaceAfter=8
    )
    
    # Bill to section (left)
    bill_to = [Paragraph("BILL TO", label_style)]
    if invoice_data.client_name:
        bill_to.append(Paragraph(f"<b>{invoice_data.client_name}</b>", card_style))
    if invoice_data.client_address:
        bill_to.append(Paragraph(invoice_data.client_address, card_style))
    
    # Invoice details (moved to right with right alignment)
    details_style = ParagraphStyle(
        'ModernDetailsRight',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        spaceAfter=4,
        alignment=2  # Right align
    )
    
    details = [Paragraph("INVOICE DETAILS", ParagraphStyle('ModernLabelRight', parent=label_style, alignment=2))]
    current_date = datetime.now().strftime("%B %d, %Y")
    details.append(Paragraph(f"<b>Date:</b> {current_date}", details_style))
    
    if invoice_data.due_date:
        # Handle both string and date object types
        if isinstance(invoice_data.due_date, str):
            due_date = datetime.strptime(invoice_data.due_date, "%Y-%m-%d").strftime("%B %d, %Y")
        else:
            due_date = invoice_data.due_date.strftime("%B %d, %Y")
        details.append(Paragraph(f"<b>Due:</b> {due_date}", details_style))
    
    info_table = Table([[bill_to, details]], colWidths=[3.25*inch, 3.25*inch])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (-1,-1), light_bg),
        ('LEFTPADDING', (0,0), (-1,-1), 20),
        ('RIGHTPADDING', (0,0), (-1,-1), 20),
        ('TOPPADDING', (0,0), (-1,-1), 15),
        ('BOTTOMPADDING', (0,0), (-1,-1), 15),
        ('GRID', (0,0), (-1,-1), 1, colors.white),
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 30))
    
    # Items table with modern design and serial numbers
    if invoice_data.items:
        items_data = [['S/N', 'ITEM', 'QTY', 'RATE', 'TOTAL']]
        
        for index, item in enumerate(invoice_data.items, 1):
            formatted_rate = format_number(item.unit_price)
            formatted_total = format_number(item.quantity * item.unit_price)
            # Format quantity as integer if it's a whole number, otherwise show decimal
            qty_display = str(int(item.quantity)) if item.quantity == int(item.quantity) else str(item.quantity)
            items_data.append([
                str(index),
                item.description,
                qty_display,
                f"{invoice_data.currency_symbol} {formatted_rate}",
                f"{invoice_data.currency_symbol} {formatted_total}"
            ])
        
        items_table = Table(items_data, colWidths=[0.5*inch, 2.5*inch, 0.7*inch, 1.15*inch, 1.15*inch])
        
        items_table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0,0), (-1,0), primary_color),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 11),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            # Data rows
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,1), (-1,-1), 10),
            ('ALIGN', (0,1), (-1,-1), 'CENTER'),
            ('ALIGN', (1,1), (1,-1), 'LEFT'),
            # Alternating backgrounds
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, light_bg]),
            # Borders
            ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
            # Padding
            ('LEFTPADDING', (0,0), (-1,-1), 12),
            ('RIGHTPADDING', (0,0), (-1,-1), 12),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ]))
        
        story.append(items_table)
        story.append(Spacer(1, 25))
    
    # Modern totals section
    totals_data = []
    
    # Subtotal
    formatted_subtotal = format_number(invoice_data.subtotal)
    totals_data.append(['', '', 'Subtotal:', f"{invoice_data.currency_symbol} {formatted_subtotal}"])
    
    # Discount
    if invoice_data.discount_rate and invoice_data.discount_amount:
        formatted_discount = format_number(invoice_data.discount_amount)
        totals_data.append(['', '', f'Discount ({invoice_data.discount_rate}%):', f"- {invoice_data.currency_symbol} {formatted_discount}"])
    
    # Tax
    if invoice_data.tax_rate and invoice_data.tax_amount:
        formatted_tax = format_number(invoice_data.tax_amount)
        totals_data.append(['', '', f'Tax ({invoice_data.tax_rate}%):', f"{invoice_data.currency_symbol} {formatted_tax}"])
    
    # Total
    formatted_total = format_number(invoice_data.total)
    totals_data.append(['', '', 'TOTAL:', f"{invoice_data.currency_symbol} {formatted_total}"])
    
    totals_table = Table(totals_data, colWidths=[2*inch, 1.5*inch, 1.25*inch, 1.75*inch])
    
    totals_table.setStyle(TableStyle([
        # Regular rows
        ('FONTNAME', (0,0), (-1,-2), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-2), 11),
        ('ALIGN', (2,0), (-1,-1), 'RIGHT'),
        # Total row highlighting
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,-1), (-1,-1), 14),
        ('BACKGROUND', (2,-1), (-1,-1), primary_color),
        ('TEXTCOLOR', (2,-1), (-1,-1), colors.white),
        ('LINEABOVE', (2,-1), (-1,-1), 2, primary_color),
        # Padding
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (2,0), (-1,-1), 15),
        ('RIGHTPADDING', (2,0), (-1,-1), 15),
    ]))
    
    story.append(totals_table)
    
    # Notes section
    if invoice_data.comments:
        story.append(Spacer(1, 25))
        notes_style = ParagraphStyle(
            'ModernNotes',
            parent=styles['Normal'],
            fontSize=10,
            textColor=accent_color,
            leftIndent=0
        )
        story.append(Paragraph(f"<b>Notes:</b> {invoice_data.comments}", notes_style))
    
    # Signature section (moved to right with proper alignment)
    if (invoice_data.signature and 
        (invoice_data.signature.user_name or signature_path)):
        story.append(Spacer(1, 40))
        
        # Create signature section with centered text and signature on line
        sig_elements = []
        
        # If signature image exists, create a combined signature + line element
        if signature_path and os.path.exists(signature_path):
            try:
                # Create signature line with image positioned on it
                sig_line_table = Table([
                    ["_" * 15, Image(signature_path, width=80, height=30), "_" * 15]
                ], colWidths=[0.8*inch, 1.2*inch, 0.8*inch])
                
                sig_line_table.setStyle(TableStyle([
                    ('FONTSIZE', (0,0), (0,0), 10),
                    ('FONTSIZE', (2,0), (2,0), 10),
                    ('TEXTCOLOR', (0,0), (0,0), primary_color),
                    ('TEXTCOLOR', (2,0), (2,0), primary_color),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
                ]))
                sig_elements.append(sig_line_table)
            except:
                # Fallback to just a line if image fails
                line_style = ParagraphStyle(
                    'ModernSigLine',
                    parent=styles['Normal'],
                    fontSize=12,
                    textColor=primary_color,
                    alignment=1  # Center align
                )
                sig_elements.append(Paragraph("_" * 30, line_style))
        else:
            # Just a signature line if no image
            line_style = ParagraphStyle(
                'ModernSigLine',
                parent=styles['Normal'],
                fontSize=12,
                textColor=primary_color,
                alignment=1  # Center align
            )
            sig_elements.append(Paragraph("_" * 30, line_style))
        
        # Name - centered
        if invoice_data.signature.user_name:
            sig_name_style = ParagraphStyle(
                'ModernSigName',
                parent=styles['Normal'],
                fontSize=12,
                textColor=primary_color,
                fontName='Helvetica-Bold',
                alignment=1,  # Center align
                spaceBefore=8
            )
            sig_elements.append(Paragraph(invoice_data.signature.user_name, sig_name_style))
            
        # Position - centered
        if invoice_data.signature.position:
            sig_pos_style = ParagraphStyle(
                'ModernSigPos',
                parent=styles['Normal'],
                fontSize=10,
                textColor=accent_color,
                alignment=1,  # Center align
                spaceBefore=4
            )
            sig_elements.append(Paragraph(invoice_data.signature.position, sig_pos_style))
        
        if sig_elements:
            # Create table to position signature section on the right
            sig_wrapper_table = Table([['', sig_elements]], colWidths=[4*inch, 2.5*inch])
            sig_wrapper_table.setStyle(TableStyle([
                ('ALIGN', (1,0), (1,0), 'CENTER'),
                ('VALIGN', (1,0), (1,0), 'TOP'),
            ]))
            story.append(sig_wrapper_table)
    
    doc.build(story)
    return buffer

def generate_minimal_template(buffer, invoice_data: InvoiceData, logo_path=None, signature_path=None):
    """Minimal template with lots of white space and clean typography"""
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch, bottomMargin=1*inch, 
                          leftMargin=1*inch, rightMargin=1*inch)
    story = []
    styles = getSampleStyleSheet()
    
    # Minimal color scheme - mostly black and white
    text_color = colors.HexColor('#1f2937')    # Dark gray instead of pure black
    light_gray = colors.HexColor('#f9fafb')    # Very light gray
    
    # Simple, clean title
    title_style = ParagraphStyle(
        'MinimalTitle',
        parent=styles['Title'],
        fontSize=24,
        alignment=0,  # Left align for minimal look
        textColor=text_color,
        fontName='Helvetica',
        spaceAfter=25,
        spaceBefore=20
    )
    story.append(Paragraph("Invoice", title_style))
    
    # Company info and invoice details side by side
    # Company name style - bigger and bolder
    company_name_style = ParagraphStyle(
        'MinimalCompanyName',
        parent=styles['Normal'],
        fontSize=14,
        textColor=text_color,
        fontName='Helvetica-Bold',
        spaceAfter=8,
        leftIndent=0
    )
    
    # Company details style - smaller
    company_details_style = ParagraphStyle(
        'MinimalCompanyDetails',
        parent=styles['Normal'],
        fontSize=9,
        textColor=text_color,
        spaceAfter=4,
        leftIndent=0
    )
    
    details_style = ParagraphStyle(
        'MinimalDetails',
        parent=styles['Normal'],
        fontSize=10,
        textColor=text_color,
        spaceAfter=6,
        alignment=2  # Right align
    )
    
    # Left column - Company info
    company_info = []
    if invoice_data.company.name:
        company_info.append(Paragraph(invoice_data.company.name, company_name_style))
    if invoice_data.company.address:
        company_info.append(Paragraph(invoice_data.company.address, company_details_style))
    if invoice_data.company.email:
        company_info.append(Paragraph(invoice_data.company.email, company_details_style))
    if invoice_data.company.phone:
        company_info.append(Paragraph(invoice_data.company.phone, company_details_style))
    
    # Right column - Invoice details
    invoice_details = []
    invoice_details.append(Paragraph(f"<b>Invoice Number:</b> {invoice_data.invoice_number}", details_style))
    
    current_date = datetime.now().strftime("%B %d, %Y")
    invoice_details.append(Paragraph(f"<b>Date:</b> {current_date}", details_style))
    
    if invoice_data.due_date:
        # Handle both string and date object types
        if isinstance(invoice_data.due_date, str):
            due_date = datetime.strptime(invoice_data.due_date, "%Y-%m-%d").strftime("%B %d, %Y")
        else:
            due_date = invoice_data.due_date.strftime("%B %d, %Y")
        invoice_details.append(Paragraph(f"<b>Due Date:</b> {due_date}", details_style))
    
    # Create side-by-side table
    info_table = Table([[company_info, invoice_details]], colWidths=[3.25*inch, 3.25*inch])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (0,0), (0,0), 'LEFT'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 30))
    
    # Bill to - enhanced styling
    bill_header_style = ParagraphStyle(
        'MinimalBillHeader',
        parent=styles['Normal'],
        fontSize=13,
        textColor=text_color,
        fontName='Helvetica-Bold',
        spaceAfter=8
    )
    
    bill_details_style = ParagraphStyle(
        'MinimalBillDetails',
        parent=styles['Normal'],
        fontSize=11,
        textColor=text_color,
        spaceAfter=4
    )
    
    story.append(Paragraph("Bill To:", bill_header_style))
    if invoice_data.client_name:
        story.append(Paragraph(invoice_data.client_name, bill_details_style))
    if invoice_data.client_address:
        story.append(Paragraph(invoice_data.client_address, bill_details_style))
    
    story.append(Spacer(1, 40))
    
    # Items - very clean table with serial numbers
    if invoice_data.items:
        items_data = [['S/N', 'Description', 'Quantity', 'Rate', 'Amount']]
        
        for index, item in enumerate(invoice_data.items, 1):
            formatted_rate = format_number(item.unit_price)
            formatted_amount = format_number(item.quantity * item.unit_price)
            # Format quantity as integer if it's a whole number, otherwise show decimal
            qty_display = str(int(item.quantity)) if item.quantity == int(item.quantity) else str(item.quantity)
            items_data.append([
                str(index),
                item.description,
                qty_display,
                f"{invoice_data.currency_symbol} {formatted_rate}",
                f"{invoice_data.currency_symbol} {formatted_amount}"
            ])
        
        items_table = Table(items_data, colWidths=[0.4*inch, 2.8*inch, 0.7*inch, 1.25*inch, 1.35*inch])
        
        items_table.setStyle(TableStyle([
            # Header - simple line
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 11),
            ('LINEBELOW', (0,0), (-1,0), 1, text_color),
            # Data rows - minimal styling
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,1), (-1,-1), 10),
            ('ALIGN', (0,1), (-1,-1), 'CENTER'),
            ('ALIGN', (1,1), (1,-1), 'LEFT'),
            # Very minimal borders
            ('LINEBELOW', (0,-1), (-1,-1), 0.5, colors.lightgrey),
            # Simple padding
            ('TOPPADDING', (0,0), (-1,-1), 12),
            ('BOTTOMPADDING', (0,0), (-1,-1), 12),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        
        story.append(items_table)
        story.append(Spacer(1, 30))
    
    # Totals - clean and simple
    totals_data = []
    
    # Subtotal
    formatted_subtotal = format_number(invoice_data.subtotal)
    totals_data.append(['Subtotal', f"{invoice_data.currency_symbol} {formatted_subtotal}"])
    
    # Discount
    if invoice_data.discount_rate and invoice_data.discount_amount:
        formatted_discount = format_number(invoice_data.discount_amount)
        totals_data.append([f'Discount ({invoice_data.discount_rate}%)', f"- {invoice_data.currency_symbol} {formatted_discount}"])
    
    # Tax
    if invoice_data.tax_rate and invoice_data.tax_amount:
        formatted_tax = format_number(invoice_data.tax_amount)
        totals_data.append([f'Tax ({invoice_data.tax_rate}%)', f"{invoice_data.currency_symbol} {formatted_tax}"])
    
    # Total
    formatted_total = format_number(invoice_data.total)
    totals_data.append(['Total', f"{invoice_data.currency_symbol} {formatted_total}"])
    
    totals_table = Table(totals_data, colWidths=[5*inch, 2*inch])
    
    totals_table.setStyle(TableStyle([
        # Simple styling
        ('FONTNAME', (0,0), (-1,-2), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-2), 11),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,-1), (-1,-1), 12),
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        # Minimal line above total
        ('LINEABOVE', (0,-1), (-1,-1), 1, text_color),
        # Simple padding
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    
    story.append(totals_table)
    
    # Notes - if any
    if invoice_data.comments:
        story.append(Spacer(1, 30))
        notes_style = ParagraphStyle(
            'MinimalNotes',
            parent=styles['Normal'],
            fontSize=10,
            textColor=text_color
        )
        story.append(Paragraph(f"Notes: {invoice_data.comments}", notes_style))
    
    # Signature - minimal approach (moved to right and centered)
    if (invoice_data.signature and 
        (invoice_data.signature.user_name or signature_path)):
        story.append(Spacer(1, 50))
        
        sig_elements = []
        
        # Create signature line with image placed on it (if provided)
        if signature_path and os.path.exists(signature_path):
            try:
                # Create signature line with image positioned on it
                sig_line_table = Table([
                    ["_" * 12, Image(signature_path, width=70, height=25), "_" * 12]
                ], colWidths=[0.8*inch, 1.0*inch, 0.8*inch])
                
                sig_line_table.setStyle(TableStyle([
                    ('FONTSIZE', (0,0), (0,0), 11),
                    ('FONTSIZE', (2,0), (2,0), 11),
                    ('TEXTCOLOR', (0,0), (0,0), text_color),
                    ('TEXTCOLOR', (2,0), (2,0), text_color),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
                ]))
                sig_elements.append(sig_line_table)
            except:
                # Fallback to just a line if image fails
                line_style = ParagraphStyle(
                    'MinimalSigLine',
                    parent=styles['Normal'],
                    fontSize=11,
                    textColor=text_color,
                    alignment=1  # Center align
                )
                sig_elements.append(Paragraph("_" * 30, line_style))
        else:
            # Just a signature line if no image
            line_style = ParagraphStyle(
                'MinimalSigLine',
                parent=styles['Normal'],
                fontSize=11,
                textColor=text_color,
                alignment=1  # Center align
            )
            sig_elements.append(Paragraph("_" * 30, line_style))
        
        # Name - centered
        if invoice_data.signature.user_name:
            sig_name_style = ParagraphStyle(
                'MinimalSigName',
                parent=styles['Normal'],
                fontSize=11,
                textColor=text_color,
                alignment=1,  # Center align
                spaceBefore=8
            )
            sig_elements.append(Paragraph(invoice_data.signature.user_name, sig_name_style))
            
        # Position - centered
        if invoice_data.signature.position:
            pos_style = ParagraphStyle(
                'MinimalSigPos',
                parent=styles['Normal'],
                fontSize=9,
                textColor=text_color,
                alignment=1,  # Center align
                spaceBefore=4
            )
            sig_elements.append(Paragraph(invoice_data.signature.position, pos_style))
        
        if sig_elements:
            # Create table to position signature on the right
            sig_table = Table([['', sig_elements]], colWidths=[4*inch, 2.5*inch])
            sig_table.setStyle(TableStyle([
                ('ALIGN', (1,0), (1,0), 'CENTER'),
                ('VALIGN', (1,0), (1,0), 'TOP'),
            ]))
            story.append(sig_table)
    
    doc.build(story)
    return buffer

def generate_corporate_template(buffer, invoice_data: InvoiceData, logo_path=None, signature_path=None):
    """Corporate template with formal business styling"""
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.75*inch, bottomMargin=0.75*inch, 
                          leftMargin=0.75*inch, rightMargin=0.75*inch)
    story = []
    styles = getSampleStyleSheet()
    
    # Corporate color scheme - conservative blues and grays
    corporate_blue = colors.HexColor('#1e3a8a')   # Dark blue
    corporate_gray = colors.HexColor('#374151')    # Professional gray
    light_blue = colors.HexColor('#eff6ff')       # Very light blue
    
    # Corporate header with formal styling
    header_style = ParagraphStyle(
        'CorporateHeader',
        parent=styles['Title'],
        fontSize=18,
        alignment=1,  # Center
        textColor=corporate_blue,
        fontName='Helvetica-Bold',
        spaceAfter=8,
        spaceBefore=8
    )
    story.append(Paragraph("INVOICE", header_style))
    
    # Horizontal line under header
    line_table = Table([['_' * 80]], colWidths=[6.5*inch])
    line_table.setStyle(TableStyle([
        ('FONTSIZE', (0,0), (0,0), 8),
        ('TEXTCOLOR', (0,0), (0,0), corporate_blue),
        ('ALIGN', (0,0), (0,0), 'CENTER'),
    ]))
    story.append(line_table)
    
    # Add prominent company name right after header
    if invoice_data.company.name:
        prominent_company_style = ParagraphStyle(
            'ProminentCompanyName',
            parent=styles['Normal'],
            fontSize=24,
            textColor=corporate_blue,
            fontName='Helvetica-Bold',
            spaceAfter=12,
            spaceBefore=8,
            alignment=1  # Center align
        )
        story.append(Paragraph(invoice_data.company.name, prominent_company_style))
    
    # Add company address immediately after company name with minimal spacing
    if invoice_data.company.address:
        address_style = ParagraphStyle(
            'ProminentAddress',
            parent=styles['Normal'],
            fontSize=12,
            textColor=corporate_gray,
            fontName='Helvetica',
            spaceAfter=4,
            spaceBefore=2,
            alignment=1  # Center align
        )
        story.append(Paragraph(invoice_data.company.address, address_style))
    
    
    # Add email and phone if available (right after address)
    if invoice_data.company.email:
        email_style = ParagraphStyle(
            'ProminentEmail',
            parent=styles['Normal'],
            fontSize=11,
            textColor=corporate_gray,
            fontName='Helvetica',
            spaceAfter=2,
            spaceBefore=2,
            alignment=1  # Center align
        )
        story.append(Paragraph(invoice_data.company.email, email_style))
    
    if invoice_data.company.phone:
        phone_style = ParagraphStyle(
            'ProminentPhone',
            parent=styles['Normal'],
            fontSize=11,
            textColor=corporate_gray,
            fontName='Helvetica',
            spaceAfter=4,
            spaceBefore=2,
            alignment=1  # Center align
        )
        story.append(Paragraph(invoice_data.company.phone, phone_style))
    
    story.append(Spacer(1, 25))
    
    # Invoice and client information in formal boxes
    info_style = ParagraphStyle(
        'CorporateInfo',
        parent=styles['Normal'],
        fontSize=10,
        textColor=corporate_gray,
        spaceAfter=4
    )
    
    label_style = ParagraphStyle(
        'CorporateLabel',
        parent=styles['Normal'],
        fontSize=10,
        textColor=corporate_blue,
        fontName='Helvetica-Bold',
        spaceAfter=8
    )
    
    # Left column - Invoice details
    invoice_info = [Paragraph("INVOICE INFORMATION", label_style)]
    invoice_info.append(Paragraph(f"Invoice Number: {invoice_data.invoice_number}", info_style))
    
    current_date = datetime.now().strftime("%B %d, %Y")
    invoice_info.append(Paragraph(f"Issue Date: {current_date}", info_style))
    
    if invoice_data.due_date:
        # Handle both string and date object types
        if isinstance(invoice_data.due_date, str):
            due_date = datetime.strptime(invoice_data.due_date, "%Y-%m-%d").strftime("%B %d, %Y")
        else:
            due_date = invoice_data.due_date.strftime("%B %d, %Y")
        invoice_info.append(Paragraph(f"Due Date: {due_date}", info_style))
    
    # Right column - Client information
    client_info = [Paragraph("BILL TO", label_style)]
    if invoice_data.client_name:
        client_info.append(Paragraph(invoice_data.client_name, info_style))
    if invoice_data.client_address:
        client_info.append(Paragraph(invoice_data.client_address, info_style))
    
    info_table = Table([[invoice_info, client_info]], colWidths=[3.25*inch, 3.25*inch])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (-1,-1), light_blue),
        ('LEFTPADDING', (0,0), (-1,-1), 15),
        ('RIGHTPADDING', (0,0), (-1,-1), 15),
        ('TOPPADDING', (0,0), (-1,-1), 15),
        ('BOTTOMPADDING', (0,0), (-1,-1), 15),
        ('LINEWIDTH', (0,0), (-1,-1), 1),
        ('LINECOLOR', (0,0), (-1,-1), corporate_blue),
        ('GRID', (0,0), (-1,-1), 1, corporate_blue),
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 25))
    
    # Items table with corporate styling
    if invoice_data.items:
        items_data = [['S.NO', 'DESCRIPTION', 'QTY', 'UNIT PRICE', 'TOTAL AMOUNT']]
        
        for index, item in enumerate(invoice_data.items, 1):
            formatted_rate = format_number(item.unit_price)
            formatted_amount = format_number(item.quantity * item.unit_price)
            # Format quantity as integer if it's a whole number, otherwise show decimal
            qty_display = str(int(item.quantity)) if item.quantity == int(item.quantity) else str(item.quantity)
            items_data.append([
                str(index),  # Serial number
                item.description,
                qty_display,
                f"{invoice_data.currency_symbol} {formatted_rate}",
                f"{invoice_data.currency_symbol} {formatted_amount}"
            ])
        
        items_table = Table(items_data, colWidths=[0.5*inch, 2.3*inch, 0.8*inch, 1.2*inch, 1.2*inch])
        
        items_table.setStyle(TableStyle([
            # Header styling - formal and professional
            ('BACKGROUND', (0,0), (-1,0), corporate_blue),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),  # Center all headers
            # Data rows
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,1), (-1,-1), 10),
            ('ALIGN', (0,1), (0,-1), 'CENTER'),  # Serial number center
            ('ALIGN', (1,1), (1,-1), 'LEFT'),    # Description left
            ('ALIGN', (2,1), (-1,-1), 'CENTER'), # QTY, Price, Total center
            # Professional borders
            ('GRID', (0,0), (-1,-1), 1, corporate_blue),
            ('LINEWIDTH', (0,0), (-1,-1), 1),
            # Formal padding
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ]))
        
        story.append(items_table)
        story.append(Spacer(1, 20))
    
    # Totals section with formal presentation
    totals_data = []
    
    # Subtotal
    formatted_subtotal = format_number(invoice_data.subtotal)
    totals_data.append(['', 'Subtotal:', f"{invoice_data.currency_symbol} {formatted_subtotal}"])
    
    # Discount
    if invoice_data.discount_rate and invoice_data.discount_amount:
        formatted_discount = format_number(invoice_data.discount_amount)
        totals_data.append(['', f'Less Discount ({invoice_data.discount_rate}%):', f"({invoice_data.currency_symbol} {formatted_discount})"])
    
    # Tax
    if invoice_data.tax_rate and invoice_data.tax_amount:
        formatted_tax = format_number(invoice_data.tax_amount)
        totals_data.append(['', f'Tax ({invoice_data.tax_rate}%):', f"{invoice_data.currency_symbol} {formatted_tax}"])
    
    # Total
    formatted_total = format_number(invoice_data.total)
    totals_data.append([' ',' TOTAL AMOUNT DUE:', f"{invoice_data.currency_symbol} {formatted_total}"])
    
    totals_table = Table(totals_data, colWidths=[3*inch, 2*inch, 1.5*inch])
    
    totals_table.setStyle(TableStyle([
        # Regular rows
        ('FONTNAME', (0,0), (-1,-2), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-2), 10),
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
        # Total row - corporate highlighting
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,-1), (-1,-1), 12),
        ('BACKGROUND', (1,-1), (-1,-1), corporate_blue),
        ('TEXTCOLOR', (1,-1), (-1,-1), colors.white),
        ('LINEABOVE', (1,-1), (-1,-1), 2, corporate_blue),
        ('GRID', (1,-1), (-1,-1), 1, corporate_blue),
        # Padding
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (1,0), (-1,-1), 15),
        ('RIGHTPADDING', (1,0), (-1,-1), 15),
    ]))
    
    story.append(totals_table)
    
    # Comments section
    if invoice_data.comments:
        story.append(Spacer(1, 25))
        comments_style = ParagraphStyle(
            'CorporateComments',
            parent=styles['Normal'],
            fontSize=10,
            textColor=corporate_gray,
            leftIndent=0
        )
        story.append(Paragraph(f"<b>Additional Notes:</b> {invoice_data.comments}", comments_style))
    
    # Compact authorized signature section
    if (invoice_data.signature and 
        (invoice_data.signature.user_name or signature_path)):
        story.append(Spacer(1, 30))
        
        # Create signature box with proper layout
        sig_box_content = []
        
        # Header with "Authorized Signature" label
        auth_sig_style = ParagraphStyle(
            'CorporateAuthSig',
            parent=styles['Normal'],
            fontSize=11,
            textColor=corporate_blue,
            fontName='Helvetica-Bold',
            spaceAfter=6,
            alignment=1  # Center align
        )
        sig_box_content.append(Paragraph("Authorized Signature", auth_sig_style))
        
        # Signature image inside the box (if provided)
        if signature_path and os.path.exists(signature_path):
            try:
                sig_img = Image(signature_path, width=70, height=30)
                sig_box_content.append(sig_img)
            except:
                # Add signature line if image fails
                line_style = ParagraphStyle(
                    'CorporateSigLine',
                    parent=styles['Normal'],
                    fontSize=12,
                    textColor=corporate_gray,
                    alignment=1
                )
                sig_box_content.append(Paragraph("_" * 25, line_style))
        else:
            # Add signature line if no image
            line_style = ParagraphStyle(
                'CorporateSigLine',
                parent=styles['Normal'],
                fontSize=12,
                textColor=corporate_gray,
                alignment=1,
                spaceAfter=8
            )
            sig_box_content.append(Paragraph("_" * 25, line_style))
        
        # Name under the signature (if provided)
        if invoice_data.signature.user_name:
            name_style = ParagraphStyle(
                'CorporateSigName',
                parent=styles['Normal'],
                fontSize=11,
                textColor=corporate_blue,
                fontName='Helvetica-Bold',
                alignment=1,  # Center align
                spaceBefore=1,
                spaceAfter=0  # Reduced from 1 to 0
            )
            sig_box_content.append(Paragraph(invoice_data.signature.user_name, name_style))
        
        # Position under the name (if provided)
        if invoice_data.signature.position:
            pos_style = ParagraphStyle(
                'CorporateSigPos',
                parent=styles['Normal'],
                fontSize=10,
                textColor=corporate_gray,
                fontName='Helvetica-Oblique',
                alignment=1,  # Center align
                spaceBefore=0  # Reduced from 1 to 0
            )
            sig_box_content.append(Paragraph(invoice_data.signature.position, pos_style))
        
        if sig_box_content:
            # Create signature box with single column layout - each element in its own row
            sig_data = []
            for element in sig_box_content:
                sig_data.append([element])  # Each element in its own row, single column
            
            sig_table = Table(sig_data, colWidths=[2.8*inch])
            sig_table.setStyle(TableStyle([
                # Center alignment for all cells
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                # Background and border
                ('BACKGROUND', (0,0), (-1,-1), light_blue),
                ('LINEWIDTH', (0,0), (-1,-1), 1),
                ('LINECOLOR', (0,0), (-1,-1), corporate_blue),
                ('BOX', (0,0), (-1,-1), 1, corporate_blue),
                # Padding for better spacing
                ('LEFTPADDING', (0,0), (-1,-1), 12),
                ('RIGHTPADDING', (0,0), (-1,-1), 12),
                ('TOPPADDING', (0,0), (-1,-1), 8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ]))
            story.append(sig_table)
    
    doc.build(story)
    return buffer

def generate_elegant_template(buffer, invoice_data: InvoiceData, logo_path=None, signature_path=None):
    """Elegant template with refined typography and sophisticated design"""
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.8*inch, bottomMargin=0.8*inch, 
                          leftMargin=0.8*inch, rightMargin=0.8*inch)
    story = []
    styles = getSampleStyleSheet()
    
    # Elegant color scheme - sophisticated purples and golds
    elegant_purple = colors.HexColor('#6b46c1')   # Rich purple
    elegant_gold = colors.HexColor('#d97706')     # Elegant gold
    elegant_gray = colors.HexColor('#4b5563')     # Sophisticated gray
    elegant_light = colors.HexColor('#faf5ff')   # Very light purple
    
    # Sophisticated header with decorative element
    header_style = ParagraphStyle(
        'ElegantHeader',
        parent=styles['Title'],
        fontSize=28,
        alignment=1,  # Center
        textColor=elegant_purple,
        fontName='Helvetica-Bold',
        spaceAfter=6,
        spaceBefore=6,
        leftIndent=0,
        rightIndent=0
    )
    
    # Add decorative line above title
    decorator_table = Table([['═' * 60]], colWidths=[6*inch])
    decorator_table.setStyle(TableStyle([
        ('FONTSIZE', (0,0), (0,0), 12),
        ('TEXTCOLOR', (0,0), (0,0), elegant_gold),
        ('ALIGN', (0,0), (0,0), 'CENTER'),
    ]))
    story.append(decorator_table)
    
    story.append(Paragraph("INVOICE", header_style))
    
    # Add decorative line below title
    story.append(decorator_table)
    story.append(Spacer(1, 12))
    
    # Company information in elegant layout
    company_section = []
    
    if logo_path and os.path.exists(logo_path):
        try:
            # Reduced logo size for the elegant template
            logo_img = Image(logo_path, width=50, height=50)
            company_section.append([logo_img])
        except:
            pass
    
    company_style = ParagraphStyle(
        'ElegantCompany',
        parent=styles['Normal'],
        fontSize=22,
        textColor=elegant_purple,
        fontName='Helvetica-Bold',
        spaceAfter=12,
        alignment=1  # Center
    )

    company_address_style = ParagraphStyle(
        'ElegantDetails',
        parent=styles['Normal'],
        fontSize=9,
        textColor=elegant_gray,
        fontName='Helvetica-Bold',
        spaceBefore=6,
        spaceAfter=4,
        alignment=1,  # Center
        # fontName='Helvetica-Oblique'  # Italic for elegance
    )
    
    company_details_style = ParagraphStyle(
        'ElegantDetails',
        parent=styles['Normal'],
        fontSize=9,
        textColor=elegant_gray,
        spaceAfter=0,
        alignment=1,  # Center
        fontName='Helvetica-Oblique'  # Italic for elegance
    )
    
    if invoice_data.company.name:
        company_section.append([Paragraph(invoice_data.company.name, company_style)])
    if invoice_data.company.address:
        company_section.append([Paragraph(invoice_data.company.address, company_address_style)])
    if invoice_data.company.email:
        company_section.append([Paragraph(invoice_data.company.email, company_details_style)])
    if invoice_data.company.phone:
        company_section.append([Paragraph(invoice_data.company.phone, company_details_style)])
    
    if company_section:
        # Slightly narrower box and reduced padding to make the company box smaller
        company_table = Table(company_section, colWidths=[5.6*inch])
        company_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BACKGROUND', (0,0), (-1,-1), elegant_light),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
            ('TOPPADDING', (0,0), (-1,-1), 1),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            # Reduce spacing between address, email and phone (assuming address is row -3, email is row -2, phone is row -1)
            ('BOTTOMPADDING', (0,-3), (0,-3), 1),  # Less space after address
            ('TOPPADDING', (0,-3), (0,-3), 6),
            ('TOPPADDING', (0,-2), (0,-2), 1),     # Less space before email
            ('BOTTOMPADDING', (0,-2), (0,-2), 1),  # Less space after email
            ('TOPPADDING', (0,-1), (0,-1), 0),     # Less space before phone
            ('LINEWIDTH', (0,0), (-1,-1), 1),
            ('LINECOLOR', (0,0), (-1,-1), elegant_gold),
            ('BOX', (0,0), (-1,-1), 1, elegant_gold),
        ]))
        story.append(company_table)
    
    story.append(Spacer(1, 25))
    
    # Invoice details with elegant styling
    details_style = ParagraphStyle(
        'ElegantDetailsHeader',
        parent=styles['Normal'],
        fontSize=12,
        textColor=elegant_purple,
        fontName='Helvetica-Bold',
        spaceAfter=10,
        alignment=1
    )
    
    info_style = ParagraphStyle(
        'ElegantInfo',
        parent=styles['Normal'],
        fontSize=10,
        textColor=elegant_gray,
        spaceAfter=6
    )
    
    # Invoice and client info in elegant boxes
    left_info = [Paragraph("INVOICE DETAILS", details_style)]
    left_info.append(Paragraph(f"<b>Invoice Number:</b> {invoice_data.invoice_number}", info_style))
    
    current_date = datetime.now().strftime("%B %d, %Y")
    left_info.append(Paragraph(f"<b>Issue Date:</b> {current_date}", info_style))

    if invoice_data.due_date:
        # Handle both string and date object types
        if isinstance(invoice_data.due_date, str):
            due_date = datetime.strptime(invoice_data.due_date, "%Y-%m-%d").strftime("%B %d, %Y")
        else:
            due_date = invoice_data.due_date.strftime("%B %d, %Y")
        left_info.append(Paragraph(f"<b>Due Date:</b> {due_date}", info_style))
    
    right_info = [Paragraph("BILL TO", details_style)]
    if invoice_data.client_name:
        right_info.append(Paragraph(f"<b>{invoice_data.client_name}</b>", info_style))
    if invoice_data.client_address:
        right_info.append(Paragraph(f"{invoice_data.client_address}", info_style))

    info_table = Table([[left_info, right_info]], colWidths=[3*inch, 3*inch])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (-1,-1), elegant_light),
        ('LEFTPADDING', (0,0), (-1,-1), 15),
        ('RIGHTPADDING', (0,0), (-1,-1), 15),
        ('TOPPADDING', (0,0), (-1,-1), 15),
        ('BOTTOMPADDING', (0,0), (-1,-1), 15),
        ('LINEWIDTH', (0,0), (-1,-1), 1),
        ('LINECOLOR', (0,0), (-1,-1), elegant_purple),
        ('GRID', (0,0), (-1,-1), 1, elegant_purple),
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 25))
    
    # Items table with elegant design
    if invoice_data.items:
        items_data = [['S.NO', 'DESCRIPTION', 'QTY', 'UNIT PRICE', 'AMOUNT']]
        
        for index, item in enumerate(invoice_data.items, 1):
            formatted_rate = format_number(item.unit_price)
            formatted_amount = format_number(item.quantity * item.unit_price)
            # Format quantity as integer if it's a whole number, otherwise show decimal
            qty_display = str(int(item.quantity)) if item.quantity == int(item.quantity) else str(item.quantity)
            items_data.append([
                str(index),  # Serial number
                item.description,
                qty_display,
                f"{invoice_data.currency_symbol} {formatted_rate}",
                f"{invoice_data.currency_symbol} {formatted_amount}"
            ])
        
        items_table = Table(items_data, colWidths=[0.5*inch, 2.3*inch, 0.8*inch, 1.2*inch, 1.2*inch])
        
        items_table.setStyle(TableStyle([
            # Elegant header with gradient-like effect
            ('BACKGROUND', (0,0), (-1,0), elegant_purple),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 11),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),  # Center all headers
            # Data rows with alternating elegant colors
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,1), (-1,-1), 10),
            ('ALIGN', (0,1), (0,-1), 'CENTER'),  # Serial number center
            ('ALIGN', (1,1), (1,-1), 'LEFT'),    # Description left
            ('ALIGN', (2,1), (-1,-1), 'CENTER'), # QTY, Price, Amount center
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, elegant_light]),
            # Sophisticated borders
            ('LINEWIDTH', (0,0), (-1,-1), 1),
            ('LINECOLOR', (0,0), (-1,-1), elegant_purple),
            ('GRID', (0,0), (-1,-1), 1, elegant_purple),
            # Generous padding for elegance
            ('LEFTPADDING', (0,0), (-1,-1), 15),
            ('RIGHTPADDING', (0,0), (-1,-1), 15),
            ('TOPPADDING', (0,0), (-1,-1), 12),
            ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ]))
        
        story.append(items_table)
        story.append(Spacer(1, 20))
    
    # Elegant totals section
    totals_data = []
    
    # Subtotal
    formatted_subtotal = format_number(invoice_data.subtotal)
    totals_data.append(['', 'Subtotal:', f"{invoice_data.currency_symbol} {formatted_subtotal}"])
    
    # Discount
    if invoice_data.discount_rate and invoice_data.discount_amount:
        formatted_discount = format_number(invoice_data.discount_amount)
        totals_data.append(['', f'Discount ({invoice_data.discount_rate}%):', f"- {invoice_data.currency_symbol} {formatted_discount}"])
    
    # Tax
    if invoice_data.tax_rate and invoice_data.tax_amount:
        formatted_tax = format_number(invoice_data.tax_amount)
        totals_data.append(['', f'Tax ({invoice_data.tax_rate}%):', f"{invoice_data.currency_symbol} {formatted_tax}"])
    
    # Total with elegant styling
    formatted_total = format_number(invoice_data.total)
    totals_data.append(['', 'TOTAL:', f"{invoice_data.currency_symbol} {formatted_total}"])
    
    totals_table = Table(totals_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
    
    totals_table.setStyle(TableStyle([
        # Regular rows
        ('FONTNAME', (0,0), (-1,-2), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-2), 11),
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
        # Total row with elegant highlighting
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,-1), (-1,-1), 14),
        ('BACKGROUND', (1,-1), (-1,-1), elegant_purple),
        ('TEXTCOLOR', (1,-1), (-1,-1), colors.white),
        ('LINEABOVE', (1,-1), (-1,-1), 3, elegant_gold),
        ('LINEBELOW', (1,-1), (-1,-1), 3, elegant_gold),
        ('GRID', (1,-1), (-1,-1), 2, elegant_gold),
        # Padding
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (1,0), (-1,-1), 15),
        ('RIGHTPADDING', (1,0), (-1,-1), 15),
    ]))
    
    story.append(totals_table)
    
    # Elegant comments section
    if invoice_data.comments:
        story.append(Spacer(1, 10))
        
        # Comments with decorative border
        comments_content = [[Paragraph(f"<b>Notes:</b><br/>{invoice_data.comments}", 
                                     ParagraphStyle('ElegantComments', parent=styles['Normal'], 
                                                  fontSize=10, textColor=elegant_gray,
                                                  fontName='Helvetica-Oblique'))]]
        
        comments_table = Table(comments_content, colWidths=[6*inch])
        comments_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,0), elegant_light),
            ('LINEWIDTH', (0,0), (0,0), 1),
            ('LINECOLOR', (0,0), (0,0), elegant_purple),
            ('BOX', (0,0), (0,0), 1, elegant_purple),
            ('LEFTPADDING', (0,0), (0,0), 20),
            ('RIGHTPADDING', (0,0), (0,0), 20),
            ('TOPPADDING', (0,0), (0,0), 2),
            ('BOTTOMPADDING', (0,0), (0,0), 2),
        ]))
        story.append(comments_table)
    
    # Elegant signature section
    if (invoice_data.signature and 
        (invoice_data.signature.user_name or signature_path)):
        story.append(Spacer(1, 2))
        
        # Compact signature presentation with signature on line
        sig_elements = []
        
        # Create signature line with embedded signature
        if signature_path and os.path.exists(signature_path):
            try:
                # Reduced signature size to fit on line
                sig_img = Image(signature_path, width=80, height=30)
                # Create signature line with image on top
                sig_elements.append([sig_img])
                sig_elements.append([Paragraph('_' * 35, ParagraphStyle(
                    'ElegantSigLine',
                    parent=styles['Normal'],
                    fontSize=12,
                    textColor=elegant_gold,
                    alignment=1,
                    spaceBefore=-1  # Move line closer to signature
                ))])
            except:
                # Fallback to signature line only
                sig_elements.append([Paragraph('_' * 40, ParagraphStyle(
                    'ElegantSigLine',
                    parent=styles['Normal'],
                    fontSize=12,
                    textColor=elegant_gold,
                    alignment=1
                ))])
        else:
            # Just signature line if no image
            sig_elements.append([Paragraph('_' * 40, ParagraphStyle(
                'ElegantSigLine',
                parent=styles['Normal'],
                fontSize=12,
                textColor=elegant_gold,
                alignment=1
            ))])
        
        if invoice_data.signature.user_name:
            sig_name_style = ParagraphStyle(
                'ElegantSigName',
                parent=styles['Normal'],
                fontSize=12,
                textColor=elegant_purple,
                fontName='Helvetica-Bold',
                alignment=1,
                spaceBefore=5
            )
            sig_elements.append([Paragraph(invoice_data.signature.user_name, sig_name_style)])
        
        if invoice_data.signature.position:
            sig_pos_style = ParagraphStyle(
                'ElegantSigPos',
                parent=styles['Normal'],
                fontSize=10,
                textColor=elegant_gray,
                fontName='Helvetica-Oblique',
                alignment=1,
                spaceBefore=2
            )
            sig_elements.append([Paragraph(invoice_data.signature.position, sig_pos_style)])
            
            sig_table = Table(sig_elements, colWidths=[3*inch])
            sig_table.setStyle(TableStyle([
                ('FONTSIZE', (0,0), (0,0), 12),
                ('TEXTCOLOR', (0,0), (0,0), elegant_gold),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('TOPPADDING', (0,1), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ]))
            
            # Center the signature table
            sig_wrapper = Table([[sig_table]], colWidths=[6*inch])
            sig_wrapper.setStyle(TableStyle([
                ('ALIGN', (0,0), (0,0), 'CENTER'),
            ]))
            story.append(sig_wrapper)
    
    doc.build(story)
    return buffer

@app.post("/api/invoices/generate-pdf")
async def generate_invoice_pdf_endpoint(
    invoice_data: str = Form(...),
    logo: UploadFile = File(None),
    signature: UploadFile = File(None)
):
    """Generate and return PDF invoice with optional logo and signature"""
    try:
        # Parse the JSON invoice data
        import json
        invoice_dict = json.loads(invoice_data)
        invoice_obj = InvoiceData(**invoice_dict)
        
        # Process logo if provided
        logo_path = None
        if logo and logo.content_type and logo.content_type.startswith('image/'):
            print(f"Processing logo: {logo.filename}")
            logo_dir = "static/temp_logos"
            os.makedirs(logo_dir, exist_ok=True)
            
            # Create temporary logo file
            logo_extension = logo.filename.split('.')[-1] if logo.filename else 'png'
            temp_logo_name = f"temp_logo_{uuid.uuid4().hex[:8]}.{logo_extension}"
            logo_path = os.path.join(logo_dir, temp_logo_name)
            
            async with aiofiles.open(logo_path, 'wb') as f:
                content = await logo.read()
                await f.write(content)
            
            print(f"Temporary logo saved: {logo_path}")
        
        # Process signature if provided
        signature_path = None
        if signature and signature.content_type and signature.content_type.startswith('image/'):
            print(f"Processing signature: {signature.filename}")
            signature_dir = "static/temp_signatures"
            os.makedirs(signature_dir, exist_ok=True)
            
            # Create temporary signature file
            sig_extension = signature.filename.split('.')[-1] if signature.filename else 'png'
            temp_sig_name = f"temp_signature_{uuid.uuid4().hex[:8]}.{sig_extension}"
            signature_path = os.path.join(signature_dir, temp_sig_name)
            
            async with aiofiles.open(signature_path, 'wb') as f:
                content = await signature.read()
                await f.write(content)
            
            print(f"Temporary signature saved: {signature_path}")
            
            # Update signature info with temp path
            if invoice_obj.signature:
                invoice_obj.signature.signature_filename = temp_sig_name
        
        # Generate PDF
        buffer = io.BytesIO()
        generate_invoice_pdf_with_temp_files(buffer, invoice_obj, logo_path, signature_path)
        buffer.seek(0)
        
        # Get PDF content before cleanup to avoid buffer issues
        pdf_content = buffer.getvalue()
        buffer.close()
        
        # Clean up temporary files after getting PDF content
        cleanup_temp_files(logo_path, signature_path)
        
        filename = f"invoice_{invoice_obj.invoice_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Use Response instead of StreamingResponse for better reliability
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(pdf_content)),
                "Cache-Control": "no-cache"
            }
        )
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        # Clean up temporary files in case of error
        if 'logo_path' in locals() and logo_path:
            cleanup_temp_files(logo_path, None)
        if 'signature_path' in locals() and signature_path:
            cleanup_temp_files(None, signature_path)
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")

# Upload endpoints removed - now using temporary files sent with PDF generation request

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/test")
async def test_endpoint():
    """Simple test endpoint to verify external access"""
    print("🔍 Test endpoint accessed successfully!")
    return {"message": "Server is accessible!", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    print("Starting Invoice Generator Server...")
    print("Server will be available at:")
    print("   - http://localhost:8000")  
    print("   - http://127.0.0.1:8000")
    print("")
    print("If external browsers don't work, try:")
    print("   1. Disable Windows Firewall temporarily")
    print("   2. Use 127.0.0.1:8000 instead of localhost:8000")
    print("   3. Run as Administrator")
    print("")
    
    # Try localhost first for better compatibility
    try:
        uvicorn.run(app, host="127.0.0.1", port=8000, access_log=True)
    except Exception as e:
        print(f"❌ Failed to start on 127.0.0.1: {e}")
        print("🔄 Trying 0.0.0.0...")
        uvicorn.run(app, host="0.0.0.0", port=8000, access_log=True)