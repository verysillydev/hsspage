#!/usr/bin/env python3
"""Build the portfolio.

  python3 build_site.py          -> single self-contained file (Claude artifact)
  python3 build_site.py web      -> deploy/our-work/ with external assets (Vercel)
"""
import base64, json, os, pathlib, re, shutil, sys

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
EMAIL = "yoni@yoniverseproductions.com"

# Paste the Google Calendar appointment booking page here and every CTA on the site
# switches at once. While it is empty the buttons fall back to a prefilled mailto,
# and the reassurance line below them is suppressed (it promises a Meet call).
BOOK_URL = ""          # e.g. https://calendar.app.google/xxxxxxxx
BOOKED = bool(BOOK_URL)

PHONE = "13105954519"                 # digits only, used for the tel: href
PHONE_DISPLAY = "(310) 595-4519"

REASSURE = ("Twenty minutes on Google Meet. We'll look at your market, your current content, "
            "and whether a monthly program makes sense.")

# what the form path actually promises, which is not a call yet
REASSURE_FORM = ("Six questions, under a minute. You will hear back within one business day, "
                 "from a person, about your market specifically.")

# Feather "phone", inlined so the header costs no extra request
PHONE_ICON = ('<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" '
              'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
              '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 '
              '19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 '
              '2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 '
              '1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg>')

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
        return (f'<a class="{cls}" href="{BOOK_URL}" target="_blank" '
                f'rel="noopener noreferrer">{label or "Book a call"}</a>')
    return f'<a class="{cls}" href="/contact/#start">{label or "Start a project"}</a>'

def reassure():
    """Sits under the CTA and describes what actually happens next. The promise has
    to match the destination, so it changes with it."""
    return f'<p class="reassure">{REASSURE if BOOKED else REASSURE_FORM}</p>'

def phonebtn(cls="navphone"):
    """Tap to call. The number is hidden on narrow screens but the icon and the
    44px target stay, so the phone never disappears behind a breakpoint."""
    # the number span is hidden below 900px, and the icon is aria-hidden, so the
    # link needs an explicit name or it reads as an unlabelled link to a screen reader
    return (f'<a class="{cls}" href="tel:+{PHONE}" aria-label="Call {PHONE_DISPLAY}">'
            f'{PHONE_ICON}<span class="phnum">{PHONE_DISPLAY}</span></a>')

def callbtn(label="Call us"):
    """Trades owners call, they do not email. Renders nothing until PHONE is set."""
    if not PHONE:
        return ""
    pretty = f"({PHONE[-10:-7]}) {PHONE[-7:-4]}-{PHONE[-4:]}"
    return f'<a class="cta ghost" href="tel:+{PHONE}">{label} {pretty}</a>'

def actionbar():
    """Phones only. Two thumbs, two jobs: call now, or send the details."""
    return (f'<div class="actionbar">'
            f'<a href="tel:+{PHONE}" aria-label="Call {PHONE_DISPLAY}">{PHONE_ICON}Call</a>'
            f'<a class="primary" href="{cta_href()}">'
            f'{"Book a call" if BOOKED else "Start a project"}</a></div>')


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
    return (
        '<nav class="nav" id="nav"><div class="wrap navin">'
        '<a class="brand" href="/">Yoniverse<span class="bsub">Productions</span></a>'
        '<div class="navlinks">'
        + link("/our-work/", "Work", "work")
        + link("/packages/", "Packages", "packages")
        + link("/contact/", "Contact", "contact", "navsecondary")
        + phonebtn()
        + (f'<a class="navcta" href="{href}" aria-label="{long_label}" '
           f'target="_blank" rel="noopener noreferrer">'
           if BOOKED else f'<a class="navcta" href="{href}" aria-label="{long_label}">')
        + f'<span class="ctalong">{long_label}</span>'
          f'<span class="ctashort">{short_label}</span></a>'
        '</div></div></nav><div class="navspacer"></div>'
    )

def b64(p): return base64.b64encode(pathlib.Path(p).read_bytes()).decode()

def asset(path, mime):
    """Inline as a data URI for the artifact, or copy out and link for the web build."""
    if MODE == "web":
        name = os.path.basename(path)
        shutil.copy(path, os.path.join(OUT, "a", name))
        # root absolute, not relative: /our-work without a trailing slash would
        # otherwise resolve "a/x.mp4" against the site root and 404
        return f"/our-work/a/{name}"
    return f"data:{mime};base64," + b64(path)

# Onest, SIL Open Font License. Soft humanist grotesque, latin subset only.
FONT_CSS = "<style>" + "".join(
    "@font-face{font-family:'Onest';font-style:normal;font-weight:" + str(w) +
    ";font-display:optional;src:url(data:font/woff2;base64," + b64(f"{S}/fonts/onest-{w}.woff2") +
    ") format('woff2');}"
    for w in (400, 600, 700)
) + "</style>"

