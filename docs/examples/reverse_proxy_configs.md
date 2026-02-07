# Reverse Proxy Configuration Examples

This document provides complete configuration examples for enabling microphone access in various reverse proxy setups.

## Why This Is Needed

For the 2-way audio feature to work, your browser needs permission to access the microphone. Modern browsers require the `Permissions-Policy` HTTP header to allow microphone access. This header must be set by your reverse proxy or web server.

## Prerequisites

- Home Assistant must be accessed via HTTPS
- Your reverse proxy must be configured to forward requests to Home Assistant
- You must have administrative access to your reverse proxy configuration

---

## Nginx

### Full Nginx Configuration Example

```nginx
server {
    listen 443 ssl http2;
    server_name homeassistant.example.com;

    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    
    # IMPORTANT: Allow microphone access for 2-way audio
    add_header Permissions-Policy "microphone=(self)" always;

    location / {
        proxy_pass http://homeassistant:8123;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        proxy_http_version 1.1;
        proxy_buffering off;
    }
}
```

### Nginx Configuration Snippet (Add to Existing Config)

If you already have Nginx configured, add this line in your `server` block (outside of any `location` blocks):

```nginx
server {
    # ... your existing SSL and server settings ...
    
    # Add this line for microphone access (in server block, not location block)
    add_header Permissions-Policy "microphone=(self)" always;
    
    location / {
        # ... your existing proxy settings ...
    }
}
```

**Important:** Place the `add_header` directive in the `server` block to ensure it doesn't override other security headers.

---

## Nginx Proxy Manager

Nginx Proxy Manager provides a web UI for managing Nginx configurations.

### Steps

1. Open Nginx Proxy Manager web interface
2. Go to **Proxy Hosts**
3. Find your Home Assistant proxy host
4. Click the **⋮** menu → **Edit**
5. Go to the **Advanced** tab
6. Add this code to the "Custom Nginx Configuration" box:

```nginx
add_header Permissions-Policy "microphone=(self)" always;
```

7. Click **Save**
8. The changes take effect immediately

### Screenshot Reference
Your Advanced tab should look similar to this:
```
┌─────────────────────────────────────────┐
│ Custom Nginx Configuration              │
├─────────────────────────────────────────┤
│ add_header Permissions-Policy           │
│   "microphone=(self)" always;           │
└─────────────────────────────────────────┘
```

---

## Caddy

### Full Caddyfile Example

```caddy
homeassistant.example.com {
    reverse_proxy homeassistant:8123
    
    # Enable microphone access
    header {
        Permissions-Policy "microphone=(self)"
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "SAMEORIGIN"
    }
}
```

### Caddy Snippet (Add to Existing Config)

If you already have a Caddyfile, add the `Permissions-Policy` line to your `header` block:

```caddy
homeassistant.example.com {
    reverse_proxy homeassistant:8123
    
    header {
        # Add this line for microphone access
        Permissions-Policy "microphone=(self)"
    }
}
```

---

## Apache

### Full Apache VirtualHost Example

```apache
<VirtualHost *:443>
    ServerName homeassistant.example.com
    
    SSLEngine on
    SSLCertificateFile /path/to/fullchain.pem
    SSLCertificateKeyFile /path/to/privkey.pem
    
    # Security headers
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-Frame-Options "SAMEORIGIN"
    
    # IMPORTANT: Allow microphone access
    Header always set Permissions-Policy "microphone=(self)"
    
    ProxyPreserveHost On
    ProxyRequests Off
    
    <Location />
        ProxyPass http://homeassistant:8123/
        ProxyPassReverse http://homeassistant:8123/
        
        # WebSocket support
        RewriteEngine on
        RewriteCond %{HTTP:Upgrade} websocket [NC]
        RewriteCond %{HTTP:Connection} upgrade [NC]
        RewriteRule ^/?(.*) "ws://homeassistant:8123/$1" [P,L]
    </Location>
</VirtualHost>
```

### Apache Configuration Snippet

Add to your existing VirtualHost:

```apache
# Add this line for microphone access
Header always set Permissions-Policy "microphone=(self)"
```

**Note:** Make sure `mod_headers` is enabled:
```bash
sudo a2enmod headers
sudo systemctl restart apache2
```

---

## Traefik

### Traefik v2 - Docker Compose Labels

Add to your Home Assistant service in `docker-compose.yml`:

```yaml
services:
  homeassistant:
    image: homeassistant/home-assistant:latest
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.homeassistant.rule=Host(`homeassistant.example.com`)"
      - "traefik.http.routers.homeassistant.entrypoints=websecure"
      - "traefik.http.routers.homeassistant.tls=true"
      
      # Middleware for permissions policy
      - "traefik.http.middlewares.ha-permissions.headers.customresponseheaders.Permissions-Policy=microphone=(self)"
      - "traefik.http.routers.homeassistant.middlewares=ha-permissions"
```

