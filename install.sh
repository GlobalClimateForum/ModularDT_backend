#!/bin/bash

# 1. Exit immediately if any command fails
set -e

# 2. Define the path to your virtual environment (change 'venv' if your folder has a different name)
VENV_DIR=".venv"

# 3. Activate the virtual environment
if [ -d "$VENV_DIR" ]; then
    echo "🔄 Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
else
    echo "❌ Error: Virtual environment directory '$VENV_DIR' not found."
    exit 1
fi

# 4. Upgrade pip inside the environment first
echo "⚡ Upgrading pip..."
pip install --upgrade pip

# 5. Install all packages from the requirements file
if [ -f "requirements.txt" ]; then
    echo "📦 Installing packages from requirements.txt..."
    pip install -r requirements.txt
    echo "✅ All packages installed successfully!"
else
    echo "❌ Error: requirements.txt not found."
    exit 1
fi

npm install
cd ./marp-server/ && npm install && cd ..

p
