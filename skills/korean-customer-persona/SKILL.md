---
name: korean-customer-persona
description: "NVIDIA Nemotron-Personas-Korea(100만 명, 실제 한국 인구통계 분포 기반 합성 페르소나)에서 린 스타트업 고객 세그먼트에 맞는 가상 고객 페르소나를 찾아 세그먼트 규모를 세고, 가상 고객 인터뷰에 바로 쓸 수 있는 페르소나 카드를 만든다. Use when the user wants Korean customer personas, a target-segment persona from real Korean demographics, segment sizing from Nemotron-Personas-Korea, early-adopter candidates for customer discovery, or persona cards for virtual/synthetic customer interviews. Keywords: 고객 페르소나, 가상 고객, 타깃 고객, 고객 세그먼트, 얼리어답터, 선각 수용자, 페르소나 카드, 시장 규모, Nemotron-Personas-Korea, synthetic persona, customer segment."
---

# 한국 고객 페르소나 (Nemotron-Personas-Korea)

## 목적

고객 세그먼트 가설을 Nemotron-Personas-Korea의 실제 분포 기반 페르소나로 구체화한다. 결과물은 세 가지다.

1. **세그먼트 리포트**: 조건, 매칭 수, 성인 인구 대비 비중, 연령·지역 분포
2. **페르소나 카드**: 데이터셋 원문 필드와, 인터뷰 주제에 맞춘 추론 확장을 구분해 담은 카드 (`references/persona-card-template.md`)
3. **인터뷰 대상 구성**: 얼리어답터 후보, 주류 고객, 경계 사례(대조군)로 나눈 명단. `lean-customer-interview` 스킬이 이 명단을 그대로 받아 쓴다.

## 데이터 접근

- 스크립트: `scripts/persona_sampler.py` (의존성은 `pip install duckdb` 하나)
- 기본은 Hugging Face parquet 원격 질의라서 다운로드나 인증이 필요 없다. 소요 시간은 인구통계 조건만 쓸 때 약 10~25초, 서술형 키워드 검색을 넣으면 약 1~1.5분이다.
- 키워드 검색을 반복할 때는 `python3 scripts/persona_sampler.py download`로 약 2GB를 한 번 받아 두면 `~/.cache/nemotron-personas-ko`를 자동으로 쓰고, 수 초 안에 끝난다.
- 스키마와 범주값: `references/dataset-schema.md`. 정확한 값이 필요하면 `values <컬럼> --like <부분문자열>`로 확인한다.

```bash
S=skills/korean-customer-persona/scripts/persona_sampler.py   # 설치 위치 기준으로 조정
python3 $S count  --age 30-44 --family-like 자녀 --by age_band,province
python3 $S sample --age 30-44 --family-like 자녀 --keyword 맞벌이,어린이집 \
                  --n 8 --stratify age_band,sex --per-stratum 2 --format md --out personas/pool.md
python3 $S sample ... --format card --project <슬러그> --out personas/<슬러그>   # 1인 1파일 카드 뼈대
python3 $S get <uuid> --format json
python3 $S values occupation --like 간호
```

## 절차

### 1단계. 가설과 맥락 받기

없으면 묻는다. 둘 이상 비어 있으면 한 번에 묶어서 질문한다.

| 입력 | 질문 |
|---|---|
| 아이디어·결정 | "이 페르소나로 어떤 제품·기능·사업 결정을 내리려고 하나요?" |
| 문제 가설 | "[어떤 사람]이 [어떤 일]을 할 때 [어떤 문제]를 겪는다고 보나요?" |
| 전환 계기·기존 대안 | "그 사람들은 지금 무엇으로 해결하나요? 무엇이 계기가 되면 대안을 찾아 나서나요?" |
| 필요 인원 | 기본값: 인터뷰 대상 5~8명 + 경계 사례 1~2명 |

### 2단계. 세그먼트를 필터로 번역

- **경성 조건**(인구통계 컬럼)은 문제가 성립하기 위한 최소 조건에만 쓴다. 예: 육아 문제라면 `--family-like 자녀`, 자영업 문제라면 `--occupation-like`.
- **행동·상황 단서**는 `--keyword`로 서술형 필드에서 찾는다. 얼리어답터는 인구통계보다 *전환 계기와 현재 행동*으로 정의하므로, 키워드는 기존 대안이나 상황을 가리키는 말로 고른다(예: `배달 앱`, `밀키트`, `가계부`, `중고거래`, `야근`, `맞벌이`, `간병`). 관련 필드만 `--fields`로 좁히면 더 빠르고 정확하다(예: 식생활 문제는 `--fields culinary_persona,family_persona`).
- 범주값은 정확히 일치해야 한다(예: 시도는 `경상남`, `전북`). 모호하면 먼저 `values`로 확인한다.
- 데이터셋에 **없는** 항목은 소득, 자산, 구매 이력, 디지털 숙련도, 성격 특성, 금융·의료 관련 페르소나다. 이런 조건은 필터로 걸지 말고, 6단계 카드에서 [추론]으로 표시한다.

