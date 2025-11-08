# Frequently Asked Questions (FAQ)

## General Questions

### What is Kanboard?

Kanboard is a free and open-source Kanban project management software. It helps teams visualize work, track progress, and collaborate effectively using boards, cards, and workflows.

### Why use Docker for deployment?

Docker provides:
- Consistent environment across different servers
- Easy updates and rollbacks
- Isolation from host system
- Simple backup and restore
- Portable configuration

---

## OAuth & Authentication

### Q: Why do I get "redirect_uri_mismatch" error?

**A:** This happens when the OAuth callback URL doesn't match between:
1. What Kanboard generates (based on `APPLICATION_URL`)
2. What's configured in Google Cloud Console

**Solution:**
- Set `APPLICATION_URL` in config.php to your public domain
- Ensure Google OAuth redirect URI matches exactly: `{APPLICATION_URL}/oauth/google/callback`

### Q: Can I use multiple OAuth providers?

**A:** Yes! Kanboard supports:
- Google OAuth
- GitHub OAuth
- GitLab OAuth
- Microsoft OAuth

Configure additional providers in config.php.

### Q: Should I disable password login?

**A:** Only after:
1. OAuth is working correctly
2. You've logged in with OAuth successfully
3. Your OAuth account has admin privileges

Then you can set:
```php
defined('DISABLE_LOGIN_FORM') or define('DISABLE_LOGIN_FORM', true);
```

### Q: What happens if OAuth goes down?

**A:** If you've disabled password login and OAuth fails:
1. SSH into your server
2. Edit config.php: Set `DISABLE_LOGIN_FORM` to `false`
3. Restart container: `docker restart kanboard`
4. Login with admin account

**Recommendation:** Keep at least one local admin account enabled as backup.

### Q: Can I restrict OAuth to specific email domains?

**A:** Yes! In Google Cloud Console:
1. Set OAuth consent screen to "Internal" (requires Google Workspace)
2. This restricts authentication to your organization only

For external OAuth with email filtering, you'll need a custom solution or Kanboard plugin.

---

## Configuration

### Q: Where should I set APPLICATION_URL?

**A:** Set it in **config.php**, not in Docker environment variables.

```php
defined('APPLICATION_URL') or define('APPLICATION_URL', 'http://your-domain.com');
```

This is critical for OAuth redirects.

### Q: Should I use HTTP or HTTPS?

**For development/testing:** HTTP is fine
**For production:** Always use HTTPS

Benefits of HTTPS:
- Encrypted communication
- Prevents MITM attacks
- Required by many OAuth providers in production
- Better SEO and user trust

### Q: Can I change the port from 8080?

**A:** Yes, edit docker-compose.yml:

```yaml
ports:
  - "3000:80"  # Maps host port 3000 to container port 80
```

Then access via http://your-domain:3000

### Q: Do I need a database server?

**A:** Not necessarily:
- **SQLite (default):** No separate database needed, perfect for small teams (< 20 users)
- **MySQL/PostgreSQL:** Better for larger deployments, multiple workers, or high traffic

---

## Deployment & Updates

### Q: How do I update Kanboard?

**A:** Simple 3-step process:

```bash
# 1. Pull latest image
docker-compose pull

# 2. Recreate container
docker-compose up -d

# 3. Verify
docker logs kanboard
```

### Q: Will updates delete my data?

**A:** No! Data is stored in Docker volumes which persist across updates.

Always backup before updates:
```bash
docker run --rm --volumes-from kanboard \
  -v $(pwd):/backup \
  alpine tar -czf /backup/kanboard-backup.tar.gz /var/www/app/data
```

### Q: Can I run multiple Kanboard instances?

**A:** Yes! Change:
1. Container name
2. Port mapping
3. Volume names

Example docker-compose.yml:
```yaml
services:
  kanboard_dev:
    container_name: kanboard_dev
    ports:
      - "8081:80"
    volumes:
      - kanboard_dev_data:/var/www/app/data
```

### Q: How do I migrate from another server?

