#!/bin/bash

# Exit on any error
set -e

# Configuration
ENV_DIR="venv"
MODEL_NAME="sovereign-ai"
ALIAS_NAME="sai"
DB_PATH="$HOME/.local_ai_memory.db"

# 1. Initialize the SQLite database
# The Python script handles creating the table if it doesn't exist, but we can ensure the file is there.
if [ ! -f "$DB_PATH" ]; then
    echo "Initializing SQLite database at $DB_PATH..."
    touch "$DB_PATH"
else
    echo "SQLite database already exists at $DB_PATH."
fi

# 2. Set up the Python virtual environment and dependencies
if [ ! -d "$ENV_DIR" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv "$ENV_DIR"
fi

echo "Activating virtual environment and installing dependencies..."
source "$ENV_DIR/bin/activate"
pip install --upgrade pip
pip install requests

# 3. Pull the base model and create the custom model via Modelfile
# Assuming ollama is installed and running
echo "Pulling base model (llama3)..."
ollama pull llama3

echo "Creating custom model ($MODEL_NAME) from Modelfile..."
ollama create $MODEL_NAME -f Modelfile

# 4. Set up a global terminal alias
# We'll determine the absolute path to the daemon.py script
SCRIPT_PATH=$(realpath "daemon.py")
VENV_PYTHON=$(realpath "$ENV_DIR/bin/python")

# Add alias to .bashrc if it doesn't exist
BASHRC="$HOME/.bashrc"
ALIAS_CMD="alias $ALIAS_NAME='$VENV_PYTHON $SCRIPT_PATH'"

if ! grep -q "alias $ALIAS_NAME=" "$BASHRC"; then
    echo "Adding alias '$ALIAS_NAME' to $BASHRC..."
    echo "" >> "$BASHRC"
    echo "# Sovereign AI Alias" >> "$BASHRC"
    echo "$ALIAS_CMD" >> "$BASHRC"
    echo "Alias added. Run 'source ~/.bashrc' or restart your terminal to use '$ALIAS_NAME'."
else
    echo "Alias '$ALIAS_NAME' already exists in $BASHRC."
fi

echo "Setup complete!"
