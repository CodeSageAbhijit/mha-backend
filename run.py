from app.main import app
# import logging
# logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Get port from environment variable or default to 8000
    port = int(os.getenv("PORT", 8000))
    
    # Bind to 0.0.0.0 to accept connections from all interfaces (required for production)
    host = os.getenv("HOST", "0.0.0.0")
    
    # Bind to all interfaces for production deployment
    # Disable reload to avoid Windows multiprocessing issues
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=False
    )
