#!/usr/bin/env python3
"""
audit_rig.py - deterministic measurements over a plain-text job advertisement.

Usage:  python3 audit_rig.py <file.txt> > results.json

Standard library only. No model, no network, no detector, no scoring.
Every number below is a count or a standard statistic over the input bytes.
Run it on any text and it will produce the same numbers on any machine.
"""
import json, re, statistics, sys, unicodedata, hashlib

WORD = re.compile(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*")

# Codepoint ranges normally rendered as colour bitmaps by an emoji font,
# plus the variation selector and ZWJ that bind sequences together.
EMOJI_RANGES = [
    (0x1F300, 0x1FAFF), (0x2600, 0x27BF), (0x2B00, 0x2BFF),
    (0x1F000, 0x1F2FF), (0xFE00, 0xFE0F), (0x200D, 0x200D),
]

def is_emojiish(ch):
    cp = ord(ch)
    return any(lo <= cp <= hi for lo, hi in EMOJI_RANGES)

def block_of(cp):
    # Coarse block attribution, sufficient to name where a codepoint lives.
    blocks = [
        (0x200D, 0x200D, "General Punctuation (ZWJ)"),
        (0x2600, 0x26FF, "Miscellaneous Symbols"),
        (0x2700, 0x27BF, "Dingbats"),
        (0x2B00, 0x2BFF, "Miscellaneous Symbols and Arrows"),
        (0xFE00, 0xFE0F, "Variation Selectors"),
        (0x1F300, 0x1F5FF, "Miscellaneous Symbols and Pictographs"),
        (0x1F600, 0x1F64F, "Emoticons"),
        (0x1F680, 0x1F6FF, "Transport and Map Symbols"),
        (0x1F900, 0x1F9FF, "Supplemental Symbols and Pictographs"),
        (0x1FA70, 0x1FAFF, "Symbols and Pictographs Extended-A"),
    ]
    for lo, hi, name in blocks:
        if lo <= cp <= hi:
            return name
    return "unassigned in this table"

def emoji_report(text):
    rows, order = [], []
    for i, ch in enumerate(text):
        if not is_emojiish(ch):
            continue
        cp = ord(ch)
        rows.append({
            "char_index": i,
            "codepoint": f"U+{cp:04X}",
            "unicode_name": unicodedata.name(ch, "(no name)"),
            "general_category": unicodedata.category(ch),
            "block": block_of(cp),
            "utf8_bytes": len(ch.encode("utf-8")),
            "utf16_code_units": len(ch.encode("utf-16-le")) // 2,
            "is_astral": cp > 0xFFFF,
            "nfkd_decomposes_to_text": unicodedata.normalize("NFKD", ch) != ch,
            "ascii_fallback": ch.encode("ascii", "replace").decode("ascii"),
        })
        order.append(f"U+{cp:04X}")
    return rows, order

def sentences(text):
    body = " ".join(l.strip() for l in text.splitlines() if l.strip())
    body = re.sub(r"\s+", " ", body)
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9"“(])', body)
    return [p.strip() for p in parts if WORD.search(p)]

def lag1(seq):
    if len(seq) < 3: return None
    m = statistics.fmean(seq)
    den = sum((x - m) ** 2 for x in seq)
    if den == 0: return None
    return sum((seq[i] - m) * (seq[i+1] - m) for i in range(len(seq)-1)) / den

# Constructions widely listed as machine-writing tells. Each is a surface
# pattern, not a verdict: a human can and does write every one of them.
TELLS = {
    "not_just_construction":      r"\b(?:it'?s|this is|we'?re)\s+not\s+just\b|\bnot\s+just\s+\w+,?\s+(?:but|it'?s)\b",
    "not_only_but_also":          r"\bnot only\b.{0,80}\bbut also\b",
    "isnt_about_its_about":       r"\bisn'?t\s+about\b.{0,60}\bit'?s\s+about\b",
    "this_isnt_for_you":          r"\b(?:this|it)\s+(?:isn'?t|is not)\s+for\s+(?:you|everyone)\b",
    "emoji_section_header":       r"(?m)^\s*[\U0001F300-\U0001FAFF☀-➿⬀-⯿]",
    "rhetorical_question_header": r"(?m)^[^.\n]{0,80}\?\s*$",
    "ensuring_allowing_enabling": r"\b(?:ensuring|allowing you to|enabling you to|making it)\b",
    "the_hard_part_framing":      r"\bthe hard parts?\b|\bwhat makes (?:it|this) hard\b",
    "x_not_y_sentence_fragment":  r"(?m)^\s*\w[^.\n]{0,60}, not [^.\n]{0,40}\.\s*$",
    "colon_why_x_matters":        r"[^\n:]{3,60}:\s*why\s+[^\n]{2,60}\bmatters\b",
    "stray_trailing_backslash":   r"(?m)^\s*\\\s*$",
    "em_dash_glyph":              r"—",
    "double_hyphen_for_dash":     r"\w--+\w|\s--+\s",
    "triadic_sentence_fragment":  r"(?m)^[A-Z][^.\n]{0,40}\.\s+[A-Z][^.\n]{0,40}\.\s+[A-Z][^.\n]{0,40}\.\s*$",
}

def tells(text):
    out = {}
    for name, pat in TELLS.items():
        found = [m.group(0)[:70].strip() for m in re.finditer(pat, text, re.I)]
        if found:
            out[name] = {"count": len(found), "first_match": found[0]}
    return out

def main(path):
    raw = open(path, encoding="utf-8").read()
    sents = sentences(raw)
    lens = [len(WORD.findall(s)) for s in sents]
    words = WORD.findall(raw)
    rows, order = emoji_report(raw)
    mean = statistics.fmean(lens)
    ac = lag1(lens)
    report = {
        "rig_version": "1.0",
        "source_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        "source_bytes_utf8": len(raw.encode("utf-8")),
        "source_characters": len(raw),
        "words": len(words),
        "sentences": len(lens),
        "sentence_length": {
            "mean": round(mean, 2),
            "median": statistics.median(lens),
            "sd": round(statistics.pstdev(lens), 2),
            "min": min(lens), "max": max(lens),
            "coefficient_of_variation": round(statistics.pstdev(lens) / mean, 3),
            "lag1_autocorrelation": round(ac, 3) if ac is not None else None,
            "sequence": lens,
        },
        "emoji": {
            "total_codepoints": len(rows),
            "distinct_codepoints": len(set(order)),
            "utf8_bytes_spent": sum(r["utf8_bytes"] for r in rows),
            "share_of_source_bytes_pct": round(100 * sum(r["utf8_bytes"] for r in rows) / len(raw.encode("utf-8")), 3),
            "codepoints": rows,
        },
        "machine_writing_tells_present": tells(raw),
        "limits": [
            "Every figure is a count or a standard statistic. None is a detector.",
            "No pattern here proves a machine wrote the text; humans write all of them.",
            "Sentence splitting is heuristic and will mis-split unusual punctuation.",
            "A short sample gives unstable dispersion figures. Treat them as descriptive.",
        ],
    }
    json.dump(report, sys.stdout, indent=2, ensure_ascii=False)
    print()

if __name__ == "__main__":
    main(sys.argv[1])
