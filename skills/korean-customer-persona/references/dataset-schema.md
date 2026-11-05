# Nemotron-Personas-Korea 스키마

- 출처: https://huggingface.co/datasets/nvidia/Nemotron-Personas-Korea (NGC: nvidia/nemotron-personas/nemotron-personas-dataset-ko_kr)
- 라이선스: CC BY 4.0 · 버전 1.0 (2026-04-20) · 1,000,000 레코드 · 만 19세 이상
- 기반 통계: KOSIS, 대법원(이름), 국민건강보험공단, 한국농촌경제연구원, NAVER Cloud
- 파일: `data/train-0000{0..8}-of-00009.parquet` (총 약 2GB)

## 서술형 필드 (키워드 검색 대상)

| 필드 | 내용 | 인터뷰 활용 |
|---|---|---|
| `persona` | 한 문장 요약 | 카드 제목 |
| `professional_persona` | 일하는 방식, 직장 내 평판 | 업무 문제, B2B |
| `family_persona` | 가족 관계, 주거, 돌봄 | 육아, 돌봄, 가계 |
| `culinary_persona` | 식습관, 배달·외식 빈도 | F&B, 커머스 |
| `travel_persona` | 여행 스타일 | 여가, 모빌리티 |
| `sports_persona` | 운동, 건강 관리 | 헬스케어 웰니스 |
| `arts_persona` | 콘텐츠 소비, 취미 예술 | 미디어, 콘텐츠 |
| `cultural_background` | 지역 문화, 말투, 성장 배경 | 말투·어휘 연기 |
| `skills_and_expertise` (+`_list`) | 숙련, 노하우 | 전문가 페르소나 |
| `hobbies_and_interests` (+`_list`) | 취미 | 채널, 커뮤니티 |
| `career_goals_and_ambitions` | 목표, 걱정 | 동기, 전환 계기 |

## 인구통계 필드 (정확 일치 필터) — 1개 샤드(111,112건) 기준 분포

- `sex`: 여자, 남자
- `age`: 19~99 (정수)
- `province`: 경기, 서울, 부산, 경상남, 인천, 경상북, 대구, 충청남, 전라남, 전북, 충청북, 강원, 대전, 광주, 울산, 제주, 세종
- `district`: `시도-시군구` 형식. 예: `서울-마포구`, `경기-성남시 분당구` → `--district-like` 사용
- `marital_status`: 배우자있음, 미혼, 사별, 이혼
- `military_status`: 비현역, 현역
- `family_type` (주요값): 배우자·자녀와 거주, 배우자와 거주, 혼자 거주, 부모와 동거, 기타2세대, 어머니와 동거, 자녀와 거주 (한부모), 기타3세대, 혼자 거주 (배우자 별거), 자녀와 거주 (배우자 별거), 배우자·자녀·어머니와 거주, 친인척과 거주, 비친족 동거, 손자녀와 거주 등 약 40종 → `--family-like` 부분일치 권장
- `housing_type`: 아파트, 단독주택, 다세대주택, 주택 이외의 거처, 연립주택, 비주거용 건물 내 주택
- `education_level`: 무학, 초등학교, 중학교, 고등학교, 2~3년제 전문대학, 4년제 대학교, 대학원
- `bachelors_field`: 해당없음, 공학·제조·건설, 경영·행정·법, 예술·인문, 보건·복지, 교육, 정보통신기술, 서비스, 사회과학·언론, 자연과학·수학, 농림어업·수의학
- `occupation`: 1,600종 이상의 세부 직업명. 예: 일반 간호사, 웹 프로그래머, 보육교사, 무직, `전직 ○○, 현재 구직중` → `--occupation-like`와 `values occupation --like` 사용

## 세그먼트 번역 예시

| 가설 속 고객 | 필터 |
|---|---|
| 수도권 맞벌이 영유아 부모 | `--province 서울,경기,인천 --age 29-42 --family-like 자녀 --keyword 맞벌이,어린이집,하원 --exclude-occupation 무직` |
| 1인 가구 사회초년생 | `--age 24-32 --family-like "혼자 거주" --marital 미혼` |
| 지방 소도시 자영업자 | `--province 전라남,경상북,충청남 --occupation-like 판매,음식점,자영,소매` |
| 부모 돌봄 중인 50대 | `--age 50-64 --keyword 간병,요양,부모님 --fields family_persona,career_goals_and_ambitions` |
| 은퇴 전후 시니어 | `--age 58-70 --keyword 은퇴,퇴직 --fields career_goals_and_ambitions,persona` |
