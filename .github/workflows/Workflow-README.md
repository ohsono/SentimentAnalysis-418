# GitHub Actions Docker Build Workflow Documentation

This document provides comprehensive instructions for using the Multi-Service Docker Build and Push workflow for the Sentiment Analysis project.

## Overview

The workflow automatically builds and pushes Docker images for multiple microservices to DockerHub under the `ohsonoresearch` organization. It supports both individual service builds and batch builds for all services.

## Services & Dockerfiles

The workflow manages the following services:

| Service | Dockerfile | Docker Image |
|---------|------------|--------------|
| Dashboard | `Dockerfile.dashboard` | `ohsonoresearch/dashboard-service` |
| Gateway API | `Dockerfile.gateway-api` | `ohsonoresearch/gateway-api` |
| Model Service | `Dockerfile.model-service` | `ohsonoresearch/model-service` |
| Model Service DistillBERT | `Dockerfile.model-service-distillbert` | `ohsonoresearch/model-service-distillbert` |
| Worker | `Dockerfile.worker` | `ohsonoresearch/worker-scraper-service` |

## Workflow Triggers

### Automatic Triggers
- **Push to branches**: `main`, `develop`, `test`
- **Git tags**: Any tag starting with `v` (e.g., `v1.0.0`, `v2.1.3`)
- **Pull requests**: To `main` branch (builds but doesn't push)

### Manual Trigger
- **Workflow Dispatch**: Manual execution via GitHub Actions UI or API

## Setup Requirements

### 1. GitHub Secrets Configuration

Add these secrets to your GitHub repository settings (Settings → Secrets → Actions):

```
DOCKERHUB_USERNAME=your_dockerhub_username
DOCKERHUB_TOKEN=your_dockerhub_access_token
```

**How to create DockerHub Access Token:**
1. Go to [DockerHub](https://hub.docker.com/)
2. Account Settings → Security
3. Create new access token with read/write permissions
4. Copy the token (you won't see it again)

### 2. Repository Structure

Ensure your repository has the following structure:
```
project-root/
├── .github/
│   └── workflows/
│       └── docker-build.yml
├── Dockerfile.dashboard
├── Dockerfile.gateway-api
├── Dockerfile.model-service
├── Dockerfile.model-service-distillbert
├── Dockerfile.worker
└── [other project files]
```

## Usage Instructions

### Production Deployment

#### Build All Services
```bash
# Trigger automatic build for all services
git push origin main
```

#### Build Specific Service via Manual Dispatch
1. Go to GitHub → Actions tab
2. Select "Multi-Service Docker Build and Push"
3. Click "Run workflow"
4. Select options:
   - **Branch**: Choose target branch
   - **Service**: Select specific service or "all"
   - **Tag**: Custom tag (optional, defaults to "latest")
   - **Local test**: Keep as "false" for production

#### Build with Git Tags (Versioned Release)
```bash
# Create and push a version tag
git tag v1.2.0
git push origin v1.2.0

# This creates images with multiple tags:
# - ohsonoresearch/[service]:1.2.0
# - ohsonoresearch/[service]:1.2
# - ohsonoresearch/[service]:1
# - ohsonoresearch/[service]:latest
```

### Local Testing

#### Method 1: Direct Docker Build (Recommended)
```bash
# Test individual services
docker build -f Dockerfile.dashboard -t ohsonoresearch/dashboard:test .
docker build -f Dockerfile.gateway-api -t ohsonoresearch/gateway-api:test .
docker build -f Dockerfile.model-service -t ohsonoresearch/model-service:test .
docker build -f Dockerfile.model-service-distillbert -t ohsonoresearch/model-service-distillbert:test .
docker build -f Dockerfile.worker -t ohsonoresearch/worker:test .

# Test running a service
docker run --rm -p 8080:8080 ohsonoresearch/dashboard:test
```

#### Method 2: Using Act (GitHub Actions Local Runner)

**Prerequisites:**
```bash
# Install act
brew install act  # macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash  # Linux

# Create secrets file
cat > .secrets << EOF
DOCKERHUB_USERNAME=your_username
DOCKERHUB_TOKEN=your_token
EOF
```

**Test specific service:**
```bash
act workflow_dispatch \
  --secret-file .secrets \
  -P ubuntu-latest=catthehacker/ubuntu:act-latest \
  --input service=dashboard \
  --input local_test=true
```

**Test all services:**
```bash
act workflow_dispatch \
  --secret-file .secrets \
  -P ubuntu-latest=catthehacker/ubuntu:act-latest \
  --input service=all \
  --input local_test=true
```

## Workflow Features

### Multi-Platform Support
- **Production**: Builds for `linux/amd64` and `linux/arm64`
- **Local Testing**: Builds only for `linux/amd64` for faster execution

### Smart Caching
- GitHub Actions cache for faster subsequent builds
- Separate cache scope for each service
- Cache reused across workflow runs

### Security Scanning
- Automatic vulnerability scanning with Trivy
- Results uploaded to GitHub Security tab
- Runs only for production builds (not PRs or local tests)

### Build Attestation
- Generates cryptographic attestation for supply chain security
- Automatically pushed to registry for production builds

## Workflow Outputs

### Docker Images
Images are tagged with multiple formats:

**Branch builds:**
- `ohsonoresearch/[service]:[branch-name]`
- `ohsonoresearch/[service]:sha-[git-sha]`

**Tag builds (semantic versioning):**
- `ohsonoresearch/[service]:[full-version]` (e.g., `1.2.3`)
- `ohsonoresearch/[service]:[major.minor]` (e.g., `1.2`)
- `ohsonoresearch/[service]:[major]` (e.g., `1`)

**Main branch:**
- `ohsonoresearch/[service]:latest`

### Build Summary
The workflow provides a summary table showing the status of each service build in the GitHub Actions interface.

## Troubleshooting

### Common Issues

#### "Dockerfile not found"
**Problem**: Build fails because Dockerfile doesn't exist
**Solution**: 
1. Check filename matches exactly: `Dockerfile.dashboard`, `Dockerfile.gateway-api`, etc.
2. Ensure Dockerfiles are in the repository root
3. Check the workflow logs for listed available Dockerfiles

#### "Username and password required"
**Problem**: DockerHub login fails
**Solution**:
1. Verify GitHub secrets are set correctly
2. Regenerate DockerHub access token
3. Ensure token has read/write permissions

#### "Invalid tag format"
**Problem**: Docker tag contains invalid characters
**Solution**: Ensure branch names and tags follow Docker naming conventions (lowercase, alphanumeric, hyphens, underscores only)

#### Act fails with "Unable to locate executable file: docker"
**Problem**: Local testing with `act` can't find Docker
**Solution**:
1. Use the direct Docker build method instead
2. Try using `catthehacker/ubuntu:act-latest-docker` image
3. Ensure Docker daemon is running locally

### Debug Commands

```bash
# Check Docker build locally
docker build -f Dockerfile.dashboard -t test-image .

# Verify DockerHub access
docker login docker.io
docker push ohsonoresearch/test-image:latest

# Check workflow syntax
act --list

# Dry run workflow
act workflow_dispatch --dry-run --input service=dashboard
```

## Advanced Configuration

### Custom Registry
To use a different registry, modify the workflow environment variables:
```yaml
env:
  REGISTRY: your-registry.com
  IMAGE_ORG: your-organization
```

### Additional Platforms
To build for more platforms, modify the workflow:
```yaml
platforms: linux/amd64,linux/arm64,linux/arm/v7
```

### Custom Build Context
If your Dockerfiles require different build contexts:
```yaml
context: ./service-directory
file: ./service-directory/Dockerfile
```

## Security Best Practices

1. **Never commit DockerHub credentials** to the repository
2. **Use access tokens** instead of passwords
3. **Regularly rotate tokens** (recommended: every 90 days)
4. **Review vulnerability scan results** in GitHub Security tab
5. **Use specific image tags** in production, avoid `:latest`
6. **Enable Docker Content Trust** for production deployments

## Monitoring & Maintenance

### Regular Tasks
- [ ] Review build logs for warnings
- [ ] Check vulnerability scan results
- [ ] Update base images in Dockerfiles
- [ ] Rotate DockerHub access tokens
- [ ] Clean up old Docker images from registry

### Performance Optimization
- Use `.dockerignore` files to exclude unnecessary files
- Multi-stage builds to reduce image size
- Leverage build cache effectively
- Consider using BuildKit for advanced features

## Support

For issues with this workflow:
1. Check the troubleshooting section above
2. Review GitHub Actions logs for detailed error messages
3. Test Docker builds locally first
4. Check DockerHub for image availability and tags

For questions about the project architecture or Docker configurations, consult the main project documentation.