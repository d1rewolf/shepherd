#!/usr/bin/env ruby
require 'fileutils'
require 'pathname'

class Setup
  SCRIPT_NAME = 'shepherd'
  SCRIPT_FILE = 'shepherd.rb'
  
  def self.install
    # Determine installation paths
    prefix = ENV['PREFIX'] || '/usr/local'
    bin_dir = File.join(prefix, 'bin')
    
    # Create bin directory if it doesn't exist
    FileUtils.mkdir_p(bin_dir) unless File.directory?(bin_dir)
    
    # Get the source file path
    script_source = File.join(File.dirname(__FILE__), SCRIPT_FILE)
    script_dest = File.join(bin_dir, SCRIPT_NAME)
    
    unless File.exist?(script_source)
      puts "Error: #{SCRIPT_FILE} not found in current directory"
      exit 1
    end
    
    # Copy the script
    puts "Installing #{SCRIPT_NAME} to #{script_dest}..."
    FileUtils.cp(script_source, script_dest)
    
    # Make it executable
    FileUtils.chmod(0755, script_dest)
    
    # Create desktop entry for system integration
    desktop_entry_content = <<~DESKTOP
      [Desktop Entry]
      Version=1.0
      Name=Shepherd Browser Router
      Comment=Smart URL router for browser profiles
      Exec=#{script_dest} %u
      Terminal=false
      Type=Application
      MimeType=x-scheme-handler/http;x-scheme-handler/https;text/html;
      Categories=Network;WebBrowser;
      NoDisplay=true
    DESKTOP
    
    # Install desktop entry
    desktop_dir = File.join(Dir.home, '.local', 'share', 'applications')
    FileUtils.mkdir_p(desktop_dir)
    desktop_file = File.join(desktop_dir, 'shepherd.desktop')
    
    puts "Installing desktop entry to #{desktop_file}..."
    File.write(desktop_file, desktop_entry_content)
    
    # Update desktop database
    system('update-desktop-database', File.join(Dir.home, '.local', 'share', 'applications'))
    
    puts <<~MSG
      
      ✅ Shepherd installed successfully!
      
      To set Shepherd as your default browser:
      1. Run: xdg-settings set default-web-browser shepherd.desktop
      2. Or use your desktop environment's settings to set Shepherd as the default browser
      
      Configuration:
      - Copy ~/.config/shepherd/config.example.rb to ~/.config/shepherd/config.rb
      - Edit the config file to define your browser profiles and URL patterns
      
      Logs are written to: ~/.local/state/shepherd/shepherd.log
    MSG
  end
  
  def self.uninstall
    prefix = ENV['PREFIX'] || '/usr/local'
    script_dest = File.join(prefix, 'bin', SCRIPT_NAME)
    desktop_file = File.join(Dir.home, '.local', 'share', 'applications', 'shepherd.desktop')
    
    # Remove script
    if File.exist?(script_dest)
      puts "Removing #{script_dest}..."
      FileUtils.rm(script_dest)
    end
    
    # Remove desktop entry
    if File.exist?(desktop_file)
      puts "Removing #{desktop_file}..."
      FileUtils.rm(desktop_file)
      system('update-desktop-database', File.join(Dir.home, '.local', 'share', 'applications'))
    end
    
    puts "✅ Shepherd uninstalled successfully!"
    puts "Note: Configuration files in ~/.config/shepherd/ were preserved"
  end
  
  def self.run(args)
    case args[0]
    when 'install', nil
      install
    when 'uninstall'
      uninstall
    else
      puts <<~USAGE
        Usage: ruby setup.rb [command]
        
        Commands:
          install    - Install shepherd system-wide (default)
          uninstall  - Remove shepherd installation
        
        Environment variables:
          PREFIX     - Installation prefix (default: /usr/local)
      USAGE
    end
  end
end

# Run if executed directly
if __FILE__ == $0
  # Check for sudo if trying to install to system directories
  if ARGV[0] != 'uninstall' && !ENV['PREFIX']
    prefix = '/usr/local'
    if !File.writable?(File.join(prefix, 'bin'))
      puts "Error: Cannot write to #{prefix}/bin"
      puts "Run with sudo: sudo ruby setup.rb install"
      puts "Or specify a different prefix: PREFIX=$HOME/.local ruby setup.rb install"
      exit 1
    end
  end
  
  Setup.run(ARGV)
end