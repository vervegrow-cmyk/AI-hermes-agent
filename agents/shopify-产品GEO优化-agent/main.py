import os

import bootstrap
import uvicorn

from api.app import app


if __name__ == "__main__":
    bootstrap.load_shared_environment()
    port = int(os.getenv("AGENT_PORT", "8094"))
    uvicorn.run(app, host="0.0.0.0", port=port)
