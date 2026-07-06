const SITE      = "https://tubevd.com";
const STORE_URL = "https://tubevd.com/rate";

// i18n helper
const t = key => chrome.i18n.getMessage(key) || key;

const $ = id => document.getElementById(id);

const SCREENS = [
  "screen-loading","screen-blocked","screen-empty",
  "screen-limit","screen-upgrade","screen-activate",
  "screen-activated","screen-history","screen-list"
];

function show(id) {
  SCREENS.forEach(s => {
    const el = document.getElementById(s);
    if (el) el.classList.add("hidden");
  });
  const target = document.getElementById(id);
  if (target) target.classList.remove("hidden");
}

// Apply translations to all static text
function applyI18n() {
  // Header
  $("badge-plan").textContent = t("free");

  // Usage bar
  $("upgrade-link").textContent = t("upgradeNow");

  // Rating bar
  document.querySelector(".rate-btn").textContent     = t("rateUs");
  document.querySelector(".rate-btn").previousSibling.textContent = t("enjoyingApp") + " ";

  // Loading
  document.querySelector("#screen-loading .hint").textContent = t("scanning");

  // Blocked
  document.querySelector(".blocked-title").textContent = t("ytBlocked");
  const blockedHints = document.querySelectorAll("#screen-blocked .hint");
  if (blockedHints[0]) blockedHints[0].textContent = t("ytBlockedHint");
  if (blockedHints[1]) blockedHints[1].innerHTML = t("ytTry");

  // Empty
  document.querySelector(".empty-title").textContent = t("noVideos");
  document.querySelector("#screen-empty .hint").textContent = t("noVideosHint");

  // Limit
  document.querySelector(".limit-title").textContent = t("limitTitle");
  document.querySelector("#screen-limit .hint").textContent  = t("limitHint");
  $("btn-upgrade-limit").textContent = t("upgradeBtn");

  // Upgrade
  document.querySelector("#screen-upgrade .upgrade-header span").textContent = t("upgradeTitle");
  $("btn-go-premium").textContent  = t("getPremium");
  document.querySelector(".upgrade-note").textContent = t("guarantee");
  document.querySelector("#screen-upgrade .upgrade-body > div:last-child p").textContent = t("alreadyBought");
  $("btn-go-activate").innerHTML   = t("enterKey");

  // Activate
  document.querySelector("#screen-activate .upgrade-header span").textContent = t("activateTitle");
  document.querySelector("#screen-activate .upgrade-badge").textContent = t("activateTitle");
  document.querySelector("#screen-activate p").textContent = t("activateHint");
  $("btn-activate-now").textContent = t("activateBtn");
  $("license-input").placeholder    = "TUBEVD-XXXX-XXXX-XXXX";
  document.querySelector("#screen-activate .upgrade-body > p:last-child").innerHTML =
    t("noCode") + ' <a id="link-get-premium" href="#" style="color:var(--red);text-decoration:none">' + t("getPremiumLink") + '</a>';

  // History
  document.querySelector("#screen-history .section-header span").textContent = t("history");
  $("btn-clear-history").textContent = t("clearHistory");
  document.querySelector("#history-empty .hint").textContent = t("noHistory");

  // Footer
  $("footer-home").textContent    = t("home");
  $("footer-faq").textContent     = t("faq");
  $("footer-contact").textContent = t("support");
  $("footer-rate").textContent    = t("rate");

  // Batch btn
  $("btn-batch").textContent = t("downloadAll");
}

// Footer links
$("footer-home").onclick    = e => { e.preventDefault(); openSite("/"); };
$("footer-faq").onclick     = e => { e.preventDefault(); openSite("/faq"); };
$("footer-contact").onclick = e => { e.preventDefault(); openSite("/contact"); };
$("footer-rate").onclick    = e => { e.preventDefault(); chrome.tabs.create({ url: STORE_URL }); };

function openSite(path) { chrome.tabs.create({ url: SITE + path }); }

// Nav buttons
$("btn-refresh").onclick       = () => { show("screen-loading"); setTimeout(loadState, 300); };
$("upgrade-link").onclick      = () => show("screen-upgrade");
$("btn-back").onclick          = () => loadState();
$("btn-back-activate").onclick = () => show("screen-upgrade");
$("btn-upgrade-limit").onclick = () => show("screen-upgrade");
$("btn-go-premium").onclick    = () => openSite("/checkout");

document.addEventListener("click", e => {
  if (e.target && e.target.id === "link-get-premium") {
    e.preventDefault(); openSite("/checkout");
  }
});

$("btn-go-activate").onclick   = () => show("screen-activate");
$("btn-activate-now").onclick  = activateLicense;

$("license-input").onkeydown = e => { if (e.key === "Enter") activateLicense(); };
$("license-input").oninput   = e => {
  e.target.value = e.target.value.toUpperCase().replace(/[^A-Z0-9-]/g, "");
  $("license-error").textContent = "";
};

