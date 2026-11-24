"""Build the standalone, offline editor used by all platforms."""
from pathlib import Path
import re

root = Path(__file__).resolve().parent
source = root / "src"
template = (source / "editor.template.html").read_text(encoding="utf-8")
output = re.sub(r"/\* @include ([\w.-]+) \*/", lambda m: (source / m[1]).read_text(encoding="utf-8"), template)
(root / "Karta-2.1.html").write_bytes(output.encode("utf-8"))
