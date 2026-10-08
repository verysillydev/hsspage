#!/usr/bin/env python3
"""Build the portfolio.

  python3 build_site.py          -> single self-contained file (Claude artifact)
  python3 build_site.py web      -> deploy/our-work/ with external assets (Vercel)
"""
import base64, datetime, html as html_lib, json, math, os, pathlib, re, shutil, sys, zlib

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

# Where every "book a call" button points. Release 37 (owner): BOOK_URL is the owner's free
# Google Calendar appointment schedule (a one-hour Strategy Call, on collab@). Every general
# CTA goes to our own /book/ page, which embeds it; leave BOOK_URL empty and they all fall
# back to the enquiry form.
# Switched 2026-08-25: homeservicestudios.com is live and receiving mail. Since
# 2026-10-07 (owner) it is collab@, the same address as FORM_TO below. See
# api_contact.js for the matching TO on the dormant Brevo path.
EMAIL = "collab@homeservicestudios.com"

# The live origin. Canonical tags, OG URLs, the sitemap, robots.txt and the JSON-LD
# record all derive from this, so it is the one place the site's own address is
# written down. It sat inside the web-build block until 2026-09-03, which put it
# out of reach of JSON_LD and left that block naming yoniverseproductions.com by
# hand long after the site had moved to GitHub Pages under the new domain. Google
# reads a canonical tag as an instruction, so every page was pointing ranking
# signals at the old Vercel copy. Moving it here is what stops that recurring.
SITE = "https://homeservicestudios.com"

# Where the enquiry form actually delivers. Kept as its own constant beside EMAIL, the
# address shown on the page: the two are allowed to differ, but since 2026-10-07
# (owner) both are collab@. api_contact.js (Brevo, via a Vercel function) is
# unreachable on GitHub Pages, which is static, so FormSubmit is the receiver until the
# form moves back to a real backend. FORM_ACTION is the no-JS fallback; FORM_JS posts
# to the /ajax/ variant. FormSubmit needs a one-time activation for every new
# destination: the first submission after a change makes it email an activation link
# to that address, and nothing is delivered until the owner clicks it.
FORM_TO = "collab@homeservicestudios.com"
FORM_ACTION = f"https://formsubmit.co/{FORM_TO}"

# Paste the Google Calendar appointment booking page here and every CTA on the site
# switches at once. While it is empty the buttons fall back to a prefilled mailto,
# and the reassurance line below them is suppressed (it promises a Meet call).
BOOK_URL = "https://calendar.app.google/aLYtZcqSZ5RvUcSM7"
# BOOK_URL 302s to this schedule; ?gv=true is Google's embeddable view of it. Only /book/
# loads it (in an iframe); the build asserts no other page does.
BOOK_EMBED = ("https://calendar.google.com/appointments/schedules/AcZssZ0xpyqKX2Q-EB1VApY3UM8vgVX"
              "oujhSLplEc_vOdARROcAsnXd_wbuXama7IXEhu7MZkRcNwWVQ?gv=true")
BOOKED = bool(BOOK_URL)

REASSURE = ("A one-hour video call on Google Meet. We'll look at your market and what you're posting now. "
            "Then we'll see if one of our Social Media Packages fits.")

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

# /packages calls reassure() twice; with booking on, its second line must not repeat the first
REASSURE_BOOKED = {
    "packages-terms": "One hour on Google Meet with our team. We'll tell you which package fits.",
}

REASSURE_VARIANTS = {
    "home": REASSURE_FORM,
    "work": ("Six questions and about a minute. A person reads it and answers within one "
             "business day, about your market rather than in general."),
    "packages": ("Under a minute to fill in. You get a real answer within one business day, "
                 "about your city and your trade, not a brochure."),
    "case": ("Under a minute and six questions. A real person answers within one business "
             "day, about your market rather than with a template."),
    "contact": ("Six questions, under a minute. One business day to a reply, written by "
                "someone here who has looked at your market."),
    # /packages calls reassure() twice, once at the top and once under the terms
    # grid, so the second needs its own line or the page repeats itself to itself.
    "packages-terms": ("Six questions, under a minute. A person answers within one business "
                       "day and tells you which package fits."),
}

# Feather "user", stands in for a headshot on /team/ until real photos exist.
PERSON_ICON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" '
               'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
               '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>'
               '<circle cx="12" cy="7" r="4"/></svg>')

# Filled triangle, marks a spot card as playable so it never looks like a
# plain photo. Optically off-center by design: a symmetric triangle reads as
# slightly left-heavy, so the play glyph nudges right via margin in .ytplay.
PLAY_ICON = ('<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true">'
             '<path d="M8 5v14l11-7z"/></svg>')

# Speaker glyphs for the hover-play spots' sound hint ("Click for sound" / "Sound on"),
# same 24px grid and stroke weight as the other line icons.
MUTED_ICON = ('<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" '
              'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
              '<path d="M11 5L6 9H2v6h4l5 4z"/><path d="M23 9l-6 6M17 9l6 6"/></svg>')
SOUND_ICON = ('<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" '
              'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
              '<path d="M11 5L6 9H2v6h4l5 4z"/><path d="M15.5 8.5a5 5 0 0 1 0 7M19 5a10 10 0 0 1 0 14"/></svg>')

# Down chevron, hints at scroll on the homepage hero only. Plain stroke, no fill,
# so it reads as a cue rather than another button competing with the CTAs below it.
SCROLL_ICON = ('<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" '
               'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
               '<path d="M6 9l6 6 6-6"/></svg>')

def cta_href():
    """Where every conversion CTA on the site points. One rule, no exceptions, so a
    button cannot quietly keep pointing somewhere stale."""
    return "/book/" if BOOKED else "/contact/#start"


# Release 34 (owner): every primary button on the site is the "Reel wheel", option D of
# the approved mockup (reports/hss-audit/button-options). The reel is drawn once per page
# as a <symbol> (BM_DEFS, emitted by nav(), which every page calls) and each button uses
# it. The symbol: a disc for the film wound on the reel (no fill of its own, so it takes
# the button's state colour through CSS fill inheritance, and the cut-outs read the same on
# cream and on dark grounds), under the orange flange with its rim groove, five round
# cut-outs and the hub hole, all one even-odd path. 56 units, the desktop diameter.
def _bm_circle(cx, cy, r):
    f = lambda v: f"{v:.1f}".rstrip("0").rstrip(".")
    return f"M{f(cx - r)} {f(cy)}a{f(r)} {f(r)} 0 1 0 {f(2 * r)} 0a{f(r)} {f(r)} 0 1 0 {f(-2 * r)} 0Z"


def _bm_flange():
    d = _bm_circle(28, 28, 27.5) + _bm_circle(28, 28, 25.2) + _bm_circle(28, 28, 23.9)
    for k in range(5):
        a = math.radians(-90 + 72 * k)
        d += _bm_circle(28 + 13.6 * math.cos(a), 28 + 13.6 * math.sin(a), 6.7)
    return d + _bm_circle(28, 28, 3.1)


BM_DEFS = ('<svg class="bm-defs" aria-hidden="true" focusable="false"><symbol id="bm-reel" '
           'viewBox="0 0 56 56"><circle cx="28" cy="28" r="25.6"/>'
           f'<path fill="#F04820" fill-rule="evenodd" d="{_bm_flange()}"/></symbol></svg>')


def reel(label):
    """Inner markup of a primary button: the reel, a row of sprocket holes above and below
    the label, and the label in its own span. FORM_JS swaps only .bm-label's text while
    the form sends, so the reel and the holes survive. Everything but the label is
    aria-hidden, so the accessible name is the label alone. validate() fails the build if
    any primary button (.cta not .ghost, .navcta, the action bar's .primary) lacks it."""
    return ('<svg class="bm-wheel" viewBox="0 0 56 56" aria-hidden="true"><use href="#bm-reel"/></svg>'
            f'<span class="bm-gate t"></span><span class="bm-label">{label}</span>'
            '<span class="bm-gate b"></span>')


def book(subject, label="", cls="cta"):
    """The single conversion CTA. While there is no scheduler it sends people to the
    enquiry form, which beats a mailto on every device and actually qualifies them.
    Set BOOK_URL and the same buttons become the calendar instead. `subject` is kept
    so the fallback can still address an email if it is ever needed."""
    assert "ghost" not in cls, "book() is the primary CTA; secondary buttons are plain links"
    default = "Book a strategy call" if BOOKED else "Start a project"
    return f'<a class="{cls}" href="{cta_href()}">{reel(label or default)}</a>'

def reassure(page="home"):
    """Sits under the CTA and describes what actually happens next. The promise has
    to match the destination, so it changes with it. Once BOOKED is set every CTA
    becomes the calendar and there is only one true promise to make, so the
    per-page phrasing collapses back to a single line on purpose."""
    # /contact/'s button is the form, so it keeps a form promise even when booking is on
    if BOOKED and page != "contact":
        return f'<p class="reassure">{REASSURE_BOOKED.get(page, REASSURE)}</p>'
    return f'<p class="reassure">{REASSURE_VARIANTS.get(page, REASSURE_FORM)}</p>'

def actionbar():
    """Phones only. Two thumbs, two jobs: reach out, or send the details.
    A <nav> with its own label, not a bare div: it sits outside <main> and
    <footer>, and axe's region rule flags content outside every landmark."""
    return (f'<nav class="actionbar" aria-label="Quick actions">'
            f'<a href="/contact/">Contact</a>'
            f'<a class="primary" href="{cta_href()}">'
            f'{reel("Book a call" if BOOKED else "Start a project")}</a></nav>')


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
        BM_DEFS +
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
        + (f'<a class="navcta" href="{href}" aria-current="page">' if active == "book"
           else f'<a class="navcta" href="{href}">')
        + reel(f'<span class="ctalong">{long_label}</span>'
               f'<span class="ctashort">{short_label}</span>') + '</a>'
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

def _mp4_boxes(f, start, end):
    """Yield (type, payload offset, payload end) for the MP4 boxes in [start, end)."""
    pos = start
    while pos + 8 <= end:
        f.seek(pos)
        head = f.read(16)
        size, kind = int.from_bytes(head[:4], "big"), head[4:8].decode("latin-1")
        hdr = 8
        if size == 1:
            size, hdr = int.from_bytes(head[8:16], "big"), 16
        elif size == 0:
            size = end - pos
        if size < hdr:
            raise ValueError(f"bad MP4 box {kind!r} at {pos}")
        yield kind, pos + hdr, pos + size
        pos += size


def mp4_info(path):
    """(width, height, seconds) of an MP4, read from its moov box with the standard
    library only, for the same reason as img_size(): the <video> width/height
    attributes and the duration check come from the file, never typed by hand.
    Also refuses a file whose moov sits after its mdat (not "faststart"): a browser
    would have to fetch the end of the file before it could show a single frame,
    which is exactly the wait hover play cannot afford."""
    end = os.path.getsize(path)
    with open(path, "rb") as f:
        top = {k: (a, b) for k, a, b in _mp4_boxes(f, 0, end)}
        assert "moov" in top and "mdat" in top, f"{path}: not an MP4 with moov and mdat"
        assert top["moov"][0] < top["mdat"][0], f"{path}: moov after mdat, re-encode with +faststart"
        seconds = w = h = None
        for kind, a, b in _mp4_boxes(f, *top["moov"]):
            if kind == "mvhd":
                f.seek(a)
                d = f.read(32)
                if d[0] == 1:   # 64-bit times: timescale at 20, duration at 24
                    scale, dur = int.from_bytes(d[20:24], "big"), int.from_bytes(d[24:32], "big")
                else:           # 32-bit times: timescale at 12, duration at 16
                    scale, dur = int.from_bytes(d[12:16], "big"), int.from_bytes(d[16:20], "big")
                seconds = dur / scale if scale else None
            elif kind == "trak":
                for k2, a2, _ in _mp4_boxes(f, a, b):
                    if k2 != "tkhd":
                        continue
                    f.seek(a2)
                    d = f.read(92)
                    o = 88 if d[0] == 1 else 76
                    tw, th = int.from_bytes(d[o:o + 4], "big") >> 16, int.from_bytes(d[o + 4:o + 8], "big") >> 16
                    if tw and th and w is None:
                        w, h = tw, th
    if not (seconds and w and h):
        raise ValueError(f"cannot read MP4 size/duration: {path}")
    return w, h, seconds


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
#
# N5, 2026-10-06: the web build ships each face once as a cached file under
# /fonts/ (about 86KB for all six) instead of inlining the same base64 into every
# page, and preloads every face from <head>. All six count as first-layout
# weights: a face is requested as soon as any text using it is laid out, which is
# at first layout for the whole page, not when it scrolls into view. The artifact
# build keeps inlining (it has no server). font-display stays optional, so a cold
# first visit on a slow link can still show the fallback for that one view; it
# never shifts layout either way.
FONT_FILES = ([("Onest", w, f"{S}/fonts/onest-{w}.woff2") for w in (400, 600, 700)]
              + [("Archivo", w, f"{S}/fonts/archivo-{w}.woff2") for w in (400, 700, 900)])


def _face(family, weight, path):
    if MODE == "web":
        name = os.path.basename(path)
        os.makedirs(f"{S}/deploy/fonts", exist_ok=True)
        shutil.copy(path, f"{S}/deploy/fonts/{name}")
        src = f"url(/fonts/{name}) format('woff2')"
    else:
        src = f"url(data:font/woff2;base64,{b64(path)}) format('woff2')"
    return (f"@font-face{{font-family:'{family}';font-style:normal;font-weight:{weight};"
            f"font-display:optional;src:{src};}}")


FONT_CSS = "<style>" + "".join(_face(*x) for x in FONT_FILES) + "</style>"
FONT_PRELOAD = ("".join(f'<link rel="preload" href="/fonts/{os.path.basename(x[2])}" as="font" '
                        f'type="font/woff2" crossorigin>\n' for x in FONT_FILES)
                if MODE == "web" else "")

