#!/bin/bash

# Invoice Generator Server Startup Script
echo "Starting Invoice Generator Server for nginx proxy..."
echo "Server will be available at: https://vmi2848672.contaboserver.net/document-generator/"

cd /root/invoice_receipt-generator/backend

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Virtual environment activated"
fi

# Start the server
python main.py