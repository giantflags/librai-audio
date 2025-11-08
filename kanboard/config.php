<?php

/*
 * Kanboard Custom Configuration
 *
 * This file overrides default settings in /var/www/app/app/constants.php
 * Place this file in /var/www/app/config.php inside the container
 */

// ==============================================================================
// CRITICAL: Application URL Configuration for OAuth
// ==============================================================================

// Set this to your public domain URL (REQUIRED for Google OAuth)
// This ensures OAuth redirects use the correct public domain instead of localhost
defined('APPLICATION_URL') or define('APPLICATION_URL', 'http://tasks.verslib.re');

// If using HTTPS (recommended for production):
// defined('APPLICATION_URL') or define('APPLICATION_URL', 'https://tasks.verslib.re');

// ==============================================================================
// Database Configuration (Optional - defaults to SQLite)
// ==============================================================================

// SQLite (default - no configuration needed)
// Data stored in: /var/www/app/data/db.sqlite

// MySQL/MariaDB example:
// defined('DB_DRIVER') or define('DB_DRIVER', 'mysql');
// defined('DB_USERNAME') or define('DB_USERNAME', 'kanboard');
// defined('DB_PASSWORD') or define('DB_PASSWORD', 'your_password');
// defined('DB_HOSTNAME') or define('DB_HOSTNAME', 'db');
// defined('DB_NAME') or define('DB_NAME', 'kanboard');
// defined('DB_PORT') or define('DB_PORT', 3306);

// PostgreSQL example:
// defined('DB_DRIVER') or define('DB_DRIVER', 'postgres');
// defined('DB_USERNAME') or define('DB_USERNAME', 'kanboard');
// defined('DB_PASSWORD') or define('DB_PASSWORD', 'your_password');
// defined('DB_HOSTNAME') or define('DB_HOSTNAME', 'db');
// defined('DB_NAME') or define('DB_NAME', 'kanboard');
// defined('DB_PORT') or define('DB_PORT', 5432);

// ==============================================================================
// Reverse Proxy Configuration
// ==============================================================================

// Enable if behind a reverse proxy (Nginx/Apache)
defined('REVERSE_PROXY_AUTH') or define('REVERSE_PROXY_AUTH', false);

// Trust X-Forwarded-* headers from reverse proxy
// Required if using HTTPS termination at the reverse proxy
defined('REVERSE_PROXY_TRUST_HEADER') or define('REVERSE_PROXY_TRUST_HEADER', true);

// ==============================================================================
// Google OAuth Configuration
// ==============================================================================

// Enable Google OAuth authentication
defined('GOOGLE_AUTH') or define('GOOGLE_AUTH', true);

// Google OAuth Client ID (from Google Developer Console)
// Replace with your actual Client ID
defined('GOOGLE_CLIENT_ID') or define('GOOGLE_CLIENT_ID', 'YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com');

// Google OAuth Client Secret (from Google Developer Console)
// Replace with your actual Client Secret
defined('GOOGLE_CLIENT_SECRET') or define('GOOGLE_CLIENT_SECRET', 'YOUR_GOOGLE_CLIENT_SECRET');

// ==============================================================================
// Security Settings
// ==============================================================================

// Enable HTTPS (set to true if using SSL)
// defined('FORCE_HTTPS') or define('FORCE_HTTPS', true);

// Session timeout in seconds (default: 0 = until browser closes)
// defined('SESSION_DURATION') or define('SESSION_DURATION', 0);

// Enable brute force protection
defined('BRUTEFORCE_PROTECTION') or define('BRUTEFORCE_PROTECTION', true);

// Enable HSTS header (only if using HTTPS)
// defined('ENABLE_HSTS') or define('ENABLE_HSTS', true);

// ==============================================================================
// Email Configuration (Optional)
// ==============================================================================

// SMTP settings for email notifications
// defined('MAIL_TRANSPORT') or define('MAIL_TRANSPORT', 'smtp');
// defined('MAIL_SMTP_HOSTNAME') or define('MAIL_SMTP_HOSTNAME', 'smtp.gmail.com');
// defined('MAIL_SMTP_PORT') or define('MAIL_SMTP_PORT', 587);
// defined('MAIL_SMTP_USERNAME') or define('MAIL_SMTP_USERNAME', 'your-email@gmail.com');
// defined('MAIL_SMTP_PASSWORD') or define('MAIL_SMTP_PASSWORD', 'your-app-password');
// defined('MAIL_SMTP_ENCRYPTION') or define('MAIL_SMTP_ENCRYPTION', 'tls');
// defined('MAIL_FROM') or define('MAIL_FROM', 'kanboard@verslib.re');

// ==============================================================================
// Logging & Debug (Development Only)
// ==============================================================================

// Enable debug mode (DO NOT use in production)
// defined('DEBUG') or define('DEBUG', true);
// defined('LOG_DRIVER') or define('LOG_DRIVER', 'stdout');

// ==============================================================================
// Other Settings
// ==============================================================================

// Timezone
defined('TIMEZONE') or define('TIMEZONE', 'UTC');

// Language (default: en_US)
// defined('DEFAULT_LANGUAGE') or define('DEFAULT_LANGUAGE', 'en_US');

// Disable local authentication (force OAuth only)
// defined('DISABLE_LOGIN_FORM') or define('DISABLE_LOGIN_FORM', false);

// API tokens (for external integrations)
// defined('API_AUTHENTICATION') or define('API_AUTHENTICATION', true);

// File upload settings
// defined('FILES_DIR') or define('FILES_DIR', '/var/www/app/data/files');
// defined('FILE_MAX_SIZE') or define('FILE_MAX_SIZE', 10485760); // 10MB in bytes
