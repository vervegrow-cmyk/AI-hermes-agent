from bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

import uvicorn

from api.app import app


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8086)
