#!/usr/bin/env python3
"""Nemotron-Personas-Korea 샘플러.

NVIDIA Nemotron-Personas-Korea(CC BY 4.0, 100만 건)에서 린 스타트업 고객 세그먼트
조건에 맞는 페르소나를 찾고, 세그먼트 규모를 세고, 가상 인터뷰용 페르소나 카드를 만든다.

기본 동작은 Hugging Face의 parquet을 DuckDB로 원격 질의한다(필요한 컬럼만 읽음).
반복 사용 시 `download`로 로컬 캐시(약 2GB)를 받아두면 수 초 안에 끝난다.

사용 예:
  python3 persona_sampler.py count  --age 30-44 --family-like 자녀 --province 서울,경기
  python3 persona_sampler.py sample --age 30-44 --family-like 자녀 \
      --keyword 어린이집,맞벌이 --n 6 --stratify age_band,sex --format md
  python3 persona_sampler.py get 03b4f36a18e6469386d0286dddd513c8
  python3 persona_sampler.py values occupation --like 개발
  python3 persona_sampler.py download
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

REPO = "nvidia/Nemotron-Personas-Korea"
N_SHARDS = 9
REMOTE_GLOB = f"hf://datasets/{REPO}/data/*.parquet"
SHARD_URL = "https://huggingface.co/datasets/" + REPO + "/resolve/main/data/train-{i:05d}-of-{n:05d}.parquet"
DEFAULT_CACHE = Path(os.environ.get("NEMOTRON_KO_CACHE", Path.home() / ".cache" / "nemotron-personas-ko"))
TOTAL_ROWS = 1_000_000

TEXT_FIELDS = [
    "persona", "professional_persona", "family_persona", "culinary_persona",
    "travel_persona", "sports_persona", "arts_persona", "cultural_background",
    "skills_and_expertise", "hobbies_and_interests", "career_goals_and_ambitions",
]
LIST_FIELDS = ["skills_and_expertise_list", "hobbies_and_interests_list"]
DEMO_FIELDS = [
    "uuid", "sex", "age", "marital_status", "military_status", "family_type",
    "housing_type", "education_level", "bachelors_field", "occupation",
    "district", "province",
]
AGE_BAND = "CASE WHEN age < 30 THEN '19-29' WHEN age < 40 THEN '30대' WHEN age < 50 THEN '40대' " \
           "WHEN age < 60 THEN '50대' WHEN age < 70 THEN '60대' ELSE '70+' END"


def die(msg: str, code: int = 2) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def connect():
    try:
        import duckdb  # noqa: WPS433
    except ImportError:
        die("duckdb가 필요합니다: pip install duckdb  (또는 uv pip install duckdb)")
    con = duckdb.connect()
    con.execute("SET enable_progress_bar=false")
    return con


def source(args) -> str:
    local = Path(args.data_dir) if args.data_dir else DEFAULT_CACHE
    files = sorted(local.glob("*.parquet")) if local.exists() else []
    if len(files) == N_SHARDS and not args.remote:
        return f"read_parquet('{local.as_posix()}/*.parquet', filename=true, file_row_number=true)"
    if args.data_dir and not files:
        die(f"{local}에 parquet 파일이 없습니다")
    return f"read_parquet('{REMOTE_GLOB}', filename=true, file_row_number=true)"


def q(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def csv(v: str | None) -> list[str]:
    return [x.strip() for x in v.split(",") if x.strip()] if v else []


def build_where(args) -> str:
    w: list[str] = []
    if args.age:
        lo, _, hi = args.age.partition("-")
        w.append(f"age BETWEEN {int(lo)} AND {int(hi or lo)}")
    if args.sex:
        w.append(f"sex = {q(args.sex)}")
    for col, val in [("province", args.province), ("marital_status", args.marital),
                     ("education_level", args.education), ("housing_type", args.housing),
                     ("bachelors_field", args.major)]:
        vals = csv(val)
        if vals:
            w.append(f"{col} IN ({', '.join(q(v) for v in vals)})")
    for col, val in [("district", args.district_like), ("occupation", args.occupation_like),
                     ("family_type", args.family_like)]:
        vals = csv(val)
        if vals:
            w.append("(" + " OR ".join(f"{col} LIKE {q('%' + v + '%')}" for v in vals) + ")")
    for col, val in [("occupation", args.exclude_occupation)]:
        for v in csv(val):
            w.append(f"{col} NOT LIKE {q('%' + v + '%')}")

    fields = csv(args.fields) or TEXT_FIELDS
    bad = [f for f in fields if f not in TEXT_FIELDS + LIST_FIELDS]
    if bad:
        die(f"알 수 없는 텍스트 필드: {bad}")
    blob = "concat_ws(' ', " + ", ".join(fields) + ")"
    kws = csv(args.keyword)
    if kws:
        joiner = " AND " if args.all_keywords else " OR "
        w.append("(" + joiner.join(f"{blob} LIKE {q('%' + k + '%')}" for k in kws) + ")")
    for k in csv(args.exclude_keyword):
        w.append(f"{blob} NOT LIKE {q('%' + k + '%')}")
    return " AND ".join(w) if w else "TRUE"


def cmd_count(con, args) -> None:
    src, where = source(args), build_where(args)
    n = con.execute(f"SELECT count(*) FROM {src} WHERE {where}").fetchall()[0][0]
    out = {"matches": n, "share_of_adults_pct": round(100 * n / TOTAL_ROWS, 3), "where": where}
    if args.by:
        cols = csv(args.by)
        expr = [AGE_BAND + " AS age_band" if c == "age_band" else c for c in cols]
        rows = con.execute(
            f"SELECT {', '.join(expr)}, count(*) n FROM {src} WHERE {where} "
            f"GROUP BY ALL ORDER BY n DESC LIMIT {args.top}").fetchall()
        out["breakdown"] = [dict(zip(cols + ["n"], r)) for r in rows]
    print(json.dumps(out, ensure_ascii=False, indent=2))


def fetch(con, sql: str) -> list[dict]:
    cur = con.execute(sql)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def cmd_sample(con, args) -> None:
    src, where = source(args), build_where(args)
    order = f"hash(uuid || {q(str(args.seed))})"
    # 1단계: uuid만 골라 정렬·층화한다(서술형 컬럼은 필터에만 쓰여 전송량이 작다).
    if args.stratify:
        keys = [AGE_BAND if s == "age_band" else s for s in csv(args.stratify)]
        part = ", ".join(keys)
        sql = (f"SELECT uuid, filename, file_row_number FROM {src} WHERE {where} "
               f"QUALIFY row_number() OVER (PARTITION BY {part} ORDER BY {order}) <= "
               f"{args.per_stratum} ORDER BY {order} LIMIT {args.n}")
    else:
        sql = f"SELECT uuid, filename, file_row_number FROM {src} WHERE {where} ORDER BY {order} LIMIT {args.n}"
    hits = con.execute(sql).fetchall()
    if not hits:
        die("조건에 맞는 페르소나가 없습니다. 조건을 완화하세요.", 1)
    emit(fetch_rows(con, hits), args)


def fetch_rows(con, hits: list[tuple]) -> list[dict]:
    """2단계: (uuid, 파일, 행번호)로 해당 row group만 읽어 전체 필드를 가져온다."""
    cols = ", ".join(DEMO_FIELDS + TEXT_FIELDS + LIST_FIELDS)
    by_file: dict[str, list[int]] = {}
    for _, f, n in hits:
        by_file.setdefault(f, []).append(n)
    rows: dict[str, dict] = {}
    for f, nums in by_file.items():
        for r in fetch(con, f"SELECT {cols} FROM read_parquet({q(f)}, file_row_number=true) "
                            f"WHERE file_row_number IN ({', '.join(map(str, nums))})"):
            rows[r["uuid"]] = r
    return [rows[u] for u, _, _ in hits if u in rows]


def cmd_get(con, args) -> None:
    ids = ", ".join(q(u) for u in args.uuid)
    hits = con.execute(f"SELECT uuid, filename, file_row_number FROM {source(args)} WHERE uuid IN ({ids})").fetchall()
    rows = fetch_rows(con, hits)
    if not rows:
        die("해당 uuid를 찾지 못했습니다", 1)
    emit(rows, args)


def cmd_values(con, args) -> None:
    src = source(args)
    col = args.column
    if col not in DEMO_FIELDS or col == "uuid":
        die(f"값 목록은 인구통계 컬럼만 지원합니다: {DEMO_FIELDS[1:]}")
    where = f"WHERE {col} LIKE {q('%' + args.like + '%')}" if args.like else ""
    rows = con.execute(f"SELECT {col}, count(*) n FROM {src} {where} GROUP BY 1 ORDER BY 2 DESC LIMIT {args.top}").fetchall()
    for v, n in rows:
        print(f"{n:>8}  {v}")


def cmd_download(args) -> None:
    dest = Path(args.data_dir) if args.data_dir else DEFAULT_CACHE
    dest.mkdir(parents=True, exist_ok=True)
    for i in range(N_SHARDS):
        url = SHARD_URL.format(i=i, n=N_SHARDS)
        path = dest / Path(url).name
        if path.exists() and path.stat().st_size > 0:
            print(f"skip {path.name}")
            continue
        print(f"download {path.name} ...", flush=True)
        tmp = path.with_suffix(".part")
        urllib.request.urlretrieve(url, tmp)
        tmp.rename(path)
    print(f"done: {dest}")


def card_md(r: dict) -> str:
    lst = as_list
    return f"""### {persona_name(r)} · {r['age']}세 {r['sex']} · {r['district']}
