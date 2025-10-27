"""
Start ReelForge API Server

Run this script to start the FastAPI server:
    uv run python start_api.py
    
Or with custom settings:
    uv run python start_api.py --host 0.0.0.0 --port 8080 --reload
"""

import argparse
import uvicorn


def main():
    """Start API server"""
    parser = argparse.ArgumentParser(description="Start ReelForge API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    ReelForge API Server                      ║
╚══════════════════════════════════════════════════════════════╝

Starting server at http://{args.host}:{args.port}
API Docs: http://{args.host}:{args.port}/docs
ReDoc: http://{args.host}:{args.port}/redoc

Press Ctrl+C to stop the server
""")
    
    uvicorn.run(
        "api.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()

