#!/usr/bin/env python3
"""Build the portfolio.

  python3 build_site.py          -> single self-contained file (Claude artifact)
  python3 build_site.py web      -> deploy/our-work/ with external assets (Vercel)
"""
import base64, datetime, json, os, pathlib, re, shutil, sys

S = os.path.dirname(os.path.abspath(__file__))
MODE = "web" if len(sys.argv) > 1 and sys.argv[1] == "web" else "inline"

# The web build serves assets separately so it can afford 720p. The artifact build
# inlines everything as base64 under a hard 16MB page cap, so it stays at 360p.
# Both sets are clean: no watermark, per the client's decision on 2026-08-15.
V = f"{S}/vid/720" if MODE == "web" else f"{S}/vid/360"
P = f"{S}/post"
OUT = f"{S}/deploy/our-work"
if MODE == "web":
    shutil.rmtree(f"{S}/deploy", ignore_errors=True)
    os.makedirs(f"{OUT}/a", exist_ok=True)

# Where every "book a call" button points. A mailto opens a blank compose window on
# a phone and most people close it, so this is meant to hold a Google Calendar
# appointment booking page URL instead. Set BOOK_URL and every CTA on every page
# follows; leave it empty and they fall back to email.
# Switched 2026-08-25: homeservicestudios.com is live and receiving mail. See
# api_contact.js for the matching TO/sender switch on the form's send path.
EMAIL = "info@homeservicestudios.com"

# The live origin. Canonical tags, OG URLs, the sitemap, robots.txt and the JSON-LD
# record all derive from this, so it is the one place the site's own address is
# written down. It sat inside the web-build block until 2026-09-03, which put it
# out of reach of JSON_LD and left that block naming yoniverseproductions.com by
# hand long after the site had moved to GitHub Pages under the new domain. Google
# reads a canonical tag as an instruction, so every page was pointing ranking
# signals at the old Vercel copy. Moving it here is what stops that recurring.
SITE = "https://homeservicestudios.com"

# Where the enquiry form actually delivers. Kept separate from EMAIL, which is the
# address shown on the page: the two are allowed to differ and currently do.
# api_contact.js (Brevo, via a Vercel function) is unreachable on GitHub Pages,
# which is static, so this is the receiver until the form is moved back to a real
# backend. FORM_ACTION is the no-JS fallback; FORM_JS posts to the /ajax/ variant.
FORM_TO = "yoni@homeservicestudios.com"
FORM_ACTION = f"https://formsubmit.co/{FORM_TO}"

# Paste the Google Calendar appointment booking page here and every CTA on the site
# switches at once. While it is empty the buttons fall back to a prefilled mailto,
# and the reassurance line below them is suppressed (it promises a Meet call).
BOOK_URL = ""          # e.g. https://calendar.app.google/xxxxxxxx
BOOKED = bool(BOOK_URL)

REASSURE = ("Twenty minutes on Google Meet. We'll look at your market, your current content, "
            "and whether a monthly program makes sense.")

# what the form path actually promises, which is not a call yet.
#
# Four variants rather than one. The single line used to render verbatim in all
# five places it appears, and the sentence insisting a human is involved reading
# identically on every page is exactly the tell it was written to avoid. Every
# variant makes the same three promises (short, fast, answered by a person about
# your own market), so nothing is being over-claimed in one place and under-claimed
# in another; only the phrasing moves. reassure() picks by page.
REASSURE_FORM = ("Six questions, under a minute. You will hear back within one business day, "
                 "from a human, about your market specifically.")

REASSURE_VARIANTS = {
    "home": REASSURE_FORM,
    "work": ("Six questions and about a minute. A person reads it and answers within one "
             "business day, about your market rather than in general."),
    "packages": ("Under a minute to fill in. You get a real answer within one business day, "
                 "about your city and your trade, not a brochure."),
    "contact": ("Six questions, under a minute. One business day to a reply, written by "
                "someone here who has looked at your market."),
    # /packages calls reassure() twice, once at the top and once under the terms
    # grid, so the second needs its own line or the page repeats itself to itself.
    "packages-terms": ("Still six questions, still under a minute. A person answers within "
                       "one business day, and tells you which program actually fits."),
}

# Feather "user", stands in for a headshot on /team/ until real photos exist.
PERSON_ICON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" '
               'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
               '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>'
               '<circle cx="12" cy="7" r="4"/></svg>')

# Filled triangle, marks a YouTube spot as click-to-play so it never looks like a
# plain photo. Optically off-center by design: a symmetric triangle reads as
# slightly left-heavy, so the play glyph nudges right via margin in .ytplay.
PLAY_ICON = ('<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true">'
             '<path d="M8 5v14l11-7z"/></svg>')

# Down chevron, hints at scroll on the homepage hero only. Plain stroke, no fill,
# so it reads as a cue rather than another button competing with the CTAs below it.
SCROLL_ICON = ('<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" '
               'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
               '<path d="M6 9l6 6 6-6"/></svg>')

def cta_href():
    """Where every conversion CTA on the site points. One rule, no exceptions, so a
    button cannot quietly keep pointing somewhere stale."""
    return BOOK_URL if BOOKED else "/contact/#start"


def book(subject, label="", cls="cta"):
    """The single conversion CTA. While there is no scheduler it sends people to the
    enquiry form, which beats a mailto on every device and actually qualifies them.
    Set BOOK_URL and the same buttons become the calendar instead. `subject` is kept
    so the fallback can still address an email if it is ever needed."""
    if BOOKED:
        return (f'<a class="{cls}" href="{cta_href()}" target="_blank" '
                f'rel="noopener noreferrer">{label or "Book a call"}</a>')
    return f'<a class="{cls}" href="{cta_href()}">{label or "Start a project"}</a>'

def reassure(page="home"):
    """Sits under the CTA and describes what actually happens next. The promise has
    to match the destination, so it changes with it. Once BOOKED is set every CTA
    becomes the calendar and there is only one true promise to make, so the
    per-page phrasing collapses back to a single line on purpose."""
    if BOOKED:
        return f'<p class="reassure">{REASSURE}</p>'
    return f'<p class="reassure">{REASSURE_VARIANTS.get(page, REASSURE_FORM)}</p>'

def actionbar():
    """Phones only. Two thumbs, two jobs: reach out, or send the details.
    A <nav> with its own label, not a bare div: it sits outside <main> and
    <footer>, and axe's region rule flags content outside every landmark."""
    return (f'<nav class="actionbar" aria-label="Quick actions">'
            f'<a href="/contact/">Contact</a>'
            f'<a class="primary" href="{cta_href()}">'
            f'{"Book a call" if BOOKED else "Start a project"}</a></nav>')


def nav(active=""):
    """Sticky top bar, shared by every page so the three can never drift apart.

    `active` is one of "work" or "packages" and marks the current page. The logo
    is the route home, which is why there is no separate Home link. The CTA
    follows BOOK_URL like every other one, and carries a short label for phones
    where the full one will not fit.
    """
    def link(href, label, key, cls=""):
        classes = " ".join(x for x in [cls, "is-on" if key == active else ""] if x)
        c = f' class="{classes}"' if classes else ''
        return f'<a href="{href}"{c}>{label}</a>'

    href = cta_href()
    long_label, short_label = (("Book a call", "Book") if BOOKED
                               else ("Start a project", "Contact"))
    # .brandmark renders at height:28px, so 84px tall covers a 3x display. The
    # source PNG was shipping at its full 1072x517 and 205KB, on every page, of
    # which Lighthouse called 203KB pure waste. The width/height attributes below
    # must keep matching the file or the reserved box changes and CLS comes back.
    icon = asset(f"{S}/logos_hss/nav_mark_hss.webp", "image/webp")
    return (
        '<nav class="nav" id="nav" aria-label="Primary"><div class="wrap navin">'
        f'<a class="brand" href="/"><img class="brandmark" src="{icon}" alt="" '
        f'width="174" height="84">Home Service Studios</a>'
        '<div class="navright">'
        '<button type="button" class="navtoggle" id="navtoggle" '
        'aria-expanded="false" aria-controls="navlinks" aria-label="Menu">'
        '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" aria-hidden="true">'
        '<path d="M4 7h16M4 12h16M4 17h16"/></svg></button>'
        '<div class="navlinks" id="navlinks">'
        + link("/our-work/", "Work", "work")
        + link("/packages/", "Packages", "packages")
        + link("/team/", "Team", "team")
        + link("/contact/", "Contact", "contact", "navsecondary")
        + '</div>'
        # No aria-label here on purpose. It used to be hard set to long_label,
        # but only one of the two spans below is ever displayed (the other is
        # display:none, so it is excluded from the accessible name), which meant
        # that under 560px the button read "Contact" and announced "Start a
        # project". That is Lighthouse's label-content-name-mismatch, and for a
        # voice-control user saying "click Contact" it simply does nothing.
        # Letting the name come from the visible span keeps the two identical at
        # every width, and both labels are descriptive enough to pass link-text.
        + (f'<a class="navcta" href="{href}" '
           f'target="_blank" rel="noopener noreferrer">'
           if BOOKED else f'<a class="navcta" href="{href}">')
        + f'<span class="ctalong">{long_label}</span>'
          f'<span class="ctashort">{short_label}</span></a>'
        '</div></div></nav><div class="navspacer"></div>'
    )

def b64(p): return base64.b64encode(pathlib.Path(p).read_bytes()).decode()


def img_size(path):
    """Intrinsic (width, height) of a JPEG, PNG or WebP, read from the file header
    with the standard library only (Pillow is not available to every Python on
    this machine). Used for the width/height attributes on every <img>, so the
    browser reserves the right box before the image arrives and CLS stays 0; the
    numbers always come from the file, never typed by hand."""
    b = pathlib.Path(path).read_bytes()
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        return int.from_bytes(b[16:20], "big"), int.from_bytes(b[20:24], "big")
    if b[:4] == b"RIFF" and b[8:12] == b"WEBP":
        kind = b[12:16]
        if kind == b"VP8 ":
            return (int.from_bytes(b[26:28], "little") & 0x3FFF,
                    int.from_bytes(b[28:30], "little") & 0x3FFF)
        if kind == b"VP8L":
            v = int.from_bytes(b[21:25], "little")
            return (v & 0x3FFF) + 1, ((v >> 14) & 0x3FFF) + 1
        if kind == b"VP8X":
            return (int.from_bytes(b[24:27], "little") + 1,
                    int.from_bytes(b[27:30], "little") + 1)
    if b[:2] == b"\xff\xd8":
        i = 2
        while i < len(b):
            while b[i] == 0xFF:
                i += 1
            marker = b[i]; i += 1
            if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                continue
            seg = int.from_bytes(b[i:i + 2], "big")
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                          0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                return int.from_bytes(b[i + 5:i + 7], "big"), int.from_bytes(b[i + 3:i + 5], "big")
            i += seg
    raise ValueError(f"cannot read image size: {path}")


_NUM_WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
              "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
              "seventeen", "eighteen", "nineteen", "twenty"]


def num_word(n):
    """A count written out in words, for copy that should read as a sentence."""
    return _NUM_WORDS[n] if 0 <= n < len(_NUM_WORDS) else format(n, ",")


def dims(path):
    """width/height attributes for an <img>, from the file itself."""
    w, h = img_size(path)
    return f' width="{w}" height="{h}"'

def asset(path, mime):
    """Inline as a data URI for the artifact, or copy out and link for the web build."""
    if MODE == "web":
        name = os.path.basename(path)
        shutil.copy(path, os.path.join(OUT, "a", name))
        # root absolute, not relative: /our-work without a trailing slash would
        # otherwise resolve "a/x.mp4" against the site root and 404
        return f"/our-work/a/{name}"
    return f"data:{mime};base64," + b64(path)

# Onest and Archivo, both SIL Open Font License, latin subset only. Three static
# weights each (not a variable file): a single combined-weight request to Google's
# css2 endpoint can come back as either a variable file or a static instance
# depending on how the query is shaped, and that ambiguity isn't worth the risk on
# a font used for every heading on the site. Individual single-weight requests are
# unambiguous, so that's what's embedded, same as Onest already does.
def _face(family, weight, path):
    return (f"@font-face{{font-family:'{family}';font-style:normal;font-weight:{weight};"
            f"font-display:optional;src:url(data:font/woff2;base64,{b64(path)}) format('woff2');}}")

FONT_CSS = ("<style>"
    + "".join(_face("Onest", w, f"{S}/fonts/onest-{w}.woff2") for w in (400, 600, 700))
    + "".join(_face("Archivo", w, f"{S}/fonts/archivo-{w}.woff2") for w in (400, 700, 900))
    + "</style>")

