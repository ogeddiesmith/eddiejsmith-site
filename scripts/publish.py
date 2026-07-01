#!/usr/bin/env python3
"""Scheduled publisher for the EJS blog (static, GitHub Pages).
All 32 posts are committed. This gates them by content/schedule.json: a post is
LIVE when its publishDate <= today. Live posts are indexable + listed on the hub
+ in the sitemap; future posts carry <meta robots noindex> and are hidden from
the hub/sitemap until their date. Run weekly by .github/workflows/publish.yml."""
import json, os, re, html
from datetime import date

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://eddiejsmith.com"   # swap to https://eddiejsmith.com when DNS live
BOOK = "https://calendar.app.google/nKdsYJffrjcYnHPt7"
NL   = "https://www.linkedin.com/newsletters/the-local-lead-gen-playbook-7393014909321736192"
PILLAR_MASTER = "marketing-roi-for-local-business"
NOINDEX = '<meta name="robots" content="noindex">'

# Google Consent Mode v2 defaults — MUST run BEFORE GTM loads. Region-scoped: denied for
# EEA/UK/CH (opt-in regimes), granted for the US + everywhere else (so US collection is unchanged).
CONSENT_HEAD = (
    "<!-- Google Consent Mode v2 (defaults set BEFORE GTM) -->"
    "<script>"
    "window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}"
    "gtag('consent','default',{'ad_storage':'denied','ad_user_data':'denied','ad_personalization':'denied','analytics_storage':'denied',"
    "'region':['AT','BE','BG','HR','CY','CZ','DK','EE','FI','FR','DE','GR','HU','IE','IT','LV','LT','LU','MT','NL','PL','PT','RO','SK','SI','ES','SE','IS','LI','NO','GB','CH']});"
    "gtag('consent','default',{'ad_storage':'granted','ad_user_data':'granted','ad_personalization':'granted','analytics_storage':'granted'});"
    "</script>"
    "<!-- End Google Consent Mode v2 -->"
)

# Google Tag Manager container (GA4 G-BWVKPMNEXE is configured INSIDE GTM, not here).
# Kept as plain (non-f) strings so their {…} JS braces don't clash with the f-string template.
GTM_HEAD = (
    "<!-- Google Tag Manager -->"
    "<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':"
    "new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],"
    "j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src="
    "'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);"
    "})(window,document,'script','dataLayer','GTM-P9X8MDSR');</script>"
    "<!-- End Google Tag Manager -->"
)
GTM_BODY = (
    "<!-- Google Tag Manager (noscript) -->"
    '<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-P9X8MDSR"'
    ' height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>'
    "<!-- End Google Tag Manager (noscript) -->"
)

