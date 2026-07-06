(function () {
  if (window.__tubevd_injected) return;
  window.__tubevd_injected = true;

  const BRAND = "#E8593C";

  function isYouTube()   { return /youtube\.com|youtu\.be/.test(location.hostname); }
  function isFacebook()  { return /facebook\.com|fb\.watch/.test(location.hostname); }
  function isTwitter()   { return /twitter\.com|x\.com/.test(location.hostname); }
  function isInstagram() { return /instagram\.com/.test(location.hostname); }
  function isTikTok()    { return /tiktok\.com/.test(location.hostname); }
  function isVimeo()     { return /vimeo\.com/.test(location.hostname); }

  // ── Helpers ──────────────────────────────────────
  function getCookie(name) {
    var p = ("; "+document.cookie).split("; "+name+"=");
    return p.length===2 ? p.pop().split(";").shift() : null;
  }

  function getQuality(v) {
    var h = v.videoHeight;
    if (h>=2160) return "4K";
    if (h>=1080) return "1080p";
    if (h>=720)  return "720p";
    if (h>=480)  return "480p";
    if (h>0)     return h+"p";
    return "HD";
  }

  function getBestSrc(v) {
    var c=[v.currentSrc,v.src];
    v.querySelectorAll("source").forEach(function(s){c.push(s.src);});
    return c.find(function(s){return s&&s.startsWith("http")&&!s.startsWith("blob:");}) || null;
  }

  // ── Quality picker popup ─────────────────────────
  function showQualityPicker(sources, onPick) {
    var existing = document.getElementById("__tubevd_picker");
    if (existing) existing.remove();

    var el = document.createElement("div");
    el.id = "__tubevd_picker";
    Object.assign(el.style, {
      position:"fixed", bottom:"20px", right:"20px",
      zIndex:"2147483647", background:"#1a1a1a",
      borderRadius:"12px", padding:"12px",
      boxShadow:"0 8px 32px rgba(0,0,0,.6)",
      fontFamily:"-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif",
      minWidth:"200px",
    });

    var header = document.createElement("div");
    header.style.cssText="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px";
    header.innerHTML = '<span style="color:#fff;font-size:13px;font-weight:700">Choose Quality</span>' +
      '<button id="__tubevd_close" style="background:none;border:none;color:#888;cursor:pointer;font-size:18px;line-height:1">×</button>';
    el.appendChild(header);

    sources.forEach(function(s) {
      var btn = document.createElement("button");
      Object.assign(btn.style, {
        display:"flex", alignItems:"center", justifyContent:"space-between",
        width:"100%", padding:"8px 12px", marginBottom:"6px",
        background: s.isMP3 ? "#1a1a2e" : "#2a2a2a",
        border: s.isMP3 ? "1px solid #7c3aed" : "1px solid #333",
        borderRadius:"8px", color:"#fff", cursor:"pointer",
        fontSize:"12px", fontWeight:"600", transition:"background .15s",
      });
      btn.innerHTML =
        '<span>'+(s.isMP3?"🎵 MP3 Audio":s.label)+'</span>' +
        '<span style="color:'+(s.isPremium?"#f59e0b":"#E8593C")+'">'+
          (s.isPremium?"🔒 Pro":"↓")+
        '</span>';
      btn.addEventListener("click", function() {
        el.remove();
        onPick(s);
      });
      btn.addEventListener("mouseenter",function(){btn.style.background=s.isMP3?"#2d2b4e":"#3a3a3a";});
      btn.addEventListener("mouseleave",function(){btn.style.background=s.isMP3?"#1a1a2e":"#2a2a2a";});
      el.appendChild(btn);
    });

    document.body.appendChild(el);
    document.getElementById("__tubevd_close").addEventListener("click",function(){el.remove();});
    setTimeout(function(){document.addEventListener("click",function h(e){if(!el.contains(e.target)){el.remove();document.removeEventListener("click",h);}});},100);
  }

  // ── Download via background ──────────────────────
  function doDownload(btn, url, quality, ext, site, origLabel) {
    btn.disabled = true;
    setStatus(btn,"↓…","#555");
    chrome.runtime.sendMessage({
      type:"DOWNLOAD_VIDEO", url:url, ext:ext||"mp4",
      quality:quality, site:site||location.hostname
    }, function(res) {
      if (!res)                          { setStatus(btn,"Error","#e74c3c",origLabel,2000); return; }
      if (res.error==="limit_reached")   { setStatus(btn,"⚠ Limit","#f59e0b",origLabel,2500); return; }
      if (res.error==="premium_required"){ setStatus(btn,"🔒 Pro","#7c3aed",origLabel,2500); return; }
      setStatus(btn,"✓ Done","#22c55e",origLabel,2000);
    });
  }

  function setStatus(btn, text, color, restore, delay) {
    var sp = btn.querySelector("span");
    if (sp) sp.textContent = text;
    btn.style.background = color;
    if (delay) setTimeout(function(){
      if(sp) sp.textContent = restore;
      btn.style.background = BRAND;
      btn.disabled = false;
    }, delay);
  }

  // ── Button factory ───────────────────────────────
  function makeBtn(label) {
    var btn = document.createElement("button");
    btn.setAttribute("data-tubevd","1");
    btn.innerHTML =
      '<svg viewBox="0 0 16 16" width="12" height="12" fill="white" style="flex-shrink:0">'+
        '<rect x="6" y="1" width="4" height="7" rx="1"/>'+
        '<polygon points="2,8 14,8 8,15"/>'+
      '</svg>'+
      '<span>'+label+'</span>';
    Object.assign(btn.style, {
      position:"absolute", bottom:"10px", right:"10px",
      zIndex:"2147483647", display:"flex", alignItems:"center",
      gap:"5px", padding:"6px 12px", background:BRAND, color:"white",
      border:"none", borderRadius:"8px", cursor:"pointer",
      opacity:"0", pointerEvents:"none",
      transition:"opacity .2s, transform .15s",
      fontFamily:"-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif",
      fontSize:"11px", fontWeight:"700",
      boxShadow:"0 2px 10px rgba(0,0,0,.4)",
    });
    btn.addEventListener("mouseenter",function(){btn.style.transform="scale(1.05)";});
    btn.addEventListener("mouseleave",function(){btn.style.transform="scale(1)";});
    return btn;
  }

  function attachHover(wrapper, btn) {
    wrapper.addEventListener("mouseenter",function(){btn.style.opacity="1";btn.style.pointerEvents="auto";});
    wrapper.addEventListener("mouseleave",function(){btn.style.opacity="0";btn.style.pointerEvents="none";});
  }

  // ══════════════════════════════════════════════════
  // FACEBOOK
  // ══════════════════════════════════════════════════
  var fbDtsg = null;
  var fbInjected = {};

  function extractDtsg() {
    var el = document.querySelector('input[name="fb_dtsg"]');
    if (el) return el.value;
    var scripts = document.querySelectorAll("script");
    for (var i=0;i<scripts.length;i++) {
      var m = scripts[i].textContent.match(/"token":"(EAA[^"]{10,})"/);
      if (m) return m[1];
      var m2 = scripts[i].textContent.match(/\["DTSGInitData".*?"token","([^"]+)"/);
      if (m2) return m2[1];
    }
    return null;
  }

  function extractFbVideoId() {
    var m1 = location.href.match(/\/videos\/(\d+)/);
    if (m1) return m1[1];
    var m2 = location.search.match(/[?&]v=(\d+)/);
    if (m2) return m2[1];
    var el = document.querySelector("[data-video-id]");
    if (el && el.dataset.videoId) return el.dataset.videoId;
    return null;
  }

  async function injectFbButton(videoEl) {
    if (videoEl.__tubevd_fb) return;
    videoEl.__tubevd_fb = true;
    var videoId = extractFbVideoId();
    if (!videoId || fbInjected[videoId]) return;
    fbInjected[videoId] = true;

    if (!fbDtsg) fbDtsg = extractDtsg();
    if (!fbDtsg) return;

    var userId = getCookie("c_user") || "";
    try {
      var res  = await fetch("https://www.facebook.com/video/video_data_async/?video_id="+videoId+"&fb_dtsg_ag="+fbDtsg+"&__user="+userId+"&__a=1");
      var text = await res.text();
      var json = JSON.parse(text.replace("for (;;);",""));
      if (!json.payload) return;
      var hd = json.payload.hd_src;
      var sd = json.payload.sd_src;
      if (!hd && !sd) return;

      var wrapper = videoEl.parentElement;
      if (!wrapper) return;
      if (getComputedStyle(wrapper).position==="static") wrapper.style.position="relative";

      var sources = [];
      if (hd) sources.push({label:"HD Quality",url:hd,quality:"720p",ext:"mp4"});
      if (sd && sd!==hd) sources.push({label:"SD Quality",url:sd,quality:"480p",ext:"mp4"});
      sources.push({label:"MP3 Audio",url:hd||sd,quality:"audio",ext:"mp3",isMP3:true});

      var btn = makeBtn("↓ Download");
      wrapper.appendChild(btn);
      attachHover(wrapper, btn);

      btn.addEventListener("click",function(e){
        e.stopPropagation(); e.preventDefault();
        showQualityPicker(sources, function(s){
          doDownload(btn, s.url, s.quality, s.ext, "Facebook", "↓ Download");
        });
      });
    } catch(e) {}
  }

  // ══════════════════════════════════════════════════
  // TWITTER / X
  // ══════════════════════════════════════════════════
  function injectTwitterButton(videoEl) {
    if (videoEl.__tubevd_done) return;
    var w = videoEl.offsetWidth||videoEl.clientWidth;
    if (w>0&&w<100) return;
    videoEl.__tubevd_done = true;

    var wrapper = videoEl.parentElement;
    if (!wrapper) return;
    if (getComputedStyle(wrapper).position==="static") wrapper.style.position="relative";

    var btn = makeBtn("↓ Download");
    wrapper.appendChild(btn);
    attachHover(wrapper, btn);

    btn.addEventListener("click",function(e){
      e.stopPropagation(); e.preventDefault();
      var src = getBestSrc(videoEl);
      if (!src) {
        // Try to get from intercepted URLs
        chrome.runtime.sendMessage({type:"GET_STATE"},function(state){
          var vids = (state&&state.videos)||[];
          var tw = vids.filter(function(v){return v.site==="Twitter / X";});
          if (tw.length) {
            var sources = tw.map(function(v){return{label:v.quality+" "+v.type,url:v.url,quality:v.quality,ext:"mp4"};});
            sources.push({label:"MP3 Audio",url:tw[0].url,quality:"audio",ext:"mp3",isMP3:true});
            showQualityPicker(sources,function(s){doDownload(btn,s.url,s.quality,s.ext,"Twitter","↓ Download");});
          } else {
            setStatus(btn,"Not found","#e74c3c","↓ Download",2000);
          }
        });
        return;
      }
      var sources=[
        {label:"Original Quality",url:src,quality:getQuality(videoEl),ext:"mp4"},
        {label:"MP3 Audio",url:src,quality:"audio",ext:"mp3",isMP3:true},
      ];
      showQualityPicker(sources,function(s){doDownload(btn,s.url,s.quality,s.ext,"Twitter","↓ Download");});
    });
  }

  // ══════════════════════════════════════════════════
  // GENERIC (Vimeo, Dailymotion, Instagram, TikTok, others)
  // ══════════════════════════════════════════════════
  function injectGenericButton(videoEl) {
    if (videoEl.__tubevd_done) return;
    if (isYouTube()) return;
    var w = videoEl.offsetWidth||videoEl.clientWidth;
    if (w>0&&w<100) return;
    videoEl.__tubevd_done = true;

    var wrapper = videoEl.parentElement;
    if (!wrapper) return;
    if (getComputedStyle(wrapper).position==="static") wrapper.style.position="relative";

    var quality = getQuality(videoEl);
    var site = location.hostname.replace("www.","");
    var btn = makeBtn("↓ Download");
    wrapper.appendChild(btn);
    attachHover(wrapper, btn);

    btn.addEventListener("click",function(e){
      e.stopPropagation(); e.preventDefault();
      var src = getBestSrc(videoEl);

      // Build quality sources
      var sources = [];
      if (src) {
        sources.push({label:quality+" Video",url:src,quality:quality,ext:"mp4"});
        sources.push({label:"MP3 Audio",url:src,quality:"audio",ext:"mp3",isMP3:true});
      }

      // Also add any intercepted URLs for this site
      chrome.runtime.sendMessage({type:"GET_STATE"},function(state){
        var vids = (state&&state.videos)||[];
        vids.forEach(function(v){
          if (!sources.find(function(s){return s.url===v.url;})) {
            sources.push({label:v.quality+" "+v.type,url:v.url,quality:v.quality,ext:"mp4"});
          }
        });
        if (!sources.length) { setStatus(btn,"Not found","#e74c3c","↓ Download",2000); return; }
        showQualityPicker(sources,function(s){doDownload(btn,s.url,s.quality,s.ext,site,"↓ Download");});
      });
    });
  }

  // ── Route by site ────────────────────────────────
  function injectButton(videoEl) {
    if (isYouTube()) return;
    if (isFacebook())  { if (!videoEl.__tubevd_fb)   { if(videoEl.readyState>=1) injectFbButton(videoEl); else videoEl.addEventListener("loadedmetadata",function(){injectFbButton(videoEl);},{once:true}); } return; }
    if (isTwitter())   { injectTwitterButton(videoEl); return; }
    injectGenericButton(videoEl);
  }

  // ── Scan + MutationObserver ──────────────────────
  function scanAll() {
    if (isYouTube()) return;
    document.querySelectorAll("video").forEach(injectButton);
  }

  new MutationObserver(function(muts){
    muts.forEach(function(m){
      m.addedNodes.forEach(function(node){
        if(node.nodeName==="VIDEO") injectButton(node);
        if(node.querySelectorAll) node.querySelectorAll("video").forEach(injectButton);
      });
    });
  }).observe(document.documentElement,{childList:true,subtree:true});

  scanAll();
  setTimeout(scanAll,1500);
  setTimeout(scanAll,4000);
  setTimeout(scanAll,8000);
})();