CSS = """<style>
  :root{
    --ground:#131619; --ground-2:#1A1E23; --panel:#1F242A;
    --line:#2C333B; --line-soft:#232A31;
    --ink:#F2EFE9; --ink-2:#A3AEB8; --ink-3:#8A96A2;
    --orange:#F5822E; --orange-dim:#8C4A1B; --cyan:#3FC7D8;

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
    --s-sec: clamp(56px, 39.11px + 4.444vw, 96px);

    /* Four radii instead of eight, so cards at different sizes still look related */
    /* R4. Sharp, not rounded. 10-14px radii and 100px pills are the app-store
       default; print and film titling are square. 2 to 4px reads as cut, not as a
       component library. --r-pill keeps its name so call sites need not change. */
    --r-sm:2px; --r-md:3px; --r-lg:4px; --r-pill:2px;

    /* Tracking: display tightens, small caps open up. Nothing in between. */
    /* R6. Tracking never past .06em. Letterspacing blown out to .14em is a screen
       era tic; typographers open small caps a little and stop there. */
    --t-display:-.03em; --t-head:-.015em; --t-caps:.055em;

    --mono: ui-monospace,"SF Mono",Menlo,monospace;
    /* A second family, for display and for the performance numbers. One typeface
       across a whole site is the tell; an old-style serif also suits a company that
       sells writing. System stack on purpose: every fallback is a humanist old-style,
       so the character survives where the first choice is missing. */
    --display: "Palatino Linotype", Palatino, "Iowan Old Style", Charter, Georgia, serif;
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
  body{margin:0;padding:0;background:var(--ground);color:var(--ink);
    background-image:
      radial-gradient(circle at 25% 30%, rgba(255,255,255,.016) 0 1px, transparent 1px),
      radial-gradient(circle at 75% 70%, rgba(255,255,255,.012) 0 1px, transparent 1px);
    background-size:9px 9px, 13px 13px;
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
  a{color:var(--orange);}
  a:focus-visible{outline:2px solid var(--orange);outline-offset:3px;border-radius:2px;}

  /* Sticky top bar. Translucent with a blur so the full bleed banner video can
     pass under it and the labels stay readable. It only grows a background and a
     hairline once you have actually scrolled, so it sits invisibly over the hero. */
  .nav{position:fixed;top:0;left:0;right:0;z-index:50;border-bottom:1px solid transparent;
    transition:background var(--ease),border-color var(--ease);}
  .nav.is-stuck{background:rgba(19,22,25,.86);border-bottom-color:var(--line-soft);
    -webkit-backdrop-filter:saturate(160%) blur(14px);backdrop-filter:saturate(160%) blur(14px);}
  .nav.is-stuck::after{content:"";position:absolute;left:0;right:0;bottom:-1px;height:1px;
    background:linear-gradient(90deg,rgba(245,130,46,.55) 0%,rgba(63,199,216,.42) 42%,
      rgba(44,51,59,.55) 78%,rgba(44,51,59,0) 100%);}
  .navin{display:flex;align-items:center;justify-content:space-between;gap:var(--s4);
    height:60px;}
  .brand{display:flex;align-items:baseline;gap:6px;text-decoration:none;color:var(--ink);
    font-weight:700;letter-spacing:var(--t-head);font-size:var(--f-sm);white-space:nowrap;}
  .brand .bsub{color:var(--ink-3);font-weight:600;font-size:var(--f-sm);display:none;}
  @media(min-width:560px){
    .brand{font-size:var(--f-h4);}
    .brand .bsub{display:inline;}
  }
  .navlinks{display:flex;align-items:center;gap:10px;}
  .navsecondary{display:none;}
  @media(min-width:620px){
    .navlinks{gap:var(--s4);}
    .navsecondary{display:inline;}
  }
  @media(min-width:560px){.navlinks{gap:var(--s5);}}
  .navlinks a{font-family:var(--display);font-variant-caps:all-small-caps;letter-spacing:.06em;
    font-size:var(--f-lede);color:var(--ink-2);text-decoration:none;white-space:nowrap;
    transition:color var(--ease);}
  .navlinks a:hover{color:var(--ink);}
  .navlinks a.is-on{color:var(--orange);}
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

  /* the one deliberate entrance above the fold. It runs on the stat cards only,
     never on the hero paragraph, which is the LCP element on most pages. */
  @keyframes heroIn{to{opacity:1;transform:none;}}
  .hero .stat{opacity:0;transform:translateY(12px);
    animation:heroIn .5s cubic-bezier(.16,1,.3,1) forwards;}
  .hero .stat:nth-child(1){animation-delay:.04s;}
  .hero .stat:nth-child(2){animation-delay:.10s;}
  .hero .stat:nth-child(3){animation-delay:.16s;}
  .hero .stat:nth-child(4){animation-delay:.22s;}
  .hero .stat:nth-child(5){animation-delay:.28s;}

  /* (b) count-up needs digits that do not jump width as they change */
  .stat .n,.op .n,.reel .v,.sh .v,.cc-metric b{font-variant-numeric:tabular-nums;}

  /* (d) hero film: a slow push in, transform only, clipped by the wrapper so a
     1.04 scale on a 100vw element cannot create a horizontal scrollbar */
  .bannerwrap{overflow:hidden;width:100vw;max-width:100vw;margin-left:calc(50% - 50vw);}
  .bannerwrap .banner{width:100%;margin-left:0;}
  @keyframes pushIn{from{transform:scale(1);}to{transform:scale(1.04);}}
  .banner.is-playing{animation:pushIn 8s cubic-bezier(.4,0,.2,1) forwards;}

  /* (e) logo marquee */
  .marquee{overflow:hidden;position:relative;
    -webkit-mask-image:linear-gradient(90deg,transparent,#000 8%,#000 92%,transparent);
    mask-image:linear-gradient(90deg,transparent,#000 8%,#000 92%,transparent);}
  .marquee-track{display:flex;width:max-content;gap:var(--s7);align-items:center;
    animation:marq 40s linear infinite;}
  .marquee:hover .marquee-track,.marquee:focus-within .marquee-track{animation-play-state:paused;}
  @keyframes marq{from{transform:translateX(0);}to{transform:translateX(-50%);}}
  .marquee .logomark{width:150px;flex:none;}
  @media(min-width:700px){.marquee .logomark{width:190px;}}

  /* (f) The sticky case header is deliberately not implemented. It was specced to
     orient a reader in a long page, but after the case split these pages run 180 to
     380 words, so a 250px pinned block only ate the viewport and painted over the
     A1 chart. Cut rather than kept as decoration. */

  /* (g) header compaction. The bar is fixed with a spacer holding its place, so
     shrinking it cannot shift the page. */
  .navspacer{height:60px;}
  .nav .brand,.nav .navin{transition:transform var(--ease),height var(--ease);}
  .nav.is-stuck .navin{height:52px;}
  .nav.is-stuck .brand{transform:scale(.92);transform-origin:left center;}

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
    outline:none;border-color:var(--orange);background:var(--panel);}
  .cform input:focus-visible,.cform select:focus-visible,.cform textarea:focus-visible{
    outline:2px solid var(--orange);outline-offset:2px;}
  .cform select{appearance:none;-webkit-appearance:none;cursor:pointer;
    background-image:linear-gradient(45deg,transparent 50%,var(--ink-3) 50%),
      linear-gradient(135deg,var(--ink-3) 50%,transparent 50%);
    background-position:calc(100% - 19px) 21px,calc(100% - 13px) 21px;
    background-size:6px 6px,6px 6px;background-repeat:no-repeat;padding-right:40px;}

  /* Budget as visible radios rather than a dropdown: a buyer who never opens a menu
     never learns the floor is $2,000, and self-selection out is wanted here. */
  .budgets{gap:var(--s3);}
  .budgetrow{display:grid;grid-template-columns:1fr;gap:var(--s2);}
  @media(min-width:560px){.budgetrow{grid-template-columns:repeat(auto-fit,minmax(172px,1fr));}}
  .budgetrow .budget{display:flex;flex-direction:column;gap:2px;cursor:pointer;position:relative;
    background:var(--ground-2);border:1px solid var(--line);border-radius:var(--r-sm);
    padding:13px 13px 14px 38px;min-height:60px;justify-content:center;
    transition:border-color var(--ease),background var(--ease);}
  .budget:hover{border-color:var(--ink-3);}
  .budget input{position:absolute;left:14px;top:50%;transform:translateY(-50%);
    width:18px;height:18px;min-height:0;padding:0;accent-color:var(--orange);cursor:pointer;}
  .budget:has(input:checked){border-color:var(--orange);background:var(--panel);}
  .budget:has(input:focus-visible){outline:2px solid var(--orange);outline-offset:2px;}
  .budget .bv{font-size:var(--f-body);font-weight:650;color:var(--ink);white-space:nowrap;}
  .budget .bt{font-family:var(--mono);font-size:var(--f-micro);color:var(--cyan);
    letter-spacing:.08em;text-transform:uppercase;}

  /* errors appear next to the field they belong to, on blur, never as a summary */
  .ferr{font-size:var(--f-sm);color:#E4574C;min-height:0;display:none;}
  .fld.is-bad .ferr,.budgets.is-bad .ferr{display:block;}
  .fld.is-bad input,.fld.is-bad select,.fld.is-bad textarea{border-color:#E4574C;}

  .hp{position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden;}
  .fsubmit{display:flex;flex-direction:column;gap:var(--s3);align-items:flex-start;}
  .cform button.cta{border:0;cursor:pointer;font-family:inherit;}
  .cform button.cta[disabled]{opacity:.6;cursor:default;}
  .fstatus{margin:0;font-size:var(--f-body);line-height:1.55;display:none;}
  .fstatus.is-err{display:block;color:#E4574C;}
  .fdone{background:var(--ground-2);border:1px solid var(--orange-dim);
    border-radius:var(--r-md);padding:var(--s6) var(--s5);}
  .fdone h3{margin:0 0 var(--s2);font-size:var(--f-h3);font-weight:700;
    letter-spacing:var(--t-head);}
  .fdone p{margin:0;color:var(--ink-2);line-height:1.55;max-width:60ch;}

  /* breadcrumbs, case pages only: these are landable straight from search */
  .crumbs{border-bottom:1px solid var(--line-soft);background:var(--ground);}
  .crumbs .wrap{display:flex;align-items:center;gap:var(--s2);flex-wrap:wrap;
    padding-top:var(--s3);padding-bottom:var(--s3);font-family:var(--mono);
    font-size:var(--f-micro);letter-spacing:.06em;text-transform:uppercase;}
  .crumbs a{color:var(--ink-3);text-decoration:none;}
  .crumbs a:hover{color:var(--ink);}
  .crumbs span[aria-hidden]{color:var(--line);}
  .crumbs [aria-current]{color:var(--ink-2);}

  /* The 128M figure briefly hung -92px into the margin. In a two column grid that
     margin is the image column, so the leading digit sat behind the thumbnail.
     Removed: a device that only works in a single column layout does not belong
     next to an image. */

  /* Sticky action bar, phones only. Trades buyers call, and on a long case page the
     header scrolls away. Sits above the safe area on notched devices. */
  .actionbar{position:fixed;left:0;right:0;bottom:0;z-index:55;display:flex;gap:1px;
    background:var(--line);border-top:1px solid var(--line);
    padding-bottom:env(safe-area-inset-bottom);}
  .actionbar a{flex:1;display:flex;align-items:center;justify-content:center;gap:8px;
    min-height:54px;text-decoration:none;font-size:var(--f-sm);font-weight:650;
    background:var(--ground-2);color:var(--ink);}
  .actionbar a.primary{background:var(--orange);color:#131619;}
  .actionbar a svg{flex:none;}
  @media(min-width:760px){.actionbar{display:none;}}
  @media(max-width:759px){body{padding-bottom:54px;}}

  /* a section that opens without a label, set larger to carry the weight the
     eyebrow used to. Two of seven on the homepage, deliberately not all. */
  .sec-head.bare h2{font-size:clamp(34px,5.6vw,58px);max-width:18ch;}
  .sec-head.bare{gap:var(--s4);}

  /* case study index cards on /our-work/ */
  .ccards{display:grid;grid-template-columns:1fr;gap:var(--s4);}
  @media(min-width:680px){.ccards{grid-template-columns:1fr 1fr;}}
  .ccard{display:flex;flex-direction:column;text-decoration:none;color:inherit;
    background:var(--panel);border:1px solid var(--line);border-radius:var(--r-md);
    overflow:hidden;scroll-margin-top:76px;
    transition:border-color var(--ease),transform var(--ease);}
  .ccard:hover{border-color:var(--orange-dim);transform:translateY(-2px);}
  .cc-art{display:block;position:relative;aspect-ratio:16/9;background:var(--ground-2);
    overflow:hidden;display:flex;align-items:center;justify-content:center;}
  .cc-art img{width:100%;height:100%;object-fit:cover;display:block;}
  /* no still for this client yet, so the mark or the number carries the card */
  .cc-logo{display:flex;align-items:center;justify-content:center;width:62%;}
  .cc-logo img{width:100%;height:auto;object-fit:contain;opacity:.85;}
  .cc-num{font-family:var(--mono);font-size:var(--f-hero);font-weight:700;color:var(--orange);
    letter-spacing:var(--t-display);line-height:1;}
  .cc-body{display:flex;flex-direction:column;gap:var(--s2);padding:var(--s5);}
  .cc-vert{font-family:var(--display);font-variant-caps:all-small-caps;letter-spacing:.06em;
    font-size:var(--f-sm);color:var(--cyan);}
  .cc-name{font-size:var(--f-h3);font-weight:700;letter-spacing:var(--t-head);line-height:1.15;}
  .cc-blurb{font-size:var(--f-body);color:var(--ink-2);line-height:1.5;}
  .cc-metric{font-size:var(--f-sm);color:var(--ink-3);border-top:1px solid var(--line);
    padding-top:var(--s3);margin-top:var(--s1);}
  .cc-metric b{font-family:var(--display);font-size:var(--f-h4);color:var(--orange);
    font-weight:700;margin-right:8px;}
  .cc-go{font-size:var(--f-sm);font-weight:650;color:var(--orange);}

  /* prev / next chain at the foot of each case page */
  .pnrow{display:grid;grid-template-columns:1fr;gap:var(--s3);margin-bottom:var(--s5);}
  @media(min-width:620px){.pnrow{grid-template-columns:1fr 1fr;}}
  .pn{display:flex;flex-direction:column;gap:var(--s1);text-decoration:none;color:inherit;
    background:var(--ground-2);border:1px solid var(--line);border-radius:var(--r-sm);
    padding:var(--s4) var(--s5);transition:border-color var(--ease),background var(--ease);}
  .pn:hover{border-color:var(--cyan);background:var(--panel);}
  .pn.next{text-align:right;}
  .pn.next:only-child{grid-column:2;}
  .pn-l{font-family:var(--mono);font-size:var(--f-micro);letter-spacing:var(--t-caps);
    text-transform:uppercase;color:var(--ink-3);}
  .pn-n{font-size:var(--f-h4);font-weight:650;letter-spacing:var(--t-head);color:var(--ink);}

  /* Tap to call. The number label drops below 900px but the icon and the full
     44px target stay, so the phone never hides behind a breakpoint or a menu. */
  .navphone{display:inline-flex;align-items:center;gap:7px;color:var(--ink-2) !important;
    min-height:44px;padding:0 4px;}
  .navphone:hover{color:var(--ink) !important;}
  .navphone svg{flex:none;}
  .navphone .phnum{display:none;}
  @media(min-width:900px){.navphone .phnum{display:inline;}}

  /* sits under a booking CTA, so nobody has to guess what happens after the click */
  .reassure{margin:var(--s3) 0 0;font-size:var(--f-sm);color:var(--ink-3);max-width:52ch;
    line-height:1.5;}

  .schedwrap{background:var(--ground-2);border:1px solid var(--line);
    border-radius:var(--r-md);overflow:hidden;}
  .schedwrap iframe{display:block;width:100%;}

  /* footer contact row */
  .fcontact{display:flex;flex-wrap:wrap;gap:var(--s2) var(--s5);align-items:center;
    margin-top:var(--s3);}
  .fcontact a{display:inline-flex;align-items:center;gap:7px;min-height:44px;
    font-size:var(--f-body);}

  .navcta{background:var(--orange);color:#131619 !important;border-radius:var(--r-pill);
    padding:0 16px;font-weight:700;transition:filter var(--ease);
    font-family:'Onest',-apple-system,sans-serif;text-transform:none;
    letter-spacing:var(--t-head);font-size:var(--f-sm);
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
  .hero > .wrap{position:relative;z-index:1;}
  .hero h1{font-size:var(--f-hero);margin:var(--s4) 0 0;}
  .hero .sub{margin:var(--s5) 0 0;max-width:58ch;font-size:var(--f-lead);color:var(--ink-2);
    line-height:1.52;}
  .hero .sub strong{color:var(--ink);font-weight:600;}

  /* hairline gaps rather than per-cell borders: an adjacent-sibling rule left a
     stray line on the first item of every wrapped row on a phone */
  .stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(158px,1fr));
    gap:1px;background:var(--line);margin-top:var(--s7);}
  .stat{background:var(--ground);padding:var(--s4) var(--s5) var(--s5);
    display:flex;flex-direction:column;gap:var(--s1);text-decoration:none;color:inherit;
    transition:background var(--ease);}
  .stat:hover{background:var(--ground-2);}
  /* reserve two lines so a wrapped client name does not push its number out of
     line with the rest of the row */
  .stat .case{font-family:var(--display);font-variant-caps:all-small-caps;letter-spacing:.05em;
    font-size:var(--f-sm);color:var(--cyan);line-height:1.3;min-height:2.6em;}
  .stat .n{font-size:var(--f-h3);font-weight:700;letter-spacing:-.012em;color:var(--orange);
    font-family:var(--display);line-height:1.1;}
  .stat .k{font-size:var(--f-micro);letter-spacing:.06em;text-transform:uppercase;color:var(--ink-3);
    font-family:var(--mono);line-height:1.35;min-height:2.7em;}

  section{padding:var(--s-sec) 0;position:relative;scroll-margin-top:76px;}
  /* section breaks get a heavier rule than anything inside a section, so the page
     has a hierarchy of lines rather than one weight repeated 31 times */
  section::before{content:"";position:absolute;top:0;left:0;right:0;height:3px;
    background:linear-gradient(90deg,var(--orange) 0%,var(--orange) 8%,
      rgba(63,199,216,.5) 34%,rgba(44,51,59,.6) 72%,rgba(44,51,59,0) 100%);}
  .sec-head{display:flex;flex-direction:column;gap:var(--s3);margin-bottom:var(--s6);}
  .sec-head h2{font-size:var(--f-h1);}
  .sec-head .lede{margin:0;max-width:62ch;color:var(--ink-2);font-size:var(--f-lede);line-height:1.58;}
  .sec-head .lede strong{color:var(--ink);font-weight:600;}

  .role{display:flex;flex-wrap:wrap;gap:var(--s2);align-items:center;margin-top:var(--s1);}
  .role .lbl{font-family:var(--mono);font-size:var(--f-micro);letter-spacing:var(--t-caps);
    text-transform:uppercase;color:var(--ink-3);margin-right:2px;}
  .pill{border:1px solid var(--orange-dim);background:rgba(245,130,46,.10);color:var(--orange);
    border-radius:var(--r-pill);padding:4px var(--s3);font-size:var(--f-lede);font-weight:400;
    font-family:var(--display);font-variant-caps:all-small-caps;letter-spacing:.05em;}

  .csi{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:var(--s3);
    margin-bottom:var(--s6);}
  .csi div{background:var(--ground-2);border-radius:var(--r-sm);
    padding:var(--s5);}
  .csi h3{margin:0 0 var(--s2);font-family:var(--mono);font-size:var(--f-micro);
    letter-spacing:var(--t-caps);text-transform:uppercase;color:var(--orange);font-weight:600;}
  /* the outcome column carries the secondary hue so results read apart from setup */
  .csi div:nth-child(3) h3{color:var(--cyan);}
  .csi div:nth-child(3){border-color:rgba(63,199,216,.28);}
  .csi p{margin:0;font-size:var(--f-body);color:var(--ink-2);line-height:1.55;}

  .ops{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:var(--s3);
    margin-bottom:var(--s6);}
  .op{background:var(--panel);border-radius:var(--r-sm);
    padding:var(--s4);display:flex;flex-direction:column;gap:var(--s1);}
  .op .n{font-size:var(--f-h3);font-weight:700;letter-spacing:-.012em;color:var(--cyan);
    font-family:var(--display);line-height:1.1;}
  .op .k{font-size:var(--f-micro);letter-spacing:.06em;text-transform:uppercase;color:var(--ink-3);
    font-family:var(--mono);}

  /* hero feature card */
  .feature{display:grid;grid-template-columns:1fr;gap:var(--s6);align-items:center;}
  /* A 9:16 still at .85fr ran 642px tall against a 324px text block, twice its
     height, which read as an image with a caption rather than a figure with an
     argument. Capped so the two columns are close to level. */
  @media(min-width:820px){
    .feature{grid-template-columns:minmax(170px,215px) 1fr;align-items:center;}
    .feature .fstack{max-width:60ch;}
  }
  .feature .shot{position:relative;display:block;border-radius:var(--r-lg);overflow:hidden;
    border:1px solid var(--line);background:#000;}
  /* The source is a YouTube Shorts still: a vertical video pillarboxed into a 16:9
     file with blurred filler either side. Cropping back to 9:16 throws the filler
     away and keeps the actual frame. height:auto is load bearing: without it the
     img's height attribute wins and pins the frame at 640px whatever the column
     does, which is what put the leading digit of 128M behind the image. */
  .feature .shot img{width:100%;height:auto;display:block;aspect-ratio:9/16;object-fit:cover;}
  /* Single column: a 9:16 frame at full width is 600px tall and swallows the
     viewport before the number is reached. Cap it so both land on one screen. */
  .feature .shot{max-width:230px;}
  .feature .play{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;
    background:rgba(10,12,14,.28);transition:background var(--ease);}
  .feature .shot:hover .play{background:rgba(10,12,14,.06);}
  .feature .play span{width:62px;height:62px;border-radius:var(--r-pill);background:rgba(242,239,233,.94);
    display:flex;align-items:center;justify-content:center;color:#131619;font-size:21px;padding-left:5px;}
  .bignum{font-size:var(--f-mega);font-weight:700;letter-spacing:-.045em;color:var(--orange);
    line-height:.88;font-family:var(--display);}
  .feature p{margin:0;color:var(--ink-2);font-size:var(--f-body);line-height:1.6;}
  .feature p strong{color:var(--ink);font-weight:600;}
  .fstack{display:flex;flex-direction:column;gap:var(--s4);}

  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(288px,1fr));gap:var(--s5);}
  .spot{background:var(--panel);border-radius:var(--r-md);
    overflow:hidden;display:flex;flex-direction:column;}
  .spot video{width:100%;display:block;background:#000;aspect-ratio:16/9;object-fit:cover;}
  .spot .meta{padding:var(--s4);display:flex;flex-direction:column;gap:var(--s1);}
  .spot .sc{font-family:var(--display);font-variant-caps:all-small-caps;letter-spacing:.06em;
    font-size:var(--f-sm);color:var(--orange);}
  .spot .nm{font-size:var(--f-h4);font-weight:600;letter-spacing:var(--t-head);}
  .spot .du{font-family:var(--mono);font-size:var(--f-sm);color:var(--ink-3);}

  /* always seven of these, and auto-fill kept orphaning the seventh onto its own
     row. Explicit columns land them as 4+3, then a single clean row of 7. */
  .reels{display:grid;grid-template-columns:repeat(2,1fr);gap:var(--s3);}
  @media(min-width:560px){.reels{grid-template-columns:repeat(4,1fr);}}
  @media(min-width:960px){.reels{grid-template-columns:repeat(7,1fr);}}
  .reel{display:flex;flex-direction:column;gap:var(--s1);text-decoration:none;background:var(--ground-2);
    border:1px solid var(--line);border-radius:var(--r-sm);padding:var(--s4);
    transition:border-color var(--ease),background var(--ease),transform var(--ease);}
  .reel:hover{border-color:var(--cyan);background:var(--panel);transform:translateY(-2px);}
  .reel .v{font-size:var(--f-h3);font-weight:700;letter-spacing:-.012em;color:var(--ink);
    font-family:var(--display);line-height:1.1;}
  .reel.is-top .v{color:var(--orange);}
  .reel .l{font-size:var(--f-micro);letter-spacing:.06em;text-transform:uppercase;color:var(--ink-3);
    font-family:var(--mono);}

  /* six shorts from the same body of work, most viewed first */
  .shorts-head{display:flex;align-items:baseline;justify-content:space-between;gap:var(--s4);
    flex-wrap:wrap;margin:var(--s7) 0 var(--s4);}
  .shorts{display:grid;grid-template-columns:repeat(2,1fr);gap:var(--s3);}
  @media(min-width:560px){.shorts{grid-template-columns:repeat(3,1fr);}}
  @media(min-width:900px){.shorts{grid-template-columns:repeat(6,1fr);}}
  .sh{display:block;text-decoration:none;background:var(--ground-2);border:1px solid var(--line);
    border-radius:var(--r-sm);overflow:hidden;
    transition:border-color var(--ease),background var(--ease),transform var(--ease);}
  .sh:hover{border-color:var(--cyan);background:var(--panel);transform:translateY(-2px);}
  .sh .th{position:relative;display:block;}
  .sh .th img{width:100%;display:block;aspect-ratio:9/16;object-fit:cover;}
  .sh .cap{padding:var(--s3);display:flex;flex-direction:column;gap:var(--s1);}
  .sh .v{font-size:var(--f-h3);font-weight:700;letter-spacing:-.012em;color:var(--ink);
    font-family:var(--display);line-height:1.15;}
  .sh .l{font-size:var(--f-micro);letter-spacing:.06em;text-transform:uppercase;color:var(--ink-3);
    font-family:var(--mono);}

  /* the funnel is a real sequence, so the numbering carries meaning */
  .funnel{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:var(--s3);
    margin-bottom:var(--s6);}
  .step{background:var(--ground-2);border-radius:var(--r-sm);
    padding:var(--s5);display:flex;flex-direction:column;gap:var(--s2);position:relative;}
  .step .sn{font-family:var(--mono);font-size:var(--f-micro);letter-spacing:var(--t-caps);
    color:var(--cyan);}
  .step h3{margin:0;font-size:var(--f-h4);font-weight:650;letter-spacing:var(--t-head);}
  .step p{margin:0;font-size:var(--f-body);color:var(--ink-2);line-height:1.55;}

  .titles{display:grid;grid-template-columns:repeat(auto-fill,minmax(266px,1fr));gap:var(--s3);}
  .tcard{background:var(--ground-2);border:1px solid var(--line);border-radius:var(--r-sm);
    display:flex;flex-direction:column;text-decoration:none;overflow:hidden;
    color:inherit;transition:border-color var(--ease),background var(--ease),transform var(--ease);}
  .tcard:hover{border-color:var(--cyan);background:var(--panel);transform:translateY(-2px);}
  .tcard .tag{font-family:var(--mono);font-size:var(--f-micro);letter-spacing:var(--t-caps);
    text-transform:uppercase;align-self:flex-start;}
  .tcard .tag.tour{color:var(--cyan);}
  .tcard .tag.exp{color:var(--orange);}
  .tcard .tag.lead{color:var(--orange);border:1px solid var(--orange-dim);
    background:rgba(245,130,46,.10);border-radius:var(--r-pill);padding:3px 10px;}
  .tcard .tt{font-size:var(--f-body);font-weight:550;line-height:1.4;letter-spacing:var(--t-head);}
  /* real YouTube thumbnails, pulled from the same video ids these cards link to */
  .titles{grid-template-columns:repeat(auto-fill,minmax(280px,1fr));}
  .tthumb{position:relative;display:block;aspect-ratio:16/9;background:#000;}
  .tthumb img{width:100%;height:100%;object-fit:cover;display:block;}
  .ytplay{position:absolute;left:50%;top:50%;width:46px;height:32px;margin:-16px 0 0 -23px;
    border-radius:8px;background:rgba(15,18,20,.72);transition:background var(--ease);}
  .ytplay::after{content:"";position:absolute;left:18px;top:9px;border-style:solid;
    border-width:7px 0 7px 12px;border-color:transparent transparent transparent #F2EFE9;}
  .tcard:hover .ytplay{background:var(--orange);}
  .tcard:hover .ytplay::after{border-left-color:#131619;}
  .tbody{display:flex;flex-direction:column;gap:var(--s2);padding:var(--s4);}

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
  .band-head{display:flex;flex-direction:column;gap:var(--s2);margin-bottom:var(--s5);}
  .band-head h2{font-size:var(--f-h2);}
  .band-head p{margin:0;color:var(--ink-2);font-size:var(--f-body);max-width:62ch;line-height:1.58;}
  .pkgs{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:var(--s4);}
  .pkg{background:var(--panel);border:1px solid var(--line);border-radius:var(--r-md);
    padding:var(--s6) var(--s5);display:flex;flex-direction:column;gap:var(--s4);position:relative;}
  .pkg.feat{border-color:var(--orange-dim);
    background:linear-gradient(180deg,rgba(245,130,46,.07) 0%,var(--panel) 46%);}
  .pkg .tier{font-family:var(--display);font-variant-caps:all-small-caps;letter-spacing:.06em;
    font-size:var(--f-lede);color:var(--cyan);}
  .pkg.feat .tier{color:var(--orange);}
  .pkg .pname{font-size:var(--f-h4);font-weight:650;letter-spacing:var(--t-head);line-height:1.25;}
  .priceline{display:flex;align-items:baseline;gap:var(--s2);}
  .pkg .price{font-size:var(--f-price);font-weight:700;letter-spacing:-.035em;
    color:var(--orange);font-family:var(--mono);line-height:1;}
  .pkg .per{font-size:var(--f-sm);color:var(--ink-3);}
  .pkg ul{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:var(--s3);}
  .pkg li{font-size:var(--f-body);color:var(--ink-2);padding-left:22px;position:relative;
    line-height:1.5;}
  .pkg li::before{content:"+";position:absolute;left:0;top:0;color:var(--cyan);
    font-family:var(--mono);font-size:var(--f-sm);}
  .pkg.feat li::before{color:var(--orange);}
  .pkg .shoot{font-size:var(--f-sm);color:var(--ink);font-weight:600;
    border-top:1px solid var(--line);padding-top:var(--s3);}
  .pkg .unit{font-size:var(--f-sm);color:var(--cyan);font-family:var(--mono);margin-top:calc(var(--s2) * -1);}
  .pkg.feat .unit{color:var(--orange);}
  .pkg .apply{align-self:flex-start;background:var(--orange);color:#131619;border-radius:var(--r-pill);
    padding:12px var(--s5);font-size:var(--f-body);font-weight:650;text-decoration:none;
    transition:filter var(--ease);}
  .pkg .apply:hover{filter:brightness(1.08);}

  .pkg .perasset{font-family:var(--mono);font-size:var(--f-micro);letter-spacing:.06em;
    text-transform:uppercase;color:var(--ink-3);margin-top:calc(var(--s2) * -1);}
  /* a full width header strip, not a corner tag: the label is a sentence and at
     62% width it wrapped to two lines and collided with the tier name */
  .pkg .best{position:absolute;top:0;left:0;right:0;background:var(--orange);color:#131619;
    font-size:var(--f-micro);font-weight:700;letter-spacing:.08em;text-transform:uppercase;
    padding:8px var(--s4);border-radius:var(--r-md) var(--r-md) 0 0;text-align:center;
    line-height:1.35;}
  .pkg:has(.best){border-color:var(--orange-dim);padding-top:calc(var(--s6) + 20px);}

  /* the constant, stated before the tiers so the tiers are easier to read */
  .always{background:var(--ground-2);border:1px solid var(--line);border-radius:var(--r-md);
    padding:var(--s6) var(--s5);margin-bottom:var(--s8);}
  .always h3{margin:0 0 var(--s2);font-size:var(--f-h4);font-weight:650;letter-spacing:var(--t-head);}
  .always .sub2{margin:0 0 var(--s5);font-size:var(--f-body);color:var(--ink-2);max-width:68ch;
    line-height:1.58;}

  /* the four benefits: numeral led, so the block reads as a designed grid rather
     than four paragraphs in boxes */
  .benefits{display:grid;grid-template-columns:repeat(auto-fit,minmax(228px,1fr));gap:var(--s3);}
  .benefit{background:var(--panel);border-radius:var(--r-sm);
    padding:var(--s5);display:flex;flex-direction:column;gap:var(--s2);}
  .benefit .bn{font-family:var(--mono);font-size:var(--f-h2);font-weight:700;line-height:1;
    color:var(--cyan);letter-spacing:var(--t-display);align-self:flex-start;
    border-bottom:2px solid var(--cyan);padding-bottom:var(--s2);margin-bottom:var(--s1);}
  .benefit h4{margin:0;font-size:var(--f-h4);font-weight:650;letter-spacing:var(--t-head);}
  .benefit p{margin:0;font-size:var(--f-body);color:var(--ink-2);line-height:1.55;}

  /* the two engines, side by side, each with a diagram of how it actually works.
     This was the hardest idea on the page and it used to be one long paragraph. */
  .engines{display:grid;grid-template-columns:1fr;gap:var(--s4);}
  @media(min-width:760px){.engines{grid-template-columns:1fr 1fr;}}
  .engine{background:var(--ground-2);border:1px solid var(--line);border-radius:var(--r-md);
    padding:var(--s5);display:flex;flex-direction:column;gap:var(--s3);}
  .engine.is-two{border-color:rgba(245,130,46,.30);}
  .engine .etag{font-family:var(--mono);font-size:var(--f-micro);letter-spacing:var(--t-caps);
    text-transform:uppercase;color:var(--cyan);}
  .engine.is-two .etag{color:var(--orange);}
  .engine h4{margin:0;font-size:var(--f-h3);font-weight:700;letter-spacing:var(--t-head);}
  .edia{width:100%;height:auto;display:block;margin:var(--s1) 0;}
  .engine p{margin:0;font-size:var(--f-body);color:var(--ink-2);line-height:1.55;}
  .engine .ewhere{font-family:var(--mono);font-size:var(--f-micro);letter-spacing:.06em;
    text-transform:uppercase;color:var(--ink-3);border-top:1px solid var(--line);
    padding-top:var(--s3);margin-top:auto;}
  .engine.is-two .ewhere{color:var(--orange);}

  .steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:var(--s3);}
  .step2{background:var(--panel);border-radius:var(--r-sm);
    padding:var(--s5);}
  .step2 span{font-family:var(--mono);font-size:var(--f-micro);letter-spacing:var(--t-caps);
    text-transform:uppercase;color:var(--cyan);}
  .step2 h4{margin:var(--s2) 0 var(--s1);font-size:var(--f-h4);font-weight:650;
    letter-spacing:var(--t-head);}
  .step2 p{margin:0;font-size:var(--f-body);color:var(--ink-2);line-height:1.55;}

  .incl{background:var(--ground-2);border:1px solid var(--line);border-radius:var(--r-md);
    padding:var(--s6) var(--s5);display:flex;flex-direction:column;gap:var(--s4);}
  .incl h3{margin:0;font-size:var(--f-h4);font-weight:650;letter-spacing:var(--t-head);}
  .incl-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:var(--s5);}
  .incl-grid div p{margin:var(--s1) 0 0;font-size:var(--f-body);color:var(--ink-2);line-height:1.55;}
  .incl-grid div span{font-family:var(--mono);font-size:var(--f-micro);letter-spacing:var(--t-caps);
    text-transform:uppercase;color:var(--cyan);}

  /* full bleed banner video, breaks the wrap to run edge to edge */
  .flush{padding:0;}
  .banner{display:block;width:100vw;max-width:100vw;margin-left:calc(50% - 50vw);
    background:#000;aspect-ratio:16/9;object-fit:cover;}
  .bannercap{padding:var(--s5) 0 var(--s1);display:flex;flex-wrap:wrap;gap:var(--s2) var(--s5);
    align-items:baseline;}
  .bannercap .who{font-size:var(--f-body);color:var(--ink-2);}
  .bannercap .who strong{color:var(--ink);font-weight:600;}

  /* ---------- homepage ---------- */
  /* the two doors off the apex: the work, and the way to buy it */
  .doors{display:grid;grid-template-columns:1fr;gap:var(--s4);}
  @media(min-width:760px){.doors{grid-template-columns:1fr 1fr;}}
  .door{background:var(--panel);border:1px solid var(--line);border-radius:var(--r-md);
    padding:var(--s6) var(--s5);display:flex;flex-direction:column;gap:var(--s2);
    text-decoration:none;color:inherit;
    transition:border-color var(--ease),background var(--ease),transform var(--ease);}
  .door:hover{border-color:var(--orange-dim);background:var(--ground-2);transform:translateY(-2px);}
  .door .tier{font-family:var(--mono);font-size:var(--f-micro);letter-spacing:var(--t-caps);
    text-transform:uppercase;color:var(--cyan);}
  .door h3{margin:0;font-size:var(--f-h2);font-weight:700;letter-spacing:var(--t-head);}
  .door p{margin:0;font-size:var(--f-body);color:var(--ink-2);line-height:1.55;}
  .door .go{margin-top:var(--s2);font-size:var(--f-sm);font-weight:650;color:var(--orange);}

  .cta{display:inline-flex;align-items:center;gap:var(--s2);background:var(--orange);color:#131619;
    border-radius:var(--r-pill);padding:14px var(--s5);font-size:var(--f-body);font-weight:650;
    text-decoration:none;transition:filter var(--ease),transform var(--ease);}
  .cta:hover{filter:brightness(1.08);transform:translateY(-1px);}
  .cta.ghost{background:transparent;color:var(--orange);border:1px solid var(--orange-dim);}
  .ctarow{display:flex;flex-wrap:wrap;gap:var(--s3);align-items:center;margin-top:var(--s6);}
  .ctanote{font-size:var(--f-sm);color:var(--ink-3);}

  .skip{position:absolute;left:-9999px;top:0;background:var(--orange);color:#131619;
    padding:var(--s3) var(--s4);border-radius:0 0 var(--r-sm) 0;z-index:99;font-weight:600;}
  .skip:focus{left:0;}

  footer{padding:var(--s8) 0 var(--s9);position:relative;overflow:hidden;}
  footer::before{content:"";position:absolute;top:0;left:0;right:0;height:1px;z-index:2;
    background:linear-gradient(90deg,rgba(245,130,46,.55) 0%,rgba(63,199,216,.42) 42%,
      rgba(44,51,59,.55) 78%,rgba(44,51,59,0) 100%);}
  footer > .wrap{position:relative;z-index:1;}
  footer .display{font-size:var(--f-h2);margin-bottom:var(--s4);}
  footer p{margin:0;color:var(--ink-2);font-size:var(--f-body);}
</style>"""