# EEA/UK/CH consent banner (reviewed): shown only to opt-in regions, updates Consent Mode v2.
CONSENT_BANNER = '''<!-- EJS consent banner (EEA/UK/CH only; updates Consent Mode v2) --><script>(function(){
  try{
    var KEY='ejs_consent';
    function upd(v){ try{ if(typeof gtag==='function'){ gtag('consent','update',{'ad_storage':v,'ad_user_data':v,'ad_personalization':v,'analytics_storage':v}); } }catch(e){} }
    var saved=null;
    try{ saved=localStorage.getItem(KEY); }catch(e){}
    if(saved==='granted'){ upd('granted'); return; }
    if(saved==='denied'){ upd('denied'); return; }
    var tz='';
    try{ tz=Intl.DateTimeFormat().resolvedOptions().timeZone||''; }catch(e){}
    var euExtra=['Atlantic/Canary','Atlantic/Madeira','Atlantic/Azores','Atlantic/Reykjavik','Asia/Nicosia','Asia/Famagusta'];
    var nonEea=['Europe/Istanbul','Europe/Moscow','Europe/Kaliningrad','Europe/Samara','Europe/Volgograd','Europe/Saratov','Europe/Astrakhan','Europe/Ulyanovsk','Europe/Kirov','Europe/Kyiv','Europe/Kiev','Europe/Simferopol','Europe/Uzhgorod','Europe/Zaporozhye','Europe/Minsk','Europe/Chisinau','Europe/Tiraspol','Europe/Belgrade','Europe/Sarajevo','Europe/Skopje','Europe/Tirane','Europe/Podgorica'];
    var euTz=((tz.indexOf('Europe/')===0)||(euExtra.indexOf(tz)>-1))&&(nonEea.indexOf(tz)<0);
    if(!euTz) return;
    function show(){
      try{
        if(document.getElementById('ejs-consent')) return;
        var s=document.createElement('style');
        s.textContent='#ejs-consent{position:fixed;left:0;right:0;bottom:0;z-index:2147483647;background:#1a1d28;border-top:1px solid #2a2f3d;color:#f3efe7;font-family:Inter,system-ui,sans-serif;font-size:14px;line-height:1.5;padding:16px 20px;display:flex;flex-wrap:wrap;gap:12px 18px;align-items:center;justify-content:center;box-shadow:0 -8px 24px rgba(0,0,0,.35)}#ejs-consent:focus{outline:none}#ejs-consent p{margin:0;max-width:640px;color:#b9bdc8}#ejs-consent a{color:#e8c178;text-decoration:underline}#ejs-consent .ejs-b{display:flex;gap:10px;flex:0 0 auto}#ejs-consent button{cursor:pointer;border-radius:8px;padding:9px 16px;font-weight:600;font-size:14px;font-family:Inter,system-ui,sans-serif;border:1px solid #2a2f3d}#ejs-consent .ejs-ok{background:#d4a64b;color:#0c0d12;border-color:#d4a64b}#ejs-consent .ejs-no{background:transparent;color:#f3efe7}#ejs-consent button:focus-visible,#ejs-consent a:focus-visible{outline:2px solid #e8c178;outline-offset:2px}';
        document.head.appendChild(s);
        var d=document.createElement('div');
        d.id='ejs-consent'; d.setAttribute('role','dialog'); d.setAttribute('aria-label','Cookie consent'); d.setAttribute('aria-describedby','ejs-consent-desc'); d.setAttribute('tabindex','-1');
        d.innerHTML='<p id="ejs-consent-desc">We use cookies to measure how this site is used — see our <a href="/privacy/">Privacy &amp; Cookie Notice</a>. Accept analytics cookies?</p><div class="ejs-b"><button type="button" class="ejs-no">Decline</button><button type="button" class="ejs-ok">Accept</button></div>';
        document.body.appendChild(d);
        function done(v){ try{localStorage.setItem(KEY,v);}catch(e){} upd(v); if(d.parentNode){d.parentNode.removeChild(d);} }
        d.querySelector('.ejs-ok').addEventListener('click',function(){done('granted');});
        d.querySelector('.ejs-no').addEventListener('click',function(){done('denied');});
        try{ d.focus(); }catch(e){}
      }catch(e){}
    }
    if(document.readyState==='loading'){ document.addEventListener('DOMContentLoaded',show); } else { show(); }
  }catch(e){}
})();</script><!-- End EJS consent banner -->'''

def esc(s): return html.escape(s or "", quote=True)

FONTS=('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
 '<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">')

def hub_css():
    """Reuse the exact CSS already shipped on a built post page (single source of truth)."""
    sample = os.path.join(HERE, "blog", PILLAR_MASTER, "index.html")
    m = re.search(r"<style>(.*?)</style>", open(sample, encoding="utf-8").read(), re.S)
    return m.group(1) if m else ""

def toggle_noindex(slug, published):
    p = os.path.join(HERE, "blog", slug, "index.html")
    if not os.path.exists(p): return
    h = open(p, encoding="utf-8").read(); orig = h
    has = NOINDEX in h
    if published and has:
        h = h.replace(NOINDEX, "")
    elif not published and not has:
        h = h.replace('<link rel="icon" href="../../favicon.svg">',
                      '<link rel="icon" href="../../favicon.svg">' + NOINDEX, 1)
    if h != orig: open(p, "w", encoding="utf-8").write(h)

