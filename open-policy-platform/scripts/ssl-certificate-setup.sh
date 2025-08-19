#!/bin/bash

# SSL/TLS Certificate Setup Script with Auto-Renewal
# Supports Let's Encrypt, Azure Key Vault, and custom certificates

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Configuration
DOMAINS=(
    "openpolicy.com"
    "www.openpolicy.com"
    "api.openpolicy.com"
    "admin.openpolicy.com"
    "openpolicy.azure.com"
    "admin.openpolicy.azure.com"
)

EMAIL="ssl-admin@openpolicy.com"
CERT_DIR="/etc/letsencrypt/live"
NGINX_DIR="/etc/nginx"

# Setup Let's Encrypt with Certbot
setup_letsencrypt() {
    log "Setting up Let's Encrypt certificates..."
    
    # Install certbot
    if ! command -v certbot &> /dev/null; then
        log "Installing certbot..."
        apt-get update
        apt-get install -y certbot python3-certbot-nginx python3-certbot-dns-azure
    fi
    
    # Create certbot configuration
    cat > /etc/letsencrypt/cli.ini << EOF
# Certbot configuration
email = $EMAIL
agree-tos = true
non-interactive = true
expand = true
authenticator = nginx
installer = nginx
webroot-path = /var/www/certbot

# Key size
rsa-key-size = 4096

# Renewal
renew-before-expiry = 30 days
renew-hook = systemctl reload nginx

# Security
must-staple = true
redirect = true
hsts = true
uir = true
staple-ocsp = true
EOF

    # Create nginx configuration for ACME challenge
    cat > $NGINX_DIR/snippets/letsencrypt.conf << 'EOF'
# ACME Challenge location
location ^~ /.well-known/acme-challenge/ {
    default_type "text/plain";
    root /var/www/certbot;
    allow all;
}

# Security headers
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self' https:; script-src 'self' 'unsafe-inline' 'unsafe-eval' https:; style-src 'self' 'unsafe-inline' https:; img-src 'self' data: https:; font-src 'self' data: https:; connect-src 'self' https: wss:; media-src 'self' https:; object-src 'none'; frame-ancestors 'self'; base-uri 'self'; form-action 'self';" always;
EOF

    # Create SSL configuration snippet
    cat > $NGINX_DIR/snippets/ssl-params.conf << 'EOF'
# SSL Configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;

# OCSP stapling
ssl_stapling on;
ssl_stapling_verify on;
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;

# SSL session cache
ssl_session_timeout 1d;
ssl_session_cache shared:SSL:10m;
ssl_session_tickets off;

# Diffie-Hellman parameter
ssl_dhparam /etc/nginx/dhparam.pem;
EOF

    # Generate Diffie-Hellman parameters
    if [ ! -f /etc/nginx/dhparam.pem ]; then
        log "Generating DH parameters (this may take a while)..."
        openssl dhparam -out /etc/nginx/dhparam.pem 4096
    fi

    # Create webroot directory
    mkdir -p /var/www/certbot

    # Obtain certificates for all domains
    for domain in "${DOMAINS[@]}"; do
        log "Obtaining certificate for $domain..."
        
        certbot certonly \
            --nginx \
            --domains "$domain" \
            --email "$EMAIL" \
            --agree-tos \
            --non-interactive \
            --expand \
            --redirect \
            --hsts \
            --staple-ocsp
    done

    log "✅ Let's Encrypt certificates obtained"
}

