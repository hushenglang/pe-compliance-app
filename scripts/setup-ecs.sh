#!/bin/bash

# ECS Server Setup Script for PE Compliance App
# This script prepares an Alibaba Cloud ECS server for Docker deployment

set -e

echo "🚀 Setting up ECS server for PE Compliance App deployment..."

# Update system packages
echo "📦 Updating system packages..."
sudo yum update -y

# Install Docker if not already installed
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    sudo yum install -y docker
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # Add current user to docker group
    sudo usermod -aG docker $USER
    echo "✅ Docker installed and configured"
else
    echo "✅ Docker is already installed"
fi

# Install essential tools
echo "🔧 Installing essential tools..."
sudo yum install -y curl wget git

# Create deployment directory
DEPLOY_DIR="$HOME/deployments/pe-compliance-app"
echo "📁 Creating deployment directory: $DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR"
cd "$DEPLOY_DIR"

# Download environment template
if [ ! -f .env ]; then
    echo "📝 Creating environment file template..."
    cat > .env << 'EOF'
# PE Compliance App Environment Configuration
# Fill in the actual values for your environment

# Application Configuration
APP_ENV=production
LOG_LEVEL=INFO

# OpenRouter Configuration (for AI services)
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Database Configuration
DATABASE_URL=mysql+pymysql://username:password@host:port/database_name
DB_HOST=your_database_host
DB_PORT=3306
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_NAME=your_database_name

# SFC Configuration
SFC_BASE_URL=https://www.sfc.hk
SFC_NEWS_ENDPOINT=/web/EN/regulatory-functions/news/

# Application Security (optional but recommended)
SECRET_KEY=your_application_secret_key_here
JWT_SECRET=your_jwt_secret_key_here

# Network Configuration
HOST=0.0.0.0
PORT=8000

# Development/Debug flags
DEBUG=false
RELOAD=false
EOF

    # Secure the environment file
    chmod 600 .env
    echo "✅ Environment file created at $DEPLOY_DIR/.env"
    echo "⚠️  IMPORTANT: Edit the .env file with your actual configuration values!"
else
    echo "✅ Environment file already exists"
fi

# Configure firewall (if firewalld is running)
if systemctl is-active --quiet firewalld; then
    echo "🔥 Configuring firewall..."
    sudo firewall-cmd --permanent --add-port=8000/tcp
    sudo firewall-cmd --permanent --add-port=22/tcp
    sudo firewall-cmd --reload
    echo "✅ Firewall configured to allow ports 8000 and 22"
fi

# Create log directory
sudo mkdir -p /var/log/pe-compliance-app
sudo chown $USER:$USER /var/log/pe-compliance-app

# Create a simple health check script
cat > health-check.sh << 'EOF'
#!/bin/bash
# Simple health check script for the application

CONTAINER_NAME="pe-compliance-app-container"

if docker ps --filter "name=$CONTAINER_NAME" --filter "status=running" --quiet | grep -q .; then
    echo "✅ Container is running"
    
    # Check if the health endpoint responds
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Health endpoint is responding"
        exit 0
    else
        echo "❌ Health endpoint is not responding"
        echo "Container logs:"
        docker logs --tail 10 $CONTAINER_NAME
        exit 1
    fi
else
    echo "❌ Container is not running"
    exit 1
fi
EOF

chmod +x health-check.sh

# Create a deployment status script
cat > status.sh << 'EOF'
#!/bin/bash
# Check deployment status

CONTAINER_NAME="pe-compliance-app-container"

echo "=== PE Compliance App Deployment Status ==="
echo ""

# Container status
echo "📦 Container Status:"
if docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -q "$CONTAINER_NAME"; then
    docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
else
    echo "❌ Container not found or not running"
fi

echo ""

# Resource usage
echo "💾 Resource Usage:"
if docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" "$CONTAINER_NAME" 2>/dev/null; then
    :
else
    echo "❌ Cannot get resource usage (container not running)"
fi

echo ""

# Recent logs
echo "📄 Recent Logs (last 10 lines):"
if docker logs --tail 10 "$CONTAINER_NAME" 2>/dev/null; then
    :
else
    echo "❌ Cannot get logs (container not running)"
fi

echo ""

# Health check
echo "🏥 Health Check:"
./health-check.sh

echo ""
echo "=== End Status Report ==="
EOF

chmod +x status.sh

# Display setup completion message
echo ""
echo "🎉 ECS server setup completed successfully!"
echo ""
echo "📍 Setup Summary:"
echo "   - Docker installed and configured"
echo "   - Deployment directory created: $DEPLOY_DIR"
echo "   - Environment file template created: $DEPLOY_DIR/.env"
echo "   - Firewall configured (if applicable)"
echo "   - Health check script created: $DEPLOY_DIR/health-check.sh"
echo "   - Status script created: $DEPLOY_DIR/status.sh"
echo ""
echo "📝 Next Steps:"
echo "   1. Edit the .env file with your actual configuration:"
echo "      nano $DEPLOY_DIR/.env"
echo ""
echo "   2. Configure GitHub Secrets for CI/CD:"
echo "      - DOCKER_HUB_USERNAME, DOCKER_HUB_REPOSITORY, DOCKER_HUB_TOKEN"
echo "      - ECS_HOST, ECS_USERNAME, ECS_SSH_KEY, ECS_PORT"
echo ""
echo "   3. Push your code to GitHub main branch to trigger deployment"
echo ""
echo "   4. Monitor deployment with:"
echo "      cd $DEPLOY_DIR && ./status.sh"
echo ""
echo "⚠️  IMPORTANT: "
echo "   - If you added the user to docker group, you may need to log out and back in"
echo "   - Make sure to edit the .env file with your actual values"
echo "   - Ensure your database is accessible from this server"
echo ""

# Check if user needs to log out for docker group changes
if ! groups | grep -q docker; then
    echo "🔄 You may need to log out and back in for Docker group changes to take effect"
fi 