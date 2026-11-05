# persona-kr

**한국 고객 페르소나 + 린 스타트업 가상 고객 인터뷰 스킬**

NVIDIA [Nemotron-Personas-Korea](https://huggingface.co/datasets/nvidia/Nemotron-Personas-Korea)(실제 한국 인구통계 분포를 따르는 합성 페르소나 100만 명, CC BY 4.0)에서 고객 세그먼트에 맞는 사람을 뽑습니다. 뽑은 사람을 가설을 모르는 가상 고객 에이전트로 띄워 문제 인터뷰를 리허설하고, 실제 고객 인터뷰 계획까지 만듭니다. Claude Code용 스킬과 에이전트로 구성되어 있습니다.

```
고객 세그먼트 가설
   │  korean-customer-persona
   ├─ 세그먼트 규모 집계 (100만 명 중 몇 명, 연령·지역 분포)
   ├─ 층화 표본 추출 → 스크리닝 (얼리어답터 후보 / 주류 / 경계 사례)
   └─ 페르소나 카드 (A 데이터셋 원문 · B 인터뷰용 추론 · C 연기 가이드)
   │  lean-customer-interview
   ├─ 질문 점검표로 스크립트 정리 (과거 행동, 특정 사건, 비유도)
   ├─ 페르소나마다 virtual-customer 에이전트 1명 (가설 비공개), 라운드제 인터뷰
   ├─ 인터뷰별 Validates / Invalidates / Also Interesting / 고객 작용력
   └─ 종합 → 가설 수정안 + 실제 인터뷰 모집 기준·스크리너·종료 기준
```

## 구성

| 구성 요소 | 역할 |
|---|---|
| `skills/korean-customer-persona` | 세그먼트를 필터로 번역하고 규모를 센 뒤, 표본 추출과 스크리닝을 거쳐 페르소나 카드를 만든다. `scripts/persona_sampler.py` 포함 |
| `skills/lean-customer-interview` | 시뮬레이션(Claude가 인터뷰어), 연습(사용자가 인터뷰어 + 코칭), 스크립트 점검의 세 가지 모드 |
| `agents/virtual-customer.md` | 페르소나 카드 한 장을 연기하는 서브에이전트. 아첨 방지와 현실성 규칙을 담고 있다 |
| `examples/dual-income-childcare` | 전체 실행 예시: 수도권 맞벌이 가정의 평일 하원~저녁 문제 인터뷰 5건 |

## 설치

### Claude Code 플러그인

```bash
claude plugin marketplace add Epsilondelta-ai/persona-kr
```

```bash
claude plugin install persona-kr@persona-kr
```

Claude Code 안에서 `/plugin marketplace add Epsilondelta-ai/persona-kr`로 추가해도 됩니다.

### 스킬만 복사

```bash
git clone https://github.com/Epsilondelta-ai/persona-kr.git
```

```bash
cp -r persona-kr/skills/* ~/.claude/skills/ && cp persona-kr/agents/* ~/.claude/agents/
```

### 의존성

```bash
pip install duckdb
```

데이터는 Hugging Face의 parquet을 DuckDB로 원격 질의합니다. 계정, API 키, 사전 다운로드가 필요 없습니다.

| 작업 | 원격 질의 | 로컬 캐시 |
|---|---|---|
| 인구통계 조건 집계 | 약 10초 | 수 초 |
| 인구통계 조건 표본 | 약 20초 | 수 초 |
| 서술형 키워드 검색 (전체 필드) | 약 1~1.5분 | 수 초 |

키워드 검색을 자주 하면 한 번만 받아 두세요(약 2GB, `~/.cache/nemotron-personas-ko`).

```bash
python3 skills/korean-customer-persona/scripts/persona_sampler.py download
```

## 사용 예

Claude Code에서 자연어로 요청하면 됩니다.

> 수도권 맞벌이 부모가 아이 하원 시간을 못 맞추는 문제를 검증하고 싶어. 페르소나 5명 뽑아서 가상 문제 인터뷰 돌려 줘.

> 이 인터뷰 질문지 점검해 줘. (질문지 붙여넣기)

> 내가 인터뷰어 할게. 30대 1인 가구 직장인 페르소나 하나 골라서 연기해 줘. 끝나면 질문 코칭해 줘.

샘플러를 직접 쓸 수도 있습니다.

```bash
S=skills/korean-customer-persona/scripts/persona_sampler.py
python3 $S count  --province 서울,경기,인천 --age 29-44 --family-like 자녀 --by age_band,sex
python3 $S sample --age 24-32 --family-like "혼자 거주" --keyword 배달,야근 \
                  --fields culinary_persona,professional_persona --n 6 --stratify sex --format md
python3 $S get 9c619348ae364fc3b5a3269acea0f0ca --format card --project my-idea --out personas/my-idea
python3 $S values occupation --like 간호
```

## 예시 결과에서 보이는 것

`examples/dual-income-childcare/interviews/99-synthesis.md`에서 가설은 "공백이 생길 때 사람을 급히 구하지 못한다"였습니다. 가상 인터뷰 5건에서는 다른 패턴이 나왔습니다. 5명 모두 돌봄 앱이나 정부 서비스를 알고 있었지만 "모르는 사람"이라서 쓰지 않았습니다. 돈을 낸 유일한 사례는 지인 소개로 신뢰가 확보된 경우였습니다. 그래서 수정된 가설은 "이미 신뢰가 확인된 백업이 없다"이고, 실제 인터뷰에서 이 가설과 모델 공통 편향 여부를 먼저 확인하도록 계획이 짜여 있습니다.

## 쓰임새와 한계

- 가상 인터뷰는 **실제 인터뷰 전 리허설**입니다. 질문을 다듬고, 가설 후보와 모집 기준을 얻는 데 씁니다. 문제를 검증했다는 판정은 실제 고객의 행동 증거로 내립니다.
- 데이터셋에는 소득·지출·서비스 이용 이력·성격 특성이 없습니다. 카드의 B 섹션은 추론이며 `[추론]`으로 표시됩니다.
- 서술형 필드는 LLM이 생성한 텍스트라 고정관념이 섞여 있습니다. 예를 들어 육아 키워드에 걸린 수도권 30~40대의 93%가 여성입니다. 그래서 스킬이 성별 층화로 반대쪽 표본을 확보하도록 안내합니다.
- 방법론 배경: Steve Blank의 고객 개발, Cindy Alvarez의 *Lean Customer Development*, Ash Maurya의 *Running Lean*, Rob Fitzpatrick의 *The Mom Test*.

## 라이선스

- 코드와 스킬 문서: MIT (`LICENSE`)
- 페르소나 데이터: Nemotron-Personas-Korea, NVIDIA Corporation, CC BY 4.0. 이 저장소는 데이터셋을 재배포하지 않고 질의만 합니다. `examples/`에 인용된 페르소나 원문의 출처 표기는 `NOTICE`에 있습니다.

---

**English summary.** Claude Code skills that turn NVIDIA's Nemotron-Personas-Korea (1M synthetic Korean personas grounded in official statistics, CC BY 4.0) into lean-startup customer personas and blind virtual customer interviews. `korean-customer-persona` sizes a segment and samples and screens personas into interview-ready cards via a DuckDB sampler that queries Hugging Face parquet remotely. `lean-customer-interview` runs round-based problem/solution interviews with one hypothesis-blind `virtual-customer` agent per persona, then synthesizes Validates/Invalidates/Forces and produces a plan for real interviews. A practice mode lets you play the interviewer and get coaching.
