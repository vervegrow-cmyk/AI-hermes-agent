(window["webpackJsonp"] = window["webpackJsonp"] || []).push([[1],{

/***/ "./src/background/agents.js":
/*!**********************************!*\
  !*** ./src/background/agents.js ***!
  \**********************************/
/*! exports provided: get_next_agent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "get_next_agent", function() { return get_next_agent; });
/* harmony import */ var _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @babel/runtime/regenerator */ "./node_modules/@babel/runtime/regenerator/index.js");
/* harmony import */ var _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _util_etask_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! /util/etask.js */ "./util/etask.js");
/* harmony import */ var _util_etask_js__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_util_etask_js__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _util_lum_api_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../util/lum_api.js */ "./src/util/lum_api.js");
// LICENSE_CODE ZON

/*jslint browser:true, es6:true*/




var proxies = [];

var fetch_proxies = function fetch_proxies() {
  return _util_etask_js__WEBPACK_IMPORTED_MODULE_1___default()( /*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default.a.mark(function _callee() {
    return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default.a.wrap(function _callee$(_context) {
      while (1) {
        switch (_context.prev = _context.next) {
          case 0:
            _context.prev = 0;
            _context.next = 3;
            return Object(_util_lum_api_js__WEBPACK_IMPORTED_MODULE_2__["load_superagents"])();

          case 3:
            proxies = _context.sent;
            _context.next = 10;
            break;

          case 6:
            _context.prev = 6;
            _context.t0 = _context["catch"](0);
            console.warn('failed to resolve super proxies: %s', _context.t0.message);
            return _context.abrupt("return", []);

          case 10:
            return _context.abrupt("return", proxies);

          case 11:
          case "end":
            return _context.stop();
        }
      }
    }, _callee, null, [[0, 6]]);
  }));
};

var get_next_agent = function get_next_agent() {
  return _util_etask_js__WEBPACK_IMPORTED_MODULE_1___default()( /*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default.a.mark(function _callee2() {
    return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default.a.wrap(function _callee2$(_context2) {
      while (1) {
        switch (_context2.prev = _context2.next) {
          case 0:
            if (proxies.length) {
              _context2.next = 3;
              break;
            }

            _context2.next = 3;
            return fetch_proxies();

          case 3:
            return _context2.abrupt("return", proxies.pop());

          case 4:
          case "end":
            return _context2.stop();
        }
      }
    }, _callee2);
  }));
};

/***/ }),

/***/ "./src/background/analytics.js":
/*!*************************************!*\
  !*** ./src/background/analytics.js ***!
  \*************************************/
/*! exports provided: analytics_actions, perr, perr_send */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "analytics_actions", function() { return analytics_actions; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "perr", function() { return perr; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "perr_send", function() { return perr_send; });
/* harmony import */ var _rx_state_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./rx_state.js */ "./src/background/rx_state.js");
// LICENSE_CODE ZON

/*jslint browser:true, es6:true*/


var analytics_actions = Object(_rx_state_js__WEBPACK_IMPORTED_MODULE_0__["create_actions"])(['ga_send']);
var perr = function perr(id) {
  var info = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : {};
  var err = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : null;
  return null;
};
var perr_send = function perr_send(evt) {
  return null;
};

/***/ }),

/***/ "./src/background/auth.js":
/*!********************************!*\
  !*** ./src/background/auth.js ***!
  \********************************/
/*! exports provided: logout, login */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "logout", function() { return logout; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "login", function() { return login; });
/* harmony import */ var _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @babel/runtime/regenerator */ "./node_modules/@babel/runtime/regenerator/index.js");
/* harmony import */ var _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _util_etask_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! /util/etask.js */ "./util/etask.js");
/* harmony import */ var _util_etask_js__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_util_etask_js__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _util_zerr_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! /util/zerr.js */ "./util/zerr.js");
/* harmony import */ var _util_zerr_js__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(_util_zerr_js__WEBPACK_IMPORTED_MODULE_2__);
/* harmony import */ var _util_lum_api_js__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ../util/lum_api.js */ "./src/util/lum_api.js");
/* harmony import */ var _util_util_js__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ../util/util.js */ "./src/util/util.js");
/* harmony import */ var _sessions_js__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ./sessions.js */ "./src/background/sessions.js");
// LICENSE_CODE ZON

/*jslint browser:true, es6:true*/

/*global chrome*/







var logout = function logout() {
  chrome.storage.local.set({
    auth: null,
    customer: null,
    customer_loading: false,
    zones: null,
    proxy_error: null
  });
  var new_session = Object.assign({}, _sessions_js__WEBPACK_IMPORTED_MODULE_5__["initial_state"], {
    is_logged_in: false,
    customer: '',
    zone: '',
    key: ''
  });
  Object(_sessions_js__WEBPACK_IMPORTED_MODULE_5__["update_session"])(new_session, false);
};
var login = function login(account_id, token) {
  return _util_etask_js__WEBPACK_IMPORTED_MODULE_1___default()( /*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default.a.mark(function _callee() {
    var customer, zones, session, set_zone_name, set_zone;
    return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default.a.wrap(function _callee$(_context) {
      while (1) {
        switch (_context.prev = _context.next) {
          case 0:
            this.on('finally', function () {
              chrome.storage.local.set({
                customer_loading: false
              });
            });
            this.on('uncaught', function (e) {
              return _util_zerr_js__WEBPACK_IMPORTED_MODULE_2___default()(_util_zerr_js__WEBPACK_IMPORTED_MODULE_2___default.a.e2s(e));
            });
            chrome.storage.local.set({
              auth: {
                account_id: account_id,
                token: token
              },
              customer_loading: true
            });
            _context.next = 5;
            return Object(_util_lum_api_js__WEBPACK_IMPORTED_MODULE_3__["load_customer_api"])(account_id, token);

          case 5:
            customer = _context.sent;
            zones = customer.zones;
            chrome.storage.local.set({
              customer: customer,
              zones: zones
            });
            _context.next = 10;
            return Object(_util_util_js__WEBPACK_IMPORTED_MODULE_4__["get_storage"])('session', {});

          case 10:
            session = _context.sent;
            set_zone_name = session.zone || Object.keys(zones)[0];
            set_zone = zones[set_zone_name];
            if (!set_zone) _util_zerr_js__WEBPACK_IMPORTED_MODULE_2___default()('no zone object');
            _context.next = 16;
            return Object(_sessions_js__WEBPACK_IMPORTED_MODULE_5__["update_session"])({
              customer: account_id,
              zone: set_zone_name,
              key: set_zone && set_zone.password && set_zone.password[0]
            });

          case 16:
          case "end":
            return _context.stop();
        }
      }
    }, _callee, this);
  }));
};

/***/ }),

/***/ "./src/background/bg_main.js":
/*!***********************************!*\
  !*** ./src/background/bg_main.js ***!
  \***********************************/
/*! exports provided: bg_loaded */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "bg_loaded", function() { return bg_loaded; });
/* harmony import */ var rxjs__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! rxjs */ "./node_modules/rxjs/Rx.js");
/* harmony import */ var rxjs__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(rxjs__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _util_zerr_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! /util/zerr.js */ "./util/zerr.js");
/* harmony import */ var _util_zerr_js__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_util_zerr_js__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _util_util_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../util/util.js */ "./src/util/util.js");
/* harmony import */ var _rx_state_js__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./rx_state.js */ "./src/background/rx_state.js");
/* harmony import */ var _tabs_js__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ./tabs.js */ "./src/background/tabs.js");
/* harmony import */ var _sessions_js__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ./sessions.js */ "./src/background/sessions.js");
/* harmony import */ var _proxy_js__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! ./proxy.js */ "./src/background/proxy.js");
/* harmony import */ var _rpc_js__WEBPACK_IMPORTED_MODULE_7__ = __webpack_require__(/*! ./rpc.js */ "./src/background/rpc.js");
/* harmony import */ var _lum_js__WEBPACK_IMPORTED_MODULE_8__ = __webpack_require__(/*! ./lum.js */ "./src/background/lum.js");
/* harmony import */ var _icons_js__WEBPACK_IMPORTED_MODULE_9__ = __webpack_require__(/*! ./icons.js */ "./src/background/icons.js");
/* harmony import */ var _storage_js__WEBPACK_IMPORTED_MODULE_10__ = __webpack_require__(/*! ./storage.js */ "./src/background/storage.js");
/* harmony import */ var _analytics_js__WEBPACK_IMPORTED_MODULE_11__ = __webpack_require__(/*! ./analytics.js */ "./src/background/analytics.js");
// LICENSE_CODE ZON

/*jslint browser:true, es6:true*/

/*global chrome*/













_util_zerr_js__WEBPACK_IMPORTED_MODULE_1___default.a.set_level('INFO');
var debug = false;
var reducer$ = rxjs__WEBPACK_IMPORTED_MODULE_0__["Observable"].merge(Object(_rx_state_js__WEBPACK_IMPORTED_MODULE_3__["reducer_map"])(_tabs_js__WEBPACK_IMPORTED_MODULE_4__["tabs_reducer$"], 'tabs'), Object(_rx_state_js__WEBPACK_IMPORTED_MODULE_3__["reducer_map"])(_sessions_js__WEBPACK_IMPORTED_MODULE_5__["sessions_reducer$"], 'sessions'), Object(_rx_state_js__WEBPACK_IMPORTED_MODULE_3__["reducer_map"])(_proxy_js__WEBPACK_IMPORTED_MODULE_6__["proxy_reducer$"], 'proxy'), Object(_rx_state_js__WEBPACK_IMPORTED_MODULE_3__["reducer_map"])(_lum_js__WEBPACK_IMPORTED_MODULE_8__["lum_reducer$"], _lum_js__WEBPACK_IMPORTED_MODULE_8__["lum_scope"]));
function bg_loaded(install_details, just_installed) {
  bg_init().subscribe(function (state$) {
    bg_run(state$, install_details);
  });
}

function bg_init() {
  return Object(_storage_js__WEBPACK_IMPORTED_MODULE_10__["storage_load"])().map(function (s) {
    return Object(_rx_state_js__WEBPACK_IMPORTED_MODULE_3__["create_state"])(reducer$, rxjs__WEBPACK_IMPORTED_MODULE_0__["Observable"].of(s));
  });
}

function bg_run(state$, install_details) {
  var state_sync$ = state$;
  state$ = state$.observeOn(rxjs__WEBPACK_IMPORTED_MODULE_0__["Scheduler"].asap);
  var main_subscription = state$.subscribe(function (x) {
    return debug && console.log(x);
  }, function (e) {
    return _util_zerr_js__WEBPACK_IMPORTED_MODULE_1___default()(_util_zerr_js__WEBPACK_IMPORTED_MODULE_1___default.a.e2s(e));
  });
  chrome.runtime.onUpdateAvailable.addListener(function (details) {
    var d = new Date();
    d.setDate(d.getDate() + 1);
    d.setHours(4);
    d.setMinutes(0);
    var t = d.getTime() - new Date().getTime();
    setTimeout(function () {
      Object(_analytics_js__WEBPACK_IMPORTED_MODULE_11__["perr"])('reload_forced');
      chrome.runtime.reload();
    }, t);
    Object(_analytics_js__WEBPACK_IMPORTED_MODULE_11__["perr"])('reload_scheduled', {
      t: t
    });
  });
  var opt = {
    state$: state$,
    debug: debug,
    state_sync$: state_sync$,
    install_details: install_details
  };
  Object(_util_util_js__WEBPACK_IMPORTED_MODULE_2__["check_domain"])();
  var tabs_stop = Object(_tabs_js__WEBPACK_IMPORTED_MODULE_4__["tabs_run"])(opt);
  var session_stop = Object(_sessions_js__WEBPACK_IMPORTED_MODULE_5__["sessions_run"])(opt);
  var proxy_stop = Object(_proxy_js__WEBPACK_IMPORTED_MODULE_6__["proxy_run"])(opt);
  var rpc_stop = Object(_rpc_js__WEBPACK_IMPORTED_MODULE_7__["rpc_run"])(opt);
  var lum_stop = Object(_lum_js__WEBPACK_IMPORTED_MODULE_8__["lum_run"])(opt);
  var icons_stop = Object(_icons_js__WEBPACK_IMPORTED_MODULE_9__["icons_run"])(opt);
  var storage_stop = Object(_storage_js__WEBPACK_IMPORTED_MODULE_10__["storage_run"])(opt);

  Object(_storage_js__WEBPACK_IMPORTED_MODULE_10__["_storage_run"])();

  window.lum = create_popup_lum_mock(opt);
  return function () {
    main_subscription.unsubscribe();
    tabs_stop();
    session_stop();
    proxy_stop();
    rpc_stop();
    lum_stop();
    icons_stop();
    storage_stop();
  };
}

function create_popup_lum_mock(_ref) {
  var state$ = _ref.state$;
  var state_subj$ = new rxjs__WEBPACK_IMPORTED_MODULE_0__["BehaviorSubject"]({});
  state$.subscribe(state_subj$);
  var webui_tabs$ = Object(_lum_js__WEBPACK_IMPORTED_MODULE_8__["select_webui_tabs"])(state$);
  var webui_tabs_subj$ = new rxjs__WEBPACK_IMPORTED_MODULE_0__["BehaviorSubject"]([]);
  webui_tabs$.subscribe(webui_tabs_subj$);
  return {
    is_enabled: function is_enabled() {
      return state_subj$.getValue().lum.enabled;
    },
    is_authed: function is_authed() {
      return !!state_subj$.getValue().sessions.customer;
    },
    open_bext_page: function open_bext_page() {
      var state = state_subj$.getValue();
      _tabs_js__WEBPACK_IMPORTED_MODULE_4__["tabs_actions"].tab_create.next({
        url: state.lum.lum_domain + '/cp/bext',
        active: true
      });
    },
    perr: function perr(id, info) {
      return Object(_analytics_js__WEBPACK_IMPORTED_MODULE_11__["perr_send"])({
        id: id,
        info: info
      });
    },
    state$: state$
  };
}

/***/ }),

/***/ "./src/background/icons.js":
/*!*********************************!*\
  !*** ./src/background/icons.js ***!
  \*********************************/
/*! exports provided: icons_run */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "icons_run", function() { return icons_run; });
/* harmony import */ var _babel_runtime_helpers_slicedToArray__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @babel/runtime/helpers/slicedToArray */ "./node_modules/@babel/runtime/helpers/slicedToArray.js");
/* harmony import */ var _babel_runtime_helpers_slicedToArray__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_babel_runtime_helpers_slicedToArray__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var rxjs__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! rxjs */ "./node_modules/rxjs/Rx.js");
/* harmony import */ var rxjs__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(rxjs__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _proxy_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./proxy.js */ "./src/background/proxy.js");
/* harmony import */ var _lum_js__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./lum.js */ "./src/background/lum.js");
/* harmony import */ var _tabs_js__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ./tabs.js */ "./src/background/tabs.js");
// LICENSE_CODE ZON

/*jslint browser:true, es6:true*/

/*global chrome*/






var icon_cache = {};

var convert_icon = function convert_icon(src, size, on_load) {
  var off = arguments.length > 3 && arguments[3] !== undefined ? arguments[3] : 0;
  if (icon_cache[src]) return on_load(icon_cache[src]);
  var canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  var ctx = canvas.getContext('2d');
  var image = new Image();

  image.onload = function () {
    ctx.drawImage(image, 0, off);
    var image_data = ctx.getImageData(0, 0, size, size);
    icon_cache[src] = image_data;
    on_load(icon_cache[src]);
  };

  image.src = src;
};

function set_default_icon(active, tabs_ids) {
  set_icon(tabs_ids, active ? 'img/brd_48.png' : 'img/brd_48_inactive.png', 48);
}

function set_country_icon(country, tabs_ids) {
  if (window.browser) return set_default_icon(1, tabs_ids);
  set_icon(tabs_ids, 'flags/4x3/' + country + '.svg', 32, 5);
}

function set_refresh_icon(tabs_ids) {
  set_icon(tabs_ids, 'img/brd_128_refresh.png', 128);
}

function set_icon(tabs_ids, path, size, off) {
  convert_icon(path, size, function (image_data) {
    tabs_ids.forEach(function (id) {
      return chrome.browserAction.setIcon({
        imageData: image_data,
        tabId: id
      });
    });
  }, off);
}

var icons_run = function icons_run(_ref) {
  var state$ = _ref.state$;
  var lum$ = Object(_lum_js__WEBPACK_IMPORTED_MODULE_3__["select_lum_enabled"])(state$);
  var switching$ = Object(_lum_js__WEBPACK_IMPORTED_MODULE_3__["select_lum_proxy_switching"])(state$);
  var tabs$ = Object(_tabs_js__WEBPACK_IMPORTED_MODULE_4__["select_tabs_list"])(state$);
  var country$ = rxjs__WEBPACK_IMPORTED_MODULE_1__["Observable"].of({}).merge(Object(_proxy_js__WEBPACK_IMPORTED_MODULE_2__["select_proxy_echo"])(state$)).map(function (c) {
    return c || {};
  }).map(function (_ref2) {
    var country = _ref2.country;
    return (country || '').toLowerCase();
  }).distinctUntilChanged();
  var subs = lum$.combineLatest(country$, switching$, tabs$).subscribe(function (_ref3) {
    var _ref4 = _babel_runtime_helpers_slicedToArray__WEBPACK_IMPORTED_MODULE_0___default()(_ref3, 4),
        enabled = _ref4[0],
        country = _ref4[1],
        switching = _ref4[2],
        tabs = _ref4[3];

    var tabs_ids = Object.values(tabs || {}).map(function (t) {
      return t.id;
    });
    if (switching) return set_refresh_icon(tabs_ids);
    if (!enabled || !country) return set_default_icon(enabled, tabs_ids);
    set_country_icon(country, tabs_ids);
  });
  return function () {
    subs.unsubscribe();
  };
};

