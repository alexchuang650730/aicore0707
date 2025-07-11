# PowerAutomation + ClaudeEditor v4.5.1 Installation Guide

## 📋 Pre-Installation Checklist

### System Requirements Verification
Before installing, please verify your system meets the requirements:

```bash
# Check macOS version
sw_vers

# Check available disk space (need at least 500MB)
df -h /Applications

# Check memory (recommended 8GB+)
system_profiler SPHardwareDataType | grep "Memory:"
```

### Required Components
- **macOS**: 10.15 (Catalina) or later
- **Xcode Command Line Tools**: For development features
- **Internet Connection**: For Claude API access

## 🚀 Installation Methods

### Method 1: Direct Download (Recommended)

1. **Download the installer**:
   ```bash
   # Create download directory
   mkdir -p ~/Downloads/PowerAutomation
   cd ~/Downloads/PowerAutomation
   
   # Download the main installer
   curl -L -o PowerAutomation_ClaudeEditor_v4.5.1_Mac.dmg \
     "https://github.com/alexchuang650730/aicore0707/releases/download/v4.5.1/PowerAutomation_ClaudeEditor_v4.5.1_Mac.dmg"
   
   # Download checksum for verification
   curl -L -o PowerAutomation_ClaudeEditor_v4.5.1_Mac.dmg.sha256 \
     "https://github.com/alexchuang650730/aicore0707/releases/download/v4.5.1/PowerAutomation_ClaudeEditor_v4.5.1_Mac.dmg.sha256"
   ```

2. **Verify the download**:
   ```bash
   # Check file integrity
   shasum -a 256 PowerAutomation_ClaudeEditor_v4.5.1_Mac.dmg
   cat PowerAutomation_ClaudeEditor_v4.5.1_Mac.dmg.sha256
   
   # The hashes should match
   ```

3. **Install the application**:
   ```bash
   # Mount the disk image
   hdiutil attach PowerAutomation_ClaudeEditor_v4.5.1_Mac.dmg
   
   # Copy to Applications (you can also drag and drop)
   cp -R "/Volumes/PowerAutomation v4.5.1/PowerAutomation.app" /Applications/
   
   # Unmount the disk image
   hdiutil detach "/Volumes/PowerAutomation v4.5.1"
   ```

### Method 2: GitHub Releases

1. **Visit the releases page**:
   - Go to: https://github.com/alexchuang650730/aicore0707/releases/tag/v4.5.1
   - Download `PowerAutomation_ClaudeEditor_v4.5.1_Mac.dmg`

2. **Install via Finder**:
   - Double-click the downloaded .dmg file
   - Drag PowerAutomation.app to Applications folder
   - Eject the disk image

## 🔧 Post-Installation Setup

### 1. First Launch Configuration

```bash
# Launch the application for the first time
open /Applications/PowerAutomation.app

# Or from terminal
/Applications/PowerAutomation.app/Contents/MacOS/PowerAutomation
```

### 2. Security Settings

If you see a security warning:

1. **Go to System Preferences**:
   ```bash
   open "x-apple.systempreferences:com.apple.preference.security"
   ```

2. **Allow the application**:
   - Click "Allow" next to the PowerAutomation entry
   - Or enable "App Store and identified developers"

3. **Alternative method**:
   ```bash
   # Remove quarantine attribute
   sudo xattr -rd com.apple.quarantine /Applications/PowerAutomation.app
   ```

### 3. Workspace Setup

```bash
# Create default workspace
mkdir -p ~/PowerAutomation
cd ~/PowerAutomation

# Create configuration directory
mkdir -p ~/.powerautomation

# Create logs directory
mkdir -p ~/Library/Logs/PowerAutomation
```

### 4. Environment Configuration

Create or update your shell profile:

```bash
# For zsh (default on macOS Catalina+)
echo 'export POWERAUTOMATION_WORKSPACE="$HOME/PowerAutomation"' >> ~/.zshrc
echo 'export PATH="$PATH:/Applications/PowerAutomation.app/Contents/MacOS"' >> ~/.zshrc

# For bash
echo 'export POWERAUTOMATION_WORKSPACE="$HOME/PowerAutomation"' >> ~/.bash_profile
echo 'export PATH="$PATH:/Applications/PowerAutomation.app/Contents/MacOS"' >> ~/.bash_profile

# Reload shell configuration
source ~/.zshrc  # or source ~/.bash_profile
```

