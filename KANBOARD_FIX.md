# Quick Fix for Kanboard Google OAuth Redirect Issue

## The Problem
You're getting: `Error 400: redirect_uri_mismatch` because Kanboard is using `http://localhost/oauth/google` instead of your public domain `http://tasks.verslib.re/oauth/google`.

## The Solution (5 minutes)

### Step 1: Edit Kanboard Configuration

SSH into your Google Cloud VM and run:

```bash
# Find your Kanboard container ID
docker ps | grep kanboard

# Access the container
docker exec -it kanboard /bin/bash

# Inside the container, edit config.php
nano /var/www/app/config.php
```

### Step 2: Add This to config.php

Add these lines at the top of the file (after `<?php`):

```php
<?php

// Fix OAuth redirect URL
defined('APPLICATION_URL') or define('APPLICATION_URL', 'http://tasks.verslib.re');

// Enable Google OAuth
defined('GOOGLE_AUTH') or define('GOOGLE_AUTH', true);
defined('GOOGLE_CLIENT_ID') or define('GOOGLE_CLIENT_ID', 'YOUR_ACTUAL_CLIENT_ID.apps.googleusercontent.com');
defined('GOOGLE_CLIENT_SECRET') or define('GOOGLE_CLIENT_SECRET', 'YOUR_ACTUAL_CLIENT_SECRET');

// Trust reverse proxy headers
defined('REVERSE_PROXY_TRUST_HEADER') or define('REVERSE_PROXY_TRUST_HEADER', true);
```

**Replace:**
- `YOUR_ACTUAL_CLIENT_ID` with your Google Client ID
- `YOUR_ACTUAL_CLIENT_SECRET` with your Google Client Secret

Save and exit (Ctrl+O, Enter, Ctrl+X in nano)

```bash
# Exit the container
exit
```

### Step 3: Restart Kanboard

```bash
docker restart kanboard
```

### Step 4: Update Google OAuth Settings

1. Go to: https://console.cloud.google.com/apis/credentials
2. Click on your OAuth 2.0 Client ID
3. Under "Authorized redirect URIs", add:
   ```
   http://tasks.verslib.re/oauth/google/callback
   ```
4. Click "Save"

### Step 5: Test

1. Go to: http://tasks.verslib.re/login
2. Click "Login with Google"
3. You should now be redirected correctly ✅

---

## Verification

Test the OAuth endpoint returns the correct redirect:

```bash
curl -I http://tasks.verslib.re/oauth/google
```

You should see a redirect to `accounts.google.com` with `redirect_uri=http://tasks.verslib.re/oauth/google/callback`

---

## If You're Using Nginx

If you have Nginx reverse proxy on the VM, ensure these headers are set:

```bash
sudo nano /etc/nginx/sites-available/kanboard
```

Add these in the `location /` block:

```nginx
location / {
    proxy_pass http://localhost:8080;

    # These headers are CRITICAL for OAuth
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Then reload:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## Troubleshooting

### Still seeing `redirect_uri_mismatch`?

1. **Check config was applied:**
   ```bash
   docker exec kanboard cat /var/www/app/config.php | grep APPLICATION_URL
   ```
   Should show: `define('APPLICATION_URL', 'http://tasks.verslib.re');`

2. **Restart container again:**
   ```bash
   docker restart kanboard
   sleep 3
   docker logs kanboard | tail -20
   ```

3. **Verify Google OAuth redirect URI exactly matches:**
   - Google Console: `http://tasks.verslib.re/oauth/google/callback`
   - Must be exact match (http vs https, trailing slash, etc.)

### Config file gets reset?

If the container overwrites config.php on restart, you need to mount it as a volume:

```bash
# Copy config out of container
docker cp kanboard:/var/www/app/config.php ./kanboard-config.php

# Edit it locally
nano ./kanboard-config.php

# Stop container
docker stop kanboard
docker rm kanboard

# Start with volume mount
docker run -d \
  --name kanboard \
  -p 8080:80 \
  -v kanboard_data:/var/www/app/data \
  -v kanboard_plugins:/var/www/app/plugins \
  -v $(pwd)/kanboard-config.php:/var/www/app/config.php:ro \
  kanboard/kanboard:latest
```

---

## One-Liner Solution

If you just want to quickly test, run this on your VM:

```bash
docker exec kanboard sh -c "echo \"<?php\ndefined('APPLICATION_URL') or define('APPLICATION_URL', 'http://tasks.verslib.re');\n?>\n\$(cat /var/www/app/config.php)\" > /tmp/config.php && mv /tmp/config.php /var/www/app/config.php" && docker restart kanboard
```

(Replace `tasks.verslib.re` with your actual domain if different)

---

## Summary

The key fix is setting `APPLICATION_URL` in Kanboard's config.php to your public domain. This tells Kanboard to generate OAuth callbacks using `tasks.verslib.re` instead of `localhost`.

**That's it!** Your OAuth should now work correctly. 🎉
