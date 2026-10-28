#!/bin/bash
set -e

CONF_FILE="/etc/nginx/sites-available/myproject"

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root or with sudo: sudo bash $0"
  exit 1
fi

# 1. Create a backup
cp "$CONF_FILE" "${CONF_FILE}.bak.$(date +%F_%T)"

# 2. Check and add location /media/ if missing
python3 -c "
import re, sys

path = '$CONF_FILE'
with open(path, 'r') as f:
    content = f.read()

if 'location /media/' in content:
    print('Media block already exists in nginx config.')
    sys.exit(0)

target = '''    location /static/ {
        alias /home/deploy/laronhall/staticfiles/;
    }'''

replacement = '''    location /static/ {
        alias /home/deploy/laronhall/staticfiles/;
    }

    location /media/ {
        alias /home/deploy/laronhall/media/;
    }'''

if target not in content:
    # Fallback to regex
    content_new = re.sub(r'location\s+/static/\s*\{[^}]*\}', replacement, content)
else:
    content_new = content.replace(target, replacement, 1)

with open(path, 'w') as f:
    f.write(content_new)
print('Successfully inserted /media/ block into nginx config.')
"

# 3. Test nginx configuration
echo "Testing Nginx configuration..."
nginx -t

# 4. Reload Nginx
echo "Reloading Nginx..."
systemctl reload nginx

echo "--------------------------------------------------------"
echo "DONE! Nginx is now directly serving media files."
echo "Images and videos will now load instantly without locking Gunicorn."
echo "--------------------------------------------------------"
