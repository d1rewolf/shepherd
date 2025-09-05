# shepherd.py

```
      .-.
     (@o@)
    /|   |\
   // \_/ \\
  //   |   \\
  \\   |   //
   \\_/ \_//
    ||| |||
    ^^^ ^^^
```

A smart URL router that guides your web links to the right browser profile - like a shepherd tending different flocks. Because sometimes you need your work emails in one profile and cat videos in another.

DISCLAIMER: shepherd.py has been vibe-coded by an experienced programmer, but most of the code is written by claude code. Make of that what you will.

## What is shepherd.py?

shepherd.py is a lightweight URL router that automatically opens different websites in different browser profiles based on customizable rules. Perfect for keeping your work, personal, and whatever-else-you're-into browsing separate.

## Features

- **Smart URL Routing** - Define regex patterns to route URLs to specific browser profiles
- **Multi-Profile Support** - Works with Chromium-based browsers' profile system
- **App Mode Support** - Preserves web app functionality when launched via desktop shortcuts
- **Default Fallback** - URLs that don't match any rule go to your default browser
- **Simple Configuration** - Edit rules in a separate config file
- **Desktop Notifications** - Optional notifications when profiles or browsers aren't found

## Installation

### Quick Install

1. Clone the repository:
```bash
git clone https://github.com/d1rewolf/shepherd.git
cd shepherd
```

2. Make the script executable:
```bash
chmod +x shepherd.py
```

3. Install it system-wide (optional):
```bash
sudo python setup.py install
```

### Setting as Default Browser

To use shepherd.py as your system's default URL handler:

1. Create a desktop entry file at `~/.local/share/applications/shepherd.desktop`:

```ini
[Desktop Entry]
Version=1.0
Type=Application
Name=Shepherd
GenericName=Web Browser Router
Comment=Routes URLs to different browser profiles
Exec=/path/to/shepherd.py %U
Terminal=false
MimeType=text/html;text/xml;application/xhtml+xml;x-scheme-handler/http;x-scheme-handler/https;
Categories=Network;WebBrowser;
Icon=web-browser
StartupNotify=true
```

2. Update the desktop database and set as default:
```bash
update-desktop-database ~/.local/share/applications/
xdg-settings set default-web-browser shepherd.desktop
```

### Omarchy Integration

If you're using [Omarchy](https://github.com/d1rewolf/omarchy), you'll need an additional step to make shepherd.py work with `omarchy-launch-webapp`. 

**The Problem:** Omarchy's `omarchy-launch-webapp` script checks for known browsers, and when it doesn't recognize `shepherd.desktop`, it falls back to `chromium.desktop`. This would bypass shepherd.py entirely.

**The Solution:** Create a local chromium.desktop (or brave.desktop, or vivaldi.desktop...) with an override that points to shepherd.py:

```bash
# Create a local override of chromium.desktop
cp /usr/share/applications/chromium.desktop ~/.local/share/applications/

# Edit the Exec line to point to shepherd.py
sed -i 's|^Exec=/usr/bin/chromium %U|Exec=/path/to/shepherd.py %U|' ~/.local/share/applications/chromium.desktop

# Also update the other Exec lines for new-window and incognito actions
sed -i 's|^Exec=/usr/bin/chromium$|Exec=/path/to/shepherd.py|' ~/.local/share/applications/chromium.desktop
sed -i 's|^Exec=/usr/bin/chromium --incognito|Exec=/path/to/shepherd.py --incognito|' ~/.local/share/applications/chromium.desktop

# Update desktop database
update-desktop-database ~/.local/share/applications/
```

This way:
1. Regular desktop clicks use `shepherd.desktop` → routes through shepherd.py
2. Omarchy falls back to `chromium.desktop` → finds your override → still routes through shepherd.py
3. No need to modify omarchy-launch-webapp itself

**Note:** This override only affects desktop/GUI launches. Command-line `chromium` commands will still use `/usr/bin/chromium` directly.

## Configuration

Shepherd.py stores its configuration in `~/.config/shepherd/config.py`. On first run, it will create an example configuration file for you.

### Quick Setup

1. Run shepherd.py once to create the config directory:
```bash
./shepherd.py https://example.com
```

2. Copy the example config to create your own:
```bash
cd ~/.config/shepherd/
cp config.example.py config.py
```

3. Edit `~/.config/shepherd/config.py` with your rules:

