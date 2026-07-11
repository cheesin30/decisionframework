#!/usr/bin/env node
/*
 * The Long Game · Live Room relay — self-hosted, zero dependencies.
 *
 * Runs the whole live experience on company infrastructure: this one process
 * serves the game HTML files AND the realtime room API the phones/big screen
 * talk to. Nothing touches Firebase or any external service.
 *
 *   node live-server/server.js            # http://localhost:8877/
 *   PORT=9000 node live-server/server.js  # custom port
 *   STATIC_DIR=/path/to/html node ...     # serve game files from elsewhere
 *
 * In the game file set:  const LIVE_BACKEND = { databaseURL: "auto" };
 * (the client then talks to whatever origin served the page — this server).
 *
 * API contract (same shape the Firebase RTDB transport speaks, so the client
 * code is identical for both backends):
 *   GET  /rooms/CODE[.json][/sub/path.json]      -> JSON value at path
 *   PUT  /rooms/CODE[/sub/path].json  {body}     -> set value at path
 *   GET  /rooms/CODE.json  (Accept: text/event-stream)
 *        -> SSE stream: "put" {path:"/",data:<full>} on connect, then a
 *           "put" {path,data} per write; ":ka" comment every 25s keeps
 *           proxies from closing idle streams.
 *
 * State is in-memory (rooms are throwaway session artifacts); rooms idle for
 * ROOM_TTL_MS are purged. For HTTPS, put the company reverse proxy (nginx,
 * ALB, etc.) in front — SSE needs proxy buffering off (nginx:
 * `proxy_buffering off;`).
 */
'use strict';
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = +(process.env.PORT || 8877);
const STATIC_DIR = path.resolve(process.env.STATIC_DIR || path.join(__dirname, '..'));
const ROOM_TTL_MS = +(process.env.ROOM_TTL_MS || 6 * 3600e3); // purge rooms idle 6h
const MAX_ROOMS = 500;
const MAX_BODY = 64 * 1024;            // per-write payload cap
const KEEPALIVE_MS = 25e3;

const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css',
  '.png': 'image/png', '.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.json': 'application/json' };

const rooms = new Map(); // CODE -> { data, clients:Set<res>, touched }

function room(code) {
  if (!rooms.has(code)) {
    if (rooms.size >= MAX_ROOMS) return null;
    rooms.set(code, { data: null, clients: new Set(), touched: Date.now() });
  }
  const r = rooms.get(code);
  r.touched = Date.now();
  return r;
}

setInterval(() => {                    // GC idle rooms
  const cutoff = Date.now() - ROOM_TTL_MS;
  for (const [code, r] of rooms) {
    if (r.touched < cutoff) { for (const c of r.clients) c.end(); rooms.delete(code); }
  }
}, 30 * 60e3).unref();

setInterval(() => {                    // SSE keep-alive comments
  for (const r of rooms.values()) for (const c of r.clients) c.write(':ka\n\n');
}, KEEPALIVE_MS).unref();

function parseApi(url) {
  const clean = decodeURIComponent(url.split('?')[0]).replace(/\.json$/, '');
  const parts = clean.split('/').filter(Boolean);
  if (parts[0] !== 'rooms' || !parts[1]) return null;
  if (!/^[A-Z0-9]{1,8}$/i.test(parts[1])) return null;
  if (parts.length > 8) return null;   // path depth cap
  return { code: parts[1].toUpperCase(), sub: parts.slice(2) };
}
const getAt = (data, sub) => { let n = data; for (const k of sub) { if (n == null) return null; n = n[k]; } return n === undefined ? null : n; };
function setAt(r, sub, value) {
  if (!sub.length) { r.data = (value && typeof value === 'object') ? value : null; return; }
  if (typeof r.data !== 'object' || r.data === null) r.data = {};
  let n = r.data;
  for (let i = 0; i < sub.length - 1; i++) { if (typeof n[sub[i]] !== 'object' || n[sub[i]] === null) n[sub[i]] = {}; n = n[sub[i]]; }
  if (value === null) delete n[sub[sub.length - 1]]; else n[sub[sub.length - 1]] = value;
}
function broadcast(r, sub, value) {
  const payload = 'event: put\ndata: ' + JSON.stringify({ path: sub.length ? '/' + sub.join('/') : '/', data: value }) + '\n\n';
  for (const res of r.clients) res.write(payload);
}
const CORS = { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET,PUT,OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type', 'Cache-Control': 'no-store' };

function serveStatic(req, res) {
  let p = decodeURIComponent(req.url.split('?')[0]);
  if (p === '/' || p === '') p = '/long-term-game-live.html';
  const file = path.join(STATIC_DIR, path.normalize(p));
  if (!file.startsWith(STATIC_DIR)) { res.writeHead(403); res.end(); return; }   // no traversal
  fs.readFile(file, (err, data) => {
    if (err) {
      // graceful fallback for "/" when the default file name differs
      if (p === '/long-term-game-live.html') {
        return fs.readFile(path.join(STATIC_DIR, 'index.html'), (e2, d2) => {
          if (e2) { res.writeHead(404); res.end('not found'); }
          else { res.writeHead(200, { 'Content-Type': MIME['.html'] }); res.end(d2); }
        });
      }
      res.writeHead(p.includes('favicon') ? 204 : 404); res.end(); return;
    }
    res.writeHead(200, { 'Content-Type': MIME[path.extname(file).toLowerCase()] || 'application/octet-stream' });
    res.end(data);
  });
}

const server = http.createServer((req, res) => {
  if (req.method === 'OPTIONS') { res.writeHead(204, { ...CORS, 'Access-Control-Max-Age': '86400' }); res.end(); return; }

  const api = parseApi(req.url);
  if (!api) {
    if (req.method === 'GET') return serveStatic(req, res);
    res.writeHead(405); res.end(); return;
  }
  const r = room(api.code);
  if (!r) { res.writeHead(503, CORS); res.end('{"error":"room limit"}'); return; }

  if (req.method === 'GET' && (req.headers.accept || '').includes('text/event-stream')) {
    res.writeHead(200, { ...CORS, 'Content-Type': 'text/event-stream', Connection: 'keep-alive' });
    res.write('event: put\ndata: ' + JSON.stringify({ path: '/', data: r.data }) + '\n\n');
    r.clients.add(res);
    req.on('close', () => r.clients.delete(res));
    return;
  }
  if (req.method === 'GET') {
    res.writeHead(200, { ...CORS, 'Content-Type': 'application/json' });
    res.end(JSON.stringify(getAt(r.data, api.sub)));
    return;
  }
  if (req.method === 'PUT') {
    let body = '', size = 0;
    req.on('data', (c) => { size += c.length; if (size > MAX_BODY) { req.destroy(); } else body += c; });
    req.on('end', () => {
      let value; try { value = JSON.parse(body); } catch (e) { res.writeHead(400, CORS); res.end('{"error":"bad json"}'); return; }
      setAt(r, api.sub, value);
      broadcast(r, api.sub, value);
      res.writeHead(200, { ...CORS, 'Content-Type': 'application/json' });
      res.end(JSON.stringify(value));
    });
    return;
  }
  res.writeHead(405, CORS); res.end();
});

server.listen(PORT, () => {
  console.log(`Long Game live relay on http://localhost:${PORT}/  (static: ${STATIC_DIR})`);
  console.log('Game file must set  LIVE_BACKEND = { databaseURL: "auto" }');
});
module.exports = server;   // for tests
