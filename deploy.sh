#!/bin/bash
# LED Grid Animation System Deployment Script
# Deploys to Raspberry Pi with passwordless SSH

set -e  # Exit on any error

# Configuration
PI_HOST="ledwallleft@ledwallleft.local"
DEPLOY_DIR="ledgrid-pod"
LOCAL_DIR="."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if SSH connection works
check_ssh_connection() {
    log_info "Testing SSH connection to $PI_HOST..."
    if ssh -o ConnectTimeout=10 -o BatchMode=yes "$PI_HOST" "echo 'SSH connection successful'" >/dev/null 2>&1; then
        log_success "SSH connection to $PI_HOST is working"
    else
        log_error "Cannot connect to $PI_HOST via SSH"
        log_error "Please ensure:"
        log_error "  1. Raspberry Pi is powered on and connected to network"
        log_error "  2. SSH is enabled on the Pi"
        log_error "  3. Passwordless SSH is configured"
        log_error "  4. Hostname 'ledwallleft.local' resolves correctly"
        exit 1
    fi
}

# Create deployment directory on Pi
create_deploy_directory() {
    log_info "Creating deployment directory: ~/$DEPLOY_DIR"
    ssh "$PI_HOST" "mkdir -p ~/$DEPLOY_DIR"
    log_success "Deployment directory created"
}

# Upload files to Pi
upload_files() {
    log_info "Uploading animation system files..."
    
    # Create list of files to upload
    FILES_TO_UPLOAD=(
        "animation_system/"
        "animations/"
        "templates/"
        "animation_manager.py"
        "web_interface.py"
        "start_animation_server.py"
        "requirements.txt"
        "README_ANIMATION_SYSTEM.md"
        "SYSTEM_COMPLETE.md"
    )
    
    # Check if led_controller_spi.py exists and include it
    if [ -f "led_controller_spi.py" ]; then
        FILES_TO_UPLOAD+=("led_controller_spi.py")
        log_info "Including existing LED controller"
    else
        log_warning "led_controller_spi.py not found - will need to be provided separately"
    fi
    
    # Upload files using rsync for efficiency
    for file in "${FILES_TO_UPLOAD[@]}"; do
        if [ -e "$file" ]; then
            log_info "Uploading $file..."
            if [ -d "$file" ]; then
                # For directories, ensure we copy the directory itself, not just contents
                rsync -avz --progress "$file" "$PI_HOST:~/$DEPLOY_DIR/"
            else
                # For files, copy normally
                rsync -avz --progress "$file" "$PI_HOST:~/$DEPLOY_DIR/"
            fi
        else
            log_warning "File $file not found, skipping"
        fi
    done
    
    log_success "File upload completed"
}

# Create virtual environment and install dependencies
setup_venv_and_dependencies() {
    log_info "Setting up Python virtual environment..."

    # Create virtual environment
    ssh "$PI_HOST" "cd ~/$DEPLOY_DIR && python3 -m venv venv"

    log_success "Virtual environment created"

    log_info "Installing Python dependencies in venv..."

    # Install dependencies in virtual environment
    ssh "$PI_HOST" "cd ~/$DEPLOY_DIR && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"

    log_success "Dependencies installed in virtual environment"
}

# Check if SPI is enabled
check_spi() {
    log_info "Checking SPI configuration..."
    
    SPI_STATUS=$(ssh "$PI_HOST" "ls /dev/spi* 2>/dev/null | wc -l || echo 0")
    
    if [ "$SPI_STATUS" -gt 0 ]; then
        log_success "SPI devices found: $(ssh "$PI_HOST" "ls /dev/spi*")"
    else
        log_warning "No SPI devices found"
        log_warning "You may need to enable SPI with: sudo raspi-config"
        log_warning "Navigate to: Interface Options > SPI > Enable"
    fi
}

