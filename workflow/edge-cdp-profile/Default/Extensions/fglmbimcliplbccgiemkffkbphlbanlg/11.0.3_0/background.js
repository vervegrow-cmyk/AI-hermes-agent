const FREE_DAILY_LIMIT  = 5;
const YOUTUBE_DOMAINS   = ["youtube.com","youtu.be","youtube-nocookie.com"];
const SITE_URL          = "https://tubevd.com";

// ── Install / Uninstall events ───────────────
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === "install") {
    // First install → open welcome page
    chrome.tabs.create({ url: SITE_URL + "/?welcome=1" });
  }
  if (details.reason === "update") {
    // Optional: open changelog on update
    // chrome.tabs.create({ url: SITE_URL + "/changelog" });
  }
});

// Uninstall redirect
chrome.runtime.setUninstallURL(SITE_URL + "/contact?from=uninstall");

// ── Video detection patterns ─────────────────
const VIDEO_PATTERNS = [
  /\.mp4(\?|$)/i,/\.webm(\?|$)/i,/\.m3u8(\?|$)/i,/\.flv(\?|$)/i,
  /videoplayback/i,/video\/mp4/i,/manifest\.mpd/i,
  /fbcdn.*video/i,/twimg.*video/i,/vimeocdn/i,
  /akamaized.*video/i,/cloudfront.*\.mp4/i,
  /cdn.*video/i,/video.*cdn/i,
  /dailymotion.*video/i,/dmcdn/i,
  /tiktokcdn/i,/tiktok.*video/i,
  /instagram.*\.mp4/i,/cdninstagram/i,
];

const SKIP_PATTERNS = [
  /analytics/i,/tracking/i,/pixel/i,/beacon/i,
  /\.jpg(\?|$)/i,/\.png(\?|$)/i,/\.gif(\?|$)/i,
  /\.css(\?|$)/i,/\.js(\?|$)/i,/\.woff/i,/thumbnail/i,
];

const tabVideos     = {};
const tabBlocked    = {};
const tabActiveVideo = {};

function isYouTube(url) {
  try {
    const h = new URL(url).hostname.replace("www.","");
    return YOUTUBE_DOMAINS.some(d => h === d || h.endsWith("."+d));
  } catch { return false; }
}

function detectQuality(url) {
  if (/2160|4k|uhd/i.test(url))  return "4K";
  if (/1440|2k/i.test(url))      return "2K";
  if (/1080|fhd/i.test(url))     return "1080p";
  if (/720|hd/i.test(url))       return "720p";
  if (/480/i.test(url))          return "480p";
  if (/360/i.test(url))          return "360p";
  return "HD";
}

function detectType(url) {
  if (/\.mp4/i.test(url))  return "MP4";
  if (/\.webm/i.test(url)) return "WEBM";
  if (/\.m3u8/i.test(url)) return "HLS";
  if (/\.mpd/i.test(url))  return "DASH";
  return "VIDEO";
}

function detectSite(tabUrl) {
  try {
    const h = new URL(tabUrl).hostname.replace("www.","");
    if (h.includes("facebook")||h.includes("fbcdn"))   return "Facebook";
    if (h.includes("twitter")||h.includes("twimg"))    return "Twitter / X";
    if (h.includes("vimeo")||h.includes("vimeocdn"))   return "Vimeo";
    if (h.includes("dailymotion")||h.includes("dmcdn"))return "Dailymotion";
    if (h.includes("instagram")||h.includes("cdninstagram")) return "Instagram";
    if (h.includes("tiktok")||h.includes("tiktokcdn")) return "TikTok";
    if (h.includes("reddit"))   return "Reddit";
    if (h.includes("twitch"))   return "Twitch";
    if (h.includes("linkedin")) return "LinkedIn";
    return h;
  } catch { return "Video"; }
}

// ── Network interception ─────────────────────
chrome.webRequest.onBeforeSendHeaders.addListener(
  ({ url, tabId, type }) => {
    if (tabId < 0) return;
    if (isYouTube(url)) { tabBlocked[tabId] = true; return; }
    if (type === "sub_frame") return;
    if (SKIP_PATTERNS.some(p => p.test(url))) return;
    if (!VIDEO_PATTERNS.some(p => p.test(url))) return;
    if (!tabVideos[tabId]) tabVideos[tabId] = [];
    if (tabVideos[tabId].some(v => v.url === url)) return;
    tabVideos[tabId].push({
      url, quality: detectQuality(url),
      type: detectType(url), timestamp: Date.now(),
    });
    tabActiveVideo[tabId] = tabVideos[tabId][tabVideos[tabId].length - 1];
    chrome.action.setBadgeText({ text:"▶", tabId });
    chrome.action.setBadgeBackgroundColor({ color:"#E8593C", tabId });
  },
  { urls:["<all_urls>"] }, ["requestHeaders"]
);

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === "loading") {
    tabVideos[tabId]     = [];
    tabBlocked[tabId]    = tab.url ? isYouTube(tab.url) : false;
    tabActiveVideo[tabId]= null;
    chrome.action.setBadgeText({ text:"", tabId });
  }
});

chrome.tabs.onRemoved.addListener((tabId) => {
  delete tabVideos[tabId];
  delete tabBlocked[tabId];
  delete tabActiveVideo[tabId];
});

// ── Storage helpers ──────────────────────────
async function getTodayCount() {
  return new Promise(resolve => {
    const today = new Date().toDateString();
    chrome.storage.local.get(["downloadDate","downloadCount"], d => {
      resolve(d.downloadDate !== today ? 0 : (d.downloadCount || 0));
    });
  });
}

