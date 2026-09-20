"""Shared entrypoint. Leaf requests receive only their module dependency closure."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path("/cas/args/modules")))
import cas
stage=cas.text("stage")
module,function=cas.ENTRYPOINTS[stage]
import importlib
getattr(importlib.import_module(module),function)()
