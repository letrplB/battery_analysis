#!/bin/bash

# Create Desktop Shortcut/App for Battery Cycle Analyzer (Mac/Linux)

echo "========================================="
echo "   Creating Desktop Shortcut"
echo "========================================="
echo ""

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Detect the operating system
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "Detected macOS"
    echo "Creating application bundle..."
    
    # Create the app bundle structure
    APP_NAME="Battery Cycle Analyzer"
    APP_DIR="$HOME/Desktop/$APP_NAME.app"
    CONTENTS_DIR="$APP_DIR/Contents"
    MACOS_DIR="$CONTENTS_DIR/MacOS"
    RESOURCES_DIR="$CONTENTS_DIR/Resources"
    
    # Remove old app if it exists
    if [ -d "$APP_DIR" ]; then
        rm -rf "$APP_DIR"
    fi
    
    # Create directories
    mkdir -p "$MACOS_DIR"
    mkdir -p "$RESOURCES_DIR"
    
    # Create the launcher script
    cat > "$MACOS_DIR/launcher" << 'EOF'
#!/bin/bash

# Get the directory of the app bundle
APP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_DIR="$(dirname "$(dirname "$APP_DIR")")"

# Get the actual script location from the symlink
REAL_SCRIPT="$(readlink "$APP_DIR/Contents/Resources/launch_script.sh")"

# Change to the battery_analysis directory and run the launcher
cd "$(dirname "$REAL_SCRIPT")"

# Open Terminal and run the launcher
osascript -e "tell application \"Terminal\"
    activate
    do script \"cd '$(dirname "$REAL_SCRIPT")' && ./launch_battery_analyzer.sh\"
end tell"
EOF
    
    chmod +x "$MACOS_DIR/launcher"
    
    # Create a symlink to the actual launcher script
    ln -s "$SCRIPT_DIR/launch_battery_analyzer.sh" "$RESOURCES_DIR/launch_script.sh"
    
    # Create Info.plist
    cat > "$CONTENTS_DIR/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>Battery Cycle Analyzer</string>
    <key>CFBundleDisplayName</key>
    <string>Battery Cycle Analyzer</string>
    <key>CFBundleIdentifier</key>
    <string>com.battery-analysis.battery-cycle-analyzer</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
    <key>CFBundleIconFile</key>
    <string>icon.icns</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.10.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF
    
    echo ""
    echo "========================================="
    echo "   SUCCESS!"
    echo "========================================="
    echo ""
    echo "Application bundle created on Desktop:"
    echo "  $APP_DIR"
    echo ""
    echo "You can now double-click 'Battery Cycle Analyzer' on your Desktop!"
    echo ""
    
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo "Detected Linux"
    echo "Creating desktop entry..."
    
    # Create .desktop file
    DESKTOP_FILE="$HOME/Desktop/battery-cycle-analyzer.desktop"
    
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Battery Cycle Analyzer
Comment=Analyze battery cycle data
Exec=$SCRIPT_DIR/launch_battery_analyzer.sh
Path=$SCRIPT_DIR
Icon=battery
Terminal=true
Categories=Science;Engineering;
EOF
    
    # Make it executable
    chmod +x "$DESKTOP_FILE"
    
    # Also install to applications menu
    APPS_DIR="$HOME/.local/share/applications"
    mkdir -p "$APPS_DIR"
    cp "$DESKTOP_FILE" "$APPS_DIR/"
    
    echo ""
    echo "========================================="
    echo "   SUCCESS!"
    echo "========================================="
    echo ""
    echo "Desktop shortcut created:"
    echo "  $DESKTOP_FILE"
    echo ""
    echo "Application also added to menu"
    echo ""
    
else
    echo "Unsupported operating system: $OSTYPE"
    exit 1
fi

echo "Press Enter to exit..."
read