## ⚙️ Configuration

### 1. Basic Configuration

Create the main configuration file:

```bash
cat > ~/PowerAutomation/config.json << 'EOF'
{
  "version": "4.5.1",
  "local_path": "/Users/$USER/PowerAutomation",
  "claude_integration": {
    "sync_enabled": true,
    "claudeditor_websocket": "ws://localhost:8081/socket.io/",
    "local_adapter_integration": {
      "default_working_dir": "/Users/$USER/PowerAutomation",
      "command_timeout": 300
    },
    "result_capture": {
      "max_buffer_size": 10000,
      "auto_format": true,
      "format_types": ["html", "markdown", "raw"]
    }
  },
  "mirror_engine": {
    "websocket_port": 8080,
    "max_connections": 10
  },
  "logging": {
    "level": "INFO",
    "file": "/Users/$USER/Library/Logs/PowerAutomation/app.log"
  }
}
EOF

# Replace $USER with actual username
sed -i '' "s/\$USER/$(whoami)/g" ~/PowerAutomation/config.json
```

### 2. Claude API Configuration (Optional)

If you plan to use Claude API directly:

```bash
# Set up Claude API key (replace with your actual key)
echo 'export CLAUDE_API_KEY="your_api_key_here"' >> ~/.zshrc
source ~/.zshrc

# Or create a dedicated config file
cat > ~/.powerautomation/claude.conf << 'EOF'
CLAUDE_API_KEY=your_api_key_here
CLAUDE_MODEL=claude-sonnet-4-20250514
EOF
```

### 3. Advanced Configuration

For advanced users, create additional configuration files:

```bash
# Mirror Code specific configuration
cat > ~/PowerAutomation/mirror_config.json << 'EOF'
{
  "sync": {
    "auto_sync": true,
    "sync_interval": 5,
    "conflict_resolution": "latest_wins"
  },
  "communication": {
    "websocket_port": 8080,
    "max_connections": 10,
    "heartbeat_interval": 30
  },
  "file_monitor": {
    "ignore_patterns": [".git/*", "node_modules/*", "*.tmp", "*.log"],
    "debounce_delay": 0.5
  }
}
EOF

# Local Adapter configuration
cat > ~/PowerAutomation/local_adapter_config.json << 'EOF'
{
  "platform": "macos",
  "terminal": {
    "default_shell": "/bin/zsh",
    "timeout": 300,
    "max_output_size": "10MB"
  },
  "security": {
    "allowed_commands": ["claude", "python", "node", "npm"],
    "restricted_paths": ["/System", "/usr/bin/sudo"]
  }
}
EOF
```

## 🧪 Installation Verification

### 1. Basic Functionality Test

```bash
# Test application launch
/Applications/PowerAutomation.app/Contents/MacOS/PowerAutomation --version

# Test workspace access
ls -la ~/PowerAutomation/

# Test configuration loading
cat ~/PowerAutomation/config.json | python -m json.tool
```

### 2. Component Test

```bash
# Navigate to workspace
cd ~/PowerAutomation

# Test Mirror Code integration (if available)
python -c "
try:
    from core.mirror_code.engine.mirror_engine import MirrorEngine
    print('✅ Mirror Code integration available')
except ImportError as e:
    print(f'❌ Mirror Code integration not available: {e}')
"

# Test Local Adapter integration (if available)
python -c "
try:
    from core.components.local_adapter_mcp.local_adapter_engine import LocalAdapterEngine
    print('✅ Local Adapter MCP available')
except ImportError as e:
    print(f'❌ Local Adapter MCP not available: {e}')
"
```

### 3. Network Connectivity Test

```bash
# Test WebSocket ports
nc -z localhost 8080 && echo "✅ Port 8080 available" || echo "❌ Port 8080 not available"
nc -z localhost 8081 && echo "✅ Port 8081 available" || echo "❌ Port 8081 not available"

# Test internet connectivity
curl -s https://api.anthropic.com > /dev/null && echo "✅ Claude API reachable" || echo "❌ Claude API not reachable"
```