### 3단계. 세그먼트 규모 확인

`count --by age_band,province`(또는 `occupation`, `sex`)를 실행해 다음을 보고한다.

- 매칭 수와 성인(만 19세 이상) 대비 비중. 데이터셋이 성인 인구 분포를 따르므로, 비중에 최신 KOSIS 성인 인구를 곱하면 TAM 수준의 대략적 추정치가 된다. 이 값은 "추정"으로 표기한다.
- 키워드 조건이 들어간 수치는 서술 텍스트에 그 단어가 나온 사람만 센 것이다. 실제 행동 인구의 **하한 근사**로만 해석한다.
- 매칭이 30명 미만이면 조건이 지나치게 좁다. 매칭이 성인의 20%를 넘으면 세그먼트가 아니라 인구 전체에 가깝다. 어느 쪽이든 사용자에게 조정안을 제시한다.

### 4단계. 후보 풀 추출

- 필요 인원의 2~3배를 뽑는다: `sample --n <2~3배> --stratify age_band,sex --per-stratum 2`.
- `--seed`를 기록해 두면 같은 풀을 다시 만들 수 있다.
- 경계 사례 1~2명은 조건 하나를 뒤집어 따로 뽑는다(예: 자녀 없음, 다른 지역, 키워드 제외 `--exclude-keyword`). "다른 사람들은 어떻게 하는가"로 패턴을 반증하는 데 쓴다.

### 5단계. 스크리닝

후보마다 원문만 근거로 다음 세 가지를 판정하고 표로 보여 준다.

| 항목 | 판정 기준 |
|---|---|
| 문제 상황 노출 | 서술에 문제 상황이 실제로 나오는가 (직접 / 간접 / 없음) |
| 기존 대안 단서 | 지금 쓰는 방법·도구·편법이 나오는가 |
| 전환 계기 가능성 | 최근 생활 변화(이직, 출산, 이사, 은퇴, 창업 등)가 보이는가 |

이 판정으로 **얼리어답터 후보**(세 항목 모두 직접), **주류**, **경계 사례**로 분류해 인터뷰 대상을 확정한다. 원문 근거 없이 점수를 올리지 않는다.

### 6단계. 페르소나 카드 작성

`references/persona-card-template.md` 형식으로 1인 1파일을 만든다. 확정한 인원의 uuid로 `get <uuid...> --format card --project <슬러그> --out personas/<슬러그>`를 실행하면 A 섹션이 채워진 뼈대가 `personas/<슬러그>/<uuid앞8자>-<이름>.md`로 생성된다. B·C의 `TODO`를 채우고 `segment_role`을 정한다.

- **A. 데이터셋 사실**: 원문 필드를 그대로 옮기고 고치지 않는다.
- **B. 인터뷰 확장 [추론]**: 인터뷰 주제와 관련된 하루 일과, 현재 쓰는 방법과 앱, 지출 감각, 말투, 낯선 인터뷰어를 대하는 태도를 A와 모순되지 않게 추론한다. 모든 항목에 `[추론]`을 붙이고 근거가 된 A 필드를 괄호로 단다.
- **C. 인터뷰 연기 가이드**: 말투(연령·지역·학력에 맞는 어휘, 사투리 정도), 말 길이, 신뢰를 얻기 전의 경계 수준, 이 사람이 *모르는* 것.
- **문제 가설은 카드에 쓰지 않는다.** 가상 고객이 가설을 알면 맞장구치는 답을 만들어 내기 때문이다.

### 7단계. 산출물 보고

다음을 한 번에 전달한다.
- 세그먼트 리포트(조건, 수치, 분포 상위 5개, 시드)
- 인터뷰 대상 표(이름, 나이, 지역, 직업, 분류, 선정 근거 한 줄, 카드 경로)
- 다음 단계: `lean-customer-interview`로 가상 인터뷰 진행

## 사용상 주의

- 데이터셋 페르소나는 통계 분포를 따른 **합성 인물**이다. 가상 인터뷰로 얻는 것은 질문 리허설과 가설 후보, 실제 인터뷰 대상자 모집 기준이고, 문제 검증 자체는 실제 고객 인터뷰에서 해야 한다.
- 서술형 텍스트는 LLM이 생성한 것이라 고정관념이 섞여 있다. 예를 들어 "맞벌이·어린이집·하원" 키워드에 걸린 수도권 30~40대의 93%가 여성이다. 같은 상황의 아빠는 서술에 육아가 덜 나온다. 키워드 결과의 성별·연령 쏠림은 실제 분포로 읽지 말고, `--stratify sex`로 반대쪽 표본을 따로 확보한다.
- 직업 배정 시 성별·전공 등의 교호작용이 반영되지 않았다(데이터셋 문서 명시). 특정 직업과 성별 조합의 대표성은 과신하지 않는다.
- 출처 표기: 결과물을 공유할 때 "Nemotron-Personas-Korea (NVIDIA, CC BY 4.0)"를 함께 적는다.
