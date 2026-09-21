import json
from backend.app.services.generators.base import ContentGenerator

class MockContentGenerator(ContentGenerator):
    def generate(self, brief: dict) -> dict[str, str]:
        title = brief.get("title", "Comprehensive Product Guide")
        primary_keyword = brief.get("primary_keyword") or "skincare essentials"
        target_audience = brief.get("target_audience", "skincare shoppers")
        suggested_angle = brief.get("suggested_angle", "practical consumer guide")

        # Parse sections if stored as json string or list
        raw_sections = brief.get("suggested_sections", [])
        if isinstance(raw_sections, str):
            try:
                sections = json.loads(raw_sections)
            except Exception:
                sections = []
        else:
            sections = list(raw_sections)

        if not sections:
            sections = [
                "Understanding the Fundamentals",
                "Key Benefits & Mechanisms",
                "How to Incorporate into Your Daily Routine",
                "Compatibility & Routine Pairing",
                "Common Misconceptions & Expert Tips"
            ]

        introduction = (
            f"When considering {primary_keyword}, having clear, evidence-based guidance makes all the difference. "
            f"Tailored for {target_audience.lower()}, this {suggested_angle} breaks down how to optimize your daily routine, "
            f"highlighting practical benefits and thoughtful usage without unnecessary complexity."
        )

        body_parts = [f"# {title}\n"]
        for idx, section in enumerate(sections, 1):
            body_parts.append(f"## {idx}. {section}\n")
            if "understanding" in section.lower() or "fundamentals" in section.lower():
                body_parts.append(
                    f"At its core, {primary_keyword} addresses fundamental skin balance and hydration. "
                    "Understanding ingredient concentrations and formulation stability ensures you select products "
                    "that harmonize with your skin's natural barrier.\n"
                )
            elif "benefit" in section.lower():
                body_parts.append(
                    f"Targeted use of {primary_keyword} supports a visibly refreshed, revitalized complexion. "
                    "Consistent daily application enhances texture, promotes moisture retention, and helps maintain resilience against everyday environmental stressors.\n"
                )
            elif "routine" in section.lower() or "incorporate" in section.lower():
                body_parts.append(
                    "For best results, apply after cleansing and toning, and before heavier creams or sunscreens. "
                    "Dispense 3-4 drops and gently press into damp skin. Always patch-test new formulations prior to full application.\n"
                )
            elif "compatibility" in section.lower() or "pairing" in section.lower():
                body_parts.append(
                    "Synergistic pairing is key to maximizing results. Ensure compatible pH levels and layer lighter, "
                    "water-based formulas first. Avoid combining potent exfoliants in the same immediate step unless specifically formulated to work together.\n"
                )
            else:
                body_parts.append(
                    f"Focusing on quality and consistent habits yields the most noticeable outcomes. Pay attention to how your skin responds over a 4-to-6 week cycle, "
                    f"adjusting frequency according to seasonal changes and personal tolerance.\n"
                )

        body_parts.append(
            "> *Disclaimer: This informational article does not constitute personal medical diagnosis. Always consult a dermatologist or healthcare provider regarding specific skin conditions.*"
        )
        body = "\n".join(body_parts)

        conclusion = (
            f"Incorporating {primary_keyword} thoughtfully into your routine provides a steady foundation for healthy, radiant skin. "
            "Prioritize balanced formulations, adhere to consistent application, and choose products that support your unique skin goals."
        )

        return {
            "title": title,
            "introduction": introduction,
            "body": body,
            "conclusion": conclusion
        }
