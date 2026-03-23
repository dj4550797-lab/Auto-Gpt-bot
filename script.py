class script(object):
    START_TXT = "👋 Hello {name}, I am **FLIXORA AI** 🤖\n\nAn advanced JARVIS-style assistant. How can I help you today?"
    HELP_TXT = "**Help Menu**\n- Send me any message to chat.\n- Use /register to sign up.\n- Use /upgrade for Premium."
    ABOUT_TXT = "**About FLIXORA AI**\nPowered by OpenRouter. Built for high performance and stability."
    TOP_SEARCH_TXT = "⭐ **Top Searching**\nCurrently trending topics..."
    VERIFY_TXT = "🔒 **Complete verification to continue.**\n\nYou need to verify your access every 24 hours.\n👉 [Click here to Verify]({short_url})"

    # --- ENHANCED PREMIUM SECTION ---

    PREMIUM_INFO_TXT = """
🚀 **Unlock the Full Power of FLIXORA AI with Premium!**

Upgrading removes all restrictions and gives you the ultimate AI experience.

✅ **Premium Benefits:**
- **No More Ads or Links:** Enjoy a clean, uninterrupted experience.
- **Unlimited Access:** No 24-hour verification required.
- **Priority Speed:** Get faster responses from the AI.
- **Exclusive AI Models:** Access to the most powerful models.
- **Longer Memory:** The AI remembers more of your conversation.
"""

    PREMIUM_PLANS_TXT = """
👇 **Choose a Plan That's Right For You:**

Select a plan below to see payment details. All plans unlock the same great features.
"""

    # This text is now dynamic and will be formatted with plan details
    UPGRADE_TXT = """
💎 **Confirm Your Purchase**

**Plan:** `{plan_name}`
**Amount:** `₹{amount}`

Please pay the exact amount to the UPI ID or scan the QR code.

**UPI ID:** `{upi_id}`

After payment, use the `/submit_payment` command to send us the UTR number and a screenshot.
"""