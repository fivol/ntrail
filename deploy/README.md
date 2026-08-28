# Deploying NTrail

The frontend is a static bundle; the backend is a container behind it.

## Frontend

Built inside Docker so the 2020-era toolchain does not have to run on the host:

```bash
docker run --rm -v "$PWD/frontend":/app -w /app node:16-alpine sh -c \
  "npm install --legacy-peer-deps && REACT_APP_API_HOST=/api npm run build"

sudo rsync -a --delete frontend/build/ /var/www/ntrail/
```

`REACT_APP_API_HOST=/api` makes the bundle call the backend on its own origin,
which is what the nginx config below expects.

## Backend

```bash
cp .env.example .env      # fill in the VK credentials and a database password
docker compose up -d --build
```

Binds to `127.0.0.1:5000`; nginx is the only thing that reaches it.

## nginx

```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/ntrail
sudo ln -s /etc/nginx/sites-available/ntrail /etc/nginx/sites-enabled/ntrail
sudo nginx -t && sudo systemctl reload nginx
```

Then point the domain's A record at the server and issue a certificate:

```bash
sudo certbot --nginx -d ntrail.fiobond.me
```