$("btn-go-back-activated").onclick = () => { show("screen-loading"); loadState(); };
$("btn-deactivate").onclick = () => {
  if (confirm(t("deactivateConfirm"))) {
    chrome.runtime.sendMessage({ type: "DEACTIVATE_LICENSE" }, () => {
      show("screen-loading"); loadState();
    });
  }
};

$("btn-history").onclick       = () => { loadHistory(); show("screen-history"); };
$("btn-clear-history").onclick = () => {
  chrome.runtime.sendMessage({ type: "CLEAR_HISTORY" }, () => loadHistory());
};

$("btn-rate-now").onclick = e => {
  e.preventDefault();
  chrome.storage.local.set({ showRatingPrompt: false, ratingDismissed: true });
  $("rating-bar").classList.add("hidden");
  chrome.tabs.create({ url: STORE_URL });
};
$("btn-rate-dismiss").onclick = () => {
  chrome.storage.local.set({ showRatingPrompt: false, ratingDismissed: true });
  $("rating-bar").classList.add("hidden");
};

// INIT
applyI18n();
show("screen-loading");
loadState();

// LOAD STATE
function loadState() {
  chrome.runtime.sendMessage({ type: "GET_STATE" }, res => {
    if (!res) { show("screen-empty"); return; }
    const { activeVideo, allVideos, blocked, premium, remaining, freeLimit } = res;

    const badge = $("badge-plan");
    badge.textContent = premium ? t("premiumBadge") : t("free");
    badge.className   = premium ? "badge-premium" : "badge-free";

    if (premium) {
      $("usage-bar").style.display = "none";
    } else {
      $("usage-bar").style.display = "block";
      $("usage-text").textContent  = `${remaining} ${t("usageOf")} ${freeLimit} ${t("usageLeft")}`;
      $("usage-fill").style.width  = `${Math.round((remaining / freeLimit) * 100)}%`;
    }

    chrome.storage.local.get(["showRatingPrompt","ratingDismissed"], d => {
      if (d.showRatingPrompt && !d.ratingDismissed) $("rating-bar").classList.remove("hidden");
    });

    if (blocked) { show("screen-blocked"); return; }

    const videos = activeVideo
      ? [activeVideo, ...(allVideos || []).filter(v => v.url !== activeVideo.url)]
      : (allVideos || []);

    if (!videos.length) { show("screen-empty"); return; }
    renderList(videos, premium, remaining);
  });
}

const LOCKED_Q = ["4K","2K","1080p"];

function renderList(videos, premium, remaining) {
  const ul = $("video-list");
  ul.innerHTML = "";
  const count = videos.length;
  $("list-count").textContent = `${count} ${count === 1 ? t("videoDetected") : t("videosDetected")}`;
  videos.forEach((v, i) => ul.appendChild(buildItem(v, premium, remaining, i === 0)));
  show("screen-list");
}

function buildItem(video, premium, remaining, isActive) {
  const li = document.createElement("li");
  li.className = "video-item" + (isActive ? " active-item" : "");
  const isQLocked      = !premium && LOCKED_Q.includes(video.quality);
  const isLimitReached = !premium && remaining <= 0;
  const locked = isQLocked || isLimitReached;
  const ext    = (video.type || "mp4").toLowerCase();
  const icon   = siteIcon(video.site || "Video");

  li.innerHTML = `
    <div class="vi-thumb" style="font-size:20px">${icon}</div>
    <div class="vi-info">
      <div class="vi-site">${isActive ? '<span class="active-dot"></span>' : ""}${video.site || "Video"}</div>
      <div class="vi-meta">
        <span class="pill pill-q${isQLocked ? " locked" : ""}">${video.quality || "HD"}</span>
        <span class="pill pill-t">${video.type || "MP4"}</span>
        ${isQLocked ? `<span class="pill pill-pro">${t("pro")}</span>` : ""}
      </div>
    </div>
    <div class="vi-action">
      <button class="btn-dl${locked ? " locked" : ""}"
        data-url="${video.url}" data-ext="${ext}"
        data-quality="${video.quality || ""}" data-site="${video.site || ""}">
        ${locked ? (isLimitReached ? t("limit") : t("pro")) : t("download")}
      </button>
    </div>`;

  const btn = li.querySelector(".btn-dl");
  if (locked) btn.onclick = () => show(isLimitReached ? "screen-limit" : "screen-upgrade");
  else        btn.addEventListener("click", handleDownload);
  return li;
}

function handleDownload(e) {
  const btn = e.currentTarget;
  const { url, ext, quality, site } = btn.dataset;
  const orig = btn.textContent.trim();
  btn.textContent = t("downloading"); btn.disabled = true;
  chrome.runtime.sendMessage({ type: "DOWNLOAD_VIDEO", url, ext, quality, site }, res => {
    if (res?.error === "limit_reached")    { show("screen-limit");   return; }
    if (res?.error === "premium_required") { show("screen-upgrade"); return; }
    btn.textContent = t("done"); btn.classList.add("done");
    setTimeout(() => { btn.textContent = orig; btn.classList.remove("done"); btn.disabled = false; loadState(); }, 1800);
  });
}