/***/ }),

/***/ "./src/background/lum.js":
/*!*******************************!*\
  !*** ./src/background/lum.js ***!
  \*******************************/
/*! exports provided: lum_scope, lum_actions, lum_reducer$, select_lum, select_lum_enabled, select_lum_lpm_enabled, select_lum_proxy_switching, select_webui_tabs, lum_run */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "lum_scope", function() { return lum_scope; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "lum_actions", function() { return lum_actions; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "lum_reducer$", function() { return lum_reducer$; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "select_lum", function() { return select_lum; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "select_lum_enabled", function() { return select_lum_enabled; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "select_lum_lpm_enabled", function() { return select_lum_lpm_enabled; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "select_lum_proxy_switching", function() { return select_lum_proxy_switching; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "select_webui_tabs", function() { return select_webui_tabs; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "lum_run", function() { return lum_run; });
/* harmony import */ var _babel_runtime_helpers_defineProperty__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @babel/runtime/helpers/defineProperty */ "./node_modules/@babel/runtime/helpers/defineProperty.js");
/* harmony import */ var _babel_runtime_helpers_defineProperty__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_babel_runtime_helpers_defineProperty__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var lodash__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! lodash */ "./node_modules/lodash/lodash.js");
/* harmony import */ var lodash__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(lodash__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var ua_parser_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ua-parser-js */ "./node_modules/ua-parser-js/src/ua-parser.js");
/* harmony import */ var ua_parser_js__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(ua_parser_js__WEBPACK_IMPORTED_MODULE_2__);
/* harmony import */ var rxjs__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! rxjs */ "./node_modules/rxjs/Rx.js");
/* harmony import */ var rxjs__WEBPACK_IMPORTED_MODULE_3___default = /*#__PURE__*/__webpack_require__.n(rxjs__WEBPACK_IMPORTED_MODULE_3__);
/* harmony import */ var _util_etask_js__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! /util/etask.js */ "./util/etask.js");
/* harmony import */ var _util_etask_js__WEBPACK_IMPORTED_MODULE_4___default = /*#__PURE__*/__webpack_require__.n(_util_etask_js__WEBPACK_IMPORTED_MODULE_4__);
/* harmony import */ var _util_ajax_js__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! /util/ajax.js */ "./util/ajax.js");
/* harmony import */ var _util_ajax_js__WEBPACK_IMPORTED_MODULE_5___default = /*#__PURE__*/__webpack_require__.n(_util_ajax_js__WEBPACK_IMPORTED_MODULE_5__);
/* harmony import */ var _rx_state_js__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! ./rx_state.js */ "./src/background/rx_state.js");
/* harmony import */ var _sessions_js__WEBPACK_IMPORTED_MODULE_7__ = __webpack_require__(/*! ./sessions.js */ "./src/background/sessions.js");
/* harmony import */ var _tabs_js__WEBPACK_IMPORTED_MODULE_8__ = __webpack_require__(/*! ./tabs.js */ "./src/background/tabs.js");
/* harmony import */ var _analytics_js__WEBPACK_IMPORTED_MODULE_9__ = __webpack_require__(/*! ./analytics.js */ "./src/background/analytics.js");
/* harmony import */ var _util_util_js__WEBPACK_IMPORTED_MODULE_10__ = __webpack_require__(/*! ../util/util.js */ "./src/util/util.js");
// LICENSE_CODE ZON

/*jslint browser:true, es6:true*/

/*global chrome*/












var lum_scope = 'lum';
var webui_regexp = new RegExp("https?://(".concat(_util_util_js__WEBPACK_IMPORTED_MODULE_10__["domains"].join('|'), ")/cp/bext.*"));
var initial_state = {
  enabled: false,
  proxy_switching: false,
  lum_domain: Object(_util_util_js__WEBPACK_IMPORTED_MODULE_10__["www_domain"])()
};
var lum_actions = Object(_rx_state_js__WEBPACK_IMPORTED_MODULE_6__["create_actions"])(['lum_enable', 'proxy_switching', 'lum_domain', 'lum_logout', 'lum_lpm_enable', 'lum_update_echo']);
var lum_enable = lum_actions.lum_enable,
    proxy_switching = lum_actions.proxy_switching,
    lum_domain = lum_actions.lum_domain,
    lum_logout = lum_actions.lum_logout,
    lum_lpm_enable = lum_actions.lum_lpm_enable,
    lum_update_echo = lum_actions.lum_update_echo;

var handle_lum_action = function handle_lum_action(fname) {
  return function (fval) {
    return function (state) {
      return state[fname] == fval ? state : lodash__WEBPACK_IMPORTED_MODULE_1___default.a.extend({}, state, _babel_runtime_helpers_defineProperty__WEBPACK_IMPORTED_MODULE_0___default()({}, fname, fval));
    };
  };
};

var lum_reducer$ = rxjs__WEBPACK_IMPORTED_MODULE_3__["Observable"].of(function (state) {
  return lodash__WEBPACK_IMPORTED_MODULE_1___default.a.extend({}, initial_state, state);
}).merge(lum_enable.map(handle_lum_action('enabled')), lum_lpm_enable.map(handle_lum_action('lpm_enabled')), lum_update_echo.map(handle_lum_action('lum_update_echo')), proxy_switching.map(handle_lum_action('proxy_switching')), lum_domain.map(handle_lum_action('lum_domain')), lum_logout.map(handle_lum_action('lum_logout')));
var select_lum = function select_lum(state$) {
  return state$.map(function (state) {
    return state[lum_scope];
  }).distinctUntilChanged(lodash__WEBPACK_IMPORTED_MODULE_1___default.a.isEmpty);
};
var select_lum_enabled = function select_lum_enabled(state$) {
  return select_lum(state$).map(function (_ref) {
    var enabled = _ref.enabled;
    return enabled;
  }).distinctUntilChanged();
};
var select_lum_lpm_enabled = function select_lum_lpm_enabled(state$) {
  return select_lum(state$).map(function (_ref2) {
    var lpm_enabled = _ref2.lpm_enabled;
    return lpm_enabled;
  }).distinctUntilChanged();
};
var select_lum_proxy_switching = function select_lum_proxy_switching(state$) {
  return select_lum(state$).map(function (s$) {
    return s$.proxy_switching;
  }).distinctUntilChanged();
};
var select_webui_tabs = function select_webui_tabs(state$) {
  return Object(_tabs_js__WEBPACK_IMPORTED_MODULE_8__["select_tabs_list"])(state$).filter(function (x) {
    return x !== undefined;
  }).map(function (x) {
    return lodash__WEBPACK_IMPORTED_MODULE_1___default.a.isEmpty(x) ? [] : lodash__WEBPACK_IMPORTED_MODULE_1___default.a.toArray(x).filter(function (t) {
      return t.url.match(webui_regexp);
    });
  }).distinctUntilChanged(lodash__WEBPACK_IMPORTED_MODULE_1___default.a.isEqual);
};
var lum_run = function lum_run(_ref3) {
  var state$ = _ref3.state$,
      install_details = _ref3.install_details;
  var uninstall_subs = Object(_sessions_js__WEBPACK_IMPORTED_MODULE_7__["select_session"])(state$).map(_util_util_js__WEBPACK_IMPORTED_MODULE_10__["gen_uninstall_url"]).distinctUntilChanged().subscribe(function (url) {
    chrome.runtime.setUninstallURL(url);
  });
  select_webui_tabs(state$).take(1).flatMap(function (tabs) {
    var n = _util_util_js__WEBPACK_IMPORTED_MODULE_10__["domains"].length;
    return rxjs__WEBPACK_IMPORTED_MODULE_3__["Observable"].fromPromise(_util_etask_js__WEBPACK_IMPORTED_MODULE_4___default.a["while"](function () {
      return true;
    }, [function try_catch$() {
      n--;
      return _util_ajax_js__WEBPACK_IMPORTED_MODULE_5___default()({
        url: Object(_util_util_js__WEBPACK_IMPORTED_MODULE_10__["www_domain"])() + '/status.json'
      });
    }, function () {
      if (!this.error) {
        lum_actions.lum_domain.next(Object(_util_util_js__WEBPACK_IMPORTED_MODULE_10__["www_domain"])());
        return this["break"](tabs);
      }

      Object(_analytics_js__WEBPACK_IMPORTED_MODULE_9__["perr"])('domains_fallback', {
        err: this.error.message || this.error,
        domain: Object(_util_util_js__WEBPACK_IMPORTED_MODULE_10__["www_domain"])()
      });
      Object(_util_util_js__WEBPACK_IMPORTED_MODULE_10__["domains_fallback"])();
      lum_actions.lum_domain.next(Object(_util_util_js__WEBPACK_IMPORTED_MODULE_10__["www_domain"])());
      if (n == 0) return this["break"](tabs);
    }]));
  }).subscribe(function (tabs) {
    if (!tabs.length && install_details && install_details.reason == 'install') {
      return _tabs_js__WEBPACK_IMPORTED_MODULE_8__["tabs_actions"].tab_create.next({
        url: Object(_util_util_js__WEBPACK_IMPORTED_MODULE_10__["www_domain"])() + '/cp/bext?ext_install=1'
      });
    }

    if (tabs.length) _tabs_js__WEBPACK_IMPORTED_MODULE_8__["tabs_actions"].tabs_reload.next(tabs);
  });
  start_content_script(state$);
  return function () {
    uninstall_subs.unsubscribe();
  };
};

function content_script(data) {
  if (window.lum_content_complete) return;

  function lum_updates(d) {
    if (d.navigator) {
      var _loop = function _loop(prop) {
        if (!d.navigator.hasOwnProperty(prop)) return "continue";

        navigator.__defineGetter__(prop, function () {
          if (d.navigator[prop] == '__UNDEFINED__') return undefined;
          return d.navigator[prop];
        });
      };

      for (var prop in d.navigator) {
        var _ret = _loop(prop);

        if (_ret === "continue") continue;
      }
    }

    if (d.window) {
      for (var _prop in d.window) {
        if (!d.window.hasOwnProperty(_prop)) continue;
        if (d.window[_prop] == '__UNDEFINED__') window[_prop] = undefined;else window[_prop] = d.window[_prop];
      }
    }

    if (d.patch_webgl && window.WebGLRenderingContext) patch_webgl(window.WebGLRenderingContext);
    if (d.patch_webgl && window.WebGLRenderingContext) patch_webgl(window.WebGL2RenderingContext);

    function patch_webgl(obj) {
      if (!obj) return;
      var unmasked_renderer_webgl = 0x9246;
      var unmasked_vendor_webgl = 0x9245;
      var get_param_bkp = obj.prototype.getParameter;

      obj.prototype.getParameter = function (p) {
        var is_apple = navigator.vendor.match(/Apple/);
        if (p == unmasked_vendor_webgl) return is_apple ? 'Apple Inc.' : 'WebKit';
        if (p == unmasked_renderer_webgl) return is_apple ? 'Apple A10 GPU' : 'WebKit WebGL';
        if (p == obj.VERSION) return 'WebGL 1.0 OpenGL ES 2.0 Metal - 50.8';
        return get_param_bkp.call(this, p);
      };
    }
  }

  var code = '' + '\n(function(data){' + '\n' + lum_updates.toString() + '\nlum_updates(data);' + '\n})(' + JSON.stringify(data) + ');';

  try {
    document.documentElement.setAttribute('onreset', code);
    document.documentElement.dispatchEvent(new CustomEvent('reset'));
    document.documentElement.removeAttribute('onreset');
  } catch (e) {}

  var s = document.createElement('script');
  s.type = 'text/javascript';
  s.textContent = code;
  (document.head || document.documentElement).prepend(s);
  s.remove();
  window.lum_content_complete = true;
}

var build_browser_data = function build_browser_data(ua, is_lum_enabled) {
  var navigator = {};
  var window = {};
  var patch_webgl = false;

  if (ua && is_lum_enabled) {
    navigator.userAgent = ua;
    navigator.appCodeName = ua.match(/^([^\/]*)\//)[1] || 'Mozilla';
    navigator.appVersion = ua.replace(new RegExp("^".concat(navigator.appCodeName, "/")), '');
    navigator.vendor = '';
    var parsed = ua_parser_js__WEBPACK_IMPORTED_MODULE_2___default()(ua);
    if (parsed.os.name == 'Windows') navigator.platform = 'Win32';else if (parsed.os.name == 'Linux') navigator.platform = 'Linux ' + parsed.os.version;else if (parsed.device.model) navigator.platform = parsed.device.model;else navigator.platform = parsed.os.name;
    if (parsed.device.vendor == 'Apple') navigator.vendor = 'Apple Computer, Inc.';else if (('' + parsed.device.vendor).match(/Google/) || parsed.browser.name.match(/Chrome/)) {
      navigator.vendor = 'Google Inc.';
    } else if (parsed.device.vendor) navigator.vendor = parsed.device.vendor;

    if (!parsed.browser.name.match(/Chrome/) || parsed.device.type == 'mobile') {
      window.chrome = '__UNDEFINED__';
    }

    navigator.productSub = '__UNDEFINED__';
    navigator.plugins = [];
    patch_webgl = true;
  }

  return {
    navigator: navigator,
    window: window,
    patch_webgl: patch_webgl
  };
};

var start_content_script = function start_content_script(state$) {
  var sess$ = Object(_sessions_js__WEBPACK_IMPORTED_MODULE_7__["select_session"])(state$);
  var sess_val$ = new rxjs__WEBPACK_IMPORTED_MODULE_3__["BehaviorSubject"]({});
  var sess_scrb = sess$.subscribe(sess_val$);
  var is_lum_enabled$ = select_lum_enabled(state$);
  var is_lum_enabled_val$ = new rxjs__WEBPACK_IMPORTED_MODULE_3__["BehaviorSubject"]({});
  var is_lum_enabled_scrb = is_lum_enabled$.subscribe(is_lum_enabled_val$);
  var is_lum_lpm_enabled$ = select_lum_lpm_enabled(state$);
  var is_lum_lpm_enabled_val$ = new rxjs__WEBPACK_IMPORTED_MODULE_3__["BehaviorSubject"]({});
  var is_lum_lpm_enabled_scrb = is_lum_lpm_enabled$.subscribe(is_lum_lpm_enabled_val$);

  var handle_navigation_commit = function handle_navigation_commit(det) {
    if (det.url.match(/^https?:\/\/(luminati|lum-cn)\.io/) || det.url.match(/^https?:\/\/brightdata\.com/) || det.url.match(/^chrome/) || det.tabId <= 0) {
      return;
    }

    var sess = sess_val$.getValue();
    var is_lum_enabled = is_lum_enabled_val$.getValue() || is_lum_lpm_enabled_val$.getValue();

    try {
      var sdata = build_browser_data(sess.ua, is_lum_enabled);
      var code = content_script.toString() + '\ncontent_script(' + JSON.stringify(sdata) + ')';
      chrome.tabs.executeScript(det.tabId, {
        code: code,
        allFrames: true,
        runAt: 'document_start'
      }, function () {
        return chrome.runtime.lastError;
      });
    } catch (e) {
      console.error(e);
    }
  };

  chrome.webNavigation.onCommitted.addListener(handle_navigation_commit);
  chrome.webRequest.onHeadersReceived.addListener(handle_navigation_commit, {
    urls: ['<all_urls>']
  }, ['blocking']);
  return function () {
    sess_scrb.unsubscribe();
    is_lum_enabled_scrb.unsubscribe();
    is_lum_lpm_enabled_scrb.unsubscribe();
    chrome.webNavigation.onCommitted.removeListener(handle_navigation_commit);
    chrome.webRequest.onHeadersReceived.removeListener(handle_navigation_commit);
  };
};

/***/ }),

/***/ "./src/background/proxy.js":
/*!*********************************!*\
  !*** ./src/background/proxy.js ***!
  \*********************************/
