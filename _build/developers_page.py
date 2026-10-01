"""Preserved MCP documentation body. Shared shell comes from the current build."""
from pathlib import Path
from partials import head, page

def build_developers_page(write_fn):
    body = Path(__file__).with_name("developers_body.html").read_text(encoding="utf-8")
    write_fn("/developers/", page(head("Valora for developers - MCP server documentation | Valora", "Public MCP server for Valora's educational financial-planning content: endpoint, tools, parameters and example calls for MCP clients.", path="/developers/"), body))