- uuid: `{r['uuid']}`
- 직업: {r['occupation']} | 학력: {r['education_level']} ({r['bachelors_field']})
- 가구: {r['family_type']} | 혼인: {r['marital_status']} | 주거: {r['housing_type']}
- 요약: {r['persona']}
- 일: {r['professional_persona']}
- 가족: {r['family_persona']}
- 식생활: {r['culinary_persona']}
- 여가·운동: {r['sports_persona']} {r['arts_persona']}
- 여행: {r['travel_persona']}
- 문화적 배경: {r['cultural_background']}
- 역량: {lst(r['skills_and_expertise_list'])}
- 관심사: {lst(r['hobbies_and_interests_list'])}
- 목표: {r['career_goals_and_ambitions']}
"""


def persona_name(r: dict) -> str:
    return (r.get("persona") or "").split(" ")[0] or r["uuid"][:8]


def as_list(v: str | None) -> str:
    if v and v.startswith("["):
        try:
            return ", ".join(json.loads(v.replace("'", '"')))
        except json.JSONDecodeError:
            pass
    return v or ""


def card_file(r: dict, project: str) -> str:
    """references/persona-card-template.md 형식의 카드 뼈대. A는 원문, B·C는 작성용 빈칸."""
    return f"""---
uuid: {r['uuid']}
source: Nemotron-Personas-Korea (NVIDIA, CC BY 4.0)
project: {project}
segment_role: TODO 얼리어답터 후보 | 주류 | 경계 사례
---

