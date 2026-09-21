"""
Adaptive Content Intelligence - Root Application Proxy.

Provides 100% backward-compatible export of the FastAPI `app`
so that running `uvicorn app:app --reload` or existing scripts continues
to function seamlessly with the modular backend architecture.
"""

from backend.app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
