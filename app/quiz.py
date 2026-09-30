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


# All quizzes are typing-only — multiple choice was removed entirely.


# ---------- session builder ----------
SESSION_SIZE = 50


def session_items(pool, make, n=SESSION_SIZE):
    """Build a session of up to n items.

    Every presented word is scheduled to come back 8-10 items later, so a word
    is always re-presented within the next 10 words. When the pool is exhausted
    it reshuffles and keeps going (up to n items).
    """
    if not pool:
        return []
    bag = list(pool)
    random.shuffle(bag)
    pending = []  # [position, word]
    items = []
    while len(items) < n:
        due = [p for p in pending if p[0] <= len(items)]
        if due:
            _, w = due[0]
            pending.remove(due[0])
        else:
            if not bag:
                bag = list(pool)
                random.shuffle(bag)
            w = bag.pop()
            pending.append([len(items) + random.randint(8, 10), w])
        item = make(pool, w)
        if item is not None:
            items.append(item)
    return items


# ---------- vocabulary ----------
def vocab_item(vocab, v):
    """One typing question for a word: EN→JP or JP→EN (no multiple choice)."""
    mode = random.choice(("type-jp", "type-en"))
    if mode == "type-jp":
        return {"kind": "type", "prompt": v["english"], "lang": "ja",
                "answers": [a for a in (v.get("kanji"), v["japanese"], v["reading"]) if a],
                "explain": _explain(v), "speakAnswer": v["japanese"], "vocabId": v["id"]}
    return {"kind": "type", "prompt": _show_pair(v), "promptJa": True, "lang": "en",
            "answers": _english_answers(v), "explain": _explain(v),
            "speakText": v["japanese"], "vocabId": v["id"]}


def quiz_words(vocab, n=SESSION_SIZE):
    """Mixed JP<->EN session from an explicit word list (re-presentation + refill)."""
    return session_items(vocab, vocab_item, n)


def quiz_vocab(lesson, n=SESSION_SIZE):
    """Build a vocab session for one lesson (prefers textbook words, then extras)."""
    vocab = [v for v in lesson["vocab"] if not v.get("extra")] or lesson["vocab"]
    return quiz_words(vocab, n)


# ---------- grammar ----------
def grammar_item(grammar, g):
    """One grammar question: hear/see the example sentence, type its English
    translation (no multiple choice). Points without an example are skipped."""
    ex = g.get("example")
    if not ex:
        return None
    return {"kind": "type", "prompt": ex["jp"], "promptJa": True, "lang": "en",
            "answers": [ex["en"].rstrip(".")], "explain": _explain_g(g),
            "speakText": ex["jp"]}


def quiz_grammar(lesson, n=SESSION_SIZE):
    """Build a grammar session for one lesson."""
    return session_items(lesson["grammar"], grammar_item, n)


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
    return f'{v["keigo"]}（{v["keigoKana"]}・尊敬語）'


def keigo_groups(verbs):
    """[(keigoKana, bases), ...] for the honorific→normal direction."""
    return list(_rev_map(verbs).items())


def keigo_item(verbs, x, direction):
    """One honorific-drill question. x is a verb dict, or a (kana, bases) group
    for the honorific→normal direction."""
    if direction == "keigo-hon-norm":
        kana, bases = x
        v = random.choice(bases)
        answers = []
        for b in bases:
            answers += [a for a in (b["japanese"], b.get("kanji")) if a]
        bases_label = " / ".join(_show_pair(b) for b in bases)
        return {"kind": "type", "prompt": _keigo_label(v), "promptJa": True, "lang": "ja",
                "answers": sorted(set(answers)),
                "explain": f'{v["keigo"]}（{v["keigoKana"]}） ← {bases_label}',
                "speakText": v["keigoKana"], "speakAnswer": bases[0]["japanese"],
                "vocabId": v["id"]}
    if direction == "keigo-en-jp":
        return {"kind": "type", "prompt": x["english"], "lang": "ja",
                "answers": [a for a in (x["keigoKana"], x["keigo"], x["keigoMasu"],
                                       *x.get("keigoAlt", [])) if a],
                "explain": f'{_show_pair(x)} → {x["keigo"]}（{x["keigoKana"]}／{x["keigoMasu"]}）',
                "speakAnswer": x["keigoKana"], "vocabId": x["id"]}
    if direction == "keigo-jp-en":
        return {"kind": "type", "prompt": _keigo_label(x), "promptJa": True, "lang": "en",
                "answers": _english_answers(x),
                "explain": f'{x["keigo"]}（{x["keigoKana"]}） = {x["english"]} (honorific of {_show_pair(x)})',
                "speakText": x["keigoKana"], "vocabId": x["id"]}
    return {"kind": "type", "prompt": _show_pair(x), "promptJa": True, "lang": "ja",
            "answers": [a for a in (x["keigoKana"], x["keigo"], x["keigoMasu"],
                                   *x.get("keigoAlt", [])) if a],
            "explain": f'{_show_pair(x)} → {x["keigo"]}（{x["keigoKana"]}／{x["keigoMasu"]}）',
            "speakText": x["japanese"], "speakAnswer": x["keigoKana"],
            "vocabId": x["id"]}


def quiz_keigo_en_jp(data, lesson_id, n=SESSION_SIZE):
    """English → Japanese session."""
    return session_items(_keigo_verbs(data, lesson_id),
                         lambda p, v: keigo_item(p, v, "keigo-en-jp"), n)


def quiz_keigo_jp_en(data, lesson_id, n=SESSION_SIZE):
    """Japanese → English session."""
    return session_items(_keigo_verbs(data, lesson_id),
                         lambda p, v: keigo_item(p, v, "keigo-jp-en"), n)


def quiz_keigo_hon_norm(data, lesson_id, n=SESSION_SIZE):
    """Honorific → normal session."""
    groups = keigo_groups(_keigo_verbs(data, lesson_id))
    return session_items(groups, lambda p, g: keigo_item(p, g, "keigo-hon-norm"), n)


def quiz_keigo_norm_hon(data, lesson_id, n=SESSION_SIZE):
    """Normal → honorific session."""
    return session_items(_keigo_verbs(data, lesson_id),
                         lambda p, v: keigo_item(p, v, "keigo-norm-hon"), n)


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