### Traefik v2 - File Configuration

Create or edit your dynamic configuration file (e.g., `dynamic.yml`):

```yaml
http:
  middlewares:
    ha-permissions-policy:
      headers:
        customResponseHeaders:
          Permissions-Policy: "microphone=(self)"
          
  routers:
    homeassistant:
      rule: "Host(`homeassistant.example.com`)"
      service: homeassistant
      middlewares:
        - ha-permissions-policy
      tls:
        certResolver: letsencrypt
        
  services:
    homeassistant:
      loadBalancer:
        servers:
          - url: "http://homeassistant:8123"
```

---

## Cloudflare Tunnel

If you're using Cloudflare Tunnel (formerly Cloudflare Argo Tunnel):

### cloudflared Configuration

Cloudflare Tunnel doesn't directly support setting custom response headers through `config.yml`. You have two options:

#### Option 1: Use Cloudflare Workers (Recommended)

Create a Cloudflare Worker to add the header:

```javascript
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  const response = await fetch(request)
  const newResponse = new Response(response.body, response)
  
  // Add microphone permission
  newResponse.headers.set('Permissions-Policy', 'microphone=(self)')
  
  return newResponse
}
```

Deploy this worker and route it to your Home Assistant domain.

#### Option 2: Use a Local Reverse Proxy

Run a local Nginx or Caddy instance that adds the header, then point Cloudflare Tunnel to that:

```yaml
# config.yml
tunnel: <your-tunnel-id>
credentials-file: /etc/cloudflared/credentials.json

ingress:
  - hostname: homeassistant.example.com
    service: http://localhost:8080  # Local Nginx with Permissions-Policy header
  - service: http_status:404
```

Then configure Nginx on localhost:8080 to proxy to Home Assistant on :8123 with the proper headers.

---

## Home Assistant Add-on: Nginx Proxy Manager

If you're using the Nginx Proxy Manager add-on in Home Assistant:

1. Open **Nginx Proxy Manager** from your Home Assistant sidebar
2. Go to **Proxy Hosts**
3. Find your external Home Assistant entry (if you have one)
4. Click **⋮** → **Edit**
5. Go to **Advanced** tab
6. Add:
   ```nginx
   add_header Permissions-Policy "microphone=(self)" always;
   ```
7. **Save**

---

## Verification

After making changes, verify the header is set correctly:

### Using Browser Developer Tools

1. Open Home Assistant in your browser
2. Press `F12` to open Developer Tools
3. Go to the **Network** tab
4. Refresh the page
5. Click on the first request (usually the main document)
6. Look in the **Response Headers** section
7. You should see: `Permissions-Policy: microphone=(self)`

### Using curl

```bash
curl -I https://homeassistant.example.com | grep -i permissions-policy
```

You should see:
```
Permissions-Policy: microphone=(self)
```

---

## Troubleshooting

### Header Not Appearing

1. **Clear browser cache**: Hard refresh with `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
2. **Restart reverse proxy**: Make sure you restarted the service after configuration changes
3. **Check syntax**: Verify there are no typos in your configuration
4. **Check conflicting headers**: Make sure no other configuration is overriding the header

### Still Getting Permission Error

1. **Verify HTTPS**: Microphone access requires HTTPS
2. **Check browser permissions**: Ensure browser has permission to use the microphone
3. **Try different browser**: Test in Chrome, Firefox, or Safari
4. **Check Home Assistant logs**: Look for any related errors

### Multiple Origins

If you access Home Assistant from multiple domains, you can allow multiple origins:

```nginx
add_header Permissions-Policy "microphone=(self 'https://other-domain.com')" always;
```

---

## Security Considerations

- The `microphone=(self)` policy only allows microphone access from your own Home Assistant domain
- Audio is only captured when you press and hold the talkback button
- No audio is recorded or transmitted without explicit user action
- All audio transmission happens over your encrypted HTTPS connection

---

## Additional Resources

- [MDN: Permissions-Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Permissions-Policy)
- [Home Assistant HTTP Integration](https://www.home-assistant.io/integrations/http/)
- [Nginx Reverse Proxy Guide](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/)
- [Caddy Documentation](https://caddyserver.com/docs/)
- [Traefik Documentation](https://doc.traefik.io/traefik/)

---

## Need Help?

If you're still having issues:

1. Check the [main README troubleshooting section](../../README.md#troubleshooting)
2. Open an issue on [GitHub](https://github.com/constructorfleet/hacs-unifiprotect-2way-audio/issues)
3. Include:
   - Your reverse proxy type and version
   - Your configuration (sanitized)
   - Browser console errors
   - Network tab screenshot showing headers
