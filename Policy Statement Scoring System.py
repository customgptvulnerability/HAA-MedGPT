#################################################################################################################################
#-------------------------------------------- Privacy Policy Statement Compliance Scoring System -------------------------------#
#################################################################################################################################

import os
import re
import csv
import math
import random
from pathlib import Path
from typing import List, Dict, Tuple

BASE_DIR = r"C:\Users\XXXXXXXXXXXXXXXXXXXX\Healthcare GPT Assessment\Privacy Policy Statements"
REFERENCE_NAME_CONTAINS = "openai privacy policy"  # case-insensitive substring for reference file
OUTPUT_CSV = "privacy_compliance_scores.csv"
ENCODINGS_TO_TRY = ("utf-8", "utf-8-sig", "cp1252", "latin-1")
BOOTSTRAP_CHUNKS = 6          # split candidate into this many contiguous chunks (if long enough)
BOOTSTRAP_SAMPLES = 8         # number of sub-sample trials
MIN_TOKENS_FOR_BOOTSTRAP = 1200
RNG_SEED = 17


# Canonical policy topic clusters (keywords are case-insensitive).
TOPIC_KEYWORDS: Dict[str, List[str]] = {
    "collection": ["collect", "collection", "gather", "obtain", "receive", "categories of personal", "information we collect"],
    "use_processing": ["use", "purpose", "process", "processing", "how we use"],
    "sharing_disclosure": ["share", "disclose", "third party", "service provider", "processor", "sell", "sale", "vendors", "partners"],
    "retention_deletion": ["retain", "retention", "store", "storage", "delete", "deletion", "erase", "keep", "duration"],
    "security": ["security", "protect", "safeguard", "encryption", "breach"],
    "rights_requests": ["your rights", "access", "correct", "rectify", "erase", "delete", "object", "restrict", "portability", "opt-out", "opt out", "appeal"],
    "cookies_tracking": ["cookie", "cookies", "tracking", "pixel", "web beacon", "sdk", "cookie policy"],
    "analytics_ads": ["analytics", "advertising", "ads", "marketing", "profiling"],
    "children": ["children", "child", "minor", "under 13", "under 16", "coppa"],
    "international_transfers": ["transfer", "international", "eea", "uk", "adequacy", "standard contractual clauses", "scc"],
    "legal_basis": ["lawful", "legal basis", "consent", "contract", "legitimate interest", "compliance with legal obligations"],
    "changes_notice": ["changes", "update", "last updated", "effective date", "notice"],
    "contact": ["contact", "questions", "privacy@", "dpo", "data protection officer", "address"],
}

STRUCTURE_CLUES: Dict[str, List[str]] = {
    "effective_date": ["effective date", "last updated"],
    "contact_block": ["contact", "privacy@", "data protection officer", "dpo"],
    "policy_heading": ["privacy policy", "privacy notice"],
}

def read_text(path: Path) -> str:
    for enc in ENCODINGS_TO_TRY:
        try:
            return path.read_text(encoding=enc, errors="ignore")
        except Exception:
            continue
    with open(path, "rb") as f:
        return f.read().decode("utf-8", errors="ignore")

def find_reference_file(base_dir: Path) -> Path:
    txt_files = [p for p in base_dir.glob("*.txt")]
    if not txt_files:
        raise FileNotFoundError(f"No .txt files found in {base_dir}")
    for p in txt_files:
        if REFERENCE_NAME_CONTAINS in p.stem.lower():
            return p
    # If not found by name, fallback to the largest file (likely the policy)
    return max(txt_files, key=lambda p: p.stat().st_size)