CSS = """<style>
  :root{
    --ground:#FFFFFF; --ground-2:#F5F4F1; --panel:#EFEEEA;
    --line:#E2E0DA; --line-soft:#ECEBE6;
    --ink:#14171A; --ink-2:#4B535B; --ink-3:#6B747C;
    --orange:#F04820; --orange-text:#B93412; --cyan:#00B0C8; --cyan-text:#006673;
    --orange-rgb:240,72,32; --cyan-rgb:0,176,200;

    /* Type scale. Every size on the site comes from this list and nowhere else.
       Each step is fluid between a 380px and a 1280px viewport, so there are no
       jumps at breakpoints. Nothing is below 12px: the old sheet had 18 usages
       under that, which is what made the pages feel squinty. */
    --f-micro: clamp(12px, 11.58px + 0.111vw, 13px);
    --f-sm:    clamp(13.5px, 13.08px + 0.111vw, 14.5px);
    --f-body:  clamp(15.5px, 15.08px + 0.111vw, 16.5px);
    --f-lede:  clamp(17px, 16.37px + 0.167vw, 18.5px);
    --f-lead:  clamp(18.5px, 17.44px + 0.278vw, 21px);
    --f-h4:    clamp(17px, 16.16px + 0.222vw, 19px);
    --f-h3:    clamp(21px, 18.89px + 0.556vw, 26px);
    --f-h2:    clamp(26px, 22.62px + 0.889vw, 34px);
    --f-h1:    clamp(30px, 23.24px + 1.778vw, 46px);
    --f-price: clamp(34px, 29.78px + 1.111vw, 44px);
    --f-hero:  clamp(42px, 22.58px + 5.111vw, 88px);
    --f-mega:  clamp(52px, 30.04px + 5.778vw, 104px);

    /* Spacing, on an 8px base. Replaces 33 hand picked values. */
    --s1:4px; --s2:8px; --s3:12px; --s4:16px; --s5:24px;
    --s6:32px; --s7:48px; --s8:64px; --s9:96px;
    /* halved 2026-08-26: section padding is top AND bottom, so the dead
       space between two sections was roughly 2x this value; halving it
       halves that gap site-wide without touching padding inside a section. */
    --s-sec: clamp(28px, 19.555px + 2.222vw, 48px);

    /* Four radii instead of eight, so cards at different sizes still look related */
    /* R4. Sharp, not rounded. 10-14px radii and 100px pills are the app-store
       default; print and film titling are square. 2 to 4px reads as cut, not as a
       component library. --r-pill keeps its name so call sites need not change. */
    --r-sm:2px; --r-md:3px; --r-lg:4px; --r-pill:2px;

    /* How far an ambient YouTube iframe is oversized past its visible 16:9 box,
       top and bottom, so YouTube's own title/uploader strip and bottom chrome
       are drawn outside the clip (see .herobg-clip and iframe.banner). A floor,
       not the value: both call sites scale it up with the player. */
    --yt-chrome:120px;

    /* Tracking: display tightens, small caps open up. Nothing in between. */
    /* R6. Tracking never past .06em. Letterspacing blown out to .14em is a screen
       era tic; typographers open small caps a little and stop there. */
    --t-display:-.03em; --t-head:-.015em; --t-caps:.055em;

    /* 2026-08-24: was a real monospace stack (ui-monospace/SF Mono/Menlo). Read as
       a code editor, not a premium data face, once pointed out against Archivo
       pricing elsewhere on the page. Every var(--mono) caller (prices, per-asset
       units, chart labels, stat captions) now gets the same bold display face as
       the big stat numbers, so there's one confident numeral system site wide
       instead of three competing ones. Keeping the token name: renaming would
       touch 26 call sites for a purely cosmetic identifier change. */
    --mono: var(--display);
    /* Second family, for display and for the big numbers. One typeface across a
       whole site is the tell. */
    --display: 'Archivo', "Arial Black", Arial, sans-serif;
    --ease:.18s cubic-bezier(.2,.6,.3,1);
  }
  *{box-sizing:border-box;}
  html{scroll-behavior:smooth;}
  /* 4.0 Hard constraint. Everything below animates transform and opacity only,
     and all of it is switched off here. Tested, not assumed. */
  @media(prefers-reduced-motion:reduce){
    *,*::before,*::after{
      animation-duration:0.01ms !important;
      animation-iteration-count:1 !important;
      transition-duration:0.01ms !important;
      scroll-behavior:auto !important;
    }
    html{scroll-behavior:auto;}
    .rv{opacity:1 !important;transform:none !important;}
    .marquee-track{animation:none !important;transform:none !important;}
    .banner{animation:none !important;transform:none !important;}
  }
  /* flat ground (2026-10-06): the two-radial-gradient dot grain that gave the
     page "tooth" went with the other faux-material textures; footage is the
     only texture on the site now */
  body{margin:0;padding:0;background:var(--ground);color:var(--ink);
    font:var(--f-lede)/1.62 'Onest',-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
    -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;}
  .display{font-family:var(--display);font-weight:700;
    letter-spacing:-.018em;line-height:1.06;text-wrap:balance;margin:0;}

  /* R1 and R2. This was a mono, uppercase, .14em-tracked kicker with a little rule
     in front of it, on 32 elements. That combination is the single most recognisable
     machine-built signature there is. It is now small caps in the text face at
     ordinary tracking, quiet, with nothing in front of it. A label announces the
     section; it does not need a flag to announce the label. */
  .eyebrow{font-family:var(--display);font-variant-caps:all-small-caps;
    font-size:var(--f-lede);letter-spacing:.07em;text-transform:none;
    color:var(--ink-3);margin:0;display:block;font-weight:400;}

  .wrap{max-width:1120px;margin:0 auto;padding:0 var(--s5);}
  a{color:var(--orange-text);}
  a:focus-visible{outline:2px solid var(--orange);outline-offset:3px;border-radius:2px;}

  /* Sticky top bar. Translucent with a blur so the full bleed banner video can
     pass under it and the labels stay readable. It only grows a background and a
     hairline once you have actually scrolled, so it sits invisibly over the hero. */
  /* Nav stays the same dark ink as the homepage hero (.hero-bold, #14171A) on every
     page, not just the homepage, so the bar reads as one consistent piece of brand
     chrome rather than switching look per page. Text tokens below are hand set to
     the same white/light values .hero-bold uses on that ground, not var(--ink*),
     since those tokens are themed for the white page ground and would be
     unreadable here. */
  .nav{position:fixed;top:0;left:0;right:0;z-index:50;background:#14171A;
    border-bottom:1px solid transparent;transition:background var(--ease),border-color var(--ease);}
  .nav.is-stuck{background:rgba(20,23,26,.92);border-bottom-color:rgba(255,255,255,.12);
    -webkit-backdrop-filter:saturate(160%) blur(14px);backdrop-filter:saturate(160%) blur(14px);}
  .nav.is-stuck::after{content:"";position:absolute;left:0;right:0;bottom:-1px;height:1px;
    background:linear-gradient(90deg,rgba(var(--orange-rgb),.55) 0%,rgba(var(--cyan-rgb),.42) 42%,
      rgba(255,255,255,.3) 78%,rgba(255,255,255,0) 100%);}
  .navin{display:flex;align-items:center;justify-content:space-between;gap:var(--s4);
    height:60px;}
  /* One plain text run now ("Home Service Studios", no separate .bsub span
     sized/coloured apart from the rest), one fixed size, no
     min-width:560px jump: those were the two places the wordmark could
     legitimately render at more than one size, which is what kept reading
     as inconsistent across pages/viewports even once markup and CSS were
     verified identical. */
  .brand{display:flex;align-items:center;gap:8px;text-decoration:none;color:#FFFFFF;
    font-family:'Onest',-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
    font-weight:700;letter-spacing:var(--t-head);font-size:var(--f-sm);white-space:nowrap;}
  .brandmark{height:28px;width:auto;display:block;border-radius:var(--r-sm);flex:none;}
  /* .navright groups everything but the brand (toggle, the link list,
     the CTA) so .navin keeps exactly the two-item space-between layout it
     always had; .navlinks used to be that grouping div itself; now it is
     just the link list, nested one level in, so it alone can become a
     mobile dropdown without disturbing how the CTA sits relative to the
     brand. Both carry the same gap escalation so the visual spacing at
     each breakpoint is unchanged from before this split. */
  .navright{display:flex;align-items:center;gap:10px;}
  .navlinks{display:flex;align-items:center;gap:10px;}
  .navsecondary{display:none;}
  @media(min-width:620px){
    .navright{gap:var(--s4);}
    .navlinks{gap:var(--s4);}
    .navsecondary{display:inline;}
  }
  @media(min-width:560px){.navright{gap:var(--s5);} .navlinks{gap:var(--s5);}}
  .navlinks a{font-family:var(--display);font-variant-caps:all-small-caps;letter-spacing:.06em;
    font-size:var(--f-lede);color:#D8D3C9;text-decoration:none;white-space:nowrap;
    transition:color var(--ease);}
  .navlinks a:hover{color:#FFFFFF;}
  .navlinks a.is-on{color:var(--orange);}
  /* 2026-08-29: Work/Packages/Team never fit next to the brand wordmark and
     the CTA pill on a real phone once Team existed (it overflowed off the
     right edge; "no hamburger, two links and a button fit" stopped being
     true the moment a third link was added and was never revisited). Below
     620px .navlinks becomes a collapsible dropdown instead of a second row
     it never got, toggled by .navtoggle (hidden at 620px+, where the old
     inline layout is untouched). */
  .navtoggle{display:none;flex:none;align-items:center;justify-content:center;
    width:40px;height:40px;padding:0;border:0;background:none;color:#FFFFFF;
    cursor:pointer;}
  @media(max-width:619px){
    .navtoggle{display:flex;order:1;}
    .navcta{order:2;}
    .navlinks{position:absolute;top:100%;left:0;right:0;z-index:-1;
      flex-direction:column;align-items:stretch;gap:0;
      background:#14171A;border-top:1px solid rgba(255,255,255,.12);
      max-height:calc(100vh - 60px);overflow-y:auto;
      transform:translateY(-8px);opacity:0;pointer-events:none;
      transition:opacity var(--ease),transform var(--ease);}
    .navlinks.is-open{z-index:0;opacity:1;transform:translateY(0);pointer-events:auto;}
    .navlinks a{padding:16px var(--s5);border-bottom:1px solid rgba(255,255,255,.08);}
    .navsecondary{display:block;}
  }
  /* ---------- 4.1 motion ---------- */
  /* (a) scroll reveals. The hidden state is applied by JS, so if the script never
     runs the content is simply visible rather than invisible forever. */
  .rv{opacity:0;transform:translateY(16px);}
  .rv-in{opacity:1;transform:none;
    transition:opacity .4s cubic-bezier(.16,1,.3,1),transform .4s cubic-bezier(.16,1,.3,1);}
  /* mobile reduces rather than replicates: shorter travel, shorter duration */
  @media(max-width:700px){
    .rv{transform:translateY(10px);}
    .rv-in{transition-duration:.3s;}
  }
  /* The four "what you are actually buying" cards get a longer, more visible
     travel than the generic reveal so they read as sliding into frame rather
     than a subtle fade. Only .benefit uses this, nothing else, so the
     generic .rv distance elsewhere is untouched.
     The actual bug behind two rounds of "it doesn't animate, just sits
     offset": the JS adds rv-in without ever removing rv, which is fine for
     the generic single-class .rv/.rv-in pair (equal specificity, source
     order picks .rv-in's transform:none). But .benefit.rv is a two-class
     compound, which outranks the generic .rv-in on specificity alone, so its
     translate offset was winning permanently once both classes were on the
     element at the same time. .benefit.rv-in has to restate transform:none
     itself at the same compound specificity to actually win. */
  .benefit.rv,.step2.rv{transform:translateY(48px);}
  .benefit.rv-in,.step2.rv-in{transform:none;transition-duration:.5s;}
  @media(max-width:700px){.benefit.rv,.step2.rv{transform:translateY(30px);}}

  /* the one deliberate entrance above the fold. It runs on the stat cards only,
     never on the hero paragraph, which is the LCP element on most pages. */
  @keyframes heroIn{to{opacity:1;transform:none;}}
  .hero .stat{opacity:0;transform:translateY(12px);
    animation:heroIn .5s cubic-bezier(.16,1,.3,1) forwards;}
  .hero .stat:nth-child(1){animation-delay:.04s;}
  .hero .stat:nth-child(2){animation-delay:.10s;}
  .hero .stat:nth-child(3){animation-delay:.16s;}
  .hero .stat:nth-child(4){animation-delay:.22s;}

  /* (b) count-up needs digits that do not jump width as they change */
  .stat .n,.op .n,.reel .vnum{font-variant-numeric:tabular-nums;}

  /* (d) hero film: a slow push in, transform only, clipped by the wrapper so a
     1.04 scale on a 100vw element cannot create a horizontal scrollbar */
  .bannerwrap{overflow:hidden;position:relative;width:100vw;max-width:100vw;margin-left:calc(50% - 50vw);}
  .bannerwrap .banner{width:100%;margin-left:0;}
  @keyframes pushIn{from{transform:scale(1);}to{transform:scale(1.04);}}
  .banner.is-playing{animation:pushIn 8s cubic-bezier(.4,0,.2,1) forwards;}

  /* (e) logo wall (D4, 2026-10-06): an ink band (.on-ink) with the marks in
     light. Desktop: one line, a slow marquee. Phones and reduced motion: a
     static grid instead, 3 across on phones and 5 across on desktop, which
     both divide the 15 marks evenly; the loop's duplicate set (.dupe) is not
     shown there. Every mark sits on the same 500x200 canvas at equal optical
     ink area, so one width per breakpoint keeps them visually equal. */
  .marquee{overflow:hidden;position:relative;
    -webkit-mask-image:linear-gradient(90deg,transparent,#000 8%,#000 92%,transparent);
    mask-image:linear-gradient(90deg,transparent,#000 8%,#000 92%,transparent);}
  .marquee-track{display:flex;width:max-content;gap:var(--s7);align-items:center;
    animation:marq 60s linear infinite;}
  .marquee:hover .marquee-track,.marquee:focus-within .marquee-track{animation-play-state:paused;}
  @keyframes marq{from{transform:translateX(0);}to{transform:translateX(-50%);}}
  .marquee .logomark{width:150px;flex:none;}
  @media(min-width:700px){.marquee .logomark{width:190px;}}
  @media(max-width:759px),(prefers-reduced-motion:reduce){
    .marquee{-webkit-mask-image:none;mask-image:none;}
    .marquee-track{animation:none;transform:none;width:auto;display:grid;
      grid-template-columns:repeat(3,minmax(0,1fr));gap:var(--s5);}
    .marquee .logomark{width:auto;}
    .marquee .dupe{display:none;}
  }
  @media(min-width:760px) and (prefers-reduced-motion:reduce){
    .marquee-track{grid-template-columns:repeat(5,minmax(0,1fr));gap:var(--s6) var(--s7);}
  }
  /* the marks are single-colour --ink silhouettes, so on the ink band they
     are simply inverted to a light grey rather than regenerated */
  .on-ink .logomark img{filter:invert(1);opacity:.78;}
  .on-ink .logomark:hover img{opacity:1;}

  /* (f) The sticky case header is deliberately not implemented. It was specced to
     orient a reader in a long page, but after the case split these pages run 180 to
     380 words, so a 250px pinned block only ate the viewport and painted over the
     A1 chart. Cut rather than kept as decoration. */

  /* (g) header compaction. The bar is fixed with a spacer holding its place, so
     shrinking it cannot shift the page. The wordmark itself no longer scales down
     with it (removed 2026-08-26): that 0.92x on scroll was the one place the exact
     same logo rendered at two different sizes on the exact same page, and a
     scrolled screenshot next to a fresh-load one read as the site being
     inconsistent page to page when it was really just this scroll state. The bar
     height still compacts; the wordmark now holds one fixed size everywhere. */
  .navspacer{height:60px;}
  .nav .navin{transition:height var(--ease);}
  .nav.is-stuck .navin{height:52px;}

  /* A1 has no fetchable stills, so the page carries a chart of the real numbers */
  .chartwrap{background:var(--ground-2);border:1px solid var(--line);border-radius:var(--r-md);
    padding:var(--s5);margin-bottom:var(--s5);}
  .charttitle{margin:0 0 var(--s4);font-size:var(--f-h4);font-weight:650;
    letter-spacing:var(--t-head);}
  .a1chart{width:100%;height:auto;display:block;}
  .chartnote{margin:var(--s4) 0 0;font-size:var(--f-body);color:var(--ink-2);line-height:1.55;
    max-width:70ch;}

  /* ---------- enquiry form ---------- */
  /* Single column per field group: multi column forms slow completion because the
     eye has to hunt for the next control. Labels sit above inputs, never inside
     them, because placeholder-as-label disappears the moment you start typing. */
  .cform{display:flex;flex-direction:column;gap:var(--s5);}
  .fgrid{display:grid;grid-template-columns:1fr;gap:var(--s4);}
  @media(min-width:680px){.fgrid{grid-template-columns:1fr 1fr;}}
  .fld{display:flex;flex-direction:column;gap:6px;min-width:0;border:0;padding:0;margin:0;}
  .fld > label,.fld > legend{font-size:var(--f-sm);font-weight:650;color:var(--ink);padding:0;}
  .fld .opt{font-weight:400;color:var(--ink-3);font-size:var(--f-micro);
    text-transform:uppercase;letter-spacing:.1em;font-family:var(--mono);margin-left:6px;}
  /* reserved whether or not there is a hint, so every field is the same height
     and the inputs line up across both columns */
  .fhint{font-size:var(--f-sm);color:var(--ink-3);line-height:1.45;min-height:1.45em;}
  .cform input,.cform select,.cform textarea{
    width:100%;background:var(--ground-2);border:1px solid var(--line);
    border-radius:var(--r-sm);padding:13px 14px;color:var(--ink);
    font:var(--f-body)/1.4 'Onest',-apple-system,sans-serif;min-height:48px;
    transition:border-color var(--ease),background var(--ease);}
  .cform textarea{min-height:110px;resize:vertical;}
  .cform input:hover,.cform select:hover,.cform textarea:hover{border-color:var(--ink-3);}
  .cform input:focus,.cform select:focus,.cform textarea:focus{
    outline:none;border-color:var(--orange-text);background:var(--panel);}
  .cform input:focus-visible,.cform select:focus-visible,.cform textarea:focus-visible{
    outline:2px solid var(--orange);outline-offset:2px;}
  .cform select{appearance:none;-webkit-appearance:none;cursor:pointer;
    background-image:linear-gradient(45deg,transparent 50%,var(--ink-3) 50%),
      linear-gradient(135deg,var(--ink-3) 50%,transparent 50%);
    background-position:calc(100% - 19px) 21px,calc(100% - 13px) 21px;
    background-size:6px 6px,6px 6px;background-repeat:no-repeat;padding-right:40px;}

  /* Budget as visible radios rather than a dropdown: a buyer who never opens a menu
     never learns where the floor is, and self-selection out is wanted here. */
  .budgets{gap:var(--s3);}
  .budgetrow{display:grid;grid-template-columns:1fr;gap:var(--s2);}
  @media(min-width:560px){.budgetrow{grid-template-columns:repeat(auto-fit,minmax(172px,1fr));}}
  /* 2026-10-06: the radio used to be absolutely positioned at top:50%, which
     put it about 17px below the first line of a two-line option and left its
     circle (plus the UA's 5px left margin) touching the label text. Each option
     is now a two-column grid: the real radio in column one, centred on the
     first text row, a --s3 (12px) gap, then the price and tier lines. The whole
     <label> is the hit area, so a tap anywhere on the card selects it. */
  .budgetrow .budget{display:grid;grid-template-columns:auto minmax(0,1fr);
    column-gap:var(--s3);row-gap:2px;align-items:center;align-content:center;
    cursor:pointer;background:var(--ground-2);border:1px solid var(--line);
    border-radius:var(--r-sm);padding:var(--s3) var(--s4);min-height:60px;
    transition:border-color var(--ease),background var(--ease),box-shadow var(--ease);}
  .budget:hover{border-color:var(--ink-3);}
  .budget input{grid-column:1;grid-row:1;margin:0;
    width:18px;height:18px;min-height:0;padding:0;accent-color:var(--orange-text);cursor:pointer;}
  /* checked: border and an inset ring read as a 2px frame without moving the
     layout, plus the darker panel fill */
  .budget:has(input:checked){border-color:var(--orange-text);background:var(--panel);
    box-shadow:inset 0 0 0 1px var(--orange-text);}
  .budget:has(input:focus-visible){outline:2px solid var(--orange);outline-offset:2px;}
  /* the card carries the focus ring, so the radio's own would only double it */
  @supports selector(:has(*)){.budget input:focus-visible{outline:none;}}
  .budget .bv{grid-column:2;grid-row:1;font-size:var(--f-body);font-weight:650;color:var(--ink);
    line-height:1.4;white-space:nowrap;}
  .budget .bt{grid-column:2;grid-row:2;font-family:var(--mono);font-size:var(--f-micro);
    color:var(--cyan-text);letter-spacing:.06em;text-transform:uppercase;line-height:1.35;}

  /* errors appear next to the field they belong to, on blur, never as a summary */
  .ferr{font-size:var(--f-sm);color:#C0392B;min-height:0;display:none;}
  .fld.is-bad .ferr,.budgets.is-bad .ferr{display:block;}
  .fld.is-bad input,.fld.is-bad select,.fld.is-bad textarea{border-color:#C0392B;}

  .hp{position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden;}
  .fsubmit{display:flex;flex-direction:column;gap:var(--s3);align-items:flex-start;}
  .cform button.cta{border:0;cursor:pointer;font-family:inherit;}
  .cform button.cta[disabled]{opacity:.6;cursor:default;}
  .fstatus{margin:0;font-size:var(--f-body);line-height:1.55;display:none;}
  .fstatus.is-err{display:block;color:#C0392B;}
  .fdone{background:var(--ground-2);border:1px solid rgba(var(--orange-rgb),.4);
    border-radius:var(--r-md);padding:var(--s6) var(--s5);}
  .fdone h3{margin:0 0 var(--s2);font-size:var(--f-h3);font-weight:700;
    letter-spacing:var(--t-head);}
  .fdone p{margin:0;color:var(--ink-2);line-height:1.55;max-width:60ch;}

  /* Sticky action bar, phones only. Trades buyers call, and on a long case page the
     header scrolls away. Sits above the safe area on notched devices. */
  .actionbar{position:fixed;left:0;right:0;bottom:0;z-index:55;display:flex;gap:1px;
    background:var(--line);border-top:1px solid var(--line);
    padding-bottom:env(safe-area-inset-bottom);}
  .actionbar a{flex:1;display:flex;align-items:center;justify-content:center;gap:8px;
    min-height:54px;text-decoration:none;font-size:var(--f-sm);font-weight:650;
    background:var(--ground-2);color:var(--ink);}
  .actionbar a.primary{background:var(--orange);color:#14171A;}
  .actionbar a svg{flex:none;}
  @media(min-width:760px){.actionbar{display:none;}}
  @media(max-width:759px){body{padding-bottom:54px;}}
  /* The homepage hero is min-height:100dvh with justify-content:flex-end, so its
     text block is anchored to the bottom of the viewport, which is exactly where
     the fixed .actionbar sits. Measured at 390x844 before this rule: the h1 ended
     at 820px and the bar started at 789px, so "does nothing.", the payoff line of
     the headline, was covered. body's padding-bottom does not help here, it moves
     the end of the document rather than anything inside a viewport-height box.
     Padding the hero itself is what clears it. */
  @media(max-width:759px){
    .hero-media{padding-bottom:calc(54px + env(safe-area-inset-bottom));}
  }

  /* a section that opens without a label, set larger to carry the weight the
     eyebrow used to. Two of seven on the homepage, deliberately not all. */
  .sec-head.bare h2{font-size:clamp(34px,5.6vw,58px);max-width:18ch;}
  .sec-head.bare{gap:var(--s4);}

  /* /our-work case grid (D5, 2026-10-06), replacing the blueprint carousel:
     flat cards, one large plus two stacked from 900px, stacked on phones. A
     real still with the big metric over it under a dark scrim; A1 has no still
     (its reels are on Facebook), so its lead card shows the real numbers on ink
     instead of invented art. No arrows, no dots. */
  .cgrid{display:grid;grid-template-columns:minmax(0,1fr);gap:var(--s4);}
  @media(min-width:900px){
    .cgrid{grid-template-columns:minmax(0,1.4fr) minmax(0,1fr);}
    .cgcard.is-lead{grid-row:span 2;}
  }
  .cgcard{display:flex;flex-direction:column;background:var(--ground-2);border-radius:var(--r-md);
    overflow:hidden;text-decoration:none;color:inherit;transition:transform var(--ease);}
  .cgcard:hover{transform:translateY(-2px);}
  .cgcard.is-active{outline:2px solid var(--orange-text);outline-offset:-2px;}
  .cg-art{position:relative;display:block;aspect-ratio:16/9;background:#14171A;overflow:hidden;}
  .cg-art img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:block;}
  .cg-art.has-still::after{content:"";position:absolute;inset:0;
    background:linear-gradient(180deg,rgba(20,23,26,0) 35%,rgba(20,23,26,.9) 100%);}
  .cg-metric{position:absolute;left:var(--s5);right:var(--s5);bottom:var(--s4);z-index:1;
    display:flex;flex-direction:column;gap:2px;}
  .cg-metric b{font-family:var(--display);font-weight:900;font-size:var(--f-h1);line-height:1;
    letter-spacing:-.02em;color:var(--orange);font-variant-numeric:tabular-nums;}
  .cg-metric span{font-size:var(--f-micro);letter-spacing:.06em;text-transform:uppercase;
    font-family:var(--mono);color:#D8D3C9;}
  .cg-data{display:flex;flex-direction:column;justify-content:space-between;gap:var(--s6);
    padding:var(--s6) var(--s5) var(--s5);aspect-ratio:auto;flex:1;}
  .cg-data .cg-metric{position:static;}
  .cg-top{display:flex;flex-direction:column;gap:var(--s4);}
  .cg-line{font-size:var(--f-lead);line-height:1.45;color:#D8D3C9;max-width:30ch;}
  .cg-data .cg-metric b{font-size:var(--f-mega);}
  .cg-data .a1chart{width:100%;height:auto;display:block;}
  .cg-body{display:flex;flex-direction:column;gap:var(--s1);padding:var(--s4) var(--s5) var(--s5);}
  .cg-vert{font-family:var(--display);font-variant-caps:all-small-caps;letter-spacing:.06em;
    font-size:var(--f-sm);color:var(--cyan-text);}
  .cg-name{font-family:var(--display);font-size:var(--f-h3);font-weight:700;
    letter-spacing:var(--t-head);line-height:1.15;}
  .cg-go{margin-top:var(--s2);font-size:var(--f-sm);font-weight:650;color:var(--orange-text);}

  /* Each is the exact same section markup a standalone case page used to
     render on its own; only one shows at a time, opened by CASES_JS from the
     URL hash the case cards link to. */
  .case-panels > section{display:none;}
  .case-panels > section.is-active{display:block;}

  /* sits under a booking CTA, so nobody has to guess what happens after the click */
  .reassure{margin:var(--s3) 0 0;font-size:var(--f-sm);color:var(--ink-3);max-width:52ch;
    line-height:1.5;}

  .schedwrap{background:var(--ground-2);border:1px solid var(--line);
    border-radius:var(--r-md);overflow:hidden;}
  .schedwrap iframe{display:block;width:100%;}

  .navcta{background:var(--orange);color:#14171A !important;border-radius:var(--r-pill);
    padding:0 16px;font-weight:700;transition:filter var(--ease);
    font-family:'Onest',-apple-system,sans-serif !important;text-transform:none;
    font-variant-caps:normal !important;letter-spacing:var(--t-head);font-size:var(--f-sm);
    display:inline-flex;align-items:center;min-height:40px;}
  .navcta:hover{filter:brightness(1.08);}
  .navcta .ctashort{display:inline;}
  .navcta .ctalong{display:none;}
  @media(min-width:560px){
    .navcta{padding:0 20px;min-height:42px;}
    .navcta .ctashort{display:none;}
    .navcta .ctalong{display:inline;}
  }

  /* R5. Two radial accent washes used to sit here. A coloured glow behind a hero is
     decoration standing in for hierarchy; the type and the splatter carry it now. */
  .hero{padding:var(--s7) 0 var(--s8);position:relative;overflow:hidden;background:var(--ground);}
  .splat{position:absolute;inset:0;width:100%;height:100%;pointer-events:none;
    filter:blur(.35px);opacity:.92;}
  /* contact page only: the lines sat mid-paragraph by default; a plain
     translate keeps the crop/zoom untouched and just moves them up, closer
     under the "Talk to us." heading. */
  .hero-contact .splat{transform:translateY(-60px);}
  .hero > .wrap{position:relative;z-index:1;}
  .hero h1{font-size:var(--f-hero);margin:var(--s4) 0 0;}
  .hero .sub{margin:var(--s5) 0 0;max-width:58ch;font-size:var(--f-lead);color:var(--ink-2);
    line-height:1.52;}
  .hero .sub strong{color:var(--ink);font-weight:600;}

  /* 2026-08-24: bold pass, homepage only. A CSS custom property scope, not a
     second theme: redeclaring the tokens inside .hero-bold re-themes every child
     that already reads var(--ink)/var(--ground)/etc, with zero new rules needed
     for the stat ledger, eyebrow, CTAs or splat text colors. --orange-text and
     --cyan-text swap to the bright hues in this scope because the AA-safe dark
     variants (tuned for white) go muddy on black; the bright hues clear AA here
     on their own, checked the same way the white-ground pairs were. */
  /* 2026-10-06 (D3): every inner page's hero shares this scope as .hero-dark,
     so the brand's strongest look is not homepage-only. Contrast on #14171A,
     checked with the WCAG formula: --ink-2 #D8D3C9 12.6:1, --ink-3 #A8A29A
     7.4:1, --orange 4.8:1, --cyan 6.9:1. */
  .hero.hero-bold,.hero.hero-dark,.on-ink{background:#14171A;color:#FFFFFF;
    --ground:#14171A; --ground-2:#1E2226; --panel:#262B30; --line:#33383D;
    --ink:#FFFFFF; --ink-2:#D8D3C9; --ink-3:#A8A29A;
    --orange-text:var(--orange); --cyan-text:var(--cyan);}
  .hero.hero-bold{padding:0;}
  /* line-height:1.18, not the 1.06 inherited from .display: that's tight
     enough on its own that adjacent lines' ascenders/descenders nearly
     touch even with a plain transparent background, which a solid
     highlight color then makes obvious rather than causing outright.
     Scoped to just this hero, not .display itself, which is shared by
     every other heading on the site. */
  .hero-bold h1{font-size:clamp(36px, 12px + 5.4vw, 84px);font-weight:900;
    letter-spacing:-.025em;line-height:1.18;}
  .hero-bold .hl,.hero-dark .hl{background:var(--orange);color:#14171A;padding:.02em .14em;
    box-decoration-break:clone;-webkit-box-decoration-break:clone;}
  /* inner pages keep their own --f-hero size; weight, tracking and the 1.18
     line-height (room for the highlight bar) match the homepage */
  .hero-dark h1{font-weight:900;letter-spacing:-.025em;line-height:1.18;}

  /* 2026-08-26: hero video pass. The black bg + animated .splat lines move
     down to only the lower half now (.hero-lines, behind the sub copy,
     stats and CTAs); the headline instead sits, bottom anchored, over an
     ambient looping YouTube background video (.hero-media) that fills the
     full viewport edge to edge, same IFrame Player technique and
     poster-mask trick as the Quality banner (see setupAmbient in SOLO_JS).
     Kept deliberately close to verysilly.dev's hero: full bleed, mostly
     undimmed footage, and a compact text block rather than type filling
     the whole frame. */
  .hero-media{position:relative;overflow:hidden;background:#14171A;
    min-height:100vh;min-height:100dvh;
    display:flex;flex-direction:column;justify-content:flex-end;}
  /* object-fit is not reliably honoured on an <iframe> (notably Firefox),
     so cover-cropping is done with a centered 16:9 box instead.
     2026-10-06: YouTube draws its title/uploader strip ("HSS Website Banner
     v02 / Sergy Olkowski") across the top of the player a few seconds into
     playback, and no player param suppresses it; the poster only covers the
     cueing phase. So the visible picture is now .herobg-clip, an exact 16:9
     box that covers the hero (height is the larger of the hero's own height
     and 56.25vw, width follows from aspect-ratio, so it covers at any aspect
     and with dvh/lvh differences), with overflow:hidden. The iframe inside is
     taller than the box by --yt-chrome (or 12% of the box, whichever is
     larger) top and bottom. A player taller than 16:9 letterboxes its video
     to full width and centres it, so the video lands exactly on the clip box
     and YouTube's own chrome, which hugs the player's edges, lands in the
     clipped margin. No delay, nothing to time. */
  .hero-media .herobg-clip{position:absolute;top:50%;left:50%;z-index:0;
    height:max(100%, 56.25vw);aspect-ratio:16/9;transform:translate(-50%,-50%);
    overflow:hidden;pointer-events:none;}
  .hero-media .herobg{position:absolute;left:0;top:calc(-1 * max(var(--yt-chrome), 12%));
    width:100%;height:calc(100% + 2 * max(var(--yt-chrome), 12%));
    border:0;pointer-events:none;}
  @media(max-width:600px){
    /* less crop on narrow phones: full-height cover on a tall narrow screen
       zooms the 16:9 video in hard enough that only a thin vertical slice
       of its width ever shows. A fixed 74.8vh-tall box (aspect-ratio keeps
       it exactly 16:9, so 133vh wide) trades a modest, deliberate letterbox
       gap top and bottom (filled by the same dark background already behind
       everything, so it is not jarring) for meaningfully more of the actual
       footage, about the ~33% more width visible that was asked for. The
       clip box still hides YouTube's chrome here, because the oversized
       iframe is clipped by the box itself, not by the hero's edges. */
    .hero-media .herobg-clip{height:74.8vh;}
    /* smaller title, same reasoning: less of the frame covered by
       text/scrim, more of the video underneath actually reads. Desktop's
       clamp is untouched. */
    .hero-bold h1{font-size:clamp(26px, 8px + 5vw, 42px);}
  }
  /* clickable, not pointer-events:none like the iframe under it: iOS
     (Low Power Mode especially) silently refuses muted autoplay on a good
     fraction of real phones, and the YouTube IFrame API gives no error
     for this, it just never leaves the cued state, so the poster would
     stay up forever with no way to start the video at all. A tap always
     bypasses autoplay restrictions on every platform, so the fallback is
     to make the poster itself the play button (see setupAmbient). */
  .hero-poster{position:absolute;inset:0;z-index:2;background:#14171A;
    transition:opacity .6s ease;cursor:pointer;}
  .hero-poster.is-hidden{opacity:0;pointer-events:none;}
  /* YouTube always draws its own watermark in this corner with controls=0
     and no param removes it; the oversized crop above may or may not push
     it past the edge depending on viewport aspect, so this covers it
     directly rather than leaving it to chance. */
  .hero-yt-mask{position:absolute;right:0;bottom:0;z-index:2;pointer-events:none;
    width:min(220px,32%);height:min(84px,16%);
    background:linear-gradient(135deg,rgba(20,23,26,0) 0%,
      rgba(20,23,26,.94) 55%,rgba(20,23,26,1) 100%);}
  /* light touch, not a wash: most of the frame stays undimmed, darkening
     only where the headline actually sits so the video reads clean rather
     than muddy, the opposite problem the first pass had. */
  .hero-scrim{position:absolute;inset:0;z-index:1;pointer-events:none;
    background:linear-gradient(180deg,rgba(20,23,26,0) 0%,rgba(20,23,26,0) 42%,
      rgba(20,23,26,.48) 74%,rgba(20,23,26,.86) 100%);}
  /* extra bottom padding (rather than var(--s7) alone) pulls the whole
     block up off the very bottom edge of the 100vh frame: on shorter
     browser windows the headline was tall enough to push its last line
     (the "does nothing." highlight) below the fold on first load, with no
     scroll yet to reveal it. */
  /* text plus scroll hint share one flex row now (was the headline's own
     .wrap alone), so the chevron sits to the right of the copy and
     vertically centered against it, rather than pinned to the bottom
     center of the whole frame. min-width:0 on the text column lets the
     headline keep wrapping normally with the icon column beside it. */
  .hero-media > .wrap{position:relative;z-index:3;display:flex;align-items:center;
    gap:var(--s5);padding-bottom:clamp(var(--s8), 10vh, 140px);}
  .hero-media > .wrap > .herotext{min-width:0;flex:1 1 auto;}
  /* scroll hint: waits a second before it appears (so it never competes
     with the headline landing), then bobs gently. Fade-in and bob are
     split across two elements so their transforms never fight over the
     same property. */
  .scrollhint{flex:none;opacity:0;color:rgba(255,255,255,.8);
    pointer-events:none;animation:scrollhint-fade .6s ease 1s forwards;}
  .scrollhint svg{display:block;animation:scrollhint-bob 1.8s ease-in-out 1.6s infinite;}
  @keyframes scrollhint-fade{to{opacity:1;}}
  @keyframes scrollhint-bob{0%,100%{transform:translateY(0);}50%{transform:translateY(7px);}}
  .hero-lines{position:relative;}
  .hero-lines > .wrap{position:relative;z-index:1;
    padding-top:var(--s6);padding-bottom:var(--s8);}

  /* hairline gaps rather than per-cell borders: an adjacent-sibling rule left a
     stray line on the first item of every wrapped row on a phone.
     2026-10-06: both ledgers (homepage hero, /our-work) hold three figures. On a
     phone they are a single-column ledger, one figure per row with the number
     on the left, because three columns at 390px left about 89px for text and
     "Conditioning" alone does not fit in that. From 560px up every figure sits
     in one row: grid-auto-flow:column makes one equal column per item, so any
     count lays out as a single row and there is never an orphan or an empty
     filler cell. */
  .stats{display:grid;grid-template-columns:minmax(0,1fr);
    gap:1px;background:var(--line);margin-top:var(--s7);}
  .stat{background:var(--ground);padding:var(--s3) var(--s4);
    display:grid;grid-template-columns:4.4em minmax(0,1fr);
    grid-template-areas:"n case" "n k";column-gap:var(--s4);row-gap:2px;align-items:center;
    text-decoration:none;color:inherit;transition:background var(--ease);}
  .stat:hover{background:var(--ground-2);}
  .stat .case{grid-area:case;font-family:var(--display);font-variant-caps:all-small-caps;
    letter-spacing:.05em;font-size:var(--f-sm);color:var(--cyan-text);line-height:1.3;}
  .stat .n{grid-area:n;font-size:var(--f-h3);font-weight:700;letter-spacing:-.012em;
    color:var(--orange-text);font-family:var(--display);line-height:1.1;}
  .stat .k{grid-area:k;font-size:var(--f-micro);letter-spacing:.06em;text-transform:uppercase;
    color:var(--ink-3);font-family:var(--mono);line-height:1.35;}
  @media(min-width:560px){
    .stats{grid-template-columns:none;grid-auto-flow:column;grid-auto-columns:minmax(0,1fr);}
    /* Subgrid lines the three rows (client, number, label) up across every
       cell, so a client name that wraps at tablet widths cannot push its
       number out of line with its neighbours. This replaces the old fixed
       two-line reservation on .case, which left an empty line under every
       name once three columns gave them room to sit on one line. */
    .stat{grid-template-columns:none;grid-template-areas:none;
      grid-row:span 3;grid-template-rows:subgrid;row-gap:var(--s1);align-items:start;
      padding:var(--s4) var(--s5) var(--s5);}
    .stat .case,.stat .n,.stat .k{grid-area:auto;}
  }
  /* Four figures (the homepage hero since 2026-10-06): 2x2 on phones and
     tablets, one row of four from 900px, with the same subgrid row alignment,
     so there is never an orphan. The three-figure /our-work ledger keeps the
     single-column phone rows above. */
  .stats.quad{grid-template-columns:repeat(2,minmax(0,1fr));}
  .stats.quad .stat{grid-template-columns:none;grid-template-areas:none;grid-row:span 3;
    grid-template-rows:subgrid;row-gap:var(--s1);align-items:start;
    padding:var(--s3) var(--s4) var(--s4);}
  .stats.quad .stat .case,.stats.quad .stat .n,.stats.quad .stat .k{grid-area:auto;}
  @media(min-width:560px){
    .stats.quad{grid-template-columns:repeat(2,minmax(0,1fr));grid-auto-flow:row;}
    .stats.quad .stat{padding:var(--s4) var(--s5) var(--s5);}
  }
  @media(min-width:900px){.stats.quad{grid-template-columns:none;grid-auto-flow:column;}}
  /* No subgrid: fall back to the reservation, so numbers still line up. */
  @supports not (grid-template-rows:subgrid){
    @media(min-width:560px){
      .stat{display:flex;flex-direction:column;gap:var(--s1);}
      .stat .case{min-height:2.6em;}
    }
  }

  section{padding:var(--s-sec) 0;position:relative;scroll-margin-top:76px;}
  /* section breaks get a heavier rule than anything inside a section, so the page
     has a hierarchy of lines rather than one weight repeated 31 times */
  section::before{content:"";position:absolute;top:0;left:0;right:0;height:3px;
    background:linear-gradient(90deg,var(--orange) 0%,var(--orange) 8%,
      rgba(var(--cyan-rgb),.5) 34%,rgba(226,224,218,.6) 72%,rgba(226,224,218,0) 100%);}
  .sec-head{display:flex;flex-direction:column;gap:var(--s3);margin-bottom:var(--s6);}
  .sec-head h2{font-size:var(--f-h1);}
  .sec-head .lede{margin:0;max-width:62ch;color:var(--ink-2);font-size:var(--f-lede);line-height:1.58;}
  .sec-head .lede strong{color:var(--ink);font-weight:600;}

  .role{display:flex;flex-wrap:wrap;gap:var(--s2);align-items:center;margin-top:var(--s1);}
  .role .lbl{font-family:var(--mono);font-size:var(--f-micro);letter-spacing:var(--t-caps);
    text-transform:uppercase;color:var(--ink-3);margin-right:2px;}
  .pill{border:1px solid rgba(var(--orange-rgb),.4);background:rgba(var(--orange-rgb),.10);color:var(--orange-text);
    border-radius:var(--r-pill);padding:4px var(--s3);font-size:var(--f-lede);font-weight:400;
    font-family:var(--display);font-variant-caps:all-small-caps;letter-spacing:.05em;}

  /* .csi: the plain three-column challenge/solution/impact text blocks on
     every case study. (The homepage's manila-folder variant, .csi-photo, was
     retired on 2026-10-06 with the other faux-material textures.) */
  /* "Three ways we work" (homepage, D2 2026-10-06): flat media-led cards. A
     real still on top, then the label, the copy and a text link. Radius stays
     inside the 2-4px rule; no icons or clip art. */
  .ways{display:grid;grid-template-columns:minmax(0,1fr);gap:var(--s4);}
  @media(min-width:760px){.ways{grid-template-columns:repeat(3,minmax(0,1fr));}}
  .way{background:var(--ground-2);border-radius:var(--r-md);overflow:hidden;
    display:flex;flex-direction:column;}
  .way img{display:block;width:100%;height:auto;aspect-ratio:16/9;object-fit:cover;}
  .way-body{padding:var(--s5);display:flex;flex-direction:column;gap:var(--s2);flex:1;}
  .way h3{margin:0;font-family:var(--display);font-size:var(--f-h3);font-weight:700;
    letter-spacing:var(--t-head);line-height:1.15;}
  .way p{margin:0;font-size:var(--f-body);color:var(--ink-2);line-height:1.55;}
  .way-go{margin-top:auto;padding-top:var(--s2);display:inline-flex;align-items:center;
    min-height:24px;font-size:var(--f-sm);font-weight:650;color:var(--orange-text);
    text-decoration:none;}
  .way-go:hover{text-decoration:underline;}

  .csi{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:var(--s3);
    margin-bottom:var(--s4);}
  .csi > div{background:var(--ground-2);border-radius:var(--r-sm);padding:var(--s5);}
  .csi h3{margin:0 0 var(--s2);font-family:var(--mono);font-size:var(--f-micro);
    letter-spacing:var(--t-caps);text-transform:uppercase;color:var(--orange-text);font-weight:600;}
  /* the outcome column carries the secondary hue so results read apart from setup */
  .csi div:nth-child(3) h3{color:var(--cyan-text);}
  .csi p{margin:0;font-size:var(--f-body);color:var(--ink-2);line-height:1.55;}

  /* Ruled ledger, not bordered cards: same technique as the hero .stats row
     (gap:1px on a --line background, each cell its own --ground fill), so a
     row of proof numbers reads as one connected figure instead of a stack of
     separate boxes. This used to be individually padded/backgrounded .panel
     cards, which is exactly the "default look" the six rules elsewhere on
     this sheet exist to avoid; .op is shared across every case page's stat
     row and the packages page, so fixing it here fixes all of them at once. */
  .ops{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:1px;
    background:var(--line);margin-bottom:var(--s4);}
  .op{background:var(--ground);padding:var(--s4);display:flex;flex-direction:column;gap:var(--s1);
    transition:background var(--ease);}
  .op:hover{background:var(--ground-2);}
  .op .n{font-size:var(--f-h3);font-weight:700;letter-spacing:-.012em;color:var(--cyan-text);
    font-family:var(--display);line-height:1.1;}
  .op .k{font-size:var(--f-micro);letter-spacing:.06em;text-transform:uppercase;color:var(--ink-3);
    font-family:var(--mono);}

  /* /our-work "More results": dated proof from three more accounts, ruled like
     the other ledgers (gap:1px on --line) rather than three boxed cards */
  .proofs{display:grid;grid-template-columns:minmax(0,1fr);gap:1px;background:var(--line);}
  @media(min-width:900px){.proofs{grid-template-columns:repeat(3,minmax(0,1fr));}}
  .proof{background:var(--ground);padding:var(--s5);display:flex;flex-direction:column;
    gap:var(--s2);}
  .proof h3{margin:0;font-family:var(--display);font-size:var(--f-h4);font-weight:700;
    letter-spacing:var(--t-head);line-height:1.2;}
  .proof .who{margin:0;font-size:var(--f-sm);color:var(--ink-3);}
  .proof .pm{margin:var(--s2) 0 0;display:flex;flex-direction:column;gap:2px;}
  .proof .pn{font-family:var(--display);font-size:var(--f-h2);font-weight:700;
    color:var(--orange-text);letter-spacing:-.012em;line-height:1.05;
    font-variant-numeric:tabular-nums;}
  .proof .pl{font-size:var(--f-micro);letter-spacing:.06em;text-transform:uppercase;
    color:var(--ink-3);font-family:var(--mono);}
  .proof p{margin:0;font-size:var(--f-body);color:var(--ink-2);line-height:1.55;}
  .proof .when{margin-top:auto;padding-top:var(--s3);border-top:1px solid var(--line);
    font-family:var(--display);font-variant-caps:all-small-caps;letter-spacing:.05em;
    font-size:var(--f-sm);color:var(--cyan-text);}

  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(288px,1fr));gap:var(--s5);}
  .spot{background:var(--panel);border-radius:var(--r-md);
    overflow:hidden;display:flex;flex-direction:column;}
  .spot video{width:100%;display:block;background:#000;aspect-ratio:16/9;object-fit:cover;}
  /* Click-to-play YouTube spots. Poster and button only until clicked, see
     MOTION_JS (h): the iframe is swapped in on click, never loaded before. */
  .ytspot{position:relative;aspect-ratio:16/9;background:#000;cursor:pointer;overflow:hidden;}
  .ytspot img{width:100%;height:100%;display:block;object-fit:cover;}
  .ytspot iframe{width:100%;height:100%;display:block;border:0;}
  .ytplay{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:52px;
    height:52px;border-radius:50%;background:rgba(20,23,26,.72);border:none;color:#fff;
    display:flex;align-items:center;justify-content:center;cursor:pointer;
    transition:background var(--ease),transform var(--ease);}
  .ytplay svg{margin-left:2px;}
  .ytspot:hover .ytplay{background:var(--orange);transform:translate(-50%,-50%) scale(1.06);}
  .spot .meta{padding:var(--s4);display:flex;flex-direction:column;gap:var(--s1);}
  .spot .sc{font-family:var(--display);font-variant-caps:all-small-caps;letter-spacing:.06em;
    font-size:var(--f-sm);color:var(--orange-text);}
  .spot .nm{font-size:var(--f-h4);font-weight:600;letter-spacing:var(--t-head);}
  /* --ink-2, not --ink-3: the card is --panel, and --ink-3 on it is 4.09:1 */
  .spot .du{font-family:var(--mono);font-size:var(--f-sm);color:var(--ink-2);}

  /* Ruled ledger, same technique as .stats/.ops: gap:1px on a --line fill
     reads as one strip of proof rather than seven boxes.
     2026-10-06: a grid with minmax(0,1fr) columns, not flex-wrap. The 7-across
     flex row had about 2px of slack at 1440 (each cell's min-content was 150px
     against a 152px basis), so a slightly wider face (font-display:optional
     can leave the Arial Black fallback in place) pushed the seventh reel onto
     its own row inside a grey box, and on phones 2-per-row left the seventh
     centred between grey filler. minmax(0,1fr) columns can never wrap. Below
     1100px the top reel (.is-top, the breakout) takes a full-width row and the
     other six fill an even 2x3 (phones) or 3x2 (tablets), so no row is ever
     short. The old worry about grid stretching rows does not apply now that
     .rthumb is a fixed 44x74: stretched cells just keep the ledger even. */
  .reels{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1px;
    background:var(--line);margin-top:var(--s6);}
  .reel{display:flex;flex-direction:row;gap:10px;min-width:0;
    text-decoration:none;background:var(--ground);
    padding:var(--s4);transition:background var(--ease),box-shadow var(--ease);}
  .reel.is-top{grid-column:1/-1;}
  @media(min-width:560px){.reels{grid-template-columns:repeat(3,minmax(0,1fr));}}
  /* seven across from 1100px (cells about 150px); a little less side padding
     buys the text column the room the old flex row did not have. Narrower
     than that, seven cells drop under the content's own width, so the 1+3x2
     layout above holds until then. */
  @media(min-width:1100px){
    .reels{grid-template-columns:repeat(7,minmax(0,1fr));}
    .reel.is-top{grid-column:auto;}
    .reel{padding:var(--s4) var(--s3);}
  }
  /* inset, not a real border, so the highlight cannot shift the tight 1px
     ledger grid it sits in. Covers hover, keyboard focus and the moment of
     a click, not just mouseover. */
  .reel:hover,.reel:focus-visible,.reel:active{background:var(--ground-2);
    box-shadow:inset 0 0 0 2px var(--cyan-text);}
  .reel .rmeta{display:flex;flex-direction:column;justify-content:space-between;
    gap:var(--s1);min-width:0;}
  .reel .vnum{font-size:var(--f-h3);font-weight:700;letter-spacing:-.012em;color:var(--ink);
    font-family:var(--display);line-height:1.1;
    white-space:nowrap;}
  .reel.is-top .vnum{color:var(--orange-text);}
  /* a taste of the actual reel, not a real preview: fixed size, not a
     stretched one. Stretching it to match the text column's height
     (align-items:stretch, the flex/grid default) sounded right for lining
     its top up with the number and its bottom with the label, but every
     card in a row gets stretched to the tallest one regardless, and since
     width here is tied to height via aspect-ratio, one taller card in the
     row inflated every thumbnail's width right along with it. Fixed at
     44x74 (9:15.1, close enough) sidesteps that entirely. */
  .rthumb{width:44px;height:74px;border-radius:2px;flex:none;object-fit:cover;}
  .reel .l{font-size:var(--f-micro);letter-spacing:.06em;text-transform:uppercase;color:var(--ink-3);
    font-family:var(--mono);}

  /* label row above a grid of clips (the homepage "Commercial spots") */
  .shorts-head{display:flex;align-items:baseline;justify-content:space-between;gap:var(--s4);
    flex-wrap:wrap;margin:var(--s7) 0 var(--s4);}
  /* Written for the old title cards and kept because it is what gives the
     click-to-play spot button its 46x32 shape: it overrides the circle above. */
  .ytplay{position:absolute;left:50%;top:50%;width:46px;height:32px;margin:-16px 0 0 -23px;
    border-radius:8px;background:rgba(15,18,20,.72);transition:background var(--ease);}
  .ytplay::after{content:"";position:absolute;left:18px;top:9px;border-style:solid;
    border-width:7px 0 7px 12px;border-color:transparent transparent transparent #F2EFE9;}

  /* client wall: every mark is pre-rendered onto an identical canvas with equal
     optical ink area, so the grid spaces itself without per logo tuning. */
  .logos{display:grid;grid-template-columns:repeat(2,1fr);gap:var(--s7) var(--s6);}
  @media(min-width:560px){.logos{grid-template-columns:repeat(3,1fr);}}
  @media(min-width:900px){.logos{grid-template-columns:repeat(4,1fr);}}
  .logomark{display:block;}
  .logomark img{width:100%;height:auto;display:block;opacity:.82;
    transition:opacity var(--ease),transform var(--ease);}
  .logomark:hover img{opacity:1;transform:scale(1.04);}

  /* ---------- packages page ---------- */
  .band{margin-bottom:var(--s8);}
  .band-head{display:flex;flex-direction:column;gap:var(--s2);margin-bottom:0;}
  .band-head h2{font-size:var(--f-h2);}
  .band-head p{margin:0;color:var(--ink-2);font-size:var(--f-body);max-width:62ch;line-height:1.58;}
  /* this one lede only: the reels row right below it now runs the full
     .wrap width (7-across fix), and a 62ch paragraph above a full-width
     row read as narrow/awkward next to it. Every other .band-head keeps
     the 62ch measure. */
  .band-head.full-lede p{max-width:none;}

  /* 2026-08-24: bold pass. Each program group reads as a filed folder, a colored
     tab above a lighter body, rather than a plain heading. The cut top-right
     corner keeps it architectural instead of a soft rounded pill. Only three
     tones exist site wide (orange, teal, ink), so the three groups just cycle
     through them; a fourth group would repeat, not invent a new color.
     2026-08-25: the 1px margin read as a seam, not an overlap, so it looked
     like a flat label sitting on the box rather than a tab folded over it.
     The tab now sinks var(--s4) into the body and needs position+z-index to
     stay on top of it, since without that the body (later in the DOM, same
     stacking context) would paint over the bottom of the tab instead of
     the tab overlapping the body. The shadow sells the same depth cue the
     reference used. */
  .band-tab{display:inline-flex;align-items:center;color:#fff;font-family:var(--display);
    font-weight:900;letter-spacing:-.01em;font-size:var(--f-h3);padding:var(--s3) var(--s6) var(--s3) var(--s5);
    clip-path:polygon(0 0,calc(100% - 22px) 0,100% 100%,0 100%);margin-bottom:calc(var(--s4) * -1);
    line-height:1.15;
    position:relative;z-index:1;box-shadow:0 10px 18px -10px rgba(0,0,0,.4);}
  /* 2026-10-06: the two bright tabs carry ink, not white. White on the cyan
     was 2.61:1 (axe color-contrast, fails AA even as large text) and white on
     the orange only 3.71:1. Ink is 6.89:1 on cyan and 4.84:1 on orange, so
     both pass AA at any size, they stay a matched pair, and it is the same
     ink-on-orange the site's CTAs already use. The ink tab keeps white. */
  .band-tab.t-orange{background:var(--orange);color:#14171A;}
  .band-tab.t-cyan{background:var(--cyan);color:#14171A;}
  .band-tab.t-ink{background:var(--ink);}
  .band-body{background:var(--ground-2);border-radius:0 var(--r-lg) var(--r-lg) var(--r-lg);
    padding:var(--s6) var(--s5) var(--s5);}
  .band-body > p{margin:0 0 var(--s5);color:var(--ink-2);font-size:var(--f-body);
    max-width:62ch;line-height:1.58;}
  .band-tab.t-orange ~ .band-body{border-top:3px solid var(--orange);}
  .band-tab.t-cyan ~ .band-body{border-top:3px solid var(--cyan);}
  .band-tab.t-ink ~ .band-body{border-top:3px solid var(--ink);}
  /* auto-fill, not auto-fit: since 2026-10-06 the groups hold one, two and
     three tiers, and with auto-fit a lone card stretched across the whole band
     and read as a banner, not a price. auto-fill keeps the empty tracks, so a
     card is the same width in every group (three tracks at desktop). min()
     keeps a narrow phone from overflowing the 280px floor. */
  .pkgs{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(280px,100%),1fr));
    gap:var(--s4);}
  .pkg{background:var(--ground);border:1px solid var(--line);border-radius:var(--r-md);
    padding:var(--s6) var(--s5);display:flex;flex-direction:column;gap:var(--s4);position:relative;}
  .pkg .tier{font-family:var(--display);font-variant-caps:all-small-caps;letter-spacing:.06em;
    font-size:var(--f-lede);color:var(--cyan-text);}
  .pkg .pname{font-size:var(--f-h4);font-weight:650;letter-spacing:var(--t-head);line-height:1.25;}
  .priceline{display:flex;align-items:baseline;gap:var(--s2);}
  .pkg .price{font-size:var(--f-price);font-weight:700;letter-spacing:-.035em;
    color:var(--orange-text);font-family:var(--mono);line-height:1;}
  .pkg .per{font-size:var(--f-sm);color:var(--ink-3);}
  .pkg ul{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:var(--s3);}
  .pkg li{font-size:var(--f-body);color:var(--ink-2);padding-left:22px;position:relative;
    line-height:1.5;}
  .pkg li::before{content:"+";position:absolute;left:0;top:0;color:var(--cyan-text);
    font-family:var(--mono);font-size:var(--f-sm);}
  .pkg .shoot{font-size:var(--f-sm);color:var(--ink);font-weight:600;
    border-top:1px solid var(--line);padding-top:var(--s3);}
  /* a full width header strip, not a corner tag: the label is a sentence and at
     62% width it wrapped to two lines and collided with the tier name. It is in
     normal flow, pulled out to the card edges with negative margins equal to the
     card padding, rather than absolutely positioned over a padding guess: at
     1440 in a 360px card the label runs to two lines, which the old fixed
     20px allowance could not hold. */
  .pkg .best{display:block;margin:calc(var(--s6) * -1) calc(var(--s5) * -1) 0;
    background:var(--orange);color:#14171A;
    font-size:var(--f-micro);font-weight:700;letter-spacing:.06em;text-transform:uppercase;
    padding:var(--s2) var(--s4);border-radius:var(--r-sm) var(--r-sm) 0 0;text-align:center;
    line-height:1.35;}
  .pkg:has(.best){border-color:rgba(var(--orange-rgb),.4);}

  /* the constant, stated before the tiers so the tiers are easier to read */
  /* flat since 2026-10-06 (was a concrete-plaster photo with shadowed white
     text on it) */
  .always{background:var(--ground-2);border:1px solid var(--line);border-radius:var(--r-md);
    padding:var(--s6) var(--s5);margin-bottom:var(--s8);}
  /* D6: the "what you are actually buying" block is a flat ink panel; .on-ink
     re-themes its heading, copy and the four benefit cards (--panel becomes a
     dark card, --cyan-text the bright cyan). The steps block and the tiers
     stay on warm white. */
  .always.on-ink{background:#14171A;border-color:#14171A;}
  .always h2{margin:0 0 var(--s2);font-size:var(--f-h4);font-weight:650;letter-spacing:var(--t-head);
    color:var(--ink);}
  .always .sub2{margin:0 0 var(--s5);font-size:var(--f-body);color:var(--ink-2);max-width:68ch;
    line-height:1.58;}

  /* the four benefits: numeral led, so the block reads as a designed grid rather
     than four paragraphs in boxes */
  .benefits{display:grid;grid-template-columns:repeat(auto-fit,minmax(228px,1fr));gap:var(--s3);}
  .benefit{background:var(--panel);border-radius:var(--r-sm);
    padding:var(--s5);display:flex;flex-direction:column;gap:var(--s2);}
  .benefit .bn{font-family:var(--mono);font-size:var(--f-h2);font-weight:700;line-height:1;
    color:var(--cyan-text);letter-spacing:var(--t-display);align-self:flex-start;
    border-bottom:2px solid var(--cyan);padding-bottom:var(--s2);margin-bottom:var(--s1);}
  .benefit h3{margin:0;font-size:var(--f-h4);font-weight:650;letter-spacing:var(--t-head);}
  .benefit p{margin:0;font-size:var(--f-body);color:var(--ink-2);line-height:1.55;}

  /* the two engines, side by side, each with a diagram of how it actually works.
     This was the hardest idea on the page and it used to be one long paragraph. */
  .engines{display:grid;grid-template-columns:1fr;gap:var(--s4);}
  @media(min-width:760px){.engines{grid-template-columns:1fr 1fr;}}
  .engine{background:var(--ground-2);border:1px solid var(--line);border-radius:var(--r-md);
    padding:var(--s5);display:flex;flex-direction:column;gap:var(--s3);}
  .engine.is-two{border-color:rgba(var(--orange-rgb),.30);}
  .engine .etag{font-family:var(--mono);font-size:var(--f-micro);letter-spacing:var(--t-caps);
    text-transform:uppercase;color:var(--cyan-text);}
  .engine.is-two .etag{color:var(--orange-text);}
  .engine h3{margin:0;font-size:var(--f-h3);font-weight:700;letter-spacing:var(--t-head);}
  .edia{width:100%;height:auto;display:block;margin:var(--s1) 0;}
  .engine p{margin:0;font-size:var(--f-body);color:var(--ink-2);line-height:1.55;}
  /* --ink-2, not --ink-3: the panel is --ground-2, and --ink-3 on it is 4.32:1 */
  .engine .ewhere{font-family:var(--mono);font-size:var(--f-micro);letter-spacing:.06em;
    text-transform:uppercase;color:var(--ink-2);border-top:1px solid var(--line);
    padding-top:var(--s3);margin-top:auto;}
  .engine.is-two .ewhere{color:var(--orange-text);}

  /* onboarding strip (D8): one ruled row of six on desktop, a compact
     numbered list on phones */
  .ob{list-style:none;margin:var(--s5) 0 0;padding:0;display:grid;
    grid-template-columns:minmax(0,1fr);gap:1px;background:var(--line);}
  @media(min-width:900px){.ob{grid-template-columns:repeat(6,minmax(0,1fr));}}
  .ob li{background:var(--ground);padding:var(--s3) var(--s4);display:grid;
    grid-template-columns:2.4em minmax(0,1fr);column-gap:var(--s2);row-gap:2px;align-items:baseline;}
  @media(min-width:900px){.ob li{display:flex;flex-direction:column;gap:var(--s1);padding:var(--s4);}}
  .ob-n{font-family:var(--display);font-weight:700;color:var(--orange-text);font-size:var(--f-sm);
    font-variant-numeric:tabular-nums;}
  .ob-t{font-weight:650;font-size:var(--f-body);color:var(--ink);line-height:1.3;}
  .ob-d{grid-column:2;font-size:var(--f-sm);color:var(--ink-2);line-height:1.45;}

  .steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:var(--s3);}
  .step2{background:var(--panel);border-radius:var(--r-sm);
    padding:var(--s5);}
  .step2 span{font-family:var(--mono);font-size:var(--f-micro);letter-spacing:var(--t-caps);
    text-transform:uppercase;color:var(--cyan-text);}
  .step2 h3{margin:var(--s2) 0 var(--s1);font-size:var(--f-h4);font-weight:650;
    letter-spacing:var(--t-head);}
  .step2 p{margin:0;font-size:var(--f-body);color:var(--ink-2);line-height:1.55;}

  .incl{background:var(--ground-2);border:1px solid var(--line);border-radius:var(--r-md);
    padding:var(--s6) var(--s5);display:flex;flex-direction:column;gap:var(--s4);}
  .incl h3{margin:0;font-size:var(--f-h4);font-weight:650;letter-spacing:var(--t-head);}
  .incl-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:var(--s5);}
  .incl-grid div p{margin:var(--s1) 0 0;font-size:var(--f-body);color:var(--ink-2);line-height:1.55;}
  .incl-grid div span{font-family:var(--mono);font-size:var(--f-micro);letter-spacing:var(--t-caps);
    text-transform:uppercase;color:var(--cyan-text);}

  /* full bleed banner video, breaks the wrap to run edge to edge */
  .flush{padding:0;}
  .banner{display:block;width:100vw;max-width:100vw;margin-left:calc(50% - 50vw);
    background:#000;aspect-ratio:16/9;object-fit:cover;}
  /* Purely ambient: nothing about this video is meant to be clicked. Without
     this, the YouTube iframe still owns its own click-to-pause and, once
     paused, a channel/share/watch-later overlay that leaves the site, and no
     URL param (controls=0 included) suppresses that. pointer-events:none
     means no click or tap can ever reach the iframe's own UI at all. */
  iframe.banner{pointer-events:none;border:0;
    /* Same fix as .herobg-clip, 2026-10-06: the iframe is oversized by the
       chrome margin top and bottom and pulled back with equal negative
       margins, so its flow height is still exactly 56.25vw (no shift when it
       replaces the placeholder) and .bannerwrap's overflow:hidden clips
       YouTube's title strip and bottom chrome. 6.75vw is 12% of the
       picture height, matching the hero. */
    aspect-ratio:auto;height:calc(56.25vw + 2 * max(var(--yt-chrome), 6.75vw));
    margin-top:calc(-1 * max(var(--yt-chrome), 6.75vw));
    margin-bottom:calc(-1 * max(var(--yt-chrome), 6.75vw));}
  .banner img{width:100%;height:100%;display:block;object-fit:cover;}
  /* the poster carries width/height for CLS; height:auto lets aspect-ratio:16/9
     size it rather than the height attribute's raw pixel value */
  img.banner{height:auto;}
  /* #yt-poster is a SIBLING of #yt-banner, not a child: the IFrame API
     replaces #yt-banner outright once it creates the player (see SOLO_JS),
     so a poster nested inside it would vanish the instant the iframe shows
     up, well before the video is actually playing. YouTube shows its own
     title/uploader card the whole time a video is cueing/buffering with no
     param to suppress it (see the comment above), so the poster stays
     layered on top and only fades once PlayerState actually reports
     PLAYING, masking that card instead of fighting it. */
  .posterlay{position:absolute;top:0;left:0;z-index:2;transition:opacity .5s ease;
    cursor:pointer;}
  .posterlay.is-hidden{opacity:0;pointer-events:none;}
  /* small, italic and pushed right: reads as a caption/annotation on the
     film rather than a section label competing with the ones below it. */
  .bannercap{padding:var(--s5) 0 var(--s1);display:flex;flex-wrap:wrap;
    justify-content:flex-end;gap:var(--s2) var(--s5);align-items:baseline;
    font-style:italic;}
  .bannercap .eyebrow{font-size:var(--f-micro);}
  .bannercap .who{font-size:var(--f-micro);color:var(--ink-2);}
  .bannercap .who strong{color:var(--ink);font-weight:600;}
  /* no section-break rule under this one: it sits right under a full
     bleed video, not a normal content gap, so the usual hairline read as
     a wall between them. */
  section.no-rule::before{content:none;}

  /* ---------- homepage ---------- */
  /* the two doors off the apex: the work, and the way to buy it */
  .doors{display:grid;grid-template-columns:1fr;gap:var(--s4);}
  @media(min-width:760px){.doors{grid-template-columns:1fr 1fr;}}
  .door{background:var(--panel);border:1px solid var(--line);border-radius:var(--r-md);
    padding:var(--s6) var(--s5);display:flex;flex-direction:column;gap:var(--s2);
    text-decoration:none;color:inherit;
    transition:border-color var(--ease),background var(--ease),transform var(--ease);}
  .door:hover{border-color:rgba(var(--orange-rgb),.4);background:var(--ground-2);transform:translateY(-2px);}
  /* D7, 2026-10-06: the two doors sit on a full-bleed footage still (the
     Quality fleet frame from the brand film) under a dark scrim, replacing
     the old wood-siding photo. A real <img> (lazy, intrinsic size) rather
     than a CSS background, so it costs nothing until it is near the
     viewport and cannot shift layout. The cards keep their own light panel,
     so legibility never depends on the footage. */
  .doors-section{position:relative;overflow:hidden;background:#14171A;padding:var(--s9) 0;}
  .doors-bg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:0;}
  .doors-section::after{content:"";position:absolute;inset:0;z-index:0;
    background:rgba(20,23,26,.5);}
  .doors-section > .wrap{position:relative;z-index:1;}

  .door .tier{font-family:var(--mono);font-size:var(--f-micro);letter-spacing:var(--t-caps);
    text-transform:uppercase;color:var(--cyan-text);}
  .door h3{margin:0;font-size:var(--f-h2);font-weight:700;letter-spacing:var(--t-head);}
  .door p{margin:0;font-size:var(--f-body);color:var(--ink-2);line-height:1.55;}
  .door .go{margin-top:var(--s2);font-size:var(--f-sm);font-weight:650;color:var(--orange-text);}

  .cta{display:inline-flex;align-items:center;gap:var(--s2);background:var(--orange);color:#14171A;
    border-radius:var(--r-pill);padding:14px var(--s5);font-size:var(--f-body);font-weight:650;
    text-decoration:none;transition:filter var(--ease),transform var(--ease);}
  .cta:hover{filter:brightness(1.08);transform:translateY(-1px);}
  .cta.ghost{background:transparent;color:var(--orange-text);border:1px solid rgba(var(--orange-rgb),.4);}
  .ctarow{display:flex;flex-wrap:wrap;gap:var(--s3);align-items:center;margin-top:var(--s6);}
  .ctanote{font-size:var(--f-sm);color:var(--ink-3);}

  /* ---------- team page ---------- */
  /* a headshot stands in for authority the way a case study still does elsewhere,
     so the placeholders keep the frame that will hold the real photo rather than
     collapsing to a name and title alone. */
  .portrait{background:var(--ground-2);border:1px solid var(--line);border-radius:var(--r-lg);
    display:flex;align-items:center;justify-content:center;overflow:hidden;color:var(--ink-3);}
  .portrait svg{width:30%;height:30%;}
  .portrait img{width:100%;height:100%;object-fit:cover;display:block;}

  .leads{display:grid;grid-template-columns:1fr;gap:var(--s6);margin-bottom:var(--s8);}
  @media(min-width:680px){.leads{grid-template-columns:1fr 1fr;gap:var(--s7);}}
  .lead .portrait{aspect-ratio:3/4;margin-bottom:var(--s4);}
  .lead h3{margin:0;font-size:var(--f-h3);font-family:var(--display);font-weight:650;
    letter-spacing:var(--t-head);}
  .lead .rtitle{display:block;margin-top:2px;font-family:var(--mono);font-size:var(--f-micro);
    letter-spacing:var(--t-caps);text-transform:uppercase;color:var(--orange-text);}
  .lead p{margin:var(--s3) 0 0;color:var(--ink-2);font-size:var(--f-body);line-height:1.6;
    max-width:52ch;}

  /* fixed nine, so explicit breakpoint columns rather than auto-fill, the same
     reasoning as .reels and .logos elsewhere on the site */
  .roster{display:grid;grid-template-columns:repeat(2,1fr);gap:var(--s5) var(--s4);}
  @media(min-width:560px){.roster{grid-template-columns:repeat(3,1fr);}}
  .member .portrait{aspect-ratio:1/1;margin-bottom:var(--s3);}
  .member h3{margin:0;font-size:var(--f-body);font-family:var(--display);font-weight:600;
    letter-spacing:var(--t-head);}
  .member .rtitle{display:block;margin-top:1px;font-family:var(--mono);font-size:var(--f-micro);
    letter-spacing:var(--t-caps);text-transform:uppercase;color:var(--ink-3);}
  /* Optional crew bio. Sizes come from the same tokens .lead p uses, one step
     down, so a filled card and an empty one still sit on the same grid. */
  .member .mbio{margin:var(--s2) 0 0;font-size:var(--f-sm);line-height:1.5;
    color:var(--ink-2);}

  .skip{position:absolute;left:-9999px;top:0;background:var(--orange);color:#14171A;
    padding:var(--s3) var(--s4);border-radius:0 0 var(--r-sm) 0;z-index:99;font-weight:600;}
  .skip:focus{left:0;}

  footer{padding:var(--s8) 0 var(--s6);position:relative;overflow:hidden;}
  footer::before{content:"";position:absolute;top:0;left:0;right:0;height:1px;z-index:2;
    background:linear-gradient(90deg,rgba(var(--orange-rgb),.55) 0%,rgba(var(--cyan-rgb),.42) 42%,
      rgba(226,224,218,.55) 78%,rgba(226,224,218,0) 100%);}
  footer > .wrap{position:relative;z-index:1;}
  footer p{margin:0;color:var(--ink-2);font-size:var(--f-body);}
  /* site_footer(): the line and its two actions on the left, the four
     destinations on the right from 760px, credentials and copyright on a
     ruled row underneath. Every link is at least 44px tall. */
  .foot{display:grid;grid-template-columns:minmax(0,1fr);gap:var(--s6);}
  @media(min-width:760px){.foot{grid-template-columns:minmax(0,1fr) auto;align-items:end;}}
  footer .foot-line{font-size:var(--f-h2);color:var(--ink);margin:0 0 var(--s5);max-width:20ch;}
  .foot-actions{display:flex;flex-wrap:wrap;align-items:center;gap:var(--s3) var(--s5);}
  .foot-mail{display:inline-flex;align-items:center;min-height:44px;font-size:var(--f-body);}
  .foot-nav{display:flex;flex-wrap:wrap;gap:0 var(--s5);}
  .foot-nav a{display:inline-flex;align-items:center;min-height:44px;font-family:var(--display);
    font-variant-caps:all-small-caps;letter-spacing:.06em;font-size:var(--f-lede);
    color:var(--ink);text-decoration:none;transition:color var(--ease);}
  .foot-nav a:hover{color:var(--orange-text);}
  .foot-meta{display:flex;flex-wrap:wrap;justify-content:space-between;gap:var(--s2) var(--s5);
    margin-top:var(--s7);padding-top:var(--s4);border-top:1px solid var(--line);}
  footer .foot-meta p{font-size:var(--f-sm);color:var(--ink-3);}
</style>"""

