import math
import re
import sqlite3
from typing import Any

def _count_syllables(word: str) -> int:
    """Heuristic syllable counter for English words."""
    word = word.lower().strip()
    if not word:
        return 0
    if len(word) <= 3:
        return 1

    # Remove non-alpha
    word = re.sub(r"[^a-z]", "", word)
    if not word:
        return 0

    # Count vowel groups
    vowels = "aeiouy"
    count = 0
    prev_is_vowel = False
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_is_vowel:
            count += 1
        prev_is_vowel = is_vowel

    # Adjust for silent 'e' at the end
    if word.endswith("e") and not word.endswith("le") and count > 1:
        count -= 1

    return max(1, count)

class QualityCheckService:
    """
    Performs comprehensive pre-publication SEO, readability, product linking,
    and brand safety audits on content drafts.
    """

    def audit_draft(self, conn: sqlite3.Connection, draft: dict[str, Any], store_id: str | None = None) -> dict[str, Any]:
        title = draft.get("title", "")
        primary_kw = (draft.get("primary_keyword") or "").lower().strip()
        intro = draft.get("introduction", "")
        body = draft.get("body", "")
        conclusion = draft.get("conclusion", "")

        full_text = f"{title}\n\n{intro}\n\n{body}\n\n{conclusion}".strip()

        # Word & Sentence tokenization
        words = re.findall(r"\b[a-zA-Z0-9'\-]+\b", full_text)
        word_count = len(words)
        sentences = [s.strip() for s in re.split(r"[.!?]+", full_text) if s.strip()]
        sentence_count = max(1, len(sentences))

        checks: list[dict[str, Any]] = []
        warnings: list[str] = []
        score = 100

        # ---------------------------------------------------------------------
        # 1. SEO Integrity Checks
        # ---------------------------------------------------------------------
        if primary_kw:
            # Keyword in Title
            in_title = primary_kw in title.lower()
            checks.append({
                "name": "Keyword in Title",
                "category": "seo",
                "passed": in_title,
                "message": f"Primary keyword '{primary_kw}' is present in the title." if in_title
                           else f"Primary keyword '{primary_kw}' is missing from the title."
            })
            if not in_title:
                score -= 15
                warnings.append("Include your primary keyword near the beginning of the title.")

            # Keyword in Introduction
            in_intro = primary_kw in intro.lower()
            checks.append({
                "name": "Keyword in Introduction",
                "category": "seo",
                "passed": in_intro,
                "message": "Keyword appears in the opening introduction section." if in_intro
                           else "Keyword is missing from the introduction."
            })
            if not in_intro:
                score -= 10
                warnings.append("Mention your primary keyword within the first paragraph.")

            # Keyword in Headings
            headings = re.findall(r"^#{1,4}\s+(.+)$", body, flags=re.MULTILINE)
            in_headings = any(primary_kw in h.lower() for h in headings)
            checks.append({
                "name": "Keyword in Headings",
                "category": "seo",
                "passed": in_headings,
                "message": f"Found primary keyword in at least one section heading ({len(headings)} headings detected)." if in_headings
                           else "None of the section headings contain the primary keyword."
            })
            if not in_headings and headings:
                score -= 10
                warnings.append("Include the primary keyword or a close variant in at least one H2/H3 heading.")

            # Keyword Density
            kw_tokens = primary_kw.split()
            kw_occurrences = len(re.findall(re.escape(primary_kw), full_text.lower()))
            density = round((kw_occurrences * len(kw_tokens) / max(1, word_count)) * 100, 2)
            density_optimal = 0.3 <= density <= 7.0
            checks.append({
                "name": "Keyword Density",
                "category": "seo",
                "passed": density_optimal,
                "value": f"{density}% ({kw_occurrences} occurrences)",
                "message": f"Keyword density is optimal at {density}%." if density_optimal
                           else f"Keyword density is {density}%. Recommended range is 0.5% to 5.0%."
            })
            if not density_optimal:
                score -= 10
                if density < 0.3:
                    warnings.append(f"Keyword density ({density}%) is quite low; consider naturally repeating the topic.")
                else:
                    warnings.append(f"Keyword density ({density}%) may appear keyword-stuffed; consider using synonyms.")
        else:
            checks.append({
                "name": "Primary Keyword Assigned",
                "category": "seo",
                "passed": False,
                "message": "No primary keyword assigned to this draft."
            })
            score -= 20
            warnings.append("Assign a target primary search query for SEO optimization.")

        # ---------------------------------------------------------------------
        # 2. Content Length
        # ---------------------------------------------------------------------
        length_ok = word_count >= 100
        checks.append({
            "name": "Content Word Count",
            "category": "readability",
            "passed": length_ok,
            "value": f"{word_count} words",
            "message": f"Article length is substantial ({word_count} words)." if length_ok
                       else f"Article length is brief ({word_count} words). 100+ words recommended."
        })
        if not length_ok:
            score -= 15
            warnings.append("Expand the draft with more practical steps or FAQ sections.")

        # ---------------------------------------------------------------------
        # 3. Readability Analysis (Flesch Reading Ease)
        # ---------------------------------------------------------------------
        total_syllables = sum(_count_syllables(w) for w in words)
        words_per_sentence = word_count / sentence_count
        syllables_per_word = total_syllables / max(1, word_count)

        flesch_score = round(206.835 - (1.015 * words_per_sentence) - (84.6 * syllables_per_word), 1)
        # Grade level
        fk_grade = round((0.39 * words_per_sentence) + (11.8 * syllables_per_word) - 15.59, 1)

        readability_ok = flesch_score >= 35.0
        checks.append({
            "name": "Flesch Reading Ease",
            "category": "readability",
            "passed": readability_ok,
            "value": f"{flesch_score} (Grade {fk_grade})",
            "message": f"Readability score is {flesch_score} (Grade {fk_grade}). Accessible to general shoppers." if readability_ok
                       else f"Readability score is {flesch_score} (Grade {fk_grade}). Copy may be too dense."
        })
        if not readability_ok:
            score -= 10
            warnings.append("Simplify complex sentences and break long paragraphs into shorter statements.")

        # ---------------------------------------------------------------------
        # 4. Store Product Mentions & Integration
        # ---------------------------------------------------------------------
        target_store_id = store_id or "demo-store"
        products = conn.execute(
            "SELECT id, name, handle FROM products WHERE store_id = ? LIMIT 100",
            (target_store_id,)
        ).fetchall()

        matched_products: list[str] = []
        for p in products:
            p_name = p["name"].strip()
            if len(p_name) >= 4 and p_name.lower() in full_text.lower():
                matched_products.append(p_name)

        has_product_link = bool(matched_products) or "product" in full_text.lower()
        checks.append({
            "name": "Catalog Product Integration",
            "category": "ecommerce",
            "passed": has_product_link,
            "value": f"{len(matched_products)} products mentioned" if matched_products else "No catalog products mentioned",
            "message": f"Article highlights store merchandise: {', '.join(matched_products[:3])}" if matched_products
                       else "No specific catalog products are linked or mentioned in the copy."
        })
        if not has_product_link:
            score -= 10
            warnings.append("Add a direct product recommendation or link to relevant merchandise.")

        # ---------------------------------------------------------------------
        # 5. Safety & Disclaimers
        # ---------------------------------------------------------------------
        has_disclaimer = bool(
            re.search(r"\b(disclaimer|consult|medical|advice|professional|physician|results may vary)\b", full_text, re.IGNORECASE)
        )
        checks.append({
            "name": "Brand Safety & Disclaimers",
            "category": "compliance",
            "passed": has_disclaimer,
            "message": "Appropriate health/routine disclaimer or cautionary advice is present." if has_disclaimer
                       else "No disclaimer or advisory note found in conclusion."
        })
        if not has_disclaimer:
            score -= 5
            warnings.append("Consider adding a standard advisory note or customer disclaimer in the conclusion.")

        final_score = max(10, min(100, score))

        return {
            "draft_id": draft.get("id"),
            "score": final_score,
            "grade": "Excellent" if final_score >= 85 else "Good" if final_score >= 70 else "Needs Improvement",
            "word_count": word_count,
            "sentence_count": sentence_count,
            "reading_ease": flesch_score,
            "grade_level": fk_grade,
            "checks": checks,
            "warnings": warnings,
            "matched_products": matched_products,
        }

quality_check_service = QualityCheckService()
