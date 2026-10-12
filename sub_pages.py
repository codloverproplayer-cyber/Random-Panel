# sub_pages.py
# Public pages that people open from a subscription link (/info/{uuid} and /p/{key}).
#
# Design goals:
#   * Aurora look (animated sky, glowing ring, glass-like cards) using only CSS + inline SVG
#   * No framework and no render-blocking external file: one inline stylesheet, one tiny inline script
#   * Animations touch only transform / opacity (cheap on phones) and stop for
#     users who prefer reduced motion
#   * Everything user-supplied is HTML-escaped here; the page never injects raw strings
#
# This module deliberately imports nothing from main.py.

import re
from html import escape as _esc


def esc(value) -> str:
    return _esc(str(value if value is not None else ""), quote=True)


# --------------------------------------------------------------------------------------
# icons (24x24, stroke)
# --------------------------------------------------------------------------------------

_ICON_PATHS = {
    "copy": '<rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
    "qr": '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><path d="M14 14h3v3h-3zM20 14v.01M14 20h.01M17 20h4v-3"/>',
    "link": '<path d="M10 13a5 5 0 0 0 7.5.5l3-3a5 5 0 0 0-7-7l-1.7 1.7"/><path d="M14 11a5 5 0 0 0-7.5-.5l-3 3a5 5 0 0 0 7 7l1.7-1.7"/>',
    "chart": '<path d="M3 3v18h18"/><path d="M7 15l4-5 3 3 5-7"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "users": '<path d="M17 21v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2"/><circle cx="10" cy="7" r="4"/><path d="M21 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8"/>',
    "db": '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/>',
    "bolt": '<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>',
    "shield": '<path d="M12 2l8 3v6c0 5-3.4 8.5-8 11-4.6-2.5-8-6-8-11V5z"/>',
    "wave": '<path d="M3 15c3-6 6-6 9 0s6 6 9 0"/><path d="M3 9c3-6 6-6 9 0s6 6 9 0" opacity=".55"/>',
    "moon": '<path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z"/>',
    "download": '<path d="M12 3v12M7 10l5 5 5-5M4 21h16"/>',
    "check": '<path d="M5 12l5 5 9-10"/>',
    "open": '<path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
    "lock": '<rect x="4" y="10" width="16" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>',
    "x": '<path d="M6 6l12 12M18 6L6 18"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
}


def ltr(value) -> str:
    """Numbers with units ("21.40 GB") must stay left-to-right inside Persian text."""
    return f'<bdi dir="ltr">{esc(value)}</bdi>'


def icon(name: str, size: int = 18) -> str:
    return (
        f'<svg class="ic" viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" '
        f'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
        f'aria-hidden="true">{_ICON_PATHS[name]}</svg>'
    )


# --------------------------------------------------------------------------------------
# shared CSS
# --------------------------------------------------------------------------------------