# CSS above is a plain string, not an f-string (it holds far too many literal
# {braces} to make that safe). If it ever needs an asset URL, patch it in after
# the fact via a placeholder, as the retired texture images used to be.
# 2026-10-06: those textures (plaster, siding, blueprint, marker strokes, the
# manila folders) and the Caveat font that only the marker sticker used were
# retired for a flat look; footage is the only texture now.

# Full width, gently scrolling data traces, the same technique as the wave
# background on verysilly.dev: smooth repeating bezier tiles inside an
# oversized path, translated by exactly one tile width with SMIL
# animateTransform so the loop has no seam. Two flowing lines carry the
# motion; a third, straighter trace with on-curve markers reads as an
# actual metric being plotted rather than decoration, which is the point for
# a company that sells measurable results.
#
# The third trace originally carried just two markers, 800 units apart on a
# 1200-wide viewBox. One (cx=0) spent its entire drift cycle (the
# animateTransform below runs 0 to -400) sitting at negative x, off the left
# edge of every viewBox slice, and depending on a given container's crop
# width the other could drift out too, which is what "the dots are missing
# in multiple spots across the site" (2026-08-27) turned out to be. Now six,
# every 400 units (the path's own repeat interval) from -400 to 1600, so
# several stay inside any reasonably cropped window at any point in the
# cycle instead of relying on just one or two surviving the crop by luck.
SPLAT_SVG = ('<svg class="splat" viewBox="0 0 1200 400" preserveAspectRatio="xMidYMid slice" '
    'xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
    '<path d="M-600,170 C-510,142 -390,142 -300,170 C-210,198 -90,198 0,170 '
    'C90,142 210,142 300,170 C390,198 510,198 600,170 C690,142 810,142 900,170 '
    'C990,198 1110,198 1200,170 C1290,142 1410,142 1500,170 C1590,198 1710,198 1800,170" '
    'stroke="rgba(240,72,32,.16)" stroke-width="1.5" fill="none">'
    '<animateTransform attributeName="transform" type="translate" from="0,0" to="-600,0" '
    'dur="26s" repeatCount="indefinite"/></path>'
    '<path d="M-800,262 C-680,246 -520,246 -400,262 C-280,278 -120,278 0,262 '
    'C120,246 280,246 400,262 C520,278 680,278 800,262 C920,246 1080,246 1200,262 '
    'C1320,278 1480,278 1600,262 C1720,246 1880,246 2000,262" '
    'stroke="rgba(0,176,200,.11)" stroke-width="1" fill="none">'
    '<animateTransform attributeName="transform" type="translate" from="0,0" to="-800,0" '
    'dur="34s" repeatCount="indefinite"/></path>'
    '<g>'
    '<path d="M-400,222 C-340,208 -260,208 -200,222 C-140,236 -60,236 0,222 C60,208 140,208 200,222 '
    'C260,236 340,236 400,222 C460,208 540,208 600,222 C660,236 740,236 800,222 C860,208 940,208 1000,222 '
    'C1060,236 1140,236 1200,222 C1260,208 1340,208 1400,222 C1460,236 1540,236 1600,222" '
    'stroke="rgba(240,72,32,.13)" stroke-width=".8" fill="none"/>'
    '<circle cx="-400" cy="222" r="3" fill="none" stroke="rgba(240,72,32,.22)" stroke-width="1"/>'
    '<circle cx="0" cy="222" r="3" fill="none" stroke="rgba(240,72,32,.22)" stroke-width="1"/>'
    '<circle cx="400" cy="222" r="3" fill="none" stroke="rgba(240,72,32,.22)" stroke-width="1"/>'
    '<circle cx="800" cy="222" r="3" fill="none" stroke="rgba(240,72,32,.22)" stroke-width="1"/>'
    '<circle cx="1200" cy="222" r="3" fill="none" stroke="rgba(240,72,32,.22)" stroke-width="1"/>'
    '<circle cx="1600" cy="222" r="3" fill="none" stroke="rgba(240,72,32,.22)" stroke-width="1"/>'
    '<animateTransform attributeName="transform" type="translate" from="0,0" to="-400,0" '
    'dur="18s" repeatCount="indefinite"/></g>'
    '</svg>')

