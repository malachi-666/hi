import sys
from pathlib import Path

# Ensure src modules can be imported
sys.path.append(str(Path(__file__).parent.parent))

from src.flip_scraper import evaluate_pennies_on_dollar_gate, extract_liquidity_pressure

def run_diagnostic():
    # Synthetic Payload Data
    intrinsic_value = 300.0
    listed_price = 40.0
    description = "eviction notice today, wife says it needs gone ASAP, take it all"

    # 1. Test the 15% ROI Gate
    passed_gate = evaluate_pennies_on_dollar_gate(listed_price, intrinsic_value)

    # 2. Test NLP Desperation Logic
    pressure_status = extract_liquidity_pressure(description)

    # 3. Calculate Arbitrage Spread
    surplus_margin = intrinsic_value - listed_price

    # Assertions
    assert passed_gate == True, f"ROI Gate Failed! Listed: {listed_price}, 15% of {intrinsic_value} is {intrinsic_value * 0.15}"
    assert pressure_status == "CRITICAL DISTRESS (Divorce/Eviction)", f"NLP Trigger Failed! Got: {pressure_status}"
    assert surplus_margin == 260.0, f"Surplus Margin Calculation Failed! Got: {surplus_margin}"

    # Print High-Contrast Terminal Confirmation
    print("\033[92m[+] PANOPTICON DIAGNOSTIC GREEN: Liquidity Crisis Detected & Gated.\033[0m")
    print(f"    -> Intrinsic: ${intrinsic_value} | Listed: ${listed_price}")
    print(f"    -> Surplus Margin Confirmed: ${surplus_margin}")
    print(f"    -> NLP Designation: {pressure_status}")

if __name__ == "__main__":
    try:
        run_diagnostic()
    except AssertionError as e:
        print(f"\033[91m[-] PANOPTICON DIAGNOSTIC FAILED:\033[0m {e}")
        sys.exit(1)
