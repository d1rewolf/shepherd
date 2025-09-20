# Shepherd configuration file for Ruby version
# Copy this to ~/.config/shepherd/config.rb and customize for your needs

# Browser rules: regex pattern -> [browser_path, profile_name] or just browser_path
# First matching pattern wins
BROWSER_RULES = {
  # Work profiles
  /^https:\/\/.*\.slack\.com/ => ['/usr/bin/chromium', 'Work'],
  /^https:\/\/.*\.github\.com/ => ['/usr/bin/chromium', 'Work'],
  /^https:\/\/.*\.gitlab\.com/ => ['/usr/bin/chromium', 'Work'],
  
  # Personal browsing
  /^https:\/\/mail\.google\.com/ => ['/usr/bin/chromium', 'Personal'],
  /^https:\/\/.*\.reddit\.com/ => ['/usr/bin/chromium', 'Personal'],
  /^https:\/\/.*\.twitter\.com/ => ['/usr/bin/chromium', 'Personal'],
  /^https:\/\/.*\.x\.com/ => ['/usr/bin/chromium', 'Personal'],
  
  # Banking - use separate profile for security
  /^https:\/\/.*\.chase\.com/ => ['/usr/bin/chromium', 'Banking'],
  /^https:\/\/.*\.wellsfargo\.com/ => ['/usr/bin/chromium', 'Banking'],
  /^https:\/\/.*\.bankofamerica\.com/ => ['/usr/bin/chromium', 'Banking'],
  
  # Shopping
  /^https:\/\/.*\.amazon\.com/ => ['/usr/bin/chromium', 'Shopping'],
  /^https:\/\/.*\.ebay\.com/ => ['/usr/bin/chromium', 'Shopping'],
  
  # News sites - different profile for tracking isolation
  /^https:\/\/.*\.nytimes\.com/ => ['/usr/bin/chromium', 'News'],
  /^https:\/\/.*\.cnn\.com/ => ['/usr/bin/chromium', 'News'],
  /^https:\/\/.*\.bbc\.com/ => ['/usr/bin/chromium', 'News']
}

# Default browser for unmatched URLs
# Can be a string (browser path) or array [browser_path, profile_name]
DEFAULT_BROWSER = '/usr/bin/chromium'
# Or with a default profile:
# DEFAULT_BROWSER = ['/usr/bin/chromium', 'Default']

# Notification settings (optional)
ENABLE_INFO_NOTIFICATIONS = false  # Set to true to show profile routing notifications
ENABLE_ERROR_NOTIFICATIONS = false  # Set to true to show error notifications
NOTIFICATION_COMMAND = ['notify-send', 'Shepherd', '{message}', '-i', 'dialog-warning']

# Logging configuration
# Options: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
LOG_LEVEL = 'INFO'

# Automatically create browser profiles if they don't exist
# When enabled, shepherd will create the profile directory automatically
CREATE_MISSING_PROFILES = false

# Add a bookmark to the bookmarks bar showing the profile name
# Helps users identify which profile they're currently using
ADD_PROFILE_BOOKMARK = false