BASE_CSS = r"""
:root{--bg:#04101a;--bg2:#08202f;--sf:rgba(13,34,48,.72);--sf2:rgba(255,255,255,.045);--bd:rgba(150,240,225,.13);
--tx:#eaf6f8;--mu:rgba(214,238,244,.6);--teal:#2dd4bf;--green:#4ade80;--violet:#a78bfa;--pink:#e879f9;--amber:#fbbf24;--red:#fb7185;
--shadow:0 20px 50px -24px rgba(0,0,0,.7);--star:.4;color-scheme:dark}
:root[data-theme=light]{--bg:#e8f7f4;--bg2:#f7fffd;--sf:rgba(255,255,255,.82);--sf2:rgba(8,70,80,.05);--bd:rgba(8,90,95,.15);
--tx:#0a2430;--mu:rgba(10,36,48,.62);--teal:#0d9488;--green:#16a34a;--violet:#7c3aed;--pink:#c026d3;--amber:#b45309;--red:#e11d48;
--shadow:0 16px 40px -22px rgba(8,70,80,.3);--star:0;color-scheme:light}
*{box-sizing:border-box;margin:0;padding:0}
html{background:var(--bg);-webkit-text-size-adjust:100%}
body{font-family:Vazirmatn,"Segoe UI",Tahoma,system-ui,-apple-system,sans-serif;color:var(--tx);min-height:100vh;line-height:1.65;overflow-x:hidden;-webkit-font-smoothing:antialiased}
button{font:inherit;color:inherit;cursor:pointer;border:0;background:none;-webkit-tap-highlight-color:transparent}
a{color:inherit;text-decoration:none;-webkit-tap-highlight-color:transparent}
.ic{flex:none;display:block}
.ltr{direction:ltr;unicode-bidi:plaintext;text-align:left}
.mono{font-family:ui-monospace,SFMono-Regular,Consolas,Menlo,monospace}

/* animated aurora sky: three soft gradients drifting (transform only) + faint stars */
.sky{position:fixed;inset:0;z-index:-1;overflow:hidden;pointer-events:none;background:linear-gradient(180deg,var(--bg2),var(--bg) 72%)}
.sky i{position:absolute;border-radius:50%;opacity:.6;will-change:transform}
.sky .a{width:120vmax;height:70vmax;left:-38vmax;top:-48vmax;background:radial-gradient(closest-side,rgba(45,212,191,.42),transparent);animation:d1 30s ease-in-out infinite alternate}
.sky .b{width:100vmax;height:60vmax;right:-42vmax;top:-22vmax;background:radial-gradient(closest-side,rgba(139,92,246,.36),transparent);animation:d2 38s ease-in-out infinite alternate}
.sky .c{width:110vmax;height:50vmax;left:-12vmax;bottom:-36vmax;background:radial-gradient(closest-side,rgba(74,222,128,.26),transparent);animation:d3 44s ease-in-out infinite alternate}
.sky::after{content:"";position:absolute;inset:0;opacity:var(--star);
background-image:radial-gradient(1.2px 1.2px at 8% 14%,#fff,transparent),radial-gradient(1px 1px at 22% 36%,#fff,transparent),radial-gradient(1.4px 1.4px at 37% 9%,#fff,transparent),radial-gradient(1px 1px at 52% 27%,#fff,transparent),radial-gradient(1.2px 1.2px at 66% 12%,#fff,transparent),radial-gradient(1px 1px at 81% 31%,#fff,transparent),radial-gradient(1.3px 1.3px at 93% 8%,#fff,transparent),radial-gradient(1px 1px at 14% 58%,#fff,transparent),radial-gradient(1px 1px at 71% 52%,#fff,transparent);
-webkit-mask-image:linear-gradient(#000,transparent 65%);mask-image:linear-gradient(#000,transparent 65%)}
@keyframes d1{to{transform:translate3d(9vmax,7vmax,0) rotate(10deg)}}
@keyframes d2{to{transform:translate3d(-10vmax,9vmax,0) rotate(-12deg)}}
@keyframes d3{to{transform:translate3d(8vmax,-6vmax,0) rotate(8deg)}}

.wrap{max-width:760px;margin:0 auto;padding:18px 14px 40px;display:grid;grid-template-columns:minmax(0,1fr);gap:14px}
.bar{display:flex;justify-content:space-between;align-items:center}
.ibtn{width:38px;height:38px;border-radius:12px;display:grid;place-items:center;background:var(--sf2);border:1px solid var(--bd);transition:transform .15s,border-color .15s,background .15s}
.ibtn:hover{border-color:var(--teal);background:rgba(45,212,191,.12)}
.ibtn:active{transform:scale(.93)}
.ibtn.done{color:var(--green);border-color:var(--green)}

.card{background:var(--sf);border:1px solid var(--bd);border-radius:22px;padding:18px;box-shadow:var(--shadow);position:relative;overflow:hidden;contain:layout paint}
.card h2{font-size:14px;font-weight:800;display:flex;align-items:center;gap:8px;margin-bottom:14px}
.card h2 .ic{color:var(--teal)}
.muted{color:var(--mu)}
.rise{opacity:0;transform:translateY(14px);animation:rise .6s cubic-bezier(.2,.7,.2,1) forwards;animation-delay:calc(var(--d,0)*70ms)}
@keyframes rise{to{opacity:1;transform:none}}

/* hero */
.hero{display:flex;gap:16px;align-items:center;flex-wrap:wrap}
.hero::before{content:"";position:absolute;inset:0 0 auto 0;height:3px;background:linear-gradient(90deg,#0d9488,#2dd4bf,#4ade80,#a78bfa,#e879f9,#0d9488);background-size:220% 100%;animation:slide 9s linear infinite}
@keyframes slide{to{background-position:220% 0}}
.orb{width:58px;height:58px;border-radius:18px;position:relative;display:grid;place-items:center;color:#fff;flex:none;overflow:hidden;background:#0b3b44}
.orb::before{content:"";position:absolute;inset:-60%;background:conic-gradient(from 0deg,#2dd4bf,#4ade80,#a78bfa,#e879f9,#2dd4bf);animation:spin 9s linear infinite;opacity:.9}
.orb::after{content:"";position:absolute;inset:2px;border-radius:16px;background:linear-gradient(160deg,#0a3a44,#0b2535)}
.orb .ic{position:relative;z-index:1}
@keyframes spin{to{transform:rotate(360deg)}}
.hero-main{flex:1;min-width:0}
.hero h1{font-size:clamp(18px,4.6vw,26px);font-weight:900;letter-spacing:-.01em;line-height:1.35;word-break:break-word}
.uuid{font-size:11px;color:var(--mu);margin-top:2px;word-break:break-all}
.chips{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin-top:10px}
.chip{display:inline-flex;align-items:center;gap:5px;font-size:11px;font-weight:700;padding:3px 10px;border-radius:99px;background:var(--sf2);border:1px solid var(--bd);color:var(--mu)}
.chip.t{color:var(--teal)}.chip.v{color:var(--violet)}.chip.g{color:var(--green)}
.pill{display:inline-flex;align-items:center;gap:8px;font-size:12px;font-weight:800;padding:3px 12px;border-radius:99px;border:1px solid;flex:none}
.pill i{width:8px;height:8px;border-radius:50%;background:currentColor;position:relative}
.pill i::after{content:"";position:absolute;inset:0;border-radius:50%;background:currentColor;animation:ping 1.8s ease-out infinite}
@keyframes ping{from{transform:scale(1);opacity:.7}to{transform:scale(3);opacity:0}}
.pill.ok{color:var(--green);border-color:rgba(74,222,128,.35);background:rgba(74,222,128,.1)}
.pill.bad{color:var(--red);border-color:rgba(251,113,133,.35);background:rgba(251,113,133,.1)}
.pill.bad i::after{animation:none}

/* usage */
.usage{display:grid;grid-template-columns:150px 1fr;gap:18px;align-items:center}
.ring{position:relative;width:150px;height:150px}
.ring svg{transform:rotate(-90deg);width:100%;height:100%}
.ring .trk{stroke:var(--sf2);stroke-width:11}
.ring .val{stroke:url(#rg);stroke-width:11;stroke-linecap:round;stroke-dasharray:339.29;stroke-dashoffset:var(--off);animation:ring 1.4s cubic-bezier(.2,.7,.2,1) both .25s}
.ring.inf .val{stroke-dashoffset:0;opacity:.35;animation:none}
@keyframes ring{from{stroke-dashoffset:339.29}to{stroke-dashoffset:var(--off)}}
.ring .mid{position:absolute;inset:0;display:grid;place-content:center;text-align:center}
.ring .pct{font-size:26px;font-weight:900;line-height:1}
.ring .cap{font-size:11px;color:var(--mu);margin-top:5px}
.big{font-size:clamp(20px,5vw,28px);font-weight:900;line-height:1.2}
.big small{font-size:13px;font-weight:600;color:var(--mu)}
.trend{margin-top:12px;border-radius:14px;background:var(--sf2);border:1px solid var(--bd);padding:8px 10px 4px}
.trend p{font-size:10.5px;color:var(--mu)}
.trend svg{width:100%;height:46px;display:block}
.tbar{margin-top:14px}
.tbar-row{display:flex;justify-content:space-between;font-size:11.5px;color:var(--mu);margin-bottom:6px;gap:8px;flex-wrap:wrap}
.tbar-row b{color:var(--tx)}
.track{height:8px;border-radius:99px;background:var(--sf2);overflow:hidden;border:1px solid var(--bd)}
.track span{display:block;height:100%;width:var(--w);border-radius:99px;background:linear-gradient(90deg,#14b8a6,#4ade80,#a78bfa);transform-origin:right;animation:grow 1.2s cubic-bezier(.2,.7,.2,1) both .35s}
.track.warn span{background:linear-gradient(90deg,#fbbf24,#fb7185)}
@keyframes grow{from{transform:scaleX(0)}to{transform:none}}

/* stat tiles */
.tiles{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}
.tile{padding:14px}
.tile .tic{width:34px;height:34px;border-radius:11px;display:grid;place-items:center;margin-bottom:10px;background:var(--sf2);border:1px solid var(--bd)}
.tile .k{font-size:11px;color:var(--mu)}
.tile .v{font-size:15px;font-weight:900;margin-top:2px;word-break:break-word}
.tile.t1 .tic{color:var(--teal)}.tile.t2 .tic{color:var(--amber)}.tile.t3 .tic{color:var(--green)}.tile.t4 .tic{color:var(--violet)}

/* quick connect */
.qc{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.btn{display:flex;align-items:center;justify-content:center;gap:7px;padding:12px 10px;border-radius:14px;font-size:12.5px;font-weight:800;border:1px solid var(--bd);background:var(--sf2);transition:transform .15s,filter .15s,border-color .15s;text-align:center}
.btn:hover{border-color:var(--teal)}
.btn:active{transform:scale(.97)}
.btn.p{border:0;color:#fff;background:linear-gradient(135deg,#0d9488,#6d28d9)}
.btn.p:hover{filter:brightness(1.12)}

/* config list */
.cfgs{list-style:none;display:grid;grid-template-columns:minmax(0,1fr);gap:8px}
.cfg{display:flex;align-items:center;gap:12px;min-width:0;padding:10px 12px;border-radius:16px;background:var(--sf2);border:1px solid var(--bd)}
.idx{width:30px;height:30px;border-radius:10px;display:grid;place-items:center;font-size:12px;font-weight:900;color:#fff;background:linear-gradient(135deg,#0d9488,#7c3aed);flex:none}
.cinfo{flex:1;min-width:0}
.cname{display:block;font-size:13.5px;font-weight:800;overflow-wrap:anywhere;line-height:1.45}
.cmeta .mono{overflow-wrap:anywhere}
.cmeta{display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin-top:2px;font-size:11px;color:var(--mu)}
.cfg .ibtn{width:34px;height:34px;border-radius:10px}

.linkrow{display:flex;align-items:center;gap:10px;padding:12px;border-radius:16px;background:var(--sf2);border:1px solid var(--bd)}
.linkrow .txt{flex:1;min-width:0;font-size:11.5px;color:var(--teal);word-break:break-all;line-height:1.7}

.grid2{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}
.kv{padding:12px 14px;border-radius:16px;background:var(--sf2);border:1px solid var(--bd)}
.kv .k{font-size:11px;color:var(--mu)}
.kv .v{font-size:13px;font-weight:800;margin-top:3px;word-break:break-word}

.apps{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.app{display:flex;align-items:center;gap:10px;padding:12px;border-radius:16px;background:var(--sf2);border:1px solid var(--bd);transition:border-color .15s}
.app:hover{border-color:var(--violet)}
.app b{display:block;font-size:12.5px}
.app span{font-size:10.5px;color:var(--mu)}
.app .lg{width:36px;height:36px;border-radius:11px;display:grid;place-items:center;font-size:11px;font-weight:900;color:#fff;background:linear-gradient(135deg,#14b8a6,#8b5cf6);flex:none}

/* modal + toast */
.modal{position:fixed;inset:0;z-index:50;display:none;align-items:center;justify-content:center;padding:18px;background:rgba(2,8,14,.72)}
.modal.on{display:flex}
.sheet{width:100%;max-width:340px;background:var(--bg2);border:1px solid var(--bd);border-radius:24px;padding:20px;text-align:center;position:relative;color:var(--tx)}
.sheet .ibtn{position:absolute;top:12px;left:12px}
.sheet h3{font-size:14px;font-weight:800;margin-bottom:4px}
.sheet p{font-size:11px;color:var(--mu);margin-bottom:12px}
#qrBox{background:#fff;border-radius:16px;padding:12px;margin:0 auto;display:grid;place-items:center;min-height:200px;max-width:260px;color:#334;font-size:12px}
#qrBox img{width:100%;height:auto;display:block;image-rendering:pixelated}
.toast{position:fixed;bottom:84px;left:50%;transform:translate(-50%,20px);opacity:0;pointer-events:none;background:var(--bg2);border:1px solid var(--bd);color:var(--tx);padding:9px 16px;border-radius:99px;font-size:12.5px;font-weight:700;z-index:60;transition:.25s}
.toast.on{opacity:1;transform:translate(-50%,0)}
.dock{display:none}

@media (max-width:640px){
 .grid2{grid-template-columns:repeat(2,1fr)}
 .usage{grid-template-columns:1fr;justify-items:center;text-align:center}
 .usage .meta{width:100%;text-align:right}
 .tiles{grid-template-columns:repeat(2,1fr)}
 .qc{grid-template-columns:repeat(2,1fr)}
 .apps{grid-template-columns:1fr}
 .wrap{padding-bottom:96px}
 .dock{position:fixed;bottom:0;inset-inline:0;z-index:40;display:flex;gap:8px;padding:10px 12px calc(10px + env(safe-area-inset-bottom));background:linear-gradient(transparent,var(--bg) 40%)}
 .dock .btn{flex:1;background:var(--bg2)}
 .dock .btn.p{background:linear-gradient(135deg,#0d9488,#6d28d9)}
 .sky .a,.sky .b,.sky .c{animation-duration:60s}
}
@media (prefers-reduced-motion:reduce){
 .sky i,.hero::before,.orb::before,.pill i::after{animation:none}
 .rise{opacity:1;transform:none;animation:none}
 .ring .val,.track span{animation:none}
}
"""

