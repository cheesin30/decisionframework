// The Long Game · Live Room relay — C# core, hosted by server.ps1 (Add-Type)
// on stock Windows PowerShell 5.1 with ZERO downloads, or compiled/run
// directly (mcs/csc + mono/.NET) anywhere else.
//
// Deliberately conservative C# 5 / .NET Framework 4.0 code with no external
// assembly references (hand-rolled JSON), because PowerShell 5.1's built-in
// compiler and locked-down corporate machines are the target.
//
// Same wire protocol as server.js / server.py:
//   GET  /rooms/CODE[/sub].json                        -> JSON at path
//   PUT  /rooms/CODE[/sub].json {json}                 -> set at path
//   GET  /rooms/CODE.json (Accept: text/event-stream)  -> SSE "put" events,
//        full snapshot on connect, ":ka" keep-alive every 25s
// Static files served from a root dir; served .html gets its LIVE_BACKEND
// line rewritten to "auto" so the game talks back to this server, unedited.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Net;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;

namespace LongGameRelay
{
    // ── minimal JSON (objects, arrays, strings, numbers, true/false/null) ──
    public static class Json
    {
        public static object Parse(string s)
        {
            int i = 0;
            object v = ParseValue(s, ref i);
            SkipWs(s, ref i);
            if (i != s.Length) throw new Exception("trailing json");
            return v;
        }
        static void SkipWs(string s, ref int i)
        {
            while (i < s.Length && (s[i] == ' ' || s[i] == '\t' || s[i] == '\n' || s[i] == '\r')) i++;
        }
        static object ParseValue(string s, ref int i)
        {
            SkipWs(s, ref i);
            if (i >= s.Length) throw new Exception("eof");
            char c = s[i];
            if (c == '{')
            {
                i++;
                Dictionary<string, object> d = new Dictionary<string, object>();
                SkipWs(s, ref i);
                if (s[i] == '}') { i++; return d; }
                while (true)
                {
                    SkipWs(s, ref i);
                    string k = ParseString(s, ref i);
                    SkipWs(s, ref i);
                    if (s[i++] != ':') throw new Exception("colon");
                    d[k] = ParseValue(s, ref i);
                    SkipWs(s, ref i);
                    char n = s[i++];
                    if (n == ',') continue;
                    if (n == '}') return d;
                    throw new Exception("obj");
                }
            }
            if (c == '[')
            {
                i++;
                List<object> a = new List<object>();
                SkipWs(s, ref i);
                if (s[i] == ']') { i++; return a; }
                while (true)
                {
                    a.Add(ParseValue(s, ref i));
                    SkipWs(s, ref i);
                    char n = s[i++];
                    if (n == ',') continue;
                    if (n == ']') return a;
                    throw new Exception("arr");
                }
            }
            if (c == '"') return ParseString(s, ref i);
            if (c == 't') { Expect(s, ref i, "true"); return true; }
            if (c == 'f') { Expect(s, ref i, "false"); return false; }
            if (c == 'n') { Expect(s, ref i, "null"); return null; }
            int start = i;
            while (i < s.Length && ("+-.eE0123456789".IndexOf(s[i]) >= 0)) i++;
            return double.Parse(s.Substring(start, i - start), CultureInfo.InvariantCulture);
        }
        static void Expect(string s, ref int i, string w)
        {
            if (i + w.Length > s.Length || s.Substring(i, w.Length) != w) throw new Exception(w);
            i += w.Length;
        }
        static string ParseString(string s, ref int i)
        {
            if (s[i++] != '"') throw new Exception("str");
            StringBuilder b = new StringBuilder();
            while (true)
            {
                char c = s[i++];
                if (c == '"') return b.ToString();
                if (c == '\\')
                {
                    char e = s[i++];
                    if (e == 'n') b.Append('\n');
                    else if (e == 't') b.Append('\t');
                    else if (e == 'r') b.Append('\r');
                    else if (e == 'b') b.Append('\b');
                    else if (e == 'f') b.Append('\f');
                    else if (e == 'u')
                    {
                        b.Append((char)Convert.ToInt32(s.Substring(i, 4), 16));
                        i += 4;
                    }
                    else b.Append(e);   // \" \\ \/
                }
                else b.Append(c);
            }
        }
        public static string Serialize(object v)
        {
            StringBuilder b = new StringBuilder();
            Write(v, b);
            return b.ToString();
        }
        static void Write(object v, StringBuilder b)
        {
            if (v == null) { b.Append("null"); return; }
            if (v is bool) { b.Append(((bool)v) ? "true" : "false"); return; }
            if (v is string) { WriteString((string)v, b); return; }
            if (v is Dictionary<string, object>)
            {
                b.Append('{');
                bool first = true;
                foreach (KeyValuePair<string, object> kv in (Dictionary<string, object>)v)
                {
                    if (!first) b.Append(',');
                    first = false;
                    WriteString(kv.Key, b);
                    b.Append(':');
                    Write(kv.Value, b);
                }
                b.Append('}');
                return;
            }
            if (v is List<object>)
            {
                b.Append('[');
                bool first = true;
                foreach (object it in (List<object>)v)
                {
                    if (!first) b.Append(',');
                    first = false;
                    Write(it, b);
                }
                b.Append(']');
                return;
            }
            // numbers (double from Parse; ints if constructed manually)
            b.Append(Convert.ToString(v, CultureInfo.InvariantCulture));
        }
        static void WriteString(string s, StringBuilder b)
        {
            b.Append('"');
            foreach (char c in s)
            {
                if (c == '"') b.Append("\\\"");
                else if (c == '\\') b.Append("\\\\");
                else if (c == '\n') b.Append("\\n");
                else if (c == '\r') b.Append("\\r");
                else if (c == '\t') b.Append("\\t");
                else if (c < ' ') b.Append("\\u" + ((int)c).ToString("x4"));
                else b.Append(c);
            }
            b.Append('"');
        }
    }

