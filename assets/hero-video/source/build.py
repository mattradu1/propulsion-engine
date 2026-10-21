#!/usr/bin/env python3
"""Generate the Propulsion hero composition for desktop (1920x1080) and mobile (1080x1350).
Same scenes and timeline; the mobile variant only changes layout CSS (stacked split)."""
import pathlib, shutil, sys

ROOT = pathlib.Path(__file__).parent
SRC = ROOT / "hf"

DESKTOP_CSS = """
.s1 .wrap{flex-direction:row;gap:140px}
.s1 .copy{width:640px}
.split{flex-direction:row;gap:120px}
.side{width:560px}
.phone{width:380px;height:760px}
.tiltL{transform:rotateY(16deg) rotateX(4deg)}
.tiltR{transform:rotateY(-16deg) rotateX(4deg)}
.h1{font-size:84px}
.cap{font-size:30px}
.end .mark{font-size:150px}
.end .line{font-size:46px}
.desk{width:980px;height:520px}
"""
MOBILE_CSS = """
.s1 .wrap{flex-direction:column;gap:60px}
.s1 .copy{width:900px;text-align:center}
.split{flex-direction:column;gap:30px}
.side{width:1000px;flex-direction:row !important;gap:40px;justify-content:center}
.side .lab{order:-1}
.phone{width:300px;height:560px}
.tiltL{transform:rotateX(10deg) rotateY(10deg)}
.tiltR{transform:rotateX(10deg) rotateY(-10deg)}
.h1{font-size:78px}
.cap{font-size:30px;width:420px;text-align:left}
.side .meta{display:flex;flex-direction:column;gap:14px;align-items:flex-start}
.end .mark{font-size:120px}
.end .line{font-size:44px;width:900px}
.desk{width:860px;height:560px}
.s1 .phone{width:340px;height:660px}
"""

TEMPLATE = (ROOT / "template.html").read_text()

def build(name, w, h, css):
    out = ROOT / name
    if name != "hf":
        if out.exists():
            shutil.rmtree(out)
        shutil.copytree(SRC, out, ignore=shutil.ignore_patterns("index.html", "renders", ".hyperframes", "node_modules"))
    html = TEMPLATE.replace("__W__", str(w)).replace("__H__", str(h)).replace("/*__LAYOUT__*/", css)
    (out / "index.html").write_text(html)
    print("wrote", out / "index.html")

build("hf", 1920, 1080, DESKTOP_CSS)
build("hf-mobile", 1080, 1350, MOBILE_CSS)
