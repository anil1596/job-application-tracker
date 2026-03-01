#!/bin/bash

# Setup script for Job Application Tracker

echo "================================="
echo "Job Application Tracker - Setup"
echo "================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version
if [ $? -ne 0 ]; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p logs

# Check for resume
echo ""
if [ -f "Resume.pdf" ]; then
    echo "✓ Resume.pdf found"
else
    echo "⚠ Resume.pdf not found - please add your resume as Resume.pdf"
fi

# Check for credentials
if [ -f "credentials.json" ]; then
    echo "✓ credentials.json found"
else
    echo "⚠ credentials.json not found"
    echo "  Please download Google service account credentials and save as credentials.json"
    echo "  See README.md for instructions"
fi

# Create .env from example if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ Created .env - please edit it with your configuration"
fi

echo ""
echo "================================="
echo "Setup Complete!"
echo "================================="
echo ""
echo "Next steps:"
echo "1. Add your Resume.pdf to this directory"
echo "2. Download Google credentials and save as credentials.json"
echo "3. Create a Google Sheet and share it with your service account"
echo "4. Test the tool:"
echo "   python main.py --sheet 'YOUR_SHEET_URL' --url 'JOB_URL'"
echo ""
echo "See README.md for detailed instructions"
echo ""
