# NTrail

A research platform for navigating social networks: give it a link to a public
profile and it assembles what open sources say about that person or community —
their graph, the communities they belong to, the traits that can be inferred
from it — and lets you compare profiles against each other.

Built 2019–2022 as a university research project (MIPT). **Archived**: the code
is published for reference, it is not maintained, and running it needs your own
API credentials.

> MVP screenshots and the original product walkthrough (RU) live in
> [`backend/description.md`](backend/description.md),
> [`backend/interfeis.md`](backend/interfeis.md) and
> [`backend/example1.md`](backend/example1.md).

## Why it exists

Doing this by hand is possible and unbearable: open a profile, open their
friends, notice that two of them went to the same school, repeat a thousand
times. NTrail does the crawl, the joins and the ranking, and shows the result as
a graph you can walk.

The hard parts it was built around:

- **Dirty data** — profiles with wrong ages, empty fields, hidden friend lists.
  Missing attributes are inferred from the neighbourhood instead of trusted from
  the profile.
- **Rate limits** — VK allows ~3 requests/second, Instagram had no usable API at
  all, so collection is spread over a fleet of workers and accounts rather than
  a single client.
- **Identity across networks** — matching the same person across VK, Instagram
  and the rest through graph overlap, nickname similarity and photos.

## Architecture

Six repositories, now one. Data flows right to left:

```
frontend ──► backend ──► core ──► worker ──► VK / Instagram / …
  React      Flask API   domain    request      public APIs
  + graph    + Postgres  objects   executor     and pages
                            ▲         │
                            │         └── credentials (token pool)
                            └── api (FastAPI service layer + Redis)
```

| Directory | What it is |
|---|---|
| `frontend/` | The MVP interface: React 16 + Redux, graph rendering with sigma / vis, charts with recharts. Paste a profile URL in the search bar and walk the result |
| `backend/` | Flask API over PostgreSQL: query objects, selective execution, caching, and the nginx config it ran behind |
| `core/` | The domain layer: `VKUser`, `VKCommunity` and friends. Classes with methods like `friends()`, `groups()`, `posts()` that hide whether the answer came from an API, a parser or the cache |
| `worker/` | The execution unit. Takes a batch of atomic requests (method, token, parameters), fans them across cores and threads, caches the results, returns them. Runs as a library or as a server on many machines |
| `api/` | The later service layer: FastAPI + Redis + gino, with the analysis stack — networkx and python-louvain for communities, pymorphy2 / nltk / pymystem3 for text |
| `credentials/` | A small FastAPI service holding the pool of access tokens the workers draw from |

Each directory keeps the full history of the repository it came from — 470+
commits, imported rather than squashed.

## Running it

Nothing here talks to a social network without credentials of your own.

```bash
cp .env.example .env      # VK app id/secret, database URL, app secret
docker compose up -d --build
```

That brings up PostgreSQL and the Flask backend on `:5000`. The frontend is a
Create React App project:

```bash
cd frontend && npm install && npm start      # http://localhost:3000
npm run build                                # static bundle for nginx
```

`api/`, `worker/` and `credentials/` are Poetry projects (`poetry install`),
each with its own `docker-stack.yml` from when they ran as separate services.

## Configuration

| Variable | What it is |
|---|---|
| `VK_APP_ID`, `VK_APP_SECRET` | VK application credentials, for OAuth |
| `MY_VK_ACCESS_TOKEN` | A VK access token for server-side calls |
| `MAIN_DB_URL` | `postgresql://user:pass@host:5432/ntrail` |
| `APP_SECRET_KEY` | Flask session key |
| `HOST` | Public URL of the deployment |

Every secret that was once committed here has been purged from the history; the
tokens that leaked have been revoked.

## Licence

MIT — see [LICENSE](LICENSE). It only covers the code: what you may collect
with it is governed by the terms of the services you point it at.
