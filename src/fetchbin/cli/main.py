import argparse
import subprocess
import sys

import requests

from .. import __about__
from . import constants


class CustomHelpFormatter(argparse.HelpFormatter):
    def _format_action(self, action):
        parts = super()._format_action(action)

        if action.nargs == argparse.PARSER:
            lines = parts.split("\n")

            if len(lines) > 1:
                lines = lines[1:]

                for i in range(len(lines)):
                    if len(lines[i]) > 2:
                        lines[i] = lines[i][2:]
                parts = "\n".join(lines)

        return parts


def make_api_request(method, path, **kwargs):
    try:
        response = requests.request(method, f"{constants.API_URL}/{path}", **kwargs)
        response.raise_for_status()
        return response
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to {constants.API_URL}.", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        if e.response and e.response.status_code == 404:
            print("Error: Share not found or already deleted.", file=sys.stderr)
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


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

    payload = {
        "content": output,
        "command": " ".join(command),
        "is_hidden": args.hidden,
    }

    response = make_api_request("post", "api/share", json=payload)
    data = response.json()
    print("Success! Your output has been shared.")
    print(f"URL: {data['url']}")
    print(f"Delete URL: {data['delete_url']}")


def delete_command(args):
    token = args.token

    if not token:
        print("Error: Please provide a delete token.", file=sys.stderr)
        sys.exit(1)

    if "/" in token:
        token = token.split("/")[-1]

    make_api_request("post", f"delete/{token}")
    print("Success! The share has been deleted.")


def main():
    parser = argparse.ArgumentParser(
        description="A simple CLI to share command outputs via the fetchbin API.",
        formatter_class=CustomHelpFormatter,
        add_help=False,
    )
    parser.add_argument("-h", "--help", action="help", help="Show this help message and exit.")
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__about__.__version__}",
        help="Show program's version number and exit.",
    )
    subparsers = parser.add_subparsers(dest="subcommand", title="subcommands")

    parser_share = subparsers.add_parser("share", help="Run a command and share its output.", add_help=False)
    parser_share.add_argument("-h", "--help", action="help", help="Show this help message and exit.")
    parser_share.add_argument("-s", "--hidden", action="store_true", help="Share the output as hidden.")
    parser_share.add_argument("command", nargs=argparse.REMAINDER, help="The command to run.")
    parser_share.set_defaults(func=share_command)

    parser_delete = subparsers.add_parser("delete", help="Delete a shared output.", add_help=False)
    parser_delete.add_argument("-h", "--help", action="help", help="Show this help message and exit.")
    parser_delete.add_argument("token", nargs="?", help="The delete token for the share.")
    parser_delete.set_defaults(func=delete_command)

    args = parser.parse_args()

    if args.subcommand is None:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