# tiny script shared by both pages: theme, copy, toast, lazy QR
BASE_JS = r"""
(function(){
var d=document,$=function(s,r){return (r||d).querySelector(s)};
window.px={
  toast:function(m){var t=$('#toast');if(!t)return;t.textContent=m;t.classList.add('on');clearTimeout(t._t);t._t=setTimeout(function(){t.classList.remove('on')},1700)},
  copy:function(text,btn){
    var done=function(){px.toast('کپی شد');if(btn){btn.classList.add('done');setTimeout(function(){btn.classList.remove('done')},1200)}};
    var fb=function(){var a=d.createElement('textarea');a.value=text;a.style.cssText='position:fixed;opacity:0';d.body.appendChild(a);a.select();try{d.execCommand('copy')}catch(e){}d.body.removeChild(a);done()};
    if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(text).then(done,fb)}else fb()
  },
  loadQR:function(cb,fail){
    if(window.qrcode)return cb();
    var urls=['/_qr.js','https://cdn.jsdelivr.net/npm/qrcode-generator@1.4.4/qrcode.min.js'],i=0;
    (function next(){
      if(i>=urls.length)return fail();
      var s=d.createElement('script');s.src=urls[i++];
      s.onload=function(){window.qrcode?cb():next()};s.onerror=next;d.head.appendChild(s)
    })()
  },
  qr:function(text,title){
    var m=$('#qrModal'),box=$('#qrBox');
    $('#qrTitle').textContent=title||'QR Code';
    box.textContent='...';m.classList.add('on');
    px.loadQR(function(){
      try{var q=qrcode(0,'L');q.addData(text);q.make();box.innerHTML=q.createImgTag(5,2)}
      catch(e){box.textContent='QR ساخته نشد (لینک خیلی طولانی است)'}
    },function(){box.textContent='برای ساخت QR اینترنت لازم است'})
  },
  theme:function(){
    var l=d.documentElement.getAttribute('data-theme')==='light';
    if(l)d.documentElement.removeAttribute('data-theme');else d.documentElement.setAttribute('data-theme','light');
    try{localStorage.setItem('px_theme',l?'dark':'light')}catch(e){}
  }
};
d.addEventListener('click',function(e){
  var b=e.target.closest('[data-copy],[data-qr],[data-copy-el],[data-theme-toggle],[data-close]');
  if(!b)return;
  if(b.hasAttribute('data-copy'))px.copy(b.getAttribute('data-copy'),b);
  else if(b.hasAttribute('data-copy-el')){var el=$(b.getAttribute('data-copy-el'));if(el)px.copy(el.textContent.trim(),b)}
  else if(b.hasAttribute('data-qr'))px.qr(b.getAttribute('data-qr'),b.getAttribute('data-title'));
  else if(b.hasAttribute('data-theme-toggle'))px.theme();
  else if(b.hasAttribute('data-close'))$('#qrModal').classList.remove('on');
});
var m=$('#qrModal');if(m)m.addEventListener('click',function(e){if(e.target===m)m.classList.remove('on')});
})();
"""