CSS = """<style>
  :root{
    --ground:#FFFFFF; --ground-2:#F5F4F1; --panel:#EFEEEA;
    --line:#E2E0DA; --line-soft:#ECEBE6;
    --hair:#BDB8AE;
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

    /* How far the /our-work banner's ambient YouTube iframe is oversized past its
       visible 16:9 box, top and bottom, so YouTube's own title/uploader strip and
       bottom chrome are drawn outside the clip (see iframe.banner). A floor, not
       the value: the call site scales it up with the player. The homepage hero is
       self-hosted since release 10 and does not use it. */
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
    font-size:var(--f-lede);letter-spacing:.06em;text-transform:none;
    color:var(--ink-3);margin:0;display:block;font-weight:400;}

  .wrap{max-width:1120px;margin:0 auto;padding:0 var(--s5);}
  a{color:var(--orange-text);}
  a:focus-visible{outline:2px solid var(--orange);outline-offset:3px;border-radius:var(--r-sm);}

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
  /* mobile reduces rather than replicates: shorter travel, shorter duration
     (.rv-in restates transform:none or this .rv wins, see CLAUDE.md Motion) */
  @media(max-width:700px){
    .rv{transform:translateY(10px);}
    .rv-in{transform:none;transition-duration:.3s;}
  }
  /* The four "what you are investing in" cards get a longer, more visible
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
  @media(max-width:700px){.benefit.rv,.step2.rv{transform:translateY(30px);}
    .benefit.rv-in,.step2.rv-in{transform:none;}}

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
     ink area, so one width per breakpoint keeps them visually equal in the
     grids. The marquee shows each mark's ink only (release 26, below). */
  .marquee{overflow:hidden;position:relative;
    -webkit-mask-image:linear-gradient(90deg,transparent,#000 8%,#000 92%,transparent);
    mask-image:linear-gradient(90deg,transparent,#000 8%,#000 92%,transparent);}
  /* animated marquee (760px up): items are ink-wide, see logomark() and logo_marquee() */
  .marquee-track{display:flex;width:max-content;gap:var(--mq-gap);padding-right:var(--mq-gap);
    align-items:center;animation:marq 60s linear infinite;}
  .marquee:hover .marquee-track,.marquee:focus-within .marquee-track{animation-play-state:paused;}
  @keyframes marq{from{transform:translateX(0);}to{transform:translateX(-50%);}}
  .marquee .logomark{width:calc(var(--w) * 190px);flex:none;}
  .marquee .logomark img{width:190px;max-width:none;margin-left:calc(var(--x) * -190px);
    clip-path:inset(0 calc((1 - var(--x) - var(--w)) * 190px) 0 calc(var(--x) * 190px));
    transform-origin:calc((var(--x) + var(--w) / 2) * 190px) 50%;}
  /* The static wall (phones, reduced motion) wraps and centres its last row, so
     any number of marks works: CLIENT_LOGOS changes as clients come and go
     (13 after R10, more on the way), and a fixed 3- or 5-column grid left an
     orphan in the corner whenever the count did not divide evenly. */
  @media(max-width:759px),(prefers-reduced-motion:reduce){
    .marquee{-webkit-mask-image:none;mask-image:none;}
    .marquee-track{animation:none;transform:none;width:auto;display:flex;flex-wrap:wrap;
      justify-content:center;gap:var(--s5);padding-right:0;}
    .marquee .logomark{width:calc((100% - 2 * var(--s5)) / 3);}
    .marquee .logomark img{width:100%;margin-left:0;clip-path:none;transform-origin:50% 50%;}
    .marquee .dupe{display:none;}
  }
  @media(min-width:760px) and (prefers-reduced-motion:reduce){
    .marquee-track{gap:var(--s6) var(--s7);}
    .marquee .logomark{width:calc((100% - 4 * var(--s7)) / 5);}
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
  /* The A1 chart on its case page is HTML, not SVG: its numbers and labels are
     real text in the page's own faces. An inline SVG with <text> made Archivo
     700 miss font-display:optional's window (see a1_bars). --plot is the
     tallest bar; every bar is a fraction of it. */
  /* before/after comparison on the Bee Right There and iComfort pages (R4) */
  .ba{display:flex;flex-direction:column;gap:var(--s5);}
  .ba-k{display:flex;justify-content:space-between;align-items:baseline;gap:var(--s3);
    margin:0 0 var(--s2);font-weight:650;font-size:var(--f-body);color:var(--ink);}
  .ba-chg{font-family:var(--display);font-weight:700;font-size:var(--f-h4);color:var(--orange-text);
    font-variant-numeric:tabular-nums;}
  .ba-line{display:grid;grid-template-columns:7.5em minmax(0,1fr);align-items:center;
    column-gap:var(--s3);margin:3px 0;font-size:var(--f-sm);}
  /* phones: the date sits above its bar, so the bar gets the full width */
  @media(max-width:559px){.ba-line{grid-template-columns:minmax(0,1fr);margin:var(--s1) 0;}}
  .ba-when{font-size:var(--f-micro);color:var(--ink-2);line-height:1.3;}
  .ba-track{display:flex;align-items:center;gap:var(--s2);min-width:0;}
  .ba-bar{flex:none;height:16px;width:calc(var(--w) * (100% - 4.5em));min-width:3px;
    background:rgba(var(--cyan-rgb),.55);border-radius:0 var(--r-sm) var(--r-sm) 0;}
  .ba-line.is-after .ba-bar{background:var(--orange);}
  .ba-v{font-family:var(--display);font-weight:700;font-size:var(--f-sm);color:var(--ink);
    white-space:nowrap;font-variant-numeric:tabular-nums;}
  .case-why{margin-top:var(--s7);padding-top:var(--s5);border-top:1px solid var(--line);
    max-width:68ch;}
  .case-close{margin:var(--s2) 0 0;font-size:var(--f-lead);line-height:1.5;color:var(--ink);}
  .case-src{margin:var(--s4) 0 0;font-size:var(--f-sm);color:var(--ink-2);}
  .a1bars{--plot:150px;}
  .a1plot{position:relative;display:grid;grid-template-columns:repeat(7,minmax(0,1fr));
    gap:var(--s1);align-items:end;height:calc(var(--plot) + 2em);padding-right:3em;
    border-bottom:1px solid var(--line);}
  @media(min-width:560px){.a1plot,.a1idx{gap:var(--s3);}}
  .a1b{display:flex;flex-direction:column;align-items:center;gap:var(--s1);min-width:0;}
  .a1b .v{font-family:var(--display);font-weight:700;font-size:var(--f-micro);color:var(--ink);
    line-height:1;white-space:nowrap;}
  @media(min-width:560px){.a1b .v{font-size:var(--f-sm);}}
  .a1b .bar{display:block;width:100%;height:calc(var(--h) * var(--plot));
    background:rgba(var(--cyan-rgb),.55);border-radius:var(--r-md) var(--r-md) 0 0;}
  .a1b.is-top .bar{background:var(--orange);}
  .a1t{position:absolute;left:0;right:3em;bottom:calc(var(--h) * var(--plot));
    border-top:1px dashed rgba(var(--orange-rgb),.5);}
  .a1t span{position:absolute;left:100%;margin-left:var(--s1);top:-.75em;font-family:var(--display);font-weight:700;
    font-size:var(--f-micro);line-height:1.5;color:var(--orange-text);letter-spacing:.05em;}
  .a1idx{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:var(--s1);
    padding-right:3em;margin-top:var(--s2);}
  .a1idx span{text-align:center;font-family:var(--display);font-weight:700;font-size:var(--f-micro);
    color:var(--ink-2);letter-spacing:.05em;}
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
    text-transform:uppercase;letter-spacing:.06em;font-family:var(--mono);margin-left:6px;}
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
  .actionbar a.primary{--d:0px;--bh:0px;background:var(--btn-cur);color:#FFFFFF;}
  .actionbar a.primary .bm-wheel{position:static;width:30px;height:30px;}
  .actionbar a.primary .bm-gate{left:0;right:0;height:5px;width:calc(100% - 8px);
    width:round(down,100% - 8px,12px);}
  .actionbar a.primary .bm-gate.t{top:3px;}
  .actionbar a.primary:focus-visible{outline-offset:-4px;}
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
    .hero-media{padding-bottom:calc(118px + env(safe-area-inset-bottom));}
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
  .pgrid{display:grid;grid-template-columns:minmax(0,1fr);gap:var(--s4);}
  @media(min-width:760px){.pgrid{grid-template-columns:repeat(2,minmax(0,1fr));}}
  .pcard{position:relative;display:flex;flex-direction:column;gap:var(--s3);
    padding:var(--s6) var(--s5) var(--s5);border-radius:var(--r-md);transition:transform var(--ease);}
  .pcard:hover{transform:translateY(-2px);}
  .pcard:focus-within{outline:2px solid var(--orange);outline-offset:3px;}
  .pcard p{margin:0;}
  .pc-tag{font-family:var(--display);font-variant-caps:all-small-caps;letter-spacing:.06em;
    font-size:var(--f-sm);color:var(--cyan-text);}
  .pcard h3{margin:0;font-family:var(--display);font-weight:700;font-size:var(--f-h3);
    line-height:1.2;letter-spacing:var(--t-head);color:var(--ink);max-width:24ch;}
  .pc-metric{display:flex;flex-direction:column;gap:var(--s1);margin-top:var(--s3) !important;}
  .pc-metric b{font-family:var(--display);font-weight:900;font-size:var(--f-mega);line-height:1;
    letter-spacing:-.02em;color:var(--orange);font-variant-numeric:tabular-nums;}
  .pc-metric span{font-size:var(--f-body);color:var(--ink-2);line-height:1.45;max-width:34ch;}
  .pc-metric .pc-now{font-size:var(--f-sm);}
  .pc-who{margin-top:auto !important;padding-top:var(--s4);border-top:1px solid var(--line);
    font-size:var(--f-sm);color:var(--ink-3);}
  .pc-go{align-self:flex-start;display:inline-flex;align-items:center;min-height:24px;
    font-size:var(--f-sm);font-weight:650;color:var(--orange-text);text-decoration:none;}
  .pc-go::after{content:"";position:absolute;inset:0;}
  .pc-go:focus-visible{outline:none;}
  /* visually hidden text, still read by screen readers */
  .vh{position:absolute;width:1px;height:1px;margin:-1px;padding:0;overflow:hidden;
    clip:rect(0 0 0 0);white-space:nowrap;border:0;}

  /* case pages (N1): breadcrumbs in the dark hero, a prev/next chain at the foot */
  .crumbs{display:flex;flex-wrap:wrap;align-items:center;gap:0 var(--s2);margin:0 0 var(--s4);
    font-size:var(--f-sm);color:var(--ink-3);}
  .crumbs a{display:inline-flex;align-items:center;min-height:24px;color:var(--ink-2);
    text-decoration:none;}
  .crumbs a:hover{color:var(--ink);text-decoration:underline;}
  .crumbs [aria-current]{color:var(--ink);}
  .hero .role{margin-top:var(--s5);}
  .pnrow{display:grid;grid-template-columns:minmax(0,1fr);gap:var(--s3);}
  @media(min-width:760px){.pnrow{grid-template-columns:1fr 1fr;}.pn.next{grid-column:2;text-align:right;}}
  .pn{display:flex;flex-direction:column;gap:var(--s1);padding:var(--s5);background:var(--ground-2);
    border-radius:var(--r-md);text-decoration:none;color:inherit;transition:transform var(--ease);}
  .pn:hover{transform:translateY(-2px);}
  .pn-l{font-family:var(--display);font-variant-caps:all-small-caps;letter-spacing:.06em;
    font-size:var(--f-sm);color:var(--cyan-text);}
  .pn-n{font-family:var(--display);font-size:var(--f-h3);font-weight:700;letter-spacing:var(--t-head);}

  /* sits under a booking CTA, so nobody has to guess what happens after the click */
  .reassure{margin:var(--s3) 0 0;font-size:var(--f-sm);color:var(--ink-3);max-width:52ch;
    line-height:1.5;}

  .booknote{margin:var(--s4) 0 0;font-size:var(--f-body);color:var(--ink-2);}
  .schedwrap{background:var(--ground-2);border:1px solid var(--line);
    border-radius:var(--r-md);overflow:hidden;}
  .schedwrap iframe{display:block;width:100%;}

  /* compact Reel wheel from 560px; film only below (80px slot, no room for a reel) */
  .navcta{--d:0px;--bh:0px;background:transparent;color:#FFFFFF !important;
    border-radius:var(--r-pill);padding:0 var(--s3);font-weight:700;text-decoration:none;
    font-family:'Onest',-apple-system,sans-serif !important;text-transform:none;
    font-variant-caps:normal !important;letter-spacing:var(--t-head);font-size:var(--f-sm);
    display:inline-flex;align-items:center;min-height:44px;}
  .navcta .bm-wheel{display:none;}
  /* The box is sized to the label in Onest, so it cannot grow when Onest lands
     after first paint (since N5 the fonts are files; the -apple-system fallback
     is about 6px narrower for "Contact" and 11px for "Start a project", which
     shifted the whole right side of the bar, CLS about 0.001 on throttled
     phones). em-based, so it scales with the fluid label size. */
  .navcta{justify-content:center;min-width:calc(3.9em + 24px);}
  @media(min-width:560px){.navcta{min-width:calc(var(--cta-em,7em) + 70px);}}
  /* below 560px the row needed about 354px of a 342px content box once the
     brand set in Onest, so the right group overflowed into the page padding
     and moved when the font arrived; a tighter gap and CTA padding make it fit */
  @media(max-width:559px){.navin{gap:var(--s2);} .navcta{padding:0 var(--s3);}}
  /* On a slow connection the browser can paint while the nav's HTML is only
     half parsed (the toggle in, the CTA not yet), and the right-aligned group
     then grew leftwards when the CTA arrived: a 0.0016 shift on throttled
     phones. Reserving the group's final width (toggle 40px + its 10px gap + the
     CTA's own minimum) means a partly parsed nav already sits in its final box. */
  @media(max-width:559px){.navright{min-width:calc(50px + 3.9 * var(--f-sm) + 24px);}}
  @media(min-width:560px) and (max-width:619px){
    .navright{min-width:calc(40px + var(--s5) + var(--cta-k,7) * var(--f-sm) + 70px);}}
  .navcta .ctashort{display:inline;}
  .navcta .ctalong{display:none;}
  @media(min-width:560px){
    .navcta{--d:44px;--bh:36px;padding:calc(var(--d) - var(--bh) + 4px) 16px 4px calc(var(--d) + 10px);}
    .navcta .bm-wheel{display:block;}
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
    --ground:#14171A; --ground-2:#1E2226; --panel:#262B30; --line:#33383D; --hair:#4B535B;
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

  /* Homepage hero (release 10, owner, 2026-10-06): a self-hosted silent film that
     COVERS the whole hero box at every size, object-fit:cover and centred, with
     no band anywhere. This reverses the earlier phone letterbox (a 74.8vh 16:9 box
     that left a black band above the picture, plus YouTube's pause icon
     mid-picture). The first paint is the poster (<picture>, the film's first
     frame, 960 or 1280 wide by the same 760px breakpoint the film uses); the
     <video> sits over it at opacity 0 and fades in once it is actually playing,
     so there is no flash and no band. HERO_JS picks the file. The headline sits,
     bottom anchored, over the footage. */
  .hero-media{position:relative;overflow:hidden;background:#14171A;
    min-height:100vh;min-height:100dvh;
    display:flex;flex-direction:column;justify-content:flex-end;}
  .hero-lqip,.hero-poster,.hero-poster img,.hero-video{position:absolute;inset:0;width:100%;height:100%;}
  .hero-lqip,.hero-poster{z-index:0;}
  .hero-lqip,.hero-poster img,.hero-video{display:block;object-fit:cover;object-position:center;}
  .hero-video{z-index:0;opacity:0;transition:opacity .6s ease;pointer-events:none;}
  .hero-video.is-on{opacity:1;}
  @media(max-width:600px){
    /* smaller title: less of the frame covered by text and scrim, more of the
       footage reads. Desktop's clamp is untouched. */
    .hero-bold h1{font-size:clamp(26px, 8px + 5vw, 42px);}
  }
  /* light touch, not a wash: most of the frame stays undimmed, darkening
     only where the headline actually sits so the video reads clean rather
     than muddy, the opposite problem the first pass had. */
  .hero-scrim{position:absolute;inset:0;z-index:1;pointer-events:none;
    background:linear-gradient(180deg,rgba(20,23,26,0) 0%,rgba(20,23,26,0) 28%,
      rgba(20,23,26,.7) 58%,rgba(20,23,26,.9) 100%);}
  /* release 10: the footage now covers the whole hero on phones too (it used to
     letterbox, with the text over a black band), so the scrim starts earlier and
     the eyebrow is lighter: measured over the brightest frames of the loop, the
     eyebrow keeps AA contrast at 390, 768 and 1440 wide. */
  .hero-media .eyebrow{color:#FFFFFF;}
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
  /* not painted half parsed: on a slow line the headline's last words can arrive after the
     first paint, and this bottom-anchored block then pushed it up (CLS .01, release 34) */
  .hero-media > .wrap:not(:has(> .scrollhint)){visibility:hidden;}
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
  /* a cell whose parts link separately (Bee Right There on the homepage: the name to
     the case, the number to the reel) instead of the whole cell */
  .stat a.case{text-decoration:none;}
  .stat a.case:hover{text-decoration:underline;text-underline-offset:3px;}
  .stat a.n,.op a.n{text-decoration:underline;text-decoration-thickness:1px;
    text-underline-offset:.16em;}
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
  .csi{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:var(--s3);
    margin-bottom:var(--s4);}
  .csi > div{background:var(--ground-2);border-radius:var(--r-sm);padding:var(--s5);}
  .csi h3{margin:0 0 var(--s2);font-family:var(--mono);font-size:var(--f-micro);
    letter-spacing:var(--t-caps);text-transform:uppercase;color:var(--orange-text);font-weight:600;}
  /* the outcome column carries the secondary hue so results read apart from setup */
  .csi div:nth-child(3) h3{color:var(--cyan-text);}
  .csi p{margin:0;font-size:var(--f-body);color:var(--ink-2);line-height:1.55;}
  .csi p.csi-lead{margin:0 0 var(--s2);font-family:var(--display);font-weight:700;
    font-size:var(--f-h4);line-height:1.3;color:var(--ink);}

  /* Ruled ledger, not bordered cards: same technique as the hero .stats row
     (gap:1px on a --line background, each cell its own --ground fill), so a
     row of proof numbers reads as one connected figure instead of a stack of
     separate boxes. This used to be individually padded/backgrounded .panel
     cards, which is exactly the "default look" the six rules elsewhere on
     this sheet exist to avoid; .op is shared across every case page's stat
     row and the packages page, so fixing it here fixes all of them at once. */
  /* wrapping flex, not an auto-fit grid (2026-10-06): with a grid, five
     figures on a phone left the fifth beside an empty grey cell; growing flex
     items stretch whatever lands on the last row to the full width instead */
  .ops{display:flex;flex-wrap:wrap;gap:1px;background:var(--line);margin-bottom:var(--s4);}
  .op{flex:1 1 140px;min-width:0;background:var(--ground);padding:var(--s4);display:flex;
    flex-direction:column;gap:var(--s1);transition:background var(--ease);}
  .op:hover{background:var(--ground-2);}
  .op .n{font-size:var(--f-h3);font-weight:700;letter-spacing:-.012em;color:var(--cyan-text);
    font-family:var(--display);line-height:1.1;}
  .op .k{font-size:var(--f-micro);letter-spacing:.06em;text-transform:uppercase;color:var(--ink-3);
    font-family:var(--mono);}


  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(288px,1fr));gap:var(--s5);}
  /* subheads inside a section (the homepage spots row) */
  .subhead{margin:var(--s7) 0 var(--s4);font-family:var(--display);font-size:var(--f-h3);
    font-weight:700;letter-spacing:var(--t-head);line-height:1.15;}
  .sec-head + .subhead{margin-top:0;}
  /* The Handyman Dan campaign on /our-work (release 28): intro, the spots, then the
     result as one quiet line in body size under a small label. No display stat. */
  .mw-body{margin:0 0 var(--s5);max-width:62ch;font-size:var(--f-lede);line-height:1.55;
    color:var(--ink-2);text-wrap:pretty;}
  .mw-result{margin:var(--s5) 0 0;max-width:62ch;font-size:var(--f-body);line-height:1.55;
    color:var(--ink);text-wrap:pretty;}
  .mw-ask{margin:var(--s5) 0 0;font-size:var(--f-body);line-height:1.55;color:var(--ink);}
  .mw-ask + .wwd-link{margin-top:var(--s1);}
  .mw-ask + .cta{margin-top:var(--s3);}
  .mw-k{display:block;margin-bottom:var(--s1);font-family:var(--display);
    font-variant-caps:all-small-caps;letter-spacing:.06em;font-size:var(--f-sm);color:var(--ink-2);}
  /* What We Do (homepage, release 8): warm white ground, three numbered blocks with a
     hairline between them. --ink-3 on --ground-2 is 4.32:1, so small text uses --ink-2. */
  section.wwd{background:var(--ground-2);}
  .wwd-block{padding:var(--s7) 0;}
  .wwd-block:first-of-type{padding-top:0;}
  .wwd-block:last-child{padding-bottom:0;}
  .wwd-block + .wwd-block{border-top:1px solid var(--line);}
  .wwd-num{margin:0;font-size:var(--f-mega);line-height:1;height:1em;}
  .wwd-title{margin:var(--s3) 0 0;font-family:var(--display);font-weight:700;font-size:var(--f-h2);
    line-height:1.15;letter-spacing:var(--t-head);color:var(--ink);}
  .wwd-copy{margin:var(--s3) 0 0;font-size:var(--f-lede);line-height:1.55;color:var(--ink-2);
    max-width:56ch;}
  .wwd-small{margin:var(--s2) 0 0;font-size:var(--f-sm);color:var(--ink-2);}
  .wwd-link{display:inline-flex;align-items:center;min-height:24px;margin-top:var(--s3);
    font-weight:650;color:var(--orange-text);text-decoration:none;}
  .wwd-link:hover{text-decoration:underline;text-underline-offset:3px;}
  .wwd-block > .igrow,.wwd-block > .grid,.wwd-film{margin-top:var(--s6);}
  /* block 01 carries the primary "Compare the packages" button (moved here from the
     removed packages section); its note needs --ink-2 on this ground */
  .wwd .ctarow{margin-top:var(--s5);}
  .wwd .ctanote{color:var(--ink-2);}
  /* three profile grabs in identical 390:766 frames, top aligned; a swipe strip on
     phones, cards at 78% so the next one peeks */
  .igrow{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:var(--s5);}
  .ig{margin:0;display:flex;flex-direction:column;gap:var(--s3);min-width:0;}
  .ig-frame{display:block;aspect-ratio:390/766;border:1px solid var(--line);
    border-radius:var(--r-lg);overflow:hidden;background:var(--ground);}
  .ig-frame:focus-visible{border-radius:var(--r-lg);}
  .ig-frame img{width:100%;height:100%;display:block;object-fit:cover;object-position:top;}
  .ig figcaption{display:flex;flex-direction:column;gap:2px;}
  .ig-name{font-weight:600;color:var(--ink);line-height:1.35;}
  .ig-meta{font-size:var(--f-sm);color:var(--ink-2);}
  @media(max-width:759px){
    .igrow{display:flex;overflow-x:auto;scroll-snap-type:x mandatory;gap:var(--s4);
      padding-bottom:var(--s2);scrollbar-width:thin;}
    .igrow > .ig{flex:0 0 78%;scroll-snap-align:start;}
  }
  .wwd-film .vspot{border-radius:var(--r-md);}
  /* testimonial (release 8): video with the pull quote beside it from 900px,
     below it on phones */
  .tmn{display:grid;grid-template-columns:minmax(0,1fr);gap:var(--s6);align-items:center;}
  @media(min-width:900px){.tmn{grid-template-columns:minmax(0,3fr) minmax(0,2fr);gap:var(--s7);}}
  .tmn-media .vspot{border-radius:var(--r-md);}
  .tmn-quote{margin:0;}
  .tmn-quote blockquote{margin:0;padding-left:var(--s5);border-left:3px solid var(--orange);}
  .tmn-quote p{margin:0;font-family:var(--display);font-weight:600;font-size:var(--f-h3);
    line-height:1.3;letter-spacing:var(--t-head);color:var(--ink);}
  .tmn-quote figcaption{margin-top:var(--s4);padding-left:var(--s5);font-size:var(--f-sm);
    color:var(--ink-2);}
  .tmn-link{margin-top:var(--s5);}
  /* captions: the site face on a solid scrim, and the sound hint moves to the top
     corner so it never sits on a caption line */
  .vspot video::cue{font-family:'Onest',-apple-system,sans-serif;color:#fff;
    background:rgba(15,18,20,.82);line-height:1.35;}
  .vspot.has-cc .vsnd{top:var(--s2);bottom:auto;}
  .wwd-cap{margin:var(--s3) 0 0;display:flex;justify-content:space-between;align-items:baseline;
    gap:var(--s3);font-size:var(--f-sm);color:var(--ink-2);}
  .wwd-cap .du{font-family:var(--mono);flex:none;}
  /* a row of spots: three across from 760px (six make two even rows), and a
     horizontal swipe strip on phones so six cards do not stack 1,700px tall */
  /* any count: one row from 1100px when there are five, otherwise rows of three
     with the last row centred, so a short row never sits in a corner */
  .strip{display:flex;flex-wrap:wrap;justify-content:center;gap:var(--s4);}
  .strip > .spot{flex:0 0 calc((100% - 2 * var(--s4)) / 3);}
  @media(min-width:1100px){.strip.five > .spot{flex-basis:calc((100% - 4 * var(--s4)) / 5);}}
  @media(max-width:759px){
    .strip{display:flex;flex-wrap:nowrap;justify-content:flex-start;overflow-x:auto;
      overflow-y:hidden;overscroll-behavior-x:contain;
      scroll-snap-type:x mandatory;gap:var(--s3);padding-bottom:var(--s2);scrollbar-width:thin;}
    .strip > .spot{flex:0 0 80%;scroll-snap-align:start;}
    /* One row, so it only ever scrolls sideways (release 28). The phone reveal
       (.rv at 10px, which outranks .rv-in by source order) left every card 10px low,
       and inside this scroller that was vertical overflow: the row scrolled up and
       down. Cards here fade in without the slide, and overflow-y:hidden guards the
       axis. The card's focus ring is inset (.vplay), so nothing it draws is clipped. */
    .strip > .spot.rv{transform:none;}
  }
  .spot{background:var(--panel);border-radius:var(--r-md);
    overflow:hidden;display:flex;flex-direction:column;}
  .spot video{width:100%;display:block;background:#000;aspect-ratio:16/9;object-fit:cover;}
  /* Click-to-play YouTube spots. Poster and button only until clicked, see
     YT_SPOT_JS: the iframe is swapped in on click, never loaded before. Inline
     artifact build only since release 4; the web build self-hosts (.vspot). */
  .ytspot{position:relative;aspect-ratio:16/9;background:#000;cursor:pointer;overflow:hidden;}
  .ytspot img{width:100%;height:100%;display:block;object-fit:cover;}
  .ytspot iframe{width:100%;height:100%;display:block;border:0;}
  .ytplay{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:52px;
    height:52px;border-radius:50%;background:rgba(20,23,26,.72);border:none;color:#fff;
    display:flex;align-items:center;justify-content:center;cursor:pointer;
    transition:background var(--ease),transform var(--ease);}
  .ytplay svg{margin-left:2px;}
  .ytspot:hover .ytplay{background:var(--orange);transform:translate(-50%,-50%) scale(1.06);}
  /* Self-hosted hover-play spots (All Heart, Handyman Dan; release 4), behaviour in
     SOLO_JS. Same 16:9 cover framing as the YouTube cards. The lazy poster <img>
     sits over the <video> until a frame is actually playing (.is-live), then fades;
     stopping brings it back. The whole picture is one button, the accessible
     control; the card around it also takes clicks and hover. */
  .is-vcard{cursor:pointer;}
  .vspot{position:relative;aspect-ratio:16/9;background:#000;overflow:hidden;}
  .vspot video,.vspot img{position:absolute;inset:0;width:100%;height:100%;display:block;
    object-fit:cover;}
  /* 1px past every edge, clipped by the box: the composited video layer snaps to
     whole device pixels and left a 1px black sliver along a fractional bottom edge */
  .vspot video{inset:-1px;width:calc(100% + 2px);height:calc(100% + 2px);}
  .vspot img{transition:opacity var(--ease);}
  .vspot.is-live img{opacity:0;}
  .vplay{position:absolute;inset:0;width:100%;height:100%;margin:0;padding:0;border:0;
    background:none;color:#fff;cursor:pointer;font:inherit;}
  /* orange ring with a dark inner ring: visible on any frame, light or dark */
  .vplay:focus-visible{outline:3px solid var(--orange);outline-offset:-3px;
    box-shadow:inset 0 0 0 6px rgba(15,18,20,.85);}
  .vglyph{position:absolute;left:50%;top:50%;width:46px;height:32px;margin:-16px 0 0 -23px;
    border-radius:var(--r-lg);background:rgba(15,18,20,.72);display:flex;align-items:center;
    justify-content:center;transition:opacity var(--ease),transform var(--ease);}
  .vglyph svg{margin-left:2px;}
  .is-vcard:hover .vglyph,.vplay:focus-visible .vglyph{background:var(--orange);transform:scale(1.06);}
  .vspot[data-state="muted"] .vglyph,.vspot[data-state="sound"] .vglyph{opacity:0;}
  /* the sound hint, pointer devices only (.hover-ui), while the spot plays */
  .vsnd{position:absolute;right:var(--s2);bottom:var(--s2);padding:var(--s1) var(--s2);
    border-radius:var(--r-sm);background:rgba(15,18,20,.8);font-size:var(--f-micro);
    font-weight:600;line-height:1.2;opacity:0;transition:opacity var(--ease);pointer-events:none;}
  .vsnd span{display:inline-flex;align-items:center;gap:var(--s1);}
  .vspot .vsnd-on,.vspot[data-state="sound"] .vsnd-off{display:none;}
  .vspot[data-state="sound"] .vsnd-on{display:inline-flex;}
  .vspot.hover-ui[data-state="muted"] .vsnd,.vspot.hover-ui[data-state="sound"] .vsnd{opacity:1;}
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
  .rthumb{width:44px;height:74px;border-radius:var(--r-sm);flex:none;object-fit:cover;}
  .reel .l{font-size:var(--f-micro);letter-spacing:.06em;text-transform:uppercase;color:var(--ink-3);
    font-family:var(--mono);}

  /* Written for the old title cards and kept because it is what gives the
     click-to-play spot button its 46x32 shape: it overrides the circle above. */
  .ytplay{position:absolute;left:50%;top:50%;width:46px;height:32px;margin:-16px 0 0 -23px;
    border-radius:var(--r-lg);background:rgba(15,18,20,.72);transition:background var(--ease);}
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
  /* Release 34 (owner): from 900px every tier card sits on one three-column grid. The first
     two groups share a row (1 + 2 columns) above the third (3). Panels lose their side
     padding there, so a card is exactly one column wide in every row, and subgrid rows line
     up both groups' tab, explainer and cards (same top, same height). */
  @media(max-width:899px){.band-row > .band:first-child{margin-bottom:var(--s8);}}
  @media(max-width:759px){.band-row > .band:first-child{margin-bottom:var(--s5);}}
  @media(min-width:900px){
    .band-row{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));column-gap:var(--s4);
      grid-template-rows:auto auto auto;margin-bottom:var(--s8);}
    .band-row > .band{display:grid;grid-row:span 3;grid-template-rows:subgrid;margin:0;}
    .band-row > .band + .band{grid-column:2 / span 2;}
    .band-row .band-tab{justify-self:start;padding-left:18px;padding-right:18px;}
    .band-row .band-body{grid-row:span 2;display:grid;grid-template-rows:subgrid;row-gap:0;}
    .band-body{padding-left:0;padding-right:0;}
    .band-body > p{padding:0 var(--s5);}
    .band .pkgs{grid-template-columns:repeat(3,minmax(0,1fr));}
    .band-row .band .pkgs{grid-template-columns:repeat(2,minmax(0,1fr));}
    .band-row .band:first-child .pkgs{grid-template-columns:minmax(0,1fr);}
  }
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
  /* D6: the "what you are investing in" block is a flat ink panel; .on-ink
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
  .ob-note{margin:var(--s3) 0 0;font-size:var(--f-sm);color:var(--ink-2);max-width:62ch;}

  .steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:var(--s3);}
  .step2{background:var(--panel);border-radius:var(--r-sm);
    padding:var(--s5);}
  .step2 span{font-family:var(--mono);font-size:var(--f-micro);letter-spacing:var(--t-caps);
    text-transform:uppercase;color:var(--cyan-text);}
  .step2 h3{margin:var(--s2) 0 var(--s1);font-size:var(--f-h4);font-weight:650;
    letter-spacing:var(--t-head);}
  .step2 p{margin:0;font-size:var(--f-body);color:var(--ink-2);line-height:1.55;}
  /* N2, 2026-10-06: /packages ran about 12,300px on a 390px phone. Below 760px
     the repeated blocks compact: tighter panels and cards, the benefit numeral
     beside its heading, the steps as a ruled list, closer tier features. */
  @media(max-width:759px){
    .always{padding:var(--s5) var(--s4);margin-bottom:var(--s5);}
    .always .sub2{margin-bottom:var(--s4);}
    .benefits{gap:var(--s2);}
    .benefit{padding:var(--s4);display:grid;grid-template-columns:auto minmax(0,1fr);
      column-gap:var(--s3);row-gap:var(--s1);align-items:baseline;}
    .benefit .bn{font-size:var(--f-h4);border-bottom:0;padding:0;margin:0;}
    .benefit p{grid-column:1 / -1;}
    .steps{gap:1px;background:var(--line);}
    .step2{padding:var(--s3) var(--s4);background:var(--ground-2);}
    .step2 h3{margin:var(--s1) 0 2px;}
    .band{margin-bottom:var(--s5);}
    .band-body{padding:var(--s5) var(--s4) var(--s4);}
    .band-body > p{margin-bottom:var(--s4);}
    .pkgs{gap:var(--s3);}
    .pkg{padding:var(--s5) var(--s4);gap:var(--s3);}
    .pkg .best{margin:calc(var(--s5) * -1) calc(var(--s4) * -1) 0;}
    .pkg ul{gap:var(--s2);}
    .incl{padding:var(--s5) var(--s4);gap:var(--s3);}
    .hero .ctarow .cta.ghost{padding-left:var(--s4);padding-right:var(--s4);}
    /* explanatory paragraphs one step down (still above the 12px floor);
       headings, prices and the "Not leads" lede keep their size */
    .benefit p,.step2 p,.pkg li{font-size:var(--f-sm);line-height:1.5;}
    .step2{display:grid;grid-template-columns:auto minmax(0,1fr);column-gap:var(--s2);
      align-items:baseline;}
    .step2 h3{margin:0;}
    .step2 p{grid-column:1 / -1;margin-top:2px;}
    .ob{grid-template-columns:repeat(2,minmax(0,1fr));}
    .ob li{display:flex;flex-direction:column;gap:2px;padding:var(--s3);}
  }

  .incl{background:var(--ground-2);border:1px solid var(--line);border-radius:var(--r-md);
    padding:var(--s6) var(--s5);display:flex;flex-direction:column;gap:var(--s4);}
  .incl h3{margin:0;font-size:var(--f-h4);font-weight:650;letter-spacing:var(--t-head);}
  .incl-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:var(--s5);}
  .incl-grid div p,.term p{margin:var(--s1) 0 0;font-size:var(--f-body);color:var(--ink-2);line-height:1.55;}
  .term summary{list-style:none;font-family:var(--mono);font-size:var(--f-micro);
    letter-spacing:var(--t-caps);text-transform:uppercase;color:var(--cyan-text);}
  .term summary::-webkit-details-marker{display:none;}
  @media(max-width:759px){
    .incl-grid.terms{gap:0;}
    .term{border-top:1px solid var(--line);}
    .term summary{display:flex;align-items:center;justify-content:space-between;min-height:44px;
      cursor:pointer;}
    .term summary::after{content:"+";font-size:var(--f-lede);color:var(--ink-2);}
    .term[open] summary::after{content:"-";}
    .term p{margin:0 0 var(--s3);}
  }
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
    /* 2026-10-06 (the same clip the YouTube hero used until release 10): the iframe is oversized by the
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
     the old wood-siding photo. A real image element (lazy, intrinsic size) rather
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

  /* Reel wheel buttons (release 34): see reel() and CLAUDE.md */
  .cta{display:inline-flex;align-items:center;gap:var(--s2);border-radius:var(--r-pill);
    font-size:var(--f-body);font-weight:700;text-decoration:none;}
  .cta:not(.ghost),.navcta,.actionbar a.primary{--btn-bg:#14171A;--btn-hover:#23292E;
    --btn-press:#0B0D0F;--btn-edge:#14171A;--btn-cur:var(--btn-bg);
    position:relative;isolation:isolate;color:#FFFFFF;}
  .hero-bold .cta:not(.ghost),.hero-dark .cta:not(.ghost),.on-ink .cta:not(.ghost),.navcta{
    --btn-bg:#262B30;--btn-hover:#30363C;--btn-press:#1A1E22;--btn-edge:#3D444B;}
  .cta:not(.ghost){--d:56px;--bh:44px;min-height:var(--d);background:transparent;
    padding:calc(var(--d) - var(--bh) + 8px) 22px 8px calc(var(--d) + 12px);}
  .cta:not(.ghost)::before,.navcta::before{content:"";position:absolute;z-index:-1;
    left:calc(var(--d) / 2);right:0;top:calc(var(--d) - var(--bh));bottom:0;
    background:var(--btn-cur);box-shadow:inset 0 0 0 1px var(--btn-edge);
    border-radius:0 var(--r-sm) var(--r-sm) 0;}
  @media(hover:hover){
    .cta:not(.ghost):hover,.navcta:hover,.actionbar a.primary:hover{--btn-cur:var(--btn-hover);}}
  .cta:not(.ghost):active,.navcta:active,.actionbar a.primary:active{--btn-cur:var(--btn-press);
    transform:translateY(1px);}
  .cta:focus-visible{outline:2px solid var(--orange);outline-offset:3px;}
  .bm-defs{position:absolute;width:0;height:0;overflow:hidden;}
  /* a half-parsed button (reel in, label not yet) paints nothing: the bar's centred reel
     moved when its label arrived (CLS); .bm-gate.b is the last child reel() writes */
  :is(.cta,.navcta,.actionbar a.primary):not(:has(> .bm-gate.b)) > *{visibility:hidden;}
  .bm-wheel{position:absolute;left:0;bottom:0;width:var(--d);height:var(--d);
    fill:var(--btn-cur);transition:transform .5s cubic-bezier(.2,.6,.3,1);}
  .bm-gate{position:absolute;left:calc(var(--d) + 2px);right:4px;margin-inline:auto;height:4px;
    width:calc(100% - var(--d) - 6px);width:round(down,100% - var(--d) - 6px,12px);
    overflow:hidden;pointer-events:none;}
  .bm-gate.t{top:calc(var(--d) - var(--bh) + 3px);}
  .bm-gate.b{bottom:3px;}
  .bm-gate::before{content:"";position:absolute;top:0;bottom:0;left:-12px;right:-12px;
    background:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='5' viewBox='0 0 12 5' preserveAspectRatio='none'%3E%3Crect x='3' width='6' height='5' rx='1.3' fill='%23F5F4F1'/%3E%3C/svg%3E") 0 0/12px 100% repeat-x;
    transition:transform .45s cubic-bezier(.2,.6,.3,1);}
  @media(hover:hover) and (prefers-reduced-motion:no-preference){
    .cta:hover .bm-wheel,.navcta:hover .bm-wheel,.actionbar a.primary:hover .bm-wheel{
      transform:rotate(-40deg);}
    .cta:hover .bm-gate::before,.navcta:hover .bm-gate::before,
    .actionbar a.primary:hover .bm-gate::before{transform:translateX(12px);}
  }
  .cta.ghost{background:transparent;color:var(--ink);border:1px solid var(--hair);
    padding:14px var(--s5);font-weight:650;}
  @media(hover:hover){.cta.ghost:hover{border-color:var(--ink-3);}}
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

  /* Crew (release 24, owner). TEAM_ROSTER is in reading order, which is also the
     phone order: one card per row below 760px, the site's phone breakpoint (the
     action bar and TERMS_JS use the same one). From 760px it is one row of three and
     the first person sits in the middle column by grid placement; dense flow puts the
     second in the left column and the third on the right. The DOM, focus and screen
     reader order never change. Below 760px a card is capped at 420px and centred, so
     on a small tablet the 4:5 frame does not fill the screen; at 390 the cap never
     bites and the frame spans the column. */
  .roster{display:grid;grid-template-columns:minmax(0,1fr);gap:var(--s6);}
  .roster > .member{width:100%;max-width:420px;margin:0 auto;}
  @media(min-width:760px){
    .roster{grid-template-columns:repeat(3,minmax(0,1fr));grid-auto-flow:row dense;
      gap:var(--s5) var(--s4);align-items:start;}
    .roster > .member{max-width:none;}
    .roster > .member:first-child{grid-column:2;}
  }
  /* 4:5 crew frames (release 19, owner): Yoni's photo is a tight 4:5 portrait and only a
     4:5 frame holds both his hair and the HSS logo on his shirt. Paloma's and Sergy's are
     700x700 squares, so in the same frame object-fit:cover trims only their sides (10%
     each), which keeps their faces and logos whole. Leadership stays 3:4. */
  .member .portrait{aspect-ratio:4/5;margin-bottom:var(--s3);}
  .member h3{margin:0;font-size:var(--f-body);font-family:var(--display);font-weight:600;
    letter-spacing:var(--t-head);}
  .member .rtitle{display:block;margin-top:1px;font-family:var(--mono);font-size:var(--f-micro);
    letter-spacing:var(--t-caps);text-transform:uppercase;color:var(--ink-3);}
  /* Optional crew bio. Sizes come from the same tokens .lead p uses, one step
     down, so a filled card and an empty one still sit on the same grid. */
  .member .mbio{margin:var(--s2) 0 0;font-size:var(--f-sm);line-height:1.5;
    color:var(--ink-2);}
  /* Optional bio teaser (release 24): see member_card() and BIO_JS. Without JS the whole
     bio shows and the ellipsis and the toggle stay hidden. BIO_JS adds .js-cut; at every
     width (release 34; phones only before) that shows the lead, "...", then "Read more".
     .is-open shows the rest, with "Show less" at the end. The toggle reads as a
     link (--orange-text, underlined: 5.9:1 on white) and its ::after gives it a 44px
     tall hit area without touching the line box, so no text moves. */
  .mbio .ell,.mbio .bio-tog{display:none;}
  .bio-tog{position:relative;padding:0;margin:0;border:0;background:none;font:inherit;
    color:var(--orange-text);text-decoration:underline;text-decoration-thickness:1px;
    text-underline-offset:.16em;cursor:pointer;border-radius:var(--r-sm);}
  .bio-tog::after{content:"";position:absolute;left:-6px;right:-6px;top:50%;height:44px;
    margin-top:-22px;}
  /* hover only where it exists, or a tap leaves the thick underline stuck on phones;
     the ring sits 1px out so it clears the full stop before "Show less" */
  @media(hover:hover){.bio-tog:hover{text-decoration-thickness:2px;}}
  .bio-tog:focus-visible{outline:2px solid var(--orange);outline-offset:1px;}
  .mbio.js-cut .bio-tog{display:inline-block;}
  .mbio.js-cut:not(.is-open) .ell{display:inline;}
  .mbio.js-cut:not(.is-open) .rest{display:none;}

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

# The nav button reserves its long label's width (font-swap CLS, see .navcta). "Start a
# project" needs 7em; with booking on the label is "Book a call", 5.03em in Onest (measured,
# release 37), so it reserves 5.2em.
if BOOKED:
    assert CSS.count("  :root{\n") == 1
    CSS = CSS.replace("  :root{\n", "  :root{\n    --cta-em:5.2em; --cta-k:5.2;\n", 1)

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
      /* a hover-play spot card resets itself (pause, 0:00, poster back on) */
      if(v.parentNode && v.parentNode.classList && v.parentNode.classList.contains('vspot')){
        v.dispatchEvent(new Event('spotstop'));
        continue;
      }
      if(!v.paused) v.pause();
      if(v.currentTime !== 0){
        try { v.currentTime = 0; } catch(err) { /* not seekable yet */ }
      }
    }
  }, true);

  /* Hover-play spots (.vspot: the All Heart and Handyman Dan films, self-hosted
     since release 4). The whole film plays, not a preview.
     - Real hover (hover:hover and pointer:fine), no reduced motion: entering the
       card plays from 0:00, muted (browsers refuse sound without a click);
       leaving pauses, rewinds to 0:00 and puts the poster back. A click turns
       sound on (a click is a user gesture, so unmuted play is allowed) and the
       film keeps playing; another click mutes it again. Once sound has been
       turned on, later hovers try with sound and fall back to muted if the
       browser refuses (NotAllowedError).
     - Touch, reduced motion, and the keyboard everywhere (Enter/Space on the
       button; a keyboard-activated click has e.detail 0): play and pause with
       sound, nothing starts by itself, focus alone never plays.
     - The end of a film puts the card back to its poster.
     - Hover means the pointer really moved over the card (release 8, E). When
       the page scrolls under a resting mouse, the browser sends enter events for
       whatever lands beneath it; those only arm a card. It starts on a pointer
       move whose screen position actually changed (synthetic post-scroll events
       keep the old one), at least 200ms after the last scroll, then the 120ms
       intent delay. Leaving still stops it at once.
     One at a time is the rule above: starting any video sends 'spotstop' to
     every other card. Only the films' first frames load before anything plays:
     preload="none", so a page load fetches no video at all. */
  var vspots = [].slice.call(document.querySelectorAll('.vspot'));
  if(vspots.length){
    var mm = function(q){ return !!(window.matchMedia && window.matchMedia(q).matches); };
    var hoverUI = mm('(hover: hover) and (pointer: fine)') && !mm('(prefers-reduced-motion: reduce)');
    var soundOn = false;
    var now = function(){ return (window.performance && performance.now) ? performance.now() : Date.now(); };
    var lastScroll = -1e9, sx = null, sy = null, realMove = false;
    if(hoverUI){
      window.addEventListener('scroll', function(){ lastScroll = now(); }, {passive: true});
      /* capture phase, so every card's own move listener sees this verdict */
      document.addEventListener('pointermove', function(e){
        /* the first move after load has nothing to compare with; the 200ms scroll
           guard still catches a synthetic one, which follows a scroll by ~100ms */
        realMove = e.pointerType === 'mouse' && (sx === null || e.screenX !== sx || e.screenY !== sy);
        sx = e.screenX; sy = e.screenY;
      }, {capture: true, passive: true});
    }
    vspots.forEach(function(el){
      var v = el.querySelector('video');
      var btn = el.querySelector('.vplay');
      if(!v || !btn) return;
      var card = el.closest('.spot') || el;
      var title = btn.getAttribute('data-title') || '';
      var over = false, armed = false, wait = 0;
      card.classList.add('is-vcard');
      if(hoverUI) el.classList.add('hover-ui');

      function state(st){
        el.setAttribute('data-state', st);
        btn.setAttribute('aria-label', (st === 'sound' ? 'Pause ' : 'Play ') + title);
      }
      function stop(){
        clearTimeout(wait); wait = 0;
        if(!v.paused) v.pause();
        try { if(v.currentTime) v.currentTime = 0; } catch(err){ /* not seekable yet */ }
        el.classList.remove('is-live');
        state('idle');
      }
      function play(withSound, fromStart){
        /* captions: the track ships disabled so nothing loads with the page;
           showing it here fetches it, and it stays on for every later play */
        if(v.textTracks && v.textTracks.length && v.textTracks[0].mode !== 'showing'){
          v.textTracks[0].mode = 'showing';
        }
        if(fromStart){ try { v.currentTime = 0; } catch(err){} }
        v.muted = !withSound;
        state(withSound ? 'sound' : 'muted');
        var pr = v.play();
        if(pr && pr.catch) pr.catch(function(err){
          /* AbortError means it was stopped before it started: nothing to do */
          if(!err || err.name !== 'NotAllowedError') return;
          if(!v.muted && hoverUI && over){
            v.muted = true;
            state('muted');
            var again = v.play();
            if(again && again.catch) again.catch(function(){ stop(); });
          } else {
            stop();
          }
        });
      }
      v.addEventListener('playing', function(){ el.classList.add('is-live'); });
      v.addEventListener('ended', stop);
      v.addEventListener('spotstop', stop);

      if(hoverUI){
        card.addEventListener('pointerenter', function(e){
          if(e.pointerType !== 'mouse') return;
          over = true; armed = true;
        });
        card.addEventListener('pointermove', function(e){
          if(!over || !armed || wait || !realMove || now() - lastScroll < 200) return;
          /* a short intent delay: a pointer crossing the grid on its way
             somewhere else starts, and downloads, nothing */
          wait = setTimeout(function(){
            wait = 0;
            if(over && armed && now() - lastScroll >= 200){ armed = false; play(soundOn, true); }
          }, 120);
        });
        card.addEventListener('pointerleave', function(e){
          if(e.pointerType !== 'mouse') return;
          over = false; armed = false; stop();
        });
      }

      card.addEventListener('click', function(e){
        var st = el.getAttribute('data-state');
        clearTimeout(wait); wait = 0;
        if(hoverUI && e.detail !== 0){
          if(st === 'sound'){ v.muted = true; state('muted'); return; }
          soundOn = true;
          if(st === 'muted' && !v.paused){ v.muted = false; state('sound'); }
          else play(true, st === 'idle');
          return;
        }
        if(st === 'sound'){ v.pause(); state('paused'); return; }
        soundOn = true;
        if(st === 'muted' && !v.paused){ v.muted = false; state('sound'); }
        else play(true, st === 'idle');
      });
    });
  }

  /* Ambient YouTube backgrounds: autoplay muted, only once actually on
     screen (nothing loads up front, not even the IFrame API script), pause
     on scroll out, resume in place on return, and loop back to their
     data-start mark rather than to zero. None of that is native <video>
     behavior, so it cannot reuse the seek/ended/loadedmetadata logic above;
     the YouTube IFrame Player API has its own equivalents (seekTo,
     onStateChange, playVideo/pauseVideo). Since release 10 only the /our-work Quality banner uses it (the homepage
     hero is self-hosted); it stays a function for a second ambient embed: each gets its own player/observer
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


MOTION_JS = """<script>
(function(){
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* (a) scroll reveals ---------------------------------------------------- */
  if(!reduce && 'IntersectionObserver' in window){
    var SEL = '.sec-head,.pcard,.benefit,.pkg,.csi > div,.op,.spot,.reel,' +
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
  var nums = [].slice.call(document.querySelectorAll('.stat .n, .op .n, .reel .vnum'))
    .filter(function(e){ return !e.hasAttribute('data-static'); });
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

  /* (d) banner push in: the /our-work banner is a YouTube embed, so "started
     playing" is a YT.Player onStateChange event, handled in SOLO_JS next to the
     rest of the banner's ambient-play logic, not here. The homepage hero is
     self-hosted since release 10 (HERO_JS) and has no push in. */

})();
</script>"""


# The YouTube click-to-play spot cards, used only by the inline artifact build now
# (it cannot carry the self-hosted films under its 16MB cap; see spot()). The web
# build has no .ytspot left and does not ship this. Was MOTION_JS section (h).
YT_SPOT_JS = """<script>
(function(){
  /* YouTube spots, click to play. Plain iframe swap, not the IFrame Player
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
  /* ?campaign= prefills "Anything else" (release 28: the Handyman Dan section on
     /our-work links here). Only known values count, each mapped to a fixed sentence;
     anything else in the address is ignored, and the text goes in through .value, so
     nothing from the URL ever reaches the page. Only into an empty field. */
  var PREFILL = {'handyman-dan': "I'd like to run the Handyman Dan campaign in my market.",
                 'brand-video': "I'd like a brand video for my company.",
                 'social-audit': "I'd like the free social audit and content calendar.",
                 'content-calendar': "I'd like the free social audit and content calendar.",
                 'commercial-shoot': "I'd like to talk about a commercial shoot.",
                 'podcast': "I'd like to talk about producing a podcast."};
  try {
    var want = new URLSearchParams(location.search).get('campaign');
    var note = document.getElementById('f-message');
    if(note && want && Object.prototype.hasOwnProperty.call(PREFILL, want) && !note.value.trim()){
      note.value = PREFILL[want];
    }
  } catch(err){}
  var btn = document.getElementById('cbtn');
  var status = document.getElementById('fstatus');
  /* the button is a Reel wheel (reel()): only its .bm-label text changes while sending */
  var lab = btn.querySelector('.bm-label') || btn;
  var LABEL = lab.textContent;

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
    btn.disabled = false; lab.textContent = LABEL;
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

    btn.disabled = true; lab.textContent = 'Sending...';

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

# ---- Free social audit: a chat-style bubble and panel (release 37, owner) --------------
# Release 35 shipped this offer as a pop-up that opened on the first scroll; release 36b took
# the trigger out and release 37 replaces the pop-up with a launcher. Nothing ever opens by
# itself any more.
# - The bubble (CAL_BUBBLE): a round charcoal <button> with the orange reel, fixed bottom
#   right on every page but /contact/, with a "Free social audit" label pill beside it. It
#   ships hidden and CAL_JS shows it, so without JS there is no dead control. Owner change
#   (release 37): the label is always visible, at every width, pill and reel as one unit; below
#   360px it reads "Free audit". On phones it sits above the action bar, and the homepage hero's
#   text sits higher so the unit never covers the headline.
# - The panel (CAL_HTML): one native <dialog> per page, opened with showModal(), so the page
#   goes inert, focus is held inside, and Esc, the backdrop, the 44px X and "No thanks, keep
#   browsing" all close it. Focus returns to whatever opened it. From 760px it is a 392px chat
#   panel anchored above the bubble; below that a bottom sheet (at most 85% of the screen).
# - The bubble and the footer link "Free social audit" (site_footer, every page) open it.
#   Without JS the footer link goes to the contact form with its own prefill.
# - It posts to the contact form's FormSubmit AJAX endpoint (FORM_TO): _subject "Free social
#   audit + content calendar - <website or first handle>", _replyto, _template table, the
#   honeypot (named "fax": the contact form's is "website", and this form has a real website
#   field), lead_type=social-audit-calendar and the page it was opened on. Success replaces the
#   form in the panel and turns the pill into "Audit requested" for the rest of the visit
#   (sessionStorage); failure keeps everything typed and offers a retry and an email.
CAL_LEGAL = "We'll use this to build your calendar and follow up about it. We never sell your information."


def _cal_week():
    """A sample week, flat: Monday to Friday a reel (orange), Saturday and Sunday a graphic
    (cyan). Desktop panel only. The weekday letters are HTML, not SVG <text>: a visible SVG
    <text> in Archivo once made that face miss its font window."""
    cw, g = 20, 4
    cells = "".join(f"M{c * (cw + g)} 0h{cw}v{cw}h-{cw}z" for c in range(7))
    uses = "".join(f'<use href="#cal-{"g" if c >= 5 else "r"}" x="{c * (cw + g)}" y="0"/>' for c in range(7))
    letters = "".join(f"<span>{d}</span>" for d in "MTWTFSS")
    return (f'<div class="cal-week"><div><p class="cal-wd" aria-hidden="true">{letters}</p>'
            f'<svg viewBox="0 0 {7 * cw + 6 * g} {cw}" role="img" aria-label="A sample week: a reel '
            f'every weekday and a graphic on Saturday and Sunday">'
            '<defs><g id="cal-r"><rect x="6" y="3" width="8" height="14" rx="1.5" fill="#F04820"/>'
            '<path d="M8.8 7.5v5l3.6-2.5z" fill="#FFFFFF"/></g>'
            '<g id="cal-g"><rect x="4" y="4" width="12" height="12" rx="1.5" fill="#00B0C8"/>'
            '<path d="M5.5 14.6l3.8-4.6 2.3 2.7 1.5-1.5 1.6 3.4z" fill="#14171A"/>'
            '<circle cx="12.8" cy="7.4" r="1.4" fill="#14171A"/></g></defs>'
            f'<path d="{cells}" fill="#262B30"/>{uses}</svg></div>'
            '<p class="cal-key" aria-hidden="true"><span class="k-r">Reels on weekdays</span>'
            '<span class="k-g">Graphics on weekends</span></p></div>')


def _cal_field(name, label, kind="text", req=False, ac="", im="", hint=""):
    attrs = (f' autocomplete="{ac}"' if ac else '') + (f' inputmode="{im}"' if im else '')
    if kind == "text" and name in ("instagram", "tiktok", "facebook", "youtube"):
        attrs += ' autocapitalize="none" autocorrect="off" spellcheck="false"'
    req_a = ' required aria-required="true"' if req else ''
    ph = f' placeholder="{hint}"' if hint else ''
    return (f'<div class="cal-fld"><label for="cal-{name}">{label}</label>'
            f'<input id="cal-{name}" name="{name}" type="{kind}"{attrs}{req_a}{ph} '
            f'aria-describedby="cal-{name}-e"><p class="cal-e" id="cal-{name}-e"></p></div>')


CAL_HTML = (
    '<dialog class="cal on-ink" id="cal" aria-labelledby="cal-h">'
    '<span class="cal-rail" aria-hidden="true"></span>'
    '<button type="button" class="cal-x" aria-label="Close"><svg viewBox="0 0 24 24" width="22" '
    'height="22" aria-hidden="true" focusable="false"><path d="M6 6l12 12M18 6L6 18" '
    'stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg></button>'
    '<div class="cal-body">'
    '<p class="eyebrow">Free for home service companies</p>'
    '<h2 class="cal-h" id="cal-h" tabindex="-1" autofocus>Get a free social audit and content '
    'calendar.</h2>'
    "<p class=\"cal-sub\">We'll audit your existing social first. Then we'll plan your next 30 days "
    "of content, built for your trade and your market.</p>"
    "<p class=\"cal-when\">We'll email both to you within 3 business days.</p>"
    + _cal_week() +
    '<form class="cal-f" id="cal-f" novalidate>'
    + _cal_field("name", "Your name", req=True, ac="name")
    + _cal_field("email", "Email", "email", True, "email", "email")
    + _cal_field("phone", "Phone", "tel", True, "tel", "tel")
    + '<fieldset class="cal-where" aria-describedby="cal-where-e"><legend>Where you post '
      '<span>At least one</span></legend>'
    + _cal_field("website", "Business website", "url", ac="url", im="url", hint="yourcompany.com")
    + _cal_field("instagram", "Instagram", hint="@handle or link")
    + _cal_field("tiktok", "TikTok", hint="@handle or link")
    + _cal_field("facebook", "Facebook", hint="Page name or link")
    + _cal_field("youtube", "YouTube", hint="Channel or link")
    + '<p class="cal-e" id="cal-where-e"></p></fieldset>'
    '<input type="hidden" name="lead_type" value="social-audit-calendar">'
    '<input type="hidden" name="page" value="">'
    '<div class="cal-hp" aria-hidden="true"><label for="cal-fax">Fax</label>'
    '<input id="cal-fax" name="fax" type="text" tabindex="-1" autocomplete="off"></div>'
    f'<button type="submit" class="cta">{reel("Get my free audit")}</button>'
    '<p class="cal-st" role="alert"></p>'
    f'<p class="cal-legal">{CAL_LEGAL}</p>'
    '<button type="button" class="cal-skip">No thanks, keep browsing</button>'
    '</form>'
    '<div class="cal-done" hidden><h3 tabindex="-1">You&#39;re in. Watch your inbox.</h3>'
    '<button type="button" class="cal-skip">Keep browsing</button></div>'
    '</div></dialog>')

CAL_BUBBLE = ('<button type="button" class="calb" data-cal hidden aria-haspopup="dialog" '
              'aria-expanded="false" aria-controls="cal" aria-label="Get a free social audit and '
              'content calendar"><span class="calb-pill"><span class="calb-l">Free social audit</span>'
              '<span class="calb-s">Free audit</span></span><span class="calb-ic">'
              '<svg class="calb-reel" viewBox="0 0 56 56" aria-hidden="true" focusable="false">'
              '<use href="#bm-reel"/></svg><svg class="calb-down" viewBox="0 0 24 24" '
              'aria-hidden="true" focusable="false"><path d="M6 9l6 6 6-6" fill="none" '
              'stroke="currentColor" stroke-width="2.4" stroke-linecap="round" '
              'stroke-linejoin="round"/></svg></span></button>')

CAL_CSS = """<style>
  html{scrollbar-gutter:stable;}
  html.cal-lock{overflow:hidden;}
  .calb{position:fixed;right:24px;bottom:24px;z-index:54;display:flex;align-items:center;
    padding:0;border:0;border-radius:var(--r-lg);background:none;color:#FFFFFF;cursor:pointer;}
  .calb[hidden]{display:none;}
  .calb:focus-visible{outline:2px solid var(--orange);outline-offset:3px;}
  .calb-pill,.calb-ic{background:#14171A;border:1px solid #3D444B;
    box-shadow:0 6px 20px rgba(20,23,26,.28);transition:background var(--ease);}
  .calb-pill{display:flex;align-items:center;height:40px;margin-right:-26px;padding:0 38px 0 16px;
    border-radius:var(--r-lg);white-space:nowrap;font:600 var(--f-sm)/1 'Onest',-apple-system,sans-serif;}
  .calb-s{display:none;}
  .calb-ic{position:relative;flex:none;width:56px;height:56px;display:flex;align-items:center;
    justify-content:center;border-radius:50%;}
  .calb-reel{display:block;width:34px;height:34px;fill:#262B30;
    transition:transform .5s cubic-bezier(.2,.6,.3,1);}
  .calb-down{display:none;width:24px;height:24px;}
  .calb[aria-expanded="true"] .calb-reel{display:none;}
  .calb[aria-expanded="true"] .calb-down{display:block;}
  @media(hover:hover){.calb:hover .calb-pill,.calb:hover .calb-ic{background:#23292E;}}
  @media(hover:hover) and (prefers-reduced-motion:no-preference){
    .calb:hover .calb-reel{transform:rotate(-40deg);}}
  @media(min-width:760px){body:has(> .calb:not([hidden])){padding-bottom:96px;}}
  @media(max-width:759px){
    .calb{right:12px;bottom:calc(66px + env(safe-area-inset-bottom));}
    .calb-pill{height:36px;margin-right:-22px;padding:0 32px 0 12px;}
    .calb-ic{width:48px;height:48px;}
    .calb-reel{width:30px;height:30px;}
    body:has(> .calb:not([hidden])){padding-bottom:calc(134px + env(safe-area-inset-bottom));}
  }
  @media(max-width:359px){.calb-l{display:none;}.calb-s{display:inline;}}
  .cal{position:fixed;inset:auto 24px 92px auto;margin:0;padding:0;
    width:min(392px,calc(100vw - 48px));max-width:none;max-height:min(80vh,calc(100vh - 116px));
    border:1px solid #33383D;border-radius:var(--r-lg);color:#FFFFFF;overflow:hidden;
    box-shadow:0 18px 48px rgba(0,0,0,.35);}
  .cal[open]{display:flex;flex-direction:column;}
  .cal [hidden]{display:none;}
  .cal::backdrop{background:rgba(10,12,14,.18);}
  .cal-rail{display:block;flex:none;height:14px;background:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='6'%3E%3Crect x='3' width='8' height='6' rx='1.5' fill='%23F5F4F1'/%3E%3C/svg%3E") 0 4px/14px 6px space no-repeat #262B30;}
  .cal-x{position:absolute;top:22px;right:12px;z-index:2;width:44px;height:44px;display:flex;
    align-items:center;justify-content:center;border:1px solid #4B535B;border-radius:var(--r-md);
    background:#262B30;color:#FFFFFF;cursor:pointer;}
  .cal-x:hover{border-color:#A8A29A;}
  .cal-x:focus-visible,.cal-skip:focus-visible,.cal input:focus-visible{outline:2px solid var(--orange);
    outline-offset:2px;}
  .cal-body{overflow:auto;overscroll-behavior:contain;padding:24px 24px 20px;}
  .cal-h:focus{outline:none;}
  .cal-h{margin:var(--s2) 52px 0 0;font:700 var(--f-h3)/1.15 var(--display);letter-spacing:var(--t-head);}
  .cal-sub{margin:var(--s3) 0 0;font-size:var(--f-body);line-height:1.55;color:#D8D3C9;}
  .cal-when{margin:var(--s2) 0 0;font-size:var(--f-sm);color:#A8A29A;}
  .cal-week{display:flex;align-items:flex-end;gap:var(--s4);margin:var(--s4) 0 0;}
  .cal-wd{display:grid;grid-template-columns:repeat(7,20px);column-gap:4px;margin:0 0 5px;
    font:700 10px/1 var(--display);letter-spacing:.04em;color:#A8A29A;text-align:center;}
  .cal-week svg{display:block;width:164px;height:20px;}
  .cal-key{display:flex;flex-direction:column;gap:5px;margin:0;font-size:var(--f-micro);
    line-height:1.2;color:#D8D3C9;}
  .cal-key span::before{content:"";display:inline-block;width:9px;height:9px;border-radius:2px;
    margin-right:6px;vertical-align:0;background:#F04820;}
  .cal-key .k-g::before{background:#00B0C8;}
  .cal-f{display:grid;grid-template-columns:minmax(0,1fr);gap:10px;margin-top:20px;}
  .cal-fld{display:flex;flex-direction:column;gap:6px;min-width:0;}
  .cal-fld label{font-size:var(--f-sm);font-weight:600;color:#FFFFFF;}
  .cal input{width:100%;min-height:44px;padding:10px 12px;font:inherit;font-size:16px;
    color:#FFFFFF;background:#1E2226;border:1px solid #4B535B;border-radius:var(--r-sm);}
  .cal input::placeholder{color:#8C939A;}
  .cal input[aria-invalid="true"]{border-color:#F04820;}
  .cal-e{margin:0;font-size:var(--f-sm);color:#F04820;}
  .cal-e:empty{display:none;}
  .cal-where{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin:6px 0 0;
    padding:14px 0 0;border:0;border-top:1px solid #33383D;min-width:0;}
  .cal-where legend{float:left;grid-column:1 / -1;padding:0;font-size:var(--f-sm);font-weight:600;}
  .cal-where legend span{margin-left:var(--s2);font-weight:400;color:#A8A29A;}
  .cal-where > .cal-fld:first-of-type,.cal-where > .cal-e{grid-column:1 / -1;}
  .cal-hp{position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden;}
  .cal-f > .cta{justify-self:start;margin-top:var(--s3);border:0;cursor:pointer;font-family:inherit;}
  .cal-f > .cta[disabled]{opacity:.6;cursor:default;}
  .cal-st{margin:0;font-size:var(--f-sm);line-height:1.5;color:#F04820;}
  .cal-st:empty{display:none;}
  .cal-st a{color:#FFFFFF;}
  .cal-legal{margin:0;font-size:var(--f-sm);line-height:1.5;color:#A8A29A;}
  .cal-skip{justify-self:start;min-height:44px;padding:0;border:0;background:none;
    font:inherit;font-size:var(--f-body);color:#FFFFFF;text-decoration:underline;
    text-underline-offset:.2em;cursor:pointer;}
  .cal-done h3{margin:var(--s5) 0 0;font:700 var(--f-h3)/1.2 var(--display);}
  .cal-done h3:focus{outline:none;}
  .cal-done .cal-skip{margin-top:var(--s2);}
  @media(max-width:759px){
    .cal{inset:auto 0 0 0;width:100%;max-height:85dvh;border-radius:var(--r-lg) var(--r-lg) 0 0;
      border-width:1px 0 0;}
    .cal::backdrop{background:rgba(10,12,14,.55);}
    .cal-body{padding:var(--s5) var(--s5) var(--s6);}
    .cal-x{top:20px;right:10px;}
    .cal-week{display:none;}
  }
  @media(prefers-reduced-motion:no-preference){
    .cal[open]{transform-origin:100% 100%;animation:cal-in .22s cubic-bezier(.2,.6,.3,1);}
    .cal[open]::backdrop{animation:cal-fade .22s ease;}
  }
  @media(prefers-reduced-motion:no-preference) and (max-width:759px){
    .cal[open]{animation-name:cal-up;animation-duration:.3s;}
  }
  @media(prefers-reduced-motion:reduce){.calb-pill{transition:none;}}
  @keyframes cal-in{from{opacity:0;transform:translateY(8px) scale(.98);}}
  @keyframes cal-up{from{transform:translateY(100%);}}
  @keyframes cal-fade{from{opacity:0;}}
</style>"""

CAL_JS = """<script>
(function(){
  try { localStorage.removeItem('hss-cal'); } catch(e){}
  var d = document.getElementById('cal');
  if(!d || !d.showModal) return;
  var f = document.getElementById('cal-f'), bub = document.querySelector('.calb'), mem = {};
  var btn = f.querySelector('button[type=submit]'), lab = btn.querySelector('.bm-label');
  var LABEL = lab.textContent, st = f.querySelector('.cal-st'), done = d.querySelector('.cal-done');
  var body = d.querySelector('.cal-body'), opener = null, y0 = 0;
  var WHERE = ['website', 'instagram', 'tiktok', 'facebook', 'youtube'];
  var MSG = {name: 'Enter your name.', email: 'Enter a valid email address.',
    phone: 'Enter a 10-digit US phone number.', website: 'Enter a website like yourcompany.com.',
    where: 'Add your website or at least one social account, so we know where to look.'};
  function sget(k){ try { return sessionStorage.getItem(k) || mem[k]; } catch(e){ return mem[k]; } }
  function sset(k){ mem[k] = '1'; try { sessionStorage.setItem(k, '1'); } catch(e){} }
  /* the accessible name always contains the visible label: "Free audit" below 360px */
  var narrow = matchMedia('(max-width: 359px)');
  function name(){
    if(!bub) return;
    var done = bub.classList.contains('is-done');
    bub.setAttribute('aria-label', (done ? 'Audit requested. ' : (narrow.matches ? 'Free audit: ' : ''))
      + (narrow.matches && !done ? 'get' : 'Get') + ' a free social audit and content calendar');
  }
  function requested(){
    if(!bub || bub.classList.contains('is-done')) return;
    bub.classList.add('is-done');
    [].forEach.call(bub.querySelectorAll('.calb-l, .calb-s'), function(e){ e.textContent = 'Audit requested'; });
    name();
  }
  if(bub){
    bub.hidden = false;
    if(sget('hss-audit')) requested();
    name();
    if(narrow.addEventListener) narrow.addEventListener('change', name);
  }
  function open(from){
    if(d.open) return;
    opener = from || document.activeElement; y0 = window.scrollY;
    f.elements.page.value = location.pathname;
    document.documentElement.classList.add('cal-lock');
    if(bub) bub.setAttribute('aria-expanded', 'true');
    d.showModal();
    body.scrollTop = 0;
  }
  d.addEventListener('close', function(){
    document.documentElement.classList.remove('cal-lock');
    if(bub) bub.setAttribute('aria-expanded', 'false');
    if(opener && opener !== document.body && opener.focus) opener.focus({preventScroll: true});
    if(Math.abs(window.scrollY - y0) > 1) window.scrollTo(0, y0);
  });
  [].forEach.call(d.querySelectorAll('.cal-x, .cal-skip'), function(b){
    b.addEventListener('click', function(){ d.close(); });
  });
  d.addEventListener('click', function(e){ if(e.target === d) d.close(); });
  document.addEventListener('click', function(e){
    var a = e.target.closest && e.target.closest('[data-cal]');
    if(a){ e.preventDefault(); open(a); }
  });
  function show(el, m){
    var e = document.getElementById(el.id + '-e');
    if(e) e.textContent = m;
    if(m) el.setAttribute('aria-invalid', 'true'); else el.removeAttribute('aria-invalid');
    return !m;
  }
  function check(el){
    var v = el.value.trim(), m = '';
    if(el.name === 'name' && !v) m = MSG.name;
    if(el.name === 'email' && !/^[^\\s@]+@[^\\s@]+\\.[^\\s@]{2,}$/.test(v)) m = MSG.email;
    if(el.name === 'phone'){ var n = v.replace(/\\D/g, '');
      if(n.length === 11 && n.charAt(0) === '1') n = n.slice(1);
      if(!/^[2-9][0-9]{9}$/.test(n)) m = MSG.phone; }
    if(el.name === 'website' && v && !/^(https?:\\/\\/)?[^\\s\\/.]+(\\.[^\\s\\/.]+)+(\\/\\S*)?$/i.test(v)) m = MSG.website;
    return show(el, m);
  }
  function where(){
    var any = WHERE.some(function(k){ return f.elements[k].value.trim(); });
    document.getElementById('cal-where-e').textContent = any ? '' : MSG.where;
    return any;
  }
  [].forEach.call(f.querySelectorAll('input[aria-describedby]'), function(el){
    el.addEventListener('blur', function(){ if(el.value.trim() || el.required) check(el); });
    el.addEventListener('input', function(){
      if(el.getAttribute('aria-invalid')) check(el);
      if(WHERE.indexOf(el.name) > -1 && document.getElementById('cal-where-e').textContent) where();
    });
  });
  function tag(x){
    var w = x.website.replace(/^https?:\\/\\//i, '').replace(/^www\\./i, '').split(/[\\/?#]/)[0];
    return w || x.instagram || x.tiktok || x.facebook || x.youtube || x.name;
  }
  f.addEventListener('submit', function(e){
    e.preventDefault();
    st.textContent = '';
    var bad = null;
    ['name', 'email', 'phone', 'website'].forEach(function(k){
      if(!check(f.elements[k]) && !bad) bad = f.elements[k]; });
    if(!where() && !bad) bad = f.elements.website;
    if(bad){ bad.focus(); return; }
    var x = {};
    [].forEach.call(f.elements, function(el){ if(el.name) x[el.name] = el.value.trim(); });
    x._honey = x.fax; delete x.fax;
    x._subject = 'Free social audit + content calendar - ' + tag(x);
    x._replyto = x.email; x._template = 'table'; x._captcha = 'false';
    btn.disabled = true; lab.textContent = 'Sending...';
    fetch('__FORM_ENDPOINT__', {method: 'POST',
      headers: {'content-type': 'application/json', 'accept': 'application/json'},
      body: JSON.stringify(x)
    }).then(function(r){
      return r.json().then(function(j){ return {ok: r.ok, j: j}; }, function(){ return {ok: r.ok, j: {}}; });
    }).then(function(r){
      if(r.ok && String(r.j.success) === 'true'){
        sset('hss-audit'); requested();
        f.hidden = true; done.hidden = false; done.querySelector('h3').focus();
        return;
      }
      fail(x);
    }).catch(function(){ fail(x); });
  });
  function fail(x){
    var lines = ['Name: ' + x.name, 'Email: ' + x.email, 'Phone: ' + x.phone];
    WHERE.forEach(function(k){ if(x[k]) lines.push(k + ': ' + x[k]); });
    var href = 'mailto:__FORM_TO__?subject=' + encodeURIComponent(x._subject)
      + '&body=' + encodeURIComponent(lines.join('\\n'));
    st.innerHTML = 'That did not send. Try again, or <a href="' + href
      + '">email us at __FORM_TO__</a>. Everything you typed is still here.';
    btn.disabled = false; lab.textContent = LABEL;
  }
})();
</script>"""
CAL_JS = (CAL_JS.replace("__FORM_ENDPOINT__", f"https://formsubmit.co/ajax/{FORM_TO}")
                .replace("__FORM_TO__", FORM_TO))
assert "__FORM" not in CAL_JS, "calendar pop-up placeholders were not substituted"
# /contact/ and /book/ get the panel (their footer link opens it) but no bubble
CAL_POPUP = CAL_CSS + CAL_BUBBLE + CAL_HTML + CAL_JS if MODE == "web" else ""
CAL_POPUP_PANEL = CAL_CSS + CAL_HTML + CAL_JS if MODE == "web" else ""


SPOT_DIR = f"{S}/spots"


def vtt_end(path):
    """End time in seconds of the last cue in a WebVTT file (stdlib only)."""
    t = pathlib.Path(path).read_text(encoding="utf-8")
    assert t.startswith("WEBVTT"), f"{path}: not a WebVTT file"
    ends = re.findall(r"--> (\d+):(\d\d):(\d\d)\.(\d{3})", t)
    assert ends, f"{path}: no cues"
    hh, mm, ss, ms = (int(x) for x in ends[-1])
    return hh * 3600 + mm * 60 + ss + ms / 1000


def vspot_media(fn, du, poster_path, title, captions=None):
    """The hover-play picture shared by the spot cards, the homepage brand and podcast
    films and the testimonial: <video preload="none" playsinline> from spots/ under a
    lazy poster <img>, the whole picture one <button>. Behaviour lives in SOLO_JS. The
    duration label is checked against the file, and mp4_info() refuses a file that is
    not faststart. captions: a WebVTT file in spots/; the build checks it exists, is
    WebVTT and ends within the film. The <track> is deliberately not `default`:
    Chrome fetches a default track at page load even under preload="none" (measured,
    release 8), so it starts disabled and SOLO_JS shows it when the film first
    plays, which is when the browser fetches it; captions then show while it plays
    muted."""
    path = os.path.join(SPOT_DIR, fn)
    w, h, secs = mp4_info(path)
    assert f"{int(secs) // 60}:{int(secs) % 60:02d}" == du, \
        f"{fn} runs {secs:.1f}s but its label says {du}"
    src = asset(path, "video/mp4")
    poster = asset(poster_path, "image/webp" if poster_path.endswith(".webp") else "image/jpeg")
    t = html_lib.escape(title, quote=True)
    track, cc = "", ""
    if captions:
        vtt = os.path.join(SPOT_DIR, captions)
        assert os.path.exists(vtt), f"{fn} declares captions but {captions} is missing"
        assert vtt_end(vtt) <= secs + 0.5, f"{captions} runs past the end of {fn}"
        track = (f'<track kind="captions" srclang="en" label="English" '
                 f'src="{asset(vtt, "text/vtt")}">')
        cc = " has-cc"
    return (f'<div class="vspot{cc}" data-state="idle">'
            f'<video src="{src}" preload="none" playsinline width="{w}" height="{h}" '
            f'aria-hidden="true">{track}</video>'
            f'<img src="{poster}"{dims(poster_path)} alt="" loading="lazy" decoding="async">'
            f'<button type="button" class="vplay" aria-label="Play {t}" data-title="{t}">'
            f'<span class="vglyph">{PLAY_ICON}</span>'
            f'<span class="vsnd"><span class="vsnd-off">{MUTED_ICON}Click for sound</span>'
            f'<span class="vsnd-on">{SOUND_ICON}Sound on</span></span>'
            f'</button></div>')


def spot(fn, sc, nm, du, yt=None):
    """One commercial spot card. Two renderings:

    fn set, web build: the self-hosted film from spots/ (release 4, owner request).
    Hover plays the WHOLE spot muted from 0:00 and leaving resets it to the poster;
    a click turns sound on; touch taps play/pause with sound; keyboard Enter/Space
    plays/pauses with sound; reduced motion gets click/tap only. Nothing downloads
    until then: preload="none", and the poster is a lazy <img> layered over the
    <video> (not its poster attribute, which is fetched eagerly and cannot be shown
    again after playback without load()). All behaviour lives in SOLO_JS, with the
    one-at-a-time rule.

    Otherwise (the inline artifact build, which has a 16MB cap and cannot carry
    the films): the YouTube click-to-play card, poster and button only until
    clicked (YT_SPOT_JS swaps the iframe in). yt is kept on every entry either way
    as the reference copy and the poster key (post_yt/<id>.webp)."""
    assert yt, f"spot {nm!r} needs its YouTube id: it keys the poster in post_yt/"
    poster_path = os.path.join(S, "post_yt", yt + ".webp")
    poster = asset(poster_path, "image/webp")
    t = html_lib.escape(nm, quote=True)
    meta = (f'<div class="meta"><span class="sc">{sc}</span><span class="nm">{t}</span>'
            f'<span class="du">{du}</span></div></article>')
    if fn and MODE == "web":
        return '<article class="spot">' + vspot_media(fn, du, poster_path, nm) + meta
    return (f'<article class="spot">'
            f'<div class="ytspot" data-yt="{yt}" data-title="{t}">'
            f'<img src="{poster}"{dims(poster_path)} alt="" loading="lazy">'
            f'<button type="button" class="ytplay" aria-label="Play {t}">{PLAY_ICON}</button>'
            f'</div>' + meta)

# (fn, number, title, duration, YouTube id). Release 4: every All Heart and Handyman
# Dan spot is self-hosted from spots/ for hover play (fn), encoded from the owner's
# own YouTube uploads; the YouTube id stays as the reference copy and the poster key.
# The duration label is checked against the file at build time. Handyman Dan files
# keep the original six-spot numbering, so there is no hd04 (Father Vs AC, R17).
allheart = [("ah01.mp4","01","Breaking Furniture 101","0:30","zaCFfVetfFI"),
    ("ah02.mp4","02","The Upsell","0:15","METoxqCqkn8"),
    ("ah03.mp4","03","The Snake","0:30","TPDZ-OvRNgc"),("ah04.mp4","04","Obsessed","0:30","Nz5hbi-0x94"),
    ("ah05.mp4","05","Meet The Carlas","0:30","A6gc-YCl94E"),("ah06.mp4","06","The Influencer","0:30","YLK9ftd4Dx4"),
    ("ah07.mp4","07","The Auctioneer","0:30","aEtwPZAdKPo"),("ah08.mp4","08","Ghosted","0:30","npKJfYqjljs"),
    ("ah09.mp4","09","Universe is Talking","0:30","COEbLTt42FI"),("ah10.mp4","10","The Quote","0:42","unFCPL3Cw5o")]

handyman = [("hd01.mp4","01","It's Way Hotter","0:30","E5qZHk03snY"),
    ("hd02.mp4","02","Don't Worry, You'll Get Used To It","0:30","4fUdKqK9cPM"),
    ("hd03.mp4","03","Sleeping On The Job","0:30","S3Hkreuykvs"),
    ("hd05.mp4","05","A Space Odyssey","0:56","AfkePSa8XLU"),("hd06.mp4","06","Where's That Coming From","0:30","Fodjt_xKovE")]
assert len({x[0] for x in allheart + handyman}) == len(allheart + handyman), "two spots share a file"

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

# The wall, in display order. R15 (2026-10-06) added fourteen marks from the HSS
# Dropbox client folders and release 8 (2026-10-06) eight more, all owner approved,
# each logo taken from the company's own website; originals and sources live outside
# the repo in reports/hss-audit/logos-new/ (manifest.json, originals/). HCCI stays out.
# HVAC, plumbing and electrical brands lead; roofing, generators, GatorWraps and garage
# doors follow; the agencies, the business advisor and the sales trainer (Rocket Group,
# Lokal Media House, Rivenway, Service MVP) come last. Busy mascot marks (All Heart, Bee
# Right There, iComfort, Veterans AC PHX, Grasshopper, Good Guy, Atticman, Warm Welcome,
# Doggone, Bellaire, Gengatorz, The Generator Guys, GatorWraps) never sit next to each
# other: in the marquee (including where it loops back to the first mark), in the
# phones' three-column grid (beside or directly above) and in the five-column
# reduced-motion grid (directly above), and they spread across all three phone
# columns. LOGO_MASCOTS and the asserts below the list hold the order to that. Alt
# text uses "and", not &, and no person's name.
# Release 25 (owner, 2026-10-07): Monarch Home Services is off the wall, Veterans AC
# PHX has its Instagram badge (a mascot mark), and Rivenway and Atticman are added.
# Closing Monarch's slot put Grasshopper three after iComfort, which the rules forbid,
# so a few HVAC marks swapped places; the order is the smallest change that keeps every
# rule at each step of the release.
CLIENT_LOGOS = [
    ("logo_allheart.png",      "All Heart Heating, Cooling and Plumbing"),
    ("logo_quality.png",       "Quality Heating Cooling Plumbing and Electric"),
    ("logo_beerightthere.png", "Bee Right There Heating and Air"),
    ("logo_a1.png",            "A1 Air Conditioning and Heating"),
    ("logo_icomfort.png",      "iComfort Heating and Air"),
    ("logo_vector.png",        "Vector Heating, Cooling, Plumbing and Electrical"),
    ("logo_veterans.png",      "Veterans AC PHX"),
    ("logo_harmony.png",       "Harmony Electrical, Plumbing and Air"),
    ("logo_grasshopper.png",   "Grasshopper Heating, Cooling and Plumbing"),
    ("logo_fiscor.png",        "Fiscor Plumbing and Air"),
    ("logo_goodguy.png",       "Good Guy Plumbing"),
    ("logo_premier.png",       "Premier Heating and Air"),
    ("logo_familyplumber.png", "The Family Plumber"),
    ("logo_acplus.png",        "AC Plus Heating and Cooling"),
    ("logo_atticman.png",      "Atticman Heating and Air Conditioning, Insulation"),
    ("logo_martins.png",       "Martins A/C and Electric"),
    ("logo_airone.png",        "Air One"),
    ("logo_blanchards.png",    "Blanchards Refrigeration"),
    ("logo_warmwelcome.png",   "Warm Welcome Heating, Cooling and Plumbing"),
    ("logo_firstmate.png",     "First Mate Heating and Cooling"),
    ("logo_doggone.png",       "Doggone Good Heating and Cooling"),
    ("logo_clogbusters.png",   "Clog Busters Drain Cleaning and Repair"),
    ("logo_bellaire.png",      "Bellaire Air Conditioning and Heating"),
    ("logo_4points.png",       "4 Points A/C and Heating"),
    ("logo_allamerican.png",   "All American Heating and Plumbing"),
    ("logo_bluepeaks.png",     "Blue Peaks Roofing"),
    ("logo_gengatorz.png",     "Gengatorz Power Systems"),
    ("logo_genstar.png",       "Genstar Generator Service"),
    ("logo_generatorguys.png", "The Generator Guys"),
    ("logo_selectpower.png",   "Select Power"),
    ("logo_gatorwraps.png",    "GatorWraps"),
    ("logo_stellar.png",       "Stellar Garage Doors"),
    ("logo_rocketgroup.png",   "Rocket Group"),
    ("logo_lmh.png",           "Lokal Media House"),
    ("logo_rivenway.png",      "Rivenway"),
    ("logo_servicemvp.png",    "Service MVP"),
]
LOGO_MASCOTS = {"logo_allheart.png", "logo_beerightthere.png", "logo_icomfort.png",
                "logo_grasshopper.png", "logo_goodguy.png", "logo_warmwelcome.png",
                "logo_doggone.png", "logo_bellaire.png", "logo_gengatorz.png",
                "logo_generatorguys.png", "logo_gatorwraps.png",
                "logo_veterans.png", "logo_atticman.png"}   # both added in release 25
_m = [i for i, (fn, _) in enumerate(CLIENT_LOGOS) if fn in LOGO_MASCOTS]
assert len(_m) == len(LOGO_MASCOTS), "a mascot mark is missing from the wall"
assert not any(b - a in (1, 3, 5) for a in _m for b in _m if b > a), \
    "two mascot marks sit side by side or stacked on the wall"
assert not (0 in _m and len(CLIENT_LOGOS) - 1 in _m), "mascots meet where the marquee loops"
assert {i % 3 for i in _m} == {0, 1, 2}, "mascots stack in one phone column"
assert len({fn for fn, _ in CLIENT_LOGOS}) == len(CLIENT_LOGOS), "a logo is listed twice"
assert not any(re.search(r"hcci", fn) for fn, _ in CLIENT_LOGOS), "HCCI stays off the wall"


_INK_ALPHA = bytes(1 if v >= 8 else 0 for v in range(256))   # "ink": alpha 8 and up


def logo_ink(fn):
    """(left, width) of a mark's ink, in pixels of its 500x200 canvas: the first to the
    last column holding any pixel with alpha 8 or more, read from the PNG master in
    logos/ (logos_webp/ holds lossless copies with identical pixels). Every master is
    8-bit RGBA, non-interlaced. PNG filters work per byte with a 4-byte pixel step, so
    each channel reconstructs on its own; only the alpha bytes are decoded, which keeps
    this fast enough to run on every build. Used by the marquee (release 26)."""
    b = pathlib.Path(S, "logos", fn).read_bytes()
    assert b[:8] == b"\x89PNG\r\n\x1a\n", fn
    i, idat = 8, []
    while i < len(b):
        n = int.from_bytes(b[i:i + 4], "big")
        kind = b[i + 4:i + 8]
        if kind == b"IHDR":
            w, h = int.from_bytes(b[i + 8:i + 12], "big"), int.from_bytes(b[i + 12:i + 16], "big")
            assert (w, h) == (500, 200) and b[i + 16:i + 19] == b"\x08\x06\x00" and b[i + 20] == 0, \
                f"{fn}: logo masters must be 500x200 8-bit RGBA, non-interlaced"
        elif kind == b"IDAT":
            idat.append(b[i + 8:i + 8 + n])
        i += 12 + n
    raw = zlib.decompress(b"".join(idat))
    row = 1 + 500 * 4
    prev = bytearray(500)
    x0, x1 = 500, -1
    for y in range(200):
        f = raw[y * row]
        a = bytearray(raw[y * row + 4:(y + 1) * row:4])   # this row's filtered alpha bytes
        if f == 1:
            for k in range(1, 500):
                a[k] = (a[k] + a[k - 1]) & 255
        elif f == 2:
            for k in range(500):
                a[k] = (a[k] + prev[k]) & 255
        elif f == 3:
            a[0] = (a[0] + (prev[0] >> 1)) & 255
            for k in range(1, 500):
                a[k] = (a[k] + ((a[k - 1] + prev[k]) >> 1)) & 255
        elif f == 4:
            a[0] = (a[0] + prev[0]) & 255
            for k in range(1, 500):
                l, u, ul = a[k - 1], prev[k], prev[k - 1]
                q = l + u - ul
                pl, pu, pul = abs(q - l), abs(q - u), abs(q - ul)
                a[k] = (a[k] + (l if pl <= pu and pl <= pul else u if pu <= pul else ul)) & 255
        hit = bytes(a).translate(_INK_ALPHA)
        first = hit.find(1)
        if first >= 0:
            x0, x1 = min(x0, first), max(x1, hit.rfind(1))
        prev = a
    assert x1 >= x0, f"{fn}: no ink"
    return x0, x1 - x0 + 1


LOGO_INK = {fn: logo_ink(fn) for fn, _ in CLIENT_LOGOS}


def _frac(v):
    """v/500 written short: exact to three decimals, no leading zero (0.338 -> .338)."""
    return f"{v / 500:g}".lstrip("0") or "0"


def logomark(fn, name):
    """WebP at the canvas size every mark is rendered onto, with width and height
    declared so the grid reserves its space before the image arrives. --x and --w
    (the ink's left edge and width as fractions of the 500px canvas) let the marquee
    size the item to the ink alone; the grids ignore them.

    Release 26 (owner), the marquee from 760px with motion allowed. The space between
    neighbouring logos is equal everywhere. Each item is as wide as its mark's ink at the
    scale a 500px canvas has at 190px, so no mark changes size or weight. The img stays
    the full canvas at 190px, shifted left to the ink and clipped to it (clip-path:
    inset). So the shipped files do not change, hover hit-testing stops at the ink and
    the hover scale is centred on it. --mq-gap is then the visible ink-to-ink gap."""
    src = asset(os.path.join(S, "logos_webp", fn.replace(".png", ".webp")), "image/webp")
    ix, iw = LOGO_INK[fn]
    return (f'<div class="logomark" style="--x:{_frac(ix)};--w:{_frac(iw)}">'
            f'<img src="{src}" alt="{name}" width="500" height="200" '
            f'loading="lazy" decoding="async"></div>')


# The roster stat on the homepage counts the wall rather than restating a number
# by hand, so adding or removing a logo can never leave the two disagreeing.
ROSTER_COUNT = len(CLIENT_LOGOS)


# A1's reels live on Facebook, which serves no public thumbnail, so its case page
# carries a chart of the real view counts (a1_bars) instead of invented artwork.


def a1_bars():
    """The seven real A1 view counts as HTML bars (see .a1bars). It used to be an inline
    SVG (a1_chart); its <text> made Archivo 700 miss font-display:optional's window, so
    every heading on the page fell back to Arial Black. Keep charts as HTML text."""
    data = [("623K", 623, 1), ("428K", 428, 0), ("410K", 410, 0), ("312K", 312, 0),
            ("195K", 195, 0), ("162K", 162, 0), ("134K", 134, 0)]
    bars = "".join(
        f'<div class="a1b{" is-top" if top else ""}" style="--h:{v / 623:.2f}">'
        f'<span class="v">{lab}</span><span class="bar"></span></div>'
        for lab, v, top in data)
    idx = "".join(f"<span>{i:02d}</span>" for i in range(1, len(data) + 1))
    return (f'<div class="a1bars" role="img" aria-label="Seven A1 reels by view count, from '
            f'623,000 down to 134,000, every one of them above 100,000">'
            f'<div class="a1plot" aria-hidden="true">'
            f'<span class="a1t" style="--h:{100 / 623:.2f}"><span>100K</span></span>{bars}</div>'
            f'<div class="a1idx" aria-hidden="true">{idx}</div></div>')


# ---- case studies ------------------------------------------------------------

# Order here is the case numbering (Case 01 to 04), the prev/next chain on the case
# pages, the sitemap and the homepage case note. Bee Right There and iComfort were
# added 2026-10-06 (R4) from the owners' figures; Handyman Dan stopped being a case
# the same day and lives in More work. tile_line is the one factual sentence on the
# case's /our-work card. desc may carry &amp; (it lands in a meta attribute).
# Bee Right There's top reel (12 Feb 2025). Its views were 982,880 when the case was
# written; the owner reported 1.2 million on 6 Oct 2026, read from Instagram. Every
# place the site shows it reads these, and the number links to the reel itself.
BRT_REEL_URL = "https://www.instagram.com/reel/DF_u1LpPd-x/"
BRT_REEL_M = 1.2
BRT_REEL_SHORT, BRT_REEL_LONG = f"{BRT_REEL_M}M", f"{BRT_REEL_M} million"
# "more than a million"; it can only have grown, and it is still the biggest of the
# three reels that passed 300,000
assert BRT_REEL_M > 1 and BRT_REEL_M * 1e6 > 982880 > 316814 > 316402 > 300000
BRT_REEL_LABEL = f"{BRT_REEL_SHORT} views on Bee Right There&#39;s top reel, on Instagram"


CASES = [
    dict(id="a1", slug="a1-air-conditioning", name="A1 Air Conditioning", og="og-a1.jpg",
         vertical="Home services", tag="Social Media Packages",
         problem="A crowded market where every company looks the same.",
         card_metric="2.26M", card_line="views on seven reels in their first six months",
         where="A1 Air Conditioning &middot; Tucson, AZ",
         desc="A Tucson HVAC company with 9,200 followers. In their first six months with Home "
              "Service Studios, seven reels reached 2.26M views."),
    dict(id="beerightthere", slug="bee-right-there", name="Bee Right There",
         full="Bee Right There Heating &amp; Air", og="og-bee-right-there.jpg",
         vertical="Home services", tag="Social Media Packages",
         problem="Posting every day and reaching almost no one.",
         card_metric="3.8x", card_line="the views in three weeks, on 24% more posts",
         where="Bee Right There Heating &amp; Air &middot; Atascadero, CA",
         desc="Bee Right There Heating &amp; Air, an HVAC company in Atascadero, CA: posts seen "
              "3.8 times as often within three weeks, on 24% more posts, and a reel past "
              f"{BRT_REEL_LONG} views."),
    dict(id="icomfort", slug="icomfort", name="iComfort",
         full="iComfort Heating and Air", og="og-icomfort.jpg",
         vertical="Home services", tag="Social Media Packages",
         problem="Twenty years in business and a feed that looked quiet.",
         card_metric="6.8x", card_line="the followers in under a year, all organic",
         card_now="3,127 followers today",
         where="iComfort Heating and Air &middot; San Fernando, CA",
         desc="iComfort Heating and Air, a family-owned HVAC company in San "
              "Fernando, CA: Instagram from 290 to 1,970 followers in under a year, all organic."),
    dict(id="allheart", slug="all-heart", name="All Heart", og="og-allheart.jpg",
         full="All Heart Heating, Cooling &amp; Plumbing",
         vertical="Home services", tag="Campaign",
         problem="A market full of forgettable HVAC ads.",
         card_metric="10 spots", card_line="produced in less than a week",
         where="All Heart Heating, Cooling &amp; Plumbing",
         desc="Ten commercial spots written and produced in a single production block on one "
              "premise: the contractor you want versus the contractor you got."),
]
CASE_BY_ID = {c["id"]: c for c in CASES}
# the stated multiples and rises must match the raw figures they come from
assert round(106439 / 27851, 1) == 3.8 and round(57 / 46 - 1, 2) == 0.24
assert round(6634 / 843, 1) == 7.9 and round(78 / 21, 1) == 3.7
assert round(27851 / 46, -2) == 600 and round(106439 / 57, -1) == 1870
assert round(1970 / 290, 1) == 6.8 and 1970 - 290 == 1680 and 508 - 154 == 354
# iComfort today (R19, public profile, 6 Oct 2026): 3,127 followers, 1,085 posts.
# "more than ten times where it started" is 3,127 / 290 = 10.8x.
assert 3127 / 290 > 10 and round(3127 / 290, 1) == 10.8


def case_url(cid):
    """Each case has its own page at /our-work/<slug>/ (N1, 2026-10-06)."""
    return f"/our-work/{CASE_BY_ID[cid]['slug']}/"


# /our-work case cards (R8, 2026-10-06): problem first, then what changed, then who.
# The grid reads in problem order, which differs from the case numbering on purpose:
# a visitor scans for the problem that sounds like theirs. Each card is an article
# whose "Read the case" link is stretched over the whole card, so the card is one
# click target while the link keeps a short, specific accessible name.
CARD_ORDER = ["beerightthere", "icomfort", "a1", "allheart"]
assert sorted(CARD_ORDER) == sorted(CASE_BY_ID), "CARD_ORDER must list every case once"


def case_card(c):
    return (f'<article class="pcard on-ink"><p class="pc-tag">{c["tag"]}</p>'
            f'<h3>{c["problem"]}</h3>'
            f'<p class="pc-metric"><b>{c["card_metric"]}</b><span>{c["card_line"]}</span>'
            + (f'<span class="pc-now">{c["card_now"]}</span>' if c.get("card_now") else "")
            + '</p>'
            f'<p class="pc-who">{c["where"]}</p>'
            f'<a class="pc-go" href="{case_url(c["id"])}">Read the case'
            f'<span class="vh"> on {c["name"]}</span>&nbsp;&rarr;</a></article>')


CASE_GRID = "\n".join(case_card(CASE_BY_ID[k]) for k in CARD_ORDER)






CSI = {
    "a1": ("Local service advertising is interchangeable. Same vans, same promises, nothing "
           "anyone would repeat.",
           "Treat the service call as a premise. The best-performing spot frames a technician "
           "alone in a dark attic like the cold open of a horror film.",
           "1,100 shares on the lead reel. Audiences passed it along themselves, which is the "
           "premise working rather than the media budget."),
    # R22 (owner copy, 2026-10-06): short sentences, one idea each.
    "beerightthere": (
        "In the three weeks before we started, they published 46 posts. Together, those posts "
        "were seen 27,851 times. That is about 600 views a post. The effort was there. The posts "
        "just gave nobody a reason to stop scrolling.",
        "Not the schedule. The ideas. We made their posts entertaining. Each reel starts from a "
        "moment homeowners and techs recognize, like skipping the manual or climbing a sketchy "
        "ladder. People watch to the end. Then they send it to a friend.",
        "In the next three weeks, 57 posts were seen 106,439 times. That is about 1,870 views a "
        "post. Likes, comments, shares and saves went from 843 to 6,634. New followers went from "
        "21 to 78. In January and February 2025, three reels passed 300,000 views each. The "
        f"biggest has passed {BRT_REEL_LONG}."),
    "icomfort": (
        "154 posts and 290 followers. A homeowner checking iComfort out before a call found a "
        "company that looked inactive, the opposite of twenty years in the Valley.",
        "Daily posting, led by their own people: technicians explaining real equipment in plain "
        "terms, the moments every tech knows, and creating trends that entertain their "
        "customers.",
        "In under a year the account grew from 290 followers to 1,970, all organic: nearly seven "
        "times the audience. It went from 154 posts to 508. Every post was produced to a high "
        "standard and went out on schedule, day after day. That consistency is what turned a "
        "quiet feed into an audience."),
    # Release 17 (owner copy): the market problem, never "he" or "the owner".
    "allheart": ("Most local HVAC ads look and sound the same. Nobody remembers them. The goal was to "
                 "disrupt the market with something different. That meant spots people would "
                 "remember when it was time to call a contractor.",
                 "We built the campaign on one comic premise: the contractor you want versus the "
                 "contractor you got. Then we produced all ten spots in less than a week. The "
                 "process is repeatable. Your next campaign can be made the same way.",
                 "Ten finished spots from a single production, delivered complete and in scope."),
}


def csi_block(cid):
    """The problem block opens with the same line as the case's /our-work card (R8),
    so the card and the page agree."""
    a, b, c = CSI[cid]
    lead = CASE_BY_ID[cid]["problem"]
    return (f'<div class="csi"><div><h3>The problem</h3><p class="csi-lead">{lead}</p><p>{a}</p></div>'
            f'<div><h3>What we changed</h3><p>{b}</p></div>'
            f'<div><h3>What happened</h3><p>{c}</p></div></div>')


def ops(rows):
    """A ruled row of figures: (number, label) or (number, label, href, aria-label),
    the second linking the number (Bee Right There's top reel). A range ("290 to
    1,970") is marked data-static so the count-up leaves it alone instead of counting
    only its first number."""
    def cell(n, k, href=None, aria=None):
        static = " data-static" if " to " in n else ""
        num = (f'<a class="n" href="{href}" aria-label="{aria}"{static}>{n}</a>' if href else
               f'<span class="n"{static}>{n}</span>')
        return f'<div class="op">{num}<span class="k">{k}</span></div>'
    return '<div class="ops">' + "".join(cell(*r) for r in rows) + '</div>'


def before_after(title, periods, rows):
    """A flat before/after comparison as HTML bars and real text (an inline SVG with
    <text> made Archivo miss font-display:optional's window, see a1_bars). rows:
    (label, one value per period, change). Bars scale within each row, so a small
    rise and a large one read differently at a glance. The change label covers the
    first two periods, the documented before and after, and is checked against
    them so the copy cannot drift from the data; a later period (iComfort's count
    today, R19) is one more bar, with no change claimed for it."""
    out = []
    for label, *vals, chg in rows:
        assert len(vals) == len(periods) >= 2, (label, vals, periods)
        x, y = vals[0], vals[1]
        if chg.endswith("%"):
            assert chg == f"+{round((y - x) / x * 100)}%", (label, chg)
        elif chg.endswith("x"):
            assert chg == f"{round(y / x, 1)}x", (label, chg)
        elif chg.startswith("+"):
            assert chg == f"+{y - x:,}", (label, chg)
        m = max(vals)
        line = lambda when, v, cls: (
            f'<p class="ba-line{cls}"><span class="ba-when">{when}</span><span class="ba-track">'
            f'<span class="ba-bar" style="--w:{v / m:.2f}"></span>'
            f'<span class="ba-v">{v:,}</span></span></p>')
        out.append(f'<div class="ba-row"><p class="ba-k"><span>{label}</span>'
                   f'<span class="ba-chg">{chg}</span></p>'
                   + "".join(line(when, v, " is-after" if i else "")
                             for i, (when, v) in enumerate(zip(periods, vals))) + '</div>')
    return (f'<div class="chartwrap"><p class="charttitle">{title}</p>'
            f'<div class="ba">{"".join(out)}</div></div>')


# What each case page carries: the hero's eyebrow, roles, the highlighted phrase
# in its headline and its lede, then the proof itself. Copy is the case write-ups
# that used to live in the /our-work panels, unchanged.
CASE_PAGE = {
    "a1": dict(
        kind="Reach",
        # H (release 8): HSS ran their organic short form only, never paid advertising or
        # brand video for A1. Never claim otherwise.
        # Release 9 (owner): every A1 figure is from their FIRST SIX MONTHS with us, and the
        # seven reels are only the biggest of everything posted in that span. There are no
        # per-post dates and no views for the other posts: never invent either.
        roles=["Social Media Packages", "Short form"], tag="2.26M views in six months.",
        lede="Ongoing Social Media Packages work on their organic short-form video. A Tucson HVAC "
             "company with 9,200 followers. In their first six months with us, <strong>seven "
             "reels passed 100,000 views and three passed 400,000</strong>. That is roughly 2.26 "
             "million views, in a market of one million people. And those are only the seven "
             "biggest. Every other video we posted in those six months added views on top.",
        proof_head="The reels",
        proof=f"""<div class="chartwrap">
    <p class="charttitle">The seven biggest reels from their first six months. Every one clears 100,000.</p>
    {a1_bars()}
    <p class="chartnote">The lead reel frames a technician alone in a dark attic like the cold
    open of a horror film. It was shared 1,100 times, which is the shape of the whole account:
    one breakout carried by a premise, and a tail that still outperforms the market.</p>
  </div>
  <div class="reels">
{A1_REELS}
  </div>""",
        ops=ops([("6 months", "From the first post"),
                 ("2.26M", "Views on the seven biggest reels"),
                 ("7", "Reels past 100,000 views"), ("3", "Reels past 400,000 views")])),
    "beerightthere": dict(
        kind="Reach", roles=["Social Media Packages", "Short form"],
        tag="Nearly 4x the views in three weeks.",
        lede="Bee Right There Heating &amp; Air was already posting almost every day from "
             "Atascadero, on California&#39;s Central Coast. Hardly anyone was watching. We "
             "changed what they posted, not how often. In the first three weeks, <strong>their "
             "posts were seen nearly four times as often</strong>. One reel has since passed "
             f"{BRT_REEL_LONG} views. Their hometown has about 30,000 people.",
        ops=ops([("3.8x", "Times their posts were seen"),
                 ("7.9x", "Likes, comments, shares and saves"),
                 ("3.7x", "New followers"),
                 (BRT_REEL_SHORT, "Views on one reel", BRT_REEL_URL, BRT_REEL_LABEL)]),
        testimonial=True,
        proof_head="Same schedule, different ideas",
        proof=before_after(
            "24% more posts. 3.8 times the views.",
            ("9 to 31 Aug 2024", "1 to 23 Sep 2024"),
            [("Posts", 46, 57, "+24%"), ("Times seen", 27851, 106439, "3.8x"),
             ("Likes, comments, shares and saves", 843, 6634, "7.9x"),
             ("New followers", 21, 78, "3.7x")])
            + '\n  <h3 class="subhead">Three reels past 300,000 views</h3>\n  '
            + ops([(BRT_REEL_SHORT, "Views, 12 Feb 2025", BRT_REEL_URL, BRT_REEL_LABEL),
                   ("316,814", "Views, 27 Jan 2025"),
                   ("316,402", "Views, 15 Jan 2025")]),
        close="A small-town HVAC company became one people pass around. Their town has about "
              "30,000 people. A reel with more than a million views is attention local "
              "advertising rarely reaches. Every one of those views carried the Bee Right There "
              "name.",
        source="Figures from the account&#39;s own analytics for 9 to 31 Aug 2024 and 1 to 23 Sep "
               "2024; reel views as reported in early 2025. Top reel&#39;s current views from "
               "Instagram, 6 Oct 2026. Atascadero population: 29,773 (2020 Census)."),
    "icomfort": dict(
        kind="Audience", roles=["Social Media Packages", "Short form"],
        tag="290 to 1,970 followers, no ads.",
        lede="iComfort Heating and Air has served the San Fernando Valley since 2004. "
             "In March 2024 their Instagram had 290 followers and looked quiet. A year of daily "
             "posts later <strong>it had 1,970 followers, all organic</strong>, and a library of "
             "354 new posts. "
             "Today, 3,127 people follow the account, more than ten times where it started.",
        ops=ops([("3,127", "Instagram followers today, up from 290"),
                 ("6.8x", "Followers in the first year, all organic"),
                 ("14.2M", "Impressions"), ("354", "New posts in the first year")]),
        proof_head="A year of daily posts",
        proof=before_after(
            "First year: 354 new posts, 6.8 times the followers.",
            ("27 Mar 2024", "11 Mar 2025", "6 Oct 2026"),
            [("Posts", 154, 508, 1085, "+354"),
             ("Instagram followers", 290, 1970, 3127, "6.8x")]),
        close="A twenty-year-old family business now looks like what it is, busy, expert and "
              "still here, to anyone who checks before they call. 3,127 people now follow their "
              "trucks and techs, and when a system fails, iComfort is the name they have been "
              "watching.",
        source="Figures from the account&#39;s own Instagram, 27&nbsp;Mar&nbsp;2024 to "
               "11&nbsp;Mar&nbsp;2025; current count from the public profile, 6&nbsp;Oct&nbsp;2026. "
               "Impressions figure from the account owner, 6&nbsp;Oct&nbsp;2026."),
    "allheart": dict(
        kind="Campaign",
        roles=["Writer", "Producer"], tag="Ten spots, one shoot.",
        lede="We wrote and produced a <strong>ten-spot campaign in a single production "
             "block</strong>. One premise carries the whole package: the contractor you want "
             "versus the contractor you got.",
        proof_head="The spots",
        proof=f'<div class="grid">\n{chr(10).join(spot(*x) for x in allheart)}\n  </div>',
        ops=ops([("10", "Spots"), ("1", "Production block"),
                 ("3", "Cut lengths: 15, 30 and 42 seconds")])),
}


# The Handyman Dan campaign on /our-work (R3, 2026-10-06; reworked in release 28, owner).
# Handyman Dan is not a case study: it is a white-label commercial campaign a home
# service company runs under its own name, in its own market. The section is the
# campaign itself (no "More work" wrapper): the work leads, then the one result as a
# quiet line, never a display stat. The result is the owner's: calls from Google for
# one company running the spots went from about one a week to ten a day. Never name who
# ran the spots or how many did, and no market counts, account counts or licensing
# terms. R17 dropped "Father Vs AC" (its picture carried one licensee's logo and phone
# number); the strip numbers what remains. Release 28 removed the 4 Points card that
# used to follow it (its logo stays on the client wall). The id stays "more-work":
# the old Handyman Dan pages and the #handyman hash forward to it.
# The enquiry link (release 28, owner) goes straight to the form with ?campaign=, which
# FORM_JS maps to a fixed prefilled message. It is a specific enquiry, not the site's
# conversion CTA, so it does not go through cta_href(): a calendar would lose the message.
CAMPAIGN_ASK = "/contact/?campaign=handyman-dan#start"
# Same pattern for block 03's brand films (release 32): FORM_JS maps brand-video to a fixed message.
BRAND_ASK = "/contact/?campaign=brand-video#start"
# Release 34 (owner): blocks 02 and 04 end the same way, and all four asks (these, BRAND_ASK
# and CAMPAIGN_ASK) are Reel wheel buttons after a one-line prompt. Each key is in FORM_JS's
# PREFILL map.
COMMERCIAL_ASK = "/contact/?campaign=commercial-shoot#start"
# Release 37: the footer's "Free social audit" link. With JS it opens the panel; this address
# is its no-JS fallback (FORM_JS prefills social-audit; content-calendar is the release-35 key,
# kept for old links).
SOCIAL_AUDIT_ASK = "/contact/?campaign=social-audit#start"
PODCAST_ASK = "/contact/?campaign=podcast#start"
MORE_WORK = f"""<section id="more-work"><div class="wrap">
  <div class="sec-head">
    <p class="eyebrow">Handyman Dan &middot; Commercial campaign</p>
    <h2 class="display">One campaign. Any market.</h2>
  </div>
  <p class="mw-body">We wrote and produced a commercial campaign built to travel. It is white
  label, so a home service company can run it under its own name, in its own market.</p>
  <div class="strip{" five" if len(handyman) == 5 else ""}">
{chr(10).join(spot(fn, f"{i:02d}", nm, du, yt) for i, (fn, _, nm, du, yt) in enumerate(handyman, 1))}
  </div>
  <p class="mw-result"><span class="mw-k">The result</span>One company running the spots saw
  calls from Google climb from about one a week to ten a day.</p>
  <p class="mw-ask">Want to run this campaign in your market?</p>
  <a class="cta" href="{CAMPAIGN_ASK}">{reel("Ask about the campaign")}</a>
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
    cta_is_here = bool(page) and cta_href().startswith(f"/{page}/")
    cta = "" if cta_is_here else book("Footer", "", "cta")
    return (f'<footer><div class="wrap">'
            f'<div class="foot">'
            f'<div class="foot-main">'
            f'<p class="display foot-line">Let&#39;s make something that travels.</p>'
            f'<div class="foot-actions">{cta}'
            f'<a class="foot-mail" href="mailto:{EMAIL}">{EMAIL}</a>'
            f'<a class="foot-mail foot-cal" href="{SOCIAL_AUDIT_ASK}" data-cal '
            f'aria-haspopup="dialog">Free social audit</a></div>'
            f'</div>'
            f'<nav class="foot-nav" aria-label="Footer">{links}</nav>'
            f'</div>'
            f'<div class="foot-meta">'
            f'<p>Los Angeles, CA &middot; Insured &middot; Working since 2020</p>'
            f'<p>&copy; {YEAR} Home Service Studios</p>'
            f'</div>'
            f'</div></footer>')


# Marquee geometry. The marquee only runs from 760px with motion allowed.
# MARQUEE_SCALE_PX: a full 500px canvas renders 190px wide, so every mark keeps the size
#   and weight it has had since release 8; the assert ties this to the CSS.
# MARQUEE_INK_GAP_PX (release 26, owner): the one visible gap between neighbouring inks.
#   It is the average visible ink-to-ink gap the marquee had before release 26 (110.414px
#   measured at 1440 across all 36 pairs), so the wall's density is unchanged. It reaches
#   the CSS as --mq-gap, inline on .marquee, so the two cannot drift.
# MARQUEE_PX_PER_S (release 25, owner): about 15% faster than the 51.3 px/s it had before.
MARQUEE_SCALE_PX = 190
MARQUEE_INK_GAP_PX = 110.4
MARQUEE_PX_PER_S = 59
assert ".marquee .logomark{width:calc(var(--w) * 190px);flex:none;}" in CSS
assert ".marquee .logomark img{width:190px;max-width:none;margin-left:calc(var(--x) * -190px);" in CSS


def logo_marquee():
    """The client wall as a continuous marquee. The track is duplicated because a
    translateX of -50% only loops seamlessly if the second half repeats the first.
    The second set is marked .dupe (and decorative, alt=""), so the static
    grid used on phones and under reduced motion can drop it."""
    marks = "".join(logomark(*c) for c in CLIENT_LOGOS)
    # The repeat set is decorative: alt="" keeps it out of the accessibility tree without
    # repeating 36 alt texts and aria-hidden in the page (release 26: these bytes paid for
    # the ink-box styles, so the homepage LCP did not get worse).
    dupe = re.sub(r'alt="[^"]*"', 'alt=""', marks.replace('class="logomark"', 'class="logomark dupe"'))
    # One lap is every mark's ink width at MARQUEE_SCALE_PX plus one gap each (the end
    # padding closes the loop), so the duration comes from the real lap length and a wall
    # of any size or mix scrolls at MARQUEE_PX_PER_S. The widths use the same exact
    # fractions logomark() writes, so this is the width the browser lays out.
    lap = sum(iw / 500 * MARQUEE_SCALE_PX + MARQUEE_INK_GAP_PX for _, iw in LOGO_INK.values())
    dur = lap / MARQUEE_PX_PER_S
    return (f'<div class="marquee" style="--mq-gap:{MARQUEE_INK_GAP_PX:g}px">'
            f'<div class="marquee-track" style="animation-duration:{dur:.1f}s">'
            f'{marks}{dupe}</div></div>')



# The case write-ups used to open inline on /our-work from #a1, #handyman and
# #allheart, and the homepage and outside links still use those. This forwards
# them to the case pages before anything paints.
# #handyman is the old in-page anchor of a case that is now the Handyman Dan section.
HASH_REDIRECT_JS = ("<script>(function(){var m={" + ",".join(
    [f'"{c["id"]}":"{case_url(c["id"])}"' for c in CASES] + ['"handyman":"#more-work"'])
    + "};var h=(location.hash||'').slice(1);if(m[h])location.replace(m[h]);})();</script>")

html = f"""<title>Selected work, Home Service Studios</title>
{HASH_REDIRECT_JS}
{FONT_CSS}
{CSS}
<a class="skip" href="#main">Skip to content</a>
{nav("work")}
<main id="main">
<div class="hero hero-dark">{SPLAT_SVG}<div class="wrap">
  <p class="eyebrow">Selected work &middot; Home Service Studios</p>
  <h1 class="display">Real accounts.<br><span class="hl">Real numbers.</span></h1>
  <p class="sub">{num_word(len(CASES)).capitalize()} home service companies, the problem each one
  started with, and what changed, <strong>measured on their own accounts</strong>.</p>
  <div class="stats quad">
    <a class="stat" href="{case_url("a1")}"><span class="case">A1 Air Conditioning</span><span class="n">2.26M</span><span class="k">Views in six months</span></a>
    <a class="stat" href="{case_url("beerightthere")}"><span class="case">Bee Right There</span><span class="n">3.8x</span><span class="k">Views in three weeks</span></a>
    <a class="stat" href="{case_url("icomfort")}"><span class="case">iComfort</span><span class="n">6.8x</span><span class="k">Followers in under a year</span></a>
    <a class="stat" href="{case_url("allheart")}"><span class="case">All Heart</span><span class="n">10</span><span class="k">Spots from one shoot</span></a>
  </div>
  <div class="ctarow">
    {book("Project%20enquiry")}
    <a class="cta ghost" href="/packages/">Social Media Packages</a>
  </div>
  {reassure("work")}
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
    <h2 class="display">Our Clients</h2>
  </div>
  {logo_marquee()}
</div></section>

<section><div class="wrap">
  <div class="sec-head">
    <p class="eyebrow">Case studies</p>
    <h2 class="display">Find the one that sounds like you.</h2>
    <p class="lede">Each started with a problem most home service companies have. Here is what
    changed.</p>
  </div>
  <div class="pgrid">
{CASE_GRID}
  </div>
</div></section>

{MORE_WORK}

</main>

{site_footer("work")}
{actionbar()}
{CAL_POPUP}
{SPLAT_JS}
{SOLO_JS}
{NAV_JS}
{MOTION_JS}
{YT_SPOT_JS if MODE != "web" else ""}
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
            + (f'<div class="shoot">{c["camera"]}</div>' if c.get("camera") else '')
            + '</div>')


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


# Terms (N2, 2026-10-06): one <details> per term, so on a phone the grid folds to
# eight 44px rows a buyer opens as needed. They render open, and TERMS_JS closes
# them only below 760px, right after the grid is parsed, so desktop and no-JS
# visitors see every term as before. Release 30: owner rewrote two terms in short sentences.
TERMS = [
    ("Starting and stopping", "There is no setup fee. To stop, give us 30 days notice and make "
     "one final payment. That makes the shortest package two months."),
    ("Ad budget", "From Starter up, each package includes the monthly ad budget shown on its card, "
     "which our team manages for you. It goes behind your own content. It is not a promise of "
     "leads."),
    ("Insurance", "We are insured. If your office needs paperwork on file before a crew is on your "
     "property or a job site, ask and we will send it over."),
    ("Who owns it", "You do. Every frame we shoot for you is yours to keep and use however you "
     "like, permanently."),
    ("Where it goes", "YouTube, Instagram, TikTok, Facebook and LinkedIn. Anywhere else you want to "
     "be, just say so."),
    ("Revisions", "One round on anything you want changed. Everything is cut to make you look good "
     "on camera in the first place."),
    ("Billing", "The first month holds your start date. Nothing else is due until the day your "
     "first post goes live, and that day sets your monthly cycle."),
]
TERMS_HTML = "\n".join(f'      <details class="term" open><summary>{t}</summary><p>{d}</p></details>'
                        for t, d in TERMS)
TERMS_JS = ("<script>if(window.matchMedia&&matchMedia('(max-width:759px)').matches)"
            "[].forEach.call(document.querySelectorAll('.term'),function(d){d.open=false;});</script>")

# The owners' onboarding timeline (D8, 2026-10-06), facts only. It replaces the
# Terms grid's "When it starts" cell, which said the first production day lands
# three to four weeks after payment; the owners' figure is three to four weeks
# from sign-up to the first post.
# R11 (owner, 2026-10-06): three to four weeks is the real answer, depending on the
# client roster at the time. The two step details that added up to five or six
# weeks (15 business days notice to book a shoot; 10 to 15 business days after the
# final production day) are gone; ONBOARDING_NOTE says timing is confirmed at kickoff.
ONBOARDING = "\n".join(
    f'      <li><span class="ob-n">{i:02d}</span><span class="ob-t">{t}</span></li>'
    for i, t in enumerate(["Strategy kickoff", "Agreement signed and first payment",
                           "Content collection and scheduling", "Production day",
                           "Post-production", "First post live"], 1))
ONBOARDING_NOTE = ("Timing depends on our production calendar when you sign up. We confirm "
                   "your dates on the kickoff call.")

PACKAGES_HTML = f"""<title>Social Media Packages</title>
{FONT_CSS}
{CSS}
<a class="skip" href="#main">Skip to content</a>
{nav("packages")}

<main id="main">
<div class="hero hero-dark">{SPLAT_SVG}<div class="wrap">
  <p class="eyebrow">Social Media Packages &middot; Home Service Studios</p>
  <h1 class="display">Known and trusted <span class="hl">before they need you.</span></h1>
  <p class="sub">Homeowners call the company they already recognize. That recognition is built
  over months, not in a month. When something goes wrong, you're top of mind. <strong>It only
  works if it actually runs.</strong> These packages keep it running without landing on your
  desk.</p>
  <div class="ctarow">
    {book("Social%20Media%20Packages")}
    <a class="cta ghost" href="/our-work/">See our work</a>
  </div>
  {reassure("packages")}
</div></div>

<section><div class="wrap">

  <div class="always on-ink">
    <h2>What you are investing in</h2>
    <p class="sub2">Not leads. Anyone selling you leads from organic short form is guessing.
    Consistent short form reliably does four things, and all four compound.</p>
    <div class="benefits">
      <div class="benefit"><span class="bn">01</span><h3>Recognition</h3>
        <p>When a breakdown, a move or a remodel puts someone in the market, they reach for the
        name they already know. Being that name takes months in the same feeds.</p></div>
      <div class="benefit"><span class="bn">02</span><h3>Recruiting</h3>
        <p>Good people are harder to find than customers, and they judge where to work from your
        feed long before they send a resume.</p></div>
      <div class="benefit"><span class="bn">03</span><h3>Trust at the door</h3>
        <p>Homeowners feel comfortable letting in a team they've already seen. They know your faces
        and how you work. That familiarity lowers their guard, so the visit starts on the right
        foot.</p></div>
      <div class="benefit"><span class="bn">04</span><h3>Proof you are still around</h3>
        <p>Everyone looks you up before they call. A feed with two years behind it says you are
        busy and still here. One that stopped in 2023 says the opposite.</p></div>
    </div>
  </div>

  <div class="always">
    <h2>The same three things happen at every tier</h2>
    <p class="sub2">The packages differ in how often our crew is on site, how much goes out and
    the ad budget we manage. Everything here is included whether you invest {money(PRICE_MIN)} or
    {money(PRICE_MAX)}.</p>
    <div class="steps">
      <div class="step2"><span>Step 01</span><h3>Planned</h3>
        <p>Our team decides what goes out and when, so nobody at your company has to
        remember.</p></div>
      <div class="step2"><span>Step 02</span><h3>Captured</h3>
        <p>Our crew films on site at your jobs, with your people, from Starter up. Baby Steps runs
        on footage your team sends in.</p></div>
      <div class="step2"><span>Step 03</span><h3>Posted for you</h3>
        <p>Reels every weekday, graphics every weekend and stories across your platforms,
        published for you rather than handed back as files.</p></div>
    </div>
  </div>

  <div class="band-row">
  {pkg_group("you-supply")}
  {pkg_group("two-days")}
  </div>

  {pkg_group("four-days")}

  <div class="band">
    <div class="band-head">
      <h2 class="display">From sign-up to first post in three to four weeks</h2>
    </div>
    <ol class="ob">
{ONBOARDING}
    </ol>
    <p class="ob-note">{ONBOARDING_NOTE}</p>
  </div>

  <div class="incl">
    <h3>Terms</h3>
    <div class="incl-grid terms">
{TERMS_HTML}
    </div>
    {TERMS_JS}
  </div>

  <div class="ctarow">
    {book("Social%20Media%20Packages")}
  </div>
  {reassure("packages-terms")}
  <p class="ctanote" style="margin-top:var(--s3);">Questions on terms?
  <a href="/contact/">Contact</a> us.</p>

</div></section>
</main>

{site_footer("packages")}
{actionbar()}
{CAL_POPUP}
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

# ---- Homepage hero (release 10, owner, 2026-10-06) --------------------------------
# Self-hosted, silent, 1:26.5, from the same film as the old YouTube hero (SiJpWlQwk04):
# spots/hero-540.mp4 (960x540) up to 760px wide, spots/hero-720.mp4 (1280x720) above.
# HERO_JS chooses one before setting src, so a visitor downloads one file, never both,
# and none at all under prefers-reduced-motion or Save-Data (poster only). The poster
# is the film's first frame (post/hero-poster.jpg master; 960 and 1280 WebP).
# First paint without costing LCP: on a throttled phone (1.6Mbps) a 27KB poster in
# the critical path delayed first paint by about 130ms. So phones paint an inline
# placeholder first: post/hero-poster-lqip.webp, the same frame at 960x540 and WebP
# quality 3 (6.5KB), as a data URI that paints with the headline. The sharp poster
# then loads at low priority and paints over it, and the film fades in over that.
# All three are 960x540 to Chrome, so neither later layer is a "larger" LCP
# candidate (a smaller placeholder let the film's first frame become LCP at ~3s).
# Desktop is not bandwidth bound: its 1280 poster is preloaded and is the LCP.
HERO_FILMS = ("hero-540.mp4", "hero-720.mp4")
HERO_POSTERS = (f"{P}/hero-poster-960.webp", f"{P}/hero-poster-1280.webp")
if MODE == "web":
    _hero_secs = []
    for _f in HERO_FILMS:
        _w, _h, _secs = mp4_info(os.path.join(SPOT_DIR, _f))   # refuses non-faststart
        _hero_secs.append(_secs)
    assert abs(_hero_secs[0] - _hero_secs[1]) < 0.1, "the two hero encodes are not the same film"
    _HERO_SRC = [asset(os.path.join(SPOT_DIR, f), "video/mp4") for f in HERO_FILMS]
else:
    _HERO_SRC = ["", ""]
_HP = [asset(x, "image/webp") for x in HERO_POSTERS]
HERO_LQIP = f"{P}/hero-poster-lqip.webp"
assert img_size(HERO_LQIP) == img_size(HERO_POSTERS[0]), "the placeholder must match the phone poster's size"
HERO_MEDIA = (f'<img class="hero-lqip" src="data:image/webp;base64,{b64(HERO_LQIP)}"{dims(HERO_LQIP)} alt="">'
              f'<picture class="hero-poster"><source media="(min-width: 761px)" srcset="{_HP[1]}"'
              f'{dims(HERO_POSTERS[1])}><img src="{_HP[0]}"{dims(HERO_POSTERS[0])} alt="" '
              f'fetchpriority="low" decoding="async"></picture>'
              + (f'<video class="hero-video" id="hero-video" autoplay muted loop playsinline '
                 f'preload="metadata" disablepictureinpicture aria-hidden="true" data-ambient '
                 f'data-sm="{_HERO_SRC[0]}" data-lg="{_HERO_SRC[1]}"></video>' if MODE == "web" else ""))
# Desktop's first paint is the 1280 poster, preloaded; phones paint the inline placeholder.
HERO_PRELOAD = f'<link rel="preload" as="image" href="{_HP[1]}" media="(min-width: 761px)" fetchpriority="high">'
HERO_JS = """<script>
/* The hero film: one file by width (<=760px the 540p encode, above it the 720p),
   chosen here before src is set, so nothing downloads that will not play. Under
   reduced motion or Save-Data there is no src at all: the poster is the hero.
   data-ambient keeps the one-at-a-time rule (SOLO_JS) from ever stopping it or
   being stopped by it. It pauses off screen and resumes on return. iOS Low Power
   Mode refuses autoplay silently, so the first touch anywhere retries it. */
(function(){
  var v = document.getElementById('hero-video');
  if(!v) return;
  var mm = function(q){ return !!(window.matchMedia && window.matchMedia(q).matches); };
  var conn = navigator.connection || {};
  if(mm('(prefers-reduced-motion: reduce)') || conn.saveData) return;
  v.muted = true;
  v.src = mm('(max-width: 760px)') ? v.getAttribute('data-sm') : v.getAttribute('data-lg');
  v.addEventListener('playing', function(){ v.classList.add('is-on'); });
  function go(){ var p = v.play(); if(p && p.catch) p.catch(function(){}); }
  go();
  document.addEventListener('touchstart', go, {passive: true, once: true});
  if('IntersectionObserver' in window){
    new IntersectionObserver(function(es){
      es.forEach(function(e){ if(e.isIntersecting) go(); else v.pause(); });
    }, {threshold: 0}).observe(v);
  }
})();
</script>"""


# ---- What We Do (homepage, release 8) ----------------------------------------
# Three Instagram profile grabs for block 01, left to right. Captured by the owner on a
# 390px phone at 3x with the login wall and "Suggested for you" removed, resized to
# 780px WebP (post/ig-*.webp). Follower counts are the public profile counts on
# 6 Oct 2026: refresh them (and the grabs) together, see CLAUDE.md.
IG_GRABS = [
    ("ig-icomfort.webp", "iComfort Heating and Air", "icomfort.hvac", "3,127"),
    ("ig-veteransacphx.webp", "Veterans AC PHX", "veteransacphx", "1,027"),
    ("ig-acplus.webp", "AC Plus Heating and Cooling", "acplus_hvac", "1,792"),
]
IG_COUNTS_DATE = "6 Oct 2026"


def ig_grab(fn, name, handle, followers):
    """One profile grab: a fixed 390:766 frame (iComfort's crop) so all three line up
    whatever each capture's height, linked to the live profile."""
    path = os.path.join(P, fn)
    src = asset(path, "image/webp")
    return (f'<figure class="ig"><a class="ig-frame" href="https://www.instagram.com/{handle}/">'
            f'<img src="{src}"{dims(path)} alt="{name} Instagram profile, @{handle}" '
            f'loading="lazy" decoding="async"></a>'
            f'<figcaption><span class="ig-name">{name}</span>'
            f'<span class="ig-meta">@{handle} &middot; {followers} followers</span></figcaption>'
            f'</figure>')


def brand_film():
    """Block 03: the Quality brand film from 1:14 to the end (spots/quality-brand.mp4),
    hover-play like the spots. Its poster is post/quality1.jpg, cut from the 1:14
    frame, so the still matches the first frame. The inline artifact build cannot
    carry the film, so it gets the still alone."""
    if MODE != "web":
        return (f'<div class="vspot"><img src="{asset(f"{P}/quality1.jpg", "image/jpeg")}"'
                f'{dims(f"{P}/quality1.jpg")} alt="" loading="lazy"></div>')
    return vspot_media("quality-brand.mp4", "1:44", f"{P}/quality1.jpg",
                       "the Quality Heating Cooling Plumbing Electrical brand film")


# Block 03's second row (release 32, owner): two more of the owner's own films beside the
# featured Quality film, as equal smaller players with the same hover-play behaviour.
# (file in spots/, poster, "m:ss" label checked against the file, caption, play label).
# Encoded like the spots from the owner's .mov masters (not committed): 1280x720 H.264
# High@3.1, CRF 23 capped at 1.6 Mbps, AAC 96k, +faststart. Posters are 1024x576 WebP
# from the masters (a 2-up card is about 524px wide, so 700px would be soft on retina):
# Gator Wraps at 61.0s (the wrapped truck at their shop), The Family Plumber at 10.25s
# (eyes open, logo wall). A caption names a city only when the company's own website
# states it in visible copy: The Family Plumber's does (Los Alamitos). Gator Wraps' lists
# two shops only in structured data, so its caption has none.
BRAND_FILMS_MORE = [
    ("gatorwraps-brand.mp4", f"{P}/gatorwraps-brand.webp", "1:24",
     "Website film for Gator Wraps.", "the Gator Wraps website film"),
    ("familyplumber-30.mp4", f"{P}/familyplumber-30.webp", "0:30",
     "30-second spot for The Family Plumber, Los Alamitos.",
     "the 30-second spot for The Family Plumber"),
]


def brand_films_more():
    """Block 03's pair of films under the Quality film, each with its caption."""
    cells = []
    for fn, poster_path, du, cap, label in BRAND_FILMS_MORE:
        media = (vspot_media(fn, du, poster_path, label) if MODE == "web" else
                 f'<div class="vspot"><img src="{asset(poster_path, "image/webp")}"'
                 f'{dims(poster_path)} alt="" loading="lazy"></div>')
        cells.append(f'<div class="wwd-film">{media}<p class="wwd-cap"><span>{cap}</span>'
                     f'<span class="du">{du}</span></p></div>')
    return f'<div class="wwd-pair">{"".join(cells)}</div>'


# Block 04, podcast production. PODCAST_VIDEO is (file in spots/, poster path,
# duration label "m:ss"); None renders the block without media, with the caption
# under the link. Release 37 (owner's choice): the Service MVP episode "The Power Of
# Perception with Maggie Swift" (YouTube xgo2kAY3DkE, 29:33). The episode opens with a
# 28s "Coming up" teaser and two title cards, so the clip is the first three minutes of
# the show itself: 0:50.75 (the first frame after the title card's black, where Joe Crisara
# starts speaking) to 3:51.15 (a pause), 180.4s. The poster is the 1:11.8 frame of the
# set's wide shot: Maggie on the studio screen, Joe in his chair, the lit logo between
# them. Never swap in another episode pulled from YouTube without the owner. Its duration
# and faststart are checked like every other film in vspot_media().
PODCAST_VIDEO = ("servicemvp-perception.mp4", f"{P}/servicemvp-perception.webp", "3:00")
PODCAST_EPISODE_URL = "https://www.youtube.com/watch?v=xgo2kAY3DkE"
PODCAST_CAPTION = "The Power of Perception with Maggie Swift, Service MVP podcast."


def podcast_media():
    """Block 04's media and caption, or the caption alone while there is no video."""
    if not PODCAST_VIDEO:
        return f'<p class="wwd-cap"><span>{PODCAST_CAPTION}</span></p>'
    fn, poster_path, du = PODCAST_VIDEO
    mime = "image/webp" if poster_path.endswith(".webp") else "image/jpeg"
    media = (vspot_media(fn, du, poster_path, "The Power of Perception, Service MVP podcast") if MODE == "web" else
             f'<div class="vspot"><img src="{asset(poster_path, mime)}"'
             f'{dims(poster_path)} alt="" loading="lazy"></div>')
    return (f'<div class="wwd-film">{media}<p class="wwd-cap"><span>{PODCAST_CAPTION}</span>'
            f'<span class="du">{du}</span></p></div>')


# ---- Testimonial (release 8, F) ----------------------------------------------
# Mike, owner of Bee Right There Heating & Air, on the Service MVP podcast (YouTube
# WoQBaTu2K28, 32:56 to 34:29). Captions are built from YouTube's auto-captions and
# time-aligned to the clip. The pull quote is his words verbatim and is NEVER edited;
# no surname (we do not have it).
TESTIMONIAL_VIDEO = ("mike-testimonial.mp4", f"{P}/mike-testimonial.webp", "1:33",
                     "mike-testimonial.vtt")
TESTIMONIAL_QUOTE = ("We would get to the customer&#39;s home and it was like they already made "
                     "their mind up that they were going to purchase from us.")
TESTIMONIAL_BY = "Mike, owner, Bee Right There Heating &amp; Air, Atascadero, CA"


def testimonial():
    """The video with the pull quote beside it (desktop) or below it (phones)."""
    fn, poster_path, du, vtt = TESTIMONIAL_VIDEO
    if MODE == "web":
        media = vspot_media(fn, du, poster_path, "Mike from Bee Right There on working with us",
                            captions=vtt)
    else:
        media = (f'<div class="vspot"><img src="{asset(poster_path, "image/webp")}"'
                 f'{dims(poster_path)} alt="" loading="lazy"></div>')
    return (f'<div class="tmn"><div class="tmn-media">{media}'
            f'<p class="wwd-cap"><span>On the Service MVP podcast.</span>'
            f'<span class="du">{du}</span></p></div>'
            f'<figure class="tmn-quote"><blockquote><p>&ldquo;{TESTIMONIAL_QUOTE}&rdquo;</p>'
            f'</blockquote><figcaption>{TESTIMONIAL_BY}</figcaption></figure></div>')


# three spots that carry the range: two premises from All Heart, one from Handyman Dan.
# Looked up by YouTube id, so the file, title and duration always match the lists.
_SPOT_BY_YT = {x[4]: x for x in allheart + handyman}
HOME_SPOTS = [(_SPOT_BY_YT[yt][0], who, _SPOT_BY_YT[yt][2], _SPOT_BY_YT[yt][3], yt)
              for who, yt in (("All Heart", "zaCFfVetfFI"), ("All Heart", "TPDZ-OvRNgc"),
                              ("Handyman Dan", "AfkePSa8XLU"))]

# The doors band's background (homepage and /team): a frame of All Heart's "The Quote"
# (spots/ah10.mp4 at 4.5s, 1280x720 WebP), a technician and a homeowner beside the condenser.
# It was the Tulsa aerial (post/quality1.jpg) until release 8, which repeated the brand
# film's poster a screen above; that still now appears only as the film's poster.
DOORS_STILL = (f'<img class="doors-bg" src="{asset(f"{P}/doors-allheart.webp", "image/webp")}"'
               f'{dims(f"{P}/doors-allheart.webp")} alt="" loading="lazy" decoding="async">')

# ---- What We Do slates (release 29) ----------------------------------------------
# The owner chose option B, "Brand production slate", from the clapper mockups in
# reports/hss-audit/clapper-options (gen.mjs optionB). Same geometry, colours and type:
# a charcoal board, HSS orange and white stripes, ROLL | SCENE | TAKE, the number large
# in the SCENE field. Flat shapes only. The artwork is drawn once (SLATE_DEFS) and each
# number is a small <svg> that <use>s it, so four slates cost the homepage about 3KB
# instead of about 10KB. Each bar's stripes are one <path> rather than one polygon each,
# same shapes. Owner correction (release 29): the arm rests OPEN at option A's angle and
# hinge, -9 degrees about the arm's bottom-left (2, 14), with A's steel hinge rivet. The
# viewBox grows to the open arm's reach and slate() scales and shifts the svg so the
# board and number stay exactly the size and place of the approved closed mockup.
# Decorative: the .wwd-num paragraph around it is aria-hidden, as the plain number was,
# and the headings carry the structure.
def _svgn(v):
    """A coordinate to two decimals, written short (14 not 14.0, -24.06)."""
    r = float("%.2f" % v)
    if r == 0:
        return "0"
    t = repr(r)
    return t[:-2] if t.endswith(".0") else t


_SLATE_INK = {"charcoal": "#1E2226", "orange": "#F04820", "white": "#FFFFFF", "rule": "#4B535B",
              "label": "#C9CDD2"}
_SLATE_FONT = "Archivo, 'Arial Black', Arial, sans-serif"


def _slate_bar(cid, y, w, h, d):
    """A white bar with orange diagonal stripes (period 32, slant .62 of the height),
    clipped to its rounded rect and framed in charcoal. d: 1 = '/', -1 = '\\'."""
    s, k, sub, xi = 16, h * 0.62, [], -h * 0.62 - 32
    while xi < w + 32:
        q = ([(xi, y + h), (xi + s, y + h), (xi + s + k, y), (xi + k, y)] if d > 0 else
             [(xi + k, y + h), (xi + k + s, y + h), (xi + s, y), (xi, y)])
        sub.append("M" + "L".join(f"{_svgn(a)} {_svgn(b)}" for a, b in q) + "Z")
        xi += 32
    return (f'<clipPath id="{cid}"><rect y="{_svgn(y)}" width="{w}" height="{h}" rx="2"/></clipPath>'
            f'<g clip-path="url(#{cid})"><rect y="{_svgn(y)}" width="{w}" height="{h}" '
            f'fill="{_SLATE_INK["white"]}"/><path d="{"".join(sub)}" fill="{_SLATE_INK["orange"]}"/></g>'
            f'<rect x="0.5" y="{_svgn(y + 0.5)}" width="{w - 1}" height="{h - 1}" rx="2" fill="none" '
            f'stroke="{_SLATE_INK["charcoal"]}" stroke-width="1"/>')


_SW, _SSTICK, _SGAP, _SBOARD = 136, 13, 1.6, 75
_S_LOW = 1 + _SSTICK + _SGAP
_S_BOARD = _S_LOW + _SSTICK + _SGAP
_S_RULE = _S_BOARD + 16.5
SLATE_DEFS = (
    '<svg class="slate-defs" aria-hidden="true" focusable="false"><defs>'
    f'<g id="slate-arm">{_slate_bar("slate-ca", 1, _SW, _SSTICK, -1)}</g>'
    f'<g id="slate-body">{_slate_bar("slate-cl", _S_LOW, _SW, _SSTICK, 1)}'
    f'<rect y="{_svgn(_S_BOARD)}" width="{_SW}" height="{_SBOARD}" rx="3" fill="{_SLATE_INK["charcoal"]}"/>'
    f'<path d="M24 {_svgn(_S_BOARD + 6)}V{_svgn(_S_BOARD + _SBOARD - 6)}M{_SW - 24} {_svgn(_S_BOARD + 6)}'
    f'V{_svgn(_S_BOARD + _SBOARD - 6)}M6 {_svgn(_S_RULE)}H{_SW - 6}" stroke="{_SLATE_INK["rule"]}" '
    f'stroke-width="1.1" fill="none"/>'
    f'<g text-anchor="middle" font-family="{_SLATE_FONT}" font-weight="700" font-size="7.4" '
    f'letter-spacing="{_svgn(0.06 * 7.4)}" fill="{_SLATE_INK["label"]}">'
    + "".join(f'<text x="{_svgn(x)}" y="{_svgn(_S_BOARD + 11.6)}">{t}</text>'
              for t, x in (("ROLL", 12), ("SCENE", _SW / 2), ("TAKE", (_SW - 24 + _SW) / 2)))
    + '</g>'
    f'<circle cx="5.6" cy="{_svgn(_S_LOW - _SGAP / 2)}" r="2.8" fill="#9AA3AB"/></g></defs></svg>')
_SLATE_NUM_Y = (_S_RULE + _S_BOARD + _SBOARD) / 2 + 0.7 * 64 / 2   # centred on the digits' ink
SLATE_ARM_DEG, SLATE_HINGE = -9, (2, 1 + _SSTICK)                  # option A's angle and pivot


def _slate_box():
    """viewBox and inline sizing for the open slate. The closed board is .86em of
    --f-mega over a 105.2-unit viewBox; the open arm reaches above and left of it, so
    the viewBox grows by that much (plus .6 units) and the svg grows and shifts by the
    same fraction: the board keeps its size and position, the heading below stays put."""
    a, (px, py) = math.radians(SLATE_ARM_DEG), SLATE_HINGE
    pts = [(x, y) for x in (0, _SW) for y in (1, 1 + _SSTICK)]
    xs = [px + (x - px) * math.cos(a) - (y - py) * math.sin(a) for x, y in pts]
    ys = [py + (x - px) * math.sin(a) + (y - py) * math.cos(a) for x, y in pts]
    left, top = -min(0, min(xs) - 0.6), -min(0, min(ys) - 0.6)
    h0 = _S_BOARD + _SBOARD
    em = 0.86 / h0
    vb = f"{_svgn(-left)} {_svgn(-top)} {_svgn(_SW + left)} {_svgn(h0 + top)}"
    # position:relative, not margins: a negative top margin collapses through the
    # paragraph and would move the heading too
    style = (f"height:{(h0 + top) * em:.4f}em;position:relative;top:{-top * em:.4f}em;"
             f"left:{-left * em:.4f}em")
    return vb, re.sub(r"(?<![0-9])0\.", ".", style)


_SLATE_VB, _SLATE_STYLE = _slate_box()


def slate(n):
    """One What We Do slate: the shared artwork plus this block's number, white Archivo
    900 at 64 units in the SCENE field. The arm is its own <use>, resting open through
    its transform attribute (so no JS, no CSS and reduced motion all show it open)."""
    assert re.fullmatch(r"\d\d", n), n
    hx, hy = SLATE_HINGE
    # size, offset and number type live in HOME_CSS (homepage only), once, not per slate
    return (f'<svg class="slate" viewBox="{_SLATE_VB}" aria-hidden="true" focusable="false">'
            f'<use class="arm" href="#slate-arm" transform="rotate({SLATE_ARM_DEG} {hx} {hy})"/>'
            f'<use href="#slate-body"/><text class="sn" x="{_svgn(_SW / 2)}" '
            f'y="{_svgn(_SLATE_NUM_Y)}">{n}</text></svg>')


# The clap (release 29, owner): each What We Do slate claps once when it scrolls into
# view. CLAP_JS adds .is-clap; the CSS keyframes (slate-clap) shut the arm and spring it
# back to its resting angle in .45s, transform only. The CSS rotation pivots on the
# hinge, (2, 14) in the slate's user space (transform-box:view-box): the same point as
# the arm's transform attribute, so the clap starts and ends exactly on the resting pose
# (checked pixel for pixel). The slate svg is overflow:visible so the small overshoot
# past -9 degrees can paint above the viewBox. Reduced motion or no
# IntersectionObserver: nothing runs and the arm rests open. The .wwd-num box keeps the
# old number's 1em line so the headings do not move; slate() sizes and offsets the svg.
# Homepage-only styles (release 29 slates, release 32 film pair, release 33 services row
# and the phone film row): CSS is inline in every page's head and render-blocking, so
# other pages should not pay for them. Release 33 (owner): below 760px block 03's three
# films are one sideways swipe row like the Handyman Dan strip (82% cards, snap,
# overflow-y hidden so it never scrolls vertically); .wwd-pair dissolves into the row
# with display:contents. From 760px the layout is unchanged. Release 34: HOME_CSS styles nothing
# in the hero, so it ships in the body just before .hero-lines, after the hero's text and its
# placeholder image (the phone LCP). Head CSS is render blocking, and at the throttled phone
# profile every KB ahead of that image costs about 5ms of LCP.
# the strip's sprocket rails: the buttons' hole tile, larger (8x6 in a 14px pitch)
SVC_HOLE = ("url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='6'%3E"
            "%3Crect x='3' width='8' height='6' rx='1.5' fill='%23F5F4F1'/%3E%3C/svg%3E\")")
SVC_HOLES = f"{SVC_HOLE},{SVC_HOLE}"
HOME_CSS = f"""<style>
  .wwd-num .slate{{display:block;width:auto;overflow:visible;{_SLATE_STYLE}}}
  .slate .sn{{font:900 64px {_SLATE_FONT};letter-spacing:{_svgn(-0.02 * 64)}px;fill:#FFFFFF;
    text-anchor:middle;}}
  .slate-defs{{position:absolute;width:0;height:0;overflow:hidden;}}
  .slate.is-clap .arm{{transform-box:view-box;transform-origin:2px 14px;
    animation:slate-clap .45s both;}}
  @keyframes slate-clap{{
    0%{{transform:rotate(-9deg);animation-timing-function:cubic-bezier(.55,0,1,.45);}}
    30%{{transform:rotate(0deg);animation-timing-function:cubic-bezier(.2,.8,.3,1);}}
    78%{{transform:rotate(-10.5deg);animation-timing-function:ease-in-out;}}
    100%{{transform:rotate(-9deg);}}}}
  .wwd-block{{scroll-margin-top:76px;}}
  .svc{{margin-top:var(--s7);}}
  /* release 34: the strip and the stat line are two sections. The band's wrap splits around a
     full-width gradient hairline (the nav and footer rule, dark-ground stops), with room on both
     sides and a "Real numbers" eyebrow over the stats */
  .hero-lines > .band-a{{padding-bottom:var(--s7);}}
  .hero-lines > .band-b{{padding-top:var(--s7);}}
  @media(min-width:760px){{.hero-lines > .band-a{{padding-bottom:var(--s8);}}
    .hero-lines > .band-b{{padding-top:var(--s8);}}}}
  .band-rule{{position:relative;z-index:1;height:1px;background:linear-gradient(90deg,
    rgba(var(--orange-rgb),.55) 0%,rgba(var(--cyan-rgb),.42) 42%,rgba(255,255,255,.3) 78%,
    rgba(255,255,255,0) 100%);}}
  .stats-h{{margin:0;}}
  .band-b .stats{{margin-top:var(--s4);}}
  .svc-h{{margin:0 0 var(--s4);}}
  .svc-strip{{list-style:none;margin:0;padding:0;display:grid;
    grid-template-columns:repeat(2,minmax(0,1fr));row-gap:var(--s5);}}
  @media(min-width:760px){{.svc-strip{{grid-template-columns:repeat(4,minmax(0,1fr));}}}}
  .svc-frame{{display:block;color:var(--ink);text-decoration:none;}}
  .svc-film{{display:block;padding:16px 4px;background:{SVC_HOLES} #262B30;
    background-repeat:space no-repeat;background-size:14px 6px;
    background-position:0 5px,0 calc(100% - 5px);}}
  .svc-pic{{display:block;position:relative;overflow:hidden;border-radius:1px;background:#0B0D0F;}}
  .svc-pic noscript img{{position:absolute;inset:0;}}
  .svc-pic img{{display:block;width:100%;height:auto;aspect-ratio:16/9;object-fit:cover;opacity:.9;
    transition:transform .4s cubic-bezier(.2,.6,.3,1),opacity .4s;}}
  @media(hover:hover){{.svc-frame:hover img{{opacity:1;transform:scale(1.045);}}
    .svc-frame:hover .svc-name{{color:var(--orange);}}}}
  .svc-cap{{display:flex;flex-direction:column;gap:2px;padding:var(--s3) var(--s2) 0;}}
  .svc-cap .slate{{display:block;align-self:flex-start;height:34px;width:auto;overflow:visible;
    margin:0 0 var(--s2) -2px;}}
  .svc-name{{font-family:var(--display);font-weight:700;font-size:var(--f-h4);line-height:1.2;
    letter-spacing:var(--t-head);}}
  .svc-line{{font-size:var(--f-sm);line-height:1.45;color:var(--ink-2);}}
  @media(max-width:559px){{.svc-cap .slate{{height:28px;}}.svc-name{{font-size:var(--f-body);}}}}
  .wwd-pair{{display:grid;grid-template-columns:minmax(0,1fr);gap:var(--s6);margin-top:var(--s6);}}
  .wwd-pair .wwd-film{{margin-top:0;}}
  @media(min-width:760px){{.wwd-pair{{grid-template-columns:repeat(2,minmax(0,1fr));gap:var(--s5);}}}}
  @media(max-width:759px){{
    .wwd-films{{display:flex;overflow-x:auto;overflow-y:hidden;overscroll-behavior-x:contain;
      scroll-snap-type:x mandatory;gap:var(--s3);margin-top:var(--s6);padding-bottom:var(--s2);
      scrollbar-width:thin;}}
    .wwd-films .wwd-pair{{display:contents;}}
    .wwd-films .wwd-film{{flex:0 0 82%;margin-top:0;scroll-snap-align:start;}}
  }}
</style>"""
# Services index (release 33, owner): the four What We Do services as a row of cards in
# the hero band, after the intro sentence and above the stat line, so a first visit
# sees what the company does at a glance. Each card is one link to its block below
# (ids on the .wwd-block divs), with the block's slate drawn small, arm open and
# without the clap (CLAP_JS only watches .wwd-num). A nav landmark labelled by a
# visible h2 eyebrow, "Our services", so it does not repeat the "What We Do" H2.
# Light cards on the dark band: they re-declare the light tokens, the same scoping the
# hero uses the other way round. One short line each, from the section copy.
SERVICES = [
    ("01", "Social Media Packages", "A reel every weekday, posted for you.", "wwd-social", "svc-social"),
    ("02", "Commercial shoots", "Spots built on one strong idea.", "wwd-commercial", "svc-commercial"),
    ("03", "Brand videos", "A film that tells your story.", "wwd-brand", "svc-brand"),
    ("04", "Podcast production", "We build the set. You talk.", "wwd-podcast", "svc-podcast"),
]


# frame width: a quarter of the 1072px content column less the 8px between frames, or of
# the viewport less the 48px gutters; half on phones (two frames a row)
SVC_SIZES = ("(min-width:1120px) 260px,(min-width:760px) calc(25vw - 20px),calc(50vw - 32px)")


BLANK_GIF = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"


def services_row():
    def frame(n, name, line, aid, still):
        big = f"{P}/{still}.webp"
        src = asset(big, "image/webp")
        # 480w covers a 2x desktop frame (260px); phones at 2x need about 330px, so they take
        # the 336w file. In the web build the stills are deferred by SVC_JS (data-src), because
        # native lazy loading fetches anything within 1250 to 2500px of the viewport, which is
        # all four at first load on a phone; <noscript> keeps them for readers without JS. The
        # inline artifact build keeps a plain src (its data URIs are already inline).
        if MODE != "web":
            img = f'<img src="{src}"{dims(big)} alt="" loading="lazy" decoding="async">'
        else:
            small = asset(f"{P}/{still}-336.webp", "image/webp")
            img = (f'<img src="{BLANK_GIF}" data-src="{src}" data-srcset="{small} 336w, {src} 480w" '
                   f'sizes="{SVC_SIZES}"{dims(big)} alt="" decoding="async">'
                   f'<noscript><img src="{small}"{dims(big)} alt=""></noscript>')
        return (f'<li><a class="svc-frame" href="#{aid}"><span class="svc-film"><span class="svc-pic">'
                f'{img}</span></span><span class="svc-cap">{slate(n)}<span class="svc-name">{name}'
                f'</span><span class="svc-line">{line}</span></span></a></li>')
    return (f'<nav class="svc" aria-labelledby="svc-h"><h2 class="eyebrow svc-h" id="svc-h">Our '
            f'services</h2><ul class="svc-strip">{"".join(frame(*x) for x in SERVICES)}</ul></nav>')


# The services strip's stills (release 34): set each src only when the strip is within 100px
# of the viewport, so a phone's first load does not carry them. No IntersectionObserver: load.
SVC_JS = """<script>
(function(){
  var imgs = [].slice.call(document.querySelectorAll('.svc img[data-src]'));
  function show(i){ i.srcset = i.getAttribute('data-srcset'); i.src = i.getAttribute('data-src');
    i.removeAttribute('data-src'); }
  if(!('IntersectionObserver' in window)){ imgs.forEach(show); return; }
  var io = new IntersectionObserver(function(es){
    es.forEach(function(e){ if(e.isIntersecting){ io.unobserve(e.target); show(e.target); } });
  }, {rootMargin: '0px 0px 100px 0px'});
  imgs.forEach(function(i){ io.observe(i); });
})();
</script>"""


CLAP_JS = """<script>
(function(){
  if(!('IntersectionObserver' in window)) return;
  if(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var io = new IntersectionObserver(function(es){
    es.forEach(function(e){
      if(!e.isIntersecting) return;
      io.unobserve(e.target);                       /* once per slate per load */
      e.target.classList.add('is-clap');
    });
  }, {threshold: 0.6});
  [].forEach.call(document.querySelectorAll('.wwd-num .slate'), function(s){ io.observe(s); });
})();
</script>"""


HOME_HTML = f"""<title>Home Service Studios</title>
{FONT_CSS}
{CSS}
<a class="skip" href="#main">Skip to content</a>
{nav("home")}

<main id="main">
<div class="hero hero-bold">
  <div class="hero-media">
    <!-- the text comes first in the DOM: a poster earlier in the markup let Chrome
         paint the image before the headline was parsed, and the text block then
         shifted into place (CLS). Poster, film and scrim are absolutely positioned
         under it by z-index, so the order changes nothing on screen. -->
    <div class="wrap">
      <div class="herotext">
        <p class="eyebrow">Home Service Studios &middot; Los Angeles</p>
        <h1 class="display">A video that makes you feel nothing <span class="hl">does nothing.</span></h1>
      </div>
      <div class="scrollhint">{SCROLL_ICON}</div>
    </div>
    {HERO_MEDIA}
    <div class="hero-scrim"></div>
  </div>
  {HOME_CSS}
  <div class="hero-lines">{SPLAT_SVG}<div class="wrap band-a">
  <p class="sub">We write, shoot, edit and post video for home service companies <strong>nationwide</strong>.
  When a homeowner needs a repair, a replacement or a remodel, they call a name they already know.
  <strong>We make sure that name is yours.</strong></p>
  {SLATE_DEFS}
  {services_row()}{SVC_JS if MODE == "web" else ""}
  </div>
  <div class="band-rule" aria-hidden="true"></div>
  <div class="wrap band-b">
  <h2 class="eyebrow stats-h">Real numbers</h2>
  <div class="stats quad">
    <a class="stat" href="{case_url("a1")}"><span class="case">A1 Air Conditioning</span><span class="n">2.26M</span><span class="k">Views in six months</span></a>
    <div class="stat"><a class="case" href="{case_url("beerightthere")}">Bee Right There</a><a class="n" href="{BRT_REEL_URL}" aria-label="{BRT_REEL_LABEL}">{BRT_REEL_SHORT}</a><span class="k">Views on one reel</span></div>
    <a class="stat" href="{case_url("icomfort")}"><span class="case">iComfort</span><span class="n">+1,680</span><span class="k">Organic followers, under a year</span></a>
    <a class="stat" href="#roster"><span class="case">Our Brands</span><span class="n">{ROSTER_COUNT}</span><span class="k">Clients across the country</span></a>
  </div>
  <div class="ctarow">
    <a class="cta" href="/packages/">{reel("See the packages")}</a>
    <a class="cta ghost" href="/our-work/">See our work</a>
  </div>
  </div></div>
</div>


<section id="roster" class="on-ink"><div class="wrap">
  <div class="sec-head bare">
    <h2 class="display">Our Clients</h2>
    <p class="lede">Home service companies across the country, most of them in heating, cooling,
    plumbing or electrical.</p>
  </div>
  {logo_marquee()}
</div></section>

<section id="what-we-do" class="wwd"><div class="wrap">
  <div class="sec-head">
    <h2 class="display">What We Do</h2>
  </div>

  <div class="wwd-block" id="wwd-social">
    <p class="wwd-num" aria-hidden="true">{slate("01")}</p>
    <h3 class="wwd-title">Social Media Packages</h3>
    <p class="wwd-copy">A reel every weekday and graphics every weekend, planned and posted for
    you. Here is what that looks like on three client accounts.</p>
    <div class="ctarow">
      <a class="cta" href="/packages/">{reel("Compare the packages")}</a>
      <span class="ctanote">Month to month, with no setup fee.</span>
    </div>
    <div class="igrow">
{chr(10).join(ig_grab(*g) for g in IG_GRABS)}
    </div>
  </div>

  <div class="wwd-block" id="wwd-commercial">
    <p class="wwd-num" aria-hidden="true">{slate("02")}</p>
    <h3 class="wwd-title">Commercial shoots</h3>
    <p class="wwd-copy">Spots built on one strong idea. Shot in a single production block, so the
    cost lands once.</p>
    <a class="wwd-link" href="/our-work/all-heart/">See the All Heart campaign&nbsp;&rarr;</a>
    <div class="grid">
{chr(10).join(spot(*s) for s in HOME_SPOTS)}
    </div>
    <p class="mw-ask">Want spots like these for your market?</p>
    <a class="cta" href="{COMMERCIAL_ASK}">{reel("Ask about a commercial shoot")}</a>
  </div>

  <div class="wwd-block" id="wwd-brand">
    <p class="wwd-num" aria-hidden="true">{slate("03")}</p>
    <h3 class="wwd-title">Brand videos</h3>
    <p class="wwd-copy">A film that tells your company&#39;s story. Made for your homepage, your
    YouTube and your hiring.</p>
    <a class="wwd-link" href="https://www.youtube.com/watch?v=m3HEWS9qMTM">Watch the full film&nbsp;&rarr;</a>
    <div class="wwd-films">
    <div class="wwd-film">
    {brand_film()}
    <p class="wwd-cap"><span>Brand film for Quality Heating Cooling Plumbing Electrical, Tulsa.</span>
    <span class="du">1:44</span></p>
    </div>
    {brand_films_more()}
    </div>
    <p class="mw-ask">Want a film like these for your company?</p>
    <a class="cta" href="{BRAND_ASK}">{reel("Ask about a brand video")}</a>
  </div>

  <div class="wwd-block" id="wwd-podcast">
    <p class="wwd-num" aria-hidden="true">{slate("04")}</p>
    <h3 class="wwd-title">Podcast production</h3>
    <p class="wwd-copy">We build the set, run the shoot and handle the edit. You show up and
    talk.</p>
    <p class="wwd-small">Set build, production and post.</p>
    <a class="wwd-link" href="{PODCAST_EPISODE_URL}">Watch the full episode&nbsp;&rarr;</a>
    {podcast_media()}
    <p class="mw-ask">Want a show of your own?</p>
    <a class="cta" href="{PODCAST_ASK}">{reel("Ask about podcast production")}</a>
  </div>
</div></section>

<section id="from-a-client" class="tmn-section"><div class="wrap">
  <div class="sec-head">
    <h2 class="display">From a client</h2>
  </div>
  {testimonial()}
  <a class="wwd-link tmn-link" href="{case_url("beerightthere")}">Read the Bee Right There case&nbsp;&rarr;</a>
</div></section>

<section class="doors-section">{DOORS_STILL}<div class="wrap">
  <div class="doors">
    <a class="door" href="/our-work/">
      <span class="tier">Portfolio</span>
      <h3>See the work</h3>
      <p>Case studies with the numbers attached, and the reasoning behind each one.</p>
      <span class="go">Open the portfolio &rarr;</span>
    </a>
    <a class="door" href="/packages/">
      <span class="tier">Social Media Packages</span>
      <h3>See the packages</h3>
      <p>{PROGRAMS_WORD.capitalize()} packages, with plain terms. We are honest about what
      consistent content does and does not do.</p>
      <span class="go">Compare the packages &rarr;</span>
    </a>
  </div>
</div></section>

</main>

{site_footer("home")}
{actionbar()}
{CAL_POPUP}
{SPLAT_JS}
{SOLO_JS}
{NAV_JS}
{MOTION_JS}
{CLAP_JS}
{HERO_JS}
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
# most of the logos on the wall are HVAC, plumbing or electrical.
TRADE_GROUPS = [
    ("Home services", ["HVAC", "Plumbing", "Electrical", "Roofing", "Garage doors", "Generators",
                       "More than one of these", "Another home service"]),
    ("Property and building", ["Remodeling, ADU or new build",
                               "Real estate agent or brokerage"]),
    ("Something else", ["Creator, artist or channel"]),
]
TRADES = [x for _, opts in TRADE_GROUPS for x in opts]
# api_contact.js validates the trade against its own TRADES list and bounces anything
# else with a 400, so the two must stay identical (same check as the budget bands).
_api_trades = re.findall(r'"([^"]*)"', re.search(
    r"const TRADES = \[(.*?)\];", pathlib.Path(f"{S}/api_contact.js").read_text(), re.S).group(1))
assert _api_trades == TRADES, "api_contact.js TRADES must match TRADE_GROUPS: " + repr(TRADES)

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
    <span class="fhint">Nobody is held to this. It tells us which packages are
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
    <button type="submit" class="cta" id="cbtn">{reel("Send to HSS")}</button>
    <p class="ctanote">We answer within one business day. No list, no newsletter,
    no automated sequence.</p>
  </div>
  <p class="fstatus" id="fstatus" role="status" aria-live="polite"></p>
</form>"""


# ---- contact page ---------------------------------------------------------

# Release 37: the Google scheduler lives on /book/ only. /contact/ points there in one line
# under its hero button (with booking on), and keeps the form as its own job.
# The scheduler's frame height, reserved up front. Google's embedded page, measured at the
# frame's width (release 37): 704 to 771px tall side by side, 1,213 to 1,256px stacked, which it
# does once the frame is under about 580px wide (a viewport under about 630px). So 800px from
# a 650px viewport up and 1,300px below, with room to spare and no second scrollbar.
BOOK_FRAME_H = (800, 1300)
BOOK_LINE = ('<p class="booknote">Rather talk it through? <a href="/book/">Book a strategy call.</a></p>'
             if BOOKED else "")




# /book/ (release 37, owner): the strategy call. Google's embedded appointment schedule in a
# frame whose height is reserved up front (no layout shift; the frame scrolls inside if
# Google's page is ever taller), loaded eagerly here and nowhere else. No floating bubble on
# this page: nothing should sit over the scheduler.
BOOK_HTML = f"""<title>Book a strategy call</title>
{FONT_CSS}
{CSS}
<style>
  .book-sec{{padding:var(--s7) 0 var(--s8);}}
  .book-frame{{height:{BOOK_FRAME_H[0]}px;}}
  .book-frame iframe{{display:block;width:100%;height:100%;border:0;}}
  @media(max-width:759px){{.book-sec{{padding:var(--s5) 0 var(--s7);}}}}
  @media(max-width:649px){{.book-frame{{height:{BOOK_FRAME_H[1]}px;}}}}
  .book-alt{{margin:var(--s5) 0 0;font-size:var(--f-body);color:var(--ink-2);}}
  .book-alt + .book-alt{{margin-top:var(--s2);font-size:var(--f-sm);}}
</style>
<a class="skip" href="#main">Skip to content</a>
{nav("book")}

<main id="main">
<div class="hero hero-dark">{SPLAT_SVG}<div class="wrap">
  <p class="eyebrow">Strategy call &middot; Home Service Studios</p>
  <h1 class="display">Book a <span class="hl">strategy call.</span></h1>
  <p class="sub">Pick a time that works for you. It&#39;s a one-hour video call with our team.
  We&#39;ll look at your market and what you&#39;re posting now.</p>
</div></div>

<section class="book-sec"><div class="wrap">
  <div class="schedwrap book-frame">
    <iframe src="{BOOK_EMBED}" title="Book a strategy call with Home Service Studios"
      width="100%" height="{BOOK_FRAME_H[0]}" loading="eager"></iframe>
  </div>
  <p class="book-alt">Prefer to write? <a href="/contact/">Send us a message</a></p>
  <p class="book-alt"><a href="{BOOK_URL}">Open the booking page</a></p>
</div></section>
</main>

{site_footer("book")}
{actionbar()}
{CAL_POPUP_PANEL}
{SPLAT_JS}
{NAV_JS}
"""


CONTACT_HTML = f"""<title>Contact</title>
{FONT_CSS}
{CSS}
<a class="skip" href="#main">Skip to content</a>
{nav("contact")}

<main id="main">
<div class="hero hero-dark hero-contact">{SPLAT_SVG}<div class="wrap">
  <p class="eyebrow">Contact &middot; Home Service Studios</p>
  <h1 class="display">Talk <span class="hl">to us.</span></h1>
  <p class="sub">Tell us your city and your trade. We will come back with something specific to
  your market, not a brochure. Want to look first? The work is in the
  <a href="/our-work/">case studies</a>, and our Social Media Packages are
  <a href="/packages/">priced in public</a>. You can also <a href="mailto:{EMAIL}">email us</a>
  directly for scope, budgets or attachments. The form gets you a faster, more specific reply.</p>
  <div class="ctarow">
    <a class="cta" href="#start">{reel("Send us a message")}</a>
  </div>
  {reassure("contact")}
  {BOOK_LINE}
</div></div>


<section id="start"><div class="wrap">
  <div class="sec-head">
    <p class="eyebrow">Send a message</p>
    <h2 class="display">Tell us about your market</h2>
    <p class="lede">Six questions, under a minute. Your first reply will be about
    <strong>your city and your trade</strong>, not a generic hello.</p>
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
{CAL_POPUP_PANEL}
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
        # Release 30 (owner copy, short sentences; R21 before). Production titles in <em>.
        "bio": "Craig is a filmmaker and photographer with more than ten years in production. "
               "He worked on the crews of network reality and game shows, including "
               "<em>America&#39;s Got Talent</em> and <em>Family Feud</em>. That meant "
               "television made fast, on schedule, with real people instead of actors. Filming "
               "a contractor on a live job takes exactly that. Craig cofounded Home Service "
               "Studios out of its Marina del Rey office. He is hands-on with every shoot."},
    {"name": "Seth Yeager", "title": "Cofounder", "photo": "seth-yeager.jpg",
        # Release 18 (owner copy, exact, short sentences). The earlier unit credit was
        # removed on the owner's instruction; do not restore it.
        "bio": "Seth came up on set. Camera, electrical, cinematography and stunts: he has done "
               "it all across film and television. His work includes <em>The Chosen</em> and many "
               "independent films. On <em>The Shop</em>, he was first assistant director. That "
               "production standard is what he brought to contractors as a cofounder of Home "
               "Service Studios."},
]
# Release 24 (owner): TEAM_ROSTER is in reading order, which is the phone order
# (Yoni, Paloma, Sergy). From 760px the CSS puts the first card in the middle column,
# so desktop still reads Paloma | Yoni | Sergy. "bio_teaser" is optional: the exact
# start of "bio" that phones show before "... Read more". No teaser, no toggle.
TEAM_ROSTER = [
    # Release 23: the owner's exact copy. No name-dropping in bios. The owner says treat it
    # as a decade; never use an exact year count like "seven years".
    # Craig Balog and Seth Yeager own the company (owner confirmed 2026-10-06); nothing
    # here may read as Yoni having founded or built it.
    {"name": "Yoni Paz", "title": "Creative Director and Producer", "photo": "yoni-paz.jpg",
        "bio": "Yoni learned video where attention is the only currency. He spent a decade in the "
               "creator economy, shaping original ideas and monetization strategies for full-time "
               "creators. In that world, one rule decides everything: if people stop watching, the "
               "money stops. Yoni brings that rule to every video we make for home service brands.",
        "bio_teaser": "Yoni learned video where attention is the only currency. He spent a decade"},
    # Release 33: the owner's exact copy, verbatim, commas and wording as written (it
    # replaces the release-27 bio). Plain ASCII apostrophes.
    {"name": "Paloma Barros", "title": "Social Media Director", "photo": "paloma-barro.jpg",
        "bio": "Paloma's approach to social media is rooted in understanding people. What "
               "captures their attention, what keeps them watching, and what ultimately makes "
               "them connect with a brand. Her academic and professional experience across "
               "different countries has given her a unique perspective on audiences, consumer "
               "behavior, and digital content. Her work combines creative direction, organic "
               "social strategy, and performance insights to create content that has generated "
               "millions of organic views for our clients and built stronger connections between "
               "brands and their audiences.",
        "bio_teaser": "Paloma's approach to social media is rooted in understanding people. "
                      "What captures their attention"},
    # Release 33: the owner's exact copy, verbatim (his first bio; until now the card had a
    # name and a title only). Plain ASCII.
    {"name": "Sergy Olkowski", "title": "Post Production Supervisor", "photo": "sergy-olkowski.jpg",
        "bio": "Sergy lives where raw footage becomes a finished story. With a background in "
               "editing, motion design, and 3D animation, Sergy builds the custom tools and "
               "workflows that keep production fast without cutting corners.",
        "bio_teaser": "Sergy lives where raw footage becomes a finished story. With a background "
                      "in editing"},
]


def lead_card(p, first=False):
    """first: the opening portrait is in the first viewport on phones and is the
    page's LCP element, so it loads eagerly at high priority instead of lazily."""
    if p.get("photo"):
        src = asset(os.path.join(P, p["photo"]), "image/jpeg")
        load = 'loading="eager" fetchpriority="high"' if first else 'loading="lazy"'
        art = (f'<img src="{src}" alt="{p["name"]}"{dims(os.path.join(P, p["photo"]))} '
               f'{load} decoding="async">')
    else:
        art = PERSON_ICON
    return (f'<div class="lead"><div class="portrait">{art}</div>'
            f'<h3>{p["name"]}</h3><span class="rtitle">{p["title"]}</span>'
            f'<p>{p["bio"]}</p></div>')


def member_card(p):
    if p.get("photo"):
        src = asset(os.path.join(P, p["photo"]), "image/jpeg")
        art = (f'<img src="{src}" alt="{p["name"]}"{dims(os.path.join(P, p["photo"]))} '
               f'loading="lazy" decoding="async">')
    else:
        art = PERSON_ICON
    # Optional, deliberately. A crew card carrying only a name and a title reads
    # as a template waiting for data, which is one of the things that makes the
    # page feel machine assembled. A bio is rendered when the roster has one and
    # the card is unchanged when it does not, so people can be filled in one at a
    # time as they send something rather than all at once.
    bio = f'<p class="mbio">{p["bio"]}</p>' if p.get("bio") else ""
    # Release 24: an optional "bio_teaser" (the exact start of the bio) adds a Read more /
    # Show less toggle, at every width since release 34 (phones only before). The markup
    # always holds the whole bio, so no-JS readers get all of it; the CSS hides .ell and
    # the button unless BIO_JS has run. One button, after the text, toggles both ways, so
    # focus stays on it. On desktop the roster grid is top aligned, so opening one card
    # grows only that card; the others keep their tops and their own height.
    teaser = p.get("bio_teaser")
    if teaser:
        full = p["bio"]
        assert full.startswith(teaser) and full[len(teaser):].strip(), \
            f'{p["name"]}: bio_teaser must be a strict prefix of bio'
        slug = re.sub(r"[^a-z0-9]+", "-", p["name"].lower()).strip("-")
        first = p["name"].split()[0]
        bio = (f'<p class="mbio" data-cut>{teaser}<span class="ell" aria-hidden="true">...</span>'
               f'<span class="rest" id="bio-{slug}">{full[len(teaser):]}</span> '
               f'<button type="button" class="bio-tog" aria-expanded="false" '
               f'aria-controls="bio-{slug}" aria-label="Read more about {first}" '
               f'data-more="Read more about {first}" data-less="Show less about {first}">'
               f'Read more</button></p>')
    return (f'<div class="member"><div class="portrait">{art}</div>'
            f'<h3>{p["name"]}</h3><span class="rtitle">{p["title"]}</span>'
            f'{bio}</div>')


BIO_JS = """<script>
(function(){
  /* Crew bio teasers (release 24; every width since release 34): see member_card().
     Inline right after the roster so the collapse lands before that part of the page
     paints. This script only adds .js-cut and flips .is-open. */
  [].forEach.call(document.querySelectorAll('.mbio[data-cut]'), function(p){
    var b = p.querySelector('.bio-tog'), card = p.closest('.member') || p;
    p.classList.add('js-cut');
    b.addEventListener('click', function(){
      var open = !p.classList.contains('is-open');
      p.classList.toggle('is-open', open);
      b.setAttribute('aria-expanded', open ? 'true' : 'false');
      b.setAttribute('aria-label', b.getAttribute(open ? 'data-less' : 'data-more'));
      b.textContent = open ? 'Show less' : 'Read more';
      /* Keep the card and the toggle in view. After Show less, if the card's top is
         now above the fixed nav, scroll it back under the nav. After Read more, if the
         toggle dropped below the phone action bar, scroll just enough to show it.
         Neither scroll may push the toggle itself out of view. The action bar comes
         later in the page than this script, so both bars are looked up here. */
      var nav = document.querySelector('.nav'), bar = document.querySelector('.actionbar');
      var top = (nav ? Math.max(0, nav.getBoundingClientRect().bottom) : 0) + 8;
      var bot = window.innerHeight;
      if(bar){ var t = bar.getBoundingClientRect(); if(t.height) bot = Math.min(bot, t.top); }
      bot -= 8;
      var c = card.getBoundingClientRect(), r = b.getBoundingClientRect(), d = 0;
      if(!open && c.top < top) d = Math.max(c.top - top, r.bottom - bot);
      else if(r.bottom > bot) d = Math.min(r.bottom - bot, r.top - top);
      if(d) window.scrollBy(0, d);
    });
  });
})();
</script>"""
ROSTER_JS = BIO_JS if any(p.get("bio_teaser") for p in TEAM_ROSTER) else ""


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
    {"".join(lead_card(p, first=(i == 0)) for i, p in enumerate(TEAM_LEADS))}
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
  {ROSTER_JS}
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
      <p>Case studies with the numbers attached, shot and cut by the people above.</p>
      <span class="go">Open the portfolio &rarr;</span>
    </a>
    <a class="door" href="/packages/">
      <span class="tier">Social Media Packages</span>
      <h3>See the packages</h3>
      <p>{PROGRAMS_WORD.capitalize()} packages, with plain terms. We are honest about what
      consistent content does and does not do.</p>
      <span class="go">Compare the packages &rarr;</span>
    </a>
  </div>
</div></section>
</main>

{site_footer("team")}
{actionbar()}
{CAL_POPUP}
{SPLAT_JS}
{NAV_JS}
{MOTION_JS}
"""


# ---- case pages ---------------------------------------------------------------
def case_page(i):
    """A case study page at /our-work/<slug>/, in the D5 style: the dark hero with
    breadcrumbs, the challenge/solution/impact cards and the real proof, then a
    prev/next chain to its neighbours and the CTA. Returns (html, crumb JSON-LD)."""
    c = CASES[i]
    d = CASE_PAGE[c["id"]]
    prev_c = CASES[i - 1] if i > 0 else None
    next_c = CASES[i + 1] if i < len(CASES) - 1 else None
    chain = ""
    if prev_c:
        chain += (f'<a class="pn prev" href="{case_url(prev_c["id"])}">'
                  f'<span class="pn-l">Previous case</span><span class="pn-n">{prev_c["name"]}</span></a>')
    if next_c:
        chain += (f'<a class="pn next" href="{case_url(next_c["id"])}">'
                  f'<span class="pn-l">Next case</span><span class="pn-n">{next_c["name"]}</span></a>')
    crumb_ld = ('<script type="application/ld+json">'
                '{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":['
                '{"@type":"ListItem","position":1,"name":"Home","item":"' + SITE + '/"},'
                '{"@type":"ListItem","position":2,"name":"Work","item":"' + SITE + '/our-work/"},'
                '{"@type":"ListItem","position":3,"name":' + json.dumps(c["name"])
                + ',"item":"' + SITE + case_url(c["id"]) + '"}]}</script>')
    pills = "".join(f'<span class="pill">{r}</span>' for r in d["roles"])
    why = ""
    if d.get("close"):
        why = (f'<div class="case-why"><p class="eyebrow">What it did for them</p>'
               f'<p class="case-close">{d["close"]}</p>'
               + (f'<p class="case-src">{d["source"]}</p>' if d.get("source") else "")
               + '</div>')
    tmn = ""
    if d.get("testimonial"):
        tmn = ('<section class="tmn-section"><div class="wrap">\n'
               '  <div class="sec-head"><h2 class="display">In Mike&#39;s words</h2></div>\n'
               f'  {testimonial()}\n</div></section>\n')
    spot_js = SOLO_JS if ('class="vspot' in d["proof"] or tmn) else ""
    page = f"""<title>{c["name"]}</title>
{FONT_CSS}
{CSS}
<a class="skip" href="#main">Skip to content</a>
{nav("work")}

<main id="main">
<div class="hero hero-dark">{SPLAT_SVG}<div class="wrap">
  <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a><span aria-hidden="true">/</span>
    <a href="/our-work/">Work</a><span aria-hidden="true">/</span>
    <span aria-current="page">{c["name"]}</span></nav>
  <p class="eyebrow">Case {i + 1:02d} &middot; {c["vertical"]} &middot; {d["kind"]}</p>
  <h1 class="display">{c["name"]}.<br><span class="hl">{d["tag"]}</span></h1>
  <p class="sub">{d["lede"]}</p>
  <div class="role"><span class="lbl">Our role</span>{pills}</div>
</div></div>

<section><div class="wrap">
  <div class="sec-head"><h2 class="display">How it worked</h2></div>
  {csi_block(c["id"])}
  {d["ops"]}
</div></section>

{tmn}<section><div class="wrap">
  <div class="sec-head"><h2 class="display">{d["proof_head"]}</h2></div>
  {d["proof"]}
  {why}
</div></section>

<section><div class="wrap">
  <div class="pnrow">{chain}</div>
  <div class="ctarow">
    {book("Project%20enquiry")}
    <a class="cta ghost" href="/our-work/">All case studies</a>
  </div>
  {reassure("case")}
</div></section>
</main>

{site_footer("case")}
{actionbar()}
{CAL_POPUP}
{SPLAT_JS}
{spot_js}
{NAV_JS}
{MOTION_JS}
"""
    return page, crumb_ld


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
    <a class="cta" href="/our-work/">{reel("See the work")}</a>
    <a class="cta ghost" href="/packages/">Social Media Packages</a>
    <a class="cta ghost" href="/contact/">Contact us</a>
  </div>
</div></div>
</main>

{site_footer("404")}
{actionbar()}
{CAL_POPUP}
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
    '"name":"Social Media Packages","itemListElement":[' + _OFFERS + ']}}'
    '</script>'
)


def validate(page, label):
    """Outbound links open in a new tab. Then the two checks that must never ship."""
    page, n = re.subn(
        r'<a ([^>]*href="https?://[^"]*"[^>]*)>',
        r'<a \1 target="_blank" rel="noopener noreferrer">',
        page,
    )
    if 'class="vspot' in page:
        assert "spotstop" in page, f"{label}: hover-play spots but no SOLO_JS to run them"
    if MODE == "web":
        assert 'class="ytspot"' not in page, f"{label}: a YouTube spot card left in the web build"
    # release 34: every primary button is a Reel wheel (reel()), on every page
    for m in re.finditer(r'<(?:a|button)\b[^>]*\bclass="(cta|navcta|primary)((?: [^"]*)?)"[^>]*>', page):
        if "ghost" in m.group(2):
            continue
        assert page.startswith('<svg class="bm-wheel"', m.end()), \
            f"{label}: a primary button without the reel: {m.group(0)[:90]}"
    if 'class="bm-wheel"' in page:
        assert page.count('id="bm-reel"') == 1, f"{label}: Reel wheel buttons need BM_DEFS once"
    assert "—" not in page and "–" not in page, f"DASH FOUND IN {label}"
    bad = sorted({c for c in page if ord(c) > 127})
    assert not bad, f"NON-ASCII IN {label} (use HTML entities): {bad}"
    print(f"  {label}: {n} external links open in a new tab, no dashes, pure ascii")
    return page


def write_web(page, path, *, title, desc, og_image, url, noindex=False, extra_head=""):
    """Vercel serves the raw file, so each page supplies its own document shell.

    noindex is for the 404: GitHub Pages serves that one file at whatever bad
    URL was asked for, so it gets a robots noindex and no canonical, og:url or
    JSON-LD (any of those would claim an address the page does not own)."""
    page = re.sub(r'^\s*<title>[^<]*</title>\s*', '', page)   # head owns the title here
    doc = (
        '<!doctype html>\n<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        + FONT_PRELOAD +
        f'<title>{title}</title>\n'
        + ('<meta name="robots" content="noindex">\n' if noindex else '')
        + f'<meta name="description" content="{desc}">\n'
        '<meta property="og:type" content="website">\n'
        f'<meta property="og:title" content="{title}">\n'
        f'<meta property="og:description" content="{desc}">\n'
        f'<meta property="og:image" content="{og_image}">\n'
        '<meta property="og:image:width" content="1200">\n'
        '<meta property="og:image:height" content="630">\n'
        + ('' if noindex else f'<meta property="og:url" content="{url}">\n')
        + '<meta property="og:site_name" content="Home Service Studios">\n'
        + ('' if noindex else f'<link rel="canonical" href="{url}">\n')
        + '<meta name="theme-color" content="#14171A">\n'
        '<meta name="twitter:card" content="summary_large_image">\n'
        f'<meta name="twitter:image" content="{og_image}">\n'
        f'<link rel="icon" href="{FAVICON}">\n'
        + ('' if noindex else JSON_LD + '\n') + (extra_head + '\n' if extra_head else '')
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
    # Release 30 (owner): 155 characters or fewer, same facts as the case pages (A1 2.26M in
    # six months, Bee Right There 3.8x in three weeks, iComfort 6.8x followers, All Heart ten
    # spots from one shoot). Also the og:description and the CollectionPage description.
    D1 = (f"{num_word(len(CASES)).capitalize()} home service companies and what changed: "
          "2.26M views in six months, 3.8x views in three weeks, 6.8x followers and ten spots "
          "from one shoot.")
    assert len(D1) <= 155, f"/our-work/ meta description is {len(D1)} characters"
    # The portfolio as structured data: a CollectionPage listing every case page.
    WORK_LD = ('<script type="application/ld+json">' + json.dumps({
        "@context": "https://schema.org", "@type": "CollectionPage",
        "name": "Case studies", "url": f"{SITE}/our-work/", "description": D1,
        "mainEntity": {"@type": "ItemList", "itemListElement": [
            {"@type": "ListItem", "position": n + 1, "url": f"{SITE}{case_url(c['id'])}",
             "name": f"{c.get('full', c['name'])} case study".replace("&amp;", "&")}
            for n, c in enumerate(CASES)]}}, separators=(",", ":")) + '</script>')
    n1 = write_web(html, f"{OUT}/index.html",
                   title="Case Studies | Home Services Video Production | Home Service Studios",
                   desc=D1, og_image=f"{SITE}/our-work/a/og-cover.jpg",
                   url=f"{SITE}/our-work/", extra_head=WORK_LD)

    packages = validate(PACKAGES_HTML, "packages")
    D2 = ("Social Media Packages from Home Service Studios: a reel every "
          "weekday, graphics every weekend and stories across your platforms, from "
          f"{money(PRICE_MIN)} a month.")
    n2 = write_web(packages, f"{S}/deploy/packages/index.html",
                   title="Social Media Packages for Home Services | Home Service Studios",
                   desc=D2, og_image=f"{SITE}/og/og-packages.jpg",
                   url=f"{SITE}/packages/")

    contact = validate(CONTACT_HTML, "contact")
    D4 = ("Contact Home Service Studios in Los Angeles. Email us, or send a message "
          "and we will come back with something specific to your market.")
    n4 = write_web(contact, f"{S}/deploy/contact/index.html",
                   title="Contact | Home Service Studios",
                   desc=D4, og_image=f"{SITE}/og/og-contact.jpg",
                   url=f"{SITE}/contact/")

    if BOOKED:
        bookp = validate(BOOK_HTML, "book")
        assert bookp.count("calendar.google.com/appointments") == 1, "book: the scheduler frame"
        D6 = ("Book a one-hour strategy call with Home Service Studios. A video call on Google "
              "Meet about your market and what you are posting now.")
        write_web(bookp, f"{S}/deploy/book/index.html",
                  title="Book a Strategy Call | Home Service Studios",
                  desc=D6, og_image=f"{SITE}/og/og-book.jpg", url=f"{SITE}/book/")

    # case pages (N1). OG art: the per-case frames in og/; A1 has no still yet.
    case_sizes = []
    for i, c in enumerate(CASES):
        page, crumb_ld = case_page(i)
        page = validate(page, c["slug"])
        og = f"{SITE}/og/{c['og']}" if c.get("og") else f"{SITE}/our-work/a/og-cover.jpg"
        case_sizes.append((c["slug"], write_web(
            page, f"{S}/deploy{case_url(c['id'])}index.html",
            title=f"{c['name']} case study | Home Service Studios", desc=c["desc"],
            og_image=og, url=f"{SITE}{case_url(c['id'])}", extra_head=crumb_ld)))
        # the pre-2026-08 address of the same case, kept alive as a redirect
        legacy = (f'<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
                  f'<title>{c["name"]} case study</title><meta name="robots" content="noindex">'
                  '<link rel="icon" href="data:,">'
                  f'<link rel="canonical" href="{SITE}{case_url(c["id"])}">'
                  f'<meta http-equiv="refresh" content="0; url={case_url(c["id"])}"></head>'
                  f'<body><a href="{case_url(c["id"])}">{c["name"]} case study</a></body></html>\n')
        validate(legacy, "legacy " + c["slug"])
        lp = pathlib.Path(f"{S}/deploy/work/{c['slug']}/index.html")
        lp.parent.mkdir(parents=True, exist_ok=True)
        lp.write_text(legacy, encoding="utf-8")

    # Handyman Dan stopped being a case study (R3, 2026-10-06); both of its old
    # addresses now forward to its section on /our-work (#more-work).
    for old in ("/our-work/handyman-dan/", "/work/handyman-dan/"):
        stub = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
                '<title>Handyman Dan commercial campaign | Home Service Studios</title>'
                '<meta name="robots" content="noindex">'
                # an empty icon, so the browser does not ask for /favicon.ico (a 404 on Pages)
                '<link rel="icon" href="data:,">'
                f'<link rel="canonical" href="{SITE}/our-work/">'
                '<meta http-equiv="refresh" content="0; url=/our-work/#more-work"></head>'
                '<body><a href="/our-work/#more-work">Handyman Dan commercial campaign</a>'
                '</body></html>\n')
        validate(stub, "stub " + old)
        sp = pathlib.Path(f"{S}/deploy{old}index.html")
        sp.parent.mkdir(parents=True, exist_ok=True)
        sp.write_text(stub, encoding="utf-8")

    nf = validate(NOT_FOUND_HTML, "404")
    write_web(nf, f"{S}/deploy/404.html", title="Page not found | Home Service Studios",
              desc="This page is not here. See the work, the Social Media Packages, or contact "
                   "Home Service Studios.",
              og_image=f"{SITE}/our-work/a/og-cover.jpg", url=f"{SITE}/404.html", noindex=True)

    team = validate(TEAM_HTML, "team")
    D5 = ("Meet the Home Service Studios team: the people who write, shoot, cut and post "
          "home service video every month.")
    n5 = write_web(team, f"{S}/deploy/team/index.html",
                   title="Meet the Team | Home Service Studios",
                   desc=D5, og_image=f"{SITE}/og/og-team.jpg",
                   url=f"{SITE}/team/")

    for _n, _name, _line, _aid, _still in SERVICES:      # every services card lands on its block
        assert HOME_HTML.count(f'id="{_aid}"') == 1, f"services card #{_aid} has no target"
    home = validate(HOME_HTML, "home")
    D3 = ("Los Angeles video production for HVAC, plumbing and home service brands. Written, "
          "shot, cut and posted monthly. 2.26M views in six months for one HVAC client.")
    n3 = write_web(home, f"{S}/deploy/index.html",
                   title="Home Services Video Production | Los Angeles | Home Service Studios",
                   desc=D3, og_image=f"{SITE}/og/og-home.jpg",
                   url=f"{SITE}/", extra_head=HERO_PRELOAD)

    # the serverless function that receives the contact form
    os.makedirs(f"{S}/deploy/api", exist_ok=True)
    shutil.copy(f"{S}/api_contact.js", f"{S}/deploy/api/contact.js")

    # 3.5 sitemap so the new URLs get discovered. The five /work/<slug>/ pages
    # are gone (2026-08-27): each case now lives inline in .case-panels on
    # /our-work/, opened by the carousel instead of its own URL.
    # 404.html is deliberately not listed: it is noindex and has no address of its own
    urls = (["/", "/our-work/"] + [case_url(c["id"]) for c in CASES]
            + ["/packages/", "/team/", "/contact/"] + (["/book/"] if BOOKED else []))
    sm = ('<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"  <url><loc>{SITE}{u}</loc></url>\n" for u in urls)
          + "</urlset>\n")
    pathlib.Path(f"{S}/deploy/sitemap.xml").write_text(sm, encoding="utf-8")
    # the Google scheduler loads on /book/ and nowhere else
    for _f in pathlib.Path(f"{S}/deploy").rglob("*.html"):
        if _f.parent.name != "book":
            assert "calendar.google.com" not in _f.read_text(), f"{_f}: the scheduler outside /book/"
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
    for slug, n in case_sizes:
        print(f"  our-work/{slug}/ -> {n/1024:.0f} KB")
    print(f"  shared assets        -> {assets/1048576:.2f} MB")
else:
    out = f"{S}/site.html"
    pathlib.Path(out).write_text(html, encoding="utf-8")
    print(f"{out} -> {os.path.getsize(out)/1048576:.2f} MB")