## 🔍 Troubleshooting Installation Issues

### Common Installation Problems

#### 1. "App is damaged and can't be opened"

**Solution**:
```bash
# Remove quarantine attribute
sudo xattr -rd com.apple.quarantine /Applications/PowerAutomation.app

# Or re-download the installer
rm ~/Downloads/PowerAutomation_ClaudeEditor_v4.5.1_Mac.dmg
# Re-download using the commands above
```

#### 2. "PowerAutomation can't be opened because it is from an unidentified developer"

**Solution**:
```bash
# Method 1: System Preferences
open "x-apple.systempreferences:com.apple.preference.security"
# Click "Open Anyway" next to PowerAutomation

# Method 2: Command line
sudo spctl --master-disable  # Temporarily disable Gatekeeper
# Launch the app, then re-enable:
sudo spctl --master-enable
```

#### 3. Insufficient disk space

**Solution**:
```bash
# Check available space
df -h /Applications

# Clean up if needed
# Empty Trash
# Remove old applications
# Use Storage Management in About This Mac
```

#### 4. Permission denied errors

**Solution**:
```bash
# Fix application permissions
sudo chown -R $(whoami):staff /Applications/PowerAutomation.app
sudo chmod -R 755 /Applications/PowerAutomation.app

# Fix workspace permissions
sudo chown -R $(whoami):staff ~/PowerAutomation
chmod -R 755 ~/PowerAutomation
```

### Installation Verification Failures

#### 1. Configuration file errors

**Solution**:
```bash
# Validate JSON configuration
python -m json.tool ~/PowerAutomation/config.json

# Reset to default if corrupted
rm ~/PowerAutomation/config.json
# Re-run the configuration setup commands above
```

#### 2. Missing dependencies

**Solution**:
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install Python dependencies (if needed)
pip3 install --user asyncio websockets
```

#### 3. Port conflicts

**Solution**:
```bash
# Find processes using required ports
lsof -i :8080
lsof -i :8081

# Kill conflicting processes if safe to do so
sudo kill -9 <PID>

# Or configure different ports in config.json
```

## 🔄 Uninstallation

If you need to remove PowerAutomation:

### Complete Removal

```bash
# Remove application
sudo rm -rf /Applications/PowerAutomation.app

# Remove user data (optional - backup first!)
rm -rf ~/PowerAutomation
rm -rf ~/.powerautomation

# Remove logs
rm -rf ~/Library/Logs/PowerAutomation

# Remove environment variables
# Edit ~/.zshrc or ~/.bash_profile and remove PowerAutomation-related lines

# Clear system caches
sudo rm -rf /Library/Caches/com.powerautomation.*
rm -rf ~/Library/Caches/com.powerautomation.*
```

### Selective Removal (Keep User Data)

```bash
# Remove only the application
sudo rm -rf /Applications/PowerAutomation.app

# Keep ~/PowerAutomation and configuration files for future reinstallation
```

## 📞 Getting Help

### Installation Support

If you encounter issues during installation:

1. **Check the logs**:
   ```bash
   # System logs
   log show --predicate 'process == "PowerAutomation"' --last 1h
   
   # Application logs (after first launch)
   tail -f ~/Library/Logs/PowerAutomation/app.log
   ```

2. **Gather system information**:
   ```bash
   # Create a support bundle
   system_profiler SPSoftwareDataType SPHardwareDataType > ~/Desktop/system_info.txt
   ls -la /Applications/PowerAutomation.app >> ~/Desktop/system_info.txt
   ```

3. **Contact support**:
   - **GitHub Issues**: https://github.com/alexchuang650730/aicore0707/issues
   - **Include**: System info, error messages, installation steps attempted

### Useful Commands for Support

```bash
# Check installation integrity
codesign -v /Applications/PowerAutomation.app

# Check system compatibility
sw_vers | grep ProductVersion

# Check available resources
vm_stat | head -5
df -h /Applications
```

---

**Installation Guide Version**: 1.0  
**Compatible with**: PowerAutomation v4.5.1  
**Last Updated**: July 10, 2025  
**Platform**: macOS 10.15+