_HEAD_COMMON = """<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="robots" content="noindex,nofollow">
<meta name="theme-color" content="#04101a">
<script>try{if(localStorage.getItem('px_theme')==='light')document.documentElement.setAttribute('data-theme','light')}catch(e){}</script>
<link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;600;800;900&display=swap" onload="this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;600;800;900&display=swap"></noscript>"""

_SKY = '<div class="sky" aria-hidden="true"><i class="a"></i><i class="b"></i><i class="c"></i></div>'

_QR_MODAL = (
    '<div class="modal" id="qrModal"><div class="sheet">'
    '<button class="ibtn" data-close aria-label="close">' + icon("x", 16) + '</button>'
    '<h3 id="qrTitle">QR Code</h3><p>برای اتصال سریع با گوشی اسکن کنید</p>'
    '<div id="qrBox"></div></div></div><div class="toast" id="toast"></div>'
)


def _shell(title: str, body: str, extra_css: str = "", extra_js: str = "") -> str:
    return (
        '<!DOCTYPE html>\n<html lang="fa" dir="rtl">\n<head>\n'
        + _HEAD_COMMON
        + f"\n<title>{esc(title)}</title>\n<style>{BASE_CSS}{extra_css}</style>\n</head>\n<body>\n"
        + _SKY + "\n" + body + "\n" + _QR_MODAL
        + f"\n<script>{BASE_JS}{extra_js}</script>\n</body>\n</html>"
    )


