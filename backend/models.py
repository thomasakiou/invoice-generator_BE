from pydantic import BaseModel
from typing import List, Optional
from datetime import date

# Pydantic models
class InvoiceItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    
class CompanyDetails(BaseModel):
    name: str
    services: Optional[str] = None
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

class ReceiptData(BaseModel):
    receipt_number: str
    currency: str = "USD"
    currency_symbol: str = "$"
    template: str = "classic"
    company: CompanyDetails
    customer_name: str
    customer_address: Optional[str] = None
    payment_date: Optional[date] = None
    payment_method: str = "cash"
    items: List[InvoiceItem]
    subtotal: float
    tax_rate: Optional[float] = None
    tax_amount: Optional[float] = None
    discount_rate: Optional[float] = None
    discount_amount: Optional[float] = None
    total: float
    comments: Optional[str] = None
    signature: Optional[SignatureInfo] = None