/*! exports provided: calc_proxy, set_proxy, update_echo, proxy_reducer$, select_proxy, select_proxy_echo, proxy_run, get_username, get_password */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "calc_proxy", function() { return calc_proxy; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "set_proxy", function() { return set_proxy; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "update_echo", function() { return update_echo; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "proxy_reducer$", function() { return proxy_reducer$; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "select_proxy", function() { return select_proxy; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "select_proxy_echo", function() { return select_proxy_echo; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "proxy_run", function() { return proxy_run; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "get_username", function() { return get_username; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "get_password", function() { return get_password; });
/* harmony import */ var _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @babel/runtime/regenerator */ "./node_modules/@babel/runtime/regenerator/index.js");
/* harmony import */ var _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var rxjs__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! rxjs */ "./node_modules/rxjs/Rx.js");
/* harmony import */ var rxjs__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(rxjs__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var lodash__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! lodash */ "./node_modules/lodash/lodash.js");
/* harmony import */ var lodash__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(lodash__WEBPACK_IMPORTED_MODULE_2__);
/* harmony import */ var _util_etask_js__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! /util/etask.js */ "./util/etask.js");
/* harmony import */ var _util_etask_js__WEBPACK_IMPORTED_MODULE_3___default = /*#__PURE__*/__webpack_require__.n(_util_etask_js__WEBPACK_IMPORTED_MODULE_3__);
/* harmony import */ var _util_url_js__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! /util/url.js */ "./util/url.js");
/* harmony import */ var _util_url_js__WEBPACK_IMPORTED_MODULE_4___default = /*#__PURE__*/__webpack_require__.n(_util_url_js__WEBPACK_IMPORTED_MODULE_4__);
/* harmony import */ var _util_zerr_js__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! /util/zerr.js */ "./util/zerr.js");
/* harmony import */ var _util_zerr_js__WEBPACK_IMPORTED_MODULE_5___default = /*#__PURE__*/__webpack_require__.n(_util_zerr_js__WEBPACK_IMPORTED_MODULE_5__);
/* harmony import */ var _util_util_js__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! ../util/util.js */ "./src/util/util.js");
/* harmony import */ var _util_lum_api_js__WEBPACK_IMPORTED_MODULE_7__ = __webpack_require__(/*! ../util/lum_api.js */ "./src/util/lum_api.js");
/* harmony import */ var _agents_js__WEBPACK_IMPORTED_MODULE_8__ = __webpack_require__(/*! ./agents.js */ "./src/background/agents.js");
/* harmony import */ var _analytics_js__WEBPACK_IMPORTED_MODULE_9__ = __webpack_require__(/*! ./analytics.js */ "./src/background/analytics.js");
// LICENSE_CODE ZON

/*jslint browser:true, es6:true*/

/*global chrome*/











var state_subj$ = new rxjs__WEBPACK_IMPORTED_MODULE_1__["BehaviorSubject"]();
var state_extender = new rxjs__WEBPACK_IMPORTED_MODULE_1__["Subject"]();
var state_extender$ = state_extender.map(function (update) {
  return function (state) {
    return lodash__WEBPACK_IMPORTED_MODULE_2___default.a.extend({}, state, update);
  };
});
var d_names = _util_util_js__WEBPACK_IMPORTED_MODULE_6__["domains"].map(function (d) {
  return d.split('.')[0];
});
var bypass_domains = [new RegExp("(?<!^trigger.)(lum-ext|".concat(d_names.join('|'), ").(io|com)")), /hola\.org/, /localhost/, /127\.0\.0\.1/, /luminati-holanetworksltd\.netdna-ssl\.com/];
var system_domains = [/lumtest\.com/, /trigger\.domain/];

var generate_pac = function generate_pac() {
  var create_pac_engine = function create_pac_engine() {
    return {
      url_proxy_map: {},
      req_since_clean: 0,
      hex_decode: function hex_decode(h) {
        var s = '';

        for (var i = 0; i < h.length; i += 2) {
          s += String.fromCharCode(parseInt(h.substr(i, 2), 16));
        }

        return decodeURIComponent(escape(s));
      },
      decode_local_url: function decode_local_url(url) {
        var parts = null;

        try {
          if (parts = url.match(/^https:\/\/(.*).local.luminati\/?$/)) parts = JSON.parse(pac.hex_decode(parts[1]));
        } catch (e) {
          return null;
        }

        return parts;
      },
      handle_local: function handle_local(url) {
        var resp = 'PROXY 127.0.0.1:0';
        var conf = pac.decode_local_url(url);
        if (!conf) return resp;
        var local = pac.url_proxy_map[conf.u] || {
          count: 0
        };
        local.ts = Date.now();
        local.count++;
        local.proxy_str = conf.p;
        pac.url_proxy_map[conf.u] = local;
        return resp;
      },
      handle_proxy: function handle_proxy(url) {
        var curr_ts = Date.now();
        if (!pac.url_proxy_map[url]) return 'DIRECT';
        var proxy = pac.url_proxy_map[url];

        if (!proxy.count || curr_ts - proxy.ts > 2000) {
          delete pac.url_proxy_map[url];
          return 'DIRECT';
        }

        proxy.count--;
        if (!proxy.count) delete pac.url_proxy_map[url];
        return proxy.proxy_str;
      },
      clean_map: function clean_map() {
        var cur_ts = Date.now();

        for (var i in pac.url_proxy_map) {
          var local = pac.url_proxy_map[i];
          if (cur_ts - local.ts > 10000) delete pac.url_proxy_map[i];
        }

        pac.req_since_clean = 0;
      },
      find_proxy_for_url: function find_proxy_for_url(url, host) {
        if (host.match(/^(.*)\.local\.luminati$/)) return pac.handle_local(url);
        if (!pac.req_since_clean % 1000) pac.clean_map();
        pac.req_since_clean++;
        return pac.handle_proxy(url);
      }
    };
  };

  var pac = 'var create_pac_engine = ' + create_pac_engine.toString() + '\nvar pac = create_pac_engine();' + '\nvar is_luminati = true;' + '\nfunction FindProxyForURL(url, host){' + '\nreturn pac.find_proxy_for_url(url, host); }';
  return pac;
};

var initial_state = {
  proxy: 'DIRECT'
};

function on_proxy_error(err) {
  var ignores = ['net::ERR_PROXY_CONNECTION_FAILED', 'net::ERR_TUNNEL_CONNECTION_FAILED', 'net::ERR_CONNECTION_CLOSED', 'net::ERR_CONNECTION_RESET', 'net::ERR_TIMED_OUT'];
  if (ignores.includes(err.error)) return;
  console.error(err.error);
}

var set_pac = function set_pac(proxy) {
  return _util_etask_js__WEBPACK_IMPORTED_MODULE_3___default()( /*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default.a.mark(function _callee() {
    var conf;
    return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default.a.wrap(function _callee$(_context) {
      while (1) {
        switch (_context.prev = _context.next) {
          case 0:
            _util_zerr_js__WEBPACK_IMPORTED_MODULE_5___default.a.info('setting proxy: %s', proxy);
            conf = {
              value: {
                mode: 'system'
              }
            };

            if (proxy != 'DIRECT') {
              conf.value = {
                mode: 'pac_script',
                pacScript: {
                  data: generate_pac(),
                  mandatory: true
                }
              };
            }

            conf.scope = chrome.extension.inIncognitoContext ? 'incognito_session_only' : 'regular';
            chrome.proxy.settings.set(conf, this.continue_fn());
            if (proxy == 'DIRECT') chrome.proxy.settings.clear({}, this.continue_fn());
            _context.next = 8;
            return this.wait();

          case 8:
            return _context.abrupt("return", _context.sent);

          case 9:
          case "end":
            return _context.stop();
        }
      }
    }, _callee, this);
  }));
};

var calc_proxy = function calc_proxy(session, enabled, agent) {
  if (session.lpm_enabled) {
    if (!session.lpm_server) throw new Error('lpm server missing');
    var split = session.lpm_server.split(':');
    if (enabled && split[1]) return "PROXY ".concat(split[1].replace('//', ''), ":").concat(session.lpm_port);
    return 'DIRECT';
  }

  if (agent && enabled && session.customer && session.zone) return "PROXY ".concat(agent, ":22225");
  if (enabled) console.error('proxy enabled with no customer or zone');
  return 'DIRECT';
};
var set_proxy = function set_proxy(session, enabled) {
  return _util_etask_js__WEBPACK_IMPORTED_MODULE_3___default()( /*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default.a.mark(function _callee2() {
    var _this = this;

    var agent, proxy, echo;
    return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default.a.wrap(function _callee2$(_context2) {
      while (1) {
        switch (_context2.prev = _context2.next) {
          case 0:
            this.on('uncaught', function (e) {
              uninstall_handlers();
              proxy = 'DIRECT';
              set_pac(proxy);
              state_extender.next({
                proxy: proxy
              });
              chrome.storage.local.set({
                proxy: proxy
              });
              var err = e && (e.x_error || e.message);

              _this["return"]({
                proxy: proxy,
                echo: {
                  err: err
                }
              });
            });

            if (session.lpm_enabled) {
              _context2.next = 10;
              break;
            }

            if (!enabled) {
              _context2.next = 8;
              break;
            }

            _context2.next = 5;
            return Object(_agents_js__WEBPACK_IMPORTED_MODULE_8__["get_next_agent"])();

          case 5:
            _context2.t0 = _context2.sent;
            _context2.next = 9;
            break;

          case 8:
            _context2.t0 = null;

          case 9:
            agent = _context2.t0;

          case 10:
            agent = agent && agent.replace('brightdata.com', 'luminati.io');
            proxy = calc_proxy(session, enabled, agent);
            _context2.next = 14;
            return set_pac(proxy);

          case 14:
            uninstall_handlers();
            if (proxy != 'DIRECT') install_handlers(proxy, session);
            state_extender.next({
              proxy: proxy
            });
            chrome.storage.local.set({
              proxy: proxy
            });
            _context2.next = 20;
            return update_echo();

          case 20:
            echo = _context2.sent;
            return _context2.abrupt("return", {
              proxy: proxy,
              echo: echo
            });

          case 22:
          case "end":
            return _context2.stop();
        }
      }
    }, _callee2, this);
  }));
};
var update_echo = function update_echo() {
  return _util_etask_js__WEBPACK_IMPORTED_MODULE_3___default()( /*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default.a.mark(function _callee3() {
    var echo;
    return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default.a.wrap(function _callee3$(_context3) {
      while (1) {
        switch (_context3.prev = _context3.next) {
          case 0:
            _context3.next = 2;
            return Object(_util_lum_api_js__WEBPACK_IMPORTED_MODULE_7__["test_echo"])();

          case 2:
            echo = _context3.sent;
            state_extender.next({
              echo: echo
            });
            chrome.storage.local.set({
              echo: echo
            });
            return _context3.abrupt("return", echo);

          case 6:
          case "end":
            return _context3.stop();
        }
      }
    }, _callee3);
  }));
};
var proxy_reducer$ = rxjs__WEBPACK_IMPORTED_MODULE_1__["Observable"].of(function () {
  return initial_state;
}).merge(state_extender$);
var select_proxy = function select_proxy(state$) {
  return state$.map(function (state) {
    return state.proxy;
  }).distinctUntilChanged(lodash__WEBPACK_IMPORTED_MODULE_2___default.a.isEqual);
};
var select_proxy_echo = function select_proxy_echo(state$) {
  return select_proxy(state$).map(function (_ref) {
    var echo = _ref.echo;
    return echo;
  }).distinctUntilChanged(lodash__WEBPACK_IMPORTED_MODULE_2___default.a.isEqual);
};
var proxy_run = function proxy_run(_ref2) {
  var state$ = _ref2.state$;
  var stop_state = state$.subscribe(state_subj$);
  return function () {
    stop_state();
  };
};

function handle_proxy_request(det, proxy, tab, session) {
  if (det.url.includes('http://' + proxy.split(':')[0].replace('PROXY ', ''))) return;
  if (det.url.includes(':22999')) return;
  set_proxy_for_url(det.url, proxy, tab.url);
}

var HTTPS_DOMAIN = new RegExp('^(https://[^/]+/)');

var set_proxy_for_url = function set_proxy_for_url(url, proxy_str, tab_url) {
  if (!chrome.proxy.onProxyError) return; // from chrome 52 https requests truncate the path when passed to PAC

  var n = url.match(HTTPS_DOMAIN);
  if (n) url = n[1];
  /* we use sync request to make sure the url is set in the pac before we
   * proceed with the request, async requests work most of the time.
   * in test, the mock XMLHTTPRequest implements sync requests by spawning
   * another instance of node, which prevents us from using nock, which
   * needs to overrides node's Request, but doesn't override Request of the
   * spawned node, so we use async in this case. */

  var prefix = Object(_util_util_js__WEBPACK_IMPORTED_MODULE_6__["hex_encode"])(JSON.stringify({
    p: proxy_str,
    u: url
  })); // XXX georgy: snippet to debug proxy requests

  var suffix = false ? undefined : '';
  var xhr = new XMLHttpRequest();
  var encoded_url = 'https://' + prefix + '.local.luminati/' + suffix;
  xhr.open('POST', encoded_url, false);
  var t0 = Date.now();

  try {
    xhr.send(null);
  } catch (e) {}

  var diff = Date.now() - t0;
  if (diff > 100) Object(_analytics_js__WEBPACK_IMPORTED_MODULE_9__["perr"])('proxy_for_url_slow', {
    label: diff,
    proxy_str: proxy_str,
    url: url
  });
};

var last_auth_id = 0;
var request_listener;
var on_auth_required;
var handle_headers;

function uninstall_handlers() {
  if (request_listener) chrome.webRequest.onBeforeRequest.removeListener(request_listener);
  if (on_auth_required) chrome.webRequest.onAuthRequired.removeListener(on_auth_required); // chrome uses proxy.onProxyError and firefox uses proxy.onError

  if (chrome.proxy.onProxyError) chrome.proxy.onProxyError.removeListener(on_proxy_error);else if (chrome.proxy.onError) chrome.proxy.onError.removeListener(on_proxy_error);
  if (handle_headers) chrome.webRequest.onBeforeSendHeaders.removeListener(handle_headers);

  if (chrome.privacy.network.webRTCIPHandlingPolicy && chrome.privacy.IPHandlingPolicy) {
    chrome.privacy.network.webRTCIPHandlingPolicy.set({
      value: chrome.privacy.IPHandlingPolicy.DEFAULT,
      scope: chrome.extension.inIncognitoContext ? 'incognito_session_only' : 'regular'
    });
  }

  if (window.browser) window.browser.proxy.onRequest.removeListener(on_proxy_request);
}

function should_bypass(url, tab, domain_whitelist, domain_blacklist) {
  if (!tab) return true;
  if (!url.match(/^https?/)) return true;
  var host = _util_url_js__WEBPACK_IMPORTED_MODULE_4___default.a.get_host(url);
  var blacklisted = bypass_domains.filter(function (b) {
    return host.match(b);
  }).length || domain_blacklist.filter(function (b) {
    return host.match(new RegExp(b));
  }).length;
  var should_whitelist = domain_whitelist && domain_whitelist.length > 0;
  var whitelisted = should_whitelist && !!lodash__WEBPACK_IMPORTED_MODULE_2___default.a.find(domain_whitelist || [], function (d) {
    return new RegExp(d).test(host);
  });
  return !whitelisted && blacklisted;
}

function is_system_request(det) {
  var host = _util_url_js__WEBPACK_IMPORTED_MODULE_4___default.a.get_host(det.url);
  return det.tabId == -1 && det.type == 'xmlhttprequest' && system_domains.filter(function (s) {
    return host.match(s);
  }).length;
}

var get_username = function get_username(opt) {
  if (opt.lpm_enabled && opt.lpm_email) return opt.lpm_email.replace('@', ',');
  var username = 'lum-customer-';
  username += (opt.customer || '').replace(/^lum-customer-/, '');
  if (!username.includes('-zone-' + opt.zone)) username += '-zone-' + opt.zone;
  if (opt.gip) username += '-gip-' + opt.gip;
  if (opt.country && opt.country != 'disabled' && opt.country.length == 2) username += '-country-' + Object(_util_util_js__WEBPACK_IMPORTED_MODULE_6__["format_part"])(opt.country.toLowerCase());

  if (opt.state && opt.state != 'disabled' || opt.city && lodash__WEBPACK_IMPORTED_MODULE_2___default.a.isObject(opt.city)) {
    username += '-state-' + Object(_util_util_js__WEBPACK_IMPORTED_MODULE_6__["format_part"])(lodash__WEBPACK_IMPORTED_MODULE_2___default.a.isObject(opt.city) ? opt.city.state : opt.state);
  }

  if (opt.city && opt.city != 'disabled') {
    username += '-city-' + Object(_util_util_js__WEBPACK_IMPORTED_MODULE_6__["format_part"])(lodash__WEBPACK_IMPORTED_MODULE_2___default.a.isObject(opt.city) ? opt.city.name : opt.city);
  }

  if (opt.asn && opt.asn != 'disabled') username += '-asn-' + Object(_util_util_js__WEBPACK_IMPORTED_MODULE_6__["format_part"])('' + opt.asn);
  if (opt.session) username += '-session-' + Object(_util_util_js__WEBPACK_IMPORTED_MODULE_6__["format_part"])(opt.session);
  if (opt.mobile && opt.mobile != 'disabled') username += '-mobile-' + opt.mobile;
  if (opt.direct) username += '-direct';
  if (opt.dns && opt.dns != 'disabled') username += '-dns-' + Object(_util_util_js__WEBPACK_IMPORTED_MODULE_6__["format_part"])(opt.dns);
  if (opt.ip && opt.ip != 'disabled') username += '-ip-' + Object(_util_util_js__WEBPACK_IMPORTED_MODULE_6__["format_part"])(opt.ip);
  if (opt.carrier && opt.carrier != 'disabled') username += '-carrier-' + Object(_util_util_js__WEBPACK_IMPORTED_MODULE_6__["format_part"])(opt.carrier);
  if (opt.vip && opt.vip != 'disabled') username += '-vip-' + Object(_util_util_js__WEBPACK_IMPORTED_MODULE_6__["format_part"])(opt.vip);
  username += '-agent-bext-agentver-' + Object(_util_util_js__WEBPACK_IMPORTED_MODULE_6__["version"])();
  return username;
};
var get_password = function get_password(session) {
  if (session.lpm_enabled && session.lpm_password) return session.lpm_password;
  return session.key;
};
var current_host;

var on_proxy_request = function on_proxy_request(det) {
  if (!current_host) return _util_zerr_js__WEBPACK_IMPORTED_MODULE_5___default()('current host not defined');

  if (is_system_request(det)) {
    _util_zerr_js__WEBPACK_IMPORTED_MODULE_5___default.a.info('system_request: %s', det.url);
    return {
      type: 'http',
      host: current_host,
      port: 22225
    };
  }

  if (should_bypass(det.url, true, [], [])) {
    _util_zerr_js__WEBPACK_IMPORTED_MODULE_5___default.a.debug('bypass: %s', det.url);
    return {
      type: 'direct'
    };
  }

  _util_zerr_js__WEBPACK_IMPORTED_MODULE_5___default.a.info("Proxying: ".concat(det.url));
  return {
    type: 'http',
    host: current_host,
    port: 22225
  };
};

function install_handlers(proxy, session) {
  // chrome uses proxy.onProxyError and firefox uses proxy.onError
  if (chrome.proxy.onProxyError) chrome.proxy.onProxyError.addListener(on_proxy_error);else if (chrome.proxy.onError) chrome.proxy.onError.addListener(on_proxy_error);

  request_listener = function request_listener(det) {
    if (det.url.match(/^chrome-extension?/)) return;

    if (is_system_request(det)) {
      _util_zerr_js__WEBPACK_IMPORTED_MODULE_5___default.a.info('system_request: %s', det.url);
      return set_proxy_for_url(det.url, proxy);
    }

    var state = state_subj$.getValue();
    var tabs = state.tabs.tabs || {};
    var tab = tabs[det.tabId];
    if (!tab && (det.type == 'main_frame' || det.tabId != -1)) tab = {
      id: det.tabId,
      url: det.url
    };

    if (should_bypass(det.url, tab, session.domain_whitelist, session.domain_blacklist || [])) {
      return _util_zerr_js__WEBPACK_IMPORTED_MODULE_5___default.a.debug('bypass: %s', det.url);
    }

    _util_zerr_js__WEBPACK_IMPORTED_MODULE_5___default.a.info('proxy: %s', det.url);
    return handle_proxy_request(det, proxy, tab, session);
  };

  if (window.browser) {
    var proxy_regexp = new RegExp('^PROXY (.+):(.+)');
    current_host = proxy.match(proxy_regexp)[1];
    window.browser.proxy.onRequest.addListener(on_proxy_request, {
      urls: ['<all_urls>']
    });
  }

  chrome.webRequest.onBeforeRequest.addListener(request_listener, {
    urls: ['<all_urls>']
  }, ['blocking']);

  on_auth_required = function on_auth_required(det) {
    if (last_auth_id == det.requestId) {
      Object(_analytics_js__WEBPACK_IMPORTED_MODULE_9__["perr"])('auth_error', {
        req_id: last_auth_id
      });
      if (det.isProxy) return {
        cancel: true
      };
    }

    last_auth_id = det.requestId;
    var username = get_username(session);
    var password = get_password(session);

    if (det.isProxy) {
      _util_zerr_js__WEBPACK_IMPORTED_MODULE_5___default.a.info('using auth: %s:%s', username, password);
      return {
        authCredentials: {
          username: username,
          password: password
        }
      };
    }
  };

  chrome.webRequest.onAuthRequired.addListener(on_auth_required, {
    urls: ['<all_urls>']
  }, ['blocking']);

  handle_headers = function handle_headers(det) {
    var headers = session.ua ? [{
      name: 'user-agent',
      value: session.ua
    }] : [];

    var _loop = function _loop(i) {
      var header = lodash__WEBPACK_IMPORTED_MODULE_2___default.a.find(det.requestHeaders, function (_ref3) {
        var name = _ref3.name;
        return name.toLowerCase() == headers[i].name.toLowerCase();
      });

      if (header) header.value = headers[i].value;else det.requestHeaders.push(lodash__WEBPACK_IMPORTED_MODULE_2___default.a.pick(headers[i], 'name', 'value'));
    };

    for (var i = 0; i < headers.length; i++) {
      _loop(i);
    }

    return {
      requestHeaders: det.requestHeaders
    };
  };

  chrome.webRequest.onBeforeSendHeaders.addListener(handle_headers, {
    urls: ['<all_urls>']
  }, ['blocking', 'requestHeaders']);

  if (chrome.privacy.network.webRTCIPHandlingPolicy && chrome.privacy.IPHandlingPolicy) {
    chrome.privacy.network.webRTCIPHandlingPolicy.set({
      value: chrome.privacy.IPHandlingPolicy.DISABLE_NON_PROXIED_UDP,
      scope: chrome.extension.inIncognitoContext ? 'incognito_session_only' : 'regular'
    });
  }
}

/***/ }),

