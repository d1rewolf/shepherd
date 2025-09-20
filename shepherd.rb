#!/usr/bin/env ruby
require 'json'
require 'fileutils'
require 'pathname'
require 'logger'
require 'open3'

VERSION = '1.0.0'

class Shepherd
  def initialize
    @config = load_config
    setup_logging
  end

  def setup_logging
    xdg_state_home = ENV['XDG_STATE_HOME'] || File.join(Dir.home, '.local', 'state')
    log_dir = File.join(xdg_state_home, 'shepherd')
    FileUtils.mkdir_p(log_dir)
    log_file = File.join(log_dir, 'shepherd.log')
    
    log_level = case @config[:log_level].upcase
                when 'DEBUG' then Logger::DEBUG
                when 'INFO' then Logger::INFO
                when 'WARNING', 'WARN' then Logger::WARN
                when 'ERROR' then Logger::ERROR
                when 'CRITICAL', 'FATAL' then Logger::FATAL
                else Logger::INFO
                end
    
    @logger = Logger.new(log_file)
    @logger.level = log_level
    @logger.formatter = proc do |severity, datetime, progname, msg|
      "#{datetime.strftime('%Y-%m-%d %H:%M:%S')} - #{severity} - #{msg}\n"
    end
    
    # Also log to stderr for debugging
    stderr_logger = Logger.new($stderr)
    stderr_logger.level = log_level
    stderr_logger.formatter = @logger.formatter
    @stderr_logger = stderr_logger
  end

  def log(level, message)
    @logger.send(level, message) if @logger
    @stderr_logger.send(level, message) if @stderr_logger
  end

  def load_config
    config_dir = File.join(Dir.home, '.config', 'shepherd')
    config_file = File.join(config_dir, 'config.rb')
    
    # Default configuration
    default_config = {
      browser_rules: {
        /^https:\/\/example\.com/ => ['/usr/bin/chromium', 'Default']
      },
      default_browser: '/usr/bin/chromium',
      enable_info_notifications: false,
      enable_error_notifications: false,
      notification_command: ['notify-send', 'Shepherd', '{message}', '-i', 'dialog-warning'],
      log_level: 'INFO',
      create_missing_profiles: false,
      add_profile_bookmark: false
    }
    
    if File.exist?(config_file)
      begin
        # Create a binding context for config evaluation
        config_binding = binding
        
        # Define variables that will be set in the config
        browser_rules = nil
        default_browser = nil
        enable_notifications = nil
        enable_info_notifications = nil
        enable_error_notifications = nil
        notification_command = nil
        log_level = nil
        create_missing_profiles = nil
        add_profile_bookmark = nil
        
        # Load and evaluate the config file
        eval(File.read(config_file), config_binding)
        
        # Extract configured values or use defaults
        config = {
          browser_rules: eval('defined?(BROWSER_RULES) ? BROWSER_RULES : nil', config_binding) || default_config[:browser_rules],
          default_browser: eval('defined?(DEFAULT_BROWSER) ? DEFAULT_BROWSER : nil', config_binding) || default_config[:default_browser],
          enable_info_notifications: eval('defined?(ENABLE_INFO_NOTIFICATIONS) ? ENABLE_INFO_NOTIFICATIONS : nil', config_binding) || default_config[:enable_info_notifications],
          enable_error_notifications: eval('defined?(ENABLE_ERROR_NOTIFICATIONS) ? ENABLE_ERROR_NOTIFICATIONS : (defined?(ENABLE_NOTIFICATIONS) ? ENABLE_NOTIFICATIONS : nil)', config_binding) || default_config[:enable_error_notifications],
          notification_command: eval('defined?(NOTIFICATION_COMMAND) ? NOTIFICATION_COMMAND : nil', config_binding) || default_config[:notification_command],
          log_level: eval('defined?(LOG_LEVEL) ? LOG_LEVEL : nil', config_binding) || default_config[:log_level],
          create_missing_profiles: eval('defined?(CREATE_MISSING_PROFILES) ? CREATE_MISSING_PROFILES : nil', config_binding) || default_config[:create_missing_profiles],
          add_profile_bookmark: eval('defined?(ADD_PROFILE_BOOKMARK) ? ADD_PROFILE_BOOKMARK : nil', config_binding) || default_config[:add_profile_bookmark]
        }
        
        return config
      rescue => e
        $stderr.puts "Error loading config from #{config_file}: #{e}"
        $stderr.puts "Using default configuration"
      end
    else
      # Create config directory and example config if it doesn't exist
      unless File.directory?(config_dir)
        FileUtils.mkdir_p(config_dir)
        $stderr.puts "Created config directory: #{config_dir}"
        
        # Create example config
        example_config = File.join(config_dir, 'config.example.rb')
        unless File.exist?(example_config)
          example_content = <<~'RUBY'
            # Shepherd configuration file
            # Rename this to config.rb and customize for your needs

            # Browser rules: regex pattern -> [browser_path, profile_name] or just browser_path
            # First matching pattern wins
            BROWSER_RULES = {
              # Work profiles
              /^https:\/\/.*\.slack\.com/ => ['/usr/bin/chromium', 'Work'],
              
              # Personal browsing
              /^https:\/\/mail\.google\.com/ => ['/usr/bin/chromium', 'Personal'],
              
              # Banking - use separate profile for security
              /^https:\/\/.*\.chase\.com/ => ['/usr/bin/chromium', 'Banking']
            }

            # Default browser for unmatched URLs
            DEFAULT_BROWSER = '/usr/bin/chromium'

            # Notification settings (optional)
            ENABLE_INFO_NOTIFICATIONS = false  # Set to true to show profile routing notifications
            ENABLE_ERROR_NOTIFICATIONS = false  # Set to true to show error notifications
            NOTIFICATION_COMMAND = ['notify-send', 'Shepherd', '{message}', '-i', 'dialog-warning']

            # Logging configuration
            # Options: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
            LOG_LEVEL = 'INFO'

            # Automatically create browser profiles if they don't exist
            # When enabled, shepherd will use the profile name as the directory name
            CREATE_MISSING_PROFILES = false

            # Add a bookmark to the bookmarks bar showing the profile name
            # Helps users identify which profile they're currently using
            ADD_PROFILE_BOOKMARK = false
          RUBY
          
          File.write(example_config, example_content)
          $stderr.puts "Created example config: #{example_config}"
          $stderr.puts "Copy #{example_config} to #{config_file} and customize it"
        end
      end
    end
    
    default_config
  end

  def send_notification(message)
    return unless @config[:notification_command]
    
    begin
      cmd = @config[:notification_command].map { |arg| arg.gsub('{message}', message) }
      Open3.popen3(*cmd) { |stdin, stdout, stderr, wait_thr| }
    rescue => e
      log(:error, "Failed to send notification: #{e}")
    end
  end

  def send_info_notification(message)
    send_notification(message) if @config[:enable_info_notifications]
  end

  def send_error_notification(message)
    send_notification(message) if @config[:enable_error_notifications]
  end

  def add_profile_bookmark(profile_dir, profile_name)
    begin
      # Enable bookmarks bar
      prefs_file = File.join(profile_dir, 'Preferences')
      begin
        prefs = File.exist?(prefs_file) ? JSON.parse(File.read(prefs_file)) : {}
        prefs['bookmark_bar'] ||= {}
        prefs['bookmark_bar']['show_on_all_tabs'] = true
        File.write(prefs_file, JSON.pretty_generate(prefs))
        log(:info, "Enabled bookmarks bar visibility for profile '#{profile_name}'")
      rescue => e
        log(:warn, "Could not update Preferences: #{e}")
      end
      
      # Add bookmark
      bookmarks_file = File.join(profile_dir, 'Bookmarks')
      profile_bookmark = {
        'date_added' => '13367051200000000',
        'id' => '1',
        'name' => "Profile: #{profile_name}",
        'type' => 'url',
        'url' => 'chrome://version/'
      }
      
      if File.exist?(bookmarks_file)
        bookmarks = JSON.parse(File.read(bookmarks_file))
        children = bookmarks.dig('roots', 'bookmark_bar', 'children') || []
        unless children.any? { |c| c['name']&.start_with?('Profile:') }
          profile_bookmark['id'] = (children.length + 100).to_s
          children.unshift(profile_bookmark)
        end
      else
        # Minimal structure
        bookmarks = {
          'checksum' => '',
          'roots' => {
            'bookmark_bar' => {
              'children' => [profile_bookmark],
              'date_added' => '13367051200000000',
              'date_modified' => '13367051200000000',
              'id' => '1',
              'name' => 'Bookmarks bar',
              'type' => 'folder'
            },
            'other' => {
              'children' => [],
              'date_added' => '13367051200000000',
              'date_modified' => '0',
              'id' => '2',
              'name' => 'Other bookmarks',
              'type' => 'folder'
            },
            'synced' => {
              'children' => [],
              'date_added' => '13367051200000000',
              'date_modified' => '0',
              'id' => '3',
              'name' => 'Mobile bookmarks',
              'type' => 'folder'
            }
          },
          'version' => 1
        }
      end
      
      File.write(bookmarks_file, JSON.pretty_generate(bookmarks))
      log(:info, "Added profile bookmark for '#{profile_name}'")
      true
    rescue => e
      log(:warn, "Could not add profile bookmark: #{e}")
      false
    end
  end

  def sanitize_profile_name(profile_name)
    return 'Default' if profile_name.nil? || profile_name.empty?
    
    safe_name = profile_name.gsub(/[^\w\-]/, '_')
    safe_name = safe_name.gsub(/_+/, '_').strip.gsub(/^_+|_+$/, '')
    safe_name.empty? ? 'Default' : "Profile_#{safe_name}"
  end

  def open_with_browser(browser, url_arg, chromium_profile: nil, extra_args: nil)
    begin
      cmd = [browser]
      
      # Check if Chromium-based
      browser_lower = browser.downcase
      is_chromium_based = ['chromium', 'chrome', 'google-chrome', 'brave', 'edge', 'vivaldi'].any? { |cb| browser_lower.include?(cb) }
      
      if chromium_profile && is_chromium_based
        if @config[:create_missing_profiles]
          profile_dir = sanitize_profile_name(chromium_profile)
          log(:info, "Using profile: #{profile_dir}")
          cmd.extend(["--profile-directory=#{profile_dir}", '--new-window'])
          
          if @config[:add_profile_bookmark]
            # Get browser config dir
            browser_name = File.basename(browser).downcase
            config_dir = if browser_name.include?('chrome')
                          File.join(Dir.home, '.config', 'google-chrome')
                        elsif browser_name.include?('brave')
                          File.join(Dir.home, '.config', 'BraveSoftware', 'Brave-Browser')
                        else
                          File.join(Dir.home, '.config', 'chromium')
                        end
            
            profile_path = File.join(config_dir, profile_dir)
            
            # Pre-create directory if needed
            FileUtils.mkdir_p(profile_path)
            
            # Add bookmark immediately
            add_profile_bookmark(profile_path, chromium_profile)
          end
        else
          log(:error, "Profile '#{chromium_profile}' requires manual creation")
          send_error_notification("Profile '#{chromium_profile}' not found")
        end
      end
      
      cmd.concat(extra_args) if extra_args
      cmd << url_arg if url_arg && !url_arg.empty?
      
      log(:info, "Running: #{cmd.join(' ')}")
      Process.spawn(*cmd)
    rescue Errno::ENOENT
      error_msg = "Error: Browser not found: #{browser}"
      $stderr.puts error_msg
      send_error_notification(error_msg)
      Process.spawn(@config[:default_browser], url_arg)
    end
  end

  def run(args)
    # Allow launching without URL
    if args.empty?
      log(:info, "Launching browser without URL...")
      # Launch default browser with no URL
      if @config[:default_browser].is_a?(Array)
        browser, profile = @config[:default_browser]
        open_with_browser(browser, '', chromium_profile: profile)
      else
        Process.spawn(@config[:default_browser])
      end
      return
    end
    
    first_arg = args[0]
    extra_args = args[1..-1] || []
    
    # Extract URL for pattern matching, but keep original argument
    if first_arg.start_with?('--app=')
      url = first_arg[6..-1]  # Extract URL for matching
      url_arg = first_arg     # Keep original --app=URL to pass through
    else
      url = first_arg
      url_arg = first_arg
    end
    
    # Debug logging
    log(:info, "Processing URL: #{url} (extra_args: #{extra_args})")
    
    # Match against rules
    @config[:browser_rules].each do |pattern, browser_config|
      if pattern.match?(url)
        # Handle both string and array configurations
        if browser_config.is_a?(Array)
          browser, profile = browser_config
          log(:info, "Matched pattern #{pattern}, using profile: #{profile}")
          send_info_notification("Using profile '#{profile}' for #{url}")
          open_with_browser(browser, url_arg, chromium_profile: profile, extra_args: extra_args)
        else
          log(:info, "Matched pattern #{pattern}, no profile specified")
          send_info_notification("Opening #{url} with configured browser")
          open_with_browser(browser_config, url_arg, extra_args: extra_args)
        end
        return
      end
    end
    
    # Fallback to default
    log(:info, "No pattern matched, using default browser")
    if @config[:default_browser].is_a?(Array)
      browser, profile = @config[:default_browser]
      send_info_notification("No matching rule for #{url}, using default profile '#{profile}'")
      open_with_browser(browser, url_arg, chromium_profile: profile, extra_args: extra_args)
    else
      send_info_notification("No matching rule for #{url}, using default browser")
      open_with_browser(@config[:default_browser], url_arg, extra_args: extra_args)
    end
  end
end

# Main execution
if __FILE__ == $0
  shepherd = Shepherd.new
  shepherd.run(ARGV)
end