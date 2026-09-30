"""Question builders and grading for the quizzes.

quiz_vocab / quiz_grammar    — the lesson's vocabulary and grammar rounds
quiz_words                  — mixed round from an explicit word list (weak-word drills)
quiz_keigo_en_jp / jp_en / hon_norm / norm_hon — the four honorific sub-drills

Every vocab item carries vocabId so the engine can update that word's stars,
and speakText / speakAnswer so the quiz widget can read Japanese aloud.
"""
import random
import re


_KATA = "ァアィイゥウェエォオカガキギクグケゲコゴサザシジスズセゼソゾタダチヂッツヅテデトドナニヌネノハバパヒビピフブプヘベペホボポマミムメモャヤュユョヨラリルレロヮワヰヱヲンヴ"
_HIRA = "ぁあぃいぅうぇえぉおかがきぎくぐけげこごさざしじすずせぜそぞただちぢっつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽまみむめもゃやゅゆょよらりるれろゎわゐゑをんゔ"
_KANA_TABLE = str.maketrans(_KATA, _HIRA)


def norm(s):
    """Normalise for comparison: lowercase, strip punctuation, unify katakana to
    hiragana so both scripts are always accepted."""
    s = str(s or "").strip().lower()
    s = re.sub(r"[。．.、,!！?？\s〜~]", "", s)
    return s.translate(_KANA_TABLE)


def _english_answers(v):
    parts = [p for p in re.split(r"[;,/]", v["english"]) if p.strip()]
    return [re.sub(r"\(.*?\)", "", p).strip() for p in parts if re.sub(r"\(.*?\)", "", p).strip()]


def _show_pair(v):
    """kanji（kana） when a kanji form exists, otherwise the kana."""
    return f'{v["kanji"]}（{v["japanese"]}）' if v.get("kanji") else v["japanese"]


def _explain(v):
    return f'{_show_pair(v)} ({v["reading"]}) = {v["english"]}'


def _explain_g(g):
    base = f'{g["pattern"]} — {g["meaning"]}'
    ex = g.get("example")
    if ex:
        base += f'\n{ex["jp"]} = {ex["en"]}'
    return base


def _pick(items, n):
    return random.sample(items, min(n, len(items)))


def _mc(prompt, correct, distractors, explain, prompt_ja=False,
        speak_text=None, vocab_id=None, options_ja=None):
    options = list(distractors) + [correct]
    random.shuffle(options)
    item = {"kind": "mc", "prompt": prompt, "promptJa": prompt_ja,
            "options": options, "correct": options.index(correct), "explain": explain}
    if speak_text:
        item["speakText"] = speak_text
    if vocab_id:
        item["vocabId"] = vocab_id
    if options_ja is not None:
        item["optionsJa"] = options_ja
    return item


# ---------- vocabulary ----------
def quiz_words(vocab, n=10):
    """Mixed JP<->EN round from an explicit word list."""
    items = []
    for v in _pick(vocab, n):
        others = [x for x in vocab if x["id"] != v["id"]]
        mode = random.choice(("jp-en", "en-jp", "type-jp", "type-en"))
        if mode == "jp-en":
            distract = [x["english"] for x in _pick(others, 3)]
            items.append(_mc(_show_pair(v), v["english"], distract, _explain(v),
                             prompt_ja=True, speak_text=v["japanese"], vocab_id=v["id"],
                             options_ja=False))
        elif mode == "en-jp":
            distract = [_show_pair(x) for x in _pick(others, 3)]
            item = _mc(v["english"], _show_pair(v), distract, _explain(v), vocab_id=v["id"],
                       options_ja=True)
            item["speakAnswer"] = v["japanese"]
            items.append(item)
        elif mode == "type-jp":
            items.append({"kind": "type", "prompt": v["english"], "lang": "ja",
                          "answers": [a for a in (v.get("kanji"), v["japanese"], v["reading"]) if a],
                          "explain": _explain(v), "speakAnswer": v["japanese"], "vocabId": v["id"]})
        else:
            items.append({"kind": "type", "prompt": _show_pair(v), "promptJa": True, "lang": "en",
                          "answers": _english_answers(v), "explain": _explain(v),
                          "speakText": v["japanese"], "vocabId": v["id"]})
    return items


def quiz_vocab(lesson, n=10):
    """Build a vocab round for one lesson (prefers textbook words, then extras)."""
    vocab = [v for v in lesson["vocab"] if not v.get("extra")] or lesson["vocab"]
    return quiz_words(vocab, n)


# ---------- grammar ----------
def quiz_grammar(lesson, n=10):
    """Build a grammar round: pattern<->meaning and example translations."""
    grammar = lesson["grammar"]
    items = []
    for g in _pick(grammar, n):
        others = [x for x in grammar if x is not g]
        form = random.choice(("p2m", "m2p", "ex"))
        if form == "p2m" and len(others) >= 3:
            distract = [x["meaning"] for x in _pick(others, 3)]
            items.append(_mc(g["pattern"], g["meaning"], distract, _explain_g(g),
                             prompt_ja=True, speak_text=g["pattern"], options_ja=False))
        elif form == "m2p" and len(others) >= 3:
            distract = [x["pattern"] for x in _pick(others, 3)]
            items.append(_mc(g["meaning"], g["pattern"], distract, _explain_g(g),
                             options_ja=True))
        else:
            ex = g.get("example")
            prompt = ex["jp"] if ex else g["pattern"]
            answers = [ex["en"].rstrip(".")] if ex else []
            item = {"kind": "type", "prompt": prompt, "promptJa": True, "lang": "en",
                    "answers": answers, "explain": _explain_g(g)}
            if ex:
                item["speakText"] = prompt
            items.append(item)
    return items