SPLAT_JS = """<script>
(function(){
  var list = document.querySelectorAll('canvas.splat');
  if(!list.length) return;
  var COLS = [[245,130,46],[63,199,216]];

  function draw(c){
    if(!c.getContext) return;
    var w = c.clientWidth, h = c.clientHeight;
    if(!w || !h) return;
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    c.width = w * dpr; c.height = h * dpr;
    var x = c.getContext('2d');
    x.setTransform(dpr, 0, 0, dpr, 0, 0);
    x.clearRect(0, 0, w, h);

    /* fixed seed so the splatter is identical on every load */
    var s = 20260814;
    function rnd(){ s = (s * 1664525 + 1013904223) % 4294967296; return s / 4294967296; }

    /* additive blending keeps the hue alive at low opacity on a dark ground.
       Straight alpha at these values goes grey and reads as dirt. */
    x.globalCompositeOperation = 'lighter';

    function blob(cx, cy, r, col, a, stretch, ang){
      x.save();
      x.translate(cx, cy);
      x.rotate(ang);
      x.beginPath();
      var pts = 13, first = true;
      for(var i = 0; i <= pts; i++){
        var t = i / pts * Math.PI * 2;
        var rr = r * (0.84 + rnd() * 0.32);
        var px = Math.cos(t) * rr * stretch, py = Math.sin(t) * rr * 0.86;
        if(first){ x.moveTo(px, py); first = false; } else { x.lineTo(px, py); }
      }
      x.closePath();
      x.fillStyle = 'rgba(' + col[0] + ',' + col[1] + ',' + col[2] + ',' + a + ')';
      x.fill();
      x.restore();
    }

    var base = parseInt(c.getAttribute('data-n'), 10) || 19;
    var n = w < 700 ? Math.max(5, Math.round(base * 0.6)) : base;
    for(var i = 0; i < n; i++){
      var col = COLS[i % 2];
      var cx = rnd() * w, cy = rnd() * h;
      var r = 2.5 + rnd() * rnd() * 11;
      var a = 0.09 + rnd() * 0.06;
      /* every splat is thrown from a direction, so satellites bias down one axis */
      var throwAng = rnd() * Math.PI * 2;

      blob(cx, cy, r, col, a, 1.0 + rnd() * 0.3, throwAng);

      var sats = 12 + Math.floor(rnd() * 18);
      for(var j = 0; j < sats; j++){
        var spread = (rnd() - 0.5) * 1.6;
        var ang = throwAng + spread;
        var dist = r * (1.8 + rnd() * rnd() * 11);
        var fleck = 0.5 + rnd() * rnd() * 2.9;
        blob(cx + Math.cos(ang) * dist, cy + Math.sin(ang) * dist,
             fleck, col, a * (0.65 + rnd() * 0.8), 1.0 + rnd() * 0.5, ang);
      }
    }
  }

  function all(){ for(var i = 0; i < list.length; i++) draw(list[i]); }
  all();
  var t;
  window.addEventListener('resize', function(){
    clearTimeout(t); t = setTimeout(all, 180);
  });
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

  /* The banner plays by itself, but only once it is actually on screen. Loading it
     up front would cost tens of megabytes before the page has said anything. */
  var amb = [].slice.call(document.querySelectorAll('video[data-ambient]'));
  if(!amb.length) return;

  function startOf(v){ return parseFloat(v.getAttribute('data-start') || '0') || 0; }

  function tryPlay(v){
    var p = v.play();
    if(p && p.then){
      p.then(function(){
        v.removeAttribute('controls');
      }).catch(function(){
        /* Autoplay refused, usually iOS low power mode. Surface controls so it is
           still playable by hand, but keep observing: the next time it scrolls back
           into view we try again instead of degrading permanently. */
        v.setAttribute('controls', '');
      });
    }
  }

  /* Seek first, then play. Calling play() before the seek lands means playback
     begins at zero and the seek arrives late, which looks like the start mark
     being ignored. currentTime is only writable once metadata exists. */
  function seekThen(v, to, done){
    if(v.readyState >= 1){
      try { v.currentTime = to; } catch(e){}
      done();
    } else {
      v.addEventListener('loadedmetadata', function(){
        try { v.currentTime = to; } catch(e){}
        done();
      }, {once: true});
    }
  }

  if(!('IntersectionObserver' in window)){
    amb.forEach(function(v){
      v.preload = 'auto';
      var s = startOf(v);
      if(s > 0) seekThen(v, s, function(){ tryPlay(v); }); else tryPlay(v);
    });
    return;
  }

  /* The film opens on a slow establishing shot, so the banner starts at its
     data-start mark and loops back to that mark rather than to zero. The native
     loop attribute cannot do this, which is why it is handled here. */
  amb.forEach(function(v){
    var s = startOf(v);
    v.addEventListener('ended', function(){
      try { v.currentTime = s; } catch(e){}
      tryPlay(v);
    });
  });

  /* Plays on entry, pauses on exit, resumes from the same frame on return.
     pause() preserves currentTime; the only call that resets it is load(), which
     is why that runs once and only on the very first appearance. */
  var io = new IntersectionObserver(function(entries){
    entries.forEach(function(en){
      var v = en.target;
      if(!en.isIntersecting){
        if(!v.paused) v.pause();         /* keeps the position for the return trip */
        return;
      }
      if(v.getAttribute('preload') !== 'auto'){
        v.setAttribute('preload', 'auto');
        v.load();                        /* first sighting only: this one resets to 0 */
        var s = startOf(v);
        if(s > 0){ seekThen(v, s, function(){ tryPlay(v); }); return; }
      }
      tryPlay(v);                        /* every later return: resume in place */
    });
  }, {threshold: 0.2});
  amb.forEach(function(v){ io.observe(v); });
})();
</script>"""


