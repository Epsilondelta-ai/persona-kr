# persona-kr 세션 안내문

다른 Claude Code 세션에서 이 스킬을 **쓰거나** **고칠** 때 보는 문서입니다.

## 1. 경로

| 구분 | 경로 | 용도 |
|---|---|---|
| 원본 저장소 (편집은 여기서) | `/run/media/epsilondelta/titanhdd/epsilonDelta/skills/persona-KR` | git 작업 사본, `origin` = https://github.com/Epsilondelta-ai/persona-kr |
| 설치본 (읽기 전용) | `~/.claude/plugins/cache/persona-kr/persona-kr/<버전>/` | Claude Code가 실제로 불러오는 사본. 직접 고치지 않는다 (업데이트 시 덮어써짐) |
| 마켓플레이스 사본 | `~/.claude/plugins/marketplaces/persona-kr/` | GitHub에서 받은 원본. 직접 고치지 않는다 |
| 데이터 캐시 (선택) | `~/.cache/nemotron-personas-ko/` | `download` 실행 시 생성(약 2GB). 없으면 Hugging Face 원격 질의. 환경변수 `NEMOTRON_KO_CACHE`로 위치 변경 가능 |

### 스킬과 에이전트 파일 (원본 저장소 기준)

```
.claude-plugin/plugin.json          플러그인 이름·버전 (persona-kr)
.claude-plugin/marketplace.json     마켓플레이스 정의 (source "./")
agents/virtual-customer.md          가상 고객 에이전트 (연기 지침 사본)
tools/sync_agent.py                 연기 지침 원본 → 에이전트 파일 동기화
docs/SESSION-GUIDE.md               이 문서
skills/korean-customer-persona/
  SKILL.md                          페르소나 추출 절차
  scripts/persona_sampler.py        DuckDB 샘플러 (count / sample / get / values / download)
  references/dataset-schema.md      컬럼·범주값·세그먼트 번역 예시
  references/persona-card-template.md
skills/lean-customer-interview/
  SKILL.md                          인터뷰 절차 (시뮬레이션 / 연습 / 스크립트 점검)
  references/virtual-customer-prompt.md   가상 고객 연기 지침 (원본)
  references/interview-scripts.md
  references/question-checklist.md
  references/synthesis-template.md
examples/dual-income-childcare/     전체 실행 예시
```

### 페르소나 파일 위치

- **예시 페르소나 카드**: `examples/dual-income-childcare/personas/` (5장: 이지영, 김유진, 김승일, 김병규, 김희정)
- **예시 후보 풀·경계 사례**: `examples/dual-income-childcare/pool.md`, `boundary.md`
- **새로 만드는 페르소나**: 스킬을 실행한 세션의 작업 폴더 기준 `personas/<프로젝트-슬러그>/<uuid앞8자>-<이름>.md`
- **새 인터뷰 기록**: 작업 폴더 기준 `interviews/<프로젝트-슬러그>/<YYYY-MM-DD>/`
- 다른 위치를 원하면 요청할 때 "페르소나는 ○○ 폴더에 저장해"라고 지정하면 된다.

## 2. 다른 세션에서 사용하기

설치된 상태라 어느 폴더에서 연 세션이든 바로 쓸 수 있습니다. 결과물은 그 세션의 작업 폴더에 저장됩니다.

| 하고 싶은 일 | 요청 예시 | 호출되는 것 |
|---|---|---|
| 세그먼트 규모 보기 | "서울 20대 후반 1인 가구 직장인이 몇 명인지, 지역 분포까지 보여 줘" | `persona-kr:korean-customer-persona` |
| 인터뷰 대상 만들기 | "중소도시 자영업자 페르소나 6명 뽑아서 카드 만들어 줘. 주제는 세무 처리" | `persona-kr:korean-customer-persona` |
| 가상 인터뷰 | "만든 카드로 문제 인터뷰 돌리고 종합해 줘" | `persona-kr:lean-customer-interview` + `persona-kr:virtual-customer` |
| 인터뷰 연습 | "내가 인터뷰어 할게. 이지영 카드로 연기하고 끝나면 코칭해 줘" | `persona-kr:lean-customer-interview` (모드 B) |
| 질문지 점검 | "이 인터뷰 질문지 점검해 줘: …" | `persona-kr:lean-customer-interview` (모드 C) |

