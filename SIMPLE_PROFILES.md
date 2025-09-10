# Simple Auto-Profile Creation

## How It Works

When `CREATE_MISSING_PROFILES=True` in your config.py, shepherd uses a beautifully simple approach:

1. **Profile names become directory names**: Instead of "Profile 1", "Profile 2", etc., Chrome creates directories like "CNN", "Reddit", "Banking"
2. **Chrome handles creation**: No manual directory creation, no LocalState manipulation
3. **Automatic and robust**: Works with any Chromium-based browser

## Example

```python
# In config.py
BROWSER_RULES = {
    r"^https://cnn\.com": ("/usr/bin/chromium", "CNN"),
    r"^https://reddit\.com": ("/usr/bin/chromium", "Reddit"),
}
CREATE_MISSING_PROFILES = True
```

When you visit cnn.com for the first time:
- Shepherd passes `--profile-directory=CNN` to Chrome
- Chrome creates `~/.config/chromium/CNN/` automatically
- The profile works immediately

## Directory Structure

```
~/.config/chromium/
├── Default/          # Your default profile
├── CNN/             # Auto-created profile
├── Reddit/          # Auto-created profile
├── Banking/         # Auto-created profile
└── Local State      # Chrome's internal file (we don't touch it!)
```

## Trade-offs

**Pros:**
- ✅ Zero complexity - just 20 lines of code
- ✅ Never breaks with Chrome updates
- ✅ Self-documenting directory names
- ✅ Works forever (Chrome has supported this for 10+ years)

**Cons:**
- ❌ Chrome UI shows "Person 1", "Person 2" instead of friendly names
- ❌ Can't use Chrome's profile switcher effectively

But since you're using shepherd to launch URLs, the Chrome UI names don't matter!

## Comparison with Complex Approach

| Aspect | Simple (Current) | Complex (Old) |
|--------|-----------------|---------------|
| Lines of code | ~20 | ~200 |
| Chrome internals touched | None | LocalState JSON |
| Risk of breaking | Nearly zero | High with Chrome updates |
| Directory names | Meaningful (CNN, Reddit) | Generic (Profile 14, Profile 15) |
| Chrome UI names | Generic (Person 1, 2) | Custom (CNN, Reddit) |
| Profile creation | Automatic by Chrome | Manual with JSON manipulation |

## Why This Works

Chrome's `--profile-directory` flag accepts ANY directory name:
- `--profile-directory=Default` ✅
- `--profile-directory=Profile 1` ✅ 
- `--profile-directory=CNN` ✅
- `--profile-directory=My_Banking_Profile` ✅

Chrome simply creates the directory if it doesn't exist. We don't need to do anything special!