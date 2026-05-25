"""ASCII art mascot and startup banner for Unagi."""


def get_ross_unagi_art() -> str:
    """Get ASCII art of Ross doing Unagi pose with eel.
    
    Returns:
        ASCII art string
    """
    return r"""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║     __  __  _  _   __   ___  _                           ║
    ║    |  \/  || \| | /  \ / __|| |                          ║
    ║    | |\/| || .` || () |\__ \| |__                        ║
    ║    |_|  |_||_|\_| \__/ |___/|____|                       ║
    ║                                                           ║
    ║         🐍 Total Food Awareness 🐍                        ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝

           .-""-.                    .-""-.
          /      \                  /      \
         |  o  o  |    UNAGI!      |  ^  ^  |
         |    >   |                |   ω   |
          \  __  /                  \  ~~  /
           '-..-'                    '-..-'
             ||                        ||
            /||\                      /||\
           / || \                    / || \
          Ross Geller              Unagi Eel
       (State of Total            (Your Nutrition
         Awareness)                  Companion)
"""


def get_startup_banner(user_name: str = None, last_log: str = None) -> str:
    """Get formatted startup banner with user info.
    
    Args:
        user_name: User's name (optional)
        last_log: Last log summary (optional)
        
    Returns:
        Formatted banner string
    """
    from datetime import datetime
    
    today = datetime.now().strftime("%A, %d %B %Y")
    
    banner = get_ross_unagi_art()
    banner += "\n"
    banner += f"    Today: {today}\n"
    
    if user_name:
        banner += f"    Welcome back, {user_name}! 👋\n"
    
    if last_log:
        banner += f"    {last_log}\n"
    
    banner += "\n"
    banner += "    Type your food log or ask me anything.\n"
    banner += "    Special commands: /help /today /week /profile /exit\n"
    banner += "    " + "─" * 55 + "\n"
    
    return banner


def get_help_text() -> str:
    """Get help text for available commands.
    
    Returns:
        Help text string
    """
    return """
╔═══════════════════════════════════════════════════════════╗
║                    UNAGI HELP                             ║
╚═══════════════════════════════════════════════════════════╝

📝 LOGGING FOOD
  Just tell me what you ate naturally:
  • "I had breakfast at 1 PM: 10 almonds, 200ml green tea..."
  • "Log today's dinner: 450g chicken breast, 150g yogurt..."
  • "Update yesterday: I forgot to add 2 boiled eggs"

💬 ASKING QUESTIONS
  • "How have I been doing this week?"
  • "Am I hitting my protein goal?"
  • "What should I eat tonight to fix my Vitamin D deficit?"

⚡ SPECIAL COMMANDS
  /help      Show this help message
  /today     Show today's log summary
  /week      Show last 7 days summary
  /profile   Show your user profile
  /config    Show current configuration
  /exit      Quit Unagi

📊 UNDERSTANDING YOUR LOGS
  • Deficit = Calories consumed - Maintenance
  • Negative deficit = You're in a caloric deficit (cutting)
  • Positive deficit = You're in a surplus (bulking)
  • All 29 micronutrients are tracked automatically

🎯 TIPS
  • Specify raw weight with (r): "450g chicken breast (r)"
  • Mention brand names when known: "Amul Masti Dahi"
  • Include meal times: "Breakfast at 1 PM"
  • Be specific about quantities for better accuracy

Type anything to continue...
"""


def get_goodbye_message() -> str:
    """Get goodbye message when exiting.
    
    Returns:
        Goodbye message string
    """
    return """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║              Thanks for using UNAGI! 🐍                   ║
    ║                                                           ║
    ║         Stay aware. Stay healthy. Stay strong.           ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝

    All your food logs are safely stored in your Obsidian vault
    and committed to Git. See you next time!
"""


def get_error_banner(error_type: str) -> str:
    """Get formatted error banner.
    
    Args:
        error_type: Type of error (e.g., "Configuration", "LLM", "Git")
        
    Returns:
        Error banner string
    """
    return f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║  ⚠️  {error_type.upper()} ERROR                           
    ╚═══════════════════════════════════════════════════════════╝
"""

# Made with Bob
