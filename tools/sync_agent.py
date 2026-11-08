#!/usr/bin/env python3
"""연기 지침 원본(virtual-customer-prompt.md)을 agents/virtual-customer.md에 반영한다.

agents/virtual-customer.md의 frontmatter는 유지하고, 본문만 원본 파일의 첫 '---' 줄 아래 내용으로 바꾼다.
저장소 루트에서 실행: python3 tools/sync_agent.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "skills/lean-customer-interview/references/virtual-customer-prompt.md"
DST = ROOT / "agents/virtual-customer.md"

dst = DST.read_text(encoding="utf-8")
_, front, _ = dst.split("---\n", 2)
src_lines = SRC.read_text(encoding="utf-8").splitlines(keepends=True)
body = "".join(src_lines[src_lines.index("---\n") + 1:])
DST.write_text(f"---\n{front}---\n\n{body}", encoding="utf-8")
print(f"updated {DST.relative_to(ROOT)}")