# Under prefers-reduced-motion the CSS animation kill switch (see @media block above)
# only catches CSS animations, not SMIL. This strips the animateTransform elements so
# the traces render as a single still frame instead, same outcome as .rv elsewhere.
SPLAT_JS = """<script>
(function(){
  if(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches){
    var els = document.querySelectorAll('.splat animateTransform');
    for(var i = 0; i < els.length; i++){ els[i].remove(); }
  }
})();
</script>"""

SOLO_JS = """<script>
/* Only one video may play at a time. Starting one stops every other and
   rewinds it to the beginning. The play event does not bubble, so this
   listens on the capture phase and catches every video on the page,
   including any added later. */
(function(){
  document.addEventListener('play', function(e){
    var started = e.target;
    if(!started || started.tagName !== 'VIDEO') return;
    /* the muted banner has no audio to clash with, so it neither stops others
       nor gets stopped by them */
    if(started.hasAttribute('data-ambient')) return;
    var all = document.getElementsByTagName('video');
    for(var i = 0; i < all.length; i++){
      var v = all[i];
      if(v === started || v.hasAttribute('data-ambient')) continue;
      if(!v.paused) v.pause();
      if(v.currentTime !== 0){
        try { v.currentTime = 0; } catch(err) { /* not seekable yet */ }
      }
    }
  }, true);

  /* Ambient YouTube backgrounds: autoplay muted, only once actually on
     screen (nothing loads up front, not even the IFrame API script), pause
     on scroll out, resume in place on return, and loop back to their
     data-start mark rather than to zero. None of that is native <video>
     behavior, so it cannot reuse the seek/ended/loadedmetadata logic above;
     the YouTube IFrame Player API has its own equivalents (seekTo,
     onStateChange, playVideo/pauseVideo). Two instances share this as of
     2026-08-26 (the Quality banner, the homepage hero video), hence a
     function rather than one-off code: each gets its own player/observer
     closure, but only one IFrame API script tag ever loads. */
  function loadApiThen(cb){
    if(window.YT && window.YT.Player){ cb(); return; }
    var prev = window.onYouTubeIframeAPIReady;
    window.onYouTubeIframeAPIReady = function(){ if(prev) prev(); cb(); };
    if(!document.getElementById('yt-iframe-api')){
      var tag = document.createElement('script');
      tag.id = 'yt-iframe-api';
      tag.src = 'https://www.youtube.com/iframe_api';
      document.head.appendChild(tag);
    }
  }

  /* iOS Safari: a tap on the poster always worked (confirmed), autoplay
     alone never did, even with Low Power Mode off. That is consistent
     with WebKit's documented autoplay policy treating a *scripted*
     playVideo() call (what a dynamically created player always does)
     more strictly than media that was autoplay-eligible from the
     page's own initial load. Since a real gesture reliably unlocks it,
     the workaround is to treat the visitor's first touch/scroll/click
     ANYWHERE on the page, not just on the video, as that gesture, and
     retry play then. Almost everyone touches or scrolls within the
     first second on a phone, so this reads as autoplay in practice. */
  var pendingPlayers = [];
  function unlockPendingPlayers(){
    pendingPlayers.forEach(function(p){
      if(p && p.getPlayerState && p.getPlayerState() !== YT.PlayerState.PLAYING){
        p.playVideo();
      }
    });
  }
  ['touchstart', 'scroll', 'click'].forEach(function(evt){
    document.addEventListener(evt, unlockPendingPlayers, {passive: true, once: true});
  });

  function setupAmbient(bannerId, posterId, sizeClass){
    var bannerEl = document.getElementById(bannerId);
    if(!bannerEl || !('IntersectionObserver' in window)) return;
    var videoId = bannerEl.getAttribute('data-yt');
    var start = parseFloat(bannerEl.getAttribute('data-start')) || 0;
    var player = null;

    function makePlayer(){
      player = new YT.Player(bannerEl, {
        videoId: videoId,
        width: '100%', height: '100%',
        /* youtube-nocookie.com, not youtube.com: the regular domain shares
           cookies with a signed-in YouTube account, so on this machine
           (signed into the channel these videos are uploaded to) the
           account's own "always show captions" preference was leaking into
           the embed and overriding cc_load_policy below. The privacy
           domain has no such session to inherit a preference from. */
        host: 'https://www.youtube-nocookie.com',
        playerVars: {autoplay: 1, mute: 1, controls: 0, rel: 0, modestbranding: 1,
          playsinline: 1, disablekb: 1, fs: 0, cc_load_policy: 0, iv_load_policy: 3, start: start},
        events: {
          onReady: function(e){
            /* the API replaces bannerEl with a new iframe rather than filling
               it, so the sizing class and .is-playing (the push-in) have to
               move to that iframe, and the observer has to start watching it
               instead. width/height:'100%' above stops the API defaulting to
               a fixed 640x390 box; stripping the attributes here too is belt
               and braces, since the stylesheet's own sizing for sizeClass is
               what should actually govern the rendered size, not either of
               these. */
            var ifr = e.target.getIframe();
            ifr.classList.add(sizeClass);
            ifr.removeAttribute('width');
            ifr.removeAttribute('height');
            io.unobserve(bannerEl);
            io.observe(ifr);
            e.target.playVideo();
            pendingPlayers.push(e.target);
          },
          onStateChange: function(e){
            /* masks YouTube's own title/uploader card, which has no
               suppressing param. Chose speed over a guarantee here: the
               poster hides the instant PLAYING first fires, no wait, which
               is a real (small) risk the card is still mid-fade at that
               exact moment on a slow/cold load. A safe delay was tried and
               reliably hid it, but cost several real seconds on every load,
               which mattered more. It still re-covers immediately if
               playback drops out of PLAYING (buffering blip, scroll pause,
               a loop restart). */
            var poster = document.getElementById(posterId);
            if(e.data === YT.PlayerState.PLAYING){
              e.target.getIframe().classList.add('is-playing');
              if(poster) poster.classList.add('is-hidden');
            } else if(poster){
              poster.classList.remove('is-hidden');
            }
            if(e.data === YT.PlayerState.ENDED){ e.target.seekTo(start, true); e.target.playVideo(); }
          }
        }
      });
    }

    var io = new IntersectionObserver(function(entries){
      entries.forEach(function(en){
        if(en.isIntersecting){
          if(!player){ loadApiThen(makePlayer); }
          else if(player.playVideo) player.playVideo();
        } else if(player && player.pauseVideo){
          player.pauseVideo();               /* pauseVideo, not stopVideo: keeps position */
        }
      });
    }, {threshold: 0.2});
    io.observe(bannerEl);

    /* fallback for autoplay silently refused (iOS Low Power Mode does this
       a lot, and gives no error to detect, the player just never leaves
       "cued"): tapping the poster always works, since a real user gesture
       bypasses autoplay restrictions everywhere. Also covers the player
       not existing yet at tap time (rare, since the observer above
       usually creates it immediately, but the hero could in principle be
       tapped before it scrolls into view on some layouts). */
    var posterEl = document.getElementById(posterId);
    if(posterEl){
      posterEl.addEventListener('click', function(){
        if(player && player.playVideo) player.playVideo();
        else loadApiThen(makePlayer);
      });
    }
  }

  setupAmbient('yt-banner', 'yt-poster', 'banner');
  setupAmbient('hero-yt', 'hero-yt-poster', 'herobg');
})();
</script>"""


