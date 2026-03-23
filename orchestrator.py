import argparse
import sys
import os

def main():
    parser = argparse.ArgumentParser(description='Universal Local AI Orchestrator')
    parser.add_argument('query', nargs='*', help='The high-level intent or instruction')
    parser.add_argument('--heavy', action='store_true', help='Use the heavy model (e.g., 70B) for deep analysis')
    parser.add_argument('--fast', action='store_true', help='Use the fast model (e.g., 8B) for quick tasks (Default)')

    args = parser.parse_args()

    # Handle piped input (stdin) for text processing
    stdin_input = ""
    if not sys.stdin.isatty():
        stdin_input = sys.stdin.read().strip()

    # Combine stdin and positional arguments
    query_parts = []
    if stdin_input:
        query_parts.append(f"Context/Input Data:\n{stdin_input}\n")
    if args.query:
        query_parts.append(" ".join(args.query))

    full_query = " ".join(query_parts).strip()

    if not full_query and not stdin_input:
        parser.print_help()
        sys.exit(1)

    # Determine Model Weight
    model_name = "ollama/llama3" # Default fast
    if args.heavy:
        model_name = "ollama/llama3:70b"

    # Enforce strictly local API execution for Open Interpreter
    # Open Interpreter will automatically use the local Ollama instance running at localhost:11434
    # when an ollama/ model is specified.

    print(f"[*] Routing to Local Model: {model_name}")
    print("[*] Privacy First: External APIs strictly disabled.")
    print("[*] Open Interpreter Engine Starting... Safety Catch [Y/n] is ENABLED.")
    print("-" * 50)

    # Note: We import interpreter here so it only loads if arguments are parsed successfully.
    try:
        from interpreter import interpreter
    except ImportError:
        print("Error: 'open-interpreter' is not installed. Please run setup.sh.")
        sys.exit(1)

    # Configure Interpreter
    interpreter.offline = True           # Strictly disable telemetry/external pings
    interpreter.llm.model = model_name   # Set the selected Ollama model
    interpreter.llm.api_base = "http://localhost:11434/api" # Enforce local endpoint

    # We explicitly do NOT set auto_run to True, preserving the crucial [Y/n] safety catch.
    interpreter.auto_run = False

    try:
        # Pass the full constructed intent to the interpreter
        interpreter.chat(full_query)
    except KeyboardInterrupt:
        print("\n[!] Execution aborted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[X] An error occurred: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