/***/ "./src/background/rpc.js":
/*!*******************************!*\
  !*** ./src/background/rpc.js ***!
  \*******************************/
/*! exports provided: rpc_run */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "rpc_run", function() { return rpc_run; });
/* harmony import */ var _babel_runtime_helpers_typeof__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @babel/runtime/helpers/typeof */ "./node_modules/@babel/runtime/helpers/typeof.js");
/* harmony import */ var _babel_runtime_helpers_typeof__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_babel_runtime_helpers_typeof__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @babel/runtime/regenerator */ "./node_modules/@babel/runtime/regenerator/index.js");
/* harmony import */ var _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var regenerator_runtime__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! regenerator-runtime */ "./node_modules/regenerator-runtime/runtime.js");
/* harmony import */ var regenerator_runtime__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(regenerator_runtime__WEBPACK_IMPORTED_MODULE_2__);
/* harmony import */ var rxjs__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! rxjs */ "./node_modules/rxjs/Rx.js");
/* harmony import */ var rxjs__WEBPACK_IMPORTED_MODULE_3___default = /*#__PURE__*/__webpack_require__.n(rxjs__WEBPACK_IMPORTED_MODULE_3__);
/* harmony import */ var _util_etask_js__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! /util/etask.js */ "./util/etask.js");
/* harmony import */ var _util_etask_js__WEBPACK_IMPORTED_MODULE_4___default = /*#__PURE__*/__webpack_require__.n(_util_etask_js__WEBPACK_IMPORTED_MODULE_4__);
/* harmony import */ var _util_zerr_js__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! /util/zerr.js */ "./util/zerr.js");
/* harmony import */ var _util_zerr_js__WEBPACK_IMPORTED_MODULE_5___default = /*#__PURE__*/__webpack_require__.n(_util_zerr_js__WEBPACK_IMPORTED_MODULE_5__);
/* harmony import */ var _sessions_js__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! ./sessions.js */ "./src/background/sessions.js");
/* harmony import */ var _proxy_js__WEBPACK_IMPORTED_MODULE_7__ = __webpack_require__(/*! ./proxy.js */ "./src/background/proxy.js");
/* harmony import */ var _auth_js__WEBPACK_IMPORTED_MODULE_8__ = __webpack_require__(/*! ./auth.js */ "./src/background/auth.js");
// LICENSE_CODE ZON

/*jslint browser:true, es6:true*/

/*global chrome*/










var ports = {};

function port_send(port, msg) {
  try {
    port.postMessage(msg);
  } catch (e) {
    console.info(e.message, port, msg);
  }
}

var handle_rpc = function handle_rpc(msg, port) {
  _util_zerr_js__WEBPACK_IMPORTED_MODULE_5___default.a.info('rpc call: %s', msg.procedure);

  switch (msg.procedure) {
    case 'switch_ip':
      _util_etask_js__WEBPACK_IMPORTED_MODULE_4___default()( /*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default.a.mark(function _callee() {
        var res, err;
        return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default.a.wrap(function _callee$(_context) {
          while (1) {
            switch (_context.prev = _context.next) {
              case 0:
                _context.next = 2;
                return _sessions_js__WEBPACK_IMPORTED_MODULE_6__["session_switch_ip"]();

              case 2:
                res = _context.sent;
                err = get_err(res.echo.err);
                port_send(port, {
                  topic: 'switch_ip',
                  data: err ? {
                    err: err
                  } : {
                    ok: true
                  }
                });

              case 5:
              case "end":
                return _context.stop();
            }
          }
        }, _callee);
      }));
      break;

    case 'set_lum_enable':
      // XXX get rid of replying on rpc
      _util_etask_js__WEBPACK_IMPORTED_MODULE_4___default()( /*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default.a.mark(function _callee2() {
        var res, err;
        return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default.a.wrap(function _callee2$(_context2) {
          while (1) {
            switch (_context2.prev = _context2.next) {
              case 0:
                _context2.next = 2;
                return _sessions_js__WEBPACK_IMPORTED_MODULE_6__["update_session"]({
                  lpm_enabled: false
                }, msg.args[0]);

              case 2:
                res = _context2.sent;
                err = get_err(res.echo.err);
                port_send(port, {
                  topic: 'session_changed',
                  data: err ? {
                    err: err
                  } : {
                    ok: true
                  }
                });

              case 5:
              case "end":
                return _context2.stop();
            }
          }
        }, _callee2);
      }));
      break;

    case 'toggle_lum':
      // XXX get rid of replying on rpc
      _util_etask_js__WEBPACK_IMPORTED_MODULE_4___default()( /*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default.a.mark(function _callee3() {
        var res, err;
        return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default.a.wrap(function _callee3$(_context3) {
          while (1) {
            switch (_context3.prev = _context3.next) {
              case 0:
                _context3.next = 2;
                return _sessions_js__WEBPACK_IMPORTED_MODULE_6__["toggle_lum"]();

              case 2:
                res = _context3.sent;
                err = get_err(res.echo.err);
                port_send(port, {
                  topic: 'session_changed',
                  data: err ? {
                    err: err
                  } : {
                    ok: true
                  }
                });

              case 5:
              case "end":
                return _context3.stop();
            }
          }
        }, _callee3);
      }));
      break;

    case 'toggle_lpm':
      // XXX get rid of replying on rpc
      _util_etask_js__WEBPACK_IMPORTED_MODULE_4___default()( /*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default.a.mark(function _callee4() {
        var res, err;
        return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default.a.wrap(function _callee4$(_context4) {
          while (1) {
            switch (_context4.prev = _context4.next) {
              case 0:
                _context4.next = 2;
                return _sessions_js__WEBPACK_IMPORTED_MODULE_6__["toggle_lpm"]();

              case 2:
                res = _context4.sent;
                err = get_err(res.echo.err);
                port_send(port, {
                  topic: 'session_changed',
                  data: err ? {
                    err: err
                  } : {
                    ok: true
                  }
                });

              case 5:
              case "end":
                return _context4.stop();
            }
          }
        }, _callee4);
      }));
      break;

    case 'set_lpm_enable':
      _sessions_js__WEBPACK_IMPORTED_MODULE_6__["update_session"]({
        lpm_enabled: msg.args[0]
      }, msg.args[0]);
      break;

    case 'update_echo':
      Object(_proxy_js__WEBPACK_IMPORTED_MODULE_7__["update_echo"])();
      break;

    case 'login':
      _auth_js__WEBPACK_IMPORTED_MODULE_8__["login"](msg.account_id || msg.args[0], msg.token || msg.args[1]);
      break;

    case 'logout':
      {
        _auth_js__WEBPACK_IMPORTED_MODULE_8__["logout"]();
        break;
      }

    case 'update_session':
      session_change(port, msg.args[0]);
      break;
  }
};

var rpc_run = function rpc_run(_ref) {
  var state$ = _ref.state$;
  var state_subj$ = new rxjs__WEBPACK_IMPORTED_MODULE_3__["BehaviorSubject"]({});
  var state_subs = state$.subscribe(state_subj$);

  var port_handler = function port_handler(port) {
    return _util_etask_js__WEBPACK_IMPORTED_MODULE_4___default()( /*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default.a.mark(function _callee5() {
      var _this = this;

      var send_state_subs;
      return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default.a.wrap(function _callee5$(_context5) {
        while (1) {
          switch (_context5.prev = _context5.next) {
            case 0:
              if (port.name.startsWith('lum_bext_')) {
                _context5.next = 2;
                break;
              }

              return _context5.abrupt("return");

            case 2:
              ports[port.name] = port;
              port.onDisconnect.addListener(function () {
                if (send_state_subs) send_state_subs.unsubscribe();
                delete ports[port.name];

                _this["continue"]();
              });
              port.onMessage.addListener(function (msg) {
                if (msg.procedure) return handle_rpc(msg, port);
              });
              _context5.next = 7;
              return this.wait();

            case 7:
              return _context5.abrupt("return", _context5.sent);

            case 8:
            case "end":
              return _context5.stop();
          }
        }
      }, _callee5, this);
    }));
  };

  chrome.runtime.onConnect.addListener(port_handler);
  return function () {
    chrome.runtime.onConnect.removeListener(port_handler);
    state_subs.unsubscribe();
  };
};

var session_change = function session_change(port, session) {
  return _util_etask_js__WEBPACK_IMPORTED_MODULE_4___default()( /*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default.a.mark(function _callee6() {
    var enable, res, err;
    return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default.a.wrap(function _callee6$(_context6) {
      while (1) {
        switch (_context6.prev = _context6.next) {
          case 0:
            enable = session.country ? true : undefined;
            _context6.next = 3;
            return _sessions_js__WEBPACK_IMPORTED_MODULE_6__["update_session"](session, enable);

          case 3:
            res = _context6.sent;
            err = get_err(res.echo.err);
            port_send(port, {
              topic: 'session_changed',
              data: err ? {
                err: err
              } : {
                ok: true
              }
            });

          case 6:
          case "end":
            return _context6.stop();
        }
      }
    }, _callee6);
  }));
};

var get_err = function get_err(err) {
  if (err && _babel_runtime_helpers_typeof__WEBPACK_IMPORTED_MODULE_0___default()(err) == 'object') return err.x_error || err.stack || err.message || err.toString();
  return err;
};

/***/ }),

/***/ "./src/background/rx_state.js":
/*!************************************!*\
  !*** ./src/background/rx_state.js ***!
  \************************************/
/*! exports provided: create_actions, create_state, reducer_map */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "create_actions", function() { return create_actions; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "create_state", function() { return create_state; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "reducer_map", function() { return reducer_map; });
/* harmony import */ var _babel_runtime_helpers_slicedToArray__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @babel/runtime/helpers/slicedToArray */ "./node_modules/@babel/runtime/helpers/slicedToArray.js");
/* harmony import */ var _babel_runtime_helpers_slicedToArray__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_babel_runtime_helpers_slicedToArray__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _babel_runtime_helpers_defineProperty__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @babel/runtime/helpers/defineProperty */ "./node_modules/@babel/runtime/helpers/defineProperty.js");
/* harmony import */ var _babel_runtime_helpers_defineProperty__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_babel_runtime_helpers_defineProperty__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var lodash__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! lodash */ "./node_modules/lodash/lodash.js");
/* harmony import */ var lodash__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(lodash__WEBPACK_IMPORTED_MODULE_2__);
/* harmony import */ var rxjs__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! rxjs */ "./node_modules/rxjs/Rx.js");
/* harmony import */ var rxjs__WEBPACK_IMPORTED_MODULE_3___default = /*#__PURE__*/__webpack_require__.n(rxjs__WEBPACK_IMPORTED_MODULE_3__);
// LICENSE_CODE ZON

/*jslint browser:true, es6:true, react:true*/





function create_actions(action_names) {
  return action_names.reduce(function (akk, name) {
    return Object(lodash__WEBPACK_IMPORTED_MODULE_2__["extend"])({}, akk, _babel_runtime_helpers_defineProperty__WEBPACK_IMPORTED_MODULE_1___default()({}, name, new rxjs__WEBPACK_IMPORTED_MODULE_3__["Subject"]()));
  }, {});
}
function create_state(reducer$) {
  var initial_state$ = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : rxjs__WEBPACK_IMPORTED_MODULE_3__["Observable"].of({});
  return initial_state$.concat(reducer$).scan(function (state, _ref) {
    var _ref2 = _babel_runtime_helpers_slicedToArray__WEBPACK_IMPORTED_MODULE_0___default()(_ref, 2),
        scope = _ref2[0],
        reducer = _ref2[1];

    if (!scope) return reducer(state);
    return Object(lodash__WEBPACK_IMPORTED_MODULE_2__["extend"])({}, state, _babel_runtime_helpers_defineProperty__WEBPACK_IMPORTED_MODULE_1___default()({}, scope, reducer(state[scope])));
  }).publishReplay(1).refCount();
}
var reducer_map = function reducer_map(reducer$, scope) {
  return reducer$.map(function (reducer) {
    return [scope, reducer];
  });
};