NAV_JS = """<script>
(function(){
  var n = document.getElementById('nav');
  if(!n) return;
  function upd(){ n.classList.toggle('is-stuck', (window.pageYOffset || 0) > 8); }
  upd();
  window.addEventListener('scroll', upd, {passive:true});

  /* mobile menu: only meaningful below 620px (see .navtoggle in the
     stylesheet), but the listeners are harmless no-ops above that since
     the button is display:none there and never gets clicked. */
  var toggle = document.getElementById('navtoggle');
  var links = document.getElementById('navlinks');
  if(!toggle || !links) return;

  function setOpen(open){
    links.classList.toggle('is-open', open);
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
  }
  toggle.addEventListener('click', function(){
    setOpen(!links.classList.contains('is-open'));
  });
  /* closing on a link click matters here specifically: same-page anchors
     (e.g. a footer link to /our-work/#a1) don't trigger navigation, so
     without this the menu would stay open covering the page after tapping
     one */
  links.addEventListener('click', function(e){
    if(e.target.tagName === 'A') setOpen(false);
  });
  document.addEventListener('click', function(e){
    if(!links.classList.contains('is-open')) return;
    if(!n.contains(e.target)) setOpen(false);
  });
  document.addEventListener('keydown', function(e){
    if(e.key === 'Escape') setOpen(false);
  });
})();
</script>"""


# /our-work/ only. The case cards are plain links to #a1, #handyman and #allheart.
# This opens the matching write-up in .case-panels (each is the markup a case page
# used to be) and scrolls to it, on load and on every hash change, so the
# homepage's /our-work/#a1-style links land on the right case too.
CASES_JS = """<script>
(function(){
  var panels = document.getElementById('case-panels');
  if(!panels) return;
  var sections = [].slice.call(panels.children);
  var cards = [].slice.call(document.querySelectorAll('.cgcard'));
  function open(){
    var id = (location.hash || '').slice(1);
    if(!id || !sections.some(function(s){ return s.id === id; })) return;
    sections.forEach(function(s){ s.classList.toggle('is-active', s.id === id); });
    cards.forEach(function(c){ c.classList.toggle('is-active', c.getAttribute('href') === '#' + id); });
    var t = document.getElementById(id);
    /* one tick so display:none -> block lands before measuring position */
    setTimeout(function(){ t.scrollIntoView({behavior: 'smooth', block: 'start'}); }, 60);
  }
  /* a click on the card that is already open does not change the hash */
  cards.forEach(function(c){
    c.addEventListener('click', function(){ if(c.getAttribute('href') === location.hash) open(); });
  });
  open();
  window.addEventListener('hashchange', open);
})();
</script>"""


MOTION_JS = """<script>
(function(){
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* (a) scroll reveals ---------------------------------------------------- */
  if(!reduce && 'IntersectionObserver' in window){
    var SEL = '.sec-head,.cgcard,.benefit,.engine,.pkg,.csi > div,.way,.op,.spot,.reel,' +
              '.step2,.door,.always,.incl,.pn,.band-head,.lead,.member';
    var vh = window.innerHeight || 800;
    var targets = [].slice.call(document.querySelectorAll(SEL)).filter(function(e){
      /* nothing above the fold gets a reveal: that space belongs to the hero
         entrance, and hiding it would sit on the critical render path.
         .benefit and .step2 are exempt: both sit close under a page hero, so
         on a lot of real viewport heights they'd land above this cutoff and
         never animate at all, which is the opposite of what was asked for
         (they should always slide in on scroll). Neither is ever the LCP
         element, so skipping the filter for them does not reintroduce the
         render-path problem the filter guards against. */
      if(e.classList.contains('benefit') || e.classList.contains('step2')) return true;
      return e.getBoundingClientRect().top > vh * 0.9;
    });
    targets.forEach(function(e){ e.classList.add('rv'); });
    var io = new IntersectionObserver(function(entries){
      entries.forEach(function(en){
        if(!en.isIntersecting) return;
        var e = en.target;
        var sibs = [].slice.call(e.parentNode.children).filter(function(c){
          return c.classList && c.classList.contains('rv');
        });
        var i = Math.max(0, Math.min(sibs.indexOf(e), 4));   /* stagger caps at 5 */
        /* .benefit and .step2 get their own, slower cadence than the generic
           60ms ripple used everywhere else: 500ms between cards, splitting
           the difference between that 60ms and the fully-cumulative "wait
           for the previous card's .5s slide plus a half second pause"
           version this replaced, which read as too slow. */
        var isSlow = e.classList.contains('benefit') || e.classList.contains('step2');
        var step = isSlow ? 500 : 60;
        e.style.willChange = 'opacity, transform';
        e.style.transitionDelay = (i * step) + 'ms';
        e.classList.add('rv-in');
        io.unobserve(e);                                     /* never re-animate */
        setTimeout(function(){ e.style.willChange = 'auto'; },
          (isSlow ? 500 : 700) + i * step);
      });
    }, {threshold: 0.15, rootMargin: '0px 0px -10% 0px'});
    targets.forEach(function(e){ io.observe(e); });
  }

  /* (b) count up ---------------------------------------------------------- */
  var nums = [].slice.call(document.querySelectorAll('.stat .n, .op .n, .reel .vnum'));
  if(nums.length && !reduce && 'IntersectionObserver' in window){
    /* thousands separators count too: a figure like +1,680 (or any price on
       the ladder) used to parse as 1 followed by ",680", so it counted 0 to 1
       in front of a frozen tail. The comma is stripped to count and put back
       when formatting; the last frame restores the original text exactly. */
    var parse = function(s){
      var m = String(s).match(/^([^0-9.]*)([0-9][0-9,]*(?:\.[0-9]+)?)(.*)$/);
      if(!m) return null;
      var raw = m[2].replace(/,/g, '');
      return {pre: m[1], val: parseFloat(raw), post: m[3], dp: (raw.split('.')[1]||'').length,
              comma: m[2].indexOf(',') > -1, orig: String(s)};
    };
    var fmt = function(p, v){
      var t = v.toFixed(p.dp);
      if(p.comma) t = Number(t).toLocaleString('en-US',
        {minimumFractionDigits: p.dp, maximumFractionDigits: p.dp});
      return p.pre + t + p.post;
    };
    var nio = new IntersectionObserver(function(entries){
      entries.forEach(function(en){
        if(!en.isIntersecting) return;
        var el = en.target; nio.unobserve(el);
        var p = parse(el.textContent); if(!p) return;
        /* reserve the final width first so counting cannot reflow the card */
        el.style.minWidth = el.getBoundingClientRect().width + 'px';
        el.style.display = 'inline-block';
        var t0 = null, dur = 1200;
        function step(ts){
          if(t0 === null) t0 = ts;
          var k = Math.min((ts - t0) / dur, 1);
          var eased = 1 - Math.pow(1 - k, 3);          /* ease out cubic */
          el.textContent = fmt(p, p.val * eased);
          if(k < 1) requestAnimationFrame(step);
          else el.textContent = p.orig;
        }
        requestAnimationFrame(step);
      });
    }, {threshold: 0.4});
    nums.forEach(function(e){ nio.observe(e); });
  }

  /* (c) hover to preview, pointer devices only ---------------------------- */
  var fine = window.matchMedia && window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  if(fine && !reduce){
    [].slice.call(document.querySelectorAll('.spot video')).forEach(function(v){
      var card = v.closest('.spot') || v.parentNode;
      card.addEventListener('mouseenter', function(){
        if(v.hasAttribute('controls') && !v.paused) return;
        v.muted = true; v.playsInline = true;
        var pr = v.play(); if(pr && pr.catch) pr.catch(function(){});
      });
      card.addEventListener('mouseleave', function(){
        if(v.paused) return;
        v.pause();
        try { v.currentTime = 0; } catch(err){}
      });
    });
  }

  /* (d) hero film push in: as of 2026-08-26 the banner is a YouTube embed, so
     "started playing" is a YT.Player onStateChange event, not a <video>
     'playing' event; that's handled in SOLO_JS, next to the rest of the
     banner's ambient-play logic, not here. */

  /* (h) YouTube spots, click to play. Plain iframe swap, not the IFrame Player
     API: nothing about this needs programmatic control, so there is nothing to
     load until someone actually clicks. youtube-nocookie.com sets no tracking
     cookie until playback starts. Only one plays at a time; starting a second
     puts the first back to its poster, same rule SOLO_JS applies to the
     self-hosted videos.
     controls=0 is load bearing, not cosmetic: YouTube's native control bar
     carries its own logo button that opens youtube.com in a new tab, and an
     ended video falls through to a related-videos screen that does the same.
     loop=1 with playlist set to the video's own id is the documented trick
     for looping a single video (loop=1 alone only loops playlists), which
     also means it never reaches that ended state at all. */
  var ytSpots = [].slice.call(document.querySelectorAll('.ytspot'));
  if(ytSpots.length){
    var ytReset = null;
    ytSpots.forEach(function(el){
      var poster = el.innerHTML;
      var id = el.getAttribute('data-yt');
      var title = el.getAttribute('data-title') || '';
      if(!id) return;
      function reset(){ el.innerHTML = poster; }
      el.addEventListener('click', function(){
        if(ytReset && ytReset !== reset) ytReset();
        el.innerHTML = '<iframe src="https://www.youtube-nocookie.com/embed/' + id +
          '?autoplay=1&rel=0&modestbranding=1&playsinline=1&controls=0&disablekb=1&' +
          'loop=1&playlist=' + id + '" title="' + title + '" '+
          'allow="autoplay; encrypted-media; picture-in-picture" '+
          'loading="lazy"></iframe>';
        ytReset = reset;
      });
    });
  }
})();
</script>"""


FORM_JS = """<script>
(function(){
  var f = document.getElementById('cform');
  if(!f) return;
  var btn = document.getElementById('cbtn');
  var status = document.getElementById('fstatus');
  var LABEL = btn.textContent;

  /* Where enquiries go. Substituted from FORM_TO at build time so the address
     lives in exactly one place, next to EMAIL at the top of this file. */
  var FORM_ENDPOINT = '__FORM_ENDPOINT__';

  function wrap(el){ return el.closest('.fld') || el.closest('.budgets'); }
  function setErr(el, msg){
    var w = wrap(el); if(!w) return;
    var slot = w.querySelector('.ferr');
    if(msg){ w.classList.add('is-bad'); if(slot) slot.textContent = msg; }
    else { w.classList.remove('is-bad'); if(slot) slot.textContent = ''; }
  }
  function checkOne(el){
    if(el.name === 'website') return true;
    if(!el.required) return true;
    var v = (el.value || '').trim();
    if(!v){ setErr(el, 'This one we do need.'); return false; }
    if(el.type === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v)){
      setErr(el, 'That email address does not look right.'); return false;
    }
    setErr(el, ''); return true;
  }

  /* validate on blur, not on keystroke: flagging an email as invalid while it is
     still being typed is the single most irritating thing a form can do */
  [].slice.call(f.elements).forEach(function(el){
    if(!el.name || el.type === 'submit') return;
    el.addEventListener('blur', function(){ checkOne(el); });
    el.addEventListener('input', function(){
      var w = wrap(el);
      if(w && w.classList.contains('is-bad')) checkOne(el);
    });
    if(el.type === 'radio'){
      el.addEventListener('change', function(){ setErr(el, ''); });
    }
  });

  /* Nothing a visitor typed should ever be lost because a delivery service is
     down, unreachable, or not yet switched on. Whatever the failure, the answers
     are already in their hands: this hands back a one-tap mail link with every
     field prefilled, so the enquiry still arrives, just through their own mail
     client. It is a worse experience than the form and a far better one than
     "try again later", which is where six days of enquiries went in Aug 2026. */
  function failover(data, serverMsg){
    var order = ['name','email','company','city','trade','phone','budget','message'];
    var labels = {name:'Name', email:'Email', company:'Company', city:'City',
                  trade:'Trade', phone:'Phone', budget:'Budget', message:'Notes'};
    var lines = [];
    order.forEach(function(k){
      if(data[k]) lines.push(labels[k] + ': ' + data[k]);
    });
    var href = 'mailto:__FORM_TO__'
      + '?subject=' + encodeURIComponent(data._subject || 'Project enquiry')
      + '&body=' + encodeURIComponent(lines.join('\\n'));

    status.className = 'fstatus is-err';
    status.innerHTML = (serverMsg ? serverMsg + ' ' : 'That did not send from here. ')
      + '<a href="' + href + '">Send it as an email instead</a>'
      + ', everything you typed is already filled in.';
    btn.disabled = false; btn.textContent = LABEL;
  }

  f.addEventListener('submit', function(e){
    e.preventDefault();
    status.className = 'fstatus'; status.textContent = '';

    var bad = null;
    [].slice.call(f.elements).forEach(function(el){
      if(el.type === 'radio' && el.name === 'budget'){
        if(!f.querySelector('input[name=budget]:checked')){
          setErr(el, 'Pick the closest one.'); if(!bad) bad = el;
        }
        return;
      }
      if(!checkOne(el) && !bad) bad = el;
    });
    if(bad){ bad.focus(); return; }

    var data = {};
    [].slice.call(f.elements).forEach(function(el){
      if(!el.name) return;
      if(el.type === 'radio'){ if(el.checked) data[el.name] = el.value; }
      else data[el.name] = el.value;
    });

    btn.disabled = true; btn.textContent = 'Sending...';

    /* The site moved to GitHub Pages on 2026-08-28. Pages is static hosting and
       cannot execute the Vercel function at /api/contact, so every POST came
       back 405 and not one enquiry was delivered until 2026-09-03. FORM_ENDPOINT
       is a receiver that works on static hosting. The subject line is still
       built here rather than server side, so the inbox stays sortable in exactly
       the same shape it was before: Company (City) - Trade - Budget. */
    data._subject = (data.company || 'Enquiry')
      + ' (' + (data.city || '') + ') - '
      + (data.trade || '') + ' - ' + (data.budget || '');
    data._replyto = data.email;
    data._captcha = 'false';
    /* the honeypot was checked server side by api_contact.js, which no longer
       runs: hand the same field to the receiver's own trap instead, so a bot
       still gets a 200 and never learns it was caught */
    data._honey = data.website || '';

    fetch(FORM_ENDPOINT, {
      method: 'POST',
      headers: {'content-type': 'application/json', 'accept': 'application/json'},
      body: JSON.stringify(data)
    }).then(function(r){
      return r.json().then(function(j){ return {ok: r.ok, body: j}; },
                          function(){ return {ok: r.ok, body: {}}; });
    }).then(function(res){
      /* the receiver reports success as the string "true", the old function
         reported it as a boolean ok: accept either */
      if(res.ok && (res.body.ok || String(res.body.success) === 'true')){
        /* replace the form rather than clearing it: a blank form after submitting
           reads as "that did not work" and people send it twice */
        var done = document.createElement('div');
        done.className = 'fdone';
        done.setAttribute('tabindex', '-1');
        done.innerHTML = '<h3>Got it, thank you.</h3><p>That is in our inbox now. ' +
          'You will hear back within one business day, from a human, ' +
          'about your market specifically.</p>';
        f.parentNode.replaceChild(done, f);
        done.focus();
        return;
      }
      if(res.body && res.body.errors){
        Object.keys(res.body.errors).forEach(function(k){
          var el = f.elements[k]; if(el) setErr(el.length ? el[0] : el, res.body.errors[k]);
        });
      }
      failover(data, res.body && res.body.error);
    }).catch(function(){
      failover(data, null);
    });
  });
})();
</script>"""

# FORM_JS is a plain string, not an f-string: the JS it holds is full of braces.
# The two values that have to come from Python are substituted here instead.
FORM_JS = FORM_JS.replace("__FORM_ENDPOINT__", f"https://formsubmit.co/ajax/{FORM_TO}")
FORM_JS = FORM_JS.replace("__FORM_TO__", FORM_TO)
assert "__FORM_ENDPOINT__" not in FORM_JS, "form endpoint placeholder was not substituted"
assert "__FORM_TO__" not in FORM_JS, "form failover address was not substituted"


def spot(fn, sc, nm, du, yt=None):
    """Renders a case-study clip two ways. With `yt` set it's a click-to-play
    YouTube spot: a poster and a play button, nothing else, until someone
    actually clicks (see the (h) section of MOTION_JS for the iframe swap) so
    it costs nothing on the page until then and never leaves the site to
    play. Without `yt` it's the original self-hosted video, kept as a
    fallback for clips not yet uploaded to YouTube."""
    if yt:
        poster_path = os.path.join(S, "post_yt", yt + ".webp")
        poster = asset(poster_path, "image/webp")
        return (f'<article class="spot">'
                f'<div class="ytspot" data-yt="{yt}" data-title="{nm}">'
                f'<img src="{poster}"{dims(poster_path)} alt="" loading="lazy">'
                f'<button type="button" class="ytplay" aria-label="Play {nm}">{PLAY_ICON}</button>'
                f'</div>'
                f'<div class="meta"><span class="sc">{sc}</span><span class="nm">{nm}</span>'
                f'<span class="du">{du}</span></div></article>')
    poster = asset(os.path.join(P, fn.replace(".mp4", ".jpg")), "image/jpeg")
    src = asset(os.path.join(V, fn), "video/mp4")
    return (f'<article class="spot">'
            f'<video controls playsinline preload="none" poster="{poster}" '
            f'src="{src}"></video>'
            f'<div class="meta"><span class="sc">{sc}</span><span class="nm">{nm}</span>'
            f'<span class="du">{du}</span></div></article>')

# All 17 clips are on YouTube as of 2026-08-26 (last batch: ah3 "The Quote"
# plus all six handyman). The fn/yt pairing (fn set, yt None) still works as a
# fallback to the original self-hosted video if a future clip needs pulling
# from YouTube and re-hosting locally instead.
allheart = [(None,"01","Breaking Furniture 101","0:30","zaCFfVetfFI"),
    (None,"02","The Upsell","0:15","METoxqCqkn8"),
    (None,"03","The Snake","0:30","TPDZ-OvRNgc"),(None,"04","Obsessed","0:30","Nz5hbi-0x94"),
    (None,"05","Meet The Carlas","0:30","A6gc-YCl94E"),(None,"06","The Influencer","0:30","YLK9ftd4Dx4"),
    (None,"07","The Auctioneer","0:30","aEtwPZAdKPo"),(None,"08","Ghosted","0:30","npKJfYqjljs"),
    (None,"09","Universe is Talking","0:30","COEbLTt42FI"),(None,"10","The Quote","0:42","unFCPL3Cw5o")]