# --------------------------------------------------------------------------------------
# /info/{uuid}
# --------------------------------------------------------------------------------------

_RING_DEFS = (
    '<defs><linearGradient id="rg" x1="0" y1="0" x2="1" y2="1">'
    '<stop offset="0" stop-color="#2dd4bf"/><stop offset=".55" stop-color="#4ade80"/>'
    '<stop offset="1" stop-color="#a78bfa"/></linearGradient></defs>'
)


def _chip(text: str, cls: str = "", ic: str = "") -> str:
    return f'<span class="chip {cls}">{icon(ic, 12) if ic else ""}{esc(text)}</span>'


def render_info(d: dict) -> str:
    """d keys (all plain, unescaped values):
    name, uid, state ('ok'|'bad'), state_text, protocol, fingerprint, used, limit (None = unlimited),
    remaining, percent (None = unlimited), trend (svg points or ''), time_left, time_pct (None = no expiry),
    time_warn (bool), expiry, connections, ip_limit, conn_limit, speed, configs [dict], sub_url, links dict
    """
    percent = d.get("percent")
    unlimited = percent is None
    off = 339.29 if unlimited else 339.29 - 339.29 * min(max(percent, 0), 100) / 100
    center = (
        '<div class="pct">∞</div><div class="cap">نامحدود</div>'
        if unlimited
        else f'<div class="pct">{ltr(("%g" % percent) + "%")}</div><div class="cap">مصرف‌شده</div>'
    )

    pill = f'<span class="pill {esc(d["state"])}"><i></i>{esc(d["state_text"])}</span>'
    chips = pill + "".join([
        _chip(d["protocol"], "t", "bolt"),
        _chip("TLS · uTLS " + d["fingerprint"], "v", "shield"),
        _chip("TCP + UDP", "g", "globe"),
        _chip(f'{len(d["configs"])} کانفیگ', "", "link"),
    ])

    trend = d.get("trend") or ""
    if trend:
        trend_svg = (
            '<svg viewBox="0 0 300 64" preserveAspectRatio="none" aria-hidden="true"><defs>'
            '<linearGradient id="tf" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2dd4bf" stop-opacity=".4"/>'
            '<stop offset="1" stop-color="#2dd4bf" stop-opacity="0"/></linearGradient></defs>'
            f'<path d="M0,64 L{esc(trend)} L300,64 Z" fill="url(#tf)"/>'
            f'<path d="M{esc(trend)}" fill="none" stroke="#2dd4bf" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke"/></svg>'
        )
    else:
        trend_svg = (
            '<svg viewBox="0 0 300 64" preserveAspectRatio="none" aria-hidden="true">'
            '<path d="M0,52 L300,52" stroke="currentColor" stroke-opacity=".25" stroke-width="2" stroke-dasharray="4 6" fill="none"/></svg>'
        )

    tp = d.get("time_pct")
    if tp is None:
        time_bar = (
            '<div class="tbar"><div class="tbar-row"><span>اعتبار زمانی</span><b>نامحدود</b></div>'
            '<div class="track" style="--w:100%"><span style="opacity:.35"></span></div></div>'
        )
    else:
        warn = " warn" if d.get("time_warn") else ""
        time_bar = (
            f'<div class="tbar"><div class="tbar-row"><span>زمان سپری‌شده</span><b>{esc(d["time_left"])} مانده</b></div>'
            f'<div class="track{warn}" style="--w:{max(2, min(100, tp)):.1f}%"><span></span></div></div>'
        )

    rows = []
    for n, c in enumerate(d["configs"], 1):
        rows.append(
            '<li class="cfg">'
            f'<span class="idx">{n}</span>'
            f'<div class="cinfo"><b class="cname">{esc(c["name"])}</b>'
            f'<div class="cmeta"><span class="chip t">{esc(c["protocol"])}</span>'
            f'<span class="ltr mono">{esc(c["address"])}:{esc(c["port"])}</span></div></div>'
            f'<button class="ibtn" data-copy="{esc(c["url"])}" aria-label="copy">{icon("copy", 16)}</button>'
            f'<button class="ibtn" data-qr="{esc(c["url"])}" data-title="{esc(c["name"])}" aria-label="qr">{icon("qr", 16)}</button>'
            "</li>"
        )

    links = d["links"]
    apps = [
        ("NG", "v2rayNG", "Android", "https://github.com/2dust/v2rayNG/releases/latest"),
        ("N", "v2rayN", "Windows / macOS / Linux", "https://github.com/2dust/v2rayN/releases/latest"),
        ("H", "Hiddify", "Android / iOS / Desktop", "https://github.com/hiddify/hiddify-app/releases/latest"),
    ]
    apps_html = "".join(
        f'<a class="app" href="{esc(u)}" target="_blank" rel="noopener noreferrer"><span class="lg">{esc(lg)}</span>'
        f'<div><b>{esc(n)}</b><span>{esc(s)}</span></div></a>'
        for lg, n, s, u in apps
    )

    def kv(k, v, plain=False):
        return f'<div class="kv"><div class="k">{esc(k)}</div><div class="v">{esc(v) if plain else ltr(v)}</div></div>'

    body = f"""
<main class="wrap">
  <div class="bar rise" style="--d:0"><span class="chip t">{icon("wave", 14)} اشتراک شما</span>
    <button class="ibtn" data-theme-toggle aria-label="theme">{icon("moon", 16)}</button></div>

  <header class="card hero rise" style="--d:1">
    <div class="orb">{icon("wave", 26)}</div>
    <div class="hero-main"><h1>{esc(d["name"])}</h1><div class="uuid ltr mono">{esc(d["uid"])}</div>
      <div class="chips">{chips}</div></div>
  </header>

  <section class="card rise" style="--d:2">
    <h2>{icon("chart", 17)} مصرف سرویس</h2>
    <div class="usage">
      <div class="ring{" inf" if unlimited else ""}" style="--off:{off:.1f}">
        <svg viewBox="0 0 132 132" aria-hidden="true">{_RING_DEFS}<circle class="trk" cx="66" cy="66" r="54" fill="none"/><circle class="val" cx="66" cy="66" r="54" fill="none"/></svg>
        <div class="mid"><div>{center}</div></div>
      </div>
      <div class="meta">
        <div class="big">{ltr(d["used"])} <small>/ {ltr(d["limit"] if d["limit"] else "∞")}</small></div>
        <div class="trend"><p>روند مصرف</p>{trend_svg}</div>
        {time_bar}
      </div>
    </div>
  </section>

  <section class="tiles rise" style="--d:3">
    <div class="card tile t1"><div class="tic">{icon("chart", 17)}</div><div class="k">مصرف فعلی</div><div class="v">{ltr(d["used"])}</div></div>
    <div class="card tile t2"><div class="tic">{icon("db", 17)}</div><div class="k">باقی‌مانده</div><div class="v">{ltr(d["remaining"]) if d["limit"] else esc(d["remaining"])}</div></div>
    <div class="card tile t3"><div class="tic">{icon("users", 17)}</div><div class="k">اتصالات فعال</div><div class="v">{ltr(d["connections"])}</div></div>
    <div class="card tile t4"><div class="tic">{icon("clock", 17)}</div><div class="k">زمان باقی‌مانده</div><div class="v">{esc(d["time_left"])}</div></div>
  </section>

  <section class="card rise" style="--d:4">
    <h2>{icon("bolt", 17)} اتصال سریع</h2>
    <div class="qc">
      <a class="btn p" href="{esc(links["v2rayng"])}">v2rayNG</a>
      <a class="btn p" href="{esc(links["hiddify"])}">Hiddify</a>
      <a class="btn p" href="{esc(links["streisand"])}">Streisand</a>
      <button class="btn" data-copy="{esc(d["sub_url"])}">{icon("copy", 15)} کپی ساب</button>
    </div>
  </section>

  <section class="card rise" style="--d:5">
    <h2>{icon("link", 17)} کانفیگ‌های اشتراک <span class="chip">{len(d["configs"])}</span></h2>
    <ul class="cfgs">{"".join(rows)}</ul>
  </section>

  <section class="card rise" style="--d:6">
    <h2>{icon("globe", 17)} لینک اشتراک</h2>
    <div class="linkrow"><div class="txt ltr mono" id="subTxt">{esc(d["sub_url"])}</div>
      <button class="ibtn" data-copy-el="#subTxt" aria-label="copy">{icon("copy", 16)}</button>
      <button class="ibtn" data-qr="{esc(d["sub_url"])}" data-title="Subscription" aria-label="qr">{icon("qr", 16)}</button></div>
  </section>

  <section class="card rise" style="--d:7">
    <h2>{icon("shield", 17)} جزئیات فنی</h2>
    <div class="grid2">
      {kv("پروتکل", d["protocol"])}{kv("Fingerprint", d["fingerprint"])}
      {kv("محدودیت IP", d["ip_limit"], d["ip_limit"] == "نامحدود")}{kv("محدودیت اتصال", d["conn_limit"], d["conn_limit"] == "نامحدود")}
      {kv("محدودیت سرعت", d["speed"], d["speed"] == "نامحدود")}{kv("تاریخ انقضا", d["expiry"], d["expiry"] == "نامحدود")}
    </div>
  </section>

  <section class="card rise" style="--d:8">
    <h2>{icon("download", 17)} دانلود برنامه‌ها</h2>
    <div class="apps">{apps_html}</div>
  </section>
</main>
<nav class="dock"><button class="btn p" data-copy="{esc(d["sub_url"])}">{icon("copy", 15)} کپی لینک ساب</button>
<button class="btn" data-qr="{esc(d["sub_url"])}" data-title="Subscription" style="flex:0 0 64px">{icon("qr", 16)}</button></nav>"""
    return _shell(d["name"], body)


