<<<<<<< HEAD
from pathlib import Path
=======
﻿from pathlib import Path
>>>>>>> 7af5a402772857b0c388489419e38a01f18be89d
from .config import settings

def ensure_dirs() -> None:
    for p in [
        settings.CHROMA_DIR,
        settings.CHAT_MEMORY_DIR,
        settings.PROCESSED_CHUNKS_PATH,
        settings.RAW_NEWS_PATH.parent,
        settings.TICKERS_DIR,
        settings.CHAT_SESSIONS_FILE.parent,
    ]:
        Path(p).mkdir(parents=True, exist_ok=True)