NAV_JS = """<script>
(function(){
  var n = document.getElementById('nav');
  if(!n) return;
  function upd(){ n.classList.toggle('is-stuck', (window.pageYOffset || 0) > 8); }
  upd();
  window.addEventListener('scroll', upd, {passive:true});
})();
</script>"""


MOTION_JS = """<script>
(function(){
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* (a) scroll reveals ---------------------------------------------------- */
  if(!reduce && 'IntersectionObserver' in window){
    var SEL = '.sec-head,.ccard,.benefit,.engine,.pkg,.csi > div,.op,.spot,.reel,.sh,' +
              '.step,.step2,.tcard,.door,.feature,.always,.incl,.pn,.band-head';
    var vh = window.innerHeight || 800;
    var targets = [].slice.call(document.querySelectorAll(SEL)).filter(function(e){
      /* nothing above the fold gets a reveal: that space belongs to the hero
         entrance, and hiding it would sit on the critical render path */
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
        e.style.willChange = 'opacity, transform';
        e.style.transitionDelay = (i * 60) + 'ms';
        e.classList.add('rv-in');
        io.unobserve(e);                                     /* never re-animate */
        setTimeout(function(){ e.style.willChange = 'auto'; }, 700 + i * 60);
      });
    }, {threshold: 0.15, rootMargin: '0px 0px -10% 0px'});
    targets.forEach(function(e){ io.observe(e); });
  }

  /* (b) count up ---------------------------------------------------------- */
  var nums = [].slice.call(document.querySelectorAll('.stat .n, .op .n'));
  if(nums.length && !reduce && 'IntersectionObserver' in window){
    var parse = function(s){
      var m = String(s).match(/^([^0-9.]*)([0-9]+(?:\.[0-9]+)?)(.*)$/);
      return m ? {pre: m[1], val: parseFloat(m[2]), post: m[3], dp: (m[2].split('.')[1]||'').length} : null;
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
          el.textContent = p.pre + (p.val * eased).toFixed(p.dp) + p.post;
          if(k < 1) requestAnimationFrame(step);
          else el.textContent = p.pre + p.val.toFixed(p.dp) + p.post;
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

  /* (d) hero film push in, started only once the banner actually plays ----- */
  [].slice.call(document.querySelectorAll('video[data-ambient]')).forEach(function(v){
    v.addEventListener('playing', function(){ if(!reduce) v.classList.add('is-playing'); });
  });
})();
</script>"""


FORM_JS = """<script>
(function(){
  var f = document.getElementById('cform');
  if(!f) return;
  var btn = document.getElementById('cbtn');
  var status = document.getElementById('fstatus');
  var LABEL = btn.textContent;

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
    fetch('/api/contact', {
      method: 'POST',
      headers: {'content-type': 'application/json'},
      body: JSON.stringify(data)
    }).then(function(r){
      return r.json().then(function(j){ return {ok: r.ok, body: j}; });
    }).then(function(res){
      if(res.ok && res.body.ok){
        /* replace the form rather than clearing it: a blank form after submitting
           reads as "that did not work" and people send it twice */
        var done = document.createElement('div');
        done.className = 'fdone';
        done.setAttribute('tabindex', '-1');
        done.innerHTML = '<h3>Got it, thank you.</h3><p>That is in Yoni&#39;s inbox now. ' +
          'You will hear back within one business day, from a person, ' +
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
      status.className = 'fstatus is-err';
      status.textContent = (res.body && res.body.error) ||
        'Something went wrong at our end. Please email yoni@yoniverseproductions.com directly.';
      btn.disabled = false; btn.textContent = LABEL;
    }).catch(function(){
      status.className = 'fstatus is-err';
      status.textContent = 'That did not send. Please email yoni@yoniverseproductions.com directly.';
      btn.disabled = false; btn.textContent = LABEL;
    });
  });
})();
</script>"""


def spot(fn, sc, nm, du):
    poster = asset(os.path.join(P, fn.replace(".mp4", ".jpg")), "image/jpeg")
    src = asset(os.path.join(V, fn), "video/mp4")
    return (f'<article class="spot">'
            f'<video controls playsinline preload="none" poster="{poster}" '
            f'src="{src}"></video>'
            f'<div class="meta"><span class="sc">{sc}</span><span class="nm">{nm}</span>'
            f'<span class="du">{du}</span></div></article>')

allheart = [("ah1.mp4","01","Breaking Furniture 101","0:30"),("ah4.mp4","02","The Upsell","0:15"),
    ("ah5.mp4","03","The Snake","0:30"),("ah6.mp4","04","Obsessed","0:30"),
    ("ah7.mp4","05","Meet The Carlas","0:30"),("ah8.mp4","06","The Influencer","0:30"),
    ("ah9.mp4","07","The Auctioneer","0:30"),("ah10.mp4","08","Ghosted","0:30"),
    ("ah2.mp4","09","Universe is Talking","0:30"),("ah3.mp4","10","The Quote","0:42")]

handyman = [("hd1.mp4","01","It's Way Hotter","0:30"),
    ("hd2.mp4","02","Don't Worry, You'll Get Used To It","0:30"),
    ("hd3.mp4","03","Sleeping On The Job","0:30"),("hd4.mp4","04","Father Vs AC","0:15"),
    ("hd5.mp4","05","A Space Odyssey","0:56"),("hd6.mp4","06","Where's That Coming From","0:30")]