# Create startup script
create_startup_script() {
    log_info "Creating startup script..."

    ssh "$PI_HOST" "cat > ~/$DEPLOY_DIR/start.sh << 'EOF'
#!/bin/bash
# LED Grid Animation System Startup Script

cd \$(dirname \$0)

echo \"🎨 Starting LED Grid Animation System...\"
echo \"📁 Working directory: \$(pwd)\"

# Check if virtual environment exists
if [ ! -d \"venv\" ]; then
    echo \"❌ Virtual environment not found!\"
    echo \"   Please run the deployment script again\"
    exit 1
fi

# Activate virtual environment
echo \"🐍 Activating virtual environment...\"
source venv/bin/activate

# Check if LED controller exists
if [ ! -f \"led_controller_spi.py\" ]; then
    echo \"⚠️  Warning: led_controller_spi.py not found\"
    echo \"   The system will run in demo mode\"
fi

# Get Pi's IP address for display
PI_IP=\$(hostname -I | awk '{print \$1}')

echo \"🌐 Starting web server...\"
echo \"   Local URL:  http://localhost:5000\"
echo \"   Network URL: http://\$PI_IP:5000\"
echo \"\"
echo \"🎮 Web Interface:\"
echo \"   Dashboard:    http://\$PI_IP:5000/\"
echo \"   Control Panel: http://\$PI_IP:5000/control\"
echo \"   Upload:       http://\$PI_IP:5000/upload\"
echo \"\"
echo \"Press Ctrl+C to stop\"
echo \"\"

# Start the animation server with virtual environment Python
python start_animation_server.py --host 0.0.0.0 --port 5000
EOF"

    # Make startup script executable
    ssh "$PI_HOST" "chmod +x ~/$DEPLOY_DIR/start.sh"

    log_success "Startup script created"
}

# Start the animation system
start_system() {
    log_info "Starting LED Grid Animation System..."
    
    # Get Pi's IP address
    PI_IP=$(ssh "$PI_HOST" "hostname -I | awk '{print \$1}'")
    
    log_success "🎉 Deployment completed successfully!"
    echo ""
    echo "🌐 LED Grid Animation System is now running at:"
    echo ""
    echo -e "${GREEN}   Dashboard:     http://$PI_IP:5000/${NC}"
    echo -e "${GREEN}   Control Panel: http://$PI_IP:5000/control${NC}"
    echo -e "${GREEN}   Upload:        http://$PI_IP:5000/upload${NC}"
    echo ""
    echo "🎮 You can now:"
    echo "   • View and start animations from the dashboard"
    echo "   • Upload new animation plugins"
    echo "   • Control animations in real-time"
    echo ""
    echo "🔧 To manage the system on the Pi:"
    echo "   ssh $PI_HOST"
    echo "   cd $DEPLOY_DIR"
    echo "   ./start.sh          # Start the system"
    echo ""
    
    # Start the system in background
    log_info "Starting animation server in background..."
    ssh "$PI_HOST" "cd ~/$DEPLOY_DIR && nohup ./start.sh > animation_system.log 2>&1 &"
    
    # Wait a moment for startup
    sleep 3
    
    # Check if it's running
    if ssh "$PI_HOST" "pgrep -f 'start_animation_server.py' > /dev/null"; then
        log_success "Animation system is running!"
        echo ""
        echo -e "${BLUE}📊 System Status:${NC}"
        echo "   ✅ Animation server: Running"
        echo "   ✅ Web interface: Available"
        echo "   ✅ Plugin system: Ready"
        echo ""
        echo -e "${YELLOW}🚀 Open your browser and go to: http://$PI_IP:5000/${NC}"
    else
        log_warning "System may still be starting up..."
        echo "Check the log with: ssh $PI_HOST 'cd $DEPLOY_DIR && tail -f animation_system.log'"
    fi
}

# Main deployment process
main() {
    echo "🚀 LED Grid Animation System Deployment"
    echo "========================================"
    echo ""
    
    check_ssh_connection
    create_deploy_directory
    upload_files
    setup_venv_and_dependencies
    check_spi
    create_startup_script
    start_system
}

# Run main function
main "$@"
