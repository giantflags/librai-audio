# Kanboard Deployment with Google OAuth SSO

> Production-ready Kanboard deployment with Google OAuth authentication for self-hosted environments (Google Cloud VM, AWS EC2, etc.)

[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com/)
[![Kanboard](https://img.shields.io/badge/Kanboard-Latest-green)](https://kanboard.org/)
[![OAuth](https://img.shields.io/badge/OAuth-Google-red)](https://console.cloud.google.com/)

---

## 🚀 Quick Start (5 Minutes)

```bash
# 1. Clone this repository
git clone <your-repo-url>
cd kanboard-deployment

# 2. Configure environment
cp .env.example .env
nano .env  # Edit with your domain and OAuth credentials

# 3. Configure Kanboard
cp config.php.template config.php
nano config.php  # Edit with your domain and OAuth credentials

# 4. Deploy
docker-compose up -d

# 5. Access Kanboard
# Open: http://your-domain (or http://localhost:8080 for local testing)
# Default login: admin / admin (change immediately!)
```

---

## 📋 Table of Contents

- [Overview](#overview)
- [Problem Solved](#problem-solved)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Google OAuth Setup](#google-oauth-setup)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)
- [Security Best Practices](#security-best-practices)

---

## 🎯 Overview

This repository provides a complete, production-ready deployment configuration for [Kanboard](https://kanboard.org/) with:

✅ **Google OAuth SSO** - Single Sign-On with Google Workspace or Gmail
✅ **Docker Deployment** - Containerized, easy to deploy and update
✅ **Nginx Reverse Proxy** - Production-ready web server configuration
✅ **SSL/HTTPS Support** - Ready for Let's Encrypt certificates
✅ **Security Hardened** - Following best practices
✅ **Well Documented** - Clear setup instructions and troubleshooting

---

## 🔧 Problem Solved

### The OAuth Redirect Issue

When deploying Kanboard with Google OAuth, you typically encounter:

```
Access blocked: request is invalid
Error 400: redirect_uri_mismatch
```

**Root Cause:** Kanboard defaults to using `http://localhost` for OAuth callbacks, which Google rejects.

**Our Solution:** Properly configure `APPLICATION_URL` in `config.php` to use your public domain, ensuring OAuth redirects work correctly.

---

## ✅ Prerequisites

Before starting, ensure you have:

- [ ] **Server/VM** (Google Cloud, AWS, DigitalOcean, etc.)
- [ ] **Docker & Docker Compose** installed
- [ ] **Domain name** configured (e.g., `tasks.yourcompany.com`)
- [ ] **DNS A record** pointing to your server's IP
- [ ] **Port 80** (and optionally 443) accessible
- [ ] **Google Cloud Console** account

### Installing Prerequisites

<details>
<summary>Click to expand: Install Docker on Ubuntu/Debian</summary>

```bash
# Update package index
sudo apt update

# Install dependencies
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Verify installation
docker --version
docker compose version

# Add your user to docker group (optional)
sudo usermod -aG docker $USER
# Log out and back in for this to take effect
```

</details>

---

## 📦 Installation

### Step 1: Clone Repository

```bash
# Clone this repository
git clone https://github.com/your-org/kanboard-deployment.git
cd kanboard-deployment
```

### Step 2: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

**Required settings in `.env`:**

```bash
# Your public domain (CRITICAL!)
APPLICATION_URL=http://tasks.yourcompany.com

# Google OAuth credentials (from Google Cloud Console)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
```

### Step 3: Configure Kanboard

```bash
# Copy configuration template
cp config.php.template config.php

# Edit configuration
nano config.php
```

**Update these values in `config.php`:**

```php
defined('APPLICATION_URL') or define('APPLICATION_URL', 'http://tasks.yourcompany.com');
defined('GOOGLE_CLIENT_ID') or define('GOOGLE_CLIENT_ID', 'your-client-id.apps.googleusercontent.com');
defined('GOOGLE_CLIENT_SECRET') or define('GOOGLE_CLIENT_SECRET', 'your-client-secret');
```

---

## 🔐 Google OAuth Setup

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Name it: `kanboard-oauth` (or your preference)

### Step 2: Enable Google+ API

1. Navigate to **APIs & Services** → **Library**
2. Search for **"Google+ API"**
3. Click **Enable**

### Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Select user type:
   - **Internal** (for Google Workspace - only your organization)
   - **External** (for public Gmail accounts)
3. Fill in required fields:
   - **App name:** `Kanboard`
   - **User support email:** Your email
   - **Developer contact:** Your email
4. Click **Save and Continue**
5. Scopes: Leave default (email, profile, openid)
6. Add **Test users** (your email) if using External
7. Click **Save and Continue**

### Step 4: Create OAuth Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth 2.0 Client ID**
3. Application type: **Web application**
4. Name: `Kanboard Web Client`

5. **Authorized redirect URIs** - Add this URL:
   ```
   http://tasks.yourcompany.com/oauth/google/callback
   ```

   > ⚠️ **Important:** Replace `tasks.yourcompany.com` with your actual domain!

   If using HTTPS (recommended):
   ```
   https://tasks.yourcompany.com/oauth/google/callback
   ```

6. Click **Create**
7. **Copy the Client ID and Client Secret** - you'll need these for configuration

---

## ⚙️ Configuration

### Configuration Files Overview

| File | Purpose | Commit to Git? |
|------|---------|----------------|
| `.env.example` | Template for environment variables | ✅ Yes |
| `.env` | Your actual configuration with secrets | ❌ **Never** |
| `config.php.template` | Template for Kanboard config | ✅ Yes |
| `config.php` | Your actual Kanboard config with secrets | ❌ **Never** |
| `docker-compose.yml` | Docker orchestration | ✅ Yes |
| `nginx.conf` | Reverse proxy configuration | ✅ Yes |

### Key Settings Explained

#### APPLICATION_URL (CRITICAL)

This is **THE most important setting** for fixing OAuth redirect issues.

```php
defined('APPLICATION_URL') or define('APPLICATION_URL', 'http://your-domain.com');
```

- Must match your public domain exactly
- Include protocol (`http://` or `https://`)
- No trailing slash
- Examples:
  - `http://tasks.verslib.re` ✅
  - `https://kanboard.company.com` ✅
  - `http://localhost` ❌ (doesn't work for OAuth)
  - `http://your-domain.com/` ❌ (trailing slash)

#### Database Configuration

**Option 1: SQLite (Default - Recommended for small teams)**

No configuration needed! Data stored in `/var/www/app/data/db.sqlite`

**Option 2: MySQL/PostgreSQL (For larger deployments)**

Uncomment database section in `docker-compose.yml` and configure in `config.php`

---

## 🚀 Deployment

### Deploy with Docker Compose

```bash
# Start Kanboard
docker-compose up -d

# Verify it's running
docker ps | grep kanboard

# Check logs
docker logs -f kanboard

# Wait for startup (usually 5-10 seconds)
```

### Access Kanboard

**Local access:**
```
http://localhost:8080
```

**Public access:**
```
http://your-domain.com
```

### First Login

**Default credentials:**
- Username: `admin`
- Password: `admin`

⚠️ **IMPORTANT:** Change these immediately after first login!

### Test OAuth

1. Go to your Kanboard URL
2. Click **"Login with Google"**
3. Authorize the application
4. You should be redirected back with a new account created

### Grant Admin Access to OAuth Account

1. Log out from OAuth account
2. Log in as `admin` / `admin`
3. Go to **Settings** → **Users**
4. Find your OAuth account
5. Change role to **Administrator**
6. Log out and log back in with Google
7. Now you can disable the default `admin` account

---

## 🔍 Troubleshooting

### Error: `redirect_uri_mismatch`

**Symptom:** Google shows "Error 400: redirect_uri_mismatch"

**Causes & Solutions:**

1. **APPLICATION_URL mismatch**
   ```bash
   # Verify config
   docker exec kanboard cat /var/www/app/config.php | grep APPLICATION_URL

   # Should show your domain, not localhost
   ```

2. **Google OAuth redirect URI doesn't match**
   - Google Console: `http://tasks.yourcompany.com/oauth/google/callback`
   - Must match `APPLICATION_URL` exactly (http vs https)

3. **Container needs restart after config change**
   ```bash
   docker restart kanboard
   ```

### Error: Container Won't Start

```bash
# Check logs
docker logs kanboard

# Common issues:
# - config.php has syntax errors
# - config.php doesn't exist
# - Port 8080 already in use
```

**Solution:**
```bash
# Validate PHP syntax
php -l config.php

# Check if port is in use
sudo lsof -i :8080

# Check volume mounts
docker inspect kanboard | grep Mounts -A 20
```

### OAuth Button Doesn't Appear

**Checklist:**
- [ ] `GOOGLE_AUTH` set to `true` in config.php
- [ ] `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are correct
- [ ] Container restarted after config changes
- [ ] Check logs: `docker logs kanboard | grep -i oauth`

### Can't Access from Public Domain

```bash
# Test DNS resolution
nslookup your-domain.com

# Test local access
curl http://localhost:8080

# Check firewall
sudo ufw status
sudo iptables -L -n

# Test from external location
curl http://your-domain.com
```

### Config File Gets Overwritten

If Kanboard overwrites `config.php`, ensure it's properly mounted:

```yaml
# In docker-compose.yml
volumes:
  - ./config.php:/var/www/app/config.php:ro  # :ro = read-only
```

---

## 🔧 Maintenance

### Backup

```bash
# Backup data (SQLite database, uploads, etc.)
docker run --rm --volumes-from kanboard \
  -v $(pwd):/backup \
  alpine tar -czf /backup/kanboard-backup-$(date +%F).tar.gz \
  /var/www/app/data

# Backup configuration
cp config.php config-backup-$(date +%F).php
cp .env .env-backup-$(date +%F)
```

### Restore

```bash
# Restore data
docker run --rm --volumes-from kanboard \
  -v $(pwd):/backup \
  alpine tar -xzf /backup/kanboard-backup-YYYY-MM-DD.tar.gz -C /

# Restart container
docker restart kanboard
```

### Update Kanboard

```bash
# Pull latest image
docker-compose pull

# Recreate container with new image
docker-compose up -d

# Verify update
docker logs kanboard
```

### View Logs

```bash
# Follow logs in real-time
docker-compose logs -f kanboard

# View last 100 lines
docker logs --tail 100 kanboard

# Search logs
docker logs kanboard 2>&1 | grep -i error
```

### Useful Commands

```bash
# Access container shell
docker exec -it kanboard /bin/bash

# View config
docker exec kanboard cat /var/www/app/config.php

# Restart Kanboard
docker-compose restart kanboard

# Stop Kanboard
docker-compose down

# Start Kanboard
docker-compose up -d

# Remove all data (⚠️ DESTRUCTIVE!)
docker-compose down -v
```

---

## 🔒 Security Best Practices

### 1. Use HTTPS in Production

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d tasks.yourcompany.com

# Update config.php
APPLICATION_URL = 'https://tasks.yourcompany.com'
```

### 2. Restrict OAuth Domain (Google Workspace Only)

In Google Console → OAuth consent screen:
- Set **Internal** instead of **External**
- Only users in your organization can authenticate

### 3. Disable Password Login (After OAuth Works!)

```php
// In config.php
defined('DISABLE_LOGIN_FORM') or define('DISABLE_LOGIN_FORM', true);
```

### 4. Enable Security Headers

```php
// In config.php
defined('FORCE_HTTPS') or define('FORCE_HTTPS', true);
defined('ENABLE_HSTS') or define('ENABLE_HSTS', true);
```

### 5. Regular Updates

```bash
# Update Docker images weekly
docker-compose pull && docker-compose up -d
```

### 6. Secrets Management

- ✅ Use `.gitignore` to prevent committing secrets
- ✅ Use environment variables for sensitive data
- ✅ Rotate OAuth credentials periodically
- ❌ Never commit `.env` or `config.php` to git

### 7. Firewall Configuration

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

---

## 📚 Additional Documentation

- [Google OAuth Setup Guide](docs/GOOGLE_OAUTH_SETUP.md)
- [Nginx Configuration Guide](docs/NGINX_SETUP.md)
- [SSL/HTTPS Setup](docs/SSL_SETUP.md)
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
- [FAQ](docs/FAQ.md)

---

## 🆘 Support

### Official Documentation

- [Kanboard Documentation](https://docs.kanboard.org/)
- [Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)
- [Docker Compose](https://docs.docker.com/compose/)

### Community

- [Kanboard Forum](https://kanboard.discourse.group/)
- [GitHub Issues](https://github.com/kanboard/kanboard/issues)

### This Repository

If you encounter issues specific to this deployment configuration:

1. Check [Troubleshooting](#troubleshooting) section
2. Review logs: `docker logs kanboard`
3. Open an issue in this repository

---

## 📝 License

This deployment configuration is provided as-is for public use.

Kanboard itself is licensed under the MIT License - see [Kanboard License](https://github.com/kanboard/kanboard/blob/master/LICENSE).

---

## 🙏 Acknowledgments

- [Kanboard](https://kanboard.org/) - The excellent project management tool
- [Docker](https://www.docker.com/) - Container platform
- [Google Cloud](https://cloud.google.com/) - OAuth provider

---

## 📊 Quick Reference

### File Structure

```
kanboard-deployment/
├── .gitignore              # Security: ignore secrets
├── README.md               # This file
├── .env.example            # Template for environment variables
├── config.php.template     # Template for Kanboard config
├── docker-compose.yml      # Docker orchestration
├── nginx.conf              # Nginx reverse proxy config
├── docs/                   # Additional documentation
│   ├── GOOGLE_OAUTH_SETUP.md
│   ├── NGINX_SETUP.md
│   ├── SSL_SETUP.md
│   ├── TROUBLESHOOTING.md
│   └── FAQ.md
└── scripts/                # Helper scripts
    └── deploy.sh           # Automated deployment script
```

### Essential Commands Cheat Sheet

```bash
# Deploy
docker-compose up -d

# Stop
docker-compose down

# Restart
docker-compose restart

# Logs
docker-compose logs -f kanboard

# Update
docker-compose pull && docker-compose up -d

# Backup
docker run --rm --volumes-from kanboard -v $(pwd):/backup \
  alpine tar -czf /backup/kanboard-backup.tar.gz /var/www/app/data

# Shell access
docker exec -it kanboard /bin/bash
```

### OAuth Redirect URI Format

```
{APPLICATION_URL}/oauth/google/callback

Examples:
- http://tasks.verslib.re/oauth/google/callback
- https://kanboard.company.com/oauth/google/callback
```

---

**Happy Project Managing! 🎉**