yt = asset(f"{P}/_yt.jpg", "image/jpeg")

# The banner is a three minute film. Inlining it as base64 would push the artifact
# build past its 16MB ceiling, so that copy shows the frame and the live site plays it.
_bposter = asset(f"{P}/quality1.jpg", "image/jpeg")
if MODE == "web":
    BANNER_MEDIA = (f'<div class="bannerwrap"><video class="banner" data-ambient muted '
                    f'data-start="74" playsinline preload="none" poster="{_bposter}" '
                    f'src="{asset(f"{V}/quality1.mp4", "video/mp4")}"></video></div>')
else:
    BANNER_MEDIA = (f'<div class="bannerwrap"><img class="banner" src="{_bposter}" '
                    f'alt="Quality Heating Cooling Plumbing Electrical website banner film"></div>')

# Sam Halaby shorts, most viewed first. Display figures are rounded from the
# exact view counts in the YouTube player data:
#   27,545,773 / 24,209,643 / 12,386,169 / 9,502,205 / 7,375,746 / 3,132,865
# sam7 and sam8 are new filenames rather than reused ones, so the already
# deployed sam2 and sam6 cannot be served from cache in their place.
sam_shorts = [("DSlESrTFvXE", "sam4.jpg", "27.5M"),
              ("Cr1LTNIsiUk", "sam7.jpg", "24.2M"),
              ("403h7URKz8s", "sam1.jpg", "12.4M"),
              ("imKJBmkcifw", "sam5.jpg", "9.5M"),
              ("vuFJ408hhSA", "sam8.jpg", "7.4M"),
              ("j-TPiHVoGuM", "sam3.jpg", "3.1M")]

def short(vid, thumb, views):
    return (f'<a class="sh" href="https://www.youtube.com/shorts/{vid}">'
            f'<span class="th"><img src="{asset(f"{P}/{thumb}", "image/jpeg")}" '
            f'width="360" height="640" loading="lazy" decoding="async" '
            f'alt="Sam Halaby short, {views} views"></span>'
            f'<span class="cap"><span class="v">{views}</span>'
            f'<span class="l">Views</span></span></a>')

a1 = [("1320266993606759","623K","The attic",1),("1682905312990623","428K","Reel 02",0),
      ("2529519850833764","410K","Reel 03",0),("1515832853025994","312K","Reel 04",0),
      ("1367347965291754","195K","Reel 05",0),("1665126741451677","162K","Reel 06",0),
      ("1718428669171616","134K","Reel 07",0)]

# built once so it can be dropped into any page. The portfolio uses it as a case,
# the pricing page uses it as evidence sitting next to a price.
A1_REELS = "\n".join(
    f'<a class="reel{" is-top" if t else ""}" href="https://www.facebook.com/reel/{i}">'
    f'<span class="v">{v}</span><span class="l">{l}</span></a>' for i, v, l, t in a1
)

