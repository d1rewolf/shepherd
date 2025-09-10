#!/usr/bin/env python3
"""
shepherd.py - Smart URL router for browser profiles
https://github.com/d1rewolf/shepherd
"""

from __version__ import __version__
import json
import os
import re
import subprocess
import sys
import importlib.util
import logging
from datetime import datetime
from pathlib import Path

# Set up logging following XDG Base Directory specification
def setup_logging(log_level_str="INFO"):
    """Set up logging to XDG_STATE_HOME/shepherd/shepherd.log"""
    xdg_state_home = os.environ.get('XDG_STATE_HOME', Path.home() / '.local' / 'state')
    log_dir = Path(xdg_state_home) / 'shepherd'
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'shepherd.log'
    
    # Convert string log level to logging constant
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stderr)  # Keep stderr output for debugging
        ]
    )
    return logging.getLogger(__name__)


def load_config():
    """Load configuration from ~/.config/shepherd/config.py or use defaults."""
    config_dir = Path.home() / ".config" / "shepherd"
    config_file = config_dir / "config.py"
    
    # Default configuration
    default_rules = {
        r"^https://example\.com": ("/usr/bin/chromium", "Default"),
    }
    default_browser = "/usr/bin/chromium"
    default_enable_info_notifications = False
    default_enable_error_notifications = False
    default_notification_command = ['notify-send', 'Shepherd', '{message}', '-i', 'dialog-warning']
    default_log_level = "INFO"
    default_create_missing_profiles = False
    
    if config_file.exists():
        try:
            # Load config.py as a module
            spec = importlib.util.spec_from_file_location("shepherd_config", config_file)
            config = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config)
            
            # Get configuration from the module
            browser_rules = getattr(config, 'BROWSER_RULES', default_rules)
            default_browser = getattr(config, 'DEFAULT_BROWSER', default_browser)
            
            # Handle backward compatibility: if ENABLE_NOTIFICATIONS exists, use it for error notifications
            enable_notifications = getattr(config, 'ENABLE_NOTIFICATIONS', None)
            enable_info_notifications = getattr(config, 'ENABLE_INFO_NOTIFICATIONS', default_enable_info_notifications)
            enable_error_notifications = getattr(config, 'ENABLE_ERROR_NOTIFICATIONS', 
                                                 enable_notifications if enable_notifications is not None else default_enable_error_notifications)
            
            notification_command = getattr(config, 'NOTIFICATION_COMMAND', default_notification_command)
            log_level = getattr(config, 'LOG_LEVEL', default_log_level)
            create_missing_profiles = getattr(config, 'CREATE_MISSING_PROFILES', default_create_missing_profiles)
            
            return browser_rules, default_browser, enable_info_notifications, enable_error_notifications, notification_command, log_level, create_missing_profiles
        except Exception as e:
            print(f"Error loading config from {config_file}: {e}", file=sys.stderr)
            print("Using default configuration", file=sys.stderr)
    else:
        # Create config directory and example config if it doesn't exist
        if not config_dir.exists():
            config_dir.mkdir(parents=True, exist_ok=True)
            print(f"Created config directory: {config_dir}", file=sys.stderr)
            
            # Create example config
            example_config = config_dir / "config.example.py"
            if not example_config.exists():
                example_content = r'''"""
Shepherd configuration file
Rename this to config.py and customize for your needs
"""

# Browser rules: regex pattern -> (browser_path, profile_name) or just browser_path
# First matching pattern wins
BROWSER_RULES = {
    # Work profiles
    r"^https://.*\.slack\.com": ("/usr/bin/chromium", "Work"),
    
    # Personal browsing
    r"^https://mail\.google\.com": ("/usr/bin/chromium", "Personal"),
    
    # Banking - use separate profile for security
    r"^https://.*\.chase\.com": ("/usr/bin/chromium", "Banking"),
}

# Default browser for unmatched URLs
DEFAULT_BROWSER = "/usr/bin/chromium"

# Notification settings (optional)
ENABLE_INFO_NOTIFICATIONS = False  # Set to True to show profile routing notifications
ENABLE_ERROR_NOTIFICATIONS = False  # Set to True to show error notifications
NOTIFICATION_COMMAND = ['notify-send', 'Shepherd', '{message}', '-i', 'dialog-warning']

# Logging configuration
# Options: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
LOG_LEVEL = "INFO"

# Automatically create browser profiles if they don't exist
# When enabled, shepherd will use the profile name as the directory name
CREATE_MISSING_PROFILES = False
'''
                example_config.write_text(example_content)
                print(f"Created example config: {example_config}", file=sys.stderr)
                print(f"Copy {example_config} to {config_file} and customize it", file=sys.stderr)
    
    return default_rules, default_browser, default_enable_info_notifications, default_enable_error_notifications, default_notification_command, default_log_level, default_create_missing_profiles


# Load configuration
BROWSER_RULES, DEFAULT_BROWSER, ENABLE_INFO_NOTIFICATIONS, ENABLE_ERROR_NOTIFICATIONS, NOTIFICATION_COMMAND, LOG_LEVEL, CREATE_MISSING_PROFILES = load_config()

# Initialize logging with configured log level
logger = setup_logging(LOG_LEVEL)


def send_info_notification(message):
    """Send an info desktop notification if enabled."""
    if ENABLE_INFO_NOTIFICATIONS and NOTIFICATION_COMMAND:
        try:
            # Replace {message} placeholder in the command
            cmd = [arg.replace('{message}', message) for arg in NOTIFICATION_COMMAND]
            subprocess.run(cmd, check=False, capture_output=True)
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")