# {persona_name(r)} ({r['age']}세, {r['sex']}, {r['district']})

## A. 데이터셋 사실 (원문, 수정 금지)
- 직업: {r['occupation']} / 학력: {r['education_level']} ({r['bachelors_field']})
- 혼인: {r['marital_status']} / 가구: {r['family_type']} / 주거: {r['housing_type']}
- 요약: {r['persona']}
- 일: {r['professional_persona']}
- 가족: {r['family_persona']}
- 식생활: {r['culinary_persona']}
- 운동: {r['sports_persona']}
- 문화·예술: {r['arts_persona']}
- 여행: {r['travel_persona']}
- 문화적 배경: {r['cultural_background']}
- 역량: {as_list(r['skills_and_expertise_list'])}
- 관심사: {as_list(r['hobbies_and_interests_list'])}
- 목표: {r['career_goals_and_ambitions']}

## B. 인터뷰 확장 [추론]
- 평일 하루 흐름: TODO
- 이 영역에서 지금 하는 방법·쓰는 앱·편법: TODO
- 최근 6개월의 관련 사건: TODO
- 돈과 시간 감각: TODO
- 정보 얻는 경로: TODO
- 새 서비스에 대한 태도: TODO

## C. 연기 가이드
- 말투: TODO
- 답변 길이: TODO
- 처음 경계 수준: TODO
- 이 사람이 모르는 것: TODO
- 민감한 지점: TODO
"""


def emit(rows: list[dict], args) -> None:
    if args.format == "card":
        out = Path(args.out or "personas")
        out.mkdir(parents=True, exist_ok=True)
        for r in rows:
            path = out / f"{r['uuid'][:8]}-{persona_name(r)}.md"
            path.write_text(card_file(r, args.project), encoding="utf-8")
            print(path)
        return
    if args.format == "md":
        text = "\n".join(card_md(r) for r in rows)
    elif args.format == "jsonl":
        text = "\n".join(json.dumps(r, ensure_ascii=False) for r in rows)
    else:
        text = json.dumps(rows, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        print(f"{len(rows)}명 저장: {args.out}")
    else:
        print(text)


def add_filters(p: argparse.ArgumentParser) -> None:
    g = p.add_argument_group("세그먼트 필터 (쉼표로 여러 값)")
    g.add_argument("--age", help="나이 범위, 예: 30-44 또는 35")
    g.add_argument("--sex", choices=["남자", "여자"])
    g.add_argument("--province", help="시도 정확값, 예: 서울,경기,경상남")
    g.add_argument("--district-like", help="시군구 부분일치, 예: 강남구,분당구")
    g.add_argument("--occupation-like", help="직업 부분일치, 예: 개발자,간호")
    g.add_argument("--exclude-occupation", help="제외할 직업 부분일치, 예: 무직")
    g.add_argument("--family-like", help="가구유형 부분일치, 예: 자녀,혼자 거주")
    g.add_argument("--marital", help="배우자있음,미혼,사별,이혼")
    g.add_argument("--education", help="무학,초등학교,중학교,고등학교,2~3년제 전문대학,4년제 대학교,대학원")
    g.add_argument("--housing", help="아파트,단독주택,다세대주택,연립주택,주택 이외의 거처,비주거용 건물 내 주택")
    g.add_argument("--major", help="전공계열 정확값, 예: 정보통신기술,보건·복지")
    g.add_argument("--keyword", help="서술형 필드 키워드(행동·상황 단서), 예: 배달,맞벌이")
    g.add_argument("--all-keywords", action="store_true", help="키워드를 OR 대신 AND로 결합")
    g.add_argument("--exclude-keyword", help="서술형 필드 제외 키워드")
    g.add_argument("--fields", help=f"키워드 검색 대상 필드(기본: 전체 서술형). 선택지: {','.join(TEXT_FIELDS)}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", help=f"로컬 parquet 디렉터리 (기본 캐시: {DEFAULT_CACHE})")
    ap.add_argument("--remote", action="store_true", help="로컬 캐시가 있어도 원격 질의")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("count", help="세그먼트 규모 세기")
    add_filters(p)
    p.add_argument("--by", help="분포 기준 컬럼, 예: age_band,sex,province,occupation")
    p.add_argument("--top", type=int, default=20)

    p = sub.add_parser("sample", help="페르소나 표본 추출")
    add_filters(p)
    p.add_argument("--n", type=int, default=5)
    p.add_argument("--seed", default="1", help="재현 가능한 무작위 순서용 시드")
    p.add_argument("--stratify", help="층화 기준, 예: age_band,sex 또는 province")
    p.add_argument("--per-stratum", type=int, default=2, help="층별 최대 인원")
    p.add_argument("--format", choices=["md", "json", "jsonl", "card"], default="md",
                   help="card: --out 디렉터리에 1인 1파일 페르소나 카드 뼈대 생성")
    p.add_argument("--project", default="project", help="card 형식의 project 값")
    p.add_argument("--out", help="저장 경로")

    p = sub.add_parser("get", help="uuid로 페르소나 조회")
    p.add_argument("uuid", nargs="+")
    p.add_argument("--format", choices=["md", "json", "jsonl", "card"], default="md",
                   help="card: --out 디렉터리에 1인 1파일 페르소나 카드 뼈대 생성")
    p.add_argument("--project", default="project", help="card 형식의 project 값")
    p.add_argument("--out")

    p = sub.add_parser("values", help="인구통계 컬럼의 실제 값 목록")
    p.add_argument("column")
    p.add_argument("--like")
    p.add_argument("--top", type=int, default=40)

    sub.add_parser("download", help=f"전체 parquet(약 2GB)을 로컬 캐시에 저장")

    args = ap.parse_args()
    if args.cmd == "download":
        return cmd_download(args)
    con = connect()
    {"count": cmd_count, "sample": cmd_sample, "get": cmd_get, "values": cmd_values}[args.cmd](con, args)


if __name__ == "__main__":
    main()
