import json
import os
import urllib.request
import urllib.error

API_KEY = os.environ.get("TYPESAFE_API_KEY")
if not API_KEY:
    # Try loading from .env file
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip()
        API_KEY = os.environ.get("TYPESAFE_API_KEY")

if not API_KEY:
    print("Error: Set TYPESAFE_API_KEY in .env or environment")
    exit(1)

API_URL = "https://api.typesafe.ai/v1/systemone"


def analyze(description: str, price: str = "") -> dict:
    state = f"Fashion item: {description}"
    if price:
        state += f"\nPrice: {price}"

    payload = {
        "state": state,
        "model": "jev-latest",
        "questions": {
            "cost_per_wear": {
                "type": "score",
                "instructions": "How often would someone realistically wear this item? Consider versatility across occasions, seasons, and outfit combinations. Higher means more wearable and better cost-per-wear value.",
                "criteria": [
                    "Rarely — special occasion only, maybe 1-2 times a year",
                    "Sometimes — specific situations, maybe monthly",
                    "Regularly — weekly rotation piece",
                    "Constantly — could wear multiple times a week across many contexts",
                ],
            },
            "trend_vs_timeless": {
                "type": "score",
                "instructions": "Is this item trendy and likely to feel dated soon, or is it a timeless piece that will still look good in 2+ years?",
                "criteria": [
                    "Very trendy — will look dated within a season",
                    "Somewhat trendy — riding a current wave",
                    "Classic with a modern twist",
                    "Timeless — would look good in any decade",
                ],
            },
            "material_quality": {
                "type": "score",
                "instructions": "Based on the described materials and construction, how is the quality and sustainability? Consider natural vs synthetic fibers, organic/sustainable sourcing, durability.",
                "criteria": [
                    "Poor — cheap synthetics, polyester, plastic-based, fast fashion quality",
                    "Below average — synthetic blends, basic construction",
                    "Good — decent materials, some natural fibers",
                    "Excellent — high-quality natural fibers, organic, sustainable, built to last",
                ],
            },
            "dopamine_vs_love": {
                "type": "score",
                "instructions": "Does this sound like an impulse purchase driven by momentary excitement, or a thoughtful addition that fills a real wardrobe need?",
                "criteria": [
                    "Pure dopamine — impulse buy, novelty-driven",
                    "Mostly excitement — fun but not needed",
                    "Considered — some thought went into this",
                    "Genuine love — fills a real gap, intentional purchase",
                ],
            },
            "closet_redundancy": {
                "type": "score",
                "instructions": "Based on the description, how likely is it that someone already owns something very similar? Consider how common/basic vs unique this item is.",
                "criteria": [
                    "Very unique — unlikely to already own anything like it",
                    "Somewhat distinct — might have something vaguely similar",
                    "Common — probably owns something similar already",
                    "Highly redundant — almost certainly a duplicate of something owned",
                ],
            },
            "verdict": {
                "type": "choice",
                "instructions": "Based on the overall assessment of cost-per-wear, trendiness, material quality, purchase intention, and redundancy — should this item be kept or returned?",
                "criteria": {
                    "keep": "Worth keeping — good value, quality, and fills a wardrobe need",
                    "return": "Should return — poor value, trendy, low quality, or redundant",
                    "sleep_on_it": "On the fence — not clearly a keep or return, think about it for a day",
                },
            },
        },
    }

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"API error ({e.code}): {error_body}")
        exit(1)


def display_bar(label: str, levels: list, result: dict):
    """Display a score result as a visual bar."""
    probs = result.get("probabilities", {})
    score = result.get("score", 0)
    confidence = result.get("confidence", 0)

    # Find the level closest to the score
    best = round(score)

    print(f"\n  {label} (score: {score:.1f}, confidence: {confidence*100:.0f}%)")
    for i, level in enumerate(levels):
        prob = probs.get(str(i), 0)
        bar_len = int(prob * 30)
        bar = "█" * bar_len + "░" * (30 - bar_len)
        marker = " ◀" if i == best else ""
        print(f"    {bar} {prob*100:4.0f}%  {level}{marker}")


def display_choice(label: str, options: dict, result: dict):
    """Display a choice result."""
    answer = result.get("choice", "")
    probs = result.get("probabilities", {})
    confidence = result.get("confidence", 0)

    print(f"\n  {label} (confidence: {confidence*100:.0f}%)")
    for key, desc in options.items():
        prob = probs.get(key, 0)
        bar_len = int(prob * 30)
        bar = "█" * bar_len + "░" * (30 - bar_len)
        marker = " ◀" if key == answer else ""
        print(f"    {bar} {prob*100:4.0f}%  {desc}{marker}")


def main():
    print("\n╔══════════════════════════════════╗")
    print("║       KEEP OR RETURN?            ║")
    print("╚══════════════════════════════════╝\n")

    description = input("Describe the item (what is it, color, material, brand, etc.):\n> ")
    price = input("\nPrice (optional, press enter to skip):\n> ")

    print("\nAnalyzing...")
    result = analyze(description, price)

    answers = result.get("answers", result)

    score_questions = {
        "cost_per_wear": {
            "label": "COST PER WEAR",
            "levels": ["Rarely worn", "Sometimes", "Regularly", "Constantly"],
        },
        "trend_vs_timeless": {
            "label": "TREND vs TIMELESS",
            "levels": ["Very trendy", "Somewhat trendy", "Modern classic", "Timeless"],
        },
        "material_quality": {
            "label": "MATERIAL QUALITY",
            "levels": ["Poor / synthetic", "Below average", "Good", "Excellent / sustainable"],
        },
        "dopamine_vs_love": {
            "label": "DOPAMINE vs LOVE",
            "levels": ["Pure impulse", "Mostly excitement", "Considered", "Genuine love"],
        },
        "closet_redundancy": {
            "label": "CLOSET REDUNDANCY",
            "levels": ["Very unique", "Somewhat distinct", "Common", "Highly redundant"],
        },
    }

    print("\n" + "─" * 50)

    for key, config in score_questions.items():
        if key in answers:
            display_bar(config["label"], config["levels"], answers[key])

    if "verdict" in answers:
        print("\n" + "═" * 50)
        display_choice(
            "VERDICT",
            {"keep": "Keep it", "return": "Return it", "sleep_on_it": "Sleep on it"},
            answers["verdict"],
        )
        print("═" * 50)

    print()


if __name__ == "__main__":
    main()
