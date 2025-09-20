# Rakefile for Shepherd Browser Router

require 'rake'
require 'rake/testtask'

desc 'Run tests'
Rake::TestTask.new(:test) do |t|
  t.libs << 'test'
  t.test_files = FileList['test_shepherd.rb']
  t.verbose = true
end

desc 'Install shepherd system-wide'
task :install do
  ruby 'setup.rb', 'install'
end

desc 'Uninstall shepherd'
task :uninstall do
  ruby 'setup.rb', 'uninstall'
end

desc 'Run shepherd with a test URL'
task :run, [:url] do |t, args|
  url = args[:url] || 'https://example.com'
  ruby 'shepherd.rb', url
end

desc 'Clean up generated files'
task :clean do
  # Clean up any temp files or logs if needed
  log_file = File.join(ENV['XDG_STATE_HOME'] || File.join(Dir.home, '.local', 'state'), 'shepherd', 'shepherd.log')
  if File.exist?(log_file) && ENV['CLEAN_LOGS']
    puts "Cleaning log file: #{log_file}"
    File.delete(log_file)
  end
end

desc 'Show version'
task :version do
  puts "Shepherd version: #{VERSION}"
end

# Default task
task default: :test