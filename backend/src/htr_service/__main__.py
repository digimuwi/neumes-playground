"""Entry point for running the HTR service."""

import logging
import os
import uvicorn


def main():
    """Run the HTR service."""
    host = os.getenv("HTR_HOST", "0.0.0.0")
    port = int(os.getenv("HTR_PORT", "8000"))
    reload = os.getenv("HTR_RELOAD", "true").lower() in {"1", "true", "yes", "on"}

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    uvicorn.run(
        "htr_service.api:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    main()
