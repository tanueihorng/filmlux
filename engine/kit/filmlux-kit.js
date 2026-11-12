/* Filmlux kit: helpers for custom html scenes, so a described idea becomes a polished frame without starting from zero.
   The engine injects this file into every html scene (and the scene template loads it too), then sets window.FILMLUX
   and calls window.onFilmlux(FILMLUX). Use Kit inside onFilmlux / renderAt.

     Kit.init()                 theme colours + fonts as CSS variables (--bg0 --bg1 --bg2 --ink --muted --accent --accent2 --card --line),
                                font families "Display" "Editorial" "Hand" "Mono" "Condensed" "Grotesk" "Fraunces" "Chunky", classes below
     Kit.safe()                 a box inside the safe area (clear of the captions when they are on)
     Kit.seg(t, a, b)           0..1 progress of t between a and b         Kit.ease.out / inOut / back (p)     Kit.spring(p, "snappy")
     Kit.reveal(el, p, kind)    an entrance at progress p in the film's motion style (kind: rise | left | right | scale | pop)
     Kit.words(el)              wrap words in spans for staggered reveals (keeps <em>)
     Kit.fit(el, max, min)      shrink text until it fits its box (px at 1080p; scaled for other formats)
     Kit.px(n)                  n design pixels (1080p) in real pixels
   CSS classes: .kit-title .kit-sub .kit-eyebrow .kit-card .kit-safe, <em> = accent italic. Everything must depend only on t. */