스킬 이름을 직접 불러도 됩니다: `/persona-kr:korean-customer-persona`, `/persona-kr:lean-customer-interview`.

샘플러를 직접 실행할 때는 다음과 같이 합니다.

```bash
S=~/.claude/plugins/cache/persona-kr/persona-kr/0.1.0/skills/korean-customer-persona/scripts/persona_sampler.py
python3 $S count  --age 25-34 --family-like "혼자 거주" --by age_band,province
python3 $S sample --age 25-34 --keyword 배달,야근 --fields culinary_persona --n 6 --stratify sex --format md
python3 $S get <uuid> --format card --project <슬러그> --out personas/<슬러그>
```

키워드 검색을 자주 하면 캐시를 먼저 받아 둡니다 (약 2GB, 한 번만).

```bash
python3 ~/.claude/plugins/cache/persona-kr/persona-kr/0.1.0/skills/korean-customer-persona/scripts/persona_sampler.py download
```

### 예시 페르소나를 다른 세션에서 재사용

카드 파일 경로를 그대로 주면 됩니다.

> `/run/media/epsilondelta/titanhdd/epsilonDelta/skills/persona-KR/examples/dual-income-childcare/personas/` 카드 5장으로 솔루션 인터뷰를 해 줘. 솔루션은 "같은 반 부모끼리 하원 백업을 맡아 주는 앱"이야.

## 3. 다른 세션에서 편집하기

### 편집 세션 시작

원본 저장소 폴더에서 세션을 엽니다. 그 폴더의 `CLAUDE.md`가 편집 규칙을 자동으로 불러옵니다.

```bash
cd /run/media/epsilondelta/titanhdd/epsilonDelta/skills/persona-KR && claude
```

### 수정한 내용을 설치하기 전에 시험하기

설치본을 건드리지 않고, 원본 폴더를 이번 세션에만 플러그인으로 불러옵니다.

```bash
claude --plugin-dir /run/media/epsilondelta/titanhdd/epsilonDelta/skills/persona-KR
```

### 반영 순서

1. 원본 저장소에서 파일을 수정한다.
2. 검증한다.
   ```bash
   claude plugin validate /run/media/epsilondelta/titanhdd/epsilonDelta/skills/persona-KR
   ```
   ```bash
   python3 -m py_compile skills/korean-customer-persona/scripts/persona_sampler.py
   ```
3. `.claude-plugin/plugin.json`의 `version`을 올린다 (예: 0.1.0 → 0.1.1). 버전이 같으면 설치본이 갱신되지 않을 수 있다.
4. 커밋하고 푸시한다.
   ```bash
   git add -A && git commit -m "<변경 요약>" && git push
   ```
5. 설치본을 갱신한다.
   ```bash
   claude plugin marketplace update persona-kr
   ```
   ```bash
   claude plugin update persona-kr@persona-kr
   ```
6. 새 세션을 열어 바뀐 스킬이 로드됐는지 확인한다.

### 편집할 때 지킬 것

- **연기 지침은 두 곳에 있다.** `skills/lean-customer-interview/references/virtual-customer-prompt.md`가 원본이고, `agents/virtual-customer.md`는 그 본문에 에이전트 frontmatter를 붙인 사본이다. 원본을 고친 뒤 사본을 갱신한다.
  ```bash
  python3 tools/sync_agent.py
  ```
- **카드 형식을 바꾸면** 세 곳을 함께 고친다: `references/persona-card-template.md`, `persona_sampler.py`의 `card_file()`, 인터뷰 SKILL의 3단계(블라인드 사본에서 지우는 줄).
- **가설 비공개 원칙**: 가상 고객 에이전트에게 문제 가설·제품 아이디어·`segment_role`이 넘어가지 않게 한다.
- **샘플러는 DuckDB 버전 차이에 주의**: 2.0부터 relation의 `fetchone()`이 없어졌다. `con.execute(...).fetchall()`만 쓴다.
- **스킬 description**은 트리거 정확도를 좌우한다. 한국어 키워드와 영어 문구를 둘 다 유지한다.
- **데이터 출처 표기**(Nemotron-Personas-Korea, NVIDIA, CC BY 4.0)를 결과물과 예시에서 지우지 않는다.