    class Room
    {
        public object Data;
        public List<BlockingCollection<byte[]>> Clients = new List<BlockingCollection<byte[]>>();
        public DateTime Touched = DateTime.UtcNow;
    }

    public static class Server
    {
        static Dictionary<string, Room> rooms = new Dictionary<string, Room>();
        static object gate = new object();
        static string staticDir;
        const int MaxRooms = 500, MaxBody = 64 * 1024, MaxDepth = 8, KeepAliveMs = 25000;
        static TimeSpan RoomTtl = TimeSpan.FromHours(6);

        static Room GetRoom(string code)
        {
            lock (gate)
            {
                Room r;
                if (!rooms.TryGetValue(code, out r))
                {
                    if (rooms.Count >= MaxRooms) return null;
                    r = new Room();
                    rooms[code] = r;
                }
                r.Touched = DateTime.UtcNow;
                return r;
            }
        }

        public static void Run(int port, string staticRoot)
        {
            staticDir = Path.GetFullPath(staticRoot);
            Thread gc = new Thread(GcLoop); gc.IsBackground = true; gc.Start();

            HttpListener listener = new HttpListener();
            bool allInterfaces = true;
            listener.Prefixes.Add("http://+:" + port + "/");
            try { listener.Start(); }
            catch (HttpListenerException)
            {
                // Non-admin Windows can't bind all interfaces without a URL ACL.
                allInterfaces = false;
                listener = new HttpListener();
                listener.Prefixes.Add("http://localhost:" + port + "/");
                listener.Start();
            }
            Console.WriteLine("Long Game live relay (PowerShell/C#) on http://localhost:" + port + "/  (static: " + staticDir + ")");
            if (allInterfaces)
            {
                Console.WriteLine("Reachable by phones at http://<this-computer's-IP>:" + port + "/  (allow the firewall prompt)");
            }
            else
            {
                Console.WriteLine("");
                Console.WriteLine("NOTE: running in LOCALHOST-ONLY mode — this browser works, phones can NOT connect yet.");
                Console.WriteLine("To let phones in, do ONE of these and rerun:");
                Console.WriteLine("  a) right-click PowerShell -> 'Run as administrator' and start this again, OR");
                Console.WriteLine("  b) have an admin run once:  netsh http add urlacl url=http://+:" + port + "/ user=Everyone");
            }
            Console.WriteLine("Served pages are auto-switched to LIVE_BACKEND \"auto\".");
            while (true)
            {
                HttpListenerContext ctx = listener.GetContext();
                ThreadPool.QueueUserWorkItem(delegate(object o) { Handle((HttpListenerContext)o); }, ctx);
            }
        }

        static void GcLoop()
        {
            while (true)
            {
                Thread.Sleep(30 * 60 * 1000);
                lock (gate)
                {
                    List<string> dead = new List<string>();
                    foreach (KeyValuePair<string, Room> kv in rooms)
                        if (DateTime.UtcNow - kv.Value.Touched > RoomTtl) dead.Add(kv.Key);
                    foreach (string code in dead)
                    {
                        foreach (BlockingCollection<byte[]> q in rooms[code].Clients) q.Add(null);
                        rooms.Remove(code);
                    }
                }
            }
        }

