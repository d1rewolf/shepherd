"""
Shepherd configuration file
Copy this to ~/.config/shepherd/config.py and customize for your needs
"""

# Browser rules: regex pattern -> (browser_path, profile_name) or just browser_path
# First matching pattern wins
BROWSER_RULES = {
    # Work profiles
    r"^https://outlook\.office\.com": ("/usr/bin/chromium", "Work"),
    r"^https://.*\.slack\.com": ("/usr/bin/chromium", "Work"),
    
    # Personal browsing
    r"^https://mail\.google\.com": ("/usr/bin/chromium", "Personal"),
    r"^https://.*\.reddit\.com": ("/usr/bin/chromium", "Personal"),
    
    # Banking - use separate profile for security
    r"^https://.*\.(chase|wellsfargo|bankofamerica)\.com": ("/usr/bin/chromium", "Banking"),
    
    # Streaming/TV
    r"^https://tv\.youtube\.com": ("/usr/bin/chromium", "TV"),
    r"^https://.*\.netflix\.com": ("/usr/bin/chromium", "TV"),
}

# Default browser for unmatched URLs
DEFAULT_BROWSER = "/usr/bin/chromium"

# Or with a specific profile for unmatched URLs:
# DEFAULT_BROWSER = ("/usr/bin/chromium", "Personal")

# Notification settings (optional)
# Set to True to get desktop notifications when profiles or browsers aren't found
ENABLE_NOTIFICATIONS = False

# Command to use for notifications - {message} will be replaced with the error message
NOTIFICATION_COMMAND = ['notify-send', 'Shepherd', '{message}', '-i', 'dialog-warning']

# You can customize this to use any notification system:
# NOTIFICATION_COMMAND = ['dunstify', '-a', 'Shepherd', '{message}']
# NOTIFICATION_COMMAND = ['zenity', '--notification', '--text={message}']