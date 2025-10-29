import argparse
import subprocess
import sys
import requests

API_URL = "http://127.0.0.1:8000/api/share"


def share_command(args):
    command = args.command

    if not command:
        print("Error: Please provide a command to run.", file=sys.stderr)
        sys.exit(1)

    try:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        output = process.stdout

        if process.stderr:
            output += "\n--- STDERR ---\n" + process.stderr

    except FileNotFoundError:
        print(f"Error: Command not found: '{command[0]}'", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error running command: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        tool_name = command[0]
        payload = {"content": output, "tool_name": tool_name}
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()

    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the fetchbin API server.", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"Error sending data to API: {e}", file=sys.stderr)
        sys.exit(1)

    data = response.json()
    print("Success! Your output has been shared.")
    print(f" URL: {data['url']}")
    print(f" Delete URL: {data['delete_url']}")


def main():
    parser = argparse.ArgumentParser(description="A simple CLI to share command outputs via the fetchbin API.")
    subparsers = parser.add_subparsers(dest="subcommand")

    parser_share = subparsers.add_parser("share", help="Run a command and share its output.")
    parser_share.add_argument("command", nargs="*", help="The command to run.")
    parser_share.set_defaults(func=share_command)

    args = parser.parse_args()

    if args.subcommand is None:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
