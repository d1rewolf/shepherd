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
    default_enable_notifications = False
    default_notification_command = ['notify-send', 'Shepherd', '{message}', '-i', 'dialog-warning']
    default_log_level = "INFO"
    
    if config_file.exists():
        try:
            # Load config.py as a module
            spec = importlib.util.spec_from_file_location("shepherd_config", config_file)
            config = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config)
            
            # Get configuration from the module
            browser_rules = getattr(config, 'BROWSER_RULES', default_rules)
            default_browser = getattr(config, 'DEFAULT_BROWSER', default_browser)
            enable_notifications = getattr(config, 'ENABLE_NOTIFICATIONS', default_enable_notifications)
            notification_command = getattr(config, 'NOTIFICATION_COMMAND', default_notification_command)
            log_level = getattr(config, 'LOG_LEVEL', default_log_level)
            
            return browser_rules, default_browser, enable_notifications, notification_command, log_level
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
ENABLE_NOTIFICATIONS = False  # Set to True to enable desktop notifications
NOTIFICATION_COMMAND = ['notify-send', 'Shepherd', '{message}', '-i', 'dialog-warning']
'''
                example_config.write_text(example_content)
                print(f"Created example config: {example_config}", file=sys.stderr)
                print(f"Copy {example_config} to {config_file} and customize it", file=sys.stderr)
    
    return default_rules, default_browser, default_enable_notifications, default_notification_command, default_log_level


# Load configuration
BROWSER_RULES, DEFAULT_BROWSER, ENABLE_NOTIFICATIONS, NOTIFICATION_COMMAND, LOG_LEVEL = load_config()

# Initialize logging with configured log level
logger = setup_logging(LOG_LEVEL)


def send_notification(message):
    """Send a desktop notification if enabled."""
    if ENABLE_NOTIFICATIONS and NOTIFICATION_COMMAND:
        try:
            # Replace {message} placeholder in the command
            cmd = [arg.replace('{message}', message) for arg in NOTIFICATION_COMMAND]
            subprocess.run(cmd, check=False, capture_output=True)
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")


def chromium_profile_lookup(profile_name=""):
    """
    Map a friendly profile name to Chromium's actual profile directory.
    Reads profile information directly from Chromium's LocalState file.
    
    Args:
        profile_name: The friendly name of the profile (e.g., "Work", "Personal")
    
    Returns:
        Profile directory name (e.g., "Default", "Profile 1") or empty string if not found
    """
    if not profile_name:
        return "Default"
    
    local_state_path = Path.home() / ".config/chromium/Local State"
    
    if not local_state_path.exists():
        logger.error(f"LocalState file not found at {local_state_path}")
        return ""
    
    try:
        with open(local_state_path, 'r') as f:
            local_state = json.load(f)
        
        # Look up profile in info_cache
        info_cache = local_state.get('profile', {}).get('info_cache', {})
        
        for profile_dir, profile_info in info_cache.items():
            if profile_info.get('name') == profile_name:
                # Verify the directory exists
                profile_path = Path.home() / ".config/chromium" / profile_dir
                if profile_path.exists():
                    return profile_dir
        
        return ""
    
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Error reading LocalState file: {e}")
        return ""


def open_with_browser(browser, url_arg, chromium_profile=None, extra_args=None):
    """
    Launch the browser with the given URL or --app=URL argument.
    
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
            profile_dir = chromium_profile_lookup(chromium_profile)
            if profile_dir:
                logger.info(f"Using profile directory: {profile_dir}")
                cmd.extend([f'--profile-directory={profile_dir}', '--new-window'])
            else:
                error_msg = f"Error: Profile '{chromium_profile}' not found"
                logger.error(error_msg)
                send_notification(error_msg)
        
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
        send_notification(error_msg)
        subprocess.Popen([DEFAULT_BROWSER, url_arg])


def main():
    # Allow launching without URL
    if len(sys.argv) < 2:
        logger.info("Launching browser without URL...")
        # Launch default browser with no URL
        if isinstance(DEFAULT_BROWSER, tuple):
            browser, profile = DEFAULT_BROWSER
            try:
                cmd = [browser]
                if profile:
                    profile_dir = chromium_profile_lookup(profile)
                    if profile_dir:
                        cmd.extend([f'--profile-directory={profile_dir}', '--new-window'])
                subprocess.Popen(cmd)
            except FileNotFoundError:
                subprocess.Popen([DEFAULT_BROWSER[0]])
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
                open_with_browser(browser, url_arg, chromium_profile=profile, extra_args=extra_args)
            else:
                logger.info(f"Matched pattern {pattern}, no profile specified")
                open_with_browser(browser_config, url_arg, extra_args=extra_args)
            return

    # Fallback to default
    logger.info(f"No pattern matched, using default browser")
    if isinstance(DEFAULT_BROWSER, tuple):
        browser, profile = DEFAULT_BROWSER
        open_with_browser(browser, url_arg, chromium_profile=profile, extra_args=extra_args)
    else:
        open_with_browser(DEFAULT_BROWSER, url_arg, extra_args=extra_args)


if __name__ == "__main__":
    main()
