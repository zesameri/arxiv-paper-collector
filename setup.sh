#!/bin/bash

echo "🔬 ArXiv Paper Collector Setup"
echo "=============================="
echo

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "📦 Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    
    # Add Poetry to PATH for current session
    export PATH="$HOME/.local/bin:$PATH"
    
    echo "✅ Poetry installed!"
    echo "⚠️  You may need to restart your terminal or run: export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo
else
    echo "✅ Poetry is already installed"
    echo
fi

# Check Python version
echo "🐍 Checking Python version..."
if command -v python3.11 &> /dev/null; then
    echo "✅ Python 3.11 found"
    PYTHON_CMD="python3.11"
elif command -v python3.12 &> /dev/null; then
    echo "✅ Python 3.12 found"
    PYTHON_CMD="python3.12"
else
    echo "❌ Python 3.11 or 3.12 required but not found"
    echo "Please install Python 3.11 or 3.12 and try again"
    exit 1
fi

# Configure Poetry to use the correct Python version
echo "⚙️  Configuring Poetry to use $PYTHON_CMD..."
poetry env use $PYTHON_CMD

# Install dependencies
echo "📚 Installing dependencies..."
poetry install

echo
echo "🎉 Setup complete!"
echo
echo "To get started:"
echo "  poetry run python quick_start.py"
echo
echo "Or use the command line interface:"
echo "  poetry run python main.py --email your@email.com --authors \"Author Name\" --expand"
echo 