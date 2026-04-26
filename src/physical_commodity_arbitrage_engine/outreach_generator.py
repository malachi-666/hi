def generate_pitch(title: str, hardware_class: str, local_price: float) -> str:
    """
    Generates a tailored, consumer-facing negotiation script.
    Emphasizes e-waste compliance and zero-cost haul-away solutions.
    """
    if local_price == 0:
        price_hook = "I saw you're offering this for free/hauling."
        offer = "I can be there today to haul it away at zero cost to you."
    else:
        price_hook = f"I saw you have this listed for ${local_price:,.2f}."
        # Lowballing strategy based on local pickup convenience
        target_offer = local_price * 0.6 if local_price > 50 else local_price - 10
        offer = f"I'm a local buyer and can do ${max(0, target_offer):,.0f} cash in hand today if we can make it quick."

    if hardware_class == "Heavy Infrastructure":
         compliance_note = "We specialize in safely decommissioning enterprise hardware. I can ensure this heavy infrastructure is removed safely, preventing it from ending up in a landfill, and handle the logistics so you don't have to lift a finger."
    elif hardware_class == "Laptop":
         compliance_note = "If you have any concerns about data, we strictly follow DoD data wiping protocols for all mobile hardware before recycling or repurposing."
    else:
         compliance_note = "We focus on e-waste compliance and keeping raw hardware out of landfills through direct localized recycling and repurposing."

    pitch = f"""Hey there,

{price_hook} I'm very interested in the {title}.

{compliance_note}

{offer} Let me know if that works for you, and I can swing by whenever is convenient.

Thanks,
[Your Name]"""

    return pitch

if __name__ == "__main__":
    print(generate_pitch("Cisco Catalyst 3850 48 Port Switch", "Heavy Infrastructure", 150.00))