/***/ }),

/***/ "./src/background/sessions.js":
/*!************************************!*\
  !*** ./src/background/sessions.js ***!
  \************************************/
/*! exports provided: initial_state, toggle_lum, toggle_lpm, update_session, session_switch_ip, sessions_reducer$, select_session, sessions_run */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "initial_state", function() { return initial_state; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "toggle_lum", function() { return toggle_lum; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "toggle_lpm", function() { return toggle_lpm; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "update_session", function() { return update_session; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "session_switch_ip", function() { return session_switch_ip; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "sessions_reducer$", function() { return sessions_reducer$; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "select_session", function() { return select_session; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "sessions_run", function() { return sessions_run; });
/* harmony import */ var _babel_runtime_helpers_slicedToArray__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @babel/runtime/helpers/slicedToArray */ "./node_modules/@babel/runtime/helpers/slicedToArray.js");
/* harmony import */ var _babel_runtime_helpers_slicedToArray__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_babel_runtime_helpers_slicedToArray__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @babel/runtime/regenerator */ "./node_modules/@babel/runtime/regenerator/index.js");
/* harmony import */ var _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var regenerator_runtime__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! regenerator-runtime */ "./node_modules/regenerator-runtime/runtime.js");
/* harmony import */ var regenerator_runtime__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(regenerator_runtime__WEBPACK_IMPORTED_MODULE_2__);
/* harmony import */ var rxjs__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! rxjs */ "./node_modules/rxjs/Rx.js");
/* harmony import */ var rxjs__WEBPACK_IMPORTED_MODULE_3___default = /*#__PURE__*/__webpack_require__.n(rxjs__WEBPACK_IMPORTED_MODULE_3__);
/* harmony import */ var lodash__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! lodash */ "./node_modules/lodash/lodash.js");
/* harmony import */ var lodash__WEBPACK_IMPORTED_MODULE_4___default = /*#__PURE__*/__webpack_require__.n(lodash__WEBPACK_IMPORTED_MODULE_4__);
/* harmony import */ var _util_etask_js__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! /util/etask.js */ "./util/etask.js");
/* harmony import */ var _util_etask_js__WEBPACK_IMPORTED_MODULE_5___default = /*#__PURE__*/__webpack_require__.n(_util_etask_js__WEBPACK_IMPORTED_MODULE_5__);
/* harmony import */ var _util_date_js__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! /util/date.js */ "./util/date.js");
/* harmony import */ var _util_date_js__WEBPACK_IMPORTED_MODULE_6___default = /*#__PURE__*/__webpack_require__.n(_util_date_js__WEBPACK_IMPORTED_MODULE_6__);
/* harmony import */ var _util_zerr_js__WEBPACK_IMPORTED_MODULE_7__ = __webpack_require__(/*! /util/zerr.js */ "./util/zerr.js");
/* harmony import */ var _util_zerr_js__WEBPACK_IMPORTED_MODULE_7___default = /*#__PURE__*/__webpack_require__.n(_util_zerr_js__WEBPACK_IMPORTED_MODULE_7__);
/* harmony import */ var _util_util_js__WEBPACK_IMPORTED_MODULE_8__ = __webpack_require__(/*! ../util/util.js */ "./src/util/util.js");
/* harmony import */ var _lum_js__WEBPACK_IMPORTED_MODULE_9__ = __webpack_require__(/*! ./lum.js */ "./src/background/lum.js");
/* harmony import */ var _proxy_js__WEBPACK_IMPORTED_MODULE_10__ = __webpack_require__(/*! ./proxy.js */ "./src/background/proxy.js");
// LICENSE_CODE ZON

/*jslint browser:true, es6:true*/

/*global chrome*/












var _date$ms = _util_date_js__WEBPACK_IMPORTED_MODULE_6___default.a.ms,
    SEC = _date$ms.SEC,
    MIN = _date$ms.MIN;
var state_subj$ = new rxjs__WEBPACK_IMPORTED_MODULE_3__["BehaviorSubject"]();
var initial_state = {
  session: 'lumext_session_initial',
  country: '',
  city: '',
  asn: '',
  state: '',
  mobile: 'disabled',
  dns: 'remote',
  ip: '',
  vip: '',
  ips: 0,
  carrier: '',
  ssl_super_proxy: false,
  domain_blacklist: [],
  ts: 0,
  lpm_enabled: false,
  ua: '',
  // XXX krzysztof: to a separate object in storage
  lpm_servers: []
};
var session_reduce = new rxjs__WEBPACK_IMPORTED_MODULE_3__["Subject"]();
var session_reducer$ = session_reduce.map(function (sess) {
  return function (state) {
    return lodash__WEBPACK_IMPORTED_MODULE_4___default.a.assign({}, state, sess);
  };
});

function can_keep_proxy(prev_session, next_session, proxy) {
  var diff = lodash__WEBPACK_IMPORTED_MODULE_4___default.a.pick(next_session, function (v, k) {
    return !lodash__WEBPACK_IMPORTED_MODULE_4___default.a.isEqual(v, prev_session[k]);
  });

  delete diff.ts;

  var pc = lodash__WEBPACK_IMPORTED_MODULE_4___default.a.get(proxy.echo, 'country', '').toLowerCase();

  return proxy.echo && (lodash__WEBPACK_IMPORTED_MODULE_4___default.a.isEqual(diff, {
    country: ''
  }) || lodash__WEBPACK_IMPORTED_MODULE_4___default.a.isEqual(diff, {
    country: pc
  }));
}

var toggle_lum = function toggle_lum() {
  return _util_etask_js__WEBPACK_IMPORTED_MODULE_5___default()( /*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default.a.mark(function _callee() {
    var _this = this;

    var cur_lum;
    return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default.a.wrap(function _callee$(_context) {
      while (1) {
        switch (_context.prev = _context.next) {
          case 0:
            chrome.proxy.settings.clear({}, function () {
              _this["continue"]();
            });
            _context.next = 3;
            return this.wait();

          case 3:
            cur_lum = lodash__WEBPACK_IMPORTED_MODULE_4___default.a.get(state_subj$.getValue(), 'lum', {});
            _context.next = 6;
            return update_session({
              lpm_enabled: false
            }, !cur_lum.enabled);

          case 6:
            return _context.abrupt("return", _context.sent);

          case 7:
          case "end":
            return _context.stop();
        }
      }
    }, _callee, this);
  }));
};
var toggle_lpm = function toggle_lpm() {
  return _util_etask_js__WEBPACK_IMPORTED_MODULE_5___default()( /*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default.a.mark(function _callee2() {
    var _this2 = this;

    var cur_session, enable, res;
    return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default.a.wrap(function _callee2$(_context2) {
      while (1) {
        switch (_context2.prev = _context2.next) {
          case 0:
            chrome.proxy.settings.clear({}, function () {
              _this2["continue"]();
            });
            _context2.next = 3;
            return this.wait();

          case 3:
            cur_session = lodash__WEBPACK_IMPORTED_MODULE_4___default.a.get(state_subj$.getValue(), 'sessions', {});
            enable = !cur_session.lpm_enabled;

            if (!(enable && !cur_session.lpm_server)) {
              _context2.next = 7;
              break;
            }

            return _context2.abrupt("return", {
              err: 'No Proxy Manager server'
            });

          case 7:
            _context2.next = 9;
            return update_session({
              lpm_enabled: enable
            }, enable);

          case 9:
            res = _context2.sent;
            return _context2.abrupt("return", res);

          case 11:
          case "end":
            return _context2.stop();
        }
      }
    }, _callee2, this);
  }));
};
var update_session = function update_session(session, enabled) {
  return _util_etask_js__WEBPACK_IMPORTED_MODULE_5___default()( /*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default.a.mark(function _callee3() {
    var cur_session, cur_enabled, cur_proxy, new_proxy;
    return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default.a.wrap(function _callee3$(_context3) {
      while (1) {
        switch (_context3.prev = _context3.next) {
          case 0:
            this.on('uncaught', function (e) {
              return _util_zerr_js__WEBPACK_IMPORTED_MODULE_7___default()(_util_zerr_js__WEBPACK_IMPORTED_MODULE_7___default.a.e2s(e));
            });
            _util_zerr_js__WEBPACK_IMPORTED_MODULE_7___default.a.info('update session', session);
            _lum_js__WEBPACK_IMPORTED_MODULE_9__["lum_actions"].proxy_switching.next(true);
            chrome.storage.local.set({
              proxy_switching: true
            });
            _context3.next = 6;
            return Object(_util_util_js__WEBPACK_IMPORTED_MODULE_8__["get_storage"])('session', {});

          case 6:
            cur_session = _context3.sent;
            _context3.next = 9;
            return Object(_util_util_js__WEBPACK_IMPORTED_MODULE_8__["get_storage"])('enabled', false);

          case 9:
            cur_enabled = _context3.sent;
            cur_proxy = lodash__WEBPACK_IMPORTED_MODULE_4___default.a.get(state_subj$.getValue(), 'proxy', {});
            session = Object.assign({}, cur_session, session);

            if (!can_keep_proxy(cur_session, session, cur_proxy)) {
              _context3.next = 18;
              break;
            }

            session_reduce.next(session);
            _lum_js__WEBPACK_IMPORTED_MODULE_9__["lum_actions"].lum_enable.next(cur_proxy.proxy != 'DIRECT');
            _lum_js__WEBPACK_IMPORTED_MODULE_9__["lum_actions"].proxy_switching.next(false);
            chrome.storage.local.set({
              session: session,
              enabled: cur_proxy.proxy != 'DIRECT',
              proxy_switching: false
            });
            return _context3.abrupt("return", {
              echo: cur_proxy.echo
            });

          case 18:
            session_reduce.next(session);
            chrome.storage.local.set({
              session: session
            });
            if (enabled === undefined) enabled = cur_enabled || session.lpm_enabled;

            if ((!session.customer || !session.zone || !session.key) && !session.lpm_enabled) {
              enabled = false;
            }

            _context3.next = 24;
            return _proxy_js__WEBPACK_IMPORTED_MODULE_10__["set_proxy"](session, enabled);

          case 24:
            new_proxy = _context3.sent;
            _lum_js__WEBPACK_IMPORTED_MODULE_9__["lum_actions"].lum_enable.next(new_proxy.proxy != 'DIRECT');
            _lum_js__WEBPACK_IMPORTED_MODULE_9__["lum_actions"].lum_lpm_enable.next(session.lpm_enabled);
            _lum_js__WEBPACK_IMPORTED_MODULE_9__["lum_actions"].proxy_switching.next(false);
            chrome.storage.local.set({
              enabled: new_proxy.proxy != 'DIRECT',
              lpm_enabled: session.lpm_enabled,
              proxy_switching: false
            });
            open_whoer_if_needed(enabled && !new_proxy.echo.err);
            return _context3.abrupt("return", {
              echo: new_proxy.echo
            });

          case 31:
          case "end":
            return _context3.stop();
        }
      }
    }, _callee3, this);
  }));
};
var session_switch_ip = function session_switch_ip() {
  return _util_etask_js__WEBPACK_IMPORTED_MODULE_5___default()( /*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default.a.mark(function _callee4() {
    var seed, session;
    return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default.a.wrap(function _callee4$(_context4) {
      while (1) {
        switch (_context4.prev = _context4.next) {
          case 0:
            seed = Math.ceil(Math.random() * Number.MAX_SAFE_INTEGER).toString(16);
            session = "lumext_session_".concat(seed);
            _context4.next = 4;
            return update_session({
              session: session
            }, true);

          case 4:
            return _context4.abrupt("return", _context4.sent);

          case 5:
          case "end":
            return _context4.stop();
        }
      }
    }, _callee4);
  }));
};
var sessions_reducer$ = rxjs__WEBPACK_IMPORTED_MODULE_3__["Observable"].of(function (state) {
  return state || initial_state;
}).merge(session_reducer$);
var select_session = function select_session(state$) {
  return state$.map(function (state) {
    return state.sessions || initial_state;
  });
};
var sessions_run = function sessions_run(_ref) {
  var state$ = _ref.state$;
  var end_long = start_long_session(state$);
  var stop_state = state$.subscribe(state_subj$);
  state_subj$.filter(function (a) {
    return !!a;
  }).first().subscribe(function (state) {
    update_session(state.sessions, state.lum.enabled);
  });
  return function () {
    end_long();
    stop_state();
  };
};

var start_long_session = function start_long_session(state$) {
  var long_subs = select_session(state$).map(function (_ref2) {
    var _long = _ref2["long"];
    return _long;
  }).combineLatest(Object(_lum_js__WEBPACK_IMPORTED_MODULE_9__["select_lum_enabled"])(state$)).distinctUntilChanged(lodash__WEBPACK_IMPORTED_MODULE_4___default.a.isEqual).switchMap(function (_ref3) {
    var _ref4 = _babel_runtime_helpers_slicedToArray__WEBPACK_IMPORTED_MODULE_0___default()(_ref3, 2),
        _long2 = _ref4[0],
        enabled = _ref4[1];

    return enabled ? rxjs__WEBPACK_IMPORTED_MODULE_3__["Observable"].timer(_long2 ? 45 * SEC : 2 * MIN, _long2 ? 45 * SEC : 2 * MIN) : rxjs__WEBPACK_IMPORTED_MODULE_3__["Observable"].never();
  })["do"](function () {
    return _proxy_js__WEBPACK_IMPORTED_MODULE_10__["update_echo"]();
  }).subscribe();
  return function () {
    long_subs.unsubscribe();
  };
};

function open_whoer_if_needed(activated) {
  if (!activated) return;
  chrome.storage.local.get(['whoer_opened'], function (_ref5) {
    var whoer_opened = _ref5.whoer_opened;
    if (whoer_opened) return;
    chrome.storage.local.set({
      whoer_opened: true
    });
    chrome.tabs.create({
      url: 'http://whatismyippro.com/'
    });
  });
}

/***/ }),

/***/ "./src/background/storage.js":
/*!***********************************!*\
  !*** ./src/background/storage.js ***!
  \***********************************/
/*! exports provided: storage_load, storage_run, _storage_run */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "storage_load", function() { return storage_load; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "storage_run", function() { return storage_run; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "_storage_run", function() { return _storage_run; });
/* harmony import */ var _babel_runtime_helpers_toConsumableArray__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @babel/runtime/helpers/toConsumableArray */ "./node_modules/@babel/runtime/helpers/toConsumableArray.js");
/* harmony import */ var _babel_runtime_helpers_toConsumableArray__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_babel_runtime_helpers_toConsumableArray__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @babel/runtime/regenerator */ "./node_modules/@babel/runtime/regenerator/index.js");
/* harmony import */ var _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var lodash__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! lodash */ "./node_modules/lodash/lodash.js");
/* harmony import */ var lodash__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(lodash__WEBPACK_IMPORTED_MODULE_2__);
/* harmony import */ var rxjs__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! rxjs */ "./node_modules/rxjs/Rx.js");
/* harmony import */ var rxjs__WEBPACK_IMPORTED_MODULE_3___default = /*#__PURE__*/__webpack_require__.n(rxjs__WEBPACK_IMPORTED_MODULE_3__);
/* harmony import */ var _util_etask_js__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! /util/etask.js */ "./util/etask.js");
/* harmony import */ var _util_etask_js__WEBPACK_IMPORTED_MODULE_4___default = /*#__PURE__*/__webpack_require__.n(_util_etask_js__WEBPACK_IMPORTED_MODULE_4__);
/* harmony import */ var _util_util_js__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ../util/util.js */ "./src/util/util.js");
/* harmony import */ var _util_lum_api_js__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! ../util/lum_api.js */ "./src/util/lum_api.js");
// LICENSE_CODE ZON

/*jslint browser:true, es6:true*/

/*global chrome*/








var chrome_get_data = rxjs__WEBPACK_IMPORTED_MODULE_3__["Observable"].bindCallback(chrome.storage.local.get).bind(chrome.storage.local, ['lum_data']);
var chrome_set_data = rxjs__WEBPACK_IMPORTED_MODULE_3__["Observable"].bindCallback(chrome.storage.local.set).bind(chrome.storage.local);

var pick_fields_to_store = function pick_fields_to_store(obj) {
  return lodash__WEBPACK_IMPORTED_MODULE_2___default.a.pick(obj, 'lum', 'sessions', 'uuid');
};

var storage_load = function storage_load() {
  return chrome_get_data().map(function (_ref) {
    var lum_data = _ref.lum_data;
    return lum_data || '{}';
  }).map(JSON.parse).map(function (s) {
    return lodash__WEBPACK_IMPORTED_MODULE_2___default.a.extend({
      uuid: Object(_util_util_js__WEBPACK_IMPORTED_MODULE_5__["gen_uuid"])()
    }, pick_fields_to_store(s));
  });
};

