import argparse
import sqlite3
import json
import sys
import os
import requests

DB_PATH = os.path.expanduser('~/.local_ai_memory.db')
OLLAMA_ENDPOINT = 'http://localhost:11434/api/generate'
MODEL_NAME = 'sovereign-ai'  # This should match the name used when creating the model via setup.sh

def init_db():
    """Initializes the SQLite database for logging queries and responses."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            query TEXT NOT NULL,
            response TEXT NOT NULL
        )
    ''')
    conn.commit()
    return conn

def get_context(conn):
    """Retrieves the last 10 executed commands for context."""
    cursor = conn.cursor()
    cursor.execute('SELECT query, response FROM history ORDER BY id DESC LIMIT 10')
    rows = cursor.fetchall()
    # Reverse to get chronological order for context
    return rows[::-1]

def log_interaction(conn, query, response):
    """Logs the query and the AI's response to the database."""
    cursor = conn.cursor()
    cursor.execute('INSERT INTO history (query, response) VALUES (?, ?)', (query, response))
    conn.commit()

def generate_command(query, context):
    """Queries the local Ollama instance to generate the bash command."""

    # Construct a prompt that includes the context of the last 10 interactions
    context_str = ""
    if context:
        context_str = "Previous interactions (for context):\n"
        for q, r in context:
            context_str += f"Q: {q}\nA: {r}\n"
        context_str += "\n"

    full_prompt = f"{context_str}Current intent: {query}\nCommand:"

    payload = {
        "model": MODEL_NAME,
        "prompt": full_prompt,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_ENDPOINT, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get('response', '').strip()
    except requests.exceptions.RequestException as e:
        print(f"Error querying Ollama: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Sovereign AI Terminal Assistant')
    parser.add_argument('query', nargs='*', help='The high-level intent or query')
    args = parser.parse_args()

    # Handle piped input (stdin)
    stdin_input = ""
    if not sys.stdin.isatty():
        stdin_input = sys.stdin.read().strip()

    # Combine stdin and positional arguments
    query_parts = []
    if stdin_input:
        query_parts.append(f"Input data:\n{stdin_input}\n")
    if args.query:
        query_parts.append(" ".join(args.query))

    query = " ".join(query_parts).strip()

    if not query:
        parser.print_help()
        sys.exit(1)

    # Initialize DB and get context
    conn = init_db()
    context = get_context(conn)

    # Generate command
    command = generate_command(query, context)

    if command:
        # Output the generated script/one-liner to stdout
        print(command)
        # Log the interaction
        log_interaction(conn, query, command)
    else:
        print("Failed to generate a command.", file=sys.stderr)
        sys.exit(1)

    conn.close()

if __name__ == '__main__':
    main()
