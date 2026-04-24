import apprise
import subprocess

def trigger_strike_notification(asset_data):
    """
    Evaluates asset data and sends notifications.
    Plays a physical audio trigger for High-Priority strikes.
    Atomic DB checks in src/database.py guarantee this is only called once per URL.
    """
    margin = asset_data.get('predicted_profit_margin', 0)
    listed = asset_data.get('listed_price', 0)

    title = f"ALPHASTRIKE [{asset_data['platform']}]: {asset_data['title']}"
    body = f"Listed: ${listed} | Profit: ${margin}\nPressure: {asset_data.get('liquidity_pressure', 'Normal')}\nLink: {asset_data['url']}"

    apobj = apprise.Apprise()
    # To expand: apobj.add('discord://webhook_id/webhook_token')

    # Desktop Notification via notify-send (Native to Kali/Debian)
    try:
        subprocess.run(['notify-send', '-u', 'critical', title, body], check=False)
    except FileNotFoundError:
        pass

    # Economic Urgency Condition: FREE and high margin
    is_critical = (listed == 0.0 and margin >= 150.0)

    if is_critical:
        print(f"\n🚨 [URGENT] HIGH-VALUE ZERO-COST TARGET: {asset_data['title']}")
        try:
            # Standard Kali alarm path
            subprocess.run(['paplay', '/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga'], check=False)
        except FileNotFoundError:
            print('\a') # Fallback terminal beep

    # Fire external webhooks
    try:
        apobj.notify(body=body, title=title)
    except Exception as e:
        print(f"Apprise notification failed: {e}")
