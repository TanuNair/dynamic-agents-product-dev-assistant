#!/bin/bash

# Installation script for Virtual PMT with Web Search Tool

echo "=================================="
echo "Virtual PMT Installation"
echo "=================================="
echo ""

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "✅ Virtual environment 'venv' found"
    VENV_PATH="venv"
elif [ -d "venv311" ]; then
    echo "✅ Virtual environment 'venv311' found"
    VENV_PATH="venv311"
else
    echo "❌ No virtual environment found"
    echo "Creating new virtual environment..."
    python3 -m venv venv
    VENV_PATH="venv"
fi

echo ""
echo "Activating virtual environment..."
source $VENV_PATH/bin/activate

echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "=================================="
echo "✅ Installation Complete!"
echo "=================================="
echo ""
echo "To run the application:"
echo "1. Activate virtual environment:"
echo "   source $VENV_PATH/bin/activate"
echo ""
echo "2. Run Streamlit app:"
echo "   streamlit run src/main.py"
echo ""
echo "To test the tools:"
echo "   python test/test_google_trends.py"
echo "   python test/test_web_search.py"
echo ""

# Made with Bob
