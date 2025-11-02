"""
FastAPI Invoice Generator Backend
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os
from datetime import datetime
from routes import pdf_router
from reportlab.lib.pagesizes import A4


# Initialize FastAPI app with root_path for nginx proxy
app = FastAPI(title="Invoice Generator API", version="1.0.0", root_path="/document-generator")


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
app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")
app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")


# Include original routers
# app.include_router(routes.pdf)
app.include_router(pdf_router)


# API Routes
@app.get("/")
async def root():
    """Serve the landing page"""
    landing_path = os.path.join(FRONTEND_DIR, "landing.html")
    print(f"📄 Serving landing.html from: {landing_path}")
    return FileResponse(landing_path)

@app.get("/invoice")
async def invoice_page():
    """Serve the invoice generation page"""
    invoice_path = os.path.join(FRONTEND_DIR, "invoice.html")
    return FileResponse(invoice_path)

@app.get("/receipt")
async def receipt_page():
    """Serve the receipt generation page"""
    receipt_path = os.path.join(FRONTEND_DIR, "receipt.html")
    return FileResponse(receipt_path)



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
    print("Starting Invoice Generator Server for nginx proxy...")
    print("Server will be available at:")
    print("   - https://vmi2848672.contaboserver.net/document-generator/")
    print("   - Local: http://127.0.0.1:8001")
    
    uvicorn.run(app, host="127.0.0.1", port=8001, access_log=True)