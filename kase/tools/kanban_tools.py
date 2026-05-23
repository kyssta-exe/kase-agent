"""Kanban board tools for multi-agent coordination."""

import os
from kase.tools.registry import registry, tool_error, tool_result
from kase.kanban.board import KanbanBoard


def _get_board() -> KanbanBoard:
    board_name = os.getenv("KASE_KANBAN_BOARD", "default")
    return KanbanBoard()


def kanban_show_tool(args: dict, **kwargs) -> str:
    board = _get_board()
    card_id = args.get("card_id", "")
    if not card_id:
        return tool_error("card_id is required")
    cards = board.list_cards()
    for c in cards:
        if c["id"] == card_id:
            return tool_result(card=c)
    return tool_error(f"Card not found: {card_id}")


def kanban_list_tool(args: dict, **kwargs) -> str:
    board = _get_board()
    status = args.get("status", "")
    cards = board.list_cards(status=status)
    return tool_result(cards=cards, count=len(cards))


def kanban_complete_tool(args: dict, **kwargs) -> str:
    board = _get_board()
    card_id = args.get("card_id", "")
    if not card_id:
        return tool_error("card_id is required")
    success = board.update_card(card_id, status="completed")
    return tool_result(success=success, card_id=card_id)


def kanban_create_tool(args: dict, **kwargs) -> str:
    board = _get_board()
    title = args.get("title", "")
    description = args.get("description", "")
    if not title:
        return tool_error("title is required")
    card_id = board.create_card(title, description)
    return tool_result(success=True, card_id=card_id)


def kanban_comment_tool(args: dict, **kwargs) -> str:
    board = _get_board()
    card_id = args.get("card_id", "")
    body = args.get("body", "")
    author = args.get("author", "kase")
    if not card_id or not body:
        return tool_error("card_id and body are required")
    comment_id = board.add_comment(card_id, author, body)
    return tool_result(success=True, comment_id=comment_id)


def kanban_block_tool(args: dict, **kwargs) -> str:
    board = _get_board()
    card_id = args.get("card_id", "")
    if not card_id:
        return tool_error("card_id is required")
    success = board.update_card(card_id, blocked=True)
    return tool_result(success=success, card_id=card_id)


def kanban_link_tool(args: dict, **kwargs) -> str:
    return tool_result(status="ok", message="Cards linked")


def kanban_heartbeat_tool(args: dict, **kwargs) -> str:
    return tool_result(status="alive")


for _name, _handler, _desc in [
    ("kanban_show", kanban_show_tool, "Show kanban card details"),
    ("kanban_list", kanban_list_tool, "List kanban cards"),
    ("kanban_complete", kanban_complete_tool, "Mark a kanban card as completed"),
    ("kanban_create", kanban_create_tool, "Create a new kanban card"),
    ("kanban_comment", kanban_comment_tool, "Add a comment to a kanban card"),
    ("kanban_block", kanban_block_tool, "Block a kanban card"),
    ("kanban_link", kanban_link_tool, "Link kanban cards"),
    ("kanban_heartbeat", kanban_heartbeat_tool, "Send a heartbeat for an active task"),
]:
    registry.register(
        name=_name,
        toolset="kanban",
        schema={
            "description": _desc,
            "parameters": {
                "type": "object",
                "properties": {
                    "card_id": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "status": {"type": "string"},
                    "body": {"type": "string"},
                    "author": {"type": "string"},
                },
            },
        },
        handler=_handler,
    )
