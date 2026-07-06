import os

import uvicorn

from api.app import app


if __name__ == "__main__":
    port = int(os.getenv("AGENT_PORT", "8091"))
    uvicorn.run(app, host="0.0.0.0", port=port)

