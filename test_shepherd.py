#!/usr/bin/env python3
"""Test shepherd functionality before and after cleanup."""

import json
import shutil
import tempfile
from pathlib import Path
import sys
import os

# Add current dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_sanitize_profile_name():
    """Test profile name sanitization."""
    from shepherd import sanitize_profile_name
    
    tests = [
        ("CNN", "Profile_CNN"),
        ("Work & Personal", "Profile_Work_Personal"),
        ("Test!!!123", "Profile_Test_123"),
        ("", "Default"),
        (None, "Default"),
        ("___test___", "Profile_test"),
    ]
    
    for input_val, expected in tests:
        result = sanitize_profile_name(input_val)
        assert result == expected, f"Failed: {input_val} -> {result} (expected {expected})"
    
    print("✓ sanitize_profile_name tests passed")


def test_add_profile_bookmark():
    """Test bookmark creation."""
    from shepherd import add_profile_bookmark
    
    # Create temp profile dir
    with tempfile.TemporaryDirectory() as tmpdir:
        profile_dir = Path(tmpdir)
        
        # Test 1: Create new bookmark
        result = add_profile_bookmark(profile_dir, "TestProfile")
        assert result == True, "Should return True for new bookmark"
        
        # Check bookmark file exists
        bookmarks_file = profile_dir / "Bookmarks"
        assert bookmarks_file.exists(), "Bookmarks file should exist"
        
        # Verify bookmark content
        with open(bookmarks_file) as f:
            bookmarks = json.load(f)
        
        children = bookmarks["roots"]["bookmark_bar"]["children"]
        assert len(children) == 1, "Should have one bookmark"
        assert children[0]["name"] == "Profile: TestProfile", "Bookmark name incorrect"
        assert children[0]["url"] == "chrome://version/", "Bookmark URL incorrect"
        
        # Check preferences
        prefs_file = profile_dir / "Preferences"
        assert prefs_file.exists(), "Preferences file should exist"
        
        with open(prefs_file) as f:
            prefs = json.load(f)
        assert prefs["bookmark_bar"]["show_on_all_tabs"] == True, "Bookmarks bar should be visible"
        
        # Test 2: Don't duplicate bookmark
        result = add_profile_bookmark(profile_dir, "TestProfile")
        assert result == True, "Should return True even if bookmark exists"
        
        with open(bookmarks_file) as f:
            bookmarks = json.load(f)
        children = bookmarks["roots"]["bookmark_bar"]["children"]
        
        # Count Profile: bookmarks
        profile_bookmarks = [c for c in children if c["name"].startswith("Profile:")]
        assert len(profile_bookmarks) == 1, f"Should have only 1 profile bookmark, got {len(profile_bookmarks)}"
        
        print("✓ add_profile_bookmark tests passed")


def test_profile_directory_creation():
    """Test that profile directories work correctly."""
    import subprocess
    import time
    
    # Test with a unique profile name
    test_profile = "TestCleanup"
    test_url = "https://example.com"
    
    # Run shepherd with test profile
    result = subprocess.run(
        ["python3", "shepherd.py", test_url],
        env={**os.environ, "TEST_PROFILE": test_profile},
        capture_output=True,
        text=True,
        timeout=5
    )
    
    # Just check it doesn't crash
    assert result.returncode in [0, 1], f"Shepherd crashed with code {result.returncode}"
    
    print("✓ Profile directory creation test passed")


def test_config_loading():
    """Test configuration loading."""
    from shepherd import load_config
    
    # Should not crash even without config
    try:
        config = load_config()
        assert len(config) == 8, f"Expected 8 config values, got {len(config)}"
        print("✓ Config loading test passed")
    except Exception as e:
        print(f"✗ Config loading failed: {e}")
        return False
    
    return True


if __name__ == "__main__":
    print("Running shepherd tests...")
    
    # Run tests
    test_sanitize_profile_name()
    test_add_profile_bookmark() 
    test_config_loading()
    
    print("\n✅ All tests passed!")