(function () {
  "use strict";
  if (window.Kit && window.Kit.__v) return;
  const F = () => window.FILMLUX || { props: {}, theme: { colors: {}, type: {} }, width: innerWidth, height: innerHeight };
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const seg = (t, a, b) => clamp((t - a) / Math.max(1e-6, b - a));
  const ease = { out: p => 1 - Math.pow(1 - p, 3), inOut: p => p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2,
                 back: p => { const c = 1.4; return 1 + (c + 1) * Math.pow(p - 1, 3) + c * Math.pow(p - 1, 2); } };
  const SPR = { spring: [10, 100, 1], snappy: [20, 200, 1], bouncy: [8, 100, 1], heavy: [15, 80, 2], smooth: [200, 100, 1] };
  function spring(p, name = "spring") {                              // the same damped spring as the stage (Remotion-style)
    if (p >= 1) return 1; const [d, k, m] = SPR[name] || SPR.spring, ts = p * 1.1; if (ts <= 0) return 0;
    const w0 = Math.sqrt(k / m), z = d / (2 * Math.sqrt(k * m));
    if (z < 1) { const wd = w0 * Math.sqrt(1 - z * z); return 1 + Math.exp(-z * w0 * ts) * (-Math.cos(wd * ts) - (z * w0 / wd) * Math.sin(wd * ts)); }
    const r = Math.sqrt(Math.max(0, z * z - 1)), r1 = -w0 * (z - r), r2 = -w0 * (z + r), B = r1 / ((r2 - r1) || 1e-6), A = -1 - B;
    return 1 + A * Math.exp(r1 * ts) + B * Math.exp(r2 * ts);
  }
  let U = 1;
  const px = n => (n * U) + "px";
  const FAM = { sans: '"Display"', heavy: '"Display"', serif: '"Editorial"', fraunces: '"Fraunces"', condensed: '"Condensed"', grotesk: '"Grotesk"', mono: '"Mono"', hand: '"Hand"', pixel: '"Pixel"', chunky: '"Chunky"' };
  function init() {
    const f = F(), c = (f.theme && f.theme.colors) || {}, ty = (f.theme && f.theme.type) || {}, r = document.documentElement.style;
    const W = f.width || innerWidth, H = f.height || innerHeight; U = Math.min(W, H) / 1080;
    Object.entries(c).forEach(([k, v]) => r.setProperty("--" + k, v));
    r.setProperty("--W", W + "px"); r.setProperty("--H", H + "px"); r.setProperty("--u", U + "px");
    r.setProperty("--font-display", FAM[ty.display] || FAM.sans); r.setProperty("--font-body", FAM[ty.body] || FAM.sans);
    r.setProperty("--font-eyebrow", FAM[ty.eyebrow] || FAM[ty.body] || FAM.sans);
    const fu = f.fonts || "../../assets/fonts", face = (fam, file, w, st) => `@font-face{font-family:"${fam}";font-weight:${w};font-style:${st || "normal"};src:url("${fu}/${file}")}`;
    const css = [face("Display", "InterDisplay-Regular.ttf", 400), face("Display", "InterDisplay-Medium.ttf", 500), face("Display", "InterDisplay-SemiBold.ttf", 600), face("Display", "inter-800.woff2", 800),
      face("Editorial", "instrument-serif-400.woff2", 400), face("Editorial", "instrument-serif-400-italic.woff2", 400, "italic"), face("Fraunces", "fraunces-500.woff2", 500),
      face("Fraunces", "fraunces-500-italic.woff2", 500, "italic"), face("Serif", "fraunces-latin-600-italic.woff2", 600, "italic"), face("Condensed", "anton-400.woff2", 400),
      face("Grotesk", "space-grotesk-500.woff2", 500), face("Grotesk", "space-grotesk-700.woff2", 700), face("Mono", "jetbrains-mono-500.woff2", 500),
      face("Hand", "caveat-700.woff2", 700), face("Chunky", "bricolage-800.woff2", 800),
      `:root{--bg0:#0b1530;--bg1:#060a16;--bg2:#16264a;--ink:#fff;--muted:rgba(255,255,255,.66);--accent:#ED193D;--accent2:#ff6b84;--card:rgba(255,255,255,.06);--line:rgba(255,255,255,.12)}`,
      `html,body{margin:0;width:${W}px;height:${H}px;overflow:hidden;background:var(--bg0);color:var(--ink);font-family:var(--font-body),"Segoe UI",system-ui,sans-serif;-webkit-font-smoothing:antialiased}`,
      `.kit-title{font-family:var(--font-display),"Display",sans-serif;font-weight:${({ serif: 400, condensed: 400, heavy: 800, fraunces: 500, hand: 700, chunky: 800 })[ty.display] || 600};letter-spacing:-.02em;line-height:1.02;text-wrap:balance}`,
      `.kit-sub{color:var(--muted);font-size:${px(32)};line-height:1.4;font-weight:500;text-wrap:pretty}`,
      `.kit-eyebrow{font-family:var(--font-eyebrow),sans-serif;font-size:${px(22)};letter-spacing:.26em;font-weight:600;color:var(--accent2);text-transform:uppercase}`,
      `.kit-card{background:var(--card);border:1px solid var(--line);border-radius:${px(24)};box-shadow:0 ${px(30)} ${px(80)} rgba(0,0,0,.28)}`,
      `.kit-safe{position:absolute;left:8%;right:8%;top:12%;bottom:${f.captions ? (H > W * 1.1 ? 26 : 21) : 14}%}`,
      `.kit-w{display:inline-block;white-space:pre}`,
      `em{font-family:"Serif",Georgia,serif;font-style:italic;font-weight:600;color:var(--accent)}`].join("\n");
    let s = document.getElementById("kit-css"); if (!s) { s = document.createElement("style"); s.id = "kit-css"; document.head.appendChild(s); } s.textContent = css;
    return f;
  }
  function safe(parent) { const b = document.createElement("div"); b.className = "kit-safe"; (parent || document.body).appendChild(b); return b; }
  function words(e) {
    const out = [], walk = (node, em) => [...node.childNodes].forEach(n => {
      if (n.nodeType === 3) n.textContent.split(/(\s+)/).forEach(part => { if (!part) return; if (/^\s+$/.test(part)) { out.push(document.createTextNode(part)); return; }
        const s = document.createElement("span"); s.className = "kit-w"; s.textContent = part; if (em) { const m = document.createElement("em"); m.appendChild(s); out.push(m); } else out.push(s); });
      else if (n.nodeName === "EM") walk(n, true); else if (n.nodeName === "BR") out.push(document.createElement("br")); });
    walk(e, false); e.innerHTML = ""; out.forEach(n => e.appendChild(n)); return [...e.querySelectorAll(".kit-w")];
  }
  function fit(e, max, min = 24) { let s = max; e.style.fontSize = px(s); const lim = e.parentElement.clientWidth;
    while (s > min && (e.scrollWidth > lim + 1 || e.scrollWidth > e.clientWidth + 1 || e.parentElement.scrollHeight > e.parentElement.clientHeight + 2)) { s -= 2; e.style.fontSize = px(s); } return s; }
  function reveal(e, p, kind = "rise", dist = 26) {
    if (!e) return; p = clamp(p); const st = e.style, m = (F().motion) || "smooth";
    const mv = (k, d) => kind === "left" ? `translateX(${px((1 - k) * -d * 1.6)})` : kind === "right" ? `translateX(${px((1 - k) * d * 1.6)})` : kind === "scale" ? `scale(${.92 + .08 * k})` : kind === "pop" ? `scale(${.86 + .14 * k})` : `translateY(${px((1 - k) * d)})`;
    st.filter = "none"; st.clipPath = "";
    if (m === "mask") { const k = ease.inOut(clamp(p * 1.15)); st.opacity = p > 0 ? 1 : 0; st.transform = `translateY(${(1 - k) * 105}%)`; st.clipPath = `inset(-30% -6% ${(1 - k) * 120 - 18}% -6%)`; }
    else if (m === "typewriter") { const n = Math.max(1, (e.textContent || "").length), q = Math.floor(clamp(p * 1.25) * n + (p > 0 ? 1 : 0)) / n; st.opacity = q > 0 ? 1 : 0; st.transform = "none"; st.clipPath = `inset(-30% ${(1 - clamp(q)) * 100}% -30% -4%)`; }
    else if (["snappy", "spring", "bouncy", "heavy", "slam", "flip", "glitch"].includes(m)) { const k = spring(p, SPR[m] ? m : "snappy"); st.opacity = clamp(p * 4); st.transform = mv(k, dist * 1.4); }
    else if (m === "stopmotion") { const q = Math.floor(p * 6) / 6, k = ease.out(q); st.opacity = q > 0 ? 1 : 0; st.transform = mv(k, dist * 1.4) + ` rotate(${((q * 7) % 2 - 1) * 1.2 * (1 - k)}deg)`; }
    else if (m === "gentle") { const k = ease.inOut(clamp(p * .9)); st.opacity = clamp(p * 1.1); st.transform = mv(k, dist * .6); }
    else { const k = ease.out(p); st.opacity = clamp(p * 1.4); st.transform = mv(k, dist); st.filter = p < 1 ? `blur(${px((1 - k) * 8)})` : "none"; }
  }
  // Layout checks for the engine's qa (run at the scene's last frame). Mark full-frame art with data-bleed to exempt it.
  function qa() {
    const f = F(), W = f.width || innerWidth, H = f.height || innerHeight, portrait = H > W * 1.1, out = [], mx = W * .04, my = H * .04;
    document.querySelectorAll("body *").forEach(e => {
      if (["SCRIPT", "STYLE", "CANVAS", "SVG", "svg"].includes(e.tagName) || e.closest("svg")) return;
      const txt = [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()); if (!txt) return;
      const cs = getComputedStyle(e), r = e.getBoundingClientRect(); if (r.width < 2 || +cs.opacity === 0 || cs.visibility === "hidden" || cs.display === "none") return;
      let op = 1; for (let a = e; a && a !== document.body; a = a.parentElement) op *= +getComputedStyle(a).opacity; if (op < .05) return;
      const label = (e.textContent || "").trim().slice(0, 40), bleed = e.closest("[data-bleed]");
      if (e.scrollWidth > e.clientWidth + 2 && cs.overflow === "visible" && e.clientWidth > 0) out.push(`text overflows its box: "${label}"`);
      if (!bleed && f.captions && r.bottom > H * (portrait ? .745 : .80) && r.top < H) out.push(`sits in the caption zone (captions will cover it): "${label}"`);
      if (!bleed && (r.left < mx - 1 || r.right > W - mx + 1 || r.top < my - 1 || r.bottom > H - my + 1)) out.push(`outside the safe area: "${label}"`);
    });
    return [...new Set(out)].slice(0, 8);
  }
  window.Kit = { __v: 1, init, safe, seg, clamp, ease, spring, reveal, words, fit, px, qa, get U() { return U; } };
})();
