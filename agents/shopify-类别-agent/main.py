import os

from bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

import uvicorn

from api.app import app


if __name__ == "__main__":
    port = int(os.getenv("AGENT_PORT", "8088"))
    uvicorn.run(app, host="0.0.0.0", port=port)
