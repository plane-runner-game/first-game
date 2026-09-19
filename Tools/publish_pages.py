"""publish_pages.py - copy Builds/WebGL into the gh-pages worktree, patch index.html for phones, commit and force-push.
Run after the WebGL build has finished. Usage: python publish_pages.py
"""
import os, shutil, subprocess, re, sys, time
PROJ = r"C:\Users\nbo6y\first-game"
BUILD = os.path.join(PROJ, "Builds", "WebGL")
WT = r"C:\Users\nbo6y\first-game-pages"      # the gh-pages worktree
def git(*a, cwd=PROJ, check=True):
    r = subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and r.returncode != 0: raise SystemExit("git " + " ".join(a) + " failed:\n" + r.stdout + r.stderr)
    return r.stdout.strip()

# 0. the build must be complete
for f in ["index.html", "Build/WebGL.loader.js", "Build/WebGL.framework.js", "Build/WebGL.wasm", "Build/WebGL.data", "TemplateData/style.css"]:
    if not os.path.exists(os.path.join(BUILD, f)): raise SystemExit("build incomplete: missing " + f)
sizes = {f: os.path.getsize(os.path.join(BUILD, "Build", f)) for f in os.listdir(os.path.join(BUILD, "Build"))}
print("build files:", {k: "%.1f MB" % (v / 1e6) for k, v in sizes.items()})

# 1. the worktree on gh-pages (a fresh orphan each publish: the branch holds one snapshot, no history of 50 MB blobs)
if os.path.exists(WT): git("worktree", "remove", "--force", WT, check=False); shutil.rmtree(WT, ignore_errors=True)
git("worktree", "prune")
git("branch", "-D", "gh-pages", check=False)   # the previous publish's local branch: each publish is a fresh orphan
git("worktree", "add", "--detach", WT, "HEAD")
git("checkout", "--orphan", "gh-pages", cwd=WT)
git("rm", "-rfq", ".", cwd=WT)
for name in os.listdir(WT):   # anything the checkout left behind (ignored files)
    if name == ".git": continue
    p = os.path.join(WT, name); shutil.rmtree(p, ignore_errors=True) if os.path.isdir(p) else os.remove(p)

# 2. the build, plus .nojekyll and a .gitattributes that keeps LFS OUT of this branch (Pages serves raw files)
shutil.copytree(BUILD, WT, dirs_exist_ok=True)
open(os.path.join(WT, ".nojekyll"), "w").close()
open(os.path.join(WT, ".gitattributes"), "w", newline="\n").write("* -filter -diff -merge -text\n")

# 3. index.html for the phone: full-viewport canvas, no browser zoom, home-screen full screen, fullscreen on the first touch (Android);
#    on a desktop a 450 x 800 portrait window instead of the template's 960 x 600
ix = os.path.join(WT, "index.html"); h = open(ix, encoding="utf-8").read()
h = h.replace('<canvas id="unity-canvas" width="960" height="600" tabindex="-1"></canvas>', '<canvas id="unity-canvas" width="450" height="800" tabindex="-1"></canvas>')
h = h.replace('<title>Unity Web Player | Sky Squad</title>', '<title>Sky Squad</title>')
h = h.replace('<link rel="shortcut icon" href="TemplateData/favicon.ico">',
              '<link rel="shortcut icon" href="TemplateData/favicon.ico">\n'
              '    <meta name="viewport" content="width=device-width, height=device-height, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">\n'
              '    <meta name="mobile-web-app-capable" content="yes">\n'
              '    <meta name="apple-mobile-web-app-capable" content="yes">\n'
              '    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">\n'
              '    <meta name="apple-mobile-web-app-title" content="Sky Squad">\n'
              '    <meta name="theme-color" content="#3b9be8">\n'
              '    <style>\n'
              '      html, body { margin: 0; padding: 0; background: #3b9be8; overscroll-behavior: none; touch-action: none; -webkit-user-select: none; user-select: none; }\n'
              '      .unity-mobile, #unity-container.unity-mobile, #unity-container.unity-mobile #unity-fullscreen-container { position: fixed; inset: 0; width: 100vw; height: 100vh; height: 100dvh; }\n'
              '      #unity-container.unity-mobile #unity-canvas { width: 100%; height: 100%; }\n'
              '    </style>')
# the desktop window: the template sets the canvas size from the config; keep it portrait
h = h.replace('fullscreenContainer.style.width = "960px";', 'fullscreenContainer.style.width = "450px";').replace('fullscreenContainer.style.height = "600px";', 'fullscreenContainer.style.height = "800px";')
assert 'fullscreenContainer.style.width = "450px"' in h
# a DPR-3 phone had Unity rendering ~3x the pixels in each axis (full-screen canvas x devicePixelRatio), which is what made
# it crawl on mobile; Unity ships this switch commented out in its own template (2026-09-19)
h = h.replace('        // config.devicePixelRatio = 1;',
              '        config.devicePixelRatio = Math.min(window.devicePixelRatio || 1, 1.5);')
assert 'config.devicePixelRatio = Math.min(' in h, 'devicePixelRatio cap not applied'
# fullscreen on the first touch (Android Chrome; iOS ignores it and uses the home-screen full screen instead)
h = h.replace('script.src = loaderUrl;', 'script.src = loaderUrl;\n      var unityInstanceRef = null;\n      document.addEventListener("touchend", function () { if (unityInstanceRef && /Android/i.test(navigator.userAgent)) { try { unityInstanceRef.SetFullscreen(1); } catch (e) {} } }, { once: true });')
h = h.replace('}).then((unityInstance) => {', '}).then((unityInstance) => {\n          unityInstanceRef = unityInstance;')
open(ix, "w", encoding="utf-8", newline="\n").write(h)
for must in ['width="450" height="800"', 'apple-mobile-web-app-capable', 'unityInstanceRef = unityInstance', '100dvh']: assert must in h, must
print("index.html patched")

# 4. commit + force-push
git("add", "-A", cwd=WT)
stamp = time.strftime("%Y-%m-%d %H:%M")
git("-c", "user.name=nbo6y", "-c", "user.email=nabeel.saleh2007@gmail.com", "commit", "-q", "-m", "Sky Squad web build " + stamp + " (dev-02 " + git("rev-parse", "--short", "HEAD") + ")", cwd=WT)
print(git("push", "--force", "origin", "gh-pages", cwd=WT)[-300:])
print("pushed gh-pages")