def normalize(text: str) -> str:
    text = text.replace("\u00A0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()

def tokenize_words(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())

def make_shingles(tokens: List[str], k: int = 3) -> set:
    if len(tokens) < k:
        return set()
    return {" ".join(tokens[i:i+k]) for i in range(len(tokens)-k+1)}

def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def topic_coverage_score(text: str) -> Tuple[float, List[str]]:
    found = []
    missing = []
    for topic, kws in TOPIC_KEYWORDS.items():
        if any(kw in text for kw in kws):
            found.append(topic)
        else:
            missing.append(topic)
    coverage = len(found) / max(len(TOPIC_KEYWORDS), 1)
    return coverage, missing

def structure_score(text: str) -> float:
    points = 0
    points += 1 if any(kw in text for kw in STRUCTURE_CLUES["effective_date"]) else 0
    points += 1 if any(kw in text for kw in STRUCTURE_CLUES["contact_block"]) else 0
    points += 1 if any(kw in text for kw in STRUCTURE_CLUES["policy_heading"]) else 0
    return points / 3.0

def length_reasonableness_factor(candidate_len: int, ref_len: int) -> float:
    if ref_len <= 0:
        return 0.5
    ratio = candidate_len / ref_len
    if 0.5 <= ratio <= 2.0:
        return 1.0
    elif 0.2 <= ratio < 0.5 or 2.0 < ratio <= 3.0:
        return 0.7
    else:
        return 0.4

def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def compliance_from_components(sim_k3: float, coverage: float, struct: float) -> float:
    # Slightly favor semantic overlap and topic breadth; structure is supportive.
    return clamp(0.50 * sim_k3 + 0.35 * coverage + 0.15 * struct)

def score_stability_across_k(ref_tokens: List[str], cand_tokens: List[str],
                             coverage: float, struct: float) -> Tuple[float, float, float, float]:
    """
    Compute compliance via k=2/3/4 shingles and return:
      (stability_conf, c2, c3, c4)  where stability_conf ∈ [0,1]
    Lower dispersion -> higher stability confidence.
    """
    def comp_for_k(k: int) -> float:
        ref_sh = make_shingles(ref_tokens, k=k)
        cand_sh = make_shingles(cand_tokens, k=k)
        sim = jaccard(ref_sh, cand_sh)
        return compliance_from_components(sim, coverage, struct)

    c2 = comp_for_k(2)
    c3 = comp_for_k(3)
    c4 = comp_for_k(4)

    # Mean abs deviation around c3
    mad = (abs(c2 - c3) + abs(c4 - c3)) / 2.0
    # Convert MAD → stability in [0.2, 1.0]
    if mad <= 0.03:
        stability = 1.0
    elif mad <= 0.07:
        stability = 0.90
    elif mad <= 0.12:
        stability = 0.75
    elif mad <= 0.18:
        stability = 0.60
    elif mad <= 0.25:
        stability = 0.45
    else:
        stability = 0.30
    return stability, c2, c3, c4

def bootstrap_stability(ref_tokens: List[str], cand_tokens: List[str],
                        coverage: float, struct: float) -> float:
    """
    Split candidate tokens into contiguous chunks, sample combinations,
    recompute similarity-based compliance, and evaluate variance.
    Returns stability factor in [0.3, 1.0].
    """
    if len(cand_tokens) < MIN_TOKENS_FOR_BOOTSTRAP or BOOTSTRAP_CHUNKS < 3:
        return 0.7  # neutral if not enough text

    # Build contiguous chunks
    chunk_size = max(1, len(cand_tokens) // BOOTSTRAP_CHUNKS)
    chunks = [cand_tokens[i:i+chunk_size] for i in range(0, len(cand_tokens), chunk_size)]
    if len(chunks) < 3:
        return 0.7

    random.seed(RNG_SEED)
    ref_sh3 = make_shingles(ref_tokens, 3)
    base_scores = []

    for _ in range(BOOTSTRAP_SAMPLES):
        # sample ~60% of chunks preserving order
        k = max(2, math.ceil(0.6 * len(chunks)))
        idxs = sorted(random.sample(range(len(chunks)), k))
        sub_tokens = []
        for ix in idxs:
            sub_tokens.extend(chunks[ix])
        cand_sh3 = make_shingles(sub_tokens, 3)
        sim = jaccard(ref_sh3, cand_sh3)
        comp = compliance_from_components(sim, coverage, struct)
        base_scores.append(comp)

    if not base_scores:
        return 0.7

    mean = sum(base_scores) / len(base_scores)
    var = sum((x - mean) ** 2 for x in base_scores) / len(base_scores)
    sd = math.sqrt(var)

    # Map sd → stability (smaller sd → higher stability)
    if sd <= 0.02:
        return 1.0
    elif sd <= 0.05:
        return 0.90
    elif sd <= 0.08:
        return 0.75
    elif sd <= 0.12:
        return 0.60
    elif sd <= 0.18:
        return 0.45
    else:
        return 0.30

def compute_confidence(sim_k3: float, coverage: float, struct: float,
                       ref_tokens: List[str], cand_tokens: List[str]) -> Tuple[float, Dict[str, float]]:
    """
    Model-estimated confidence in the computed compliance score.
    Higher when:
      - independent signals agree,
      - results are stable across k and chunking,
      - candidate length is reasonable,
      - coverage & structure are present.
    """
    agreement = 1.0 - abs(sim_k3 - coverage)         

    k_stability, c2, c3, c4 = score_stability_across_k(ref_tokens, cand_tokens, coverage, struct)

    boot_stability = bootstrap_stability(ref_tokens, cand_tokens, coverage, struct)

    length_factor = length_reasonableness_factor(len(cand_tokens), len(ref_tokens))

    signal_quality = 0.7 * coverage + 0.3 * struct

    confidence = clamp(
        0.43 * k_stability +
        0.22 * boot_stability +
        0.15 * agreement +
        0.10 * length_factor +
        0.10 * signal_quality
    )

    debug = {
        "agreement": agreement,
        "k_stability": k_stability,
        "boot_stability": boot_stability,
        "length_factor": length_factor,
        "signal_quality": signal_quality,
        "alt_compliance_k2": c2,
        "alt_compliance_k3": c3,
        "alt_compliance_k4": c4,
    }
    return confidence, debug

def score_candidate(reference_text: str, candidate_text: str) -> Dict[str, float]:
    ref_tokens = tokenize_words(reference_text)
    cand_tokens = tokenize_words(candidate_text)

    # base signals
    ref_sh3 = make_shingles(ref_tokens, 3)
    cand_sh3 = make_shingles(cand_tokens, 3)
    sim_k3 = jaccard(ref_sh3, cand_sh3)

    cand_norm = normalize(candidate_text)
    coverage, missing_topics = topic_coverage_score(cand_norm)
    struct = structure_score(cand_norm)

    compliance = compliance_from_components(sim_k3, coverage, struct)
    confidence, dbg = compute_confidence(sim_k3, coverage, struct, ref_tokens, cand_tokens)

    # Build short reasoning note (helps auditing)
    reasons = []
    if dbg["k_stability"] >= 0.90 and dbg["boot_stability"] >= 0.90:
        reasons.append("stable across methods & chunks")
    elif dbg["k_stability"] < 0.60 or dbg["boot_stability"] < 0.60:
        reasons.append("instability observed")
    if abs(sim_k3 - coverage) <= 0.08:
        reasons.append("metrics agree")
    if dbg["length_factor"] < 0.7:
        reasons.append("length questionable")
    if coverage < 0.5:
        reasons.append("low topic coverage")
    if struct < 0.5:
        reasons.append("weak structure")
    note = "; ".join(reasons) if reasons else "balanced evidence"

    return {
        "compliance_score": compliance,
        "confidence_score": confidence,
        "shingle_similarity_k3": sim_k3,
        "topic_coverage": coverage,
        "structure_score": struct,
        "alt_compliance_k2": dbg["alt_compliance_k2"],
        "alt_compliance_k3": dbg["alt_compliance_k3"],
        "alt_compliance_k4": dbg["alt_compliance_k4"],
        "confidence_note": note,
        "missing_topics": "; ".join(missing_topics),
    }


def main():
    base = Path(BASE_DIR)
    if not base.exists():
        raise FileNotFoundError(f"Directory not found: {BASE_DIR}")

    reference_path = find_reference_file(base)
    reference_text = read_text(reference_path)

    all_txts = [p for p in base.glob("*.txt")]
    candidates = [p for p in all_txts if p.resolve() != reference_path.resolve()]

    if not candidates:
        print("No candidate policy files found (only the reference file exists).")
        return

    print(f"Reference policy: {reference_path.name}")
    print(f"Found {len(candidates)} candidate file(s). Scoring...")

    out_path = base / OUTPUT_CSV
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "file_name",
            "compliance_score_0to1",
            "confidence_score_0to1",
            "diag_shingle_similarity_k3",
            "diag_topic_coverage",
            "diag_structure_score",
            "alt_compliance_k2",
            "alt_compliance_k3",
            "alt_compliance_k4",
            "confidence_note",
            "missing_topics",
        ])

        for cand in sorted(candidates, key=lambda p: p.name.lower()):
            try:
                cand_text = read_text(cand)
                scores = score_candidate(reference_text, cand_text)
                writer.writerow([
                    cand.name,
                    f"{scores['compliance_score']:.3f}",
                    f"{scores['confidence_score']:.3f}",
                    f"{scores['shingle_similarity_k3']:.3f}",
                    f"{scores['topic_coverage']:.3f}",
                    f"{scores['structure_score']:.3f}",
                    f"{scores['alt_compliance_k2']:.3f}",
                    f"{scores['alt_compliance_k3']:.3f}",
                    f"{scores['alt_compliance_k4']:.3f}",
                    scores["confidence_note"],
                    scores["missing_topics"],
                ])
                print(
                    f"✓ {cand.name} → Compliance: {scores['compliance_score']:.3f} | "
                    f"Confidence: {scores['confidence_score']:.3f} ({scores['confidence_note']})"
                )
            except Exception as e:
                print(f"✗ {cand.name} → ERROR: {e}")

    print(f"\nDone. Results saved to: {out_path}")

if __name__ == "__main__":
    main()