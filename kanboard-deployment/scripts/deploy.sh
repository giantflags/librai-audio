#!/bin/bash

################################################################################
# Kanboard Automated Deployment Script
#
# This script automates the deployment of Kanboard with Google OAuth
# and validates configuration to prevent common issues.
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo ""
    echo -e "${GREEN}===================================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}===================================================${NC}"
    echo ""
}

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        print_error "$1 is not installed"
        return 1
    else
        print_info "$1 is installed ✓"
        return 0
    fi
}

################################################################################
# Main Script
################################################################################

print_header "Kanboard Automated Deployment"

echo -e "${BLUE}This script will:${NC}"
echo "  1. Check prerequisites (Docker, Docker Compose)"
echo "  2. Validate configuration files"
echo "  3. Deploy Kanboard with your settings"
echo "  4. Verify the deployment is working"
echo ""

# Step 1: Check prerequisites
print_header "Step 1: Checking Prerequisites"

MISSING_DEPS=0

if ! check_command docker; then
    print_error "Please install Docker: https://docs.docker.com/engine/install/"
    MISSING_DEPS=1
fi

# Check for docker-compose or docker compose plugin
if ! check_command docker-compose; then
    if docker compose version &> /dev/null 2>&1; then
        print_info "Docker Compose V2 (plugin) is installed ✓"
        COMPOSE_CMD="docker compose"
    else
        print_error "Please install Docker Compose: https://docs.docker.com/compose/install/"
        MISSING_DEPS=1
    fi
else
    print_info "Docker Compose is installed ✓"
    COMPOSE_CMD="docker-compose"
fi

if [ $MISSING_DEPS -eq 1 ]; then
    print_error "Missing required dependencies. Please install them and try again."
    exit 1
fi

# Step 2: Check configuration files
print_header "Step 2: Configuration Validation"

cd "$SCRIPT_DIR"

# Check for .env file
if [ ! -f ".env" ]; then
    print_warning ".env file not found"
    print_info "Creating .env from template..."
    cp .env.example .env

    print_warning "Please edit .env file with your settings:"
    print_warning "  1. Set APPLICATION_URL to your domain"
    print_warning "  2. Add your Google OAuth Client ID and Secret"
    echo ""

    read -p "Press Enter to open .env in editor (or Ctrl+C to exit and edit manually)..."

    if command -v nano &> /dev/null; then
        nano .env
    elif command -v vim &> /dev/null; then
        vim .env
    else
        print_error "No editor found. Please edit .env manually and run this script again."
        exit 1
    fi
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Validate critical environment variables
print_info "Validating environment variables..."

VALIDATION_FAILED=0

if [[ -z "$APPLICATION_URL" ]]; then
    print_error "APPLICATION_URL not set in .env"
    VALIDATION_FAILED=1
elif [[ "$APPLICATION_URL" == *"REPLACE"* ]] || [[ "$APPLICATION_URL" == *"your-domain"* ]]; then
    print_error "APPLICATION_URL still contains placeholder value"
    VALIDATION_FAILED=1
else
    print_success "APPLICATION_URL: $APPLICATION_URL"
fi

if [[ -z "$GOOGLE_CLIENT_ID" ]] || [[ "$GOOGLE_CLIENT_ID" == *"YOUR_CLIENT_ID"* ]]; then
    print_error "GOOGLE_CLIENT_ID not set in .env"
    VALIDATION_FAILED=1
else
    print_success "GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID:0:20}..."
fi

if [[ -z "$GOOGLE_CLIENT_SECRET" ]] || [[ "$GOOGLE_CLIENT_SECRET" == *"YOUR_CLIENT_SECRET"* ]]; then
    print_error "GOOGLE_CLIENT_SECRET not set in .env"
    VALIDATION_FAILED=1
else
    print_success "GOOGLE_CLIENT_SECRET: (set)"
fi

if [ $VALIDATION_FAILED -eq 1 ]; then
    print_error "Configuration validation failed"
    print_error "Please update .env file with correct values and run again"
    exit 1
fi

# Check for config.php
if [ ! -f "config.php" ]; then
    print_warning "config.php not found"
    print_info "Creating config.php from template..."
    cp config.php.template config.php

    print_info "Populating config.php with .env values..."

    # Replace placeholders with actual values from .env
    sed -i "s|REPLACE_WITH_YOUR_DOMAIN|${APPLICATION_URL}|g" config.php
    sed -i "s|REPLACE_WITH_YOUR_CLIENT_ID|${GOOGLE_CLIENT_ID}|g" config.php
    sed -i "s|REPLACE_WITH_YOUR_CLIENT_SECRET|${GOOGLE_CLIENT_SECRET}|g" config.php

    print_success "config.php created and configured"
else
    print_info "config.php already exists"
fi