handyman = [(None,"01","It's Way Hotter","0:30","E5qZHk03snY"),
    (None,"02","Don't Worry, You'll Get Used To It","0:30","4fUdKqK9cPM"),
    (None,"03","Sleeping On The Job","0:30","S3Hkreuykvs"),(None,"04","Father Vs AC","0:15","IppFw7pSssA"),
    (None,"05","A Space Odyssey","0:56","AfkePSa8XLU"),(None,"06","Where's That Coming From","0:30","Fodjt_xKovE")]

# The banner is a three minute film, on YouTube as of 2026-08-26 (see SOLO_JS
# for the ambient autoplay/loop-to-1:14 handling, which replaces #yt-banner
# with the actual player once it scrolls into view). Inlining it as base64
# would push the artifact build past its 16MB ceiling regardless, so that
# copy just shows the poster frame; only the live site plays anything.
_bposter = asset(f"{P}/quality1.jpg", "image/jpeg")
if MODE == "web":
    BANNER_MEDIA = (f'<div class="bannerwrap"><div class="banner" id="yt-banner" '
                    f'data-yt="m3HEWS9qMTM" data-start="74"></div>'
                    f'<img class="banner posterlay" id="yt-poster" src="{_bposter}"'
                    f'{dims(f"{P}/quality1.jpg")} loading="lazy" '
                    f'alt="Quality Heating Cooling Plumbing Electrical website banner film"></div>')
else:
    BANNER_MEDIA = (f'<div class="bannerwrap"><img class="banner" src="{_bposter}" '
                    f'alt="Quality Heating Cooling Plumbing Electrical website banner film"></div>')

# thumb ids are 2026-08-26 crops of screenshots the client sent (Facebook serves
# no public og:image/thumbnail without auth, see the case-visuals note in
# CLAUDE.md), cropped to cut the recording UI (mute icon, caption, byline) and
# down to a tiny 9x15 next to the view count, not a real preview image.
a1 = [("1320266993606759","623K","The attic",1,"a1r1"),("1682905312990623","428K","Reel 02",0,"a1r2"),
      ("2529519850833764","410K","Reel 03",0,"a1r3"),("1515832853025994","312K","Reel 04",0,"a1r4"),
      ("1367347965291754","195K","Reel 05",0,"a1r5"),("1665126741451677","162K","Reel 06",0,"a1r6"),
      ("1718428669171616","134K","Reel 07",0,"a1r7")]

# built once so it can be dropped into any page. The portfolio uses it as a case,
# the pricing page uses it as evidence sitting next to a price.
A1_REELS = "\n".join(
    # .rmeta (number + label) sits beside .rthumb, not around it, so the
    # thumbnail can stretch (align-items:stretch, see .reel) to match the
    # full height of the text column, top of the number to bottom of the
    # label. The count-up script (MOTION_JS) does el.textContent = ... on
    # whatever it targets, every animation frame, which would silently
    # delete the thumbnail if it were still nested inside the element the
    # count-up rewrites; targeting .reel .vnum specifically, a text-only
    # span with no img in it, is what keeps that safe.
    f'<a class="reel{" is-top" if t else ""}" href="https://www.facebook.com/reel/{i}">'
    f'<div class="rmeta"><span class="vnum">{v}</span><span class="l">{l}</span></div>'
    f'<img class="rthumb" src="{asset(f"{P}/{th}.webp", "image/webp")}"{dims(f"{P}/{th}.webp")} '
    f'alt="" loading="lazy"></a>'
    for i, v, l, t, th in a1
)

CLIENT_LOGOS = [
    ("logo_allheart.png",    "All Heart Heating and Cooling"),
    ("logo_veterans.png",    "Veterans AC PHX"),
    ("logo_acplus.png",      "AC Plus Heating and Cooling"),

    ("logo_a1.png",          "A1 Air Conditioning and Heating"),
    ("logo_icomfort.png",    "iComfort Heating and Air"),
    ("logo_goodguy.png",     "Good Guy Plumbing"),
    ("logo_premier.png",     "Premier Heating and Air"),

    ("logo_martins.png",     "Martins A/C and Electric"),
    ("logo_stellar.png",     "Stellar Garage Doors"),
    ("logo_quality.png",     "Quality Heating Cooling Plumbing and Electric"),
    ("logo_airone.png",      "Air One"),

    ("logo_blanchards.png",  "Blanchards Refrigeration"),
    ("logo_neobuilders.png", "Neo Builders"),
    ("logo_aduinsider.png",  "ADU Insider"),
    ("logo_doggone.png",     "Doggone Good Heating and Cooling"),
]


def logomark(fn, name):
    """WebP at the canvas size every mark is rendered onto, with width and height
    declared so the grid reserves its space before the image arrives."""
    src = asset(os.path.join(S, "logos_webp", fn.replace(".png", ".webp")), "image/webp")
    return (f'<div class="logomark">'
            f'<img src="{src}" alt="{name}" width="500" height="200" '
            f'loading="lazy" decoding="async"></div>')


# The roster stat on the homepage counts the wall rather than restating a number
# by hand, so adding or removing a logo can never leave the two disagreeing.
ROSTER_COUNT = len(CLIENT_LOGOS)


# A1's reels live on Facebook, which serves no public thumbnail, so the page gets a
# chart of the real view counts instead of invented artwork. The shape is the story:
# one breakout and a tail that still clears 100k.
def a1_chart(dark=False, decorative=False):
    """dark: light labels for an ink ground (the /our-work lead card).
    decorative: aria-hidden and no <text> at all, for places where the numbers are
    already real text beside it. The no-text part matters: an inline SVG whose
    <text> is laid out on first paint requested Archivo 700 early enough that it
    missed font-display:optional's window, and Chrome then rendered every
    Archivo 700 heading on the page in the Arial Black fallback (measured on
    /our-work, 2026-10-06). The labelled chart inside the case write-up is
    display:none until opened, so it never races."""
    ink, sub, base, tlab = (("#F2EFE9", "#A8A29A", "#33383D", "#F04820") if dark
                            else ("#14171A", "#6B747C", "#E2E0DA", "#B93412"))
    data = [("623K", 623, 1), ("428K", 428, 0), ("410K", 410, 0), ("312K", 312, 0),
            ("195K", 195, 0), ("162K", 162, 0), ("134K", 134, 0)]
    W, H, PAD, BASE = 700, 224, 18, 176
    bw, gap = 66, 22
    bars, labels = "", ""
    for i, (lab, v, top) in enumerate(data):
        h = round(v / 623 * 132)
        x = PAD + i * (bw + gap)
        y = BASE - h
        col = "#F04820" if top else "#00B0C8"
        op = "1" if top else ".55"
        bars += (f'<rect x="{x}" y="{y}" width="{bw}" height="{h}" rx="3" fill="{col}" '
                 f'opacity="{op}"/>')
        labels += (f'<text x="{x + bw/2:.0f}" y="{y - 8}" text-anchor="middle" fill="{ink}" '
                   f'font-size="15" font-family="Archivo,sans-serif" '
                   f'font-weight="700">{lab}</text>')
        labels += (f'<text x="{x + bw/2:.0f}" y="{BASE + 20}" text-anchor="middle" fill="{sub}" '
                   f'font-size="11" font-family="Archivo,sans-serif" font-weight="700" '
                   f'letter-spacing="1">{"0" + str(i+1)}</text>')
    # the 100k line the whole tail clears
    ty = BASE - round(100 / 623 * 132)
    lx = PAD + 7 * (bw + gap) - gap + 10          # just past the last bar
    thresh = (f'<line x1="{PAD}" y1="{ty}" x2="{lx - 6}" y2="{ty}" stroke="#F04820" '
              f'stroke-width="1" stroke-dasharray="4 4" opacity=".5"/>'
              f'<text x="{lx}" y="{ty + 4}" fill="{tlab}" font-size="11" '
              f'font-family="Archivo,sans-serif" font-weight="700" letter-spacing="1">100K</text>')
    a11y = ('aria-hidden="true"' if decorative else
            'role="img" aria-label="Seven A1 reels by view count, from 623,000 down to 134,000, '
            'every one of them above 100,000"')
    if decorative:
        labels = ""
        thresh = thresh[:thresh.index("<text")]
    return (f'<svg class="a1chart" viewBox="0 0 {W} {H}" {a11y}>'
            f'<line x1="{PAD}" y1="{BASE}.5" x2="{lx - 6}" y2="{BASE}.5" stroke="{base}" '
            f'stroke-width="1"/>{thresh}{bars}{labels}</svg>')


# ---- the three case studies, shown inline on /our-work/ --------------------

# Order here is the reading order everywhere: the carousel, its dots and the case
# panels below it. A1 leads because it is the one with numbers a home service
# owner can picture in their own market.
CASES = [
    dict(id="a1",       slug="a1-air-conditioning", name="A1 Air Conditioning", og=None,
         vertical="Home services", metric="2.26M", mlabel="Views in a market of one million",
         still=None, logo="logo_a1.png",
         blurb="An ongoing monthly engagement across their entire video distribution: organic "
               "social, paid and brand video.",
         desc="How a Tucson HVAC company with 9,200 followers built seven reels past 100,000 "
              "views, roughly 2.26 million views in a market of one million people."),
    dict(id="handyman", og="og-handyman.jpg", slug="handyman-dan", name="Handyman Dan",
         vertical="Home services", metric="12", mlabel="Markets deployed",
         still="hd5.jpg", logo=None,
         blurb="A six-spot package written and produced once, then licensed across twelve "
               "markets on twelve-month agreements.",
         desc="One production block, six spots, three cut lengths, deployed across twelve markets "
              "nationwide and licensed to twelve accounts."),
    dict(id="allheart", og="og-allheart.jpg", slug="all-heart", name="All Heart",
         vertical="Home services", metric="10", mlabel="Spots from one production block",
         still="ah1.jpg", logo="logo_allheart.png",
         blurb="A ten-spot comic campaign built on a single premise and shot in one block, so "
               "the cost lands once.",
         desc="Ten commercial spots written and produced in a single production block on one "
              "premise: the contractor you want versus the contractor you got."),
]
CASE_BY_ID = {c["id"]: c for c in CASES}


# The still each case card leads with. Handyman Dan uses its 1200px OG frame, which
# holds up at the card's 2x size; A1 has no still, so it gets the data panel.
CASE_TILE_STILL = {"handyman": f"{S}/og/og-handyman.jpg", "allheart": f"{P}/ah1.jpg"}


def case_tile(c, lead=False):
    """One card in the /our-work case grid (D5)."""
    metric = f'<span class="cg-metric"><b>{c["metric"]}</b><span>{c["mlabel"]}</span></span>'
    still = CASE_TILE_STILL.get(c["id"])
    if still:
        src = asset(still, "image/jpeg")
        art = (f'<span class="cg-art has-still"><img src="{src}"{dims(still)} alt="" '
               f'loading="lazy" decoding="async">{metric}</span>')
    else:
        art = (f'<span class="cg-art cg-data"><span class="cg-top">{metric}'
               f'<span class="cg-line">Seven reels past 100,000 views for a Tucson HVAC company '
               f'with 9,200 followers.</span></span>{a1_chart(dark=True, decorative=True)}</span>')
    return (f'<a class="cgcard{" is-lead" if lead else ""}" href="#{c["id"]}">{art}'
            f'<span class="cg-body"><span class="cg-vert">{c["vertical"]}</span>'
            f'<span class="cg-name">{c["name"]}</span>'
            f'<span class="cg-go">See the case &darr;</span></span></a>')


CASE_GRID = "\n".join(case_tile(c, lead=(i == 0)) for i, c in enumerate(CASES))






CASE_BODY = {}
CASE_BODY["a1"] = f"""<section id="a1"><div class="wrap">
  <div class="sec-head casehead">
    <p class="eyebrow">Case 01 &middot; Home services &middot; Reach</p>
    <h2 class="display">A1 Air Conditioning</h2>
    <div class="role"><span class="lbl">Our role</span><span class="pill">Video Distribution</span><span class="pill">Monthly Package</span></div>
    <p class="lede">An ongoing monthly engagement covering their entire video distribution: organic social,
    paid advertising and brand video. A Tucson HVAC company with 9,200 followers, now carrying
    <strong>seven reels past 100,000 views and three past 400,000</strong>, for roughly 2.26 million
    views in a market of one million people.</p>
  </div>

  <div class="csi">
    <div><h3>The challenge</h3><p>Local service advertising is interchangeable. Same vans, same promises,
      nothing anyone would repeat.</p></div>
    <div><h3>The solution</h3><p>Treat the service call as a premise. The best-performing spot frames a
      technician alone in a dark attic like the cold open of a horror film.</p></div>
    <div><h3>The impact</h3><p>1,100 shares on the lead reel. Audiences passed it along themselves, which is
      the premise working rather than the media budget.</p></div>
  </div>

  <div class="chartwrap">
    <p class="charttitle">Seven reels, by views. Every one of them clears 100,000.</p>
    {a1_chart()}
    <p class="chartnote">The lead reel frames a technician alone in a dark attic like the cold
    open of a horror film. It was shared 1,100 times, which is the shape of the whole account:
    one breakout carried by a premise, and a tail that still outperforms the market.</p>
  </div>

  <div class="reels">
{A1_REELS}
  </div>
</div></section>"""
CASE_BODY["handyman"] = f"""<section id="handyman"><div class="wrap">
  <div class="sec-head casehead">
    <p class="eyebrow">Case 02 &middot; Home services &middot; Scale</p>
    <h2 class="display">Handyman Dan</h2>
    <div class="role"><span class="lbl">Our role</span><span class="pill">Writer</span><span class="pill">Producer</span></div>
    <p class="lede">We wrote and produced a six-spot package once, then <strong>deployed it across twelve
    markets nationwide</strong> and licensed it to twelve accounts on twelve-month agreements.</p>
  </div>

  <div class="csi">
    <div><h3>The challenge</h3><p>Home service brands rarely commission real commercial work because they
      cannot picture what it looks like or what it returns.</p></div>
    <div><h3>The solution</h3><p>Build the package on spec across three cut lengths, so every placement is
      covered and the work can be evaluated as finished product rather than a pitch.</p></div>
    <div><h3>The impact</h3><p>One production, twelve markets, twelve accounts on annual agreements. The
      package earned back its cost many times over.</p></div>
  </div>

  <div class="ops">
    <div class="op"><span class="n">12</span><span class="k">Markets deployed</span></div>
    <div class="op"><span class="n">12</span><span class="k">Accounts licensed</span></div>
    <div class="op"><span class="n">12mo</span><span class="k">Agreement length</span></div>
    <div class="op"><span class="n">6</span><span class="k">Spots delivered</span></div>
    <div class="op"><span class="n">3</span><span class="k">Cut lengths</span></div>
  </div>

  <div class="grid">
{chr(10).join(spot(*s) for s in handyman)}
  </div>
</div></section>"""
CASE_BODY["allheart"] = f"""<section id="allheart"><div class="wrap">
  <div class="sec-head casehead">
    <p class="eyebrow">Case 03 &middot; Home services &middot; Campaign</p>
    <h2 class="display">All Heart</h2>
    <div class="role"><span class="lbl">Our role</span><span class="pill">Writer</span><span class="pill">Producer</span></div>
    <p class="lede">We wrote and produced a <strong>ten-spot campaign in a single production
    block</strong>. One premise carries the whole package: the contractor you want versus the
    contractor you got.</p>
  </div>

  <div class="csi">
    <div><h3>The challenge</h3><p>Fill a year of paid and organic inventory for a brand with no library and
      no appetite for repeat shoot days.</p></div>
    <div><h3>The solution</h3><p>Write one comic premise strong enough to sustain ten spots, then shoot the
      entire campaign in one block so the cost lands once.</p></div>
    <div><h3>The impact</h3><p>Ten finished spots from a single production, delivered complete and in scope.</p></div>
  </div>

  <div class="ops">
    <div class="op"><span class="n">10</span><span class="k">Spots delivered</span></div>
    <div class="op"><span class="n">1</span><span class="k">Production block</span></div>
    <div class="op"><span class="n">11</span><span class="k">Shot list sheets</span></div>
    <div class="op"><span class="n">100%</span><span class="k">Scope delivered</span></div>
  </div>

  <div class="grid">
{chr(10).join(spot(*s) for s in allheart)}
  </div>
</div></section>"""


# ---- more results, from the owners' pitch deck -----------------------------
# Owner approved 2026-10-06. Every figure is copied from the deck and written in
# English formats (the deck's screenshots used Portuguese ones: "509 mil" is 509K,
# "6.096" is 6,096). Rules that came with it: Be Right There's impressions are not
# called organic (that report was filtered organic and paid; its engagements were
# organic); the two unnamed clients and any reel from an account not named here
# are excluded; there are no logos for Be Right There or 4 Points, so none are
# drawn. The dates are real and double as the site's first recency signal; 4 Points
# came without dates, so it shows none rather than a guessed one.
PROOF = [
    dict(client="Be Right There Heating and Air", who="@beerightthereheatingair on Instagram",
         metric="982,880", mlabel="Views on one reel",
         line="Two more reels passed 316,000 views. From 1 to 23 Sep 2024, impressions rose "
              "282% and organic engagements 687% on the 23 days before.",
         when="Sep 2024 to Feb 2025"),
    dict(client="iComfort Heating and Air", who="@icomfort.hvac on Instagram",
         metric="+1,680", mlabel="Followers in under a year, all organic",
         line="From 290 followers on 27 Mar 2024 to 1,970 on 11 Mar 2025. Five TikTok posts "
              "from the same stretch drew between 16,518 and 150,282 views.",
         when="Mar 2024 to Mar 2025"),
    dict(client="4 Points", who="Home services",
         metric="509K", mlabel="Views on one post",
         line="Before us, eight posts drew 235 to 705 views each. In a sample of the same size "
              "since, posts reached 509K, 89.4K, 24.6K and 6,096 views.",
         when=""),
]


def proof_card(x):
    when = f'<p class="when">{x["when"]}</p>' if x["when"] else ""
    return (f'<article class="proof"><h3>{x["client"]}</h3><p class="who">{x["who"]}</p>'
            f'<p class="pm"><span class="pn">{x["metric"]}</span>'
            f'<span class="pl">{x["mlabel"]}</span></p>'
            f'<p>{x["line"]}</p>{when}</article>')


MORE_RESULTS = f"""<section id="more-results"><div class="wrap">
  <div class="sec-head">
    <p class="eyebrow">More results</p>
    <h2 class="display">Three more accounts, with the dates attached</h2>
    <p class="lede">Short form for three more home service companies, measured on their own
    accounts.</p>
  </div>
  <div class="proofs">
{chr(10).join(proof_card(x) for x in PROOF)}
  </div>
</div></section>"""


# The footer every page shares. It used to be hand copied five times and had
# shrunk to one sentence, a tiny "Contact" link and the meta line. Now it carries
# the primary CTA (through book(), so it follows cta_href() like every other
# conversion button), the email as a plain mailto text link (the one secondary
# path CLAUDE.md allows), the site's four destinations with 44px targets, the
# credentials line and a copyright. A page never links to itself here: the
# current page is left out of the nav, and on /contact the CTA is dropped too
# while it would only point back at the form on the same page.
FOOTER_LINKS = [("/our-work/", "Work", "work"), ("/packages/", "Packages", "packages"),
                ("/team/", "Team", "team"), ("/contact/", "Contact", "contact")]
YEAR = datetime.date.today().year


def site_footer(page=""):
    links = "".join(f'<a href="{h}">{label}</a>' for h, label, key in FOOTER_LINKS
                    if key != page)
    cta_is_here = page == "contact" and cta_href().startswith("/contact/")
    cta = "" if cta_is_here else book("Footer", "", "cta")
    return (f'<footer><div class="wrap">'
            f'<div class="foot">'
            f'<div class="foot-main">'
            f'<p class="display foot-line">Let&#39;s make something that travels.</p>'
            f'<div class="foot-actions">{cta}'
            f'<a class="foot-mail" href="mailto:{EMAIL}">{EMAIL}</a></div>'
            f'</div>'
            f'<nav class="foot-nav" aria-label="Footer">{links}</nav>'
            f'</div>'
            f'<div class="foot-meta">'
            f'<p>Los Angeles, CA &middot; Insured &middot; Working since 2019</p>'
            f'<p>&copy; {YEAR} Home Service Studios</p>'
            f'</div>'
            f'</div></footer>')


def logo_marquee():
    """The client wall as a continuous marquee. The track is duplicated because a
    translateX of -50% only loops seamlessly if the second half repeats the first.
    The second set is marked .dupe (and hidden from assistive tech), so the static
    grid used on phones and under reduced motion can drop it."""
    marks = "".join(logomark(*c) for c in CLIENT_LOGOS)
    dupe = (marks.replace('class="logomark"', 'class="logomark dupe"')
                 .replace('loading="lazy"', 'loading="lazy" aria-hidden="true"'))
    return (f'<div class="marquee"><div class="marquee-track">{marks}{dupe}</div></div>')



html = f"""<title>Selected work, Home Service Studios</title>
{FONT_CSS}
{CSS}
<a class="skip" href="#main">Skip to content</a>
{nav("work")}
<main id="main">
<div class="hero hero-dark">{SPLAT_SVG}<div class="wrap">
  <p class="eyebrow">Selected work &middot; Home Service Studios</p>
  <h1 class="display">Three clients.<br><span class="hl">Three kinds of proof.</span></h1>
  <p class="sub">From one HVAC company&#39;s feed to a spot package licensed across twelve
  markets. <strong>The approach does not change.</strong></p>
  <div class="stats">
    <a class="stat" href="#a1"><span class="case">A1 Air Conditioning</span><span class="n">2.26M</span><span class="k">One client, 7 reels</span></a>
    <a class="stat" href="#handyman"><span class="case">Handyman Dan</span><span class="n">12</span><span class="k">Markets deployed</span></a>
    <a class="stat" href="#allheart"><span class="case">All Heart</span><span class="n">10</span><span class="k">Spots delivered</span></a>
  </div>
  <div class="ctarow">
    {book("Project%20enquiry", "Start a project")}
    <a class="cta ghost" href="/packages/">Monthly packages</a>
  </div>
  {reassure("work")}
  <p class="ctanote" style="margin-top:16px;max-width:60ch;">Home Service Studios is run by its
  cofounders, filmmaker Craig Balog and film and television crew veteran Seth Yeager, out of a
  Marina del Rey office. Creative direction comes from Yoni Paz, who spent seven years across the
  creator economy, live streaming and social commerce before turning to commercial work.</p>
</div></div>

<section id="quality" class="flush">
  {BANNER_MEDIA}
  <div class="wrap"><div class="bannercap">
    <p class="eyebrow">Brand film</p>
    <span class="who"><strong>Quality Heating Cooling Plumbing Electrical</strong>, Tulsa.</span>
  </div></div>
</section>

<section class="no-rule on-ink"><div class="wrap">
  <div class="sec-head">
    <p class="eyebrow">Roster</p>
    <h2 class="display">Writing and production across home services nationwide</h2>
  </div>
  {logo_marquee()}
</div></section>

<section><div class="wrap">
  <div class="sec-head">
    <p class="eyebrow">Case studies</p>
    <h2 class="display">Three clients, three kinds of proof</h2>
  </div>
  <div class="cgrid">
{CASE_GRID}
  </div>
</div></section>

<div class="case-panels" id="case-panels">
{chr(10).join(CASE_BODY[c["id"]] for c in CASES)}
</div>

{MORE_RESULTS}

</main>

{site_footer("work")}
{actionbar()}
{SPLAT_JS}
{SOLO_JS}
{NAV_JS}
{MOTION_JS}
{CASES_JS}
"""

