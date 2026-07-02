#!/usr/bin/env python3
from __future__ import annotations

import os

os.environ["WORKFLOW_HOOK_CLIENT"] = "cursor"

from codex_enforce_hook import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
