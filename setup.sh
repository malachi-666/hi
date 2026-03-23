#!/bin/bash

# Exit on any error
set -e

# Configuration
ENV_DIR="ai_env"
ALIAS_NAME="lai" # local ai
FAST_MODEL="llama3" # Example 8B fast model
HEAVY_MODEL="llama3:70b" # Example 70B heavy model (adjust based on actual quantized model availability)

# 1. Set up the Python virtual environment
if [ ! -d "$ENV_DIR" ]; then
    echo "Creating Python virtual environment in $ENV_DIR..."
    python3 -m venv "$ENV_DIR"
else
    echo "Virtual environment $ENV_DIR already exists."
fi

# 2. Install dependencies (Open Interpreter)
echo "Activating virtual environment and installing Open Interpreter..."
source "$ENV_DIR/bin/activate"
pip install --upgrade pip
# Install open-interpreter which handles the heavy lifting of system interaction safely
pip install open-interpreter

# 3. Pull required Ollama models
# Assuming ollama is installed and running
echo "Pulling fast model ($FAST_MODEL)..."
ollama pull $FAST_MODEL || echo "Warning: Could not pull $FAST_MODEL. Is Ollama running?"

echo "Pulling heavy model ($HEAVY_MODEL)..."
ollama pull $HEAVY_MODEL || echo "Warning: Could not pull $HEAVY_MODEL. Is Ollama running?"

# 4. Set up a global terminal alias
SCRIPT_PATH=$(realpath "orchestrator.py")
VENV_PYTHON=$(realpath "$ENV_DIR/bin/python")

BASHRC="$HOME/.bashrc"
ALIAS_CMD="alias $ALIAS_NAME='$VENV_PYTHON $SCRIPT_PATH'"

if ! grep -q "alias $ALIAS_NAME=" "$BASHRC"; then
    echo "Adding alias '$ALIAS_NAME' to $BASHRC..."
    echo "" >> "$BASHRC"
    echo "# Sovereign AI Orchestrator Alias" >> "$BASHRC"
    echo "$ALIAS_CMD" >> "$BASHRC"
    echo "Alias added. Run 'source ~/.bashrc' or restart your terminal to use '$ALIAS_NAME'."
else
    echo "Alias '$ALIAS_NAME' already exists in $BASHRC."
fi

echo "Setup complete! Open Interpreter is installed and ready."
