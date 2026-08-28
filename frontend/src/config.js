// The API host. Set REACT_APP_API_HOST at build time to point the bundle at a
// deployed backend ("/api" when nginx proxies it under the same origin);
// falls back to the local dev backend.
export const apiHost = process.env.REACT_APP_API_HOST || "http://localhost:5050";