def render_not_found() -> str:
    body = (
        '<main class="wrap"><section class="card" style="text-align:center;padding:40px 20px">'
        f'<div class="orb" style="margin:0 auto 14px">{icon("lock", 24)}</div>'
        '<h1 style="font-size:20px;font-weight:900">لینک پیدا نشد</h1>'
        '<p class="muted" style="margin-top:6px;font-size:13px">این لینک حذف شده یا اشتباه است.</p></section></main>'
    )
    return _shell("404", body)


# --------------------------------------------------------------------------------------
# /p/{key}  (group page, filled in by the browser from /api/public/sub/{key})
# --------------------------------------------------------------------------------------

_GROUP_CSS = r"""
.gl{list-style:none;display:grid;grid-template-columns:minmax(0,1fr);gap:10px}
.gi{padding:14px;border-radius:18px;background:var(--sf2);border:1px solid var(--bd);display:grid;gap:10px}
.gi-h{display:flex;align-items:center;gap:10px}
.dot{width:10px;height:10px;border-radius:50%;background:var(--green);flex:none;box-shadow:0 0 0 4px rgba(74,222,128,.15)}
.dot.off{background:var(--red);box-shadow:0 0 0 4px rgba(251,113,133,.15)}
.gi-h b{flex:1;min-width:0;font-size:14px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.gi-f{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.gi-f .btn{padding:9px 8px;font-size:12px;white-space:nowrap}
.gi-f .btn.p{grid-column:1/-1}
.lock{display:grid;gap:12px;justify-items:center;text-align:center;padding:10px 0}
.lock input{width:100%;max-width:300px;padding:12px 14px;border-radius:14px;border:1px solid var(--bd);background:var(--sf2);color:var(--tx);font:inherit;text-align:center;outline:none}
.lock input:focus{border-color:var(--teal)}
.err{color:var(--red);font-size:12px;min-height:18px}
.sk{height:84px;border-radius:18px;background:linear-gradient(90deg,var(--sf2),rgba(255,255,255,.09),var(--sf2));background-size:200% 100%;animation:slide 1.4s linear infinite}
"""