$("btn-batch").onclick = () => {
  chrome.runtime.sendMessage({ type: "GET_STATE" }, res => {
    (res?.allVideos || []).forEach((v, i) => {
      setTimeout(() => {
        chrome.runtime.sendMessage({ type: "DOWNLOAD_VIDEO", url: v.url, ext: (v.type||"mp4").toLowerCase(), quality: v.quality, site: v.site });
      }, i * 600);
    });
  });
};

function loadHistory() {
  chrome.runtime.sendMessage({ type: "GET_HISTORY" }, res => {
    const hist  = res?.history || [];
    const ul    = $("history-list");
    const empty = $("history-empty");
    ul.innerHTML = "";
    if (!hist.length) { empty.classList.remove("hidden"); return; }
    empty.classList.add("hidden");
    hist.forEach(h => {
      const li = document.createElement("li");
      li.className = "history-item";
      li.innerHTML = `
        <div class="hi-icon">${siteIcon(h.site||"Video")}</div>
        <div class="hi-info">
          <div class="hi-site">${h.site||"Video"}</div>
          <div class="hi-meta">${h.quality} · ${h.type} · ${h.date}</div>
        </div>
        <button class="hi-redown" data-url="${h.url}" data-ext="${(h.type||"MP4").toLowerCase()}"
          data-quality="${h.quality}" data-site="${h.site}">${t("download")}</button>`;
      li.querySelector(".hi-redown").onclick = e => {
        const b = e.currentTarget;
        b.textContent = t("downloading");
        chrome.runtime.sendMessage({ type:"DOWNLOAD_VIDEO", url:b.dataset.url, ext:b.dataset.ext, quality:b.dataset.quality, site:b.dataset.site }, () => {
          b.textContent = t("done");
          setTimeout(() => { b.textContent = t("download"); }, 2000);
        });
      };
      ul.appendChild(li);
    });
  });
}

function activateLicense() {
  const code  = $("license-input").value.trim().toUpperCase();
  const errEl = $("license-error");
  const btn   = $("btn-activate-now");

  if (!code) { errEl.textContent = t("enterCode"); return; }
  if (!code.startsWith("TUBEVD-")) { errEl.textContent = t("invalidFormat"); return; }

  btn.textContent = t("verifying"); btn.disabled = true; errEl.textContent = "";

  chrome.storage.local.get("deviceId", d => {
    let deviceId = d.deviceId;
    if (!deviceId) {
      deviceId = "ext_" + Math.random().toString(36).substr(2, 16);
      chrome.storage.local.set({ deviceId });
    }

    chrome.runtime.sendMessage({ type: "ACTIVATE_CODE", code, device: deviceId }, res => {
      btn.disabled = false; btn.textContent = t("activateBtn");
      if (res?.success) {
        $("license-code-display").textContent = code;
        const days = Math.ceil((res.expiry - Date.now()) / 86400000);
        $("license-expiry-display").textContent =
          `${t("validFor")} ${days} ${t("days")} ${new Date(res.expiry).toLocaleDateString()}`;
        // Update activated screen texts
        document.querySelector("#screen-activated p:first-of-type").textContent = t("activatedTitle");
        document.querySelector("#screen-activated .hint").textContent = t("activatedSub");
        $("btn-go-back-activated").textContent = t("startDown");
        $("btn-deactivate").textContent        = t("deactivate");
        document.querySelector("#license-info div:first-child").textContent = t("licenseKey");
        show("screen-activated");
        loadState();
      } else {
        const errs = {
          "invalid_code":  t("invalidCode"),
          "already_used":  t("alreadyUsed"),
          "expired":       t("expired"),
          "network_error": t("networkError"),
          "server_error":  t("serverError"),
        };
        errEl.textContent = errs[res?.error] || t("genericError");
      }
    });
  });
}

function siteIcon(site) {
  const s = (site || "").toLowerCase();
  if (s.includes("facebook"))    return "📘";
  if (s.includes("twitter") || s.includes("x.com")) return "🐦";
  if (s.includes("vimeo"))       return "🎬";
  if (s.includes("dailymotion")) return "▶️";
  if (s.includes("instagram"))   return "📸";
  if (s.includes("tiktok"))      return "🎵";
  if (s.includes("reddit"))      return "🤖";
  if (s.includes("twitch"))      return "🎮";
  return "🎬";
}

chrome.runtime.sendMessage({ type: "CHECK_LICENSE" }, res => {
  if (res?.isPremium) {
    $("badge-plan").textContent = t("premiumBadge");
    $("badge-plan").className   = "badge-premium";
  }
});
