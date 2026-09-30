"""Systematic audit of honorific (keigo) data.

Checks, in order:
  1. every keigo-carrying vocab item is a verb (catches misattached entries)
  2. noun+なさる honorifics follow the curated ご/お prefix rules
  3. cross-field consistency: kana form and 〜ます form agree with the kanji form
  4. curated answer variants (alt) are present and correct
  5. full-database お/ご prefix consistency between kanji and kana fields

Usage:  python scripts\\audit_keigo.py [path-to-genki-data.json]
Default path:  <repo>/data/genki-data.json
Exit code 1 if any problem is found.
"""
import json
import os
import sys

# curated prefix rules for noun+なさる honorifics (kept in sync with data/keigo-map.mjs)
PREFIX_RULES = {
    # 漢語 → ご
    "勉強": "ご", "結婚": "ご", "演奏": "ご", "採用": "ご", "案内": "ご",
    "説明": "ご", "紹介": "ご", "挨拶": "ご", "報告": "ご", "遠慮": "ご",
    "招待": "ご", "勘違い": "ご", "混乱": "ご",
    # conventional お
    "料理": "お", "散歩": "お", "読書": "お", "気に": "お",
    # no prefix (never ご/お + noun)
    "感謝": "", "失礼": "", "プレゼント": "", "デート": "",
}
# nouns whose ご is part of the noun itself (not an honorific prefix)
INHERENT = {"ご馳走": "ご"}
# なる-ending forms that are irregular specials, not the お+stem+になる pattern
SPECIAL_NARU = {"ごらんになる", "おやすみになる"}
# する → なさる itself (the base special, not a noun entry)
PLAIN_NASARU = "なさる"

VERB_TYPES = ("verb", "verb-u", "verb-ru", "verb-irr", "verb-tr", "verb-intr", "expression")


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "genki-data.json")
    data = json.load(open(path, encoding="utf-8"))
    problems = []
    seen_nouns = set()

    for lesson in data["lessons"]:
        for v in lesson["vocab"]:
            k = v.get("keigo")
            if not k:
                continue
            loc = f"L{v['lesson']} {v['id']} {v['japanese']}"
            # 1) verbs only
            if v["type"] not in VERB_TYPES:
                problems.append(f"{loc}: keigo on a non-verb ({v['type']}) -> {k}")
                continue
            kana = v.get("keigoKana") or ""
            m = v.get("keigoMasu") or ""
            alt = v.get("keigoAlt") or []

            # noun+なさる entries
            if kana.endswith("なさる") and k != PLAIN_NASARU:
                stem_k = k[:-3]        # drop なさる
                stem_kana = kana[:-3]
                seen_nouns.add(stem_k)
                prefix = stem_k[0] if stem_k.startswith(("ご", "お")) else ""
                noun = stem_k[1:] if prefix else stem_k
                # 2) prefix rule
                if stem_k in INHERENT:
                    if stem_k != INHERENT[stem_k] + noun:
                        problems.append(f"{loc}: inherent ご noun mismatch -> {k}")
                    expect_kana = stem_kana + "なさる"
                    if kana != expect_kana:
                        problems.append(f"{loc}: kana {kana} != expected {expect_kana}")
                elif noun in PREFIX_RULES:
                    if prefix != PREFIX_RULES[noun]:
                        problems.append(f"{loc}: prefix should be {PREFIX_RULES[noun] or '(none)'} -> {k}")
                else:
                    problems.append(f"{loc}: noun {noun} missing from PREFIX_RULES audit table")
                # 3) cross-field consistency
                noun_kana = v["japanese"][:-2] if v["japanese"].endswith("する") else None
                if noun_kana is not None and not any("ァ" <= ch <= "ヶ" for ch in noun_kana) \
                        and stem_k not in INHERENT:
                    expect_kana = (prefix + noun_kana + "なさる")
                    if kana != expect_kana:
                        problems.append(f"{loc}: kana {kana} != expected {expect_kana}")
                if stem_k not in INHERENT:
                    expect_m = stem_k + "なさいます"
                    if m != expect_m:
                        problems.append(f"{loc}: masu {m} != expected {expect_m}")
                # 4) curated alt variants
                if noun == "気に":
                    expect_alt = [f"{noun}なさる", f"{noun_kana}なさる", f"{noun}なさいます"]
                elif stem_k in INHERENT:
                    expect_alt = [f"{stem_k}になる", f"{stem_kana}になる", f"{stem_k}になります"]
                elif prefix:
                    expect_alt = [f"{noun}なさる", f"{noun_kana}なさる", f"{noun}なさいます",
                                  f"{stem_k}になる", f"{stem_kana}になる", f"{stem_k}になります"]
                else:
                    expect_alt = []
                if sorted(alt) != sorted(expect_alt):
                    problems.append(f"{loc}: alts {sorted(alt)} != expected {sorted(expect_alt)}")
                if len(set(alt)) != len(alt):
                    problems.append(f"{loc}: duplicate alt variants")
            elif kana.endswith("になる") and kana not in SPECIAL_NARU:
                # お+stem+になる pattern: light sanity only (stems vary by conjugation)
                if not kana.startswith("お"):
                    problems.append(f"{loc}: になる-pattern kana missing お -> {kana}")
                if m != k[:-3] + "になります":
                    problems.append(f"{loc}: masu {m} != expected {k[:-3] + 'になります'}")
            elif kana not in ("いらっしゃる", "くださる", "おっしゃる", "めしあがる",
                              "なさる", "ごらんになる", "おやすみになる"):
                problems.append(f"{loc}: unrecognised keigo form -> {k} / {kana}")

    # 5) full-database prefix consistency (kanji has お/ご but kana doesn't)
    for lesson in data["lessons"]:
        for v in lesson["vocab"]:
            kanji = v.get("kanji") or ""
            if kanji and kanji.startswith(("お", "ご")) and not v["japanese"].startswith(kanji[0]):
                problems.append(f"L{v['lesson']} {v['id']} {v['japanese']}: kanji {kanji} "
                                f"starts {kanji[0]} but kana doesn't")

    out = "\n".join(problems) if problems else "no problems"
    report_path = os.path.join(os.path.dirname(path), "keigo-audit-report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(out + "\n")
    print(f"audit: {len(problems)} problem(s) — report written to {report_path}")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