var storage_save = function storage_save(data) {
  return chrome_set_data({
    lum_data: JSON.stringify(data)
  });
};

var storage_run = function storage_run(_ref2) {
  var state$ = _ref2.state$;
  var state_subsc = state$.map(function (state) {
    return pick_fields_to_store(state);
  }).distinctUntilChanged(lodash__WEBPACK_IMPORTED_MODULE_2___default.a.isEqual).debounceTime(5000).flatMap(function (state) {
    return storage_save(state);
  }).subscribe();
  return function () {
    state_subsc.unsubscribe();
  };
};
var _storage_run = function _storage_run() {
  fetch_info();
  chrome.storage.local.get(function (res) {
    if (res.session !== undefined && res.session.zone) {
      var zone_info;

      if (!(zone_info = (res.zones || {})[res.session.zone])) {
        reset_alloc_ips();
        reset_alloc_vips();
        return;
      }

      update_alloc_ips(res.session.zone, zone_info.plan);
      update_alloc_vips(res.session.zone, zone_info.plan);
    }
  });
  chrome.storage.onChanged.addListener(_util_etask_js__WEBPACK_IMPORTED_MODULE_4___default.a.fn( /*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default.a.mark(function _callee(res) {
    var zones, zone_info;
    return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default.a.wrap(function _callee$(_context) {
      while (1) {
        switch (_context.prev = _context.next) {
          case 0:
            if (!(res.session && (!res.session.newValue || !res.session.oldValue || res.session.newValue.zone != res.session.oldValue.zone))) {
              _context.next = 10;
              break;
            }

            _context.next = 3;
            return Object(_util_util_js__WEBPACK_IMPORTED_MODULE_5__["get_storage"])('zones', {});

          case 3:
            zones = _context.sent;

            if (zone_info = zones[res.session.newValue.zone]) {
              _context.next = 8;
              break;
            }

            reset_alloc_ips();
            reset_alloc_vips();
            return _context.abrupt("return");

          case 8:
            update_alloc_ips(res.session.newValue.zone, zone_info.plan);
            update_alloc_vips(res.session.newValue.zone, zone_info.plan);

          case 10:
          case "end":
            return _context.stop();
        }
      }
    }, _callee);
  })));
};

var fetch_info = function fetch_info() {
  return _util_etask_js__WEBPACK_IMPORTED_MODULE_4___default()( /*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default.a.mark(function _callee2() {
    var shared_block_cns, vipdb, locations, asns_set, asns;
    return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default.a.wrap(function _callee2$(_context2) {
      while (1) {
        switch (_context2.prev = _context2.next) {
          case 0:
            this.on('uncaught', function (e) {
              console.error('error in fetch info: %s', e.message);
            });
            _context2.next = 3;
            return Object(_util_lum_api_js__WEBPACK_IMPORTED_MODULE_6__["fetch_shared_block_countries"])();

          case 3:
            shared_block_cns = _context2.sent;
            chrome.storage.local.set({
              shared_block_cns: shared_block_cns
            });
            _context2.next = 7;
            return Object(_util_lum_api_js__WEBPACK_IMPORTED_MODULE_6__["fetch_vipdb"])();

          case 7:
            vipdb = _context2.sent;
            locations = vipdb.split('\n').map(function (loc) {
              return loc.split('_');
            });
            asns_set = new Set();
            locations.forEach(function (loc) {
              var asn = Number(loc[1]);
              if (!isNaN(asn)) asns_set.add(asn);
            });
            asns = _babel_runtime_helpers_toConsumableArray__WEBPACK_IMPORTED_MODULE_0___default()(asns_set);
            asns.sort(function (a, b) {
              return a - b;
            });
            asns = asns.map(function (asn) {
              return '' + asn;
            });
            chrome.storage.local.set({
              asns: asns
            });

          case 15:
          case "end":
            return _context2.stop();
        }
      }
    }, _callee2, this);
  }));
};

var reset_alloc_ips = function reset_alloc_ips() {
  return chrome.storage.local.set({
    alloc_ips: null
  });
};

var reset_alloc_vips = function reset_alloc_vips() {
  return chrome.storage.local.set({
    alloc_vips: null
  });
};

var update_alloc_ips = function update_alloc_ips(zone_name, plan) {
  return _util_etask_js__WEBPACK_IMPORTED_MODULE_4___default()( /*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default.a.mark(function _callee3() {
    var res, alloc_ips;
    return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default.a.wrap(function _callee3$(_context3) {
      while (1) {
        switch (_context3.prev = _context3.next) {
          case 0:
            this.on('uncaught', function (e) {
              console.error('could not update alloc ips');
              reset_alloc_ips();
            });

            if (Object(_util_util_js__WEBPACK_IMPORTED_MODULE_5__["is_static_zone"])(plan)) {
              _context3.next = 3;
              break;
            }

            return _context3.abrupt("return", reset_alloc_ips());

          case 3:
            _context3.next = 5;
            return Object(_util_lum_api_js__WEBPACK_IMPORTED_MODULE_6__["fetch_alloc_ips"])(zone_name);

          case 5:
            res = _context3.sent;
            alloc_ips = res.map(function (ip) {
              return [ip.ip, ip.maxmind];
            });
            chrome.storage.local.set({
              alloc_ips: alloc_ips
            });

          case 8:
          case "end":
            return _context3.stop();
        }
      }
    }, _callee3, this);
  }));
};

var update_alloc_vips = function update_alloc_vips(zone_name, plan) {
  return _util_etask_js__WEBPACK_IMPORTED_MODULE_4___default()( /*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default.a.mark(function _callee4() {
    var res, alloc_vips;
    return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default.a.wrap(function _callee4$(_context4) {
      while (1) {
        switch (_context4.prev = _context4.next) {
          case 0:
            this.on('uncaught', function (e) {
              console.error('could not update alloc vips');
              reset_alloc_vips();
            });

            if (Object(_util_util_js__WEBPACK_IMPORTED_MODULE_5__["plan_with_vip"])(plan)) {
              _context4.next = 3;
              break;
            }

            return _context4.abrupt("return", reset_alloc_vips());

          case 3:
            _context4.next = 5;
            return Object(_util_lum_api_js__WEBPACK_IMPORTED_MODULE_6__["fetch_alloc_vips"])(zone_name);

          case 5:
            res = _context4.sent;
            alloc_vips = res.map(function (_ref3) {
              var vip = _ref3.vip,
                  country = _ref3.country;
              return [vip, country];
            });
            chrome.storage.local.set({
              alloc_vips: alloc_vips
            });

          case 8:
          case "end":
            return _context4.stop();
        }
      }
    }, _callee4, this);
  }));
};

/***/ }),

/***/ "./src/background/tabs.js":
/*!********************************!*\
  !*** ./src/background/tabs.js ***!
  \********************************/
/*! exports provided: tabs_actions, tabs_reducer$, select_tabs_list, tabs_run */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "tabs_actions", function() { return tabs_actions; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "tabs_reducer$", function() { return tabs_reducer$; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "select_tabs_list", function() { return select_tabs_list; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "tabs_run", function() { return tabs_run; });
/* harmony import */ var _babel_runtime_helpers_defineProperty__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @babel/runtime/helpers/defineProperty */ "./node_modules/@babel/runtime/helpers/defineProperty.js");
/* harmony import */ var _babel_runtime_helpers_defineProperty__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_babel_runtime_helpers_defineProperty__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var lodash__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! lodash */ "./node_modules/lodash/lodash.js");
/* harmony import */ var lodash__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(lodash__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var rxjs__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! rxjs */ "./node_modules/rxjs/Rx.js");
/* harmony import */ var rxjs__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(rxjs__WEBPACK_IMPORTED_MODULE_2__);
/* harmony import */ var _rx_state_js__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./rx_state.js */ "./src/background/rx_state.js");
// LICENSE_CODE ZON

/*jslint browser:true, es6:true*/





var chrome = window.chrome;
var tab_tracker_initial_state = {
  loading: false,
  tabs: undefined
};
var chrome_tabs$ = rxjs__WEBPACK_IMPORTED_MODULE_2__["Observable"].create(function (observer) {
  var tab_updated = function tab_updated(id, status, tab) {
    return observer.next({
      action: 'updated',
      tab: lodash__WEBPACK_IMPORTED_MODULE_1___default.a.clone(tab)
    });
  };

  var tab_created = function tab_created(tab) {
    return observer.next({
      action: 'created',
      tab: lodash__WEBPACK_IMPORTED_MODULE_1___default.a.clone(tab)
    });
  };

  var tab_deleted = function tab_deleted(tab_id) {
    return observer.next({
      action: 'deleted',
      tab_id: tab_id
    });
  };

  var tab_replaced = function tab_replaced(added_id, removed_id) {
    return observer.next({
      action: 'replaced',
      removed_id: removed_id
    });
  };

  var tab_moved = function tab_moved(tab_id, move_info) {
    return observer.next({
      action: 'moved',
      tab_id: tab_id,
      move_info: move_info
    });
  };

  var tab_detached = function tab_detached(tab_id, detach_info) {
    return observer.next({
      action: 'detached',
      tab_id: tab_id,
      detach_info: detach_info
    });
  };

  var tab_attached = function tab_attached(tab_id, attach_info) {
    return observer.next({
      action: 'attached',
      tab_id: tab_id,
      attach_info: attach_info
    });
  };

  var before_request = function before_request(det) {
    if (det.type != 'main_frame' || det.tab == -1) return;
    observer.next({
      action: 'request',
      tab: {
        id: det.tabId,
        url: det.url
      }
    });
  };

  chrome.tabs.query({}, function (tabs) {
    tabs = tabs.reduce(function (akk, tab) {
      akk[tab.id] = lodash__WEBPACK_IMPORTED_MODULE_1___default.a.clone(tab);
      return akk;
    }, {});
    observer.next({
      action: 'query',
      tabs: tabs
    });
    chrome.tabs.onUpdated.addListener(tab_updated);
    chrome.tabs.onCreated.addListener(tab_created);
    chrome.tabs.onRemoved.addListener(tab_deleted);
    chrome.tabs.onMoved.addListener(tab_moved);
    chrome.tabs.onReplaced.addListener(tab_replaced);
    chrome.tabs.onDetached.addListener(tab_detached);
    chrome.tabs.onAttached.addListener(tab_attached);
    chrome.webRequest.onBeforeRequest.addListener(before_request, {
      urls: ['<all_urls>']
    }, ['blocking']);
  });
  return function () {
    chrome.tabs.onUpdated.removeListener(tab_updated);
    chrome.tabs.onCreated.removeListener(tab_created);
    chrome.tabs.onRemoved.removeListener(tab_deleted);
    chrome.tabs.onMoved.removeListener(tab_moved);
    chrome.tabs.onReplaced.removeListener(tab_replaced);
    chrome.tabs.onDetached.removeListener(tab_detached);
    chrome.tabs.onAttached.removeListener(tab_attached);
    chrome.webRequest.onBeforeRequest.removeListener(before_request);
  };
});
var tabs$ = chrome_tabs$.scan(function (akk, act) {
  if (act.action == 'query') return act.tabs;

  if (act.action == 'deleted') {
    var deleted_tab = akk[act.tab_id];
    return lodash__WEBPACK_IMPORTED_MODULE_1___default.a.reduce(akk, function (acc, t) {
      if (t.id == act.tab_id) return acc;
      if (t.windowId === deleted_tab.windowId && t.index > deleted_tab.index) acc[t.id] = Object.assign({}, t, {
        index: t.index - 1
      });else acc[t.id] = t;
      return acc;
    }, {});
  }

  if (act.action == 'replaced') return lodash__WEBPACK_IMPORTED_MODULE_1___default.a.omit(akk, '' + act.removed_id);
  if (act.action == 'request') return akk;

  if (act.action == 'moved' && akk[act.tab_id]) {
    var moving_tab = akk[act.tab_id];

    var moved_tab = lodash__WEBPACK_IMPORTED_MODULE_1___default.a.find(akk, function (tab) {
      return tab.index == act.move_info.toIndex && tab.windowId == moving_tab.windowId;
    });

    moving_tab.index = act.move_info.toIndex;
    moved_tab.index = act.move_info.fromIndex;
    return akk;
  }

  if (act.action === 'attached') {
    var new_window = act.attach_info.newWindowId;
    var new_tab = act.attach_info.newPosition;

    var cp = lodash__WEBPACK_IMPORTED_MODULE_1___default.a.mapValues(akk, function (t) {
      if (t.windowId == new_window && t.index >= new_tab) return Object.assign({}, t, {
        index: t.index + 1
      });
      return t;
    });

    cp[act.tab_id].index = new_tab;
    cp[act.tab_id].windowId = new_window;
    return cp;
  }

  if (act.action == 'detached') {
    return lodash__WEBPACK_IMPORTED_MODULE_1___default.a.mapValues(akk, function (t) {
      if (t.windowId == act.detach_info.oldWindowId && t.index >= act.detach_info.oldPosition) {
        return Object.assign({}, t, {
          index: t.index - 1
        });
      }

      return t;
    });
  }

  return lodash__WEBPACK_IMPORTED_MODULE_1___default.a.extend({}, akk, _babel_runtime_helpers_defineProperty__WEBPACK_IMPORTED_MODULE_0___default()({}, act.tab.id, lodash__WEBPACK_IMPORTED_MODULE_1___default.a.clone(act.tab)));
}, {}).map(function (tabs) {
  return Object.keys(tabs).reduce(function (akk, id) {
    if (/^https?.*/.test(tabs[id].url) || tabs[id].url == 'chrome://newtab/') akk[id] = tabs[id];
    return akk;
  }, {});
});
var tabs_scope = 'tabs';
var tabs_actions = Object(_rx_state_js__WEBPACK_IMPORTED_MODULE_3__["create_actions"])(['tabs_update', 'tabs_reload', 'tab_create', 'tab_highlight']);
var tabs_reducer$ = rxjs__WEBPACK_IMPORTED_MODULE_2__["Observable"].of(function () {
  return tab_tracker_initial_state;
}).merge(tabs_actions.tabs_update.map(function (tabs) {
  return function (state) {
    var loading = Object.keys(tabs).reduce(function (akk, tab_id) {
      return akk || tabs[tab_id].status == 'loading';
    }, false);
    return Object.assign({}, state, {
      loading: loading,
      tabs: tabs
    });
  };
}));

var handle_tabs_update = function handle_tabs_update(tabs) {
  return tabs_actions.tabs_update.next(tabs);
};

var tab_list_equal = function tab_list_equal(tl1, tl2) {
  if (!tl1 && !tl2) return tl1 === tl2;
  if (!tl1 || !tl2) return false;
  if (!lodash__WEBPACK_IMPORTED_MODULE_1___default.a.isEqual(Object.keys(tl1), Object.keys(tl2))) return false;

  for (var key in tl1) {
    if (!tabs_equal(tl1[key], tl2[key])) return false;
  }

  return true;
};

var tabs_equal = function tabs_equal(t1, t2) {
  return lodash__WEBPACK_IMPORTED_MODULE_1___default.a.isEqual(lodash__WEBPACK_IMPORTED_MODULE_1___default.a.omit(t1, 'title', 'mutedInfo'), lodash__WEBPACK_IMPORTED_MODULE_1___default.a.omit(t2, 'title', 'mutedInfo'));
};

var select_tabs = function select_tabs(state$) {
  return state$.map(function (state) {
    return state[tabs_scope];
  }).distinctUntilChanged(function (p, v) {
    if (!lodash__WEBPACK_IMPORTED_MODULE_1___default.a.isEqual(Object.keys(p), Object.keys(v))) return false;
    if (p.status != v.status) return false;
    return tab_list_equal(p.tabs, v.tabs);
  });
};

var select_tabs_list = function select_tabs_list(state$) {
  return select_tabs(state$).map(function (_ref) {
    var tabs = _ref.tabs;
    return tabs;
  }).distinctUntilChanged(tab_list_equal);
};
var tabs_run = function tabs_run() {
  var tabs_subscription = tabs$.subscribe(handle_tabs_update);
  var tabs_reload_subs = tabs_actions.tabs_reload.subscribe(function (tabs) {
    tabs = lodash__WEBPACK_IMPORTED_MODULE_1___default.a.isArray(tabs) ? tabs : [tabs];
    tabs.forEach(function (_ref2) {
      var id = _ref2.id;
      return chrome.tabs.reload(id);
    });
  });
  var tab_highlight_subs = tabs_actions.tab_highlight.subscribe(function (tab) {
    chrome.tabs.highlight({
      tabs: tab.index,
      windowId: tab.windowId
    }, function () {});
  });
  var tab_create_subs = tabs_actions.tab_create.subscribe(function (opt) {
    return chrome.tabs.create(opt);
  });
  return function () {
    tabs_subscription.unsubscribe();
    tabs_reload_subs.unsubscribe();
    tab_highlight_subs.unsubscribe();
    tabs_reload_subs.unsubscribe();
    tab_create_subs.unsubscribe();
  };
};

/***/ }),

/***/ "./src/util/consts.js":
/*!****************************!*\
  !*** ./src/util/consts.js ***!
  \****************************/
