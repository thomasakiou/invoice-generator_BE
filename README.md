# Invoice Generator

A professional invoice generator web application built with FastAPI backend and modern frontend. Create, customize, and generate beautiful PDF invoices with company branding.

## Features

### 🏢 Company Information
- Company name, address, email, and phone
- Company logo upload and display
- Professional branding integration

### 📄 Invoice Management
- Auto-generated invoice numbers
- Customizable purchase and due dates
- Client information management

### 🛒 Item Management
- Dynamic item addition/removal
- Quantity and unit price tracking
- Real-time total calculations

### 💰 Financial Calculations
- Automatic subtotal calculation
- Optional tax percentage and amount
- Optional discount percentage and amount
- Final total computation

### ✍️ Professional Touch
- Custom comments and notes
- User signature with name and position
- Signature image upload
- Professional PDF layout

### 📱 User Experience
- Responsive design for all devices
- Real-time preview functionality
- Drag-and-drop file uploads
- Professional UI with smooth animations

## Technology Stack

- **Backend**: FastAPI (Python)
- **Frontend**: HTML5, CSS3, JavaScript
- **PDF Generation**: ReportLab
- **File Handling**: Multipart uploads
- **Styling**: Modern CSS with animations

## Project Structure

```
invoice_generator/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   └── static/             # Static files
│       ├── logos/          # Company logos
│       └── signatures/     # Signature images
├── frontend/
│   ├── index.html          # Main application page
│   ├── css/
│   │   └── styles.css      # Application styles
│   └── js/
│       └── invoice.js      # Frontend functionality
├── .github/
│   └── copilot-instructions.md
└── README.md
```

## Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd invoice_generator
   ```

2. **Set up Python environment:**
   ```bash
   cd backend
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Start the backend server:**
   ```bash
   cd backend
   python main.py
   ```

2. **Open your browser and navigate to:**
   ```
   http://localhost:8000
   ```

3. **Fill in the invoice details:**
   - Company information
   - Invoice number (auto-generated)
   - Client details
   - Items with quantities and prices
   - Optional tax and discount
   - Comments and signature

4. **Generate your invoice:**
   - Click "Preview" to view before download
   - Click "Generate PDF" to download

## API Endpoints

- `GET /` - Main application page
- `POST /api/invoices/generate-pdf` - Generate PDF invoice
- `POST /api/upload/logo` - Upload company logo
- `POST /api/upload/signature` - Upload signature image
- `GET /api/health` - Health check

## Features in Detail

### Company Logo
- Upload any image format (PNG, JPG, GIF, etc.)
- Automatic resizing and positioning
- Fallback placeholder when no logo is provided

### Invoice Items
- Add unlimited items
- Real-time calculation of totals
- Easy item removal
- Responsive item management

### Tax and Discount
- Percentage-based calculations
- Optional fields (shown only when used)
- Automatic total recalculation

### Signature System
- Upload signature images
- Display user name and position
- Professional signature section in PDF

### PDF Generation
- Professional invoice layout
- Company branding integration
- Responsive design elements
- High-quality output

## Customization

The application is designed to be easily customizable:

1. **Styling**: Modify `frontend/css/styles.css`
2. **PDF Layout**: Update the PDF generation functions in `backend/main.py`
3. **Form Fields**: Add new fields in `frontend/index.html` and corresponding JavaScript
4. **Business Logic**: Extend the FastAPI backend with additional endpoints

## Development

### Frontend Development
The frontend uses vanilla JavaScript with modern ES6+ features:
- Class-based architecture
- Event-driven programming
- Real-time calculations
- File upload handling

### Backend Development
The backend uses FastAPI with:
- Pydantic models for validation
- ReportLab for PDF generation
- Async file handling
- CORS enabled for development

### Adding New Features
1. Update the Pydantic models in `main.py`
2. Modify the PDF generation function
3. Update the frontend form and JavaScript
4. Test the complete workflow

## Troubleshooting

### Common Issues

1. **PDF Generation Fails**
   - Ensure ReportLab is properly installed
   - Check image file formats and sizes
   - Verify all required fields are filled

2. **File Upload Issues**
   - Check file permissions in static directories
   - Ensure image files are valid format
   - Verify sufficient disk space

3. **Styling Issues**
   - Clear browser cache
   - Check CSS file path
   - Verify responsive design breakpoints

### Error Messages
The application provides user-friendly error messages for:
- Missing required fields
- Invalid file uploads
- PDF generation errors
- Network connectivity issues

## License

This project is open source and available under the MIT License.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

For support and questions:
- Check the troubleshooting section
- Review the code documentation
- Create an issue in the repository

---

**Happy Invoicing!** 🧾✨