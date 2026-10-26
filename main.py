"""
Quanteinstein B2B Outbound Intelligence & Connection Request Engine.
Unified entry point for Web Server and CLI operations.
"""

import sys
import uvicorn
from app.config import settings

def start_server(host: str = None, port: int = None, reload: bool = None):
    """Start the FastAPI application with Uvicorn."""
    h = host or settings.HOST
    p = port or settings.PORT
    r = reload if reload is not None else settings.DEBUG
    print("=" * 70)
    print(f"Starting Quanteinstein B2B Intelligence Engine on http://{h}:{p}")
    print(f"API Docs available at: http://{h}:{p}/docs")
    print(f"Interactive Web UI at: http://{h}:{p}/")
    print("=" * 70)
    uvicorn.run("app.api:app", host=h, port=p, reload=r)


if __name__ == "__main__":
    cli_commands = ("cli", "analyze", "batch", "stats", "interactive", "prospect", "test-smtp", "send-email")
    if len(sys.argv) > 1 and (sys.argv[1] in cli_commands or sys.argv[1] in ("--help", "-h")):
        from app.cli import main as cli_main
        # If user typed 'python main.py cli ...', strip 'cli'
        if sys.argv[1] == "cli":
            sys.argv.pop(1)
        cli_main()
    else:
        start_server()

