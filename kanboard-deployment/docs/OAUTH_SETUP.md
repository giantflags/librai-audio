# Kanboard Google OAuth SSO Setup Guide

This guide provides a complete solution for setting up Google OAuth authentication on a self-hosted Kanboard instance with a public domain.

---

## Table of Contents

1. [Problem Summary](#problem-summary)
2. [Prerequisites](#prerequisites)
3. [Solution Overview](#solution-overview)
4. [Step-by-Step Implementation](#step-by-step-implementation)
5. [Troubleshooting](#troubleshooting)
6. [Security Best Practices](#security-best-practices)

---

## Problem Summary

### The Issue

When attempting to enable Google OAuth on Kanboard, you encounter:

```
Access blocked: vl-tasks-kanboard's request is invalid
Error 400: redirect_uri_mismatch
```

### Root Cause

1. **Hardcoded redirect URL**: Kanboard defaults to `http://localhost/oauth/google`
2. **Container network context**: Docker containers see `localhost`, not your public domain
3. **Google OAuth requirements**: Redirect URIs must match exactly and use public domains

### Why This Happens

- Kanboard doesn't automatically detect the public domain when running in Docker
- Without `APPLICATION_URL` set, Kanboard generates OAuth callbacks using `localhost`
- Google OAuth rejects mismatched redirect URIs for security reasons

---

## Prerequisites

- ✅ Docker and Docker Compose installed
- ✅ Domain name configured (e.g., `tasks.verslib.re`)
- ✅ DNS A record pointing to your VM's public IP
- ✅ Port 80 (and optionally 443 for HTTPS) accessible
- ✅ Google Cloud Console account

---

## Solution Overview

### Option 1: Quick Fix (HTTP Only) ⚡

**Best for**: Quick testing, internal networks, development

1. Set `APPLICATION_URL` in Kanboard's `config.php`
2. Configure Google OAuth with public domain redirect URI
3. Deploy with Docker Compose

**Pros**: Simple, fast setup
**Cons**: No encryption (not recommended for production)

### Option 2: Production Setup (HTTPS) 🔒

**Best for**: Production deployments, public access

1. All steps from Option 1
2. Add SSL certificate (Let's Encrypt)
3. Configure Nginx reverse proxy with HTTPS
4. Enable security headers and HSTS

**Pros**: Secure, production-ready
**Cons**: Requires additional SSL setup

---

## Step-by-Step Implementation

### Phase 1: Google OAuth Application Setup

1. **Go to Google Cloud Console**
   - Navigate to: https://console.cloud.google.com/

2. **Create a New Project (or use existing)**
   - Click "Select a project" → "New Project"
   - Name: `vl-tasks-kanboard` (or your preferred name)
   - Click "Create"

3. **Enable Google+ API**
   - Go to "APIs & Services" → "Library"
   - Search for "Google+ API"
   - Click "Enable"

4. **Configure OAuth Consent Screen**
   - Go to "APIs & Services" → "OAuth consent screen"
   - Choose "External" (for public access) or "Internal" (G Suite only)
   - Fill in required fields:
     - App name: `Kanboard - Vers Libre Tasks`
     - User support email: Your email
     - Developer contact email: Your email
   - Click "Save and Continue"
   - Scopes: Leave default (email, profile, openid)
   - Test users: Add your email for testing
   - Click "Save and Continue"

5. **Create OAuth Client ID**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth 2.0 Client ID"
   - Application type: **Web application**
   - Name: `Kanboard Web Client`

   **Authorized redirect URIs** (add both):
   ```
   http://tasks.verslib.re/oauth/google/callback
   ```

   If using HTTPS (recommended):
   ```
   https://tasks.verslib.re/oauth/google/callback
   ```

6. **Save Credentials**
   - Copy the **Client ID** (ends with `.apps.googleusercontent.com`)
   - Copy the **Client Secret**
   - ⚠️ Store these securely - you'll need them for Kanboard configuration

---

### Phase 2: Kanboard Configuration

#### Step 1: Update `config.php`

Edit `/home/user/librai-audio/kanboard/config.php`:

```php
<?php

// ============================================================
// CRITICAL: Set your public domain
// ============================================================
defined('APPLICATION_URL') or define('APPLICATION_URL', 'http://tasks.verslib.re');

// If using HTTPS (recommended):
// defined('APPLICATION_URL') or define('APPLICATION_URL', 'https://tasks.verslib.re');

// ============================================================
// Google OAuth Settings
// ============================================================
defined('GOOGLE_AUTH') or define('GOOGLE_AUTH', true);
defined('GOOGLE_CLIENT_ID') or define('GOOGLE_CLIENT_ID', 'YOUR_CLIENT_ID.apps.googleusercontent.com');
defined('GOOGLE_CLIENT_SECRET') or define('GOOGLE_CLIENT_SECRET', 'YOUR_CLIENT_SECRET');

// ============================================================
// Reverse Proxy Settings
// ============================================================
defined('REVERSE_PROXY_TRUST_HEADER') or define('REVERSE_PROXY_TRUST_HEADER', true);
```

**Replace**:
- `YOUR_CLIENT_ID` → Your actual Google Client ID
- `YOUR_CLIENT_SECRET` → Your actual Google Client Secret

#### Step 2: Deploy with Docker Compose

```bash
cd /home/user/librai-audio/kanboard

# Start Kanboard
docker-compose up -d

# Verify container is running
docker ps | grep kanboard

# Check logs
docker logs kanboard
```

#### Step 3: Test OAuth Redirect

```bash
# Test that OAuth endpoint is accessible
curl -I http://tasks.verslib.re/oauth/google

# You should see a 302 redirect with the correct domain
# Location should show: https://accounts.google.com/o/oauth2/...
```

---

### Phase 3: Nginx Reverse Proxy (Optional but Recommended)

If you already have Nginx on your VM (not in Docker), use this configuration:

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/kanboard
```

Paste the contents from `nginx.conf` (provided in this directory), then:

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/kanboard /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

**Key Nginx headers for OAuth**:
```nginx
proxy_set_header Host $host;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
```

---

### Phase 4: SSL/HTTPS Setup (Production)

#### Option A: Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt update
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d tasks.verslib.re

# Certbot will automatically configure Nginx for HTTPS
```

#### Option B: Manual Certificate

1. Place your SSL certificate files:
   - `/etc/nginx/ssl/tasks.verslib.re.crt`
   - `/etc/nginx/ssl/tasks.verslib.re.key`

2. Uncomment the HTTPS server block in `nginx.conf`

3. Update `config.php`:
   ```php
   defined('APPLICATION_URL') or define('APPLICATION_URL', 'https://tasks.verslib.re');
   ```

4. Update Google OAuth redirect URI to use `https://`

---

### Phase 5: First Login & User Management

1. **Access Kanboard**
   - Navigate to: `http://tasks.verslib.re` (or `https://`)

2. **Initial Admin Login**
   - Username: `admin`
   - Password: `admin`
   - ⚠️ **IMPORTANT**: Change this immediately!

3. **Create Your User Account via OAuth**
   - Click "Login with Google"
   - Authorize the application
   - You'll be redirected back with a new account

4. **Grant Admin Access to Your OAuth Account**
   - Log out from OAuth account
   - Log in as `admin` / `admin`
   - Go to "Users" → Find your OAuth account
   - Change role to "Administrator"
   - Log out and log back in with Google

5. **Disable Default Admin (Optional)**
   - Settings → Users → Disable `admin` account
   - Or delete after confirming OAuth admin access works

---

## Troubleshooting

### Error: `redirect_uri_mismatch`

**Cause**: Google OAuth redirect URI doesn't match Kanboard's configured URI

**Solutions**:
1. Verify `APPLICATION_URL` in `config.php` matches your domain exactly
2. Check Google Cloud Console → Credentials → Authorized redirect URIs
3. Ensure protocol matches (http vs https)
4. Restart Docker container after config changes:
   ```bash
   docker restart kanboard
   ```

### Error: `Access blocked: request is invalid`

**Causes**:
- OAuth consent screen not configured
- App not published (stuck in "Testing" mode)
- User email not added to test users

**Solutions**:
1. Complete OAuth consent screen configuration
2. Add your email to "Test users"
3. Publish the app (if ready for public access)

### OAuth Button Doesn't Appear

**Check**:
1. `GOOGLE_AUTH` is set to `true` in `config.php`
2. `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are correct
3. Restart Docker container:
   ```bash
   docker restart kanboard
   ```

4. Check container logs:
   ```bash
   docker logs kanboard | grep -i oauth
   ```

### Container Not Accessible from Public Domain

**Causes**:
- DNS not propagated
- Firewall blocking port 80/443
- Nginx not forwarding requests

**Diagnostic**:
```bash
# Test DNS resolution
nslookup tasks.verslib.re

# Check if port is open
sudo netstat -tulpn | grep :80

# Test local access
curl http://localhost:8080

# Test public access
curl http://tasks.verslib.re
```

### Application URL Still Shows `localhost`

**Causes**:
- Config file not mounted correctly in Docker
- Config changes not applied

**Solutions**:
1. Verify volume mount in `docker-compose.yml`:
   ```yaml
   volumes:
     - ./config.php:/var/www/app/config.php:ro
   ```

2. Check file permissions:
   ```bash
   ls -l kanboard/config.php
   # Should be readable by Docker user
   ```

3. Restart container:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

4. Verify config is loaded:
   ```bash
   docker exec kanboard cat /var/www/app/config.php | grep APPLICATION_URL
   ```

---

## Security Best Practices

### 🔒 HTTPS/SSL

- **Always use HTTPS in production**
- Use Let's Encrypt for free SSL certificates
- Enable HSTS header to force HTTPS:
  ```php
  defined('ENABLE_HSTS') or define('ENABLE_HSTS', true);
  ```

### 🔑 Secrets Management

- Never commit `config.php` with real credentials to git
- Use environment variables for sensitive data:
  ```yaml
  environment:
    - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
    - GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
  ```
- Store secrets in `.env` file (add to `.gitignore`)

### 🚪 Access Control

1. **Disable password login** (force OAuth only):
   ```php
   defined('DISABLE_LOGIN_FORM') or define('DISABLE_LOGIN_FORM', true);
   ```

2. **Restrict OAuth domain** (G Suite/Workspace only):
   - Google Cloud Console → OAuth consent screen
   - Set "Internal" instead of "External"
   - Only users in your organization can authenticate

3. **Enable 2FA** on Google accounts for additional security

### 🛡️ Nginx Security Headers

```nginx
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
```

### 🔄 Regular Updates

```bash
# Update Kanboard image
docker pull kanboard/kanboard:latest
docker-compose up -d

# Backup before updates
docker exec kanboard tar -czf /backup/kanboard-$(date +%F).tar.gz /var/www/app/data
```

---

## Verification Checklist

After completing setup, verify:

- [ ] Docker container is running: `docker ps | grep kanboard`
- [ ] Application accessible via public domain: `http://tasks.verslib.re`
- [ ] OAuth button appears on login page
- [ ] Clicking "Login with Google" redirects to Google
- [ ] After authorization, redirected back to Kanboard
- [ ] New user account created with Google email
- [ ] No `redirect_uri_mismatch` errors
- [ ] HTTPS working (if configured)
- [ ] SSL certificate valid (if using HTTPS)
- [ ] Nginx headers correctly forwarded

---

## Quick Reference

### Important Files

| File | Location | Purpose |
|------|----------|---------|
| `config.php` | `/var/www/app/config.php` | Main Kanboard configuration |
| `docker-compose.yml` | `/home/user/librai-audio/kanboard/` | Docker orchestration |
| `nginx.conf` | `/etc/nginx/sites-available/kanboard` | Reverse proxy config |

### Docker Commands

```bash
# Start Kanboard
docker-compose up -d

# Stop Kanboard
docker-compose down

# Restart Kanboard
docker restart kanboard

# View logs
docker logs -f kanboard

# Access container shell
docker exec -it kanboard /bin/bash

# Backup data
docker exec kanboard tar -czf /backup/kanboard.tar.gz /var/www/app/data
```

### Nginx Commands

```bash
# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx

# Restart Nginx
sudo systemctl restart nginx

# View logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Testing OAuth Flow

```bash
# Check OAuth endpoint
curl -I http://tasks.verslib.re/oauth/google

# Expected response:
# HTTP/1.1 302 Found
# Location: https://accounts.google.com/o/oauth2/auth?...

# Verify redirect_uri parameter in Location header contains your domain
```

---

## Additional Resources

- [Kanboard Documentation](https://docs.kanboard.org/)
- [Google OAuth 2.0 Setup](https://developers.google.com/identity/protocols/oauth2)
- [Let's Encrypt Certbot](https://certbot.eff.org/)
- [Nginx Reverse Proxy Guide](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/)

---

## Support

If you encounter issues not covered in this guide:

1. Check Kanboard logs: `docker logs kanboard`
2. Check Nginx logs: `sudo tail -f /var/log/nginx/error.log`
3. Verify DNS: `nslookup tasks.verslib.re`
4. Test local access: `curl http://localhost:8080`
5. Review Google Cloud Console audit logs

---

**Last Updated**: 2025-11-08
**Kanboard Version**: Latest (Docker)
**Tested On**: Ubuntu 20.04/22.04 LTS