        static void Cors(HttpListenerResponse res)
        {
            res.Headers["Access-Control-Allow-Origin"] = "*";
            res.Headers["Access-Control-Allow-Methods"] = "GET,PUT,OPTIONS";
            res.Headers["Access-Control-Allow-Headers"] = "Content-Type";
            res.Headers["Cache-Control"] = "no-store";
        }

        static void SendJson(HttpListenerContext ctx, string json, int status)
        {
            byte[] b = Encoding.UTF8.GetBytes(json);
            Cors(ctx.Response);
            ctx.Response.StatusCode = status;
            ctx.Response.ContentType = "application/json";
            ctx.Response.ContentLength64 = b.Length;
            ctx.Response.OutputStream.Write(b, 0, b.Length);
            ctx.Response.Close();
        }

        static bool ParseApi(string rawPath, out string code, out string[] sub)
        {
            code = null; sub = null;
            string clean = rawPath.Split('?')[0];
            if (clean.EndsWith(".json")) clean = clean.Substring(0, clean.Length - 5);
            List<string> parts = new List<string>();
            foreach (string p in clean.Split('/')) if (p.Length > 0) parts.Add(Uri.UnescapeDataString(p));
            if (parts.Count < 2 || parts[0] != "rooms" || parts.Count > MaxDepth) return false;
            if (!Regex.IsMatch(parts[1], "^[A-Za-z0-9]{1,8}$")) return false;
            code = parts[1].ToUpperInvariant();
            sub = parts.GetRange(2, parts.Count - 2).ToArray();
            return true;
        }

        static object GetAt(object data, string[] sub)
        {
            object node = data;
            foreach (string k in sub)
            {
                Dictionary<string, object> d = node as Dictionary<string, object>;
                if (d == null || !d.ContainsKey(k)) return null;
                node = d[k];
            }
            return node;
        }

        static void SetAt(Room r, string[] sub, object value)
        {
            if (sub.Length == 0)
            {
                r.Data = (value is Dictionary<string, object>) ? value : null;
                return;
            }
            Dictionary<string, object> node = r.Data as Dictionary<string, object>;
            if (node == null) { node = new Dictionary<string, object>(); r.Data = node; }
            for (int i = 0; i < sub.Length - 1; i++)
            {
                object next;
                if (!node.TryGetValue(sub[i], out next) || !(next is Dictionary<string, object>))
                {
                    next = new Dictionary<string, object>();
                    node[sub[i]] = next;
                }
                node = (Dictionary<string, object>)next;
            }
            if (value == null) node.Remove(sub[sub.Length - 1]);
            else node[sub[sub.Length - 1]] = value;
        }

        static byte[] SsePayload(string[] sub, object value)
        {
            string path = sub.Length == 0 ? "/" : "/" + string.Join("/", sub);
            Dictionary<string, object> m = new Dictionary<string, object>();
            m["path"] = path;
            m["data"] = value;
            return Encoding.UTF8.GetBytes("event: put\ndata: " + Json.Serialize(m) + "\n\n");
        }

        static void Handle(HttpListenerContext ctx)
        {
            try { HandleInner(ctx); }
            catch (Exception) { try { ctx.Response.Abort(); } catch (Exception) { } }
        }

        static void HandleInner(HttpListenerContext ctx)
        {
            string method = ctx.Request.HttpMethod;
            string path = ctx.Request.Url.AbsolutePath;

            if (method == "OPTIONS")
            {
                Cors(ctx.Response);
                ctx.Response.Headers["Access-Control-Max-Age"] = "86400";
                ctx.Response.StatusCode = 204;
                ctx.Response.Close();
                return;
            }

            string code; string[] sub;
            if (!ParseApi(path, out code, out sub))
            {
                if (method == "GET") { ServeStatic(ctx, path); return; }
                ctx.Response.StatusCode = 405; ctx.Response.Close(); return;
            }

            Room r = GetRoom(code);
            if (r == null) { SendJson(ctx, "{\"error\":\"room limit\"}", 503); return; }

            if (method == "GET")
            {
                string accept = ctx.Request.Headers["Accept"];
                if (accept != null && accept.IndexOf("text/event-stream") >= 0) { Sse(ctx, r); return; }
                object val;
                lock (gate) { val = GetAt(r.Data, sub); }
                SendJson(ctx, Json.Serialize(val), 200);
                return;
            }
            if (method == "PUT")
            {
                long len = ctx.Request.ContentLength64;
                if (len > MaxBody) { SendJson(ctx, "{\"error\":\"too large\"}", 413); return; }
                string body = new StreamReader(ctx.Request.InputStream, Encoding.UTF8).ReadToEnd();
                object value;
                try { value = body.Length == 0 ? null : Json.Parse(body); }
                catch (Exception) { SendJson(ctx, "{\"error\":\"bad json\"}", 400); return; }
                List<BlockingCollection<byte[]>> clients;
                lock (gate)
                {
                    SetAt(r, sub, value);
                    clients = new List<BlockingCollection<byte[]>>(r.Clients);
                }
                byte[] payload = SsePayload(sub, value);
                foreach (BlockingCollection<byte[]> q in clients) q.Add(payload);
                SendJson(ctx, Json.Serialize(value), 200);
                return;
            }
            ctx.Response.StatusCode = 405; ctx.Response.Close();
        }

