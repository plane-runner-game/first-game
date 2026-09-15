"""Tiny client for the MCP-for-Unity HTTP bridge (http://127.0.0.1:8080/mcp), for driving the open editor
from a shell when no MCP-capable client is attached: compile, read the console, run menu items.

  python Tools/unity_mcp.py refresh                 # asset refresh + compile request, waits for ready
  python Tools/unity_mcp.py console [error|all] [n] # console entries (default: errors, 10)
  python Tools/unity_mcp.py menu "Sky Squad/2. Build Everything"
  python Tools/unity_mcp.py stop                    # exit play mode
  python Tools/unity_mcp.py call <tool> '<json args>'
"""
import io, json, sys, urllib.request

URL = "http://127.0.0.1:8080/mcp"


class Client:
    def __init__(self):
        self.session = None
        self.n = 0
        r = self.rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "unity_mcp.py", "version": "1"}})
        self.notify("notifications/initialized")

    def _post(self, body):
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(URL, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json, text/event-stream")
        if self.session: req.add_header("Mcp-Session-Id", self.session)
        resp = urllib.request.urlopen(req, timeout=600)
        sid = resp.headers.get("Mcp-Session-Id")
        if sid: self.session = sid
        raw = resp.read().decode("utf-8", "replace")
        ctype = resp.headers.get("Content-Type", "")
        if "text/event-stream" in ctype:
            msgs = []
            for line in raw.splitlines():
                if line.startswith("data:"):
                    try: msgs.append(json.loads(line[5:].strip()))
                    except Exception: pass
            return msgs[-1] if msgs else None
        return json.loads(raw) if raw.strip() else None

    def rpc(self, method, params):
        self.n += 1
        return self._post({"jsonrpc": "2.0", "id": self.n, "method": method, "params": params})

    def notify(self, method, params=None):
        body = {"jsonrpc": "2.0", "method": method}
        if params: body["params"] = params
        try: self._post(body)
        except Exception: pass

    def call(self, tool, args):
        r = self.rpc("tools/call", {"name": tool, "arguments": args})
        if r is None: return None
        if "error" in r: return {"error": r["error"]}
        res = r.get("result", {})
        out = []
        for c in res.get("content", []):
            if c.get("type") == "text":
                t = c["text"]
                try: out.append(json.loads(t))
                except Exception: out.append(t)
        return out[0] if len(out) == 1 else out


def main():
    a = sys.argv[1:]
    if not a: print(__doc__); return
    c = Client()
    cmd = a[0]
    if cmd == "refresh":
        print(json.dumps(c.call("refresh_unity", {"compile": "request", "mode": "force", "scope": "all", "wait_for_ready": True}), indent=1)[:1500])
    elif cmd == "console":
        types = [a[1]] if len(a) > 1 else ["error"]
        n = int(a[2]) if len(a) > 2 else 10
        print(json.dumps(c.call("read_console", {"action": "get", "types": types, "count": str(n), "format": "plain"}), indent=1)[:4000])
    elif cmd == "clear":
        print(c.call("read_console", {"action": "clear"}))
    elif cmd == "menu":
        print(json.dumps(c.call("execute_menu_item", {"menu_path": a[1]}))[:800])
    elif cmd == "stop":
        print(c.call("manage_editor", {"action": "stop"}))
    elif cmd == "call":
        print(json.dumps(c.call(a[1], json.loads(a[2]) if len(a) > 2 else {}), indent=1)[:4000])
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
