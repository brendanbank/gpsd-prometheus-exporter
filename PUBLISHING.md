# Publishing Guide

This guide explains how to publish the gpsd-prometheus-exporter Docker image to GitHub Container Registry (ghcr.io) using fine-grained personal access tokens and automated CI/CD.

## Setup Fine-Grained Personal Access Token

### 1. Create Fine-Grained Token

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. Click "Generate new token"
3. Configure the token:

**Token name**: `gpsd-exporter-publish`

**Repository access**: 
- Select "Only select repositories"
- Choose your repository

**Permissions**:
- **Repository permissions**:
  - `Contents`: Read and write
  - `Metadata`: Read-only
  - `Pull requests`: Read and write
  - `Workflows`: Read and write

**Token expiration**: Choose appropriate expiration (e.g., 90 days)

### 2. Store Token as Repository Secret

1. Go to your repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `FINE_GRAINED_TOKEN`
4. Value: Paste your fine-grained token

### 3. Enable Package Publishing

The workflow uses the built-in `GITHUB_TOKEN` for package publishing, which is automatically provided by GitHub Actions and has the necessary permissions for the repository.

## CI/CD Pipeline Features

The pipeline includes:

### 1. **Testing Job**
- Python syntax validation
- Dependency installation
- Entrypoint script testing

### 2. **Build and Push Job**
- Multi-platform Docker builds
- Automatic tagging based on:
  - Git tags (semantic versions)
  - Branch names
  - Commit SHA
- Caching for faster builds

### 3. **Security Scanning**
- Trivy vulnerability scanning
- SARIF report upload to GitHub Security tab

## Pipeline Triggers

The pipeline runs on:
- **Push to main/develop branches**: Build and push latest
- **Pull requests**: Test only (no push)
- **Git tags (v*)**: Build and push versioned releases
- **Manual trigger**: Via GitHub Actions UI

## Usage Examples

### Manual Publishing

```bash
# Login with fine-grained token
echo $FINE_GRAINED_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# Build and push
docker build -t ghcr.io/YOUR_USERNAME/gpsd-prometheus-exporter:latest .
docker push ghcr.io/YOUR_USERNAME/gpsd-prometheus-exporter:latest
```

### Automated Publishing

```bash
# Create a release
git tag v1.0.0
git push origin v1.0.0
# Pipeline automatically builds and publishes
```

### Using the Published Image

Update your `docker-compose.yml`:

```yaml
services:
  gpsd-exporter:
    image: ghcr.io/YOUR_USERNAME/gpsd-prometheus-exporter:latest
    # ... rest of configuration
```

## Security Benefits of Fine-Grained Tokens

1. **Minimal permissions**: Only access to specific repository
2. **Time-limited**: Automatic expiration
3. **Granular control**: Exact permissions needed
4. **Audit trail**: Clear logging of token usage
5. **No cross-repo access**: Cannot access other repositories

## Troubleshooting

### Token Issues
- Ensure token has correct repository permissions
- Check token expiration
- Verify token is stored as `FINE_GRAINED_TOKEN` secret
- Ensure repository has package publishing enabled

### Build Issues
- Check GitHub Actions logs for detailed error messages
- Verify Dockerfile syntax
- Ensure all dependencies are available

### Registry Issues
- Verify repository is public (or you have access)
- Check package visibility settings
- Ensure image name matches repository name

## Best Practices

1. **Use semantic versioning** for releases
2. **Test locally** before pushing
3. **Monitor security scans** in GitHub Security tab
4. **Rotate tokens** regularly
5. **Use specific tags** for production deployments