**A:**
1. Backup old server: Tar `/var/www/app/data` directory
2. Copy backup to new server
3. Deploy Kanboard on new server
4. Restore data:
```bash
docker run --rm --volumes-from kanboard \
  -v $(pwd):/backup \
  alpine tar -xzf /backup/kanboard-backup.tar.gz -C /
```
5. Restart: `docker restart kanboard`

---

## Security

### Q: Is it safe to expose Kanboard to the internet?

**A:** Yes, if you follow security best practices:
- ✅ Use HTTPS with valid SSL certificate
- ✅ Enable security headers (HSTS, etc.)
- ✅ Use strong passwords or OAuth only
- ✅ Keep Kanboard updated
- ✅ Use firewall rules
- ❌ Don't use default admin credentials
- ❌ Don't commit secrets to git

### Q: Should I use a reverse proxy?

**A:** Highly recommended for production:
- SSL/TLS termination
- Load balancing
- Better logging
- Security headers
- Rate limiting
- DDoS protection

Nginx or Caddy are popular choices.

### Q: How do I enable HTTPS?

**A:** Two options:

**Option 1: Let's Encrypt (Recommended)**
```bash
sudo certbot --nginx -d your-domain.com
```

**Option 2: Manual certificate**
1. Obtain SSL certificate
2. Configure in Nginx
3. Update APPLICATION_URL to use `https://`

See docs/SSL_SETUP.md for details.

### Q: What should I backup?

**A:** Essential items:
- `/var/www/app/data` - Database, uploads, files
- `config.php` - Your configuration (store securely!)
- `.env` - Environment variables (store securely!)

**Backup command:**
```bash
# Data
docker run --rm --volumes-from kanboard \
  -v $(pwd):/backup \
  alpine tar -czf /backup/kanboard-backup-$(date +%F).tar.gz \
  /var/www/app/data

# Configuration
cp config.php config-backup-$(date +%F).php
```

---

## Performance & Scaling

### Q: How many users can Kanboard handle?

**A:** Depends on configuration:
- **SQLite:** 10-20 concurrent users
- **MySQL/PostgreSQL:** 100+ concurrent users
- **With proper tuning:** 1000+ users

### Q: My Kanboard is slow. How can I optimize it?

**A:** Performance tips:
1. Switch from SQLite to PostgreSQL/MySQL
2. Increase Docker container resources
3. Enable PHP opcode cache
4. Use Redis for sessions
5. Optimize database indexes
6. Reduce background workers

### Q: Can I use an external database?

**A:** Yes! In config.php:

```php
defined('DB_DRIVER') or define('DB_DRIVER', 'mysql');
defined('DB_USERNAME') or define('DB_USERNAME', 'kanboard');
defined('DB_PASSWORD') or define('DB_PASSWORD', 'password');
defined('DB_HOSTNAME') or define('DB_HOSTNAME', 'your-db-host');
defined('DB_NAME') or define('DB_NAME', 'kanboard');
```

---

## Customization

### Q: Can I customize the look and feel?

**A:** Yes! Options:
1. **Themes:** Install from plugin directory
2. **Custom CSS:** Place in `/var/www/app/assets/css/custom/`
3. **Plugins:** Extend functionality

### Q: How do I install plugins?

**A:**
1. Download plugin
2. Extract to `/var/www/app/plugins/`
3. Go to Settings → Plugins
4. Enable the plugin

Via Docker:
```bash
docker exec kanboard /bin/bash
cd /var/www/app/plugins
# Download and extract plugin
```

### Q: Can I integrate with Slack/Email/etc?

**A:** Yes! Kanboard supports:
- Email notifications
- Slack integration
- Webhook notifications
- Calendar integration
- More via plugins

Configure in Settings → Integrations.

---

## Troubleshooting

### Q: Container won't start. What do I check?