def send_error_notification(message):
    """Send an error desktop notification if enabled."""
    if ENABLE_ERROR_NOTIFICATIONS and NOTIFICATION_COMMAND:
        try:
            # Replace {message} placeholder in the command
            cmd = [arg.replace('{message}', message) for arg in NOTIFICATION_COMMAND]
            subprocess.run(cmd, check=False, capture_output=True)
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")


def sanitize_profile_name(profile_name):
    """
    Sanitize a profile name to be safe for use as a directory name.
    
    Args:
        profile_name: The friendly name of the profile (e.g., "Work & Personal")
    
    Returns:
        Sanitized name safe for filesystem use (e.g., "Work_Personal")
    """
    if not profile_name:
        return "Default"
    
    # Replace any non-alphanumeric characters (except dash and underscore) with underscore
    safe_name = re.sub(r'[^\w\-]', '_', profile_name)
    
    # Remove leading/trailing underscores and collapse multiple underscores
    safe_name = re.sub(r'_+', '_', safe_name).strip('_')
    
    return safe_name or "Default"


def open_with_browser(browser, url_arg, chromium_profile=None, extra_args=None):
    """
    Launch the browser with the given URL or --app=URL argument.
    If CREATE_MISSING_PROFILES is True, will automatically create profiles by using
    the profile name as the directory name.
    
    Args:
        browser: Path to the browser executable
        url_arg: URL or --app=URL to open
        chromium_profile: Optional profile name for Chromium-based browsers
        extra_args: Additional arguments to pass to the browser
    """
    try:
        cmd = [browser]
        
        # Check if it's a Chromium-based browser
        chromium_browsers = ['chromium', 'chrome', 'google-chrome', 'brave', 'edge', 'vivaldi']
        is_chromium_based = any(cb in browser.lower() for cb in chromium_browsers)
        
        # Add profile argument for Chromium-based browsers if specified
        if chromium_profile and is_chromium_based:
            if CREATE_MISSING_PROFILES:
                # Simple approach: use sanitized profile name as directory name
                profile_dir = sanitize_profile_name(chromium_profile)
                logger.info(f"Using profile directory: {profile_dir} (auto-create enabled)")
                cmd.extend([f'--profile-directory={profile_dir}', '--new-window'])
                
                # Note: Chrome will automatically create the directory on first use
                # The profile will show as "Person N" in Chrome UI, but the directory
                # name will be meaningful (e.g., CNN, Reuters, Banking, etc.)
            else:
                # Legacy behavior: look up profile in LocalState
                # This requires manual profile creation in Chrome
                logger.warning("CREATE_MISSING_PROFILES is disabled - using legacy profile lookup")
                error_msg = f"Error: Profile '{chromium_profile}' requires manual creation in browser"
                logger.error(error_msg)
                send_error_notification(error_msg)
                # Don't add profile arguments - let it use default
        
        # Add any extra arguments
        if extra_args:
            cmd.extend(extra_args)
        
        # Add the URL or --app=URL argument
        cmd.append(url_arg)
        
        logger.info(f"Running command: {' '.join(cmd)}")
        subprocess.Popen(cmd)
    except FileNotFoundError:
        error_msg = f"Error: Browser not found: {browser}"
        print(f"{error_msg}", file=sys.stderr)
        send_error_notification(error_msg)
        subprocess.Popen([DEFAULT_BROWSER, url_arg])


def main():
    # Allow launching without URL
    if len(sys.argv) < 2:
        logger.info("Launching browser without URL...")
        # Launch default browser with no URL
        if isinstance(DEFAULT_BROWSER, tuple):
            browser, profile = DEFAULT_BROWSER
            open_with_browser(browser, "", chromium_profile=profile)
        else:
            subprocess.Popen([DEFAULT_BROWSER])
        return

    first_arg = sys.argv[1]
    extra_args = sys.argv[2:] if len(sys.argv) > 2 else []
    
    # Extract URL for pattern matching, but keep original argument
    if first_arg.startswith("--app="):
        url = first_arg[6:]  # Extract URL for matching
        url_arg = first_arg  # Keep original --app=URL to pass through
    else:
        url = first_arg
        url_arg = first_arg
    
    # Debug logging
    logger.info(f"Processing URL: {url} (extra_args: {extra_args})")

    # Match against rules
    for pattern, browser_config in BROWSER_RULES.items():
        if re.match(pattern, url):
            # Handle both string and tuple configurations
            if isinstance(browser_config, tuple):
                browser, profile = browser_config
                logger.info(f"Matched pattern {pattern}, using profile: {profile}")
                send_info_notification(f"Using profile '{profile}' for {url}")
                open_with_browser(browser, url_arg, chromium_profile=profile, extra_args=extra_args)
            else:
                logger.info(f"Matched pattern {pattern}, no profile specified")
                send_info_notification(f"Opening {url} with configured browser")
                open_with_browser(browser_config, url_arg, extra_args=extra_args)
            return

    # Fallback to default
    logger.info(f"No pattern matched, using default browser")
    if isinstance(DEFAULT_BROWSER, tuple):
        browser, profile = DEFAULT_BROWSER
        send_info_notification(f"No matching rule for {url}, using default profile '{profile}'")
        open_with_browser(browser, url_arg, chromium_profile=profile, extra_args=extra_args)
    else:
        send_info_notification(f"No matching rule for {url}, using default browser")
        open_with_browser(DEFAULT_BROWSER, url_arg, extra_args=extra_args)


if __name__ == "__main__":
    main()
