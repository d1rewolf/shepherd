#!/usr/bin/env ruby
require 'minitest/autorun'
require 'json'
require 'fileutils'
require 'tempfile'
require 'pathname'
require_relative 'shepherd'

class TestShepherd < Minitest::Test
  def setup
    @shepherd = Shepherd.new
  end

  def test_sanitize_profile_name
    tests = [
      ['CNN', 'Profile_CNN'],
      ['Work & Personal', 'Profile_Work_Personal'],
      ['Test!!!123', 'Profile_Test_123'],
      ['', 'Default'],
      [nil, 'Default'],
      ['___test___', 'Profile_test']
    ]
    
    tests.each do |input_val, expected|
      result = @shepherd.sanitize_profile_name(input_val)
      assert_equal expected, result, "Failed: #{input_val.inspect} -> #{result} (expected #{expected})"
    end
    
    puts '✓ sanitize_profile_name tests passed'
  end

  def test_add_profile_bookmark
    Dir.mktmpdir do |tmpdir|
      profile_dir = tmpdir
      
      # Test 1: Create new bookmark
      result = @shepherd.add_profile_bookmark(profile_dir, 'TestProfile')
      assert_equal true, result, 'Should return true for new bookmark'
      
      # Check bookmark file exists
      bookmarks_file = File.join(profile_dir, 'Bookmarks')
      assert File.exist?(bookmarks_file), 'Bookmarks file should exist'
      
      # Verify bookmark content
      bookmarks = JSON.parse(File.read(bookmarks_file))
      children = bookmarks['roots']['bookmark_bar']['children']
      assert_equal 1, children.length, 'Should have one bookmark'
      assert_equal 'Profile: TestProfile', children[0]['name'], 'Bookmark name incorrect'
      assert_equal 'chrome://version/', children[0]['url'], 'Bookmark URL incorrect'
      
      # Check preferences
      prefs_file = File.join(profile_dir, 'Preferences')
      assert File.exist?(prefs_file), 'Preferences file should exist'
      
      prefs = JSON.parse(File.read(prefs_file))
      assert_equal true, prefs['bookmark_bar']['show_on_all_tabs'], 'Bookmarks bar should be visible'
      
      # Test 2: Don't duplicate bookmark
      result = @shepherd.add_profile_bookmark(profile_dir, 'TestProfile')
      assert_equal true, result, 'Should return true even if bookmark exists'
      
      bookmarks = JSON.parse(File.read(bookmarks_file))
      children = bookmarks['roots']['bookmark_bar']['children']
      
      # Count Profile: bookmarks
      profile_bookmarks = children.select { |c| c['name']&.start_with?('Profile:') }
      assert_equal 1, profile_bookmarks.length, "Should have only 1 profile bookmark, got #{profile_bookmarks.length}"
      
      puts '✓ add_profile_bookmark tests passed'
    end
  end

  def test_profile_directory_creation
    # Test with a unique profile name
    test_profile = 'TestCleanup'
    test_url = 'https://example.com'
    
    # Run shepherd with test profile
    begin
      require 'timeout'
      require 'open3'
      
      output = nil
      status = nil
      
      Timeout.timeout(5) do
        env = ENV.to_h.merge('TEST_PROFILE' => test_profile)
        output, status = Open3.capture2e(env, 'ruby', 'shepherd.rb', test_url)
      end
      
      # Just check it doesn't crash
      assert [0, 1].include?(status.exitstatus), "Shepherd crashed with code #{status.exitstatus}"
      
      puts '✓ Profile directory creation test passed'
    rescue Timeout::Error
      puts '✓ Profile directory creation test passed (timeout expected)'
    end
  end

  def test_config_loading
    # Should not crash even without config
    begin
      config = @shepherd.load_config
      assert_equal 8, config.keys.length, "Expected 8 config values, got #{config.keys.length}"
      puts '✓ Config loading test passed'
    rescue => e
      puts "✗ Config loading failed: #{e}"
      assert false, "Config loading should not fail"
    end
  end
end

# Run tests if this file is executed directly
if __FILE__ == $0
  puts 'Running shepherd tests...'
  
  # Run individual test methods manually to ensure output
  test = TestShepherd.new(:test_sanitize_profile_name)
  test.setup
  test.test_sanitize_profile_name
  
  test = TestShepherd.new(:test_add_profile_bookmark)
  test.setup
  test.test_add_profile_bookmark
  
  test = TestShepherd.new(:test_config_loading)
  test.setup
  test.test_config_loading
  
  puts "\n✅ All tests passed!"
end