**A:** Debug steps:
```bash
# 1. Check logs
docker logs kanboard

# 2. Verify config.php syntax
php -l config.php

# 3. Check port availability
sudo lsof -i :8080

# 4. Verify file permissions
ls -la config.php

# 5. Check Docker volumes
docker volume ls
docker volume inspect kanboard_kanboard_data
```

### Q: OAuth worked before but now fails. What happened?

**A:** Common causes:
1. **Config change:** APPLICATION_URL was modified
2. **Google changes:** OAuth credentials rotated or app suspended
3. **DNS change:** Domain points to different IP
4. **Container recreated:** Config not properly mounted

**Solution:**
- Verify config.php is mounted correctly
- Check Google Cloud Console for app status
- Restart container: `docker restart kanboard`

### Q: I can't access Kanboard from external network

**A:** Checklist:
- [ ] DNS resolves to correct IP: `nslookup your-domain.com`
- [ ] Port 80/443 open on firewall
- [ ] Docker container running: `docker ps`
- [ ] Reverse proxy configured correctly (if using)
- [ ] No cloud firewall rules blocking traffic

```bash
# Test from external network
curl -I http://your-domain.com
```

### Q: How do I reset admin password?

**A:** Via command line:

```bash
docker exec -it kanboard /bin/bash
cd /var/www/app
./cli user:reset-password admin newpassword
exit
```

### Q: I lost my OAuth credentials. How do I recover?

**A:**
1. Disable OAuth requirement in config.php:
```php
defined('DISABLE_LOGIN_FORM') or define('DISABLE_LOGIN_FORM', false);
```
2. Restart: `docker restart kanboard`
3. Login with admin account
4. Generate new OAuth credentials in Google Console
5. Update config.php

---

## Best Practices

### Q: What's the recommended deployment setup?

**A:** Production-ready setup:
```
Internet
    ↓
Nginx (HTTPS, port 443)
    ↓
Docker Container (Kanboard, port 8080)
    ↓
PostgreSQL/MySQL Database
```

With:
- Let's Encrypt SSL
- Firewall rules
- Regular backups
- Monitoring/logging
- OAuth authentication

### Q: How often should I backup?

**A:** Recommended schedule:
- **Daily:** Automated backups
- **Before updates:** Manual backup
- **After major changes:** Manual backup

Retention:
- Keep daily backups for 7 days
- Keep weekly backups for 4 weeks
- Keep monthly backups for 12 months

### Q: Should I run Kanboard as root?

**A:** No! The official Docker image runs as www-data user by default. Never modify this to run as root.

---

## Getting Help

### Q: Where can I get more help?

**A:**
- **Official docs:** https://docs.kanboard.org/
- **Community forum:** https://kanboard.discourse.group/
- **GitHub issues:** https://github.com/kanboard/kanboard/issues
- **This repo docs:** Check docs/ directory

### Q: How do I report a bug?

**A:**
1. Check if it's a known issue
2. Gather information:
   - Kanboard version
   - Docker image version
   - Error logs
   - Steps to reproduce
3. Open issue on GitHub
4. Include all relevant details

### Q: Can I contribute?

**A:** Yes! Ways to contribute:
- Report bugs
- Submit pull requests
- Improve documentation
- Create plugins
- Help others in forums

---

## Miscellaneous

### Q: What's the difference between Kanboard and Trello?

**A:**
| Feature | Kanboard | Trello |
|---------|----------|--------|
| Hosting | Self-hosted | Cloud only |
| Cost | Free, open-source | Free tier, paid plans |
| Privacy | Full control | Atlassian manages |
| Customization | Fully customizable | Limited |
| Integrations | Via plugins | Many native |

### Q: Can I use Kanboard commercially?

**A:** Yes! Kanboard is MIT licensed - free for commercial use.

### Q: Does Kanboard have a mobile app?

**A:** No official app, but:
- Web interface is mobile-responsive
- Community apps available
- API allows custom app development

### Q: Can I import data from Trello/Jira?

**A:** Yes! Via:
- Import plugins
- CSV import
- API migration scripts

---

**Still have questions?** Check the other documentation files or open an issue!
