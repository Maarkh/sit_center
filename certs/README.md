# TLS certificates for the nginx reverse proxy

The `nginx` service in `docker-compose.prod.yml` mounts this directory read-only at
`/etc/nginx/certs` and expects:

- `fullchain.pem` — certificate chain
- `privkey.pem` — private key

For a real deployment, issue them with certbot/Let's Encrypt, e.g.:

```
certbot certonly --standalone -d your.domain
cp /etc/letsencrypt/live/your.domain/fullchain.pem ./certs/
cp /etc/letsencrypt/live/your.domain/privkey.pem  ./certs/
```

For local testing you can generate a self-signed pair:

```
openssl req -x509 -newkey rsa:2048 -nodes -days 365 \
  -keyout certs/privkey.pem -out certs/fullchain.pem -subj "/CN=localhost"
```

The actual `*.pem` / `*.key` files are gitignored and must never be committed.
