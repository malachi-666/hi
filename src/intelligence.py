import json
import requests
import re

OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
MODEL_NAME = "sovereign-ai"

def analyze_listing(title, description, category):
    """
    Sends the listing description to a local LLM via Ollama to perform forensic sentiment analysis.
    Extracts Condition Score (1-10) and Hidden Gem status.
    """
    if not description or len(description) < 10:
        return {"condition_score": 5, "hidden_gem": False, "ai_notes": "Insufficient description."}

    prompt = f"""
    You are an expert appraiser and forensic analyst for physical commodities in the {category} sector.
    Analyze the following second-hand market listing.

    Title: {title}
    Description: {description}

    Tasks:
    1. Condition Score: Rate the functional condition from 1 (broken/parts) to 10 (mint/new).
    2. Hidden Gem: Is this item mislabeled by the seller (e.g. they don't know what they have)? Reply TRUE or FALSE.
    3. Notes: Provide a 1-sentence reason for the score.

    Format the output EXACTLY as valid JSON with keys: "condition_score" (int), "hidden_gem" (bool), "ai_notes" (string).
    """

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }

    try:
        response = requests.post(OLLAMA_ENDPOINT, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()

        result_text = data.get('response', '{}')
        parsed = json.loads(result_text)

        score = int(parsed.get("condition_score", 5))
        gem = bool(parsed.get("hidden_gem", False))
        notes = str(parsed.get("ai_notes", "Analysis complete."))

        return {"condition_score": score, "hidden_gem": gem, "ai_notes": notes}

    except Exception as e:
        score = 5
        gem = False
        notes = f"AI Offline fallback used."

        desc_lower = description.lower()
        if re.search(r'(broken|parts|wont start)', desc_lower):
            score = 2
        elif re.search(r'(brand new|sealed|mint)', desc_lower):
            score = 10
        elif re.search(r'(junk|cleaning out)', desc_lower):
            gem = True

        return {"condition_score": score, "hidden_gem": gem, "ai_notes": notes}
