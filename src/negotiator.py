def generate_negotiation_template(title, listed_price, pressure):
    """
    Generates two specific text blocks (Blitz vs. Professional) based on listing data.
    """
    item_short = title.split()[0] if title else "item"

    # Template 1: The "Blitz" Template
    if listed_price == 0:
        blitz = f"Hey! I'm in Bluffdale and can be there in 15 minutes with a truck. Is the {item_short} still available? I can take it right now."
    elif pressure == "Distressed (Fixer/Moving)":
        blitz = f"Saw you're trying to get rid of the {item_short}. I'm in Bluffdale and can bring ${listed_price} cash right now so you don't have to deal with it. Let me know."
    else:
        blitz = f"Hi, I can do ${listed_price} cash today and pick it up immediately. Are you available?"

    # Template 2: The "Professional" Template
    professional = f"Hello, I'm a local buyer interested in the {title}. I'm prepared to pay your asking price of ${listed_price} cash. Before I head over, are there any functional issues or cosmetic damage I should be aware of?"

    return {
        "blitz": blitz,
        "professional": professional
    }