async function incrementCount() {
  const today = new Date().toDateString();
  const count = await getTodayCount();
  chrome.storage.local.set({ downloadDate: today, downloadCount: count + 1 });
}

async function isPremium() {
  return new Promise(r => chrome.storage.local.get(["isPremium","licenseExpiry"], d => {
    const valid = d.isPremium && (!d.licenseExpiry || d.licenseExpiry > Date.now());
    r(valid);
  }));
}

async function getHistory() {
  return new Promise(r => chrome.storage.local.get("dlHistory", d => r(d.dlHistory || [])));
}

async function addToHistory(item) {
  const hist = await getHistory();
  hist.unshift(item);
  chrome.storage.local.set({ dlHistory: hist.slice(0, 20) });
}

async function getTotalDownloads() {
  return new Promise(r => chrome.storage.local.get("totalDownloads", d => r(d.totalDownloads || 0)));
}

async function incrementTotal() {
  const t = await getTotalDownloads();
  chrome.storage.local.set({ totalDownloads: t + 1 });
  return t + 1;
}

// ── Messages ─────────────────────────────────
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {

  if (msg.type === "GET_STATE") {
    chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
      const tabId   = tabs[0]?.id;
      const tabUrl  = tabs[0]?.url || "";
      const blocked = tabBlocked[tabId] || isYouTube(tabUrl);
      const premium = await isPremium();
      const todayCount = await getTodayCount();
      const remaining  = Math.max(0, FREE_DAILY_LIMIT - todayCount);
      const history    = await getHistory();
      const site       = detectSite(tabUrl);
      sendResponse({
        activeVideo: tabActiveVideo[tabId] || null,
        allVideos:   tabVideos[tabId] || [],
        blocked, premium, todayCount,
        remaining, freeLimit: FREE_DAILY_LIMIT,
        history, site,
      });
    });
    return true;
  }

  if (msg.type === "SET_ACTIVE_VIDEO") {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const tabId = tabs[0]?.id;
      if (tabId) {
        tabActiveVideo[tabId] = msg.video;
        chrome.action.setBadgeText({ text:"▶", tabId });
        chrome.action.setBadgeBackgroundColor({ color:"#E8593C", tabId });
      }
    });
    return true;
  }

  if (msg.type === "DOWNLOAD_VIDEO") {
    (async () => {
      const premium    = await isPremium();
      const todayCount = await getTodayCount();
      if (!premium && todayCount >= FREE_DAILY_LIMIT) { sendResponse({ error:"limit_reached" }); return; }
      const q = msg.quality || "";
      if (!premium && ["4K","2K","1080p"].includes(q)) { sendResponse({ error:"premium_required" }); return; }

      const filename = `TubeVD_${Date.now()}.${msg.ext || "mp4"}`;
      chrome.downloads.download({ url: msg.url, filename }, () => {
        if (chrome.runtime.lastError) chrome.tabs.create({ url: msg.url });
      });

      await incrementCount();
      const total = await incrementTotal();
      await addToHistory({
        url: msg.url, site: msg.site || "Video",
        quality: q || "HD", type: (msg.ext || "mp4").toUpperCase(),
        date: new Date().toLocaleDateString(), filename,
      });

      if ([3,10,25].includes(total)) chrome.storage.local.set({ showRatingPrompt: true });
      sendResponse({ success: true });
    })();
    return true;
  }

  if (msg.type === "ACTIVATE_CODE") {
    const code   = (msg.code || "").trim().toUpperCase();
    const device = msg.device || "unknown";

    if (!code.startsWith("TUBEVD-")) {
      sendResponse({ success: false, error: "invalid_code" });
      return true;
    }

    // Verify with server API — codes are NOT stored in extension
    fetch("https://tubevd.com/api/verify-license.php", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ code, device }),
    })
    .then(r => r.json())
    .then(res => {
      if (res.success) {
        chrome.storage.local.set({
          isPremium:     true,
          licenseCode:   code,
          licenseExpiry: res.expiry * 1000, // convert to ms
        }, () => sendResponse({ success: true, expiry: res.expiry * 1000 }));
      } else {
        sendResponse({ success: false, error: res.error });
      }
    })
    .catch(() => {
      // Fallback: offline check
      sendResponse({ success: false, error: "network_error" });
    });
    return true;
  }

    if (msg.type === "CHECK_LICENSE") {
    chrome.storage.local.get(["isPremium","licenseCode","licenseExpiry"], (d) => {
      const valid = d.isPremium && d.licenseExpiry && d.licenseExpiry > Date.now();
      if (!valid && d.isPremium) chrome.storage.local.set({ isPremium: false });
      sendResponse({
        isPremium: valid,
        licenseCode: d.licenseCode || null,
        daysLeft: d.licenseExpiry ? Math.ceil((d.licenseExpiry - Date.now()) / 86400000) : 0,
      });
    });
    return true;
  }

  if (msg.type === "DEACTIVATE_LICENSE") {
    chrome.storage.local.set({ isPremium:false, licenseCode:null, licenseExpiry:null });
    sendResponse({ success:true });
    return true;
  }

  if (msg.type === "GET_HISTORY") {
    getHistory().then(h => sendResponse({ history:h }));
    return true;
  }

  if (msg.type === "CLEAR_HISTORY") {
    chrome.storage.local.set({ dlHistory:[] });
    sendResponse({ success:true });
    return true;
  }

  if (msg.type === "OPEN_WEBSITE") {
    chrome.tabs.create({ url: SITE_URL + (msg.path || "/") });
    return true;
  }
});