# Validate config.php syntax
print_info "Validating config.php syntax..."

if command -v php &> /dev/null; then
    if php -l config.php &> /dev/null; then
        print_success "config.php syntax is valid"
    else
        print_error "config.php has syntax errors:"
        php -l config.php
        exit 1
    fi
else
    print_warning "PHP not installed - skipping config.php syntax validation"
fi

# Step 3: Check if container already exists
print_header "Step 3: Docker Container Management"

if docker ps -a --format '{{.Names}}' | grep -q "^kanboard$"; then
    print_warning "Kanboard container already exists"

    read -p "$(echo -e "${YELLOW}Stop and recreate container? (y/n): ${NC}")" -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Stopping and removing existing container..."
        docker stop kanboard 2>/dev/null || true
        docker rm kanboard 2>/dev/null || true
        print_success "Existing container removed"
    else
        print_info "Keeping existing container"
        print_warning "Note: Config changes may not take effect until container is recreated"
    fi
fi

# Step 4: Deploy Kanboard
print_header "Step 4: Deploying Kanboard"

print_info "Pulling latest Kanboard image..."
docker pull kanboard/kanboard:latest

print_info "Starting Kanboard with Docker Compose..."
$COMPOSE_CMD up -d

print_info "Waiting for Kanboard to start..."
sleep 5

# Check if container is running
if docker ps --format '{{.Names}}' | grep -q "^kanboard$"; then
    print_success "Kanboard container is running ✓"
else
    print_error "Kanboard container failed to start"
    print_error "Check logs with: docker logs kanboard"
    exit 1
fi

# Step 5: Verify deployment
print_header "Step 5: Verifying Deployment"

# Wait a bit more for full startup
sleep 3

# Test local access
print_info "Testing local access..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080 2>/dev/null || echo "000")

if [[ "$HTTP_CODE" == "200" ]]; then
    print_success "Kanboard is responding on localhost:8080 ✓"
else
    print_warning "Kanboard returned HTTP $HTTP_CODE on localhost:8080"
    print_info "This may be normal during startup. Check logs: docker logs kanboard"
fi

# Test OAuth endpoint
print_info "Testing OAuth endpoint..."
OAUTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/oauth/google 2>/dev/null || echo "000")

if [[ "$OAUTH_CODE" == "302" ]]; then
    print_success "OAuth endpoint is responding correctly ✓"
else
    print_warning "OAuth endpoint returned HTTP $OAUTH_CODE"
    print_info "This may require Google OAuth configuration in Cloud Console"
fi

# Step 6: Display summary
print_header "Deployment Complete! 🎉"

echo ""
print_success "Kanboard is now running!"
echo ""
echo -e "${BLUE}Access Information:${NC}"
echo "  Local:  http://localhost:8080"
echo "  Public: $APPLICATION_URL"
echo ""
echo -e "${BLUE}Default Admin Credentials:${NC}"
echo "  Username: admin"
echo "  Password: admin"
echo -e "  ${RED}⚠️  CHANGE THESE IMMEDIATELY!${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "  1. Open your browser and go to: $APPLICATION_URL"
echo "  2. Login with admin/admin and change the password"
echo "  3. Configure Google OAuth redirect URI in Cloud Console:"
echo "     ${APPLICATION_URL}/oauth/google/callback"
echo "  4. Test OAuth login by clicking 'Login with Google'"
echo "  5. Grant admin access to your OAuth account"
echo "  6. Optionally disable the default admin account"
echo ""
echo -e "${BLUE}Useful Commands:${NC}"
echo "  View logs:         docker logs -f kanboard"
echo "  Restart:           docker restart kanboard"
echo "  Stop:              docker-compose down"
echo "  Update:            docker-compose pull && docker-compose up -d"
echo "  Backup:            docker run --rm --volumes-from kanboard \\"
echo "                       -v \$(pwd):/backup alpine tar -czf \\"
echo "                       /backup/kanboard-backup-\$(date +%F).tar.gz /var/www/app/data"
echo ""
echo -e "${BLUE}Troubleshooting:${NC}"
echo "  If OAuth redirect fails:"
echo "    1. Verify APPLICATION_URL in .env matches your domain exactly"
echo "    2. Ensure Google OAuth redirect URI is: ${APPLICATION_URL}/oauth/google/callback"
echo "    3. Check logs: docker logs kanboard | grep -i oauth"
echo "    4. Restart: docker restart kanboard"
echo ""
echo -e "${BLUE}Documentation:${NC}"
echo "  README:            cat README.md"
echo "  OAuth Setup:       cat docs/OAUTH_SETUP.md"
echo "  Quick Fix Guide:   cat docs/QUICK_FIX.md"
echo ""

print_success "Deployment successful! Happy project managing! 🚀"

exit 0