```python
# Browser rules: regex pattern -> (browser_path, profile_name) or just browser_path
BROWSER_RULES = {
    # Work stuff goes to work profile
    r"^https://.*\.company\.com": ("/usr/bin/chromium", "Work"),
    r"^https://slack\.com": ("/usr/bin/chromium", "Work"),
    
    # Personal stuff
    r"^https://mail\.google\.com": ("/usr/bin/chromium", "Personal"),
    r"^https://.*\.facebook\.com": ("/usr/bin/chromium", "Personal"),
    
    # Shopping in a separate profile (for price tracking isolation)
    r"^https://.*amazon\.com": ("/usr/bin/chromium", "Shopping"),
    
    # Banking gets its own profile for security
    r"^https://.*\.chase\.com": ("/usr/bin/brave", "Banking"),
}

# Default browser for unmatched URLs
DEFAULT_BROWSER = "/usr/bin/chromium"

# Or with a default profile:
# DEFAULT_BROWSER = ("/usr/bin/chromium", "Personal")

# Enable desktop notifications for errors (optional)
ENABLE_NOTIFICATIONS = True
NOTIFICATION_COMMAND = ['notify-send', 'Shepherd', '{message}', '-i', 'dialog-warning']
```

### Rule Format

Both rules and DEFAULT_BROWSER can be either:
- **Simple string**: Just the browser path
- **Tuple**: `(browser_path, profile_name)` for profile-specific routing

### Notification Settings

shepherd.py can send desktop notifications when it encounters errors:

- **ENABLE_NOTIFICATIONS**: Set to `True` to enable notifications
- **NOTIFICATION_COMMAND**: Customize the notification command
  - `{message}` will be replaced with the error message
  - Default uses `notify-send` (works with most Linux desktops)
  - Can be customized for other notification systems (dunstify, zenity, etc.)

## Usage

### Command Line

```bash
# Open a URL (will route based on rules)
shepherd.py https://github.com

# Works with app mode (for web apps)
shepherd.py --app=https://slack.com

# Pass additional browser arguments
shepherd.py https://example.com --incognito
```

### As System Default

Once set as the default browser, clicking links in any application will automatically route through shepherd.py.

## Supported Browsers

shepherd.py automatically detects and supports profile switching for:
- Chromium
- Google Chrome
- Brave
- Microsoft Edge
- Vivaldi
- Opera

## How It Works

1. **URL Matching**: When a URL is opened, shepherd.py checks it against your defined regex patterns
2. **Profile Lookup**: For Chromium-based browsers, it reads the browser's Local State file to map friendly profile names to profile directories
3. **Smart Routing**: Opens the URL in the matched browser/profile combination
4. **App Mode Preservation**: Maintains web app functionality when launched with `--app` flag

## Examples

### Separate Work and Personal

```python
BROWSER_RULES = {
    # All work domains
    r"^https://(mail\.google|calendar\.google|drive\.google)\.com": ("/usr/bin/chromium", "Work"),
    r"^https://.*\.slack\.com": ("/usr/bin/chromium", "Work"),
    r"^https://github\.com/workorg": ("/usr/bin/chromium", "Work"),
    
    # Personal stuff
    r"^https://reddit\.com": ("/usr/bin/chromium", "Personal"),
    r"^https://twitter\.com": ("/usr/bin/chromium", "Personal"),
}
```

### Security-Conscious Setup

```python
BROWSER_RULES = {
    # Banking in hardened Brave profile
    r"^https://.*\.(chase|wellsfargo|bankofamerica)\.com": ("/usr/bin/brave", "Banking"),
    
    # Shopping with tracker isolation
    r"^https://.*\.(amazon|ebay|etsy)\.com": ("/usr/bin/chromium", "Shopping"),
    
    # Social media sandboxed
    r"^https://.*\.(facebook|instagram|tiktok)\.com": ("/usr/bin/chromium", "Social"),
}
```

## Troubleshooting

### Profile Not Found

If shepherd.py can't find a profile, check:
1. The profile name matches exactly what's shown in your browser's profile manager
2. The browser's Local State file exists at `~/.config/[browser]/Local State`

### Debug Mode

shepherd.py outputs debug information to stderr. Run it from terminal to see:
```bash
shepherd.py https://example.com
# Processing URL: https://example.com (app_mode: False)
# Matched pattern ^https://example\.com, using profile: Work
# Using profile directory: Profile 2
```

## Contributing

Contributions are welcome! Feel free to submit issues and pull requests.

## License

MIT License - see LICENSE file for details

## Why "shepherd.py"?

Because like a shepherd guides different flocks to different pastures, shepherd.py guides your URLs to the right browser profiles. Plus, shepherd's pie is delicious, and this makes your browsing experience more delicious too.

---

*Made for people who have too many browser profiles*
