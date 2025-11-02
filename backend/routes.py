from pdf_template import cleanup_temp_files, generate_invoice_pdf_with_temp_files
from receipt_template import generate_receipt_pdf_with_temp_files
from fastapi import HTTPException, UploadFile, APIRouter, File, Form
from fastapi.responses import Response
import io
import os
import uuid
from datetime import datetime
import aiofiles
from models import InvoiceData, ReceiptData

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch



pdf_router = APIRouter(
    tags=["Invoice-Genrator"], 
)


@pdf_router.post("/api/receipts/generate-pdf")
async def generate_receipt_pdf_endpoint(
    receipt_data: str = Form(...),
    logo: UploadFile = File(None),
    signature: UploadFile = File(None)
):
    """Generate and return PDF receipt with optional logo and signature"""
    try:
        # Parse the JSON receipt data
        import json
        receipt_dict = json.loads(receipt_data)
        receipt_obj = ReceiptData(**receipt_dict)
        
        # Process logo if provided
        logo_path = None
        if logo and logo.content_type and logo.content_type.startswith('image/'):
            logo_dir = "static/temp_logos"
            os.makedirs(logo_dir, exist_ok=True)
            
            logo_extension = logo.filename.split('.')[-1] if logo.filename else 'png'
            temp_logo_name = f"temp_logo_{uuid.uuid4().hex[:8]}.{logo_extension}"
            logo_path = os.path.join(logo_dir, temp_logo_name)
            
            async with aiofiles.open(logo_path, 'wb') as f:
                content = await logo.read()
                await f.write(content)
        
        # Process signature if provided
        signature_path = None
        if signature and signature.content_type and signature.content_type.startswith('image/'):
            signature_dir = "static/temp_signatures"
            os.makedirs(signature_dir, exist_ok=True)
            
            sig_extension = signature.filename.split('.')[-1] if signature.filename else 'png'
            temp_sig_name = f"temp_signature_{uuid.uuid4().hex[:8]}.{sig_extension}"
            signature_path = os.path.join(signature_dir, temp_sig_name)
            
            async with aiofiles.open(signature_path, 'wb') as f:
                content = await signature.read()
                await f.write(content)
            
            if receipt_obj.signature:
                receipt_obj.signature.signature_filename = temp_sig_name
        
        # Generate PDF using receipt template
        buffer = io.BytesIO()
        generate_receipt_pdf_with_temp_files(buffer, receipt_obj, logo_path, signature_path)
        buffer.seek(0)
        
        pdf_content = buffer.getvalue()
        buffer.close()
        
        cleanup_temp_files(logo_path, signature_path)
        
        filename = f"receipt_{receipt_obj.receipt_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
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
        if 'logo_path' in locals() and logo_path:
            cleanup_temp_files(logo_path, None)
        if 'signature_path' in locals() and signature_path:
            cleanup_temp_files(None, signature_path)
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")

@pdf_router.post("/api/invoices/generate-pdf")
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
