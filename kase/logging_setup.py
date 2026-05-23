import logging
import os
from pathlib import Path
from kase.utils import get_kase_home


def setup_logging(name: str = "kase", level: int = logging.INFO) -> None:
    log_dir = get_kase_home() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    
    agent_log = logging.getLogger("kase")
    agent_log.setLevel(level)
    
    fh = logging.FileHandler(log_dir / f"{name}.log", encoding="utf-8")
    fh.setFormatter(fmt)
    agent_log.addHandler(fh)
    
    if os.getenv("KASE_VERBOSE"):
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        agent_log.addHandler(sh)