/*! exports provided: CHROME_STORE_LINK, RATING_URL, LUMTEST_URL, PROXY_ERRORS */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "CHROME_STORE_LINK", function() { return CHROME_STORE_LINK; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "RATING_URL", function() { return RATING_URL; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "LUMTEST_URL", function() { return LUMTEST_URL; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "PROXY_ERRORS", function() { return PROXY_ERRORS; });
var module; // LICENSE_CODE ZON

'use strict';
/*jslint browser:true, es6:true*/


var APP_ID = 'efohiadmkaogdhibjbmeppjpebenaool';
var CHROME_STORE_LINK = 'https://chrome.google.com/webstore/detail/' + 'luminati/' + APP_ID;
var RATING_URL = 'https://chrome.google.com/webstore/detail/luminati/' + APP_ID;
var LUMTEST_URL = 'http://lumtest.com/echo.json';
var PROXY_ERRORS = {
  ip_forbidden: 'Auth Failed (code: ip_forbidden)',
  peers_unavailable: 'Proxy Error: No peers available',
  city_unavailable: 'Proxy Error: We do not have IPs in the city'
};

/***/ }),

/***/ "./src/util/lum_api.js":
/*!*****************************!*\
  !*** ./src/util/lum_api.js ***!
  \*****************************/
/*! exports provided: fetch_shared_block_countries, submit_support_ticket, load_cities_api, load_customer_api, fetch_vipdb, fetch_alloc_ips, fetch_alloc_vips, auth_zone, load_carriers_api, get_version, load_superagents, test_echo, test_port, test_lpm_port, test_lpm_server */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "fetch_shared_block_countries", function() { return fetch_shared_block_countries; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "submit_support_ticket", function() { return submit_support_ticket; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "load_cities_api", function() { return load_cities_api; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "load_customer_api", function() { return load_customer_api; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "fetch_vipdb", function() { return fetch_vipdb; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "fetch_alloc_ips", function() { return fetch_alloc_ips; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "fetch_alloc_vips", function() { return fetch_alloc_vips; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "auth_zone", function() { return auth_zone; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "load_carriers_api", function() { return load_carriers_api; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "get_version", function() { return get_version; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "load_superagents", function() { return load_superagents; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "test_echo", function() { return test_echo; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "test_port", function() { return test_port; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "test_lpm_port", function() { return test_lpm_port; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "test_lpm_server", function() { return test_lpm_server; });
/* harmony import */ var _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @babel/runtime/regenerator */ "./node_modules/@babel/runtime/regenerator/index.js");
/* harmony import */ var _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _util_etask_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! /util/etask.js */ "./util/etask.js");
/* harmony import */ var _util_etask_js__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_util_etask_js__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _util_ajax_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! /util/ajax.js */ "./util/ajax.js");
/* harmony import */ var _util_ajax_js__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(_util_ajax_js__WEBPACK_IMPORTED_MODULE_2__);
/* harmony import */ var _util_zerr_js__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! /util/zerr.js */ "./util/zerr.js");
/* harmony import */ var _util_zerr_js__WEBPACK_IMPORTED_MODULE_3___default = /*#__PURE__*/__webpack_require__.n(_util_zerr_js__WEBPACK_IMPORTED_MODULE_3__);
/* harmony import */ var _util_escape_js__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! /util/escape.js */ "./util/escape.js");
/* harmony import */ var _util_escape_js__WEBPACK_IMPORTED_MODULE_4___default = /*#__PURE__*/__webpack_require__.n(_util_escape_js__WEBPACK_IMPORTED_MODULE_4__);
/* harmony import */ var _util_url_js__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! /util/url.js */ "./util/url.js");
/* harmony import */ var _util_url_js__WEBPACK_IMPORTED_MODULE_5___default = /*#__PURE__*/__webpack_require__.n(_util_url_js__WEBPACK_IMPORTED_MODULE_5__);
/* harmony import */ var _util_js__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! ./util.js */ "./src/util/util.js");
/* harmony import */ var _consts_js__WEBPACK_IMPORTED_MODULE_7__ = __webpack_require__(/*! ./consts.js */ "./src/util/consts.js");


var _this = undefined;

var module; // LICENSE_CODE ZON

'use strict';
/*jslint browser:true, es6:true*/









var sb_countries_loader;
var fetch_shared_block_countries = function fetch_shared_block_countries() {
  if (sb_countries_loader) return _this.wait_ext(sb_countries_loader);
  sb_countries_loader = _this;
  return _util_ajax_js__WEBPACK_IMPORTED_MODULE_2___default()({
    json: 1,
    url: Object(_util_js__WEBPACK_IMPORTED_MODULE_6__["www_domain"])() + '/users/zone/shared_block_countries'
  });
};
var submit_support_ticket = function submit_support_ticket(data) {
  return _util_etask_js__WEBPACK_IMPORTED_MODULE_1___default()( /*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default.a.mark(function _callee() {
    var auth, res;
    return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default.a.wrap(function _callee$(_context) {
      while (1) {
        switch (_context.prev = _context.next) {
          case 0:
            _context.next = 2;
            return Object(_util_js__WEBPACK_IMPORTED_MODULE_6__["get_storage"])('auth');

          case 2:
            auth = _context.sent;
            _context.next = 5;
            return _util_ajax_js__WEBPACK_IMPORTED_MODULE_2___default()({
              json: 1,
              method: 'POST',
              url: Object(_util_js__WEBPACK_IMPORTED_MODULE_6__["www_domain"])() + '/bext/report_bug',
              data: data,
              headers: {
                Authorization: 'Bearer ' + auth.token
              }
            });

          case 5:
            res = _context.sent;
            return _context.abrupt("return", res);

          case 7:
          case "end":
            return _context.stop();
        }
      }
    }, _callee);
  }));
};
var load_cities_api = function load_cities_api(country) {
  return _util_ajax_js__WEBPACK_IMPORTED_MODULE_2___default()({
    json: 1,
    url: Object(_util_js__WEBPACK_IMPORTED_MODULE_6__["www_domain"])() + '/cities',
    qs: {
      country: country
    }
  });
};
var load_customer_api = function load_customer_api(account_id, token) {
  return _util_etask_js__WEBPACK_IMPORTED_MODULE_1___default()( /*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default.a.mark(function _callee2() {
    var res;
    return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default.a.wrap(function _callee2$(_context2) {
      while (1) {
        switch (_context2.prev = _context2.next) {
          case 0:
            _context2.next = 2;
            return _util_ajax_js__WEBPACK_IMPORTED_MODULE_2___default()({
              json: 1,
              url: Object(_util_js__WEBPACK_IMPORTED_MODULE_6__["www_domain"])() + '/bext/customer',
              qs: {
                customer: account_id
              },
              headers: {
                Authorization: 'Bearer ' + token
              }
            });

          case 2:
            res = _context2.sent;
            return _context2.abrupt("return", res);

          case 4:
          case "end":
            return _context2.stop();
        }
      }
    }, _callee2);
  }));
};
var fetch_vipdb = function fetch_vipdb() {
  return _util_etask_js__WEBPACK_IMPORTED_MODULE_1___default()( /*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default.a.mark(function _callee3() {
    return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default.a.wrap(function _callee3$(_context3) {
      while (1) {
        switch (_context3.prev = _context3.next) {
          case 0:
            _context3.next = 2;
            return _util_ajax_js__WEBPACK_IMPORTED_MODULE_2___default()({
              // XXX krzysztof: switch lpm->bext when ready
              url: Object(_util_js__WEBPACK_IMPORTED_MODULE_6__["www_domain"])() + '/lpm/vipdb/main'
            });

          case 2:
            return _context3.abrupt("return", _context3.sent);

          case 3:
          case "end":
            return _context3.stop();
        }
      }
    }, _callee3);
  }));
};
var fetch_alloc_ips = function fetch_alloc_ips(zone) {
  return _util_etask_js__WEBPACK_IMPORTED_MODULE_1___default()( /*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default.a.mark(function _callee4() {
    var auth, res;
    return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default.a.wrap(function _callee4$(_context4) {
      while (1) {
        switch (_context4.prev = _context4.next) {
          case 0:
            _context4.next = 2;
            return Object(_util_js__WEBPACK_IMPORTED_MODULE_6__["get_storage"])('auth');

          case 2:
            auth = _context4.sent;

            if (auth) {
              _context4.next = 5;
              break;
            }

            return _context4.abrupt("return", []);

          case 5:
            _context4.next = 7;
            return _util_ajax_js__WEBPACK_IMPORTED_MODULE_2___default()({
              json: 1,
              url: Object(_util_js__WEBPACK_IMPORTED_MODULE_6__["www_domain"])() + '/bext/alloc_ips',
              qs: {
                zone: zone
              },
              headers: {
                Authorization: 'Bearer ' + auth.token
              }
            });

          case 7:
            res = _context4.sent;
            return _context4.abrupt("return", res.ips);

          case 9:
          case "end":
            return _context4.stop();
        }
      }
    }, _callee4);
  }));
};
var fetch_alloc_vips = function fetch_alloc_vips(zone) {
  return _util_etask_js__WEBPACK_IMPORTED_MODULE_1___default()( /*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default.a.mark(function _callee5() {
    var auth, res;
    return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default.a.wrap(function _callee5$(_context5) {
      while (1) {
        switch (_context5.prev = _context5.next) {
          case 0:
            _context5.next = 2;
            return Object(_util_js__WEBPACK_IMPORTED_MODULE_6__["get_storage"])('auth');

          case 2:
            if (auth = _context5.sent) {
              _context5.next = 4;
              break;
            }

            return _context5.abrupt("return", []);

          case 4:
            _context5.next = 6;
            return _util_ajax_js__WEBPACK_IMPORTED_MODULE_2___default()({
              json: 1,
              url: Object(_util_js__WEBPACK_IMPORTED_MODULE_6__["www_domain"])() + '/bext/alloc_vips',
              qs: {
                zone: zone
              },
              headers: {
                Authorization: 'Bearer ' + auth.token
              }
            });

          case 6:
            res = _context5.sent;
            return _context5.abrupt("return", res.vips);

          case 8:
          case "end":
            return _context5.stop();
        }
      }
    }, _callee5);
  }));
};
var auth_zone = function auth_zone(username, key) {
  return _util_etask_js__WEBPACK_IMPORTED_MODULE_1___default()( /*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default.a.mark(function _callee6() {
    var res;
    return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default.a.wrap(function _callee6$(_context6) {
      while (1) {
        switch (_context6.prev = _context6.next) {
          case 0:
            _context6.next = 2;
            return _util_ajax_js__WEBPACK_IMPORTED_MODULE_2___default()({
              json: 1,
              method: 'POST',
              url: Object(_util_js__WEBPACK_IMPORTED_MODULE_6__["www_domain"])() + '/bext/gen_token_zone',
              data: {
                username: username,
                key: key
              },
              no_throw: 1
            });

          case 2:
            res = _context6.sent;
            return _context6.abrupt("return", res);

          case 4:
          case "end":
            return _context6.stop();
        }
      }
    }, _callee6);
  }));
};
var load_carriers_api = function load_carriers_api() {
  return _util_ajax_js__WEBPACK_IMPORTED_MODULE_2___default()({
    json: 1,
    url: Object(_util_js__WEBPACK_IMPORTED_MODULE_6__["bext_domains"])().client + '/carriers'
  });
};
var get_version = function get_version(version) {
  return _util_ajax_js__WEBPACK_IMPORTED_MODULE_2___default()({
    json: 1,
    url: Object(_util_js__WEBPACK_IMPORTED_MODULE_6__["www_domain"])() + '/bext/get_version',
    qs: {
      version: version
    }
  });
};
var load_superagents = function load_superagents() {
  var fetch_super_proxies = function fetch_super_proxies(n) {
    return _util_etask_js__WEBPACK_IMPORTED_MODULE_1___default()( /*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default.a.mark(function _callee7() {
      var url, res;
      return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default.a.wrap(function _callee7$(_context7) {
        while (1) {
          switch (_context7.prev = _context7.next) {
            case 0:
              _context7.prev = 0;
              url = Object(_util_js__WEBPACK_IMPORTED_MODULE_6__["www_domain"])() + '/bext/resolve_super_proxy';
              _context7.next = 4;
              return _util_ajax_js__WEBPACK_IMPORTED_MODULE_2___default()({
                url: url,
                json: 1
              });

            case 4:
              res = _context7.sent;
              return _context7.abrupt("return", res.proxies.map(Object(_util_js__WEBPACK_IMPORTED_MODULE_6__["bext_domains"])().agent_name));

            case 8:
              _context7.prev = 8;
              _context7.t0 = _context7["catch"](0);
              _util_zerr_js__WEBPACK_IMPORTED_MODULE_3___default.a.warn('could not fetch ' + url);
              Object(_util_js__WEBPACK_IMPORTED_MODULE_6__["domains_fallback"])();

              if (!(n <= 1)) {
                _context7.next = 14;
                break;
              }

              return _context7.abrupt("return", this["throw"](new Error('could not get_super_proxy')));

            case 14:
              _context7.next = 16;
              return fetch_super_proxies(n - 1);

            case 16:
              return _context7.abrupt("return", _context7.sent);

            case 17:
            case "end":
              return _context7.stop();
          }
        }
      }, _callee7, this, [[0, 8]]);
    }));
  };

  return fetch_super_proxies(_util_js__WEBPACK_IMPORTED_MODULE_6__["domain_config"].length);
};
var test_echo = function test_echo() {
  return _util_etask_js__WEBPACK_IMPORTED_MODULE_1___default()( /*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default.a.mark(function _callee8() {
    var res;
    return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default.a.wrap(function _callee8$(_context8) {
      while (1) {
        switch (_context8.prev = _context8.next) {
          case 0:
            _context8.next = 2;
            return _util_ajax_js__WEBPACK_IMPORTED_MODULE_2___default()({
              url: _consts_js__WEBPACK_IMPORTED_MODULE_7__["LUMTEST_URL"],
              json: 1,
              timeout: 8000
            });

          case 2:
            res = _context8.sent;
            return _context8.abrupt("return", res);

          case 4:
          case "end":
            return _context8.stop();
        }
      }
    }, _callee8);
  }));
};
var test_port = function test_port() {
  return _util_etask_js__WEBPACK_IMPORTED_MODULE_1___default()( /*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default.a.mark(function _callee9() {
    return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default.a.wrap(function _callee9$(_context9) {
      while (1) {
        switch (_context9.prev = _context9.next) {
          case 0:
            _context9.prev = 0;
            _context9.next = 3;
            return _util_ajax_js__WEBPACK_IMPORTED_MODULE_2___default()({
              url: 'https://zproxy.lum-superproxy.io:22225/ping'
            });

          case 3:
            _context9.next = 9;
            break;

          case 5:
            _context9.prev = 5;
            _context9.t0 = _context9["catch"](0);
            console.error(_context9.t0.message);
            return _context9.abrupt("return", {
              port_error: true
            });

          case 9:
            return _context9.abrupt("return", {
              port_error: false
            });

          case 10:
          case "end":
            return _context9.stop();
        }
      }
    }, _callee9, null, [[0, 5]]);
  }));
};
var test_lpm_port = function test_lpm_port(lpm_server) {
  return _util_etask_js__WEBPACK_IMPORTED_MODULE_1___default()( /*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default.a.mark(function _callee10() {
    return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default.a.wrap(function _callee10$(_context10) {
      while (1) {
        switch (_context10.prev = _context10.next) {
          case 0:
            _context10.prev = 0;
            _context10.next = 3;
            return _util_ajax_js__WEBPACK_IMPORTED_MODULE_2___default()({
              url: "".concat(lpm_server, "/api/version")
            });

          case 3:
            _context10.next = 9;
            break;

          case 5:
            _context10.prev = 5;
            _context10.t0 = _context10["catch"](0);
            console.error(_context10.t0.message);
            return _context10.abrupt("return", {
              port_error: true
            });

          case 9:
            return _context10.abrupt("return", {
              port_error: false
            });

          case 10:
          case "end":
            return _context10.stop();
        }
      }
    }, _callee10, null, [[0, 5]]);
  }));
};
var test_lpm_server = function test_lpm_server(lpm_server) {
  return _util_etask_js__WEBPACK_IMPORTED_MODULE_1___default()( /*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default.a.mark(function _callee11() {
    var res;
    return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_0___default.a.wrap(function _callee11$(_context11) {
      while (1) {
        switch (_context11.prev = _context11.next) {
          case 0:
            _context11.next = 2;
            return fetch(_util_escape_js__WEBPACK_IMPORTED_MODULE_4___default.a.uri(lpm_server + '/api/proxies_running'));

          case 2:
            res = _context11.sent;

            if (!(!res.ok && res.status != 403)) {
              _context11.next = 5;
              break;
            }

            throw new Error('test lpm failed');

          case 5:
            return _context11.abrupt("return", {
              redirect: res.redirected && res.url.replace(_util_url_js__WEBPACK_IMPORTED_MODULE_5___default.a.parse(res.url).path, '')
            });

          case 6:
          case "end":
            return _context11.stop();
        }
      }
    }, _callee11);
  }));
};

/***/ }),

/***/ "./util/url.js":
/*!*********************!*\
  !*** ./util/url.js ***!
  \*********************/
/*! no static exports found */
/***/ (function(module, exports, __webpack_require__) {

var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;
var module;
// LICENSE_CODE ZON ISC
'use strict'; /*zlint node, br*/
(function(){

var is_node = typeof module=='object' && module.exports && module.children;
var is_rn = (typeof global=='object' && !!global.nativeRequire) ||
    (typeof navigator=='object' && navigator.product=='ReactNative');
var is_ff_addon = typeof module=='object' && module.uri
    && !module.uri.indexOf('resource://');
var qs;

if (is_rn)
    ;
else if (!is_node)
    ;
else
{
    // XXX arik HACK: react-native bundler will try to require querystring
    // even thoguh it never reaches this if (it is done in pre-processing)
    // so we fool him
    var _require = require;
    qs = _require('querystring');
}
!(__WEBPACK_AMD_DEFINE_ARRAY__ = [], __WEBPACK_AMD_DEFINE_RESULT__ = (function(){
var assign = Object.assign;
var E = {};

function replace_slashes(url){ return url.replace(/\\/g, '/'); }

E.add_proto = function(url){
    if (!url.match(/^([a-z0-9]+:)?\/\//i))
        url = 'http://'+url;
    return url;
};

E.rel_proto_to_abs = function(url){
    var proto = is_node ? 'http:' : location.protocol;
    return url.replace(/^\/\//, proto+'//');
};

E.get_top_level_domain = function(host){
    var n = host.match(/\.([^.]+)$/);
    return n ? n[1] : '';
};

E.get_host = function(url){
    var n = replace_slashes(url).match(/^(https?:)?\/\/([^\/]+)\/.*$/);
    return n ? n[2] : '';
};

E.get_host_without_tld = function(host){
    return host.replace(/^([^.]+)\.[^.]{2,3}(\.[^.]{2,3})?$/, '$1');
};

var generic_2ld = {com: 1, biz: 1, net: 1, org: 1, xxx: 1, edu: 1, gov: 1,
    ac: 1, co: 1, or: 1, ne: 1, kr: 1, jp: 1, jpn: 1, cn: 1};

E.get_root_domain = function(domain){
    if (E.is_ip(domain))
        return domain;
    var s = domain.split('.'), root = s, len = s.length;
    if (len>2) // www.abc.com abc.com.tw www.abc.com.tw,...
    {
        var hd = 0;
        if (s[len-1]=='hola')
        {
            hd = 2; // domain.us.hola
            if (s[len-2].match(/^\d+$/))
                hd = 3; // domain.us.23456.hola
        }
        if (generic_2ld[s[len-2-hd]])
            root = s.slice(-3-hd, len-hd); // abc.com.tw
        else
            root = s.slice(-2-hd, len-hd); // abc.com
    }
    return root.join('.');
};

// XXX josh: move to email.js:get_domain
E.get_domain_email = function(email){
    var match = email.toLowerCase().match(/^[a-z0-9_.\-+*%]+@(.*)$/);
    return match && match[1];
};

// XXX josh: move to email.js:get_root_domain or remove and let developer
// combine email.js:get_domain with url.js:get_root_domain
E.get_root_domain_email = function(email){
    var domain = E.get_domain_email(email);
    return domain && E.get_root_domain(domain);
};

E.get_path = function(url){
    var n = url.match(/^https?:\/\/[^\/]+(\/.*$)/);
    return n ? n[1] : '';
};

E.get_proto = function(url){
    var n = url.match(/^([a-z0-9]+):\/\//);
    return n ? n[1] : '';
};

E.get_host_gently = function(url){
    var n = replace_slashes(url).match(/^(?:(?:[a-z0-9]+?:)?\/\/)?([^\/]+)/);
    return n ? n[1] : '';
};

E.is_ip = function(host){
    var m = /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/.exec(host);
    if (!m)
        return false;
    for (var i=1; i<=4; i++)
    {
        if (+m[i]>255)
            return false;
    }
    return true;
};

E.is_ip_mask = function(host){
    var m = /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/.exec(host);
    if (!m)
        return false;
    if (E.ip2num(host)==0)
        return false;
    var final = false;
    var check_num_mask = function(num){
        var arr = (num >>> 0).toString(2).split(''), _final = false;
        for (var i=0; i<arr.length; i++)
        {
            if (_final && arr[i]=='1')
                return false;
            if (!_final && arr[i]=='0')
                _final = true;
        }
        return true;
    };
    for (var i=1; i<=4; i++)
    {
        if (+m[i]>255)
            return false;
        if (final && +m[i]>0)
            return false;
        if (!final && +m[i]<255)
        {
            if (!check_num_mask(+m[i]))
                return false;
            final = true;
        }
    }
    return !!final;
};

E.ip2num = function(ip){
    var num = 0;
    ip.split('.').forEach(function(octet){
        num <<= 8;
        num += +octet;
    });
    return num>>>0;
};

E.num2ip = function(num){
    return (num>>>24)+'.'+(num>>16 & 255)+'.'+(num>>8 & 255)+'.'+(num & 255);
};

E.is_ip_subnet = function(host){
    var m = /(.+?)\/(\d+)$/.exec(host);
    return m && E.is_ip(m[1]) && +m[2]<=32;
};

E.is_ip_netmask = function(host){
    var ips = host.split('/');
    if (ips.length!=2 || !E.is_ip(ips[0]) || !E.is_ip_mask(ips[1]))
        return false;
    return true;
};

E.is_ip_range = function(host){
    if (typeof host.split !== 'function')
        return false;
    var ips = host.split('-');
    if (ips.length!=2 || !E.is_ip(ips[0]) || !E.is_ip(ips[1]))
        return false;
    return E.ip2num(ips[0])<E.ip2num(ips[1]);
};

E.is_ip_port = function(host){
    var m = /(.+?)(?::(\d{1,5}))?$/.exec(host);
    return m && E.is_ip(m[1]) && !(+m[2]>65535);
};

/* basic url validation to prevent script injection like 'javascript:....' */
E.is_valid_url = function(url){
    return /^(https?:\/\/)?([a-z0-9-]+\.)+[a-z0-9-]+(:\d+)?(\/.*)?$/i
    .test(url);
};

E.is_valid_domain = function(domain){
    return /^([a-z0-9]([a-z0-9-_]*[a-z0-9])?\.)+[a-z]{2,63}$/.test(domain); };

// XXX josh: move to email.js:is_valid
E.is_valid_email = function(email, is_signup){
    if (!email || typeof email!='string')
        return false;
    var re = /^[a-z0-9_\-+*]+(?:\.[a-z0-9_\-+*]+)*@(.*)$/;
    var n = email.toLowerCase().match(re);
    if ((n&&is_signup&&email.split('@')[0].match(/\+/g)||[]).length>1)
        return false;
    return !!(n && E.is_valid_domain(n[1]));
};

E.get_first_valid_email = function(email){
    return email.split(/\s+/).find(E.is_valid_email); };

// XXX dmitriie: move to email.js:is_alias
E.is_alias_email = function(email){
    if (!E.is_valid_email(email))
        return false;
    var n = email.toLowerCase().match(/^([a-z0-9_.\-+*]+)@.*$/);
    return !!(n && /.+\+.+/.test(n[1]));
};

// XXX vadimr: move to email.js:is_need_sanitize
E.is_email_need_sanitize = function(email){
    var valid_domains = ['gmail.com', 'googlemail.com', 'protonmail.ch',
        'protonmail.com'];
    return valid_domains.indexOf(E.get_domain_email(email)) !== -1;
};

// XXX vadimr: move to email.js:sanitize
E.sanitize_email = function(email){
    var main = E.get_main_email(email);
    if(!main)
        return;
    var sp = main.split('@');
    return sp[0].replace(/\.*/g, '')+'@'+sp[1];
};

// XXX dmitriie: move to email.js:get_main
E.get_main_email = function(email){
    if (!E.is_valid_email(email))
        return;
    if (E.is_alias_email(email))
        return email.replace(/\+.+@/, '@');
    return email;
};

E.is_ip_in_range = function(ips_range, ip){
    if (!E.is_ip_range(ips_range) || !E.is_ip(ip))
        return false;
    var ips = ips_range.split('-');
    var min_ip = E.ip2num(ips[0]), max_ip = E.ip2num(ips[1]);
    var num_ip = E.ip2num(ip);
    return num_ip>=min_ip && num_ip<=max_ip;
};

E.is_ip_local = function(ip){
    return E.is_ip_in_range('10.0.0.0-10.255.255.255', ip) ||
        E.is_ip_in_range('172.16.0.0-172.31.255.255', ip) ||
        E.is_ip_in_range('192.168.0.0-192.168.255.255', ip) ||
        E.is_ip_in_range('169.254.0.0-169.254.255.255', ip);
};

E.host_lookup = function(lookup, host){
    var pos;
    while (1)
    {
        if (host in lookup)
            return lookup[host];
        if ((pos = host.indexOf('.'))<0)
            return;
        host = host.slice(pos+1);
    }
};

// more-or-less compatible with NodeJS url API
E.uri_obj_href = function(uri){
    return (uri.protocol||'')+(uri.slashes ? '//' : '')
        +(uri.host ? (uri.auth ? uri.auth+'@' : '')+uri.host : '')
        +uri.path
        +(uri.hash||'');
};

var protocol_re = /^((?:about|http|https|file|ftp|ws|wss):)?(\/\/)?/i;
var host_section_re = /^(.*?)(?:[\/?#]|$)/;
var host_re = /^(?:(([^:@]*):?([^:@]*))?@)?([a-zA-Z0-9._+-]*)(?::(\d*))?/;
var path_section_re = /^([^?#]*)(\?[^#]*)?(#.*)?$/;
var path_re_loose = /^(\/(?:.(?![^\/]*\.[^\/.]+$))*\/?)?([^\/]*?(?:\.([^.]+))?)$/;
var path_re_strict = /^(\/(?:.(?![^\/]*(?:\.[^\/.]+)?$))*\/?)?([^\/]*?(?:\.([^.]+))?)$/;

E.parse = function(url, strict){
    function re(expr, str){
        var m;
        try { m = expr.exec(str); } catch(e){ m = null; }
        if (!m)
            return m;
        for (var i=0; i<m.length; i++)
            m[i] = m[i]===undefined ? null : m[i];
        return m;
    }
    url = url||location.href;
    var uri = {orig: url};
    url = replace_slashes(url);
    var m, remaining = url;
    // protocol
    if (!(m = re(protocol_re, remaining)))
        return {};
    uri.protocol = m[1];
    if (uri.protocol!==null)
        uri.protocol = uri.protocol.toLowerCase();
    uri.slashes = !!m[2];
    if (!uri.protocol && !uri.slashes)
    {
        uri.protocol = 'http:';
        uri.slashes = true;
    }
    remaining = remaining.slice(m[0].length);
    // host
    if (!(m = re(host_section_re, remaining)))
        return {};
    uri.authority = m[1];
    remaining = remaining.slice(m[1].length);
    // host elements
    if (!(m = re(host_re, uri.authority)))
        return {};
    uri.auth = m[1];
    uri.user = m[2];
    uri.password = m[3];
    uri.hostname = m[4];
    uri.port = m[5];
    if (uri.hostname!==null)
    {
        uri.hostname = uri.hostname.toLowerCase();
        uri.host = uri.hostname+(uri.port ? ':'+uri.port : '');
    }
    // path
    if (!(m = re(path_section_re, remaining)))
        return {};
    uri.relative = m[0];
    uri.pathname = m[1];
    uri.search = m[2];
    uri.query = uri.search ? uri.search.substring(1) : null;
    uri.hash = m[3];
    // path elements
    if (!(m = re(strict ? path_re_strict : path_re_loose, uri.pathname)))
        return {};
    uri.directory = m[1];
    uri.file = m[2];
    uri.ext = m[3];
    if (uri.file=='.'+uri.ext)
        uri.ext = null;
    // finals
    if (!uri.pathname)
        uri.pathname = '/';
    uri.path = uri.pathname+(uri.search||'');
    uri.href = E.uri_obj_href(uri);
    return uri;
};

E.qs_parse = function(q, bin, safe){
    var obj = {};
    q = q.length ? q.split('&') : [];
    var len = q.length;
    var unescape_val = bin ? function(val){
        return qs.unescapeBuffer(val, true).toString('binary');
    } : safe ? function(val){
        try { return decodeURIComponent(val.replace(/\+/g, ' ')); }
        catch(e){ return val; }
    } : function(val){
        return decodeURIComponent(val.replace(/\+/g, ' '));
    };
    for (var i = 0; i<len; ++i)
    {
        var x = q[i];
        var idx = x.indexOf('=');
        var kstr = idx>=0 ? x.substr(0, idx) : x;
        var vstr = idx>=0 ? x.substr(idx + 1) : '';
        var k = unescape_val(kstr);
        var v = unescape_val(vstr);
        if (obj[k]===undefined)
            obj[k] = v;
        else if (Array.isArray(obj[k]))
            obj[k].push(v);
        else
            obj[k] = [obj[k], v];
    }
    return obj;
};

function token_regex(s, end){ return end ? '^'+s+'$' : s; }

E.http_glob_host = function(host, end){
    var port = '';
    var parts = host.split(':');
    host = parts[0];
    if (parts.length>1)
        port = ':'+parts[1].replace('*', '[0-9]+');
    var n = host.match(/^(|.*[^*])(\*+)$/);
    if (n)
    {
        host = E.http_glob_host(n[1])
        +(n[2].length==1 ? '[^./]+' : '[^/]'+(n[1] ? '*' : '+'));
        return token_regex(host+port, end);
    }
    /* '**' replace doesn't use '*' in output to avoid conflict with '*'
     * replace following it */
    host = host.replace(/\*\*\./, '**').replace(/\*\./, '*')
    .replace(/\./g, '\\.').replace(/\*\*/g, '(([^./]+\\.)+)?')
    .replace(/\*/g, '[^./]+\\.');
    return token_regex(host+port, end);
};

E.http_glob_path = function(path, end){
    if (path[0]=='*')
        return E.http_glob_path('/'+path, end);
    var n = path.match(/^(|.*[^*])(\*+)([^*^\/]*)$/);
    if (n)
    {
        path = E.http_glob_path(n[1])+(n[2].length==1 ? '[^/]+' : '.*')+
            E.http_glob_path(n[3]);
        return token_regex(path, end);
    }
    path = path.replace(/\*\*\//, '**').replace(/\*\//, '*')
    .replace(/\//g, '\\/').replace(/\./g, '\\.')
    .replace(/\*\*/g, '(([^/]+\\/)+)?').replace(/\*/g, '[^/]+\\/');
    return token_regex(path, end);
};

E.http_glob_url = function(url, end){
    var n = url.match(/^((.*):\/\/)?([^\/]+)(\/.*)?$/);
    if (!n)
        return null;
    var prot = n[1] ? n[2] : '*';
    var host = n[3];
    var path = n[4]||'**';
    if (prot=='*')
        prot = 'https?';
    host = E.http_glob_host(host);
    path = E.http_glob_path(path);
    return token_regex(prot+':\\/\\/'+host+path, end);
};

E.root_url_cmp = function(a, b){
    var a_s = a.match(/^[*.]*([^*]+)$/);
    var b_s = b.match(/^[*.]*([^*]+)$/);
    if (!a_s && !b_s)
        return false;
    var re, s;
    if (a_s && b_s && a_s[1].length>b_s[1].length || a_s && !b_s)
    {
        s = a_s[1];
        re = b;
    }
    else
    {
        s = b_s[1];
        re = a;
    }
    s = E.add_proto(s)+'/';
    if (!(re = E.http_glob_url(re, 1)))
        return false;
    try { re = new RegExp(re); }
    catch(e){ return false; }
    return re.test(s);
};

E.qs_strip = function(url){ return /^[^?#]*/.exec(url)[0]; };

// mini-implementation of zescape.qs to avoid dependency of escape.js
E.qs_str = function(qs){
    var q = [];
    for (var k in qs)
    {
        (Array.isArray(qs[k]) ? qs[k] : [qs[k]]).forEach(function(v){
            q.push(encodeURIComponent(k)+'='+encodeURIComponent(v)); });
    }
    return q.join('&');
};

E.qs_add = function(url, qs){
    var u = E.parse(url), q = assign(u.query ? E.qs_parse(u.query) : {}, qs);
    u.path = u.pathname+'?'+E.qs_str(q);
    return E.uri_obj_href(u);
};

E.qs_remove = function(url, qs){
    var u = E.parse(url), q = assign(u.query ? E.qs_parse(u.query) : {});
    qs.forEach(function(query){ delete q[query]; });
    u.path = u.pathname+'?'+E.qs_str(q);
    return E.uri_obj_href(u);
};

E.qs_parse_url = function(url){
    return E.qs_parse(url.replace(/(^.*\?)|(^[^?]*$)/, ''));
};

return E; }).apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__)); }());


/***/ })

}]);