# ---------- honorific drills ----------
def _keigo_verbs(data, lesson_id):
    verbs = []
    for lesson in data["lessons"]:
        if lesson["id"] > lesson_id:
            break
        for v in lesson["vocab"]:
            if v.get("keigo"):
                verbs.append(v)
    return verbs


def _rev_map(verbs):
    m = {}
    for v in verbs:
        m.setdefault(v["keigoKana"], []).append(v)
    return m


def _keigo_label(v):
    return f'{v["keigo"]}（尊敬語）'


def quiz_keigo_en_jp(data, lesson_id, n=10):
    """English → Japanese: type the honorific (kana/kanji/〜ます accepted)."""
    items = []
    for v in _pick(_keigo_verbs(data, lesson_id), n):
        items.append({"kind": "type", "prompt": v["english"], "lang": "ja",
                      "answers": [a for a in (v["keigoKana"], v["keigo"], v["keigoMasu"]) if a],
                      "explain": f'{_show_pair(v)} → {v["keigo"]}（{v["keigoKana"]}／{v["keigoMasu"]}）',
                      "speakAnswer": v["keigoKana"], "vocabId": v["id"]})
    return items


def quiz_keigo_jp_en(data, lesson_id, n=10):
    """Japanese → English: see and hear the honorific, type the meaning."""
    items = []
    for v in _pick(_keigo_verbs(data, lesson_id), n):
        items.append({"kind": "type", "prompt": _keigo_label(v), "promptJa": True, "lang": "en",
                      "answers": _english_answers(v),
                      "explain": f'{v["keigo"]}（{v["keigoKana"]}） = {v["english"]} (honorific of {_show_pair(v)})',
                      "speakText": v["keigoKana"], "vocabId": v["id"]})
    return items


def quiz_keigo_hon_norm(data, lesson_id, n=10):
    """Honorific → normal: hear the honorific, type any valid base verb."""
    verbs = _keigo_verbs(data, lesson_id)
    rev = _rev_map(verbs)
    items = []
    for kana, bases in _pick(list(rev.items()), n):
        v = random.choice(bases)
        answers = []
        for b in bases:
            answers += [a for a in (b["japanese"], b.get("kanji")) if a]
        bases_label = " / ".join(_show_pair(b) for b in bases)
        items.append({"kind": "type", "prompt": _keigo_label(v), "promptJa": True, "lang": "ja",
                      "answers": sorted(set(answers)),
                      "explain": f'{v["keigo"]}（{v["keigoKana"]}） ← {bases_label}',
                      "speakText": v["keigoKana"], "speakAnswer": bases[0]["japanese"],
                      "vocabId": v["id"]})
    return items


def quiz_keigo_norm_hon(data, lesson_id, n=10):
    """Normal → honorific: hear the base verb, type the honorific."""
    items = []
    for v in _pick(_keigo_verbs(data, lesson_id), n):
        items.append({"kind": "type", "prompt": _show_pair(v), "promptJa": True, "lang": "ja",
                      "answers": [a for a in (v["keigoKana"], v["keigo"], v["keigoMasu"]) if a],
                      "explain": f'{_show_pair(v)} → {v["keigo"]}（{v["keigoKana"]}／{v["keigoMasu"]}）',
                      "speakText": v["japanese"], "speakAnswer": v["keigoKana"],
                      "vocabId": v["id"]})
    return items


# ---------- preview table rows (Education Perfect style) ----------
def vocab_rows(lesson):
    """[(stimulus, answer, vocabId)] for the lesson's words."""
    rows = []
    for v in lesson["vocab"]:
        rows.append({"stim": _show_pair(v),
                     "ans": f'{v["english"]} · {v["reading"]}', "vid": v["id"]})
    return rows


def grammar_rows(lesson):
    rows = []
    for g in lesson["grammar"]:
        ex = g.get("example")
        ans = g["meaning"] + (f'\n{ex["jp"]} = {ex["en"]}' if ex else "")
        rows.append({"stim": g["pattern"], "ans": ans, "vid": None})
    return rows


def keigo_rows(data, lesson_id, direction):
    """Preview rows for an honorific sub-drill."""
    verbs = _keigo_verbs(data, lesson_id)
    rows = []
    if direction == "keigo-norm-hon":
        for v in verbs:
            rows.append({"stim": _show_pair(v),
                         "ans": f'{v["keigo"]}（{v["keigoKana"]}／{v["keigoMasu"]}）', "vid": v["id"]})
    elif direction == "keigo-en-jp":
        for v in verbs:
            rows.append({"stim": v["english"],
                         "ans": f'{v["keigo"]}（{v["keigoKana"]}／{v["keigoMasu"]}）', "vid": v["id"]})
    elif direction == "keigo-jp-en":
        for v in verbs:
            rows.append({"stim": _keigo_label(v), "ans": v["english"], "vid": v["id"]})
    else:  # keigo-hon-norm
        for kana, bases in _rev_map(verbs).items():
            rows.append({"stim": _keigo_label(bases[0]),
                         "ans": " / ".join(_show_pair(b) for b in bases),
                         "vid": bases[0]["id"]})
    return rows


def grade(item, answer):
    if item["kind"] == "mc":
        return answer == item["correct"]
    return norm(answer) in [norm(a) for a in item["answers"]]
