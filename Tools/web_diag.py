"""web_diag.py - like web_check, but hooks WebGL2 before the Unity loader runs: after every draw call it checks gl.getError() and, on the
first error per program, prints that program's sampler uniforms and the head of its fragment shader - i.e. WHICH shader is failing.
Usage: python web_diag.py <url> <out.png> [seconds]"""
import subprocess, time, json, sys, base64, urllib.request, os, shutil
import websocket

url, out = sys.argv[1], sys.argv[2]; budget = int(sys.argv[3]) if len(sys.argv) > 3 else 200
edge = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
prof = os.path.join(os.path.dirname(out), "edgeprof3"); shutil.rmtree(prof, ignore_errors=True)
HOOK = r"""
(function () {
  const P = WebGL2RenderingContext.prototype;
  const srcOf = new Map(), shadersOf = new Map(), reported = new Set();
  const oShaderSource = P.shaderSource, oAttach = P.attachShader;
  P.shaderSource = function (sh, src) { srcOf.set(sh, src); return oShaderSource.call(this, sh, src); };
  P.attachShader = function (prog, sh) { if (!shadersOf.has(prog)) shadersOf.set(prog, []); shadersOf.get(prog).push(sh); return oAttach.call(this, prog, sh); };
  function report(gl, where) {
    const err = gl.getError(); if (!err) return;
    const prog = gl.getParameter(gl.CURRENT_PROGRAM); if (reported.has(prog)) return; reported.add(prog);
    const n = gl.getParameter(gl.ACTIVE_UNIFORMS) ? 0 : 0;
    const samplers = [];
    const count = gl.getProgramParameter(prog, gl.ACTIVE_UNIFORMS);
    for (let i = 0; i < count; i++) { const u = gl.getActiveUniform(prog, i); if (u && (u.type === gl.SAMPLER_2D || u.type === gl.SAMPLER_2D_SHADOW || u.type === gl.SAMPLER_CUBE || u.type === gl.SAMPLER_2D_ARRAY || u.type === gl.SAMPLER_2D_ARRAY_SHADOW || u.type === gl.SAMPLER_3D)) {
      const t = u.type === gl.SAMPLER_2D_SHADOW ? "2DShadow" : u.type === gl.SAMPLER_2D_ARRAY_SHADOW ? "2DArrayShadow" : u.type === gl.SAMPLER_CUBE ? "Cube" : u.type === gl.SAMPLER_2D_ARRAY ? "2DArray" : u.type === gl.SAMPLER_3D ? "3D" : "2D";
      // which texture unit / what is bound there
      const loc = gl.getUniformLocation(prog, u.name); let unit = -1; try { unit = gl.getUniform(prog, loc); } catch (e) {}
      samplers.push(u.name + ":" + t + "@" + unit); } }
    let head = "";
    for (const sh of (shadersOf.get(prog) || [])) { const s = srcOf.get(sh) || ""; if (gl.getShaderParameter(sh, gl.SHADER_TYPE) === gl.FRAGMENT_SHADER) head = s.slice(0, 160).replace(/\n/g, " "); }
    const props = [];
    for (let i = 0; i < count && props.length < 14; i++) { const u = gl.getActiveUniform(prog, i); if (u && !samplers.some(s => s.startsWith(u.name + ":"))) props.push(u.name.replace(/^_/, "")); }
    console.log("GLERR " + where + " err=" + err + " samplers=[" + samplers.join(", ") + "] uniforms=[" + props.join(", ") + "] frag=" + head);
  }
  for (const name of ["drawElements", "drawArrays", "drawElementsInstanced", "drawArraysInstanced", "drawRangeElements"]) {
    const o = P[name]; P[name] = function () { const r = o.apply(this, arguments); report(this, name); return r; };
  }
  console.log("GL hook installed");
})();
"""
proc = subprocess.Popen([edge, "--headless=new", "--remote-debugging-port=9334", "--user-data-dir=" + prof, "--window-size=450,800", "--hide-scrollbars",
                         "--use-angle=d3d11", "--enable-gpu-rasterization", "--ignore-gpu-blocklist", "--no-first-run", "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    for _ in range(40):
        try: targets = json.load(urllib.request.urlopen("http://127.0.0.1:9334/json")); break
        except Exception: time.sleep(0.5)
    page = next(t for t in targets if t.get("type") == "page")
    ws = websocket.create_connection(page["webSocketDebuggerUrl"], suppress_origin=True); ws.settimeout(5)
    msg_id = 0; console = []
    def handle(m):
        if m.get("method") == "Runtime.consoleAPICalled": console.append(" ".join(str(a.get("value", a.get("description", ""))) for a in m["params"]["args"])[:900])
        elif m.get("method") == "Runtime.exceptionThrown": console.append("EXCEPTION " + m["params"]["exceptionDetails"].get("text", "")[:300])
    def send(method, params=None):
        global msg_id
        msg_id += 1; ws.send(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
        while True:
            m = json.loads(ws.recv()); handle(m)
            if m.get("id") == msg_id: return m.get("result", {})
    def pump(seconds):
        end = time.time() + seconds
        while time.time() < end:
            try: handle(json.loads(ws.recv()))
            except websocket.WebSocketTimeoutException: pass
    def js(expr): return send("Runtime.evaluate", {"expression": expr, "returnByValue": True}).get("result", {}).get("value")
    send("Page.enable"); send("Runtime.enable")
    send("Page.addScriptToEvaluateOnNewDocument", {"source": HOOK})
    send("Page.navigate", {"url": url})
    t0 = time.time(); booted = False
    while time.time() - t0 < budget:
        pump(5)
        if js("typeof unityInstanceRef!=='undefined' && unityInstanceRef!==null"): booted = True; pump(10); break
    shot = send("Page.captureScreenshot", {"format": "png"}); open(out, "wb").write(base64.b64decode(shot["data"]))
    print("booted:", booted, "| screenshot", os.path.getsize(out), "bytes")
    gl = [c for c in console if c.startswith("GLERR") or c.startswith("GL hook")]
    print("=== GL errors by program (%d) ===" % (len(gl) - 1))
    for c in gl: print("  ", c)
    other = [c for c in console if "AudioContext" not in c and not c.startswith("GLERR") and not c.startswith("GL hook")]
    print("=== other console (%d, last 12) ===" % len(other))
    for c in other[-12:]: print("  ", c[:240])
finally:
    proc.kill()
