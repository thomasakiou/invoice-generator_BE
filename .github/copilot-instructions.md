# Invoice Generator - Copilot Instructions

## Project Overview
A professional invoice generator web application built with FastAPI backend and modern frontend. Create, customize, and generate beautiful PDF invoices with company branding.

## ✨ Key Features
- **Company Information**: Name, address, email, phone with logo upload
- **Invoice Management**: Auto-generated numbers, dates, client details
- **Item Management**: Dynamic item addition with quantity/price tracking
- **Financial Calculations**: Automatic subtotal, tax, discount, and total calculations
- **Professional Touch**: Custom comments, signature upload, professional PDF layout
- **User Experience**: Responsive design, real-time preview, drag-and-drop uploads

## 🛠 Technology Stack
- **Backend**: FastAPI (Python) with ReportLab for PDF generation
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **File Handling**: Multipart uploads for images
- **PDF Generation**: Professional invoice layouts with company branding

## 🚀 Quick Start
1. **Start the server**: `cd backend && python main.py`
2. **Open browser**: Navigate to `http://localhost:8000`
3. **Create invoice**: Fill in company details, items, and generate PDF

## 📁 Project Structure
```
invoice_generator/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   └── static/             # Static files
│       ├── logos/          # Company logos
│       └── signatures/     # Signature images
├── frontend/
│   ├── index.html          # Main application
│   ├── css/styles.css      # Application styles
│   └── js/invoice.js       # Frontend functionality
└── .github/copilot-instructions.md
```

## 🔌 API Endpoints
- `GET /` - Main application page
- `POST /api/invoices/generate-pdf` - Generate PDF invoice
- `POST /api/upload/logo` - Upload company logo
- `POST /api/upload/signature` - Upload signature image
- `GET /api/health` - Health check

## 💡 Development Guidelines
- **Code Quality**: Follow PEP 8 for Python, use semantic HTML/CSS
- **Error Handling**: Implement comprehensive validation and user feedback
- **Responsive Design**: Ensure mobile compatibility
- **Security**: Validate file uploads and sanitize inputs
- **Performance**: Optimize PDF generation and file handling

## 🎯 Usage Instructions
1. **Company Setup**: Add company details and upload logo
2. **Invoice Details**: Set invoice number, dates, client information
3. **Add Items**: Use dynamic item management with real-time calculations
4. **Customize**: Add tax/discount, comments, and signature
5. **Generate**: Preview or download professional PDF invoice

This is a complete, production-ready invoice generator with modern UI and professional PDF output.