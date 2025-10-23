# Shared location blocks for RentFlow Staging
# Relaxed rate limiting for easier testing

# Timeouts
proxy_connect_timeout 90s;
proxy_send_timeout 90s;
proxy_read_timeout 90s;

# Static files caching (shorter for staging)
location /static {
    alias /app/website/static;
    expires 1h;
    add_header Cache-Control "public";
    add_header X-Environment "staging" always;
}

# Uploaded files
location /uploads {
    alias /app/uploads;
    expires 1h;
    add_header Cache-Control "private";
    add_header X-Environment "staging" always;
}

# Authentication endpoints - relaxed rate limiting for testing
location ~ ^/(login|register|reset-password) {
    limit_req zone=auth burst=20 nodelay;
    proxy_pass http://rentflow_app;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_redirect off;
}

# Health check endpoint - no rate limiting
location /health {
    proxy_pass http://rentflow_app;
    proxy_set_header Host $host;
    access_log off;
}

# Main application - very relaxed rate limiting for testing
location / {
    limit_req zone=general burst=50 nodelay;
    proxy_pass http://rentflow_app;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_redirect off;

    # WebSocket support
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}

# Custom error pages
error_page 502 503 504 /50x.html;
location = /50x.html {
    root /usr/share/nginx/html;
}