# ---- packages page --------------------------------------------------------

# ---- packages, rendered from data/packages.json --------------------------
# Every price on the site comes from that file. A build assertion below fails if a
# price string ever reappears in a template, which is how the home page and this
# page drifted apart in the first place.
PKG = json.loads(pathlib.Path(f"{S}/data/packages.json").read_text())
TIER = {x["id"]: x for x in PKG["tiers"]}
money = lambda n: "$" + format(n, ",")

# Every price-bearing phrase in the copy is derived from these, never typed: the
# cheapest and dearest tier, and how many programs there are, in words.
PRICE_MIN = min(t["price"] for t in PKG["tiers"])
PRICE_MAX = max(t["price"] for t in PKG["tiers"])
PROGRAMS_WORD = num_word(len(PKG["tiers"]))


def pkg_card(tid):
    """One tier card. The ad budget line is written from the tier's adSpend number,
    so the dollar figure lives in packages.json once. Since the 2026-10-06 price
    book there is no per-asset price, no application-only tier and no free month;
    the recommended strip is driven by the json (Silver, owner confirmed)."""
    c = TIER[tid]
    feats = list(c["features"])
    if c.get("adSpend"):
        feats.append(f"A {money(c['adSpend'])} monthly ad budget, managed by our team")
    lis = "".join(f"<li>{b}</li>" for b in feats)
    badge = (f'<span class="best">{c["recommendedLabel"]}</span>'
             if c.get("recommended") else "")
    return (f'<div class="pkg">'
            f'{badge}<span class="tier">{c["name"]}</span>'
            f'<span class="pname">{c["tagline"]}</span>'
            f'<div class="priceline"><span class="price">{money(c["price"])}</span>'
            f'<span class="per">per month</span></div>'
            f'<ul>{lis}</ul>'
            f'<div class="shoot">{c["camera"]}</div></div>')


# One tab color per group, in ascending commitment order. Only three tones exist
# site wide, so this is the whole rotation, not a sample of a larger palette.
BAND_TONE = {"you-supply": "t-cyan", "two-days": "t-orange", "four-days": "t-ink"}


def pkg_group(gid):
    g = next(x for x in PKG["groups"] if x["id"] == gid)
    cards = "".join(pkg_card(t) for t in g["tiers"])
    tone = BAND_TONE[gid]
    return (f'<div class="band"><span class="band-tab {tone}">{g["heading"]}</span>'
            f'<div class="band-body"><p>{g["subhead"]}</p>'
            f'<div class="pkgs">{cards}</div></div></div>')


def price_ladder():
    """The home page strip. Same source, so it cannot disagree with the tiers."""
    return "".join(
        f'<div class="op"><span class="n">{money(c["price"])}</span>'
        f'<span class="k">{c["name"]} &middot; {c["tagline"]}</span></div>'
        for c in PKG["tiers"])


# Two small diagrams for the packages page. The first is breadth: a lot of posts,
# familiarity rising slowly across all of them. The second is depth: fewer people,
# each one further along, narrowing to a booked job.
ENGINE_SHORT = ('<svg class="edia" viewBox="0 0 300 92" role="img" aria-label="Many small posts over time, with familiarity rising slowly across them"><line x1="6" y1="82.5" x2="294" y2="82.5" stroke="#E2E0DA" stroke-width="1"/><rect x="8.0" y="72" width="6" height="10" rx="1.5" fill="#00B0C8" opacity=".42"/><rect x="20.5" y="66" width="6" height="16" rx="1.5" fill="#00B0C8" opacity=".42"/><rect x="33.0" y="73" width="6" height="9" rx="1.5" fill="#00B0C8" opacity=".42"/><rect x="45.5" y="61" width="6" height="21" rx="1.5" fill="#00B0C8" opacity=".42"/><rect x="58.0" y="69" width="6" height="13" rx="1.5" fill="#00B0C8" opacity=".42"/><rect x="70.5" y="75" width="6" height="7" rx="1.5" fill="#00B0C8" opacity=".42"/><rect x="83.0" y="64" width="6" height="18" rx="1.5" fill="#00B0C8" opacity=".42"/><rect x="95.5" y="70" width="6" height="12" rx="1.5" fill="#00B0C8" opacity=".42"/><rect x="108.0" y="58" width="6" height="24" rx="1.5" fill="#00B0C8" opacity=".42"/><rect x="120.5" y="72" width="6" height="10" rx="1.5" fill="#00B0C8" opacity=".42"/><rect x="133.0" y="67" width="6" height="15" rx="1.5" fill="#00B0C8" opacity=".42"/><rect x="145.5" y="63" width="6" height="19" rx="1.5" fill="#00B0C8" opacity=".42"/><rect x="158.0" y="73" width="6" height="9" rx="1.5" fill="#00B0C8" opacity=".42"/><rect x="170.5" y="60" width="6" height="22" rx="1.5" fill="#00B0C8" opacity=".42"/><rect x="183.0" y="69" width="6" height="13" rx="1.5" fill="#00B0C8" opacity=".42"/><rect x="195.5" y="66" width="6" height="16" rx="1.5" fill="#00B0C8" opacity=".42"/><rect x="208.0" y="72" width="6" height="10" rx="1.5" fill="#00B0C8" opacity=".42"/><rect x="220.5" y="61" width="6" height="21" rx="1.5" fill="#00B0C8" opacity=".42"/><rect x="233.0" y="67" width="6" height="15" rx="1.5" fill="#00B0C8" opacity=".42"/><rect x="245.5" y="73" width="6" height="9" rx="1.5" fill="#00B0C8" opacity=".42"/><rect x="258.0" y="64" width="6" height="18" rx="1.5" fill="#00B0C8" opacity=".42"/><rect x="270.5" y="70" width="6" height="12" rx="1.5" fill="#00B0C8" opacity=".42"/><rect x="283.0" y="63" width="6" height="19" rx="1.5" fill="#00B0C8" opacity=".42"/><path d="M8,76 C90,72 156,56 292,14" fill="none" stroke="#F04820" stroke-width="2.5" stroke-linecap="round"/></svg>')

ENGINE_LONG = ('<svg class="edia" viewBox="0 0 300 92" role="img" aria-label="A narrowing funnel, from people searching down to a booked job"><rect x="28" y="8" width="244" height="14" rx="3" fill="#00B0C8" opacity=".26"/><rect x="62" y="30" width="176" height="14" rx="3" fill="#00B0C8" opacity=".40"/><rect x="96" y="52" width="108" height="14" rx="3" fill="#00B0C8" opacity=".58"/><rect x="124" y="74" width="52" height="14" rx="3" fill="#F04820" opacity="1"/></svg>')

# The owners' onboarding timeline (D8, 2026-10-06), facts only. It replaces the
# Terms grid's "When it starts" cell, which said the first production day lands
# three to four weeks after payment; the owners' figure is three to four weeks
# from sign-up to the first post.
ONBOARDING = "\n".join(
    f'      <li><span class="ob-n">{i:02d}</span><span class="ob-t">{t}</span>'
    + (f'<span class="ob-d">{d}</span>' if d else '') + '</li>'
    for i, (t, d) in enumerate([
        ("Strategy kickoff", ""),
        ("Agreement signed and first payment", ""),
        ("Content collection and scheduling", "Shoots are booked with 15 business days notice."),
        ("Production day", ""),
        ("Post-production", ""),
        ("First post live", "10 to 15 business days after the final production day."),
    ], 1))

PACKAGES_HTML = f"""<title>Monthly content packages</title>
{FONT_CSS}
{CSS}
<a class="skip" href="#main">Skip to content</a>
{nav("packages")}

<main id="main">
<div class="hero hero-dark">{SPLAT_SVG}<div class="wrap">
  <p class="eyebrow">Monthly packages &middot; Home Service Studios</p>
  <h1 class="display">Known and trusted <span class="hl">before they need you.</span></h1>
  <p class="sub">Nobody calls a home service company because they saw one good video. They call the
  company they already recognize, and that recognition is built over months, not in a month.
  <strong>This is a long play, and it only works if it actually runs.</strong> These packages exist
  to make it run without landing on your desk.</p>
  <div class="ctarow">
    {book("Monthly%20packages")}
    <a class="cta ghost" href="/our-work/">See the work first</a>
  </div>
  {reassure("packages")}
</div></div>

<section><div class="wrap">

  <div class="always on-ink">
    <h2>What you are actually buying</h2>
    <p class="sub2">Not leads. Anyone selling you leads from organic short form is guessing.
    Consistent short form reliably does four things, and all four compound.</p>
    <div class="benefits">
      <div class="benefit"><span class="bn">01</span><h3>Recognition</h3>
        <p>Whatever finally puts someone in the market, a breakdown, a move, a remodel they have
        been putting off, they reach for the name they already know. Being that name takes months
        of showing up in the same feeds.</p></div>
      <div class="benefit"><span class="bn">02</span><h3>Recruiting</h3>
        <p>Good people are harder to find than customers. They apply to the company that looks
        like somewhere worth working, and they decide that from your feed long before they ever
        send a resume.</p></div>
      <div class="benefit"><span class="bn">03</span><h3>Trust at the door</h3>
        <p>Someone who has already watched your team work is a different conversation from someone
        meeting you for the first time. You start past the part where they size you up.</p></div>
      <div class="benefit"><span class="bn">04</span><h3>Proof you are still around</h3>
        <p>Everyone looks you up before they call. A feed with two years behind it reads as a
        company that is busy and still here. A feed that stopped in 2023 reads as the opposite,
        and they will notice which one you are.</p></div>
    </div>
  </div>

  <div class="band">
    <div class="band-head">
      <h2 class="display">Two different ways this works</h2>
      <p>Every package below is built on the first one. The second works the other way around,
      and it is what Platinum adds on top of Gold.</p>
    </div>
    <div class="engines">
      <div class="engine">
        <span class="etag">Engine 01 &middot; Short form</span>
        <h3>Attention</h3>
        {ENGINE_SHORT}
        <p>Aimed at someone scrolling past who was not looking for you. Each post does little on
        its own. Together, across months, they build the four things above. Genuinely not
        attributable to leads, which is why we do not sell it that way.</p>
        <span class="ewhere">Included in every package</span>
      </div>
      <div class="engine is-two">
        <span class="etag">Engine 02 &middot; Long form</span>
        <h3>Intent</h3>
        {ENGINE_LONG}
        <p>Made for intent rather than attention, aimed at someone already searching for what you
        sell. Fewer people, each one further along. Slower to start, it does produce trackable
        inbound, and <strong>unlike short form it does not expire</strong>: a video made for
        search keeps getting found years after it is posted.</p>
        <span class="ewhere">Platinum only</span>
      </div>
    </div>
  </div>

  <div class="always">
    <h2>The same three things happen at every tier</h2>
    <p class="sub2">The packages differ in how often our crew is on site, how much goes out and
    the ad budget we manage. Everything here is included whether you spend {money(PRICE_MIN)} or
    {money(PRICE_MAX)}.</p>
    <div class="steps">
      <div class="step2"><span>Step 01</span><h3>Planned</h3>
        <p>Our team decides what goes out and when, so the schedule never depends on someone at
        your company remembering.</p></div>
      <div class="step2"><span>Step 02</span><h3>Captured</h3>
        <p>Your team supplies footage, and from Starter up our crew adds production days on
        site.</p></div>
      <div class="step2"><span>Step 03</span><h3>Posted for you</h3>
        <p>Reels every weekday, graphics on the weekend and stories across your platforms,
        published to your channels rather than handed back as files.</p></div>
    </div>
  </div>

  {pkg_group("you-supply")}

  <div class="band">
    <div class="band-head full-lede">
      <p class="eyebrow">Proof, before you look at the bigger numbers</p>
      <h2 class="display">This is what running it looks like</h2>
      <p>A1 Air Conditioning is a Tucson HVAC company with 9,200 followers. These are their seven
      best-performing reels, all of them ours, and together they carry roughly 2.26 million views
      in a market of one million people. The top one frames a technician alone in a dark attic like
      the cold open of a horror film, and it was shared 1,100 times.</p>
    </div>
    <div class="reels">
{A1_REELS}
    </div>
  </div>

  {pkg_group("two-days")}

  {pkg_group("four-days")}

  <div class="band">
    <div class="band-head">
      <h2 class="display">From sign-up to first post in three to four weeks</h2>
    </div>
    <ol class="ob">
{ONBOARDING}
    </ol>
  </div>

  <div class="incl">
    <h3>Terms</h3>
    <div class="incl-grid">
      <div><span>Starting and stopping</span><p>There is no setup fee. When you want out, we ask
        for 30 days notice and one final payment, so the shortest a package runs is two months.
        You keep every frame we shot and everything we posted, permanently.</p></div>
      <div><span>Commitment</span><p>Every package runs month to month, on the notice terms
        above.</p></div>
      <div><span>Ad budget</span><p>From Starter up, each package includes the monthly ad budget
        shown on its card, which our team manages for you. It goes behind your own content; it is
        not a promise of leads.</p></div>
      <div><span>Insurance</span><p>We are insured. If your office needs paperwork on file
        before a crew is on your property or a job site, ask and we will send it over.</p></div>
      <div><span>Who owns it</span><p>You do. Every frame we shoot for you is yours to keep and
        use however you like, permanently.</p></div>
      <div><span>Where it goes</span><p>YouTube, Instagram, TikTok, Facebook and LinkedIn. Anywhere else
        you want to be, just say so.</p></div>
      <div><span>Revisions</span><p>One round on anything you want changed. Everything is cut to
        make you look good on camera in the first place.</p></div>
      <div><span>Billing</span><p>The first month holds your start date. Nothing else is due until
        the day your first post goes live, and that day sets your monthly cycle.</p></div>
    </div>
  </div>

  <div class="ctarow">
    {book("Monthly%20packages")}
  </div>
  {reassure("packages-terms")}
  <p class="ctanote" style="margin-top:var(--s3);">Questions on terms?
  <a href="/contact/">Contact</a> us.</p>

</div></section>
</main>

{site_footer("packages")}
{actionbar()}
{SPLAT_JS}
{NAV_JS}
{MOTION_JS}
{FORM_JS}
"""


# ---- homepage, the apex domain -------------------------------------------

# The apex speaks as the company. /our-work is the portfolio and
# /packages is the retainer menu, so this page routes to both rather than
# repeating either. Every asset here is one the other pages already copied out,
# so the homepage adds markup and no new weight.

# three spots that carry the range: two premises from All Heart, one from Handyman Dan
HOME_SPOTS = [(None, "All Heart", "Breaking Furniture 101", "0:30", "zaCFfVetfFI"),
              (None, "All Heart", "The Snake", "0:30", "TPDZ-OvRNgc"),
              (None, "Handyman Dan", "A Space Odyssey", "0:56", "AfkePSa8XLU")]

# "Three ways we work" (D2, 2026-10-06): media-led cards, a real still on top
# instead of the retired manila folders. Every image is footage the company shot:
# an All Heart campaign frame, a client crew in a training room, and All Heart's
# "The Influencer" spot framed through a phone camera, which shows the short-form
# format without implying a creator client. The creator link is a conversion CTA,
# so it goes through cta_href().
WAYS = [
    dict(img=f"{P}/ah4.jpg", alt="A family watching a kiddie pool in the living room, from the "
                                 "All Heart campaign",
         title="Campaigns",
         copy="One premise strong enough to carry a whole package, shot in a single production "
              "block so the cost lands once and the inventory lasts a year.",
         href="/our-work/#allheart", go="See the All Heart campaign"),
    dict(img=f"{P}/og-cover.jpg", alt="A client&#39;s technicians in a training room while a "
                                      "shoot is set up",
         title="Monthly programs",
         copy="A reel every weekday and graphics every weekend, planned and posted on a schedule "
              "that does not depend on anyone at your company remembering to post.",
         href="/packages/", go="See the monthly packages"),
    dict(img=f"{S}/og/og-allheart.jpg", alt="A scene from All Heart&#39;s The Influencer spot, "
                                            "framed through a phone camera",
         title="Creator work",
         copy="Short form built for reach, for creators and channels where the audience is the "
              "business. We write the premise so it travels far past the size of the account "
              "that posts it.",
         href=cta_href(), go="Talk to us about creator work"),
]


def way_card(w):
    src = asset(w["img"], "image/jpeg")
    return (f'<article class="way"><img src="{src}"{dims(w["img"])} alt="{w["alt"]}" '
            f'loading="lazy" decoding="async"><div class="way-body"><h3>{w["title"]}</h3>'
            f'<p>{w["copy"]}</p><a class="way-go" href="{w["href"]}">{w["go"]} &rarr;</a>'
            f'</div></article>')


WAYS_CARDS = "\n".join(way_card(w) for w in WAYS)

DOORS_STILL = (f'<img class="doors-bg" src="{asset(f"{P}/quality1.jpg", "image/jpeg")}"'
               f'{dims(f"{P}/quality1.jpg")} alt="" loading="lazy" decoding="async">')

HOME_HTML = f"""<title>Home Service Studios</title>
{FONT_CSS}
{CSS}
<a class="skip" href="#main">Skip to content</a>
{nav("home")}

<main id="main">
<div class="hero hero-bold">
  <div class="hero-media">
    <div class="herobg-clip"><div class="herobg" id="hero-yt" data-yt="SiJpWlQwk04" data-start="0"></div></div>
    <div class="hero-poster" id="hero-yt-poster"></div>
    <div class="hero-scrim"></div>
    <div class="hero-yt-mask"></div>
    <div class="wrap">
      <div class="herotext">
        <p class="eyebrow">Home Service Studios &middot; Los Angeles</p>
        <h1 class="display">A video that makes you feel nothing <span class="hl">does nothing.</span></h1>
      </div>
      <div class="scrollhint">{SCROLL_ICON}</div>
    </div>
  </div>
  <div class="hero-lines">{SPLAT_SVG}<div class="wrap">
  <p class="sub">We write, shoot, edit and post video for home service companies every month, so
  when a homeowner needs a repair, a replacement or a remodel, <strong>the name they already know
  is yours</strong>.</p>
  <div class="stats quad">
    <a class="stat" href="/our-work/#a1"><span class="case">A1 Air Conditioning</span><span class="n">2.26M</span><span class="k">Views on 7 reels</span></a>
    <a class="stat" href="/our-work/#more-results"><span class="case">Be Right There</span><span class="n">983K</span><span class="k">Views on one reel</span></a>
    <a class="stat" href="/our-work/#more-results"><span class="case">iComfort</span><span class="n">+1,680</span><span class="k">Organic followers, under a year</span></a>
    <a class="stat" href="/our-work/#handyman"><span class="case">Handyman Dan</span><span class="n">12</span><span class="k">Markets deployed</span></a>
  </div>
  <div class="ctarow">
    <a class="cta" href="/packages/">See the packages</a>
    <a class="cta ghost" href="/our-work/">See the work first</a>
  </div>
  </div></div>
</div>


<section><div class="wrap">
  <div class="sec-head">
    <h2 class="display">Three ways we work</h2>
    <p class="lede">All of it starts the same way, with a premise worth repeating. The difference is
    how much of the year it has to cover.</p>
  </div>
  <div class="ways">
{WAYS_CARDS}
  </div>
</div></section>

<section id="roster" class="on-ink"><div class="wrap">
  <div class="sec-head bare">
    <h2 class="display">Brands we write and produce for</h2>
    <p class="lede">These are {num_word(ROSTER_COUNT)} home service companies across the country,
    and most of them work in heating, cooling, plumbing or electrical.</p>
  </div>
  {logo_marquee()}
</div></section>

<section><div class="wrap">
  <div class="sec-head">
    <h2 class="display">Proven results with real data</h2>
    <p class="lede">One Tucson HVAC company with 9,200 followers now carries seven reels past
    100,000 views, <strong>roughly 2.26 million views in a market of one million people</strong>.
    The top one frames a technician alone in a dark attic like the cold open of a horror film. It
    was shared 1,100 times, which is the premise working rather than the media budget.</p>
  </div>

  <div class="reels">
{A1_REELS}
  </div>

  <div class="shorts-head">
    <p class="eyebrow">Commercial spots</p>
  </div>

  <div class="grid">
{chr(10).join(spot(*s) for s in HOME_SPOTS)}
  </div>

  <div class="ctarow">
    <a class="cta ghost" href="/our-work/">All three case studies &rarr;</a>
    <span class="ctanote">A1 Air Conditioning, Handyman Dan, All Heart.</span>
  </div>
</div></section>

<section><div class="wrap">
  <div class="sec-head">
    <p class="eyebrow">Monthly packages</p>
    <h2 class="display">Known and trusted before they need you.</h2>
    <p class="lede">Nobody calls a home service company because they saw one good video. They call
    the company they already recognize, and <strong>that recognition is built over months, not in a
    month</strong>. There are {PROGRAMS_WORD} monthly programs, from footage your own team
    supplies to our crew on site four times a year, and every one of them posts a reel every
    weekday. The top one adds long form built for intent rather than attention.</p>
  </div>
  <div class="ops">{price_ladder()}</div>
  <div class="ctarow">
    <a class="cta" href="/packages/">Compare the packages</a>
    <span class="ctanote">Month to month, with no setup fee.</span>
  </div>
</div></section>

<section class="doors-section">{DOORS_STILL}<div class="wrap">
  <div class="doors">
    <a class="door" href="/our-work/">
      <span class="tier">Portfolio</span>
      <h3>See the work</h3>
      <p>Three case studies with the numbers attached, and the reasoning behind each one.</p>
      <span class="go">Open the portfolio &rarr;</span>
    </a>
    <a class="door" href="/packages/">
      <span class="tier">Retainers</span>
      <h3>Hire us monthly</h3>
      <p>{PROGRAMS_WORD.capitalize()} programs, plain terms, and an honest account of what
      consistent content does and does not do.</p>
      <span class="go">See the packages &rarr;</span>
    </a>
  </div>
</div></section>

</main>

{site_footer("home")}
{actionbar()}
{SPLAT_JS}
{SOLO_JS}
{NAV_JS}
{MOTION_JS}
"""




# ---- enquiry form ---------------------------------------------------------

# Field order is deliberate: the two easiest questions first to build momentum,
# then the qualifying ones. Six required, two optional. Every required field
# earns its place by changing how Yoni answers; nothing is collected "for the
# database".
# Grouped, not one flat list. The old version had both "HVAC" and "HVAC, plumbing
# and electrical", so a contractor doing two trades could not tell which was theirs.
# Now the single trades are mutually exclusive and "More than one of these" is the
# explicit escape hatch, which is the only honest way to do single select here.
# Order within the first group follows the actual client mix: HVAC leads because
# twelve of the fifteen logos on the wall are HVAC, plumbing or electrical.
TRADE_GROUPS = [
    ("Home services", ["HVAC", "Plumbing", "Electrical", "Roofing", "Garage doors",
                       "More than one of these", "Another home service"]),
    ("Property and building", ["Remodeling, ADU or new build",
                               "Real estate agent or brokerage"]),
    ("Something else", ["Creator, artist or channel"]),
]
TRADES = [x for _, opts in TRADE_GROUPS for x in opts]