_GROUP_JS = r"""
(function(){
var d=document,key=location.pathname.split('/').filter(Boolean).pop(),pw='';
try{pw=sessionStorage.getItem('pw_'+key)||''}catch(e){}
var app=d.getElementById('app');
function el(t,c,x){var e=d.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e}
function svg(path,s){var w=d.createElement('span');w.innerHTML='<svg class="ic" viewBox="0 0 24 24" width="'+(s||16)+'" height="'+(s||16)+'" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'+path+'</svg>';return w.firstChild}
var P={copy:'<rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
qr:'<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><path d="M14 14h3v3h-3zM20 14v.01M14 20h.01M17 20h4v-3"/>',
open:'<path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
wave:'<path d="M3 15c3-6 6-6 9 0s6 6 9 0"/><path d="M3 9c3-6 6-6 9 0s6 6 9 0" opacity=".55"/>',
lock:'<rect x="4" y="10" width="16" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>',
users:'<path d="M17 21v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2"/><circle cx="10" cy="7" r="4"/><path d="M21 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8"/>',
chart:'<path d="M3 3v18h18"/><path d="M7 15l4-5 3 3 5-7"/>',link:'<path d="M10 13a5 5 0 0 0 7.5.5l3-3a5 5 0 0 0-7-7l-1.7 1.7"/><path d="M14 11a5 5 0 0 0-7.5-.5l-3 3a5 5 0 0 0 7 7l1.7-1.7"/>'};
function bd(txt){var b=d.createElement('bdi');b.setAttribute('dir','ltr');b.textContent=txt;return b}
function btn(cls,ic,txt,fn){var b=el('button','btn '+cls);b.appendChild(svg(P[ic],15));b.appendChild(d.createTextNode(' '+txt));if(fn)b.onclick=fn;return b}
function bar(){var b=el('div','bar rise'),c=el('span','chip t');c.appendChild(svg(P.wave,14));c.appendChild(d.createTextNode(' اشتراک گروهی'));b.appendChild(c);
 var t=el('button','ibtn');t.setAttribute('data-theme-toggle','');t.setAttribute('aria-label','theme');t.innerHTML='<svg class="ic" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z"/></svg>';b.appendChild(t);return b}
function card(c,d0){var x=el('section','card rise '+(c||''));x.style.setProperty('--d',d0||0);return x}
function skeleton(){app.textContent='';app.appendChild(bar());var s=card('',1);s.appendChild(el('div','sk'));app.appendChild(s)}
function locked(name,bad){
  app.textContent='';app.appendChild(bar());
  var c=card('',1),w=el('div','lock'),o=el('div','orb');o.appendChild(svg(P.lock,24));w.appendChild(o);
  w.appendChild(el('h1',null,name||'اشتراک'));w.appendChild(el('p','muted','این اشتراک رمز دارد'));
  var i=el('input');i.type='password';i.placeholder='رمز عبور';i.autocomplete='current-password';
  var e=el('div','err',bad?'رمز اشتباه است':'');
  var go=btn('p','lock','ورود',function(){pw=i.value;load()});
  i.onkeydown=function(ev){if(ev.key==='Enter'){pw=i.value;load()}};
  w.appendChild(i);w.appendChild(e);w.appendChild(go);c.appendChild(w);app.appendChild(c);setTimeout(function(){i.focus()},50)
}
function pct(l){return l.limit_bytes>0?Math.min(100,Math.round(l.used_bytes/l.limit_bytes*100)):null}
function render(j){
  var subUrl=j.sub_url+(pw?('?pw='+encodeURIComponent(pw)):'');
  app.textContent='';app.appendChild(bar());
  var h=card('hero',1),o=el('div','orb');o.appendChild(svg(P.wave,26));h.appendChild(o);
  var m=el('div','hero-main');m.appendChild(el('h1',null,j.name));if(j.desc)m.appendChild(el('p','uuid',j.desc));
  var ch=el('div','chips');
  var pl0=null;
  [['t',null,j.links.length+' کانفیگ'],['g',null,'TCP + UDP'],['v',j.total_used_fmt,' مصرف']].forEach(function(x){var c=el('span','chip '+x[0]);if(x[1]){c.appendChild(bd(x[1]))}c.appendChild(d.createTextNode(x[2]));ch.appendChild(c)});
  var on=j.links.some(function(l){return l.active});
  var pl=el('span','pill '+(on?'ok':'bad'));pl.appendChild(el('i'));pl.appendChild(d.createTextNode(on?'فعال':'غیرفعال'));ch.insertBefore(pl,ch.firstChild);
  m.appendChild(ch);h.appendChild(m);app.appendChild(h);

  var s=card('',2),h2=el('h2');h2.appendChild(svg(P.link,17));h2.appendChild(d.createTextNode(' لینک اشتراک'));s.appendChild(h2);
  var lr=el('div','linkrow'),tx=el('div','txt ltr mono',subUrl);lr.appendChild(tx);
  var cb=el('button','ibtn');cb.setAttribute('data-copy',subUrl);cb.appendChild(svg(P.copy,16));lr.appendChild(cb);
  var qb=el('button','ibtn');qb.setAttribute('data-qr',subUrl);qb.setAttribute('data-title','Subscription');qb.appendChild(svg(P.qr,16));lr.appendChild(qb);
  s.appendChild(lr);app.appendChild(s);

  var lc=card('',3),lh=el('h2');lh.appendChild(svg(P.chart,17));lh.appendChild(d.createTextNode(' کانفیگ‌ها '));lh.appendChild(el('span','chip',String(j.links.length)));lc.appendChild(lh);
  var ul=el('ul','gl');
  j.links.forEach(function(l){
    var li=el('li','gi'),hd=el('div','gi-h');hd.appendChild(el('span','dot'+(l.active?'':' off')));hd.appendChild(el('b',null,l.label||'—'));
    hd.appendChild(el('span','chip t',(l.protocol==='vless-ws'?'Web Socket':l.protocol)));li.appendChild(hd);
    var p=pct(l),tr=el('div','track'),sp=el('span');tr.style.setProperty('--w',(p==null?100:Math.max(2,p))+'%');if(p==null)sp.style.opacity='.35';tr.appendChild(sp);li.appendChild(tr);
    var meta=el('div','tbar-row');var us=el('span');us.appendChild(bd(l.used_fmt+' / '+l.limit_fmt));meta.appendChild(us);var cs=el('span');cs.appendChild(bd(String(l.connections||0)));cs.appendChild(d.createTextNode(' اتصال'));meta.appendChild(cs);li.appendChild(meta);
    var f=el('div','gi-f');
    f.appendChild(btn('p','copy','کپی کانفیگ',function(ev){px.copy(l.vless_link,ev.currentTarget)}));
    f.appendChild(btn('','qr','QR',function(){px.qr(l.vless_link,l.label)}));
    var a=btn('','open','جزئیات');a.onclick=function(){location.href=l.info_url};f.appendChild(a);
    li.appendChild(f);ul.appendChild(li)
  });
  lc.appendChild(ul);app.appendChild(lc);
  var dk=el('nav','dock');dk.appendChild(btn('p','copy','کپی لینک ساب',function(ev){px.copy(subUrl,ev.currentTarget)}));app.appendChild(dk)
}
function load(){
  skeleton();
  fetch('/api/public/sub/'+encodeURIComponent(key)+(pw?('?pw='+encodeURIComponent(pw)):''),{cache:'no-store'})
   .then(function(r){return r.json().then(function(j){return[r.status,j]})})
   .then(function(x){var j=x[1];
     if(x[0]===404||!j){app.textContent='';app.appendChild(bar());var c=card('',1);c.appendChild(el('h1',null,'اشتراک پیدا نشد'));app.appendChild(c);return}
     if(j.locked){var bad=!!pw;try{sessionStorage.removeItem('pw_'+key)}catch(e){}pw='';return locked(j.name,bad)}
     try{if(pw)sessionStorage.setItem('pw_'+key,pw)}catch(e){}
     render(j)})
   .catch(function(){app.textContent='';var c=card('',1);c.appendChild(el('p','muted','ارتباط برقرار نشد'));app.appendChild(c)})
}
load();
})();
"""


def render_group_page() -> str:
    body = '<main class="wrap" id="app"></main>'
    return _shell("اشتراک", body, _GROUP_CSS, _GROUP_JS)
