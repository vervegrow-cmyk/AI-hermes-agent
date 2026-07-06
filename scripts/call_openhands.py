from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.clients import OpenHandsClient


def _print(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _health(client: OpenHandsClient) -> None:
    response = client.health()
    _print(
        {
            "status_code": response.status_code,
            "ok": response.is_success,
            "body_preview": response.text[:500],
        }
    )


def _run(client: OpenHandsClient, args: argparse.Namespace) -> None:
    response = client.start_conversation(
        initial_user_text=args.prompt,
        title=args.title,
        run=not args.no_run,
        llm_model=args.llm_model,
        agent_type=args.agent_type,
        trigger="automation",
    )
    response.raise_for_status()
    start_task = response.json()
    if args.wait_ready and start_task.get("status") != "READY":
        start_task = client.wait_for_start_task(
            str(start_task["id"]),
            timeout_seconds=args.timeout,
            poll_interval_seconds=args.poll_interval,
        )
    _print(start_task)


def _send(client: OpenHandsClient, args: argparse.Namespace) -> None:
    response = client.send_message(
        args.conversation_id,
        text=args.prompt,
        run=not args.no_run,
    )
    response.raise_for_status()
    _print(response.json())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Call the local OpenHands instance.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("health", help="Check whether OpenHands is reachable.")

    run_parser = subparsers.add_parser(
        "run",
        help="Start a new OpenHands conversation with an initial prompt.",
    )
    run_parser.add_argument("--prompt", required=True, help="Initial user prompt.")
    run_parser.add_argument("--title", help="Optional conversation title.")
    run_parser.add_argument("--llm-model", help="Optional OpenHands llm_model override.")
    run_parser.add_argument("--agent-type", help="Optional agent type, e.g. default or plan.")
    run_parser.add_argument(
        "--wait-ready",
        action="store_true",
        help="Poll the start task until it reaches READY.",
    )
    run_parser.add_argument(
        "--timeout",
        type=float,
        default=180.0,
        help="Max seconds to wait when --wait-ready is enabled.",
    )
    run_parser.add_argument(
        "--poll-interval",
        type=float,
        default=2.0,
        help="Polling interval in seconds when --wait-ready is enabled.",
    )
    run_parser.add_argument(
        "--no-run",
        action="store_true",
        help="Create the message without auto-running the agent.",
    )

    send_parser = subparsers.add_parser(
        "send",
        help="Send a follow-up user prompt to an existing OpenHands conversation.",
    )
    send_parser.add_argument("--conversation-id", required=True, help="Target conversation id.")
    send_parser.add_argument("--prompt", required=True, help="Follow-up user prompt.")
    send_parser.add_argument(
        "--no-run",
        action="store_true",
        help="Send the message without auto-running the agent.",
    )

    return parser


def main() -> None:
    args = build_parser().parse_args()
    client = OpenHandsClient()

    if args.command == "health":
        _health(client)
        return
    if args.command == "run":
        _run(client, args)
        return
    if args.command == "send":
        _send(client, args)
        return
    raise ValueError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
