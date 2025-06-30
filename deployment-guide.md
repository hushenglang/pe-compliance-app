# GitHub Actions CI/CD Deployment Guide

This guide explains how to set up automated CI/CD pipeline for deploying your PE Compliance App to Alibaba Cloud ECS using GitHub Actions.

## Prerequisites

1. **Alibaba Cloud Account** with:
   - Container Registry (ACR) service enabled
   - ECS instance running with Docker installed
   - Access credentials

2. **GitHub Repository** with admin access to configure secrets

3. **ECS Server Setup**:
   - Docker installed
   - SSH access configured
   - User with Docker permissions

## Step 1: Set up Docker Hub Repository

1. Go to Docker Hub (https://hub.docker.com)
2. Sign in to your Docker Hub account (or create one if needed)
3. Create a new repository named `pe-compliance-app` (or use your preferred name)
4. Set the repository visibility (public or private)
5. Note down:
   - Your Docker Hub username
   - Repository name (format: `username/pe-compliance-app`)
   - Generate an access token for secure authentication

## Step 2: Prepare ECS Server

### Install Docker (if not already installed)
```bash
# Update system
sudo yum update -y

# Install Docker
sudo yum install -y docker

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker $USER

# Install curl for health checks
sudo yum install -y curl
```

### Create deployment directory and environment file
```bash
# Create deployment directory
mkdir -p ~/deployments/pe-compliance-app
cd ~/deployments/pe-compliance-app

# Create environment file
cat > .env << EOF
# Application Configuration
APP_ENV=production
LOG_LEVEL=INFO

# OpenRouter Configuration
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Database Configuration
DATABASE_URL=mysql+pymysql://user:password@host:port/database
DB_HOST=your_db_host
DB_PORT=3306
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=your_db_name

# SFC Configuration
SFC_BASE_URL=https://www.sfc.hk
SFC_NEWS_ENDPOINT=/web/EN/regulatory-functions/news/

# Other environment variables as needed
EOF

# Secure the environment file
chmod 600 .env
```

## Step 3: Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions, and add the following secrets:

### Docker Hub Secrets
- `DOCKER_HUB_USERNAME`: Your Docker Hub username
- `DOCKER_HUB_REPOSITORY`: Your Docker Hub repository (format: `username/pe-compliance-app`)
- `DOCKER_HUB_TOKEN`: Your Docker Hub access token (recommended) or password

### ECS Server Secrets
- `ECS_HOST`: Your ECS server public IP or domain
- `ECS_USERNAME`: SSH username (e.g., `root` or `ecs-user`)
- `ECS_SSH_KEY`: Your private SSH key for accessing the ECS server
- `ECS_PORT`: SSH port (default: `22`)

### Example SSH Key Setup
```bash
# Generate SSH key pair on your local machine
ssh-keygen -t rsa -b 4096 -C "github-actions@yourdomain.com"

# Copy public key to ECS server
ssh-copy-id -i ~/.ssh/id_rsa.pub user@your-ecs-ip

# Copy private key content to GitHub secret ECS_SSH_KEY
cat ~/.ssh/id_rsa
```

## Step 4: Workflow Features

The GitHub Actions workflow includes:

### 🧪 Testing Stage
- Python 3.13 setup
- UV dependency installation
- Code linting with Ruff
- Type checking with MyPy

### 🏗️ Build and Push Stage
- Docker image building
- Tagging with timestamp and commit SHA
- Push to Alibaba Cloud Container Registry
- Security scanning with Trivy

### 🚀 Deploy Stage
- SSH connection to ECS server
- Graceful container replacement
- Health check verification
- Image cleanup (keeps last 3 versions)
- Automatic rollback on failure

### 📢 Notification Stage
- Deployment status notification
- Application URL display

## Step 5: Triggering Deployments

### Automatic Deployment
- Push to `main` branch triggers full CI/CD pipeline
- Push to `develop` branch triggers tests only
- Pull requests trigger tests only

### Manual Deployment
1. Go to GitHub → Actions
2. Select "CI/CD Pipeline" workflow
3. Click "Run workflow"
4. Choose branch and run

## Step 6: Monitoring and Troubleshooting

### Check Deployment Status
```bash
# On ECS server
cd ~/deployments/pe-compliance-app

# Check container status
docker ps --filter name=pe-compliance-app-container

# View logs
docker logs -f pe-compliance-app-container

# Check health
curl http://localhost:8000/health
```

### Common Issues and Solutions

1. **Container fails to start**
   - Check environment variables in `.env` file
   - Verify database connectivity
   - Check application logs

2. **Health check failures**
   - Ensure port 8000 is accessible
   - Verify application starts correctly
   - Check firewall settings

3. **SSH connection issues**
   - Verify SSH key format in GitHub secrets
   - Check ECS security group allows SSH (port 22)
   - Confirm SSH user has Docker permissions

4. **Docker Hub authentication failures**
   - Verify Docker Hub credentials in GitHub secrets
   - Check Docker Hub repository format (username/repository)
   - Ensure repository exists and is accessible

## Step 7: Security Best Practices

1. **Use access tokens** instead of passwords for Docker Hub authentication
2. **Limit SSH key permissions** to deployment user only
3. **Regularly rotate secrets** and update in GitHub
4. **Monitor container logs** for security issues
5. **Keep base images updated** for security patches

## Step 8: Scaling and Improvements

### Production Enhancements
- Set up load balancer for multiple ECS instances
- Implement blue-green deployment strategy
- Add automated database migrations
- Set up monitoring and alerting
- Configure log aggregation

### CI/CD Enhancements
- Add integration tests
- Implement staging environment
- Add manual approval for production deployments
- Set up Slack/email notifications
- Add performance testing

## Support

If you encounter issues:
1. Check GitHub Actions logs
2. Review ECS server logs
3. Verify all secrets are correctly configured
4. Ensure network connectivity between services

---

**Note**: Replace placeholder values with your actual configuration before deploying. 