def render_hub(published):
    css = hub_css()
    master = next((m for m in published if m["slug"] == PILLAR_MASTER), None)
    rest = [m for m in published if m["slug"] != PILLAR_MASTER]
    rest.sort(key=lambda m: (m["publishDate"], m["slot"]), reverse=True)  # newest first
    url = BASE + "/blog/"
    feat = ""
    if master:
        feat = ('<a class="feat" href="%s/"><img src="%s/hero.webp" alt="%s"><div class="pad">'
                '<div class="k">Start here &middot; the pillar guide</div><h2>%s</h2><p>%s</p>'
                '<span class="go">Read the guide &rarr;</span></div></a>'
                % (master["slug"], master["slug"], esc(master["h1"]), esc(master["h1"]), esc(master["metaDescription"])))
    cards = "".join(
        '<a class="pcard" href="%s/"><img src="%s/hero.webp" alt="%s"><div class="pad"><h3>%s</h3><p>%s</p></div></a>'
        % (m["slug"], m["slug"], esc(m["h1"]), esc(m["h1"]), esc(m["metaDescription"])) for m in rest)
    schema = {"@context":"https://schema.org","@type":"Blog","name":"The Local Lead Gen Playbook","url":url,
              "author":{"@type":"Person","name":"Eddie J. Smith"}}
    cta = ('<div class="ctablock"><h3>Read how I think before you pay me a dollar.</h3>'
        '<p>The Local Lead Gen Playbook — my newsletter and public teardowns on making local marketing actually pay.</p>'
        '<div class="row"><a class="btn btn-gold" href="%s" target="_blank" rel="noopener">Read the free Playbook</a>'
        '<a class="btn btn-ghost" href="%s" target="_blank" rel="noopener">Book a call</a></div></div>' % (NL, BOOK))
    out = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">{CONSENT_HEAD}{GTM_HEAD}
<title>The Local Lead Gen Playbook — Eddie J. Smith</title>
<meta name="description" content="Field notes on making local marketing actually pay — attribution, wasted spend, Google Ads, local SEO, and AI for local service businesses.">
<link rel="canonical" href="{url}"><link rel="icon" href="../favicon.svg">
<meta property="og:type" content="website"><meta property="og:site_name" content="Eddie J. Smith">
<meta property="og:title" content="The Local Lead Gen Playbook — Eddie J. Smith"><meta property="og:description" content="Field notes on making local marketing actually pay.">
<meta property="og:url" content="{url}"><meta property="og:image" content="{BASE}/og-image.png">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{BASE}/og-image.png">
{FONTS}
<script type="application/ld+json">{json.dumps(schema)}</script>
<style>{css}</style></head><body>{GTM_BODY}
<header><nav class="wrap nav"><a class="brand" href="../">EDDIE J<span>.</span> SMITH</a><a class="btn btn-gold" href="{BOOK}" target="_blank" rel="noopener">Book a call</a></nav></header>
<main class="wrap hubhero">
<div class="eyebrow">The Local Lead Gen Playbook</div>
<h1>Field notes on making local marketing pay.</h1>
<p class="dek">How to see what your marketing actually turns into in booked revenue — attribution, wasted spend, Google Ads, local SEO, and where AI takes the manual work off your plate.</p>
{feat}<div class="grid">{cards}</div>{cta}
</main>
<footer><div class="wrap">Eddie J. Smith &middot; AI &amp; Growth Systems &middot; <a href="../">eddiejsmith.com</a> &middot; <a href="/privacy/">Privacy</a></div></footer>{CONSENT_BANNER}
</body></html>"""
    open(os.path.join(HERE, "blog", "index.html"), "w", encoding="utf-8").write(out)

def render_sitemap(published):
    urls = [BASE + "/", BASE + "/blog/"] + [BASE + "/blog/%s/" % m["slug"] for m in published]
    body = "\n".join("<url><loc>%s</loc><changefreq>monthly</changefreq></url>" % u for u in urls)
    open(os.path.join(HERE, "sitemap.xml"), "w", encoding="utf-8").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + body + "\n</urlset>\n")

def main():
    today = date.today().isoformat()
    posts = json.load(open(os.path.join(HERE, "content", "posts.json")))
    published, scheduled = [], []
    for m in posts:
        live = m["publishDate"] <= today
        toggle_noindex(m["slug"], live)
        (published if live else scheduled).append(m)
    render_hub(published)
    render_sitemap(published)
    print("Publish run %s — live: %d, scheduled: %d" % (today, len(published), len(scheduled)))
    nextup = sorted(scheduled, key=lambda m: m["publishDate"])[:2]
    if nextup: print("Next up:", ", ".join("%s (%s)" % (m["slug"], m["publishDate"]) for m in nextup))

if __name__ == "__main__":
    main()
