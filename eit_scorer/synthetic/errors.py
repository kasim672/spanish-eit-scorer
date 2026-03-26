"""
eit_scorer/synthetic/errors.py
================================
spaCy-powered linguistic error transformation engine.

Generates realistic learner errors by:
  - Using spaCy morphological features to target errors precisely
  - Mapping CEFR level → error type probability distribution
  - Deterministic mode (fixed seed) or stochastic mode

Error types:
  DROP        : omit a token (function word, clitic, or content word)
  SUB_CONTENT : replace content word with different lemma
  MORPHO      : inflectional error — same lemma, wrong form
  INSERT      : insert an extra word
  SWAP        : reorder two adjacent tokens
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, Optional

# ── Word banks ────────────────────────────────────────────────
COMMON_NOUNS = [
    "cosa","vez","año","día","tiempo","hombre","mujer","niño","trabajo",
    "vida","caso","manera","lugar","parte","semana","gobierno","país",
    "ciudad","libro","agua","familia","mano","mundo","persona","punto",
    "problema","momento","empresa","resultado","ejemplo",
]
COMMON_VERBS = [
    "ser","estar","tener","hacer","poder","decir","ir","ver","dar",
    "saber","querer","llegar","pasar","deber","poner","parecer","quedar",
    "creer","hablar","llevar","dejar","seguir","encontrar","llamar",
    "venir","pensar","salir","volver","tomar","vivir",
]
COMMON_ADJ = [
    "grande","pequeño","bueno","malo","nuevo","viejo","primero","último",
    "largo","alto","bajo","importante","poco","mismo","otro","tanto",
    "mucho","todo","cada","cierto","solo","posible","necesario",
]
FUNCTION_WORDS = {
    "el","la","los","las","un","una","unos","unas",
    "a","de","en","con","por","para","sin","sobre","entre",
    "que","y","o","pero","si","aunque","cuando","donde",
    "del","al","se","me","te","nos","os","lo","le","les",
    "muy","más","ya","no","también","solo","aquí","allí",
}
CLITICS = {"me","te","se","lo","la","le","nos","os","los","las","les"}

# ── CEFR level → (mean_errors, {error_type: weight}, p_correct) ──
LEVEL_PROFILES = {
    "A1": (3.8, {"drop":0.40,"sub":0.28,"morpho":0.18,"insert":0.09,"swap":0.05}, 0.04),
    "A2": (2.9, {"drop":0.35,"sub":0.25,"morpho":0.24,"insert":0.10,"swap":0.06}, 0.09),
    "B1": (2.0, {"drop":0.25,"sub":0.20,"morpho":0.35,"insert":0.10,"swap":0.10}, 0.16),
    "B2": (1.2, {"drop":0.18,"sub":0.14,"morpho":0.46,"insert":0.08,"swap":0.14}, 0.28),
    "C1": (0.6, {"drop":0.12,"sub":0.10,"morpho":0.56,"insert":0.06,"swap":0.16}, 0.48),
    "C2": (0.25,{"drop":0.08,"sub":0.08,"morpho":0.62,"insert":0.06,"swap":0.16}, 0.68),
}

# ── Gender / number swaps ─────────────────────────────────────
_GENDER_MAP = {"o":"a","a":"o","os":"as","as":"os","ón":"ona","or":"ora"}
_TENSE_SWAPS = {
    "ó": ["a","aba"], "aron": ["an","aban"], "ió": ["e","ía"],
    "ieron":["en","ían"], "amos":["an","aban"], "aste":["as","abas"],
}


@dataclass
class ErrorTransform:
    name:  str
    apply: Callable[[list[str]], list[str]]


def _drop_token_at(idx: int) -> ErrorTransform:
    def fn(tokens):
        t = tokens[:]
        if idx < len(t): t.pop(idx)
        return t
    return ErrorTransform(f"drop@{idx}", fn)


def _sub_token_at(idx: int, new_token: str) -> ErrorTransform:
    def fn(tokens):
        t = tokens[:]
        if idx < len(t): t[idx] = new_token
        return t
    return ErrorTransform(f"sub@{idx}→{new_token}", fn)


def _swap_adjacent(idx: int) -> ErrorTransform:
    def fn(tokens):
        t = tokens[:]
        j = idx + 1
        if idx < len(t) and j < len(t):
            t[idx], t[j] = t[j], t[idx]
        return t
    return ErrorTransform(f"swap@{idx}↔{idx+1}", fn)


def _insert_token_at(idx: int, word: str) -> ErrorTransform:
    def fn(tokens):
        t = tokens[:]
        t.insert(min(idx, len(t)), word)
        return t
    return ErrorTransform(f"insert'{word}'@{idx}", fn)


def _gender_swap(word: str) -> str:
    for src, dst in _GENDER_MAP.items():
        if src and word.endswith(src):
            return word[:-len(src)] + dst
    return word + "a" if not word.endswith("a") else word[:-1] + "o"


def _number_swap(word: str) -> str:
    if word.endswith("es") and len(word) > 3: return word[:-2]
    if word.endswith("s") and len(word) > 2:  return word[:-1]
    return word + "s"


def _tense_swap(word: str, rng: random.Random) -> str:
    for ending, alts in _TENSE_SWAPS.items():
        if word.endswith(ending):
            return word[:-len(ending)] + rng.choice(alts)
    # Fallback: change person
    if word.endswith("amos"): return word[:-4] + "an"
    if word.endswith("an") and len(word) > 3: return word[:-2] + "a"
    return word


# ── spaCy lazy loader ────────────────────────────────────────
_NLP = None

def _get_nlp():
    global _NLP
    if _NLP is None:
        try:
            import spacy
            for model in ("es_core_news_lg","es_core_news_md","es_core_news_sm"):
                try:
                    _NLP = spacy.load(model)
                    break
                except OSError:
                    continue
        except ImportError:
            pass
    return _NLP


# ── Token annotation ─────────────────────────────────────────
def _annotate(tokens: list[str]):
    """Annotate tokens with spaCy. Returns list of dicts, one per token."""
    nlp = _get_nlp()
    result = []
    if nlp:
        try:
            doc = nlp(" ".join(tokens))
            for tok in doc:
                if tok.text.strip():
                    morph = {}
                    for feat in str(tok.morph).split("|"):
                        if "=" in feat:
                            k, v = feat.split("=",1)
                            morph[k] = v
                    result.append({
                        "text": tok.text,
                        "pos":  tok.pos_,
                        "lemma":tok.lemma_.lower(),
                        "morph":morph,
                        "is_content": tok.pos_ in {"NOUN","VERB","ADJ","ADV","PROPN","NUM"},
                        "is_function":tok.pos_ in {"DET","ADP","CCONJ","SCONJ","PART"},
                        "is_clitic":  tok.text.lower() in CLITICS,
                    })
            # Pad or truncate to match tokens length
            while len(result) < len(tokens):
                t = tokens[len(result)]
                result.append({"text":t,"pos":"NOUN","lemma":t,"morph":{},
                    "is_content":t not in FUNCTION_WORDS,
                    "is_function":t in FUNCTION_WORDS,
                    "is_clitic":t in CLITICS})
            return result[:len(tokens)]
        except Exception:
            pass

    # Fallback without spaCy
    for t in tokens:
        result.append({"text":t,"pos":"NOUN","lemma":t,"morph":{},
            "is_content":t not in FUNCTION_WORDS,
            "is_function":t in FUNCTION_WORDS,
            "is_clitic":t in CLITICS})
    return result


# ── Error plan generator ─────────────────────────────────────
def build_error_plan(
    tokens: list[str],
    level:  str,
    rng:    random.Random,
    force_errors: Optional[int] = None,
) -> list[ErrorTransform]:
    """
    Build a list of ErrorTransform objects for the given token list.
    Uses spaCy annotations when available.
    Deterministic when rng is seeded.
    """
    if not tokens:
        return []

    profile = LEVEL_PROFILES.get(level, LEVEL_PROFILES["B1"])
    mean_n, type_weights, p_correct = profile

    if rng.random() < p_correct:
        return []

    n_errors = force_errors if force_errors is not None else max(
        0, round(rng.gauss(mean_n, mean_n * 0.35))
    )
    n_errors = min(n_errors, max(1, len(tokens) - 1))
    if n_errors == 0:
        return []

    ann = _annotate(tokens)
    plan: list[ErrorTransform] = []
    used: set[int] = set()
    etypes = list(type_weights.keys())
    eweights = [type_weights[e] for e in etypes]

    for _ in range(n_errors):
        avail = [i for i in range(len(tokens)) if i not in used]
        if not avail:
            break
        etype = rng.choices(etypes, weights=eweights)[0]

        if etype == "drop":
            # Prefer function words at lower levels; content at all
            func_idxs = [i for i in avail if ann[i]["is_function"] or ann[i]["is_clitic"]]
            cont_idxs = [i for i in avail if ann[i]["is_content"]]
            if level in ("A1","A2") and cont_idxs and rng.random() < 0.55:
                idx = rng.choice(cont_idxs)
            elif func_idxs and rng.random() < 0.70:
                idx = rng.choice(func_idxs)
            elif cont_idxs:
                idx = rng.choice(cont_idxs)
            else:
                idx = rng.choice(avail)
            plan.append(_drop_token_at(idx))
            used.add(idx)

        elif etype == "sub":
            cont_idxs = [i for i in avail if ann[i]["is_content"]]
            idx = rng.choice(cont_idxs) if cont_idxs else rng.choice(avail)
            pos = ann[idx]["pos"]
            if pos == "NOUN":    new = rng.choice([w for w in COMMON_NOUNS if w != tokens[idx]])
            elif pos in ("VERB","AUX"): new = rng.choice([w for w in COMMON_VERBS if w != tokens[idx]])
            elif pos == "ADJ":   new = rng.choice([w for w in COMMON_ADJ  if w != tokens[idx]])
            else:                new = rng.choice(COMMON_NOUNS)
            if new and new != tokens[idx]:
                plan.append(_sub_token_at(idx, new))
                used.add(idx)

        elif etype == "morpho":
            verb_idxs = [i for i in avail if ann[i]["pos"] in ("VERB","AUX")]
            adj_idxs  = [i for i in avail if ann[i]["pos"] == "ADJ"]
            if verb_idxs and rng.random() < 0.65:
                idx = rng.choice(verb_idxs)
                new = _tense_swap(tokens[idx], rng)
            elif adj_idxs:
                idx = rng.choice(adj_idxs)
                new = _gender_swap(tokens[idx]) if rng.random() < 0.6 else _number_swap(tokens[idx])
            else:
                idx = rng.choice(avail)
                new = _gender_swap(tokens[idx])
            if new and new != tokens[idx]:
                plan.append(_sub_token_at(idx, new))
                used.add(idx)

        elif etype == "insert":
            idx = rng.choice(avail)
            word = rng.choice(list(FUNCTION_WORDS) + COMMON_NOUNS[:4])
            plan.append(_insert_token_at(idx, word))
            # insertions don't consume a slot

        elif etype == "swap":
            swap_avail = [i for i in avail if i+1 not in used and i+1 < len(tokens)]
            if swap_avail:
                idx = rng.choice(swap_avail)
                plan.append(_swap_adjacent(idx))
                used.add(idx); used.add(idx+1)

    return plan


def apply_plan(tokens: list[str], plan: list[ErrorTransform]) -> list[str]:
    """Apply error transforms in order. Returns modified token list."""
    result = tokens[:]
    for transform in plan:
        result = transform.apply(result)
    return result


def deterministic_error_plan(
    ref_tokens: list[str],
    severity:   int,
) -> list[ErrorTransform]:
    """
    Fully deterministic plan (no randomness) derived from severity 0–3.
    Severity 0 = perfect; 3 = many errors.
    Uses token indices derived from sentence length.
    """
    if severity == 0 or not ref_tokens:
        return []

    n = len(ref_tokens)
    plan = []

    if severity >= 1 and n > 2:
        idx = n // 3
        plan.append(_drop_token_at(idx))

    if severity >= 2 and n > 4:
        idx = n * 2 // 3
        if idx < n:
            new_tok = COMMON_NOUNS[idx % len(COMMON_NOUNS)]
            plan.append(_sub_token_at(idx, new_tok))

    if severity >= 3 and n > 5:
        idx = n // 4
        if idx + 1 < n:
            plan.append(_swap_adjacent(idx))

    return plan