CLIENT_LOGOS = [
    ("logo_samhalaby.png",   "Sam Halaby"),
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



# The nine Peretz videos, with their real YouTube thumbnails pulled from the same
# video ids the page already links to. The titles are the strategy on this account,
# so the card leads with the thumbnail and keeps the title verbatim.
PERETZ_TITLES = [
    ("52WDcQztJaM", "lead", "Lead magnet",
     "340 sq ft Los Angeles Garage Conversion + FREE ADU Floor Plan Download"),
    ("h874duk79gg", "exp",  "Explainer", "NEW ADU Laws in 2025 Are a GAMECHANGER"),
    ("p0ke0hdSBHo", "tour", "Tour", "THE ADU FINAL WALKTHROUGH YOU&#39;VE BEEN WAITING FOR"),
    ("LBOZsBnpEvo", "tour", "Tour", "440 sq ft ADU Tour in Culver City"),
    ("XZGJHHBfiRw", "tour", "Tour", "Los Angeles Above Garage ADU Tour, 500 sq ft"),
    ("J8CwbSBXxOg", "tour", "Tour", "ADU 2 Bed 2 Bath 750 sq ft Property Tour"),
    ("NQYrUAl-adI", "tour", "Tour", "340 sq ft Garage Conversion in Culver City"),
    ("Nks3ejFl9Io", "tour", "Tour", "Garage Conversion Inspired by Santorini, Valley Glen"),
    ("ztnHUaPrB8M", "tour", "Tour", "500 sq ft ADU Tour in Thousand Oaks"),
]


def ytcard(vid, tag, taglabel, title):
    thumb = asset(os.path.join(S, "post_yt", vid + ".webp"), "image/webp")
    return (f'<a class="tcard" href="https://www.youtube.com/watch?v={vid}">'
            f'<span class="tthumb"><img src="{thumb}" alt="{title}" width="700" height="394" '
            f'loading="lazy" decoding="async"><span class="ytplay" aria-hidden="true"></span></span>'
            f'<span class="tbody"><span class="tag {tag}">{taglabel}</span>'
            f'<span class="tt">{title}</span></span></a>')

PERETZ_CARDS = "\n".join(ytcard(*x) for x in PERETZ_TITLES)


# A1's reels live on Facebook, which serves no public thumbnail, so the page gets a
# chart of the real view counts instead of invented artwork. The shape is the story:
# one breakout and a tail that still clears 100k.
def a1_chart():
    data = [("623K", 623, 1), ("428K", 428, 0), ("410K", 410, 0), ("312K", 312, 0),
            ("195K", 195, 0), ("162K", 162, 0), ("134K", 134, 0)]
    W, H, PAD, BASE = 700, 224, 18, 176
    bw, gap = 66, 22
    bars, labels = "", ""
    for i, (lab, v, top) in enumerate(data):
        h = round(v / 623 * 132)
        x = PAD + i * (bw + gap)
        y = BASE - h
        col = "#F5822E" if top else "#3FC7D8"
        op = "1" if top else ".55"
        bars += (f'<rect x="{x}" y="{y}" width="{bw}" height="{h}" rx="3" fill="{col}" '
                 f'opacity="{op}"/>')
        labels += (f'<text x="{x + bw/2:.0f}" y="{y - 8}" text-anchor="middle" fill="#F2EFE9" '
                   f'font-size="15" font-family="ui-monospace,Menlo,monospace" '
                   f'font-weight="700">{lab}</text>')
        labels += (f'<text x="{x + bw/2:.0f}" y="{BASE + 20}" text-anchor="middle" fill="#6F7C86" '
                   f'font-size="11" font-family="ui-monospace,Menlo,monospace" '
                   f'letter-spacing="1">{"0" + str(i+1)}</text>')
    # the 100k line the whole tail clears
    ty = BASE - round(100 / 623 * 132)
    lx = PAD + 7 * (bw + gap) - gap + 10          # just past the last bar
    thresh = (f'<line x1="{PAD}" y1="{ty}" x2="{lx - 6}" y2="{ty}" stroke="#F5822E" '
              f'stroke-width="1" stroke-dasharray="4 4" opacity=".5"/>'
              f'<text x="{lx}" y="{ty + 4}" fill="#F5822E" font-size="11" '
              f'font-family="ui-monospace,Menlo,monospace" letter-spacing="1">100K</text>')
    return (f'<svg class="a1chart" viewBox="0 0 {W} {H}" role="img" aria-label="Seven A1 reels by '
            f'view count, from 623,000 down to 134,000, every one of them above 100,000">'
            f'<line x1="{PAD}" y1="{BASE}.5" x2="{lx - 6}" y2="{BASE}.5" stroke="#2C333B" '
            f'stroke-width="1"/>{thresh}{bars}{labels}</svg>')


# ---- the five case studies, each now its own page ------------------------

# Order here is the reading order everywhere: the index, the prev/next chain and
# the homepage stat bar. Home services first, Sam as the closing flex.
CASES = [
    dict(id="a1",       slug="a1-air-conditioning", name="A1 Air Conditioning", og=None,
         vertical="Home services", metric="2.26M", mlabel="Views in a market of one million",
         still=None, logo="logo_a1.png",
         blurb="An ongoing monthly engagement across their entire video distribution: organic "
               "social, paid and brand video.",
         desc="How a Tucson HVAC company with 9,200 followers built seven reels past 100,000 "
              "views, roughly 2.26 million views in a market of one million people."),
    dict(id="peretz", og="og-peretz.jpg",   slug="joseph-peretz", name="Joseph Peretz",
         vertical="Home services", metric="50%", mlabel="Of the company's annual projects",
         still=None, logo=None,
         blurb="Six years on a Los Angeles ADU builder's channel, built to fill a construction "
               "calendar rather than chase reach.",
         desc="Six years and 258 videos on a Los Angeles ADU builder's channel. About half the "
              "company's annual projects now originate there, on builds worth $100,000 to $500,000."),
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
    dict(id="sam", og="og-sam.jpg",      slug="sam-halaby", name="Sam Halaby",
         vertical="Creator", metric="605M", mlabel="Views for one artist",
         still="sam4.jpg", logo="logo_samhalaby.png",
         blurb="Every short-form video for the artist known as The Color Hunter, written and "
               "directed. One of them reached 128 million views.",
         desc="Every short-form video for the artist The Color Hunter: 605 million channel views, "
              "33 videos past a million, and one at 128 million."),
]
CASE_BY_ID = {c["id"]: c for c in CASES}


def case_card(c):
    """One card on the /our-work/ index. Keeps the old anchor id so links to
    /work/joseph-peretz/ from anywhere still land on the right card."""
    name = c["name"]
    if c["still"]:
        src = asset(os.path.join(P, c["still"]), "image/jpeg")
        art = (f'<img src="{src}" alt="{name}" width="640" height="360" '
               f'loading="lazy" decoding="async">')
    elif c["logo"]:
        src = asset(os.path.join(S, "logos", c["logo"]), "image/png")
        art = (f'<span class="cc-logo"><img src="{src}" alt="{name}" width="500" height="200" '
               f'loading="lazy" decoding="async"></span>')
    else:
        art = '<span class="cc-num">' + c["metric"] + '</span>'
    return (f'<a class="ccard" id="{c["id"]}" href="/work/{c["slug"]}/">'
            f'<span class="cc-art">{art}</span>'
            f'<span class="cc-body">'
            f'<span class="cc-vert">{c["vertical"]}</span>'
            f'<span class="cc-name">{c["name"]}</span>'
            f'<span class="cc-blurb">{c["blurb"]}</span>'
            f'<span class="cc-metric"><b>{c["metric"]}</b> {c["mlabel"]}</span>'
            f'<span class="cc-go">Read the case &rarr;</span>'
            f'</span></a>')

CASE_INDEX = "\n".join(case_card(c) for c in CASES)


def case_page(i):
    """A single case study page, with the chain to its neighbours at the foot."""
    c = CASES[i]
    prev_c = CASES[i-1] if i > 0 else None
    next_c = CASES[i+1] if i < len(CASES)-1 else None
    links = ""
    if prev_c:
        links += (f'<a class="pn prev" href="/work/{prev_c["slug"]}/">'
                  f'<span class="pn-l">Previous case</span>'
                  f'<span class="pn-n">{prev_c["name"]}</span></a>')
    if next_c:
        links += (f'<a class="pn next" href="/work/{next_c["slug"]}/">'
                  f'<span class="pn-l">Next case</span>'
                  f'<span class="pn-n">{next_c["name"]}</span></a>')
    crumb_ld = (
        '<script type="application/ld+json">'
        '{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":['
        '{"@type":"ListItem","position":1,"name":"Home",'
        '"item":"https://yoniverseproductions.com/"},'
        '{"@type":"ListItem","position":2,"name":"Work",'
        '"item":"https://yoniverseproductions.com/our-work/"},'
        '{"@type":"ListItem","position":3,"name":"' + c["name"] + '"}]}'
        '</script>')
    crumbs = (f'<nav class="crumbs" aria-label="Breadcrumb"><div class="wrap">'
              f'<a href="/">Home</a><span aria-hidden="true">/</span>'
              f'<a href="/our-work/">Work</a><span aria-hidden="true">/</span>'
              f'<span aria-current="page">{c["name"]}</span>'
              f'</div></nav>')
    return f"""<title>{c["name"]}</title>
{FONT_CSS}
{CSS}
{crumb_ld}
<a class="skip" href="#main">Skip to content</a>
{nav("work")}
{crumbs}
<main id="main">
{CASE_BODY[c["id"]]}
<section><div class="wrap">
  <div class="pnrow">{links}</div>
  <div class="ctarow">
    <a class="cta ghost" href="/our-work/">All five case studies</a>
    {book("Project%20enquiry", "Start a project")}{callbtn()}
  </div>
  {reassure()}
</div></section>
</main>
<footer><canvas class="splat" data-n="8" aria-hidden="true"></canvas><div class="wrap">
  <p class="eyebrow">Contact</p>
  <p class="display">Let&#39;s make something that travels.</p>
  <div class="fcontact">{phonebtn("fphone")}<a href="mailto:{EMAIL}">{EMAIL}</a></div>
  <p style="margin-top:var(--s3);">Los Angeles, CA &nbsp;&middot;&nbsp; Insured &nbsp;&middot;&nbsp; Working since 2019
  &nbsp;&middot;&nbsp; <a href="/our-work/">See the work</a>
  &nbsp;&middot;&nbsp; <a href="/packages/">Packages</a>
  &nbsp;&middot;&nbsp; <a href="/contact/">Contact</a></p>
</div></footer>
{actionbar()}
{SPLAT_JS}
{SOLO_JS}
{NAV_JS}
{MOTION_JS}
"""




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
CASE_BODY["peretz"] = f"""<section id="peretz"><div class="wrap">
  <div class="sec-head casehead">
    <p class="eyebrow">Case 02 &middot; Home services &middot; Conversion</p>
    <h2 class="display">Joseph Peretz</h2>
    <div class="role"><span class="lbl">Our role</span><span class="pill">Content Strategist</span><span class="pill">Producer</span></div>
    <p class="lede">The most commercially valuable channel here is also the smallest. We have spent six
    years on a Los Angeles ADU builder's channel, now 258 videos deep, built to fill a construction
    calendar rather than to chase reach. We run it end to end: strategy, production, publishing and
    performance analysis.</p>
  </div>

  <div class="csi">
    <div><h3>The challenge</h3><p>A general contractor competes for high-value jobs against every other
      builder in Los Angeles, and bought construction leads arrive expensive and cold.</p></div>
    <div><h3>The solution</h3><p>A library built for intent rather than attention. The audience is smaller,
      but it skews heavily toward homeowners researching a build of their own, and the work compounds. These
      videos still bring in leads years after they were posted.</p></div>
    <div><h3>The impact</h3><p>About half of the company's annual projects now originate from the channel, in
      a category where a single build runs from roughly $100,000 for a garage conversion to over
      $500,000.</p></div>
  </div>

  <div class="ops">
    <div class="op"><span class="n">6 yrs</span><span class="k">On the account</span></div>
    <div class="op"><span class="n">258</span><span class="k">Video library</span></div>
    <div class="op"><span class="n">50%</span><span class="k">Of projects sourced</span></div>
  </div>

  <div class="funnel">
    <div class="step"><span class="sn">STEP 01</span><h3>Explain</h3>
      <p>Videos on ADU law reach homeowners still working out whether they are allowed to build at all.</p></div>
    <div class="step"><span class="sn">STEP 02</span><h3>Show</h3>
      <p>Property tours, titled by square footage, type and neighborhood, catch people who already
      know what they want.</p></div>
    <div class="step"><span class="sn">STEP 03</span><h3>Capture</h3>
      <p>A free floor plan download turns a viewer into a named contact.</p></div>
    <div class="step"><span class="sn">STEP 04</span><h3>Book</h3>
      <p>A free consultation turns that contact into a scheduled project.</p></div>
  </div>

  <p class="lede" style="margin:0 0 18px;">The titles are the strategy: square footage, project type
  and neighborhood, written for someone typing exactly that into a search bar.</p>

  <div class="titles">
{PERETZ_CARDS}
  </div>
</div></section>"""
CASE_BODY["handyman"] = f"""<section id="handyman"><div class="wrap">
  <div class="sec-head casehead">
    <p class="eyebrow">Case 03 &middot; Home services &middot; Scale</p>
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
    <p class="eyebrow">Case 04 &middot; Home services &middot; Campaign</p>
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
CASE_BODY["sam"] = f"""<section id="sam"><div class="wrap">
  <div class="sec-head casehead">
    <p class="eyebrow">Case 05 &middot; Creator &middot; Audience</p>
    <h2 class="display">Sam Halaby</h2>
    <div class="role"><span class="lbl">Our role</span><span class="pill">Writer</span><span class="pill">Director</span></div>
    <p class="lede">We write and direct every short-form video for the artist known as The Color Hunter.
    The channel has 170,000 subscribers and <strong>more than 600 million views</strong>, and thirty-three
    of the videos have passed a million on their own.</p>
  </div>

  <div class="ops">
    <div class="op"><span class="n">605M</span><span class="k">Total channel views</span></div>
    <div class="op"><span class="n">33</span><span class="k">Shorts past a million</span></div>
    <div class="op"><span class="n">12</span><span class="k">Shorts past ten million</span></div>
    <div class="op"><span class="n">170K</span><span class="k">Subscribers</span></div>
  </div>

  <div class="feature">
    <a class="shot" href="https://www.youtube.com/shorts/ls_vYanttiI">
      <img src="{yt}" alt="Sam Halaby short, paint on matzah" width="360" height="640"
        loading="lazy" decoding="async">
      <span class="play"><span>&#9654;</span></span>
    </a>
    <div class="fstack">
      <span class="bignum">128M</span>
      <p><strong>Our most viewed and most shared video to date.</strong> 448,000 likes, eleven
      seconds long, and 128 million views on a channel with 170,000 subscribers.</p>
      <p>Cross-platform performance carried the same shape. Reach at this scale is not bought, it is written.
      This is what happens when the premise does the work instead of the spend.</p>
      <p><a href="https://www.youtube.com/shorts/ls_vYanttiI">Watch on YouTube &rarr;</a></p>
    </div>
  </div>

  <div class="shorts-head">
    <p class="eyebrow">Also written and directed</p>
  </div>

  <div class="shorts">
{chr(10).join(short(*s) for s in sam_shorts)}
  </div>
</div></section>"""


def logo_marquee():
    """The client wall as a continuous marquee. The track is duplicated because a
    translateX of -50% only loops seamlessly if the second half repeats the first."""
    marks = "".join(logomark(*c) for c in CLIENT_LOGOS)
    dupe = marks.replace('loading="lazy"', 'loading="lazy" aria-hidden="true"')
    return (f'<div class="marquee"><div class="marquee-track">{marks}{dupe}</div></div>')



html = f"""<title>Selected work, Yoniverse Productions</title>
{FONT_CSS}
{CSS}
<a class="skip" href="#main">Skip to content</a>
{nav("work")}
<div class="hero"><canvas class="splat" data-n="19" aria-hidden="true"></canvas><div class="wrap">
  <p class="eyebrow">Selected work &middot; Yoniverse Productions</p>
  <h1 class="display">Five clients.<br>Five kinds of proof.</h1>
  <p class="sub">From a brand-new account with zero followers to an artist at six hundred million
  views. <strong>The approach does not change.</strong></p>
  <div class="stats">
    <a class="stat" href="#a1"><span class="case">A1 Air Conditioning</span><span class="n">2.26M</span><span class="k">One client, 7 reels</span></a>
    <a class="stat" href="#peretz"><span class="case">Joseph Peretz</span><span class="n">50%</span><span class="k">Of projects sourced</span></a>
    <a class="stat" href="#handyman"><span class="case">Handyman Dan</span><span class="n">12</span><span class="k">Markets deployed</span></a>
    <a class="stat" href="#allheart"><span class="case">All Heart</span><span class="n">10</span><span class="k">Spots delivered</span></a>
    <a class="stat" href="#sam"><span class="case">Sam Halaby</span><span class="n">605M</span><span class="k">Views for one artist</span></a>
  </div>
  <div class="ctarow">
    {book("Project%20enquiry", "Start a project")}{callbtn()}
    <a class="cta ghost" href="/packages/">Monthly packages</a>
  </div>
  {reassure()}
  <p class="ctanote" style="margin-top:16px;max-width:60ch;">Yoniverse Productions is led by founder
  and creative director Yoni Paz, who spent seven years across the creator economy, live streaming
  and social commerce, running portfolios of more than ten thousand creators and one hundred and
  twenty talent agencies before building this company around commercial work.</p>
</div></div>

<main id="main">
<section id="quality" class="flush">
  {BANNER_MEDIA}
  <div class="wrap"><div class="bannercap">
    <p class="eyebrow">Brand film</p>
    <span class="who"><strong>Quality Heating Cooling Plumbing Electrical</strong>, Tulsa.
    Website banner film.</span>
  </div></div>
</section>

<section><div class="wrap">
  <div class="sec-head">
    <p class="eyebrow">Roster</p>
    <h2 class="display">Brands and creators</h2>
    <p class="lede">Writing and production across home services nationwide, plus creator work in art,
    live streaming and social commerce.</p>
  </div>
  {logo_marquee()}
</div></section>

<section><div class="wrap">
  <div class="sec-head">
    <p class="eyebrow">Case studies</p>
    <h2 class="display">Five clients, five kinds of proof</h2>
    <p class="lede">Ordered the way a business owner should read them, so the one closest
    to your problem comes first.</p>
  </div>
  <div class="ccards">
{CASE_INDEX}
  </div>
</div></section>

</main>

<footer><canvas class="splat" data-n="8" aria-hidden="true"></canvas><div class="wrap">
  <p class="eyebrow">Contact</p>
  <p class="display">Let's make something that travels.</p>
  <div class="fcontact">{phonebtn("fphone")}<a href="mailto:{EMAIL}">{EMAIL}</a></div><p style="margin-top:var(--s3);">Los Angeles, CA &nbsp;&middot;&nbsp; Insured &nbsp;&middot;&nbsp; Working since 2019&nbsp;&middot;&nbsp; <a href="/contact/">Contact</a></p>
</div></footer>
{actionbar()}
{SPLAT_JS}
{SOLO_JS}
{NAV_JS}
{MOTION_JS}
"""

# ---- packages page --------------------------------------------------------

# earned at six and twelve months, on both crew packages
MILESTONE = [
    "Six months in: a banner film, team photos and professionally lit interviews with your key people",
    "Twelve months in: your twelfth month is on us",
]

# only the crew tiers get this: it needs a professional on site, which the two
# phone tiers by definition do not have
PHOTOS = ("Professional photos from every shoot, edited and delivered for your "
          "Google Business Profile or carousel posts")


# ---- packages, rendered from data/packages.json --------------------------
# Every price on the site comes from that file. A build assertion below fails if a
# price string ever reappears in a template, which is how the home page and this
# page drifted apart in the first place.
PKG = json.loads(pathlib.Path(f"{S}/data/packages.json").read_text())
TIER = {x["id"]: x for x in PKG["tiers"]}
money = lambda n: "$" + format(n, ",")


def pkg_card(tid):
    c = TIER[tid]
    lis = "".join(f"<li>{b}</li>" for b in c["features"])
    badge = (f'<span class="best">{c["recommendedLabel"]}</span>'
             if c.get("recommended") else "")
    unit = '<div class="unit">By application</div>' if c.get("byApplication") else ""
    apply_btn = (f'<a class="apply" href="{cta_href()}">Ask how to apply</a>'
                 if c.get("byApplication") else "")
    per = (f'<div class="perasset">{c["perAsset"]}</div>' if c.get("perAsset") else "")
    return (f'<div class="pkg{" feat" if c.get("featured") else ""}">'
            f'{badge}<span class="tier">{c["name"]}</span>'
            f'<span class="pname">{c["tagline"]}</span>'
            f'<div class="priceline"><span class="price">{money(c["price"])}</span>'
            f'<span class="per">per month</span></div>'
            + unit + per + f'<ul>{lis}</ul>' + apply_btn
            + f'<div class="shoot">{c["camera"]}</div></div>')


def pkg_group(gid):
    g = next(x for x in PKG["groups"] if x["id"] == gid)
    cards = "".join(pkg_card(t) for t in g["tiers"])
    return (f'<div class="band"><div class="band-head">'
            f'<h2 class="display">{g["heading"]}</h2><p>{g["subhead"]}</p></div>'
            f'<div class="pkgs">{cards}</div></div>')


def price_ladder():
    """The home page strip. Same source, so it cannot disagree with the tiers."""
    return "".join(
        f'<div class="op"><span class="n">{money(c["price"])}</span>'
        f'<span class="k">{c["name"]} &middot; {c["tagline"]}</span></div>'
        for c in PKG["tiers"])


def pkg(tier, name, price, unit, bullets, shooter, feat=False,
        apply_href="", apply_label=""):
    lis = "".join(f"<li>{b}</li>" for b in bullets)
    return (f'<div class="pkg{" feat" if feat else ""}">'
            + f'<span class="tier">{tier}</span>'
            f'<span class="pname">{name}</span>'
            f'<div class="priceline"><span class="price">{price}</span>'
            f'<span class="per">per month</span></div>'
            + (f'<div class="unit">{unit}</div>' if unit else "")
            + f'<ul>{lis}</ul>'
            + (f'<a class="apply" href="{apply_href}">{apply_label}</a>' if apply_href else "")
            + f'<div class="shoot">{shooter}</div></div>')

# Two small diagrams for the packages page. The first is breadth: a lot of posts,
# familiarity rising slowly across all of them. The second is depth: fewer people,
# each one further along, narrowing to a booked job.
ENGINE_SHORT = ('<svg class="edia" viewBox="0 0 300 92" role="img" aria-label="Many small posts over time, with familiarity rising slowly across them"><line x1="6" y1="82.5" x2="294" y2="82.5" stroke="#2C333B" stroke-width="1"/><rect x="8.0" y="72" width="6" height="10" rx="1.5" fill="#3FC7D8" opacity=".42"/><rect x="20.5" y="66" width="6" height="16" rx="1.5" fill="#3FC7D8" opacity=".42"/><rect x="33.0" y="73" width="6" height="9" rx="1.5" fill="#3FC7D8" opacity=".42"/><rect x="45.5" y="61" width="6" height="21" rx="1.5" fill="#3FC7D8" opacity=".42"/><rect x="58.0" y="69" width="6" height="13" rx="1.5" fill="#3FC7D8" opacity=".42"/><rect x="70.5" y="75" width="6" height="7" rx="1.5" fill="#3FC7D8" opacity=".42"/><rect x="83.0" y="64" width="6" height="18" rx="1.5" fill="#3FC7D8" opacity=".42"/><rect x="95.5" y="70" width="6" height="12" rx="1.5" fill="#3FC7D8" opacity=".42"/><rect x="108.0" y="58" width="6" height="24" rx="1.5" fill="#3FC7D8" opacity=".42"/><rect x="120.5" y="72" width="6" height="10" rx="1.5" fill="#3FC7D8" opacity=".42"/><rect x="133.0" y="67" width="6" height="15" rx="1.5" fill="#3FC7D8" opacity=".42"/><rect x="145.5" y="63" width="6" height="19" rx="1.5" fill="#3FC7D8" opacity=".42"/><rect x="158.0" y="73" width="6" height="9" rx="1.5" fill="#3FC7D8" opacity=".42"/><rect x="170.5" y="60" width="6" height="22" rx="1.5" fill="#3FC7D8" opacity=".42"/><rect x="183.0" y="69" width="6" height="13" rx="1.5" fill="#3FC7D8" opacity=".42"/><rect x="195.5" y="66" width="6" height="16" rx="1.5" fill="#3FC7D8" opacity=".42"/><rect x="208.0" y="72" width="6" height="10" rx="1.5" fill="#3FC7D8" opacity=".42"/><rect x="220.5" y="61" width="6" height="21" rx="1.5" fill="#3FC7D8" opacity=".42"/><rect x="233.0" y="67" width="6" height="15" rx="1.5" fill="#3FC7D8" opacity=".42"/><rect x="245.5" y="73" width="6" height="9" rx="1.5" fill="#3FC7D8" opacity=".42"/><rect x="258.0" y="64" width="6" height="18" rx="1.5" fill="#3FC7D8" opacity=".42"/><rect x="270.5" y="70" width="6" height="12" rx="1.5" fill="#3FC7D8" opacity=".42"/><rect x="283.0" y="63" width="6" height="19" rx="1.5" fill="#3FC7D8" opacity=".42"/><path d="M8,76 C90,72 156,56 292,14" fill="none" stroke="#F5822E" stroke-width="2.5" stroke-linecap="round"/></svg>')

ENGINE_LONG = ('<svg class="edia" viewBox="0 0 300 92" role="img" aria-label="A narrowing funnel, from people searching down to a booked job"><rect x="28" y="8" width="244" height="14" rx="3" fill="#3FC7D8" opacity=".26"/><rect x="62" y="30" width="176" height="14" rx="3" fill="#3FC7D8" opacity=".40"/><rect x="96" y="52" width="108" height="14" rx="3" fill="#3FC7D8" opacity=".58"/><rect x="124" y="74" width="52" height="14" rx="3" fill="#F5822E" opacity="1"/></svg>')

PACKAGES_HTML = f"""<title>Monthly content packages</title>
{FONT_CSS}
{CSS}
<a class="skip" href="#main">Skip to content</a>
{nav("packages")}

<div class="hero"><canvas class="splat" data-n="14" aria-hidden="true"></canvas><div class="wrap">
  <p class="eyebrow">Monthly packages &middot; Yoniverse Productions</p>
  <h1 class="display">Known and trusted before they need you.</h1>
  <p class="sub">Nobody calls a home service company because they saw one good video. They call the
  company they already recognize, and that recognition is built over months, not in a month.
  <strong>This is a long play, and it only works if it actually runs.</strong> These packages exist
  to make it run without landing on your desk.</p>
  <div class="ctarow">
    {book("Monthly%20packages")}{callbtn()}
    <a class="cta ghost" href="/our-work/">See the work first</a>
  </div>
  {reassure()}
</div></div>

<main id="main">
<section><div class="wrap">

  <div class="always">
    <h3>What you are actually buying</h3>
    <p class="sub2">Not leads. Anyone selling you leads from organic short form is guessing.
    Consistent short form reliably does four things, and all four compound.</p>
    <div class="benefits">
      <div class="benefit"><span class="bn">01</span><h4>Recognition</h4>
        <p>Whatever finally puts someone in the market, a breakdown, a move, a remodel they have
        been putting off, they reach for the name they already know. Being that name takes months
        of showing up in the same feeds.</p></div>
      <div class="benefit"><span class="bn">02</span><h4>Recruiting</h4>
        <p>Good people are harder to find than customers. They apply to the company that looks
        like somewhere worth working, and they decide that from your feed long before they ever
        send a resume.</p></div>
      <div class="benefit"><span class="bn">03</span><h4>Trust at the door</h4>
        <p>Someone who has already watched your team work is a different conversation from someone
        meeting you for the first time. You start past the part where they size you up.</p></div>
      <div class="benefit"><span class="bn">04</span><h4>Proof you are still around</h4>
        <p>Everyone looks you up before they call. A feed with two years behind it reads as a
        company that is busy and still here. A feed that stopped in 2023 reads as the opposite,
        and they will notice which one you are.</p></div>
    </div>
  </div>

  <div class="band">
    <div class="band-head">
      <p class="eyebrow">Two engines</p>
      <h2 class="display">Two different ways this works</h2>
      <p>Every package below is built on the first one. The second works the other way around,
      and it is the only real difference between the mid tiers and the Studio tiers.</p>
    </div>
    <div class="engines">
      <div class="engine">
        <span class="etag">Engine 01 &middot; Short form</span>
        <h4>Attention</h4>
        {ENGINE_SHORT}
        <p>Aimed at someone scrolling past who was not looking for you. Each post does little on
        its own. Together, across months, they build the four things above. Genuinely not
        attributable to leads, which is why we do not sell it that way.</p>
        <span class="ewhere">Included in every package</span>
      </div>
      <div class="engine is-two">
        <span class="etag">Engine 02 &middot; Long form</span>
        <h4>Intent</h4>
        {ENGINE_LONG}
        <p>Made for intent rather than attention, aimed at someone already searching for what you
        sell. Fewer people, each one further along. Slower to start, it does produce trackable
        inbound, and <strong>unlike short form it does not expire</strong>: one client&#39;s channel
        is six years deep and still booking work from videos posted at the beginning.</p>
        <span class="ewhere">Studio and Studio Max only</span>
      </div>
    </div>
  </div>

  <div class="always">
    <h3>The same three things happen at every tier</h3>
    <p class="sub2">The only real difference between the packages is who holds the camera and how
    much goes out. Everything here is included whether you spend $2,000 or $15,000.</p>
    <div class="steps">
      <div class="step2"><span>Step 01</span><h4>Planned</h4>
        <p>Our team works out what your content needs to do, then sends you a shot list before
        anyone films anything.</p></div>
      <div class="step2"><span>Step 02</span><h4>Captured</h4>
        <p>Either your team shoots to that list, or our crew comes out and shoots it for you.</p></div>
      <div class="step2"><span>Step 03</span><h4>Cut and posted</h4>
        <p>Edited, captioned and published to your channels. Not handed back to you as files.</p></div>
    </div>
  </div>

  {pkg_group("you-shoot")}

  <div class="band">
    <div class="band-head">
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
    <div class="ops" style="margin-top:22px;">
      <div class="op"><span class="n">50%</span><span class="k">Of one client&#39;s annual projects</span></div>
      <div class="op"><span class="n">6 yrs</span><span class="k">That account has run</span></div>
      <div class="op"><span class="n">258</span><span class="k">Videos in their library</span></div>
      <div class="op"><span class="n">$100K+</span><span class="k">Value of one job it sources</span></div>
    </div>
    <p class="ctanote" style="margin-top:14px;">A Los Angeles ADU builder, six years in on what is
    now the Studio Max shape: weekly long form built around what people actually search, plus regular
    posting everywhere else. About half of the company&#39;s annual projects now start on that
    channel, in a category where a single build runs from roughly $100,000 to over $500,000.
    <a href="/work/joseph-peretz/">Read that case</a>.</p>
  </div>

  {pkg_group("we-shoot")}

  {pkg_group("studio")}

  <div class="band">
    <div class="band-head">
      <p class="eyebrow">Who we do this for</p>
      <h2 class="display">Brands and creators</h2>
      <p>Home services nationwide, plus creator work in art, live streaming and social commerce.
      <a href="/our-work/">See the work</a>.</p>
    </div>
    {logo_marquee()}
  </div>

  <div class="incl">
    <h3>Terms</h3>
    <div class="incl-grid">
      <div><span>Starting and stopping</span><p>There is no setup fee. When you want out, we ask
        for 30 days notice and one final payment, so the shortest a package runs is two months.
        You keep every frame we shot and everything we posted, permanently.</p></div>
      <div><span>Commitment</span><p>Every package runs month to month. Commit to twelve months
        and the twelfth is free, so you pay for eleven. Studio Max is the one you apply for, because
        capacity is limited.</p></div>
      <div><span>Insurance</span><p>We are insured. If your office needs paperwork on file
        before a crew is on your property or a job site, ask and we will send it over.</p></div>
      <div><span>Who owns it</span><p>You do. Every frame we shoot for you is yours to keep and
        use however you like, permanently.</p></div>
      <div><span>Where it goes</span><p>YouTube, Instagram, TikTok, Facebook and LinkedIn. Anywhere else
        you want to be, just say so.</p></div>
      <div><span>When it starts</span><p>On current scheduling your first production day lands
        three to four weeks after your initial payment clears. Posting begins once that footage is
        cut, so the first month is a build month by design.</p></div>
      <div><span>Revisions</span><p>One round on anything you want changed. Everything is cut to
        make you look good on camera in the first place.</p></div>
      <div><span>Billing</span><p>The first month holds your start date. Nothing else is due until
        the day your first post goes live, and that day sets your monthly cycle.</p></div>
    </div>
  </div>

  <div class="ctarow">
    {book("Monthly%20packages")}{callbtn()}
  </div>
  {reassure()}
  <p class="ctanote" style="margin-top:var(--s3);">Questions on terms? Call
  <a href="tel:+{PHONE}">{PHONE_DISPLAY}</a>.</p>

</div></section>
</main>

<footer><canvas class="splat" data-n="8" aria-hidden="true"></canvas><div class="wrap">
  <p class="eyebrow">Contact</p>
  <p class="display">Let&#39;s make something that travels.</p>
  <div class="fcontact">{phonebtn("fphone")}<a href="mailto:{EMAIL}">{EMAIL}</a></div><p style="margin-top:var(--s3);">Los Angeles, CA &nbsp;&middot;&nbsp; Insured &nbsp;&middot;&nbsp; Working since 2019
  &nbsp;&middot;&nbsp; <a href="/our-work/">See the work</a>&nbsp;&middot;&nbsp; <a href="/contact/">Contact</a></p>
</div></footer>
{actionbar()}
{SPLAT_JS}
{NAV_JS}
{MOTION_JS}
{FORM_JS}
"""


# ---- homepage, the apex domain -------------------------------------------

# The apex speaks as the company. /our-work is Yoni's personal credit list and
# /packages is the retainer menu, so this page routes to both rather than
# repeating either. Every asset here is one the other pages already copied out,
# so the homepage adds markup and no new weight.

# three spots that carry the range: two premises from All Heart, one from Handyman Dan
HOME_SPOTS = [("ah1.mp4", "All Heart", "Breaking Furniture 101", "0:30"),
              ("ah5.mp4", "All Heart", "The Snake", "0:30"),
              ("hd5.mp4", "Handyman Dan", "A Space Odyssey", "0:56")]

HOME_HTML = f"""<title>Yoniverse Productions</title>
{FONT_CSS}
{CSS}
<a class="skip" href="#main">Skip to content</a>
{nav("home")}

<div class="hero"><canvas class="splat" data-n="19" aria-hidden="true"></canvas><div class="wrap">
  <p class="eyebrow">Yoniverse Productions &middot; Los Angeles</p>
  <h1 class="display">A video that makes you feel nothing does nothing.</h1>
  <p class="sub">We write, shoot, cut and post short-form and commercial video for home service
  brands, builders, realtors and creators. One good video will not do it, and neither will the
  leads nobody can honestly promise you. It takes <strong>video worth watching, often enough to
  stay in mind</strong> until the day they need you.</p>
  <div class="stats">
    <a class="stat" href="/work/joseph-peretz/"><span class="case">Joseph Peretz</span><span class="n">50%</span><span class="k">Of projects sourced</span></a>
    <a class="stat" href="/work/a1-air-conditioning/"><span class="case">A1 Air Conditioning</span><span class="n">2.26M</span><span class="k">One client, 7 reels</span></a>
    <a class="stat" href="/work/handyman-dan/"><span class="case">Handyman Dan</span><span class="n">12</span><span class="k">Markets deployed</span></a>
    <a class="stat" href="#roster"><span class="case">Roster</span><span class="n">16</span><span class="k">Brands and creators</span></a>
    <a class="stat" href="/work/sam-halaby/"><span class="case">Sam Halaby</span><span class="n">605M</span><span class="k">Views for one artist</span></a>
  </div>
  <div class="ctarow">
    <a class="cta" href="/packages/">See the packages</a>
    <a class="cta ghost" href="/our-work/">See the work first</a>
  </div>
  <p class="ctanote" style="margin-top:16px;max-width:60ch;">Los Angeles. Led by founder and
  creative director Yoni Paz.</p>
</div></div>

<main id="main">

<section class="flush">
  {BANNER_MEDIA}
  <div class="wrap"><div class="bannercap">
    <p class="eyebrow">Brand film</p>
    <span class="who"><strong>Quality Heating Cooling Plumbing Electrical</strong>, Tulsa.
    Website banner film.</span>
  </div></div>
</section>

<section><div class="wrap">
  <div class="sec-head">
    <p class="eyebrow">What we do</p>
    <h2 class="display">Three ways we work</h2>
    <p class="lede">All of it starts the same way, with a premise worth repeating. The difference is
    how much of the year it has to cover.</p>
  </div>
  <div class="csi">
    <div><h3>Campaigns</h3><p>One premise strong enough to carry a whole package, shot in a single
      production block so the cost lands once and the inventory lasts a year.</p></div>
    <div><h3>Monthly programs</h3><p>Planned, filmed, edited and published every month, on a schedule
      that does not depend on anyone at your company remembering to film.</p></div>
    <div><h3>Creator work</h3><p>Short form built for reach, for artists and channels where the
      audience is the business. We write the premise so it travels far past the size of the account
      that posts it.</p></div>
  </div>
</div></section>

<section><div class="wrap">
  <div class="sec-head">
    <p class="eyebrow">Selected work &middot; Home services</p>
    <h2 class="display">The premise doing the work</h2>
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
    <a class="cta ghost" href="/our-work/">All five case studies &rarr;</a>
    <span class="ctanote">A1 Air Conditioning, Joseph Peretz, Handyman Dan, All Heart, Sam Halaby.</span>
  </div>
</div></section>

<section><div class="wrap">
  <div class="sec-head bare">
    <h2 class="display">And when the job is pure reach</h2>
    <p class="lede">Different job, different measure. A creator is not trying to be remembered
    later, they are trying to be watched now, by people who have never heard of them.
    <strong>Nothing gets a video watched by strangers except the premise</strong>, which is the
    part we are actually hired for.</p>
  </div>

  <div class="feature">
    <a class="shot" href="https://www.youtube.com/shorts/ls_vYanttiI">
      <img src="{yt}" alt="Sam Halaby short, paint on matzah" width="360" height="640"
        loading="lazy" decoding="async">
      <span class="play"><span>&#9654;</span></span>
    </a>
    <div class="fstack">
      <span class="bignum">128M</span>
      <p><strong>Our most viewed and most shared video to date.</strong> 448,000 likes, eleven
      seconds long, and 128 million views on a channel with 170,000 subscribers.</p>
      <p>Written and directed for the artist Sam Halaby, whose channel has passed 605 million
      views with thirty-three videos over a million on their own. Reach at this scale is not
      bought, it is written, and nothing about that video cost more than the ones around it.</p>
      <p><a href="/work/sam-halaby/">See the creator case &rarr;</a></p>
    </div>
  </div>

  <div class="ctarow">
    {book("Creator%20project", "Talk about creator work", "cta ghost")}
    <span class="ctanote">Creator work is quoted per project, not on the monthly packages.</span>
  </div>
  {reassure()}
</div></section>

<section><div class="wrap">
  <div class="sec-head">
    <p class="eyebrow">Monthly packages</p>
    <h2 class="display">Known and trusted before they need you.</h2>
    <p class="lede">Nobody calls a home service company because they saw one good video. They call
    the company they already recognize, and <strong>that recognition is built over months, not in a
    month</strong>. There are six monthly programs, from your team holding the phone to a
    four-person crew on set twice a month. Planning, editing and posting are included at every
    tier, and the top two add long form built for intent rather than attention.</p>
  </div>
  <div class="ops">{price_ladder()}</div>
  <div class="ctarow">
    <a class="cta" href="/packages/">Compare the packages</a>
    <span class="ctanote">Month to month. Commit to twelve and the twelfth is free.</span>
  </div>
</div></section>

<section id="roster"><div class="wrap">
  <div class="sec-head bare">
    <h2 class="display">Brands and creators</h2>
    <p class="lede">Writing and production across home services nationwide, plus creator work in art,
    live streaming and social commerce.</p>
  </div>
  {logo_marquee()}
</div></section>

<section><div class="wrap">
  <div class="doors">
    <a class="door" href="/our-work/">
      <span class="tier">Portfolio</span>
      <h3>See the work</h3>
      <p>Five case studies with the numbers attached, the spots playable in full, and the reasoning
      behind each one.</p>
      <span class="go">Open the portfolio &rarr;</span>
    </a>
    <a class="door" href="/packages/">
      <span class="tier">Retainers</span>
      <h3>Hire us monthly</h3>
      <p>Six programs, plain terms, and an honest account of what consistent content does and
      does not do.</p>
      <span class="go">See the packages &rarr;</span>
    </a>
  </div>
</div></section>

</main>

<footer><canvas class="splat" data-n="8" aria-hidden="true"></canvas><div class="wrap">
  <p class="eyebrow">Contact</p>
  <p class="display">Let&#39;s make something that travels.</p>
  <div class="fcontact">{phonebtn("fphone")}<a href="mailto:{EMAIL}">{EMAIL}</a></div><p style="margin-top:var(--s3);">Los Angeles, CA &nbsp;&middot;&nbsp; Insured &nbsp;&middot;&nbsp; Working since 2019
  &nbsp;&middot;&nbsp; <a href="/our-work/">See the work</a> &nbsp;&middot;&nbsp; <a href="/packages/">Packages</a>&nbsp;&middot;&nbsp; <a href="/contact/">Contact</a></p>
</div></footer>
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
# twelve of the sixteen logos on the wall are HVAC, plumbing or electrical.
TRADE_GROUPS = [
    ("Home services", ["HVAC", "Plumbing", "Electrical", "Roofing", "Garage doors",
                       "More than one of these", "Another home service"]),
    ("Property and building", ["Remodeling, ADU or new build",
                               "Real estate agent or brokerage"]),
    ("Something else", ["Creator, artist or channel"]),
]
TRADES = [x for _, opts in TRADE_GROUPS for x in opts]

# Shown as visible radios, not a dropdown, on purpose. A buyer who never opens the
# menu never learns the floor is $2,000, and self-selection out is a feature here.
BUDGETS = [("$2,000 to $3,000", "Bronze and Silver"),
           ("$4,000 to $5,000", "Gold and Platinum"),
           ("$10,000 to $15,000", "Studio and Studio Max"), ("Not sure yet", "")]


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
    return f"""<form class="cform" id="cform" method="post" action="/api/contact" novalidate>
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
    <button type="submit" class="cta" id="cbtn">Send to Yoniverse</button>
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
        'Yoniverse Productions" loading="lazy" style="border:0" width="100%" height="640" '
        'frameborder="0"></iframe></div>'
        '</div></section>')
else:
    SCHEDULER_SECTION = ""




CONTACT_HTML = f"""<title>Contact</title>
{FONT_CSS}
{CSS}
<a class="skip" href="#main">Skip to content</a>
{nav("contact")}

<div class="hero"><canvas class="splat" data-n="12" aria-hidden="true"></canvas><div class="wrap">
  <p class="eyebrow">Contact &middot; Yoniverse Productions</p>
  <h1 class="display">Talk to us.</h1>
  <p class="sub">Tell us your city and your trade and we will come back with something specific
  to your market, not a brochure. If you would rather look first, the work is on the
  <a href="/our-work/">case studies</a> and the monthly programs are
  <a href="/packages/">priced in public</a>.</p>
  <div class="ctarow">
    <a class="cta" href="#start">Send us a message</a>{callbtn()}
  </div>
  {reassure()}
</div></div>

<main id="main">
<section><div class="wrap">
  <div class="sec-head">
    <p class="eyebrow">Three ways</p>
    <h2 class="display">However you prefer to do it</h2>
  </div>
  <div class="benefits">
    <div class="benefit"><span class="bn">01</span><h4>Call</h4>
      <p>Straight through to us, no switchboard.
      <a href="tel:+{PHONE}">{PHONE_DISPLAY}</a></p></div>
    <div class="benefit"><span class="bn">02</span><h4>Email</h4>
      <p>Good for scope, budgets and anything with attachments.
      <a href="mailto:{EMAIL}">{EMAIL}</a></p></div>
    <div class="benefit"><span class="bn">03</span><h4>The form</h4>
      <p>Best if you want the first reply to already be about your city and your trade.
      It is <a href="#start">right below</a>.</p></div>
  </div>
</div></section>

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
      <div><span>Response time</span><p>We answer email within one business day. If you call
        during business hours in Los Angeles and we cannot pick up, we call back the same
        day.</p></div>
      <div><span>Where we are</span><p>Los Angeles, CA. We shoot nationwide, and most of our
        home service clients are outside California.</p></div>
      <div><span>What to bring</span><p>Nothing prepared. Your market, roughly what you are
        posting now, and what you want more of next year is enough to work with.</p></div>
    </div>
  </div>
</div></section>
</main>

<footer><canvas class="splat" data-n="8" aria-hidden="true"></canvas><div class="wrap">
  <p class="eyebrow">Contact</p>
  <p class="display">Let&#39;s make something that travels.</p>
  <div class="fcontact">{phonebtn("fphone")}<a href="mailto:{EMAIL}">{EMAIL}</a></div>
  <p style="margin-top:var(--s3);">Los Angeles, CA &nbsp;&middot;&nbsp; Insured &nbsp;&middot;&nbsp; Working since 2019
  &nbsp;&middot;&nbsp; <a href="/our-work/">See the work</a>
  &nbsp;&middot;&nbsp; <a href="/packages/">Packages</a>&nbsp;&middot;&nbsp; <a href="/contact/">Contact</a></p>
</div></footer>
{actionbar()}
{SPLAT_JS}
{NAV_JS}
{MOTION_JS}
{FORM_JS}
"""


# ---- shared post processing, used by every page --------------------------

FAVICON = ('data:image/svg+xml,'
           '%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22%3E'
           '%3Ctext y=%22.9em%22 font-size=%2290%22%3E%F0%9F%94%A6%3C/text%3E%3C/svg%3E')


# 3.3 Structured data. One block, identical on every page, so search engines get a
# single consistent record of who this is and how to reach them.
JSON_LD = (
    '<script type="application/ld+json">'
    '{"@context":"https://schema.org","@type":"ProfessionalService",'
    '"name":"Yoniverse Productions","url":"https://yoniverseproductions.com/",'
    '"telephone":"+1-310-595-4519","email":"yoni@yoniverseproductions.com",'
    '"address":{"@type":"PostalAddress","addressLocality":"Los Angeles",'
    '"addressRegion":"CA","addressCountry":"US"},'
    '"areaServed":"US","founder":{"@type":"Person","name":"Yoni Paz"},'
    '"description":"Video production for home service brands and creators."}'
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


def write_web(page, path, *, title, desc, og_image, url):
    """Vercel serves the raw file, so each page supplies its own document shell."""
    page = re.sub(r'^\s*<title>[^<]*</title>\s*', '', page)   # head owns the title here
    doc = (
        '<!doctype html>\n<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        f'<title>{title}</title>\n'
        f'<meta name="description" content="{desc}">\n'
        '<meta property="og:type" content="website">\n'
        f'<meta property="og:title" content="{title}">\n'
        f'<meta property="og:description" content="{desc}">\n'
        f'<meta property="og:image" content="{og_image}">\n'
        f'<meta property="og:url" content="{url}">\n'
        '<meta property="og:site_name" content="Yoniverse Productions">\n'
        f'<link rel="canonical" href="{url}">\n'
        '<meta name="theme-color" content="#131619">\n'
        '<meta name="twitter:card" content="summary_large_image">\n'
        f'<link rel="icon" href="{FAVICON}">\n'
        + JSON_LD + '\n'
        '</head>\n<body>\n' + page + '\n</body>\n</html>\n'
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
    SITE = "https://yoniverseproductions.com"
    D1 = ("Five case studies from Yoniverse Productions, a Los Angeles writing and production "
          "company. Short form and commercial work across home services and the creator economy.")
    n1 = write_web(html, f"{OUT}/index.html",
                   title="Case Studies | Home Services Video Production | Yoniverse",
                   desc=D1, og_image=f"{SITE}/our-work/a/og-cover.jpg",
                   url=f"{SITE}/our-work/")

    packages = validate(PACKAGES_HTML, "packages")
    D2 = ("Monthly short-form content packages from Yoniverse Productions. Planning, "
          "direction, editing and posting included, from 2,000 dollars per month.")
    n2 = write_web(packages, f"{S}/deploy/packages/index.html",
                   title="Monthly Video Packages for Home Services | Yoniverse",
                   desc=D2, og_image=f"{SITE}/our-work/a/og-cover.jpg",
                   url=f"{SITE}/packages/")

    contact = validate(CONTACT_HTML, "contact")
    D4 = ("Contact Yoniverse Productions in Los Angeles. Call (310) 595-4519, email "
          "yoni@yoniverseproductions.com, or book twenty minutes on Google Meet.")
    n4 = write_web(contact, f"{S}/deploy/contact/index.html",
                   title="Contact | Yoniverse Productions",
                   desc=D4, og_image=f"{SITE}/our-work/a/og-cover.jpg",
                   url=f"{SITE}/contact/")

    home = validate(HOME_HTML, "home")
    D3 = ("Los Angeles video production for HVAC, plumbing and home service brands. Written, "
          "shot, cut and posted monthly. 128M+ views produced. Call (310) 595-4519.")
    n3 = write_web(home, f"{S}/deploy/index.html",
                   title="Home Services Video Production | Los Angeles | Yoniverse",
                   desc=D3, og_image=f"{SITE}/og/og-home.jpg",
                   url=f"{SITE}/")

    # 3.5 one page per case study, each with its own title and description
    case_sizes = []
    for i, c in enumerate(CASES):
        page = validate(case_page(i), "work/" + c["slug"])
        n = write_web(page, f"{S}/deploy/work/{c['slug']}/index.html",
                      title=f"{c['name']} | Case Study | Yoniverse Productions",
                      desc=c["desc"],
                      og_image=f"{SITE}/og/{c['og']}" if c.get("og") else f"{SITE}/our-work/a/og-cover.jpg",
                      url=f"{SITE}/work/{c['slug']}/")
        case_sizes.append((c["slug"], n))

    # the serverless function that receives the contact form
    os.makedirs(f"{S}/deploy/api", exist_ok=True)
    shutil.copy(f"{S}/api_contact.js", f"{S}/deploy/api/contact.js")

    # 3.5 sitemap so the new URLs get discovered
    urls = ["/", "/our-work/", "/packages/", "/contact/"] + [f"/work/{c['slug']}/" for c in CASES]
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
    for slug, n in case_sizes:
        print(f"  work/{slug}/".ljust(23) + f"-> {n/1024:.0f} KB")
    print(f"  shared assets        -> {assets/1048576:.2f} MB")
else:
    out = f"{S}/site.html"
    pathlib.Path(out).write_text(html, encoding="utf-8")
    print(f"{out} -> {os.path.getsize(out)/1048576:.2f} MB")
