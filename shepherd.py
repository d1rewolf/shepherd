#!/usr/bin/env python3
"""
shepherd.py - Smart URL router for browser profiles
https://github.com/d1rewolf/shepherd
"""

import json
import os
import re
import subprocess
import sys
import importlib.util
from pathlib import Path


def load_config():
    """Load configuration from ~/.config/shepherd/config.py or use defaults."""
    config_dir = Path.home() / ".config" / "shepherd"
    config_file = config_dir / "config.py"
    
    # Default configuration
    default_rules = {
        r"^https://example\.com": ("/usr/bin/chromium", "Default"),
    }
    default_browser = "/usr/bin/chromium"
    
    if config_file.exists():
        try:
            # Load config.py as a module
            spec = importlib.util.spec_from_file_location("shepherd_config", config_file)
            config = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config)
            
            # Get configuration from the module
            browser_rules = getattr(config, 'BROWSER_RULES', default_rules)
            default_browser = getattr(config, 'DEFAULT_BROWSER', default_browser)
            
            return browser_rules, default_browser
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
                example_content = '''"""
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
'''
                example_config.write_text(example_content)
                print(f"Created example config: {example_config}", file=sys.stderr)
                print(f"Copy {example_config} to {config_file} and customize it", file=sys.stderr)
    
    return default_rules, default_browser


# Load configuration
BROWSER_RULES, DEFAULT_BROWSER = load_config()


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
        print(f"Error: LocalState file not found at {local_state_path}", file=sys.stderr)
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
        print(f"Error reading LocalState file: {e}", file=sys.stderr)
        return ""


def open_with_browser(browser, url, chromium_profile=None, app_mode=False, extra_args=None):
    """
    Launch the browser with the given URL.
    
    Args:
        browser: Path to the browser executable
        url: URL to open
        chromium_profile: Optional profile name for Chromium-based browsers
        app_mode: Whether to open in app mode (for Chromium-based browsers)
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
                print(f"Using profile directory: {profile_dir}", file=sys.stderr)
                cmd.extend([f'--profile-directory={profile_dir}', '--new-window'])
            else:
                print(f"Warning: Profile '{chromium_profile}' not found in Chromium", file=sys.stderr)
        
        # Add any extra arguments
        if extra_args:
            cmd.extend(extra_args)
        
        # Add app mode if requested and browser supports it
        if app_mode and is_chromium_based:
            cmd.append(f'--app={url}')
        else:
            cmd.append(url)
        
        print(f"Running command: {' '.join(cmd)}", file=sys.stderr)
        subprocess.Popen(cmd)
    except FileNotFoundError:
        print(f"Error: Browser not found: {browser}", file=sys.stderr)
        subprocess.Popen([DEFAULT_BROWSER, url])


def main():
    if len(sys.argv) < 2:
        print("Usage: url_router.py <url> [extra args...]", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]
    app_mode = False
    extra_args = sys.argv[2:] if len(sys.argv) > 2 else []
    
    # Handle --app=URL format from omarchy-launch-webapp
    if url.startswith("--app="):
        url = url[6:]  # Remove "--app=" prefix
        app_mode = True
    
    # Debug logging
    print(f"Processing URL: {url} (app_mode: {app_mode}, extra_args: {extra_args})", file=sys.stderr)

    # Match against rules
    for pattern, browser_config in BROWSER_RULES.items():
        if re.match(pattern, url):
            # Handle both string and tuple configurations
            if isinstance(browser_config, tuple):
                browser, profile = browser_config
                print(f"Matched pattern {pattern}, using profile: {profile}", file=sys.stderr)
                open_with_browser(browser, url, chromium_profile=profile, app_mode=app_mode, extra_args=extra_args)
            else:
                print(f"Matched pattern {pattern}, no profile specified", file=sys.stderr)
                open_with_browser(browser_config, url, app_mode=app_mode, extra_args=extra_args)
            return

    # Fallback to default
    print(f"No pattern matched, using default browser", file=sys.stderr)
    if isinstance(DEFAULT_BROWSER, tuple):
        browser, profile = DEFAULT_BROWSER
        open_with_browser(browser, url, chromium_profile=profile, app_mode=app_mode, extra_args=extra_args)
    else:
        open_with_browser(DEFAULT_BROWSER, url, app_mode=app_mode, extra_args=extra_args)


if __name__ == "__main__":
    main()