# Shown as visible radios, not a dropdown, on purpose. A buyer who never opens the
# menu never learns where the floor is, and self-selection out is a feature here.
# Built from PKG's budgetBands (pairs of tier ids), so the ranges cannot drift
# from the price book. api_contact.js validates against its own BUDGETS list and
# bounces anything else with a 400, so the build checks the two are identical.
BUDGETS = ([(f"{money(TIER[a]['price'])} to {money(TIER[b]['price'])}",
             f"{TIER[a]['name']} and {TIER[b]['name']}") for a, b in PKG["budgetBands"]]
           + [("Not sure yet", "")])
_api_budgets = re.findall(r'"([^"]*)"', re.search(
    r"const BUDGETS = \[(.*?)\];", pathlib.Path(f"{S}/api_contact.js").read_text(), re.S).group(1))
assert _api_budgets == [v for v, _ in BUDGETS], (
    "api_contact.js BUDGETS must match the bands built from data/packages.json: "
    + repr([v for v, _ in BUDGETS]))


def field(name, label, kind="text", req=True, hint="", ac="", im=""):
    r = ' required aria-required="true"' if req else ''
    opt = '' if req else ' <span class="opt">optional</span>'
    ac = f' autocomplete="{ac}"' if ac else ''
    im = f' inputmode="{im}"' if im else ''
    h = f'<span class="fhint">{hint}</span>'
    ctl = (f'<textarea id="f-{name}" name="{name}" rows="4"{r}{ac}></textarea>'
           if kind == "textarea" else
           f'<input id="f-{name}" name="{name}" type="{kind}"{r}{ac}{im}>')
    return (f'<div class="fld"><label for="f-{name}">{label}{opt}</label>{h}{ctl}'
            f'<span class="ferr" id="e-{name}" role="alert"></span></div>')


def enquiry_form():
    trades = "".join(
        f'<optgroup label="{g}">'
        + "".join(f'<option value="{x}">{x}</option>' for x in opts)
        + '</optgroup>'
        for g, opts in TRADE_GROUPS)
    budgets = "".join(
        f'<label class="budget"><input type="radio" name="budget" value="{v}"'
        f'{" required" if i == 0 else ""}><span class="bv">{v}</span>'
        + (f'<span class="bt">{n}</span>' if n else '') + '</label>'
        for i, (v, n) in enumerate(BUDGETS))
    return f"""<form class="cform" id="cform" method="post" action="{FORM_ACTION}" novalidate>
  <div class="fgrid">
    {field("name", "Your name", ac="name")}
    {field("email", "Email", kind="email", ac="email")}
    {field("company", "Company, @handle or channel", ac="organization",
           hint="A link is even better")}
    {field("city", "City you serve", ac="address-level2",
           hint="Your main market")}
    <div class="fld">
      <label for="f-trade">What you do</label>
      <span class="fhint">Pick the closest match</span>
      <select id="f-trade" name="trade" required aria-required="true">
        <option value="" disabled selected>Choose one</option>
        {trades}
      </select>
      <span class="ferr" id="e-trade" role="alert"></span>
    </div>
    {field("phone", "Phone", kind="tel", req=False, ac="tel", im="tel",
           hint="If you would rather we called")}
  </div>

  <fieldset class="fld budgets">
    <legend>Roughly what you can spend a month</legend>
    <span class="fhint">Nobody is held to this. It tells us which programs are
    worth talking about.</span>
    <div class="budgetrow">{budgets}</div>
    <span class="ferr" id="e-budget" role="alert"></span>
  </fieldset>

  {field("message", "Anything else", kind="textarea", req=False,
         hint="What you are posting now, or what you would like to see")}

  <div class="hp" aria-hidden="true">
    <label for="f-website">Leave this empty</label>
    <input id="f-website" name="website" type="text" tabindex="-1" autocomplete="off">
  </div>

  <div class="fsubmit">
    <button type="submit" class="cta" id="cbtn">Send to HSS</button>
    <p class="ctanote">We answer within one business day. No list, no newsletter,
    no automated sequence.</p>
  </div>
  <p class="fstatus" id="fstatus" role="status" aria-live="polite"></p>
</form>"""


# ---- contact page ---------------------------------------------------------

# Google Calendar appointment pages can be iframed. Until BOOK_URL is set there is
# nothing to embed, so the slot explains itself instead of rendering an empty frame.
# The booking section exists only when there is a calendar to put in it. An empty
# "coming soon" panel advertises a thing you cannot do, which is worse than silence.
if BOOKED:
    SCHEDULER_SECTION = (
        '<section><div class="wrap">'
        '<div class="sec-head"><p class="eyebrow">Booking</p>'
        '<h2 class="display">Or pick a time now</h2>'
        '<p class="lede">Twenty minutes on Google Meet. We look at your market, your current '
        'content, and whether a monthly program makes sense. No deck, no pitch.</p></div>'
        '<div class="schedwrap"><iframe src="' + BOOK_URL + '" title="Book a call with '
        'Home Service Studios" loading="lazy" style="border:0" width="100%" height="640" '
        'frameborder="0"></iframe></div>'
        '</div></section>')
else:
    SCHEDULER_SECTION = ""




CONTACT_HTML = f"""<title>Contact</title>
{FONT_CSS}
{CSS}
<a class="skip" href="#main">Skip to content</a>
{nav("contact")}

<main id="main">
<div class="hero hero-dark hero-contact">{SPLAT_SVG}<div class="wrap">
  <p class="eyebrow">Contact &middot; Home Service Studios</p>
  <h1 class="display">Talk <span class="hl">to us.</span></h1>
  <p class="sub">Tell us your city and your trade and we will come back with something specific
  to your market, not a brochure. If you would rather look first, the work is on the
  <a href="/our-work/">case studies</a> and the monthly programs are
  <a href="/packages/">priced in public</a>. You can also
  <a href="mailto:{EMAIL}">email us</a> directly, good for scope, budgets or anything with
  attachments, but the form below gets you a faster, more specific reply.</p>
  <div class="ctarow">
    <a class="cta" href="#start">Send us a message</a>
  </div>
  {reassure("contact")}
</div></div>


{SCHEDULER_SECTION}

<section id="start"><div class="wrap">
  <div class="sec-head">
    <p class="eyebrow">Send a message</p>
    <h2 class="display">Tell us about your market</h2>
    <p class="lede">Six questions. It takes under a minute, and it means the first
    reply you get is about <strong>your city and your trade</strong> rather than a
    generic hello.</p>
  </div>
  {enquiry_form()}
</div></section>

<section><div class="wrap">
  <div class="incl">
    <h3>What to expect</h3>
    <div class="incl-grid">
      <div><span>Response time</span><p>We answer within one business day, from a human,
        about your market specifically.</p></div>
      <div><span>Where we are</span><p>Los Angeles, CA. We shoot nationwide, and most of our
        home service clients are outside California.</p></div>
      <div><span>What to bring</span><p>Nothing prepared. Your market, roughly what you are
        posting now, and what you want more of next year is enough to work with.</p></div>
    </div>
  </div>
</div></section>
</main>

{site_footer("contact")}
{actionbar()}
{SPLAT_JS}
{NAV_JS}
{MOTION_JS}
{FORM_JS}
"""


# ---- team page -------------------------------------------------------------

# Real people replace placeholders here as they are ready; everything still
# marked "Full Name" / "Title" below is a stand in, not a real staff record.
# Kept as data, not repeated markup, so swapping someone in is an edit to
# these two lists rather than to the page structure.
TEAM_LEADS = [
    {"name": "Craig Balog", "title": "Cofounder", "photo": "craig-balog.jpg",
        "bio": "A filmmaker and photographer based in Beverly Hills with more than ten years "
               "in the industry. Craig founded Home Service Studios out of its Marina del Rey "
               "office, and stays hands on with the craft on every project the company shoots "
               "for contractors."},
    {"name": "Seth Yeager", "title": "Cofounder", "photo": "seth-yeager.jpg",
        "bio": "Seth's background is on set: camera and electrical crew, cinematography and "
               "stunt work in film and television, including second unit and assistant "
               "directing on The Shop. He cofounded Home Service Studios to bring that "
               "production experience to work for contractors."},
]
TEAM_ROSTER = [
    {"name": "Paloma Barros", "title": "Social Media Director", "photo": "paloma-barro.jpg"},
    # Describes him in the same terms as the /our-work paragraph. Craig Balog and
    # Seth Yeager own the company (owner confirmed 2026-10-06); nothing here may
    # read as Yoni having founded or built it.
    {"name": "Yoni Paz", "title": "Creative Director and Producer", "photo": "yoni-paz.jpg",
        "bio": "Seven years across the creator economy, live streaming and social commerce, "
               "running portfolios of more than ten thousand creators and one hundred and "
               "twenty talent agencies, before turning to commercial work."},
    {"name": "Sergy Olkowski", "title": "Post Production Supervisor", "photo": "sergy-olkowski.jpg"},
]


def lead_card(p):
    if p.get("photo"):
        src = asset(os.path.join(P, p["photo"]), "image/jpeg")
        art = (f'<img src="{src}" alt="{p["name"]}" width="900" height="600" '
               f'loading="lazy" decoding="async">')
    else:
        art = PERSON_ICON
    return (f'<div class="lead"><div class="portrait">{art}</div>'
            f'<h3>{p["name"]}</h3><span class="rtitle">{p["title"]}</span>'
            f'<p>{p["bio"]}</p></div>')


def member_card(p):
    if p.get("photo"):
        src = asset(os.path.join(P, p["photo"]), "image/jpeg")
        art = (f'<img src="{src}" alt="{p["name"]}" width="700" height="700" '
               f'loading="lazy" decoding="async">')
    else:
        art = PERSON_ICON
    # Optional, deliberately. A crew card carrying only a name and a title reads
    # as a template waiting for data, which is one of the things that makes the
    # page feel machine assembled. A bio is rendered when the roster has one and
    # the card is unchanged when it does not, so people can be filled in one at a
    # time as they send something rather than all at once.
    bio = f'<p class="mbio">{p["bio"]}</p>' if p.get("bio") else ""
    return (f'<div class="member"><div class="portrait">{art}</div>'
            f'<h3>{p["name"]}</h3><span class="rtitle">{p["title"]}</span>'
            f'{bio}</div>')


TEAM_HTML = f"""<title>Meet the team</title>
{FONT_CSS}
{CSS}
<a class="skip" href="#main">Skip to content</a>
{nav("team")}

<main id="main">
<div class="hero hero-dark">{SPLAT_SVG}<div class="wrap">
  <p class="eyebrow">Meet the team &middot; Home Service Studios</p>
  <h1 class="display">Meet <span class="hl">the team.</span></h1>
  <p class="sub">Every video on this site was written, shot and cut by people you could actually
  meet, not a vendor network stitched together per project.</p>
</div></div>

<section><div class="wrap">
  <div class="sec-head">
    <p class="eyebrow">Leadership</p>
    <h2 class="display">The people steering the work</h2>
  </div>
  <div class="leads">
    {"".join(lead_card(p) for p in TEAM_LEADS)}
  </div>
</div></section>

<section><div class="wrap">
  <div class="sec-head">
    <h2 class="display">The crew</h2>
    <p class="lede">The same people who write, shoot, cut and post your work today are the ones
    you would meet on set or in a review call.</p>
  </div>
  <div class="roster">
    {"".join(member_card(p) for p in TEAM_ROSTER)}
  </div>
</div></section>

<!-- /team was a dead end: 231 words, then nothing but the footer, on the one page
     where a visitor has just decided they like the people. Same .doors pair the
     homepage closes with, so it is an existing pattern rather than a new one, and
     the copy leads from the faces above into the work those faces made. -->
<section class="doors-section">{DOORS_STILL}<div class="wrap">
  <div class="doors">
    <a class="door" href="/our-work/">
      <span class="tier">Portfolio</span>
      <h3>See what they made</h3>
      <p>Three case studies with the numbers attached, shot and cut by the people above.</p>
      <span class="go">Open the portfolio &rarr;</span>
    </a>
    <a class="door" href="/packages/">
      <span class="tier">Retainers</span>
      <h3>Put them on your account</h3>
      <p>{PROGRAMS_WORD.capitalize()} monthly programs, plain terms, and an honest account of
      what consistent content does and does not do.</p>
      <span class="go">See the packages &rarr;</span>
    </a>
  </div>
</div></section>
</main>

{site_footer("team")}
{actionbar()}
{SPLAT_JS}
{NAV_JS}
{MOTION_JS}
"""


# ---- 404 ------------------------------------------------------------------
# GitHub Pages serves deploy/404.html for any path it cannot find, at that path,
# so everything here must be root absolute (asset() already is) and the page is
# noindex and left out of the sitemap. It routes to the three places a lost
# visitor most likely wanted.
NOT_FOUND_HTML = f"""<title>Page not found</title>
{FONT_CSS}
{CSS}
<a class="skip" href="#main">Skip to content</a>
{nav("")}

<main id="main">
<div class="hero hero-dark">{SPLAT_SVG}<div class="wrap">
  <p class="eyebrow">404 &middot; Page not found</p>
  <h1 class="display">That page is <span class="hl">not here.</span></h1>
  <p class="sub">The link may be out of date, or the address may have a typo in it. The work,
  the packages and a way to reach us are all one click away.</p>
  <div class="ctarow">
    <a class="cta" href="/our-work/">See the work</a>
    <a class="cta ghost" href="/packages/">Monthly packages</a>
    <a class="cta ghost" href="/contact/">Contact us</a>
  </div>
</div></div>
</main>

{site_footer("404")}
{actionbar()}
{SPLAT_JS}
{NAV_JS}
"""


# ---- shared post processing, used by every page --------------------------

FAVICON = "data:image/png;base64," + b64(f"{S}/logos_hss/favicon_hss.png")


# 3.3 Structured data. One block, identical on every page, so search engines get a
# single consistent record of who this is and how to reach them.
#
# 2026-09-03: this used to hard code both the URL and the email as literals, which
# is how it kept naming yoniverseproductions.com after the site had moved. Both now
# come from the constants at the top of the file, so the record cannot drift from
# the canonical tags again.
#
# The offer catalogue is generated from data/packages.json, the same file the
# /packages page renders from, so the six prices in search results cannot disagree
# with the six on the page. This is free rich-result eligibility that the site was
# declining while publishing every price in public, which is the rare case that
# makes the markup worth having.
_OFFERS = ",".join(
    '{"@type":"Offer","name":%s,"description":%s,"price":"%d",'
    '"priceCurrency":%s,"availability":"https://schema.org/InStock",'
    '"priceSpecification":{"@type":"UnitPriceSpecification","price":"%d",'
    '"priceCurrency":%s,"unitCode":"MON","billingIncrement":"1"}}'
    % (json.dumps(t["name"]), json.dumps(t["tagline"]), t["price"],
       json.dumps(PKG["currency"]), t["price"], json.dumps(PKG["currency"]))
    for t in PKG["tiers"])

JSON_LD = (
    '<script type="application/ld+json">'
    '{"@context":"https://schema.org","@type":"ProfessionalService",'
    '"name":"Home Service Studios","url":"' + SITE + '/",'
    '"logo":"' + SITE + '/our-work/a/og-cover.jpg",'
    '"image":"' + SITE + '/og/og-home.jpg",'
    '"email":"' + EMAIL + '",'
    '"address":{"@type":"PostalAddress","addressLocality":"Los Angeles",'
    '"addressRegion":"CA","addressCountry":"US"},'
    '"areaServed":"US","priceRange":"$$$",'
    '"description":"Video production for home service brands and creators.",'
    '"hasOfferCatalog":{"@type":"OfferCatalog",'
    '"name":"Monthly video programs","itemListElement":[' + _OFFERS + ']}}'
    '</script>'
)


def validate(page, label):
    """Outbound links open in a new tab. Then the two checks that must never ship."""
    page, n = re.subn(
        r'<a ([^>]*href="https?://[^"]*"[^>]*)>',
        r'<a \1 target="_blank" rel="noopener noreferrer">',
        page,
    )
    assert "—" not in page and "–" not in page, f"DASH FOUND IN {label}"
    bad = sorted({c for c in page if ord(c) > 127})
    assert not bad, f"NON-ASCII IN {label} (use HTML entities): {bad}"
    print(f"  {label}: {n} external links open in a new tab, no dashes, pure ascii")
    return page


def write_web(page, path, *, title, desc, og_image, url, noindex=False):
    """Vercel serves the raw file, so each page supplies its own document shell.

    noindex is for the 404: GitHub Pages serves that one file at whatever bad
    URL was asked for, so it gets a robots noindex and no canonical, og:url or
    JSON-LD (any of those would claim an address the page does not own)."""
    page = re.sub(r'^\s*<title>[^<]*</title>\s*', '', page)   # head owns the title here
    doc = (
        '<!doctype html>\n<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        f'<title>{title}</title>\n'
        + ('<meta name="robots" content="noindex">\n' if noindex else '')
        + f'<meta name="description" content="{desc}">\n'
        '<meta property="og:type" content="website">\n'
        f'<meta property="og:title" content="{title}">\n'
        f'<meta property="og:description" content="{desc}">\n'
        f'<meta property="og:image" content="{og_image}">\n'
        + ('' if noindex else f'<meta property="og:url" content="{url}">\n')
        + '<meta property="og:site_name" content="Home Service Studios">\n'
        + ('' if noindex else f'<link rel="canonical" href="{url}">\n')
        + '<meta name="theme-color" content="#14171A">\n'
        '<meta name="twitter:card" content="summary_large_image">\n'
        f'<link rel="icon" href="{FAVICON}">\n'
        + ('' if noindex else JSON_LD + '\n')
        + '</head>\n<body>\n' + page + '\n</body>\n</html>\n'
    )
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(doc, encoding="utf-8")
    return os.path.getsize(path)


# no price may live in a template. This is the assertion that stops /packages/ and
# the home page drifting apart again, which is exactly how they did last time.
_TEMPLATE_PRICES = re.findall(r'"\$[0-9][0-9,]*"', pathlib.Path(__file__).read_text())
assert not _TEMPLATE_PRICES, (
    "Hardcoded price in build_site.py: " + ", ".join(sorted(set(_TEMPLATE_PRICES)))
    + ". Prices belong in data/packages.json.")

html = validate(html, "our-work")

if MODE == "web":
    # SITE now lives at the top of the file beside EMAIL, so JSON_LD can reach it
    # too. The old domain should 301 here rather than keep serving its stale
    # pre-rebrand build, which is the one part of this that is not a code change.
    D1 = ("Case studies from Home Service Studios, a Los Angeles video company: 2.26M views "
          "for one HVAC client, 983K on one reel for another, spots licensed in 12 markets.")
    n1 = write_web(html, f"{OUT}/index.html",
                   title="Case Studies | Home Services Video Production | Home Service Studios",
                   desc=D1, og_image=f"{SITE}/our-work/a/og-cover.jpg",
                   url=f"{SITE}/our-work/")

    packages = validate(PACKAGES_HTML, "packages")
    D2 = ("Monthly short-form video packages from Home Service Studios: a reel every "
          "weekday, graphics every weekend and stories across your platforms, from "
          f"{money(PRICE_MIN)} a month.")
    n2 = write_web(packages, f"{S}/deploy/packages/index.html",
                   title="Monthly Video Packages for Home Services | Home Service Studios",
                   desc=D2, og_image=f"{SITE}/our-work/a/og-cover.jpg",
                   url=f"{SITE}/packages/")

    contact = validate(CONTACT_HTML, "contact")
    D4 = ("Contact Home Service Studios in Los Angeles. Email us, or send a message "
          "and we will come back with something specific to your market.")
    n4 = write_web(contact, f"{S}/deploy/contact/index.html",
                   title="Contact | Home Service Studios",
                   desc=D4, og_image=f"{SITE}/our-work/a/og-cover.jpg",
                   url=f"{SITE}/contact/")

    nf = validate(NOT_FOUND_HTML, "404")
    write_web(nf, f"{S}/deploy/404.html", title="Page not found | Home Service Studios",
              desc="This page is not here. See the work, the monthly packages, or contact "
                   "Home Service Studios.",
              og_image=f"{SITE}/our-work/a/og-cover.jpg", url=f"{SITE}/404.html", noindex=True)

    team = validate(TEAM_HTML, "team")
    D5 = ("Meet the Home Service Studios team: the people who write, shoot, cut and post "
          "home service video every month.")
    n5 = write_web(team, f"{S}/deploy/team/index.html",
                   title="Meet the Team | Home Service Studios",
                   desc=D5, og_image=f"{SITE}/our-work/a/og-cover.jpg",
                   url=f"{SITE}/team/")

    home = validate(HOME_HTML, "home")
    D3 = ("Los Angeles video production for HVAC, plumbing and home service brands. Written, "
          "shot, cut and posted monthly. 2.26M views for one HVAC client.")
    n3 = write_web(home, f"{S}/deploy/index.html",
                   title="Home Services Video Production | Los Angeles | Home Service Studios",
                   desc=D3, og_image=f"{SITE}/og/og-home.jpg",
                   url=f"{SITE}/")

    # the serverless function that receives the contact form
    os.makedirs(f"{S}/deploy/api", exist_ok=True)
    shutil.copy(f"{S}/api_contact.js", f"{S}/deploy/api/contact.js")

    # 3.5 sitemap so the new URLs get discovered. The five /work/<slug>/ pages
    # are gone (2026-08-27): each case now lives inline in .case-panels on
    # /our-work/, opened by the carousel instead of its own URL.
    # 404.html is deliberately not listed: it is noindex and has no address of its own
    urls = ["/", "/our-work/", "/packages/", "/team/", "/contact/"]
    sm = ('<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"  <url><loc>{SITE}{u}</loc></url>\n" for u in urls)
          + "</urlset>\n")
    pathlib.Path(f"{S}/deploy/sitemap.xml").write_text(sm, encoding="utf-8")
    pathlib.Path(f"{S}/deploy/robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")

    shutil.copytree(f"{S}/og", f"{S}/deploy/og", dirs_exist_ok=True)

    # link preview image, referenced by URL rather than through asset()
    shutil.copy(f"{P}/og-cover.jpg", f"{OUT}/a/og-cover.jpg")

    assets = sum(f.stat().st_size for f in pathlib.Path(f"{OUT}/a").iterdir())
    print(f"\n  index.html           -> {n3/1024:.0f} KB")
    print(f"  contact/index.html   -> {n4/1024:.0f} KB")
    print(f"  our-work/index.html  -> {n1/1024:.0f} KB")
    print(f"  packages/index.html  -> {n2/1024:.0f} KB")
    print(f"  team/index.html      -> {n5/1024:.0f} KB")
    print(f"  shared assets        -> {assets/1048576:.2f} MB")
else:
    out = f"{S}/site.html"
    pathlib.Path(out).write_text(html, encoding="utf-8")
    print(f"{out} -> {os.path.getsize(out)/1048576:.2f} MB")