        static void Sse(HttpListenerContext ctx, Room r)
        {
            Cors(ctx.Response);
            ctx.Response.ContentType = "text/event-stream";
            ctx.Response.SendChunked = true;
            Stream os = ctx.Response.OutputStream;
            BlockingCollection<byte[]> q = new BlockingCollection<byte[]>();
            lock (gate)
            {
                q.Add(SsePayload(new string[0], r.Data));
                r.Clients.Add(q);
            }
            byte[] ka = Encoding.UTF8.GetBytes(":ka\n\n");
            try
            {
                while (true)
                {
                    byte[] item;
                    if (!q.TryTake(out item, KeepAliveMs)) item = ka;
                    if (item == null) break;           // room purged
                    os.Write(item, 0, item.Length);
                    os.Flush();
                }
            }
            catch (Exception) { }
            finally
            {
                lock (gate) { r.Clients.Remove(q); }
                try { ctx.Response.Close(); } catch (Exception) { }
            }
        }

        static void ServeStatic(HttpListenerContext ctx, string path)
        {
            string p = path;
            if (p == "/" || p.Length == 0) p = "/long-term-game-live.html";
            string rel = Uri.UnescapeDataString(p).TrimStart('/').Replace('/', Path.DirectorySeparatorChar);
            string full = Path.GetFullPath(Path.Combine(staticDir, rel));
            if (!full.StartsWith(staticDir)) { ctx.Response.StatusCode = 403; ctx.Response.Close(); return; }
            if (!File.Exists(full) && p == "/long-term-game-live.html")
                full = Path.Combine(staticDir, "index.html");
            if (!File.Exists(full))
            {
                ctx.Response.StatusCode = p.IndexOf("favicon") >= 0 ? 204 : 404;
                ctx.Response.Close();
                return;
            }
            byte[] data = File.ReadAllBytes(full);
            string ext = Path.GetExtension(full).ToLowerInvariant();
            string ctype = ext == ".html" ? "text/html; charset=utf-8"
                : ext == ".js" ? "text/javascript" : ext == ".css" ? "text/css"
                : ext == ".png" ? "image/png" : ext == ".svg" ? "image/svg+xml"
                : ext == ".json" ? "application/json" : "application/octet-stream";
            if (ext == ".html")
            {
                // Same on-the-fly switch as the Node/Python editions.
                string html = Encoding.UTF8.GetString(data);
                html = Regex.Replace(html,
                    "(const LIVE_BACKEND\\s*=\\s*\\{\\s*databaseURL:\\s*)\"[^\"]*\"",
                    "$1\"auto\"");
                data = Encoding.UTF8.GetBytes(html);
            }
            Cors(ctx.Response);
            ctx.Response.ContentType = ctype;
            ctx.Response.ContentLength64 = data.Length;
            ctx.Response.OutputStream.Write(data, 0, data.Length);
            ctx.Response.Close();
        }

        public static void Main(string[] args)
        {
            int port = 8877;
            string dir = AppDomain.CurrentDomain.BaseDirectory;
            string envPort = Environment.GetEnvironmentVariable("PORT");
            string envDir = Environment.GetEnvironmentVariable("STATIC_DIR");
            if (args.Length > 0) port = int.Parse(args[0]);
            else if (envPort != null) port = int.Parse(envPort);
            if (args.Length > 1) dir = args[1];
            else if (envDir != null) dir = envDir;
            Run(port, dir);
        }
    }
}
