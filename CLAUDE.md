# persona-kr 편집 규칙

이 저장소는 Claude Code 플러그인 `persona-kr`의 원본이다. 경로, 사용법, 반영 절차는 `docs/SESSION-GUIDE.md`를 따른다.

- 설치본(`~/.claude/plugins/cache/persona-kr/...`)이나 마켓플레이스 사본은 고치지 않는다. 이 폴더에서 고친다.
- `skills/lean-customer-interview/references/virtual-customer-prompt.md`를 고쳤으면 `python3 tools/sync_agent.py`를 실행한다.
- 카드 형식을 바꾸면 `persona-card-template.md`, `persona_sampler.py`의 `card_file()`, 인터뷰 SKILL 3단계를 함께 고친다.
- 가상 고객 에이전트에게 문제 가설, 제품 아이디어, `segment_role`을 넘기지 않는다.
- 반영 전에 `claude plugin validate .`와 `python3 -m py_compile skills/korean-customer-persona/scripts/persona_sampler.py`를 실행하고, `.claude-plugin/plugin.json`의 `version`을 올린다.
- 데이터 출처 표기(Nemotron-Personas-Korea, NVIDIA, CC BY 4.0)를 유지한다.