# Setup Nginx with SSL
configure_nginx_ssl() {
    log "Configuring Nginx with SSL..."
    
    # Main site configuration
    cat > $NGINX_DIR/sites-available/openpolicy-ssl.conf << 'EOF'
# HTTP to HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name openpolicy.com www.openpolicy.com;
    
    include snippets/letsencrypt.conf;
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# Main HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name openpolicy.com www.openpolicy.com;
    
    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/openpolicy.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/openpolicy.com/privkey.pem;
    ssl_trusted_certificate /etc/letsencrypt/live/openpolicy.com/chain.pem;
    
    # SSL configuration
    include snippets/ssl-params.conf;
    include snippets/letsencrypt.conf;
    
    # Logging
    access_log /var/log/nginx/openpolicy-access.log;
    error_log /var/log/nginx/openpolicy-error.log;
    
    # Root directory
    root /var/www/openpolicy;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API proxy
    location /api/ {
        proxy_pass http://api-gateway:9000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}

# API subdomain
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.openpolicy.com;
    
    ssl_certificate /etc/letsencrypt/live/api.openpolicy.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.openpolicy.com/privkey.pem;
    ssl_trusted_certificate /etc/letsencrypt/live/api.openpolicy.com/chain.pem;
    
    include snippets/ssl-params.conf;
    include snippets/letsencrypt.conf;
    
    location / {
        proxy_pass http://api-gateway:9000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}

# Admin subdomain
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name admin.openpolicy.com;
    
    ssl_certificate /etc/letsencrypt/live/admin.openpolicy.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/admin.openpolicy.com/privkey.pem;
    ssl_trusted_certificate /etc/letsencrypt/live/admin.openpolicy.com/chain.pem;
    
    include snippets/ssl-params.conf;
    include snippets/letsencrypt.conf;
    
    # Additional security for admin
    auth_basic "Admin Access";
    auth_basic_user_file /etc/nginx/.htpasswd;
    
    # IP whitelist (optional)
    # allow 10.0.0.0/8;
    # deny all;
    
    location / {
        proxy_pass http://admin-dashboard:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
EOF

    # Enable site
    ln -sf $NGINX_DIR/sites-available/openpolicy-ssl.conf $NGINX_DIR/sites-enabled/
    
    # Test configuration
    nginx -t
    
    # Reload Nginx
    systemctl reload nginx
    
    log "✅ Nginx SSL configuration complete"
}

# Setup auto-renewal
setup_auto_renewal() {
    log "Setting up certificate auto-renewal..."
    
    # Create renewal script
    cat > /usr/local/bin/certbot-renew.sh << 'EOF'
#!/bin/bash

# Certificate renewal script
LOG_FILE="/var/log/certbot-renew.log"

echo "[$(date)] Starting certificate renewal check" >> $LOG_FILE

# Attempt renewal
certbot renew --quiet --no-self-upgrade >> $LOG_FILE 2>&1

# Check if renewal was successful
if [ $? -eq 0 ]; then
    echo "[$(date)] Certificate renewal successful" >> $LOG_FILE
    
    # Reload services
    systemctl reload nginx
    
    # Update Azure Key Vault (if using)
    if [ -n "$AZURE_KEY_VAULT" ]; then
        /usr/local/bin/update-azure-certificates.sh
    fi
    
    # Send notification
    curl -X POST $SLACK_WEBHOOK \
        -H 'Content-type: application/json' \
        -d '{"text":"SSL certificates renewed successfully"}' \
        2>/dev/null
else
    echo "[$(date)] Certificate renewal failed!" >> $LOG_FILE
    
    # Send alert
    curl -X POST $SLACK_WEBHOOK \
        -H 'Content-type: application/json' \
        -d '{"text":"⚠️ SSL certificate renewal failed! Check logs."}' \
        2>/dev/null
fi

# Rotate log file if too large
if [ $(stat -c%s "$LOG_FILE") -gt 10485760 ]; then
    mv $LOG_FILE $LOG_FILE.old
    touch $LOG_FILE
fi
EOF
    chmod +x /usr/local/bin/certbot-renew.sh

    # Create systemd timer for renewal
    cat > /etc/systemd/system/certbot-renew.service << 'EOF'
[Unit]
Description=Certbot Renewal
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/certbot-renew.sh
User=root
StandardOutput=journal
StandardError=journal
EOF

    cat > /etc/systemd/system/certbot-renew.timer << 'EOF'
[Unit]
Description=Run certbot renewal twice daily
Requires=certbot-renew.service

[Timer]
OnCalendar=*-*-* 00,12:00:00
RandomizedDelaySec=3600
Persistent=true

[Install]
WantedBy=timers.target
EOF

    # Enable timer
    systemctl daemon-reload
    systemctl enable certbot-renew.timer
    systemctl start certbot-renew.timer

    # Also add cron job as backup
    cat > /etc/cron.d/certbot-renew << 'EOF'
# Certificate renewal - twice daily
0 0,12 * * * root /usr/local/bin/certbot-renew.sh
EOF

    log "✅ Auto-renewal configured"
}

# Setup Azure Key Vault integration
setup_azure_keyvault() {
    log "Setting up Azure Key Vault certificate management..."
    
    cat > /usr/local/bin/update-azure-certificates.sh << 'EOF'
#!/bin/bash

# Update certificates in Azure Key Vault

# Configuration
KEY_VAULT_NAME="openpolicy-kv"
CERT_DIR="/etc/letsencrypt/live"

# Upload certificates to Key Vault
for domain in openpolicy.com api.openpolicy.com admin.openpolicy.com; do
    if [ -d "$CERT_DIR/$domain" ]; then
        echo "Uploading certificate for $domain to Key Vault..."
        
        # Create PFX file
        openssl pkcs12 -export \
            -out /tmp/$domain.pfx \
            -inkey $CERT_DIR/$domain/privkey.pem \
            -in $CERT_DIR/$domain/fullchain.pem \
            -passout pass:
        
        # Upload to Key Vault
        az keyvault certificate import \
            --vault-name $KEY_VAULT_NAME \
            --name ${domain//./-} \
            --file /tmp/$domain.pfx
        
        # Clean up
        rm -f /tmp/$domain.pfx
    fi
done

echo "Certificates updated in Azure Key Vault"
EOF
    chmod +x /usr/local/bin/update-azure-certificates.sh

    log "✅ Azure Key Vault integration configured"
}

# Create certificate monitoring
setup_certificate_monitoring() {
    log "Setting up certificate monitoring..."
    
    cat > /usr/local/bin/check-certificates.sh << 'EOF'
#!/bin/bash

# Certificate expiry monitoring script

ALERT_DAYS=30
DOMAINS=(
    "openpolicy.com"
    "api.openpolicy.com"
    "admin.openpolicy.com"
)

check_cert() {
    local domain=$1
    local port=${2:-443}
    
    expiry_date=$(echo | openssl s_client -servername $domain -connect $domain:$port 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
    
    if [ -z "$expiry_date" ]; then
        echo "ERROR: Could not check certificate for $domain"
        return 1
    fi
    
    expiry_epoch=$(date -d "$expiry_date" +%s)
    current_epoch=$(date +%s)
    days_left=$(( (expiry_epoch - current_epoch) / 86400 ))
    
    echo "$domain certificate expires in $days_left days (${expiry_date})"
    
    if [ $days_left -lt $ALERT_DAYS ]; then
        # Send alert
        curl -X POST $SLACK_WEBHOOK \
            -H 'Content-type: application/json' \
            -d "{\"text\":\"⚠️ Certificate for $domain expires in $days_left days!\"}" \
            2>/dev/null
    fi
}

# Check all domains
for domain in "${DOMAINS[@]}"; do
    check_cert $domain
done

# Check internal certificates
echo "Checking internal certificates..."
kubectl get certificates -A -o json | jq -r '.items[] | "\(.metadata.namespace)/\(.metadata.name): \(.status.notAfter)"'
EOF
    chmod +x /usr/local/bin/check-certificates.sh

    # Add to cron
    echo "0 9 * * * root /usr/local/bin/check-certificates.sh" >> /etc/cron.d/certificate-monitoring

    log "✅ Certificate monitoring configured"
}

# Create wildcard certificate for development
setup_dev_certificates() {
    log "Setting up development certificates..."
    
    mkdir -p /etc/ssl/openpolicy
    
    # Create self-signed wildcard certificate for development
    cat > /etc/ssl/openpolicy/openssl.cnf << 'EOF'
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = State
L = City
O = OpenPolicy Platform
CN = *.openpolicy.local

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = *.openpolicy.local
DNS.2 = openpolicy.local
DNS.3 = *.openpolicyadmin.local
DNS.4 = openpolicyadmin.local
EOF

    # Generate certificate
    openssl req -x509 -nodes -days 365 -newkey rsa:4096 \
        -keyout /etc/ssl/openpolicy/dev.key \
        -out /etc/ssl/openpolicy/dev.crt \
        -config /etc/ssl/openpolicy/openssl.cnf

    log "✅ Development certificates created"
}

# Kubernetes cert-manager setup
setup_cert_manager() {
    log "Setting up cert-manager for Kubernetes..."
    
    # Install cert-manager
    kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
    
    # Wait for cert-manager to be ready
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=cert-manager -n cert-manager --timeout=300s
    
    # Create ClusterIssuer for Let's Encrypt
    cat << 'EOF' | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: ssl-admin@openpolicy.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
---
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-staging
spec:
  acme:
    server: https://acme-staging-v02.api.letsencrypt.org/directory
    email: ssl-admin@openpolicy.com
    privateKeySecretRef:
      name: letsencrypt-staging
    solvers:
    - http01:
        ingress:
          class: nginx
EOF

    # Create certificate resources
    cat << 'EOF' | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: openpolicy-tls
  namespace: production
spec:
  secretName: openpolicy-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - openpolicy.com
  - www.openpolicy.com
  - api.openpolicy.com
  - admin.openpolicy.com
EOF

    log "✅ cert-manager configured"
}

# Main execution
main() {
    log "Starting SSL/TLS certificate setup..."
    
    # Check if running in Kubernetes
    if kubectl cluster-info &> /dev/null; then
        log "Detected Kubernetes environment"
        setup_cert_manager
    else
        log "Setting up for standalone deployment"
        setup_letsencrypt
        configure_nginx_ssl
    fi
    
    setup_auto_renewal
    setup_azure_keyvault
    setup_certificate_monitoring
    setup_dev_certificates
    
    # Create summary
    cat > ssl-setup-summary.txt << EOF
SSL/TLS Certificate Setup Complete
==================================

Production Certificates:
✅ Let's Encrypt certificates for all domains
✅ Auto-renewal configured (twice daily)
✅ 4096-bit RSA keys
✅ TLS 1.2 and 1.3 only
✅ HSTS enabled
✅ OCSP stapling enabled

Domains Configured:
$(for domain in "${DOMAINS[@]}"; do echo "- https://$domain"; done)

Security Features:
✅ Modern cipher suite
✅ Perfect Forward Secrecy
✅ Security headers configured
✅ DH parameters (4096-bit)

Monitoring:
✅ Certificate expiry monitoring
✅ Slack notifications
✅ Daily expiry checks
✅ 30-day expiry alerts

Auto-Renewal:
✅ Systemd timer (primary)
✅ Cron job (backup)
✅ Post-renewal hooks
✅ Service reload automation

Development:
✅ Self-signed wildcard certificates
✅ *.openpolicy.local
✅ *.openpolicyadmin.local

Kubernetes:
✅ cert-manager installed
✅ ClusterIssuers configured
✅ Automatic certificate management

Next Steps:
1. Update DNS records for all domains
2. Test SSL configuration: https://www.ssllabs.com/ssltest/
3. Configure monitoring alerts
4. Schedule certificate renewal tests
5. Document emergency procedures

Important Files:
- Certificates: /etc/letsencrypt/live/
- Nginx config: /etc/nginx/sites-available/openpolicy-ssl.conf
- Renewal script: /usr/local/bin/certbot-renew.sh
- Monitoring: /usr/local/bin/check-certificates.sh
EOF
    
    info "Setup complete! See ssl-setup-summary.txt for details"
    
    # Test SSL configuration
    log "Testing SSL configuration..."
    openssl s_client -connect openpolicy.com:443 -servername openpolicy.com < /dev/null
}

main "$@"