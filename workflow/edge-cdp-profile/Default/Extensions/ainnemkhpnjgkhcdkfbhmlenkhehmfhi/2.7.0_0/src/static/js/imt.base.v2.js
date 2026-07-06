
/*
Integromat Base

@author Patrik Simek
@license Copyright 2016 Integromat. All right reserved.
 */

(function() {
  "use strict";
  var ANIMATION_EASING, ANIMATION_FPS, CAROUSEL_MAX_SLIDES, CONTEXT_MENU, CONTEXT_MENU_MARGIN, CONTEXT_MENU_OFFSET, Carousel, CountDown, DIACRITICS_MAP, Grid, LOADER_STORE, MODAL_SIZES, PANEL_MARGIN, PANEL_ONE, PANEL_PADDING, PANEL_WIDTH, PARSERS, PREVIEW_PANEL, RemoteChart, RemoteList, RemoteTable, SIGNED_USER_MENU, __dateToString, __jsonParse, attachFakeCursor, ex, fn, fn1, global, html, initSwitch, install, item, l, len1, len2, len3, letter, q, ref, ref1, ref2, ref3, u, window,
    slice = [].slice,
    extend1 = function(child, parent) { for (var key in parent) { if (hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; },
    hasProp = {}.hasOwnProperty,
    indexOf = [].indexOf || function(item) { for (var i = 0, l = this.length; i < l; i++) { if (i in this && this[i] === item) return i; } return -1; },
    bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; };

  window = self;


  /*!
   * simDOM
   * http://simdom.org/
  
   * Released under the MIT license
   * http://simdom.org/license
   */

  (function(window) {
    var ALTERNATIVE_EVENT_CONSTRUCTORS, BOOTSTRAP_EVENT, COMPONENT, CSS_NUMBER, CSS_SHEET, EVENT_CONSTRUCTOR, FF, HAS_COMPONENTS, JQUERY, JQUERY_POLYFILLS, NAMESPACE, NODE, READY_LISTENERS, SIMArray, SIMBase, SIMDocument, SIMElement, SIMText, SIMWindow, TAGS, TEMP_ID, WHEEL_EVENT, check, clearImmediate, document, filter, matches, normalizeCssKey, normalizeCssValue, parse, query, queryAll, queryDo, sanitize, setImmediate, sim, simArray;
    if ((window != null ? window.sim : void 0) != null) {
      return;
    }
    NODE = window == null;
    JQUERY = (window != null ? window.jQuery : void 0) != null;
    FF = (typeof navigator !== "undefined" && navigator !== null ? navigator.userAgent.toLowerCase().indexOf('firefox') : void 0) > -1;
    WHEEL_EVENT = window ? "onwheel" in window.document.createElement("div") ? "wheel" : window.document.onmousewheel !== undefined ? "mousewheel" : "DOMMouseScroll" : "wheel";
    TEMP_ID = 0;
    TAGS = ['a', 'abbr', 'address', 'area', 'article', 'aside', 'audio', 'b', 'base', 'bdi', 'bdo', 'blockquote', 'body', 'br', 'button', 'canvas', 'caption', 'cite', 'code', 'col', 'colgroup', 'datalist', 'dd', 'del', 'details', 'dfn', 'dialog', 'div', 'dl', 'dt', 'em', 'embed', 'fieldset', 'figcaption', 'figure', 'footer', 'form', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'head', 'header', 'hr', 'i', 'iframe', 'img', 'input', 'ins', 'kbd', 'keygen', 'label', 'legend', 'li', 'link', 'main', 'map', 'mark', 'menu', 'menuitem', 'meta', 'meter', 'nav', 'noscript', 'object', 'ol', 'optgroup', 'option', 'output', 'p', 'param', 'pre', 'progress', 'q', 'rp', 'rt', 'ruby', 's', 'samp', 'script', 'section', 'select', 'small', 'source', 'span', 'strong', 'style', 'sub', 'summary', 'sup', 'table', 'tbody', 'td', 'textarea', 'tfoot', 'th', 'thead', 'time', 'title', 'tr', 'track', 'u', 'ul', 'var', 'video', 'wbr'];
    JQUERY_POLYFILLS = ['animate', 'stop', 'slideDown', 'slideUp', 'slideToggle', 'fadeIn', 'fadeOut', 'fadeToggle'];
    READY_LISTENERS = [];
    CSS_SHEET = null;
    CSS_NUMBER = {
      'columnCount': true,
      'fillOpacity': true,
      'flexGrow': true,
      'flexShrink': true,
      'fontWeight': true,
      'lineHeight': true,
      'opacity': true,
      'order': true,
      'orphans': true,
      'widows': true,
      'zIndex': true,
      'zoom': true
    };
    COMPONENT = Object.create(null);
    HAS_COMPONENTS = false;
    NAMESPACE = Object.create(null);
    EVENT_CONSTRUCTOR = {
      resize: 'UIEvent',
      scroll: 'UIEvent'
    };
    BOOTSTRAP_EVENT = /^[^\.]+\.bs\.[^\.]+$/;
    ALTERNATIVE_EVENT_CONSTRUCTORS = {
      'CustomEvent': function(name, options) {
        var ref, ref1, ref2;
        return this.initCustomEvent(name, (ref = options.bubbles) != null ? ref : true, (ref1 = options.cancelable) != null ? ref1 : false, (ref2 = options.detail) != null ? ref2 : {});
      },
      'UIEvent': function(name, options) {
        var ref, ref1;
        return this.initUIEvent(name, (ref = options.bubbles) != null ? ref : true, (ref1 = options.cancelable) != null ? ref1 : false, window, 0);
      }
    };
    sim = function(selector) {
      var defaultKlass, ref, ref1, ref2;
      if (selector == null) {
        return null;
      }
      if (selector instanceof SIMBase || selector instanceof SIMArray) {
        return selector;
      }
      if (selector.__sim__ instanceof SIMBase) {
        return selector.__sim__;
      }
      if ('function' === typeof selector) {
        return sim.ready(selector);
      }
      if ('string' === typeof selector) {
        if ((selector === 'html' || selector === 'body') || /^#([a-z]+[_a-z0-9-]*)$/i.test(selector)) {
          return sim(query(window.document, selector));
        } else {
          return simArray(queryAll(window.document, selector));
        }
      }
      if (Array.isArray(selector)) {
        return new SIMArray(selector);
      }
      if (selector.nodeType === 3) {
        return new SIMText(selector);
      }
      if (selector.nodeType === 9) {
        return new SIMDocument(selector);
      }
      if (selector.nodeType === 1) {
        defaultKlass = (ref = NAMESPACE[selector.namespaceURI]) != null ? ref : SIMElement;
        if (HAS_COMPONENTS) {
          if (selector.hasAttribute('sim-component')) {
            return new ((ref1 = COMPONENT[selector.getAttribute('sim-component')]) != null ? ref1 : defaultKlass)(selector);
          } else if (selector.hasAttribute('data-sim-component')) {
            return new ((ref2 = COMPONENT[selector.getAttribute('data-sim-component')]) != null ? ref2 : defaultKlass)(selector);
          }
        }
        return new defaultKlass(selector);
      }
      if (JQUERY && selector instanceof window.jQuery) {
        return new SIMArray(selector.toArray());
      }
      if ((window.Window != null) && selector.constructor === window.Window) {
        return new SIMWindow(selector);
      }
      return null;
    };

    /*
    	Ensures argument is SIMArray and if it isn't, it will create it.
    	
    	@param {*} array Array.
    	@returns {SIMArray}
     */
    simArray = function(array) {
      if (array instanceof SIMArray) {
        return array;
      }
      return new SIMArray(array);
    };
    if (NODE) {
      module.exports = sim;
      window = require('./dom');
      sim.window = window;
      sim.require = function(files, done) {
        var next;
        if ('string' === typeof files) {
          files = [files];
        }
        next = function() {
          var file;
          file = require('path').resolve(process.cwd(), files.shift());
          return sim(window.document.body).script("[src=\"" + file + "\"]", function() {
            var _error, _load;
            _error = (function(_this) {
              return function(err) {
                _this.off('load', _load);
                return typeof done === "function" ? done(err) : void 0;
              };
            })(this);
            _load = function() {
              this.off('error', _error);
              JQUERY = (window != null ? window.jQuery : void 0) != null;
              if (files.length) {
                return next();
              } else {
                return typeof done === "function" ? done(null) : void 0;
              }
            };
            this.once('error', _error);
            return this.once('load', _load);
          });
        };
        return next();
      };
    }
    window.sim = sim;
    window.document.addEventListener('DOMContentLoaded', function() {
      return sim.ready();
    });
    document = window.document;
    setImmediate = window.setImmediate || function(fn) {
      return setTimeout(fn, 0);
    };
    clearImmediate = window.clearImmediate || function(fn) {
      return clearTimeout(fn);
    };
    query = function(dom, selector) {
      return queryDo('querySelector', dom, selector);
    };
    queryAll = function(dom, selector) {
      return Array.prototype.slice.call(queryDo('querySelectorAll', dom, selector));
    };
    queryDo = function(method, dom, selector) {
      var ex, res, tempId;
      tempId = false;
      selector = selector.replace(/@([a-z]+[_a-z0-9-]*)/gi, function(a, b) {
        return "[sim-component=\"" + b + "\"]";
      });
      if (':scope ' === selector.substr(0, 7)) {
        if (!dom.hasAttribute('id')) {
          tempId = true;
          dom.setAttribute('id', "sim-temp-id-" + (TEMP_ID++));
        }
        selector = "#" + (dom.getAttribute('id')) + " " + (selector.substr(7));
      }
      try {
        res = dom[method](selector);
      } catch (error) {
        ex = error;
        console.error("simdom query '" + selector + "' failed: " + ex.message);
        if (method === 'querySelectorAll') {
          return [];
        } else {
          return null;
        }
      }
      if (tempId) {
        dom.removeAttribute('id');
      }
      return res;
    };
    check = function() {
      var l, len1, type, types, valid, value;
      value = arguments[0], types = 2 <= arguments.length ? slice.call(arguments, 1) : [];
      for (l = 0, len1 = types.length; l < len1; l++) {
        type = types[l];
        valid = (function() {
          switch (type) {
            case String:
              return 'string' === typeof value;
            case Number:
              return 'number' === typeof value;
            case Boolean:
              return 'boolean' === typeof value;
            case Function:
              return 'function' === typeof value;
            default:
              return value instanceof type;
          }
        })();
        if (valid) {
          return true;
        }
      }
      throw new Error("Type '" + type.name + "' expeceted.");
    };
    parse = function(selectors) {
      var buffer, chr, cond, condition, conditions, cursor, inarg, instr, length, next, parsing;
      conditions = [];
      if ('string' === typeof selectors && selectors.length) {
        condition = null;
        parsing = null;
        buffer = '';
        cursor = -1;
        length = selectors.length;
        instr = false;
        inarg = false;
        next = function(type) {
          var match;
          buffer = buffer.trim();
          if (buffer.length) {
            switch (parsing) {
              case 'tag':
                condition.tag = buffer;
                break;
              case 'id':
                condition.id = buffer;
                break;
              case 'class':
                condition["class"].push(buffer);
                break;
              case 'component':
                condition.attribute.push({
                  name: 'sim-component',
                  operator: '=',
                  value: buffer
                });
                break;
              case 'attr':
                match = buffer.match(/^([_a-z0-9-]+)(?:=(.*))?\]$/i);
                if (match) {
                  condition.attribute.push({
                    name: match[1],
                    operator: '=',
                    value: match[2]
                  });
                }
                break;
              case 'pseudo':
                match = buffer.match(/^([-a-z]+)(?:\((.*))?$/i);
                if (match) {
                  condition.pseudo.push({
                    name: match[1],
                    conditions: parse(match[2])
                  });
                }
            }
          }
          buffer = '';
          return parsing = type;
        };
        cond = function() {
          next('tag');
          condition = {
            id: null,
            tag: null,
            'class': [],
            attribute: [],
            pseudo: []
          };
          return conditions.push(condition);
        };
        cond();
        while (++cursor < length) {
          chr = selectors.charAt(cursor);
          if (instr) {
            if (chr === '"') {
              instr = false;
            } else {
              buffer += chr;
            }
            continue;
          } else if (inarg) {
            if (chr === ')') {
              inarg = false;
            } else {
              buffer += chr;
            }
            continue;
          }
          switch (chr) {
            case '.':
              next('class');
              break;
            case '#':
              next('id');
              break;
            case '[':
              next('attr');
              break;
            case ':':
              next('pseudo');
              break;
            case '@':
              next('component');
              break;
            case '(':
              if (parsing === 'pseudo') {
                buffer += chr;
                inarg = true;
              } else {
                parsing = null;
              }
              break;
            case '"':
              if (parsing === 'attr') {
                instr = true;
              } else {
                parsing = null;
              }
              break;
            case ',':
              cond();
              break;
            default:
              buffer += chr;
          }
        }
        next(null);
      }
      return conditions;
    };
    matches = function(elm, conditions, index) {
      var attr, condition, fulfilled, l, len1, len2, len3, len4, name, ps, q, ref, ref1, ref2, ref3, ref4, u, z;
      if (index == null) {
        index = 0;
      }
      if (conditions.length === 0) {
        return true;
      }
      if (elm instanceof SIMText) {
        return false;
      }
      for (l = 0, len1 = conditions.length; l < len1; l++) {
        condition = conditions[l];
        if (condition.tag != null) {
          if (condition.tag === '*') {
            if (!(elm instanceof SIMElement)) {
              continue;
            }
          } else {
            if (elm.prop('tagName').toLowerCase() !== condition.tag) {
              continue;
            }
          }
        }
        if ((condition.id != null) && elm.attr('id') !== condition.id) {
          continue;
        }
        if (condition['class'].length) {
          fulfilled = true;
          ref = condition['class'];
          for (q = 0, len2 = ref.length; q < len2; q++) {
            name = ref[q];
            if (!(!elm.hasClass(name))) {
              continue;
            }
            fulfilled = false;
            break;
          }
          if (!fulfilled) {
            continue;
          }
        }
        if (condition.attribute.length) {
          fulfilled = true;
          ref1 = condition.attribute;
          for (u = 0, len3 = ref1.length; u < len3; u++) {
            attr = ref1[u];
            if (attr.value != null) {
              if (attr.value !== elm.attr(attr.name)) {
                fulfilled = false;
                break;
              }
            } else {
              if (!elm.__dom.hasAttribute(attr.name)) {
                fulfilled = false;
                break;
              }
            }
          }
          if (!fulfilled) {
            continue;
          }
        }
        if (condition.pseudo.length) {
          fulfilled = true;
          ref2 = condition.pseudo;
          for (z = 0, len4 = ref2.length; z < len4; z++) {
            ps = ref2[z];
            switch (ps.name) {
              case 'visible':
                if (elm.__dom.offsetWidth === 0 || elm.__dom.offsetHeight === 0) {
                  fulfilled = false;
                  break;
                }
                break;
              case 'disabled':
                if (elm.__dom.disabled !== true) {
                  fulfilled = false;
                  break;
                }
                break;
              case 'focus':
                if (elm.__dom.ownerDocument.activeElement !== elm.__dom) {
                  fulfilled = false;
                  break;
                }
                break;
              case 'first-child':
              case 'first':
                if (((ref3 = elm.__dom.parentNode) != null ? ref3.firstChild : void 0) !== elm.__dom) {
                  fulfilled = false;
                  break;
                }
                break;
              case 'last-child':
              case 'last':
                if (((ref4 = elm.__dom.parentNode) != null ? ref4.lastChild : void 0) !== elm.__dom) {
                  fulfilled = false;
                  break;
                }
                break;
              case 'checked':
                if (elm.__dom.checked !== true) {
                  fulfilled = false;
                  break;
                }
                break;
              case 'odd':
                if (index % 2 === 1) {
                  fulfilled = false;
                  break;
                }
                break;
              case 'even':
                if (index % 2 === 0) {
                  fulfilled = false;
                  break;
                }
                break;
              case 'not':
                if (matches(elm, ps.conditions)) {
                  fulfilled = false;
                  break;
                }
            }
          }
          if (!fulfilled) {
            continue;
          }
        }
        return true;
      }
      return false;
    };
    normalizeCssKey = function(key) {
      return key.replace(/\-(.)/g, function(a, b) {
        return b.toUpperCase();
      });
    };
    normalizeCssValue = function(key, value) {
      if ('number' === typeof value && !CSS_NUMBER[key]) {
        return value + "px";
      } else {
        return value;
      }
    };
    sanitize = function(text) {
      return text.replace(/>/g, '&gt;').replace(/</g, '&lt;').replace(/"/g, '&quot;');
    };
    filter = function(array, selectors) {
      var arr, conditions, index, item, l, len1, len2, len3, q, u;
      arr = new SIMArray;
      if (selectors == null) {
        for (l = 0, len1 = array.length; l < len1; l++) {
          item = array[l];
          if (!(item instanceof SIMText)) {
            arr.push(item);
          }
        }
        return arr;
      }
      if ('function' === typeof selectors) {
        for (index = q = 0, len2 = array.length; q < len2; index = ++q) {
          item = array[index];
          if (!(item instanceof SIMText)) {
            if (selectors.call(item, item, index, array)) {
              arr.push(item);
            }
          }
        }
        return arr;
      }
      conditions = parse(selectors);
      for (index = u = 0, len3 = array.length; u < len3; index = ++u) {
        item = array[index];
        if (!(item instanceof SIMText) && matches(item, conditions, index)) {
          arr.push(item);
        }
      }
      return arr;
    };
    SIMArray = (function() {
      SIMArray.prototype.length = 0;

      function SIMArray(elms) {
        var e, elm, l, len1;
        if (elms instanceof SIMElement || elms instanceof SIMText) {
          this.push(elms);
        } else if (elms instanceof SIMArray || Array.isArray(elms)) {
          for (l = 0, len1 = elms.length; l < len1; l++) {
            elm = elms[l];
            e = sim(elm);
            if (e) {
              this.push(e);
            }
          }
        } else {
          e = sim(elms);
          if (e) {
            this.push(e);
          }
        }
      }

      SIMArray.prototype.addClass = function() {
        var elm, l, len1, ref;
        ref = this;
        for (l = 0, len1 = ref.length; l < len1; l++) {
          elm = ref[l];
          elm.addClass.apply(elm, arguments);
        }
        return this;
      };

      SIMArray.prototype.appendTo = function() {
        var elm, l, len1, ref;
        ref = this;
        for (l = 0, len1 = ref.length; l < len1; l++) {
          elm = ref[l];
          elm.appendTo.apply(elm, arguments);
        }
        return this;
      };

      SIMArray.prototype.attr = function(key, value) {
        var elm, l, len1, ref, ref1;
        if (arguments.length === 1) {
          return (ref = this.first()) != null ? ref.attr(key) : void 0;
        } else {
          ref1 = this;
          for (l = 0, len1 = ref1.length; l < len1; l++) {
            elm = ref1[l];
            elm.attr(key, value);
          }
          return this;
        }
      };

      SIMArray.prototype.after = function() {
        var elm, l, len1, ref;
        ref = this;
        for (l = 0, len1 = ref.length; l < len1; l++) {
          elm = ref[l];
          elm.after.apply(elm, arguments);
        }
        return this;
      };

      SIMArray.prototype.append = function() {
        var elm, l, len1, ref;
        ref = this;
        for (l = 0, len1 = ref.length; l < len1; l++) {
          elm = ref[l];
          elm.append.apply(elm, arguments);
        }
        return this;
      };

      SIMArray.prototype.blur = function() {
        var ref;
        if ((ref = this.first()) != null) {
          ref.blur();
        }
        return this;
      };

      SIMArray.prototype.css = function(key, value) {
        var elm, l, len1, len2, q, ref, ref1, ref2;
        if ('object' === typeof key) {
          ref = this;
          for (l = 0, len1 = ref.length; l < len1; l++) {
            elm = ref[l];
            elm.css(key);
          }
          return this;
        } else if (arguments.length === 1) {
          return (ref1 = this.first()) != null ? ref1.css(key) : void 0;
        } else {
          ref2 = this;
          for (q = 0, len2 = ref2.length; q < len2; q++) {
            elm = ref2[q];
            elm.css(key, value);
          }
          return this;
        }
      };

      SIMArray.prototype.children = function() {
        var arr, elm, l, len1, ref;
        arr = new SIMArray;
        ref = this;
        for (l = 0, len1 = ref.length; l < len1; l++) {
          elm = ref[l];
          arr.push(elm.children.apply(elm, arguments));
        }
        return arr;
      };

      SIMArray.prototype.clone = function() {
        var arr, elm, l, len1, ref;
        arr = new SIMArray;
        ref = this;
        for (l = 0, len1 = ref.length; l < len1; l++) {
          elm = ref[l];
          arr.push(elm.clone.apply(elm, arguments));
        }
        return arr;
      };

      SIMArray.prototype.data = function(key, value) {
        var elm, l, len1, ref, ref1;
        if (arguments.length < 2) {
          return (ref = this.first()) != null ? ref.data(key) : void 0;
        } else {
          ref1 = this;
          for (l = 0, len1 = ref1.length; l < len1; l++) {
            elm = ref1[l];
            elm.data(key, value);
          }
          return this;
        }
      };

      SIMArray.prototype.detach = function() {
        var elm, l, len1, ref;
        ref = this;
        for (l = 0, len1 = ref.length; l < len1; l++) {
          elm = ref[l];
          elm.detach();
        }
        return this;
      };

      SIMArray.prototype["do"] = function(method) {
        var elm, l, len1, ref;
        ref = this;
        for (l = 0, len1 = ref.length; l < len1; l++) {
          elm = ref[l];
          method.call(elm);
        }
        return this;
      };

      SIMArray.prototype.each = function(method) {
        var index, item, l, len1, ref;
        ref = this;
        for (index = l = 0, len1 = ref.length; l < len1; index = ++l) {
          item = ref[index];
          method.call(item, index, item);
        }
        return this;
      };

      SIMArray.prototype.emit = function() {
        var elm, l, len1, ref;
        ref = this;
        for (l = 0, len1 = ref.length; l < len1; l++) {
          elm = ref[l];
          elm.emit.apply(elm, arguments);
        }
        return this;
      };

      SIMArray.prototype.empty = function() {
        var elm, l, len1, ref;
        ref = this;
        for (l = 0, len1 = ref.length; l < len1; l++) {
          elm = ref[l];
          elm.empty();
        }
        return this;
      };

      SIMArray.prototype.filter = function(selectors) {
        if (selectors == null) {
          return new SIMArray;
        }
        return filter(this, selectors);
      };

      SIMArray.prototype.find = function() {
        var arr, elm, l, len1, ref;
        arr = new SIMArray;
        ref = this;
        for (l = 0, len1 = ref.length; l < len1; l++) {
          elm = ref[l];
          arr.push(elm.find.apply(elm, arguments));
        }
        return arr;
      };

      SIMArray.prototype.first = function() {
        return this[0];
      };

      SIMArray.prototype.focus = function() {
        var ref;
        if ((ref = this.first()) != null) {
          ref.focus();
        }
        return this;
      };

      SIMArray.prototype.hasClass = function(name) {
        var elm, l, len1, ref;
        ref = this;
        for (l = 0, len1 = ref.length; l < len1; l++) {
          elm = ref[l];
          if (elm.hasClass(name)) {
            return true;
          }
        }
        return false;
      };

      SIMArray.prototype.height = function(value) {
        var elm, l, len1, ref, ref1, ref2;
        if (arguments.length) {
          ref = this;
          for (l = 0, len1 = ref.length; l < len1; l++) {
            elm = ref[l];
            elm.height(value);
          }
          return this;
        } else {
          return (ref1 = (ref2 = this.first()) != null ? ref2.height() : void 0) != null ? ref1 : 0;
        }
      };

      SIMArray.prototype.hide = function() {
        var elm, l, len1, ref;
        ref = this;
        for (l = 0, len1 = ref.length; l < len1; l++) {
          elm = ref[l];
          elm.hide.apply(elm, arguments);
        }
        return this;
      };

      SIMArray.prototype.html = function(value) {
        var elm, l, len1, ref, ref1, ref2;
        if (arguments.length) {
          ref = this;
          for (l = 0, len1 = ref.length; l < len1; l++) {
            elm = ref[l];
            elm.html(value);
          }
          return this;
        } else {
          return (ref1 = (ref2 = this.first()) != null ? ref2.html() : void 0) != null ? ref1 : '';
        }
      };

      SIMArray.prototype.indexOf = Array.prototype.indexOf;

      SIMArray.prototype.insertAfter = function() {
        var elm, l, len1, ref;
        ref = this;
        for (l = 0, len1 = ref.length; l < len1; l++) {
          elm = ref[l];
          elm.insertAfter.apply(elm, arguments);
        }
        return this;
      };

      SIMArray.prototype.insertBefore = function() {
        var elm, l, len1, ref;
        ref = this;
        for (l = 0, len1 = ref.length; l < len1; l++) {
          elm = ref[l];
          elm.insertBefore.apply(elm, arguments);
        }
        return this;
      };

      SIMArray.prototype.inspect = function() {
        var elm;
        return "[SIMArray " + (((function() {
          var l, len1, ref, results;
          ref = this;
          results = [];
          for (l = 0, len1 = ref.length; l < len1; l++) {
            elm = ref[l];
            results.push(elm.inspect());
          }
          return results;
        }).call(this)).join(', ')) + "]";
      };

      SIMArray.prototype.last = function() {
        return this[this.length - 1];
      };

      SIMArray.prototype.map = function(method) {
        var item, l, len1, ref, results;
        ref = this;
        results = [];
        for (l = 0, len1 = ref.length; l < len1; l++) {
          item = ref[l];
          results.push(method(item));
        }
        return results;
      };

      SIMArray.prototype.next = function() {
        var arr, elm, l, len1, ref;
        arr = new SIMArray;
        ref = this;
        for (l = 0, len1 = ref.length; l < len1; l++) {
          elm = ref[l];
          arr.push(elm.next.apply(elm, arguments));
        }
        return arr;
      };

      SIMArray.prototype.nextAll = function() {
        var arr, elm, l, len1, ref;
        arr = new SIMArray;
        ref = this;
        for (l = 0, len1 = ref.length; l < len1; l++) {
          elm = ref[l];
          arr.push(elm.nextAll.apply(elm, arguments));
        }
        return arr;
      };

      SIMArray.prototype.not = function(selectors) {
        var arr, conditions, index, item, l, len1, len2, q, ref, ref1;
        arr = new SIMArray;
        if (selectors == null) {
          ref = this;
          for (l = 0, len1 = ref.length; l < len1; l++) {
            item = ref[l];
            arr.push(item);
          }
          return arr;
        }
        conditions = parse(selectors);
        ref1 = this;
        for (index = q = 0, len2 = ref1.length; q < len2; index = ++q) {
          item = ref1[index];
          if (!matches(item, conditions, index)) {
            arr.push(item);
          }
        }
        return arr;
      };

      SIMArray.prototype.off = function() {
        var elm, l, len1, ref;
        ref = this;
        for (l = 0, len1 = ref.length; l < len1; l++) {
          elm = ref[l];
          elm.off.apply(elm, arguments);
        }
        return this;
      };

      SIMArray.prototype.on = function() {
        var elm, l, len1, ref;
        ref = this;
        for (l = 0, len1 = ref.length; l < len1; l++) {
          elm = ref[l];
          elm.on.apply(elm, arguments);
        }
        return this;
      };

      SIMArray.prototype.once = function() {
        var elm, l, len1, ref;
        ref = this;
        for (l = 0, len1 = ref.length; l < len1; l++) {
          elm = ref[l];
          elm.once.apply(elm, arguments);
        }
        return this;
      };

      SIMArray.prototype.outerHeight = function(margin) {
        var ref, ref1;
        return (ref = (ref1 = this.first()) != null ? ref1.outerHeight(margin) : void 0) != null ? ref : 0;
      };

      SIMArray.prototype.outerWidth = function(margin) {
        var ref, ref1;
        return (ref = (ref1 = this.first()) != null ? ref1.outerWidth(margin) : void 0) != null ? ref : 0;
      };

      SIMArray.prototype.parent = function() {
        var arr, elm, l, len1, ref;
        arr = new SIMArray;
        ref = this;
        for (l = 0, len1 = ref.length; l < len1; l++) {
          elm = ref[l];
          arr.push(elm.parent.apply(elm, arguments));
        }
        return arr;
      };

      SIMArray.prototype.push = function(elm) {
        var e, l, len1;
        if (elm == null) {
          return this;
        }
        check(elm, SIMElement, SIMText, SIMArray);
        if (elm instanceof SIMArray) {
          for (l = 0, len1 = elm.length; l < len1; l++) {
            e = elm[l];
            this.push(e);
          }
          return this;
        }
        Array.prototype.push.call(this, elm);
        return this;
      };

      SIMArray.prototype.prependTo = function() {
        var elm, l, len1, ref;
        ref = this;
        for (l = 0, len1 = ref.length; l < len1; l++) {
          elm = ref[l];
          elm.prependTo.apply(elm, arguments);
        }
        return this;
      };

      SIMArray.prototype.prev = function() {
        var arr, elm, l, len1, ref;
        arr = new SIMArray;
        ref = this;
        for (l = 0, len1 = ref.length; l < len1; l++) {
          elm = ref[l];
          arr.push(elm.prev.apply(elm, arguments));
        }
        return arr;
      };

      SIMArray.prototype.prevAll = function() {
        var arr, elm, l, len1, ref;
        arr = new SIMArray;
        ref = this;
        for (l = 0, len1 = ref.length; l < len1; l++) {
          elm = ref[l];
          arr.push(elm.prevAll.apply(elm, arguments));
        }
        return arr;
      };

      SIMArray.prototype.prop = function(key, value) {
        var elm, l, len1, ref, ref1;
        if (arguments.length === 1) {
          return (ref = this.first()) != null ? ref.prop(key) : void 0;
        } else {
          ref1 = this;
          for (l = 0, len1 = ref1.length; l < len1; l++) {
            elm = ref1[l];
            elm.prop(key, value);
          }
          return this;
        }
      };

      SIMArray.prototype.remove = function() {
        var elm, l, len1, ref;
        ref = this;
        for (l = 0, len1 = ref.length; l < len1; l++) {
          elm = ref[l];
          elm.remove();
        }
        return this;
      };

      SIMArray.prototype.removeClass = function() {
        var elm, l, len1, ref;
        ref = this;
        for (l = 0, len1 = ref.length; l < len1; l++) {
          elm = ref[l];
          elm.removeClass.apply(elm, arguments);
        }
        return this;
      };

      SIMArray.prototype.reverse = Array.prototype.reverse;

      SIMArray.prototype.shift = Array.prototype.shift;

      SIMArray.prototype.show = function() {
        var elm, l, len1, ref;
        ref = this;
        for (l = 0, len1 = ref.length; l < len1; l++) {
          elm = ref[l];
          elm.show.apply(elm, arguments);
        }
        return this;
      };

      SIMArray.prototype.slice = function(begin, end) {
        var arr, i, l, len, ref, size, start, upto;
        arr = new SIMArray;
        len = this.length;
        start = begin || 0;
        start = start >= 0 ? start : Math.max(0, len + start);
        upto = 'number' === typeof end ? Math.min(end, len) : len;
        if (end < 0) {
          upto = len + end;
        }
        size = upto - start;
        if (size > 0) {
          for (i = l = 0, ref = size; 0 <= ref ? l < ref : l > ref; i = 0 <= ref ? ++l : --l) {
            arr.push(this[start + i]);
          }
        }
        return arr;
      };

      SIMArray.prototype.sort = function() {
        return new SIMArray(Array.prototype.sort.apply(this, arguments));
      };

      SIMArray.prototype.splice = function() {
        return this;
      };

      SIMArray.prototype.text = function(value) {
        var elm, l, len1, ref, ref1, ref2;
        if (arguments.length) {
          ref = this;
          for (l = 0, len1 = ref.length; l < len1; l++) {
            elm = ref[l];
            elm.text(value);
          }
          return this;
        } else {
          return (ref1 = (ref2 = this.first()) != null ? ref2.text() : void 0) != null ? ref1 : '';
        }
      };

      SIMArray.prototype.toArray = function() {
        var elm, l, len1, ref, results;
        ref = this;
        results = [];
        for (l = 0, len1 = ref.length; l < len1; l++) {
          elm = ref[l];
          results.push(elm);
        }
        return results;
      };

      SIMArray.prototype.toggleClass = function() {
        var elm, l, len1, ref;
        ref = this;
        for (l = 0, len1 = ref.length; l < len1; l++) {
          elm = ref[l];
          elm.toggleClass.apply(elm, arguments);
        }
        return this;
      };

      SIMArray.prototype.toString = function() {
        var elm;
        return ((function() {
          var l, len1, ref, results;
          ref = this;
          results = [];
          for (l = 0, len1 = ref.length; l < len1; l++) {
            elm = ref[l];
            results.push(elm.toString());
          }
          return results;
        }).call(this)).join('');
      };

      SIMArray.prototype.trigger = function() {
        var elm, l, len1, ref;
        ref = this;
        for (l = 0, len1 = ref.length; l < len1; l++) {
          elm = ref[l];
          elm.trigger.apply(elm, arguments);
        }
        return this;
      };

      SIMArray.prototype.val = function(value) {
        var elm, l, len1, ref, ref1, ref2;
        if (arguments.length) {
          ref = this;
          for (l = 0, len1 = ref.length; l < len1; l++) {
            elm = ref[l];
            elm.val(value);
          }
          return this;
        } else {
          return (ref1 = (ref2 = this.first()) != null ? ref2.val() : void 0) != null ? ref1 : null;
        }
      };

      SIMArray.prototype.width = function(value) {
        var elm, l, len1, ref, ref1, ref2;
        if (arguments.length) {
          ref = this;
          for (l = 0, len1 = ref.length; l < len1; l++) {
            elm = ref[l];
            elm.width(value);
          }
          return this;
        } else {
          return (ref1 = (ref2 = this.first()) != null ? ref2.width() : void 0) != null ? ref1 : 0;
        }
      };

      return SIMArray;

    })();
    SIMBase = (function() {
      function SIMBase(dom) {
        var ex;
        Object.defineProperty(this, '__dom', {
          value: dom
        });
        Object.defineProperty(this, '__handlers', {
          value: Object.create(null)
        });
        Object.defineProperty(this, '__data', {
          value: Object.create(null)
        });
        try {
          Object.defineProperty(dom, '__sim__', {
            value: this
          });
        } catch (error) {
          ex = error;
        }
      }

      return SIMBase;

    })();
    Object.defineProperties(SIMBase.prototype, {
      nodeType: {
        get: function() {
          return this.__dom.nodeType;
        }
      }
    });
    SIMElement = (function(superClass) {
      extend1(SIMElement, superClass);


      /*
      		@param {String|SIMElement} tag
      		@param {SIMElement} [parent]
      		@param {String} [props]
      		@param {Function} [next]
       */

      function SIMElement(tag, parent, props, next) {
        var attr, klass, l, len1, len2, q, ref, ref1;
        if ('function' === typeof props) {
          next = props;
          props = void 0;
        }
        if ('string' === typeof parent) {
          props = parent;
          parent = null;
        }
        if (parent != null) {
          check(parent, SIMElement);
        }
        if (tag instanceof SIMElement) {
          SIMElement.__super__.constructor.call(this, tag.__dom);
        } else if (JQUERY && tag instanceof window.jQuery) {
          SIMElement.__super__.constructor.call(this, tag[0]);
        } else if (tag.nodeName) {
          SIMElement.__super__.constructor.call(this, tag);
        } else if ('string' === typeof tag) {
          if (this.constructor.NS != null) {
            SIMElement.__super__.constructor.call(this, window.document.createElementNS(this.constructor.NS, tag));
          } else {
            SIMElement.__super__.constructor.call(this, window.document.createElement(tag));
          }
        } else {
          throw new Error("Invalid arguments.");
        }
        if ('string' === typeof props) {
          props = parse(props)[0];
          if (props.id != null) {
            this.attr('id', props.id);
          }
          if (props["class"] != null) {
            ref = props["class"];
            for (l = 0, len1 = ref.length; l < len1; l++) {
              klass = ref[l];
              this.addClass(klass);
            }
          }
          if (props.attribute != null) {
            ref1 = props.attribute;
            for (q = 0, len2 = ref1.length; q < len2; q++) {
              attr = ref1[q];
              this.attr(attr.name, attr.value);
            }
          }
        }
        if (parent != null) {
          this.appendTo(parent);
        }
        if (next != null) {
          next.call(this);
        }
      }

      SIMElement.prototype.addClass = function(names) {
        var classes, l, len1, name, ref;
        if ('string' !== typeof names) {
          return this;
        }
        classes = this.__dom.className.length === 0 ? [] : this.__dom.className.split(' ');
        ref = names.split(' ');
        for (l = 0, len1 = ref.length; l < len1; l++) {
          name = ref[l];
          if (indexOf.call(classes, name) < 0) {
            classes.push(name);
          }
        }
        this.__dom.className = classes.join(' ');
        return this;
      };

      SIMElement.prototype.after = function(children) {
        var child, l, len1;
        children = simArray(children).reverse();
        for (l = 0, len1 = children.length; l < len1; l++) {
          child = children[l];
          this.__dom.parentNode.insertBefore(child.__dom, this.__dom.nextSibling);
        }
        return this;
      };

      SIMElement.prototype.append = function(children) {
        var child, l, len1;
        children = simArray(children);
        for (l = 0, len1 = children.length; l < len1; l++) {
          child = children[l];
          this.__dom.appendChild(child.__dom);
        }
        return this;
      };

      SIMElement.prototype.attr = function(key, value) {
        if (arguments.length === 1) {
          return this.__dom.getAttribute(key);
        } else {
          if (value != null) {
            if ((key === 'disabled' || key === 'checked') && (value === true || value === false)) {
              if (value) {
                this.__dom.setAttribute(key, key);
              } else {
                this.__dom.removeAttribute(key);
              }
            } else {
              this.__dom.setAttribute(key, value);
            }
          } else {
            this.__dom.removeAttribute(key);
          }
          return this;
        }
      };

      SIMElement.prototype.appendTo = function(parent) {
        parent = sim(parent);
        parent.append(this);
        return this;
      };

      SIMElement.prototype.before = function(children) {
        var child, l, len1, ref;
        children = simArray(children);
        for (l = 0, len1 = children.length; l < len1; l++) {
          child = children[l];
          if ((ref = this.__dom.parentNode) != null) {
            ref.insertBefore(child.__dom, this.__dom);
          }
        }
        return this;
      };

      SIMElement.prototype.blur = function() {
        this.__dom.blur();
        return this;
      };

      SIMElement.prototype.css = function(key, value) {
        var styles;
        if ('object' === typeof key) {
          styles = key;
        } else if (arguments.length > 1) {
          styles = {};
          styles[key] = value;
        }
        if (styles == null) {
          if (this.__dom.ownerDocument.body.contains(this.__dom)) {
            return this.__dom.ownerDocument.defaultView.getComputedStyle(this.__dom, null).getPropertyValue(key);
          } else {
            key = normalizeCssKey(key);
            return this.__dom.style[key];
          }
        } else {
          for (key in styles) {
            value = styles[key];
            key = normalizeCssKey(key);
            value = normalizeCssValue(key, value);
            if (value != null) {
              this.__dom.style[key] = value;
            } else {
              delete this.__dom.style[key];
            }
          }
          return this;
        }
      };

      SIMElement.prototype.closest = function(selector) {
        var conditions, parent;
        conditions = parse(selector);
        parent = SIMElement.prototype.parent.call(this);
        if (!parent) {
          return null;
        }
        while (!matches(parent, conditions)) {
          parent = SIMElement.prototype.parent.call(parent);
          if (parent == null) {
            return null;
          }
        }
        return parent;
      };

      SIMElement.prototype.contains = function(descendants) {
        var descendant, l, len1;
        descendants = simArray(descendants);
        if (descendants.length === 0) {
          return false;
        }
        for (l = 0, len1 = descendants.length; l < len1; l++) {
          descendant = descendants[l];
          if (descendant === this) {
            return false;
          }
          if (!this.__dom.contains(descendant.__dom)) {
            return false;
          }
        }
        return true;
      };

      SIMElement.prototype.contents = function() {
        return simArray(Array.prototype.slice.call(this.__dom.childNodes));
      };

      SIMElement.prototype.clone = function(withDataAndEvents) {
        var elm, event, fn, l, len1, len2, o, oo, q, ref, ref1, ref2, ref3, ref4, ref5, selector;
        elm = sim(this.__dom.cloneNode(true));
        if (withDataAndEvents) {
          ref = this.__handlers;
          for (event in ref) {
            o = ref[event];
            ref2 = (ref1 = o.original) != null ? ref1 : [];
            for (l = 0, len1 = ref2.length; l < len1; l++) {
              fn = ref2[l];
              elm.on(event, fn);
            }
            ref3 = o.selector;
            for (selector in ref3) {
              oo = ref3[selector];
              ref5 = (ref4 = oo.original) != null ? ref4 : [];
              for (q = 0, len2 = ref5.length; q < len2; q++) {
                fn = ref5[q];
                elm.on(event, selector, fn);
              }
            }
          }
        }
        return elm;
      };

      SIMElement.prototype.data = function(key, value) {
        var attr, l, len1, obj, ref, ref1;
        if (arguments.length === 0) {
          obj = {};
          ref = this.__dom.attributes;
          for (l = 0, len1 = ref.length; l < len1; l++) {
            attr = ref[l];
            if (/^data-(.*)$/.exec(attr.name)) {
              obj[RegExp.$1] = attr.value;
            }
          }
          ref1 = this.__data;
          for (key in ref1) {
            value = ref1[key];
            obj[key] = value;
          }
          return obj;
        } else if (arguments.length === 1) {
          if (this.__data[key] != null) {
            return this.__data[key];
          }
          return this.__dom.getAttribute("data-" + key);
        } else {
          if ('object' === typeof value) {
            if (this.__dom.hasAttribute("data-" + key)) {
              this.__dom.removeAttribute("data-" + key);
            }
            this.__data[key] = value;
          } else {
            this.__data[key] = value;
            this.__dom.setAttribute("data-" + key, value);
          }
          return this;
        }
      };

      SIMElement.prototype.detach = function() {
        return this.remove.apply(this, arguments);
      };

      SIMElement.prototype["do"] = function(method) {
        method.call(this);
        return this;
      };


      /*
      		@param {String} name Event name.
      		@param {Object} [options] Event options.
      		
      		**Options:**
      		- `bubbles` - Is a Boolean indicating whether the event bubbles up through the DOM or not.
      		- `cancelable` - Is a Boolean indicating whether the event is cancelable.
      		- `detail` - Event detail.
       */

      SIMElement.prototype.emit = function(name, options) {
        var event, jq, klass, ref, ref1;
        if (options == null) {
          options = {};
        }
        if (FF && this.__dom.disabled) {
          return;
        }
        if (BOOTSTRAP_EVENT.test(name)) {
          jq = this.toJquery();
          jq.trigger.apply(jq, arguments);
        } else {
          if ('string' === typeof name) {
            klass = (ref = EVENT_CONSTRUCTOR[name]) != null ? ref : 'CustomEvent';
            try {
              event = new window[klass](name, options);
            } catch (error) {
              event = ((ref1 = this.__dom.ownerDocument) != null ? ref1 : this.__dom.document).createEvent(klass);
              ALTERNATIVE_EVENT_CONSTRUCTORS[klass].call(event, name, options);
            }
          } else {
            throw new Error("Invalid arguments.");
          }
          this.__dom.dispatchEvent(event);
        }
        return this;
      };

      SIMElement.prototype.empty = function() {
        while (this.__dom.hasChildNodes()) {
          this.__dom.removeChild(this.__dom.lastChild);
        }
        return this;
      };

      SIMElement.prototype.find = function(selector) {
        if (selector == null) {
          return new SIMArray;
        }
        if ('string' === typeof selector) {
          return simArray(queryAll(this.__dom, selector));
        } else {
          throw new Error("Invalid arguments.");
        }
      };

      SIMElement.prototype.findOne = function(selector) {
        if (selector == null) {
          return null;
        }
        return sim(query(this.__dom, selector));
      };

      SIMElement.prototype.focus = function() {
        this.__dom.focus();
        return this;
      };

      SIMElement.prototype.hasClass = function(names) {
        var classes, l, len1, name, ref;
        if (this.__dom.className.length === 0) {
          return false;
        }
        classes = this.__dom.className.split(' ');
        ref = names.split(' ');
        for (l = 0, len1 = ref.length; l < len1; l++) {
          name = ref[l];
          if (indexOf.call(classes, name) < 0) {
            return false;
          }
        }
        return true;
      };

      SIMElement.prototype.height = function(value) {
        var h;
        if (arguments.length) {
          this.css('height', 'string' === typeof value ? value : value + "px");
          return this;
        } else {
          if (this.is(':visible')) {
            return this.__dom.offsetHeight;
          } else {
            h = parseFloat(this.css('height'));
            if (isNaN(h)) {
              return 0;
            }
            return h;
          }
        }
      };

      SIMElement.prototype.hide = function() {
        return this.css('display', 'none');
      };

      SIMElement.prototype.html = function(value) {
        if (arguments.length) {
          this.__dom.innerHTML = value;
          return this;
        } else {
          return this.__dom.innerHTML;
        }
      };

      SIMElement.prototype.children = function(selector) {
        return filter(simArray(Array.prototype.slice.call(this.__dom.childNodes)), selector);
      };

      SIMElement.prototype.insertAfter = function(elms) {
        var elm, l, len1;
        elms = simArray(elms);
        for (l = 0, len1 = elms.length; l < len1; l++) {
          elm = elms[l];
          SIMElement.prototype.after.call(elm, this);
        }
        return this;
      };

      SIMElement.prototype.insertBefore = function(elms) {
        var elm, l, len1;
        elms = simArray(elms);
        for (l = 0, len1 = elms.length; l < len1; l++) {
          elm = elms[l];
          SIMElement.prototype.before.call(elm, this);
        }
        return this;
      };

      SIMElement.prototype.inspect = function() {
        return "[SIMElement " + (this.__dom.nodeName.toLowerCase()) + (this.__dom.id ? "#" + this.__dom.id : "") + "]";
      };

      SIMElement.prototype.is = function(selector) {
        return matches(this, parse(selector));
      };

      SIMElement.prototype.next = function(selector) {
        var elm;
        elm = sim(this.__dom.nextSibling);
        if (elm == null) {
          return null;
        }
        if (selector != null) {
          if (!matches(elm, parse(selector))) {
            return null;
          }
        }
        return elm;
      };

      SIMElement.prototype.nextAll = function(selector) {
        var index;
        if (!this.__dom.parentNode) {
          return simArray();
        }
        index = Array.prototype.indexOf.call(this.__dom.parentNode.childNodes, this.__dom);
        if (index === -1) {
          return simArray();
        }
        return filter(simArray(Array.prototype.slice.call(this.__dom.parentNode.childNodes, index + 1)), selector);
      };

      SIMElement.prototype.off = function(events, selector, handler) {
        var event, fn, index, l, len1, ref, ref1, ref2, ref3;
        if ('function' === typeof selector) {
          handler = selector;
          selector = void 0;
        }
        fn = handler;
        if (events == null) {
          events = Object.keys(this.__handlers).join(' ');
        }
        ref = events.split(' ');
        for (l = 0, len1 = ref.length; l < len1; l++) {
          event = ref[l];
          if (FF) {
            if (event === 'focusin') {
              event = 'focus';
            } else if (event === 'focusout') {
              event = 'blur';
            }
          }
          if (event === 'wheel' || event === 'mousewheel') {
            event = WHEEL_EVENT;
          }
          if (selector) {
            index = (ref1 = this.__handlers[event]) != null ? (ref2 = ref1.selector[selector]) != null ? ref2.original.indexOf(handler) : void 0 : void 0;
            if ((index == null) || index === -1) {
              return this;
            }
            fn = this.__handlers[event].selector[selector].temporary[index];
            this.__handlers[event].selector[selector].original.splice(index, 1);
            this.__handlers[event].selector[selector].temporary.splice(index, 1);
          } else {
            index = (ref3 = this.__handlers[event]) != null ? ref3.original.indexOf(handler) : void 0;
            if ((index == null) || index === -1) {
              return this;
            }
            fn = this.__handlers[event].temporary[index];
            this.__handlers[event].original.splice(index, 1);
            this.__handlers[event].temporary.splice(index, 1);
          }
          if (BOOTSTRAP_EVENT.test(event)) {
            this.toJquery().off(event, fn);
          } else {
            this.__dom.removeEventListener(event, fn);
          }
        }
        return this;
      };

      SIMElement.prototype.offset = function() {
        var bounds;
        bounds = this.__dom.getBoundingClientRect();
        return {
          left: bounds.left + this.__dom.ownerDocument.defaultView.pageXOffset,
          top: bounds.top + this.__dom.ownerDocument.defaultView.pageYOffset
        };
      };


      /*
      		@param {String} events Space separated list of event to handle.
      		@param {String} [selector] Optional target selector.
      		@param {Function} handler Event handler.
       */

      SIMElement.prototype.on = function(events, selector, handler, _once) {
        var base, base1, capture, event, fn, index, jqevt, l, len1, ref, ref1, self;
        if ('function' === typeof selector) {
          handler = selector;
          selector = void 0;
        }
        if ('function' !== typeof handler) {
          throw new Error("Invalid arguments.");
        }
        self = this;
        jqevt = false;
        capture = void 0;
        ref = events.split(' ');
        for (l = 0, len1 = ref.length; l < len1; l++) {
          event = ref[l];
          if (FF) {
            if (event === 'focusin') {
              event = 'focus';
              capture = true;
            } else if (event === 'focusout') {
              event = 'blur';
              capture = true;
            }
          }
          if (event === 'wheel' || event === 'mousewheel') {
            event = WHEEL_EVENT;
          }
          if ((base = this.__handlers)[event] == null) {
            base[event] = {
              original: [],
              temporary: [],
              selector: Object.create(null)
            };
          }
          if (selector) {
            index = (ref1 = this.__handlers[event].selector[selector]) != null ? ref1.original.indexOf(handler) : void 0;
            if ((index != null) && index !== -1) {
              return this;
            }
            fn = function(e) {
              var closest, eventType, ret, target;
              if (_once) {
                eventType = jqevt ? "" + e.type + (e.namespace ? "." + e.namespace : '') : e.type;
                SIMElement.prototype.off.call(self, eventType, selector, handler);
              }
              target = sim(e.target);
              if (target.is(selector)) {
                ret = handler.apply(target, arguments);
                if (ret === false) {
                  if (typeof e.preventDefault === "function") {
                    e.preventDefault();
                  }
                }
                return ret;
              }
              closest = target.closest(selector);
              if (closest) {
                ret = handler.apply(closest, arguments);
                if (ret === false) {
                  if (typeof e.preventDefault === "function") {
                    e.preventDefault();
                  }
                }
                return ret;
              }
              return null;
            };
            if ((base1 = this.__handlers[event].selector)[selector] == null) {
              base1[selector] = {
                original: [],
                temporary: []
              };
            }
            this.__handlers[event].selector[selector].original.push(handler);
            this.__handlers[event].selector[selector].temporary.push(fn);
          } else {
            index = this.__handlers[event].original.indexOf(handler);
            if ((index != null) && index !== -1) {
              return this;
            }
            fn = function(e) {
              var eventType, ret;
              if (_once) {
                eventType = jqevt ? "" + e.type + (e.namespace ? "." + e.namespace : '') : e.type;
                SIMElement.prototype.off.call(self, eventType, selector, handler);
              }
              if (e.type === 'DOMMouseScroll') {
                e.wheelDelta = e.detail * -20;
              }
              ret = handler.call(self, e);
              if (ret === false) {
                if (typeof e.preventDefault === "function") {
                  e.preventDefault();
                }
              }
              return ret;
            };
            this.__handlers[event].original.push(handler);
            this.__handlers[event].temporary.push(fn);
          }
          if (BOOTSTRAP_EVENT.test(event)) {
            jqevt = true;
            this.toJquery().on(event, fn);
          } else {
            this.__dom.addEventListener(event, fn, capture);
          }
        }
        return this;
      };

      SIMElement.prototype.once = function(event, selector, handler) {
        if ('function' === typeof selector) {
          handler = selector;
          selector = void 0;
        }
        SIMElement.prototype.on.call(this, event, selector, handler, true);
        return this;
      };

      SIMElement.prototype.outerHeight = function(margin) {
        var add, m;
        add = 0;
        if (margin) {
          m = parseFloat(this.css('margin-top'));
          if (!isNaN(m)) {
            add += m;
          }
          m = parseFloat(this.css('margin-bottom'));
          if (!isNaN(m)) {
            add += m;
          }
        }
        return SIMElement.prototype.height.call(this) + add;
      };

      SIMElement.prototype.outerWidth = function(margin) {
        var add, m;
        add = 0;
        if (margin) {
          m = parseFloat(this.css('margin-left'));
          if (!isNaN(m)) {
            add += m;
          }
          m = parseFloat(this.css('margin-right'));
          if (!isNaN(m)) {
            add += m;
          }
        }
        return SIMElement.prototype.width.call(this) + add;
      };

      SIMElement.prototype.parent = function() {
        if (this.__dom.parentNode === this.__dom.ownerDocument) {
          return null;
        }
        return sim(this.__dom.parentNode);
      };

      SIMElement.prototype.prepend = function(children) {
        var child, l, len1;
        children = simArray(children).reverse();
        for (l = 0, len1 = children.length; l < len1; l++) {
          child = children[l];
          if (this.__dom.hasChildNodes()) {
            this.__dom.insertBefore(child.__dom, this.__dom.firstChild);
          } else {
            this.__dom.appendChild(child.__dom);
          }
        }
        return this;
      };

      SIMElement.prototype.prependTo = function(parent) {
        parent = sim(parent);
        SIMElement.prototype.prepend.call(parent, this);
        return this;
      };

      SIMElement.prototype.prev = function(selector) {
        var elm;
        elm = sim(this.__dom.previousSibling);
        if (elm == null) {
          return null;
        }
        if (selector != null) {
          if (!matches(elm, parse(selector))) {
            return null;
          }
        }
        return elm;
      };

      SIMElement.prototype.prevAll = function(selector) {
        var index;
        if (!this.__dom.parentNode) {
          return simArray();
        }
        index = Array.prototype.indexOf.call(this.__dom.parentNode.childNodes, this.__dom);
        if (index <= 0) {
          return simArray();
        }
        return filter(simArray(Array.prototype.slice.call(this.__dom.parentNode.childNodes, 0, index)), selector);
      };

      SIMElement.prototype.prop = function(key, value) {
        if (arguments.length === 1) {
          return this.__dom[key];
        } else {
          if (key === 'disabled' || key === 'selected' || key === 'checked') {
            if (value) {
              this.__dom.setAttribute(key, key);
            } else {
              this.__dom.removeAttribute(key);
            }
          }
          this.__dom[key] = value;
          return this;
        }
      };

      SIMElement.prototype.remove = function(child) {
        var ref;
        if (child == null) {
          if ((ref = this.__dom.parentNode) != null) {
            ref.removeChild(this.__dom);
          }
          return this;
        }
        child = sim(child);
        this.__dom.removeChild(child.__dom);
        return this;
      };

      SIMElement.prototype.removeClass = function(names) {
        var classes, index, l, len1, name, ref;
        if (this.__dom.className.length === 0) {
          return this;
        }
        classes = this.__dom.className.split(' ');
        ref = names.split(' ');
        for (l = 0, len1 = ref.length; l < len1; l++) {
          name = ref[l];
          index = classes.indexOf(name);
          if (index !== -1) {
            classes.splice(index, 1);
          }
          if (classes.length === 0) {
            this.__dom.className = classes.join(' ');
            return this;
          }
        }
        this.__dom.className = classes.join(' ');
        return this;
      };

      SIMElement.prototype.replaceWith = function(children) {
        var child, l, len1, ref, ref1;
        children = simArray(children);
        for (l = 0, len1 = children.length; l < len1; l++) {
          child = children[l];
          if ((ref = this.__dom.parentNode) != null) {
            ref.insertBefore(child.__dom, this.__dom);
          }
        }
        if ((ref1 = this.__dom.parentNode) != null) {
          ref1.removeChild(this.__dom);
        }
        return this;
      };

      SIMElement.prototype.scrollLeft = function() {
        return this.__dom.scrollLeft;
      };

      SIMElement.prototype.scrollTop = function() {
        return this.__dom.scrollTop;
      };

      SIMElement.prototype.show = function() {
        return SIMElement.prototype.css.call(this, 'display', 'block');
      };

      SIMElement.prototype.text = function(value) {
        if (arguments.length) {
          this.__dom.textContent = value;
          return this;
        } else {
          return this.__dom.textContent;
        }
      };

      SIMElement.prototype.toggleClass = function(names) {
        var l, len1, name, ref;
        ref = names.split(' ');
        for (l = 0, len1 = ref.length; l < len1; l++) {
          name = ref[l];
          if (this.hasClass(name)) {
            this.removeClass(name);
          } else {
            this.addClass(name);
          }
        }
        return this;
      };

      SIMElement.prototype.toString = function() {
        return this.__dom.outerHTML;
      };

      SIMElement.prototype.trigger = function() {
        return SIMElement.prototype.emit.apply(this, arguments);
      };

      SIMElement.prototype.val = function(value) {
        if (arguments.length) {
          this.__dom.value = value != null ? value : '';
          return this;
        } else {
          return this.__dom.value;
        }
      };

      SIMElement.prototype.width = function(value) {
        var w;
        if (arguments.length) {
          this.css('width', 'string' === typeof value ? value : value + "px");
          return this;
        } else {
          if (this.is(':visible')) {
            return this.__dom.offsetWidth;
          } else {
            w = parseFloat(this.css('width'));
            if (isNaN(w)) {
              return 0;
            }
            return w;
          }
        }
      };

      SIMElement.prototype.write = function(text) {
        if (/&#?([a-z0-9]+);/gi.test(text)) {
          text = sim.div().html(sanitize(text)).text();
        }
        return SIMElement.prototype.append.call(this, new SIMText(text));
      };

      return SIMElement;

    })(SIMBase);
    Object.defineProperties(SIMElement.prototype, {
      enabled: {
        get: function() {
          return !this.is(':disabled');
        },
        set: function(value) {
          return this.prop('disabled', !value);
        }
      },
      checked: {
        get: function() {
          return this.is(':checked');
        },
        set: function(value) {
          return this.prop('checked', value);
        }
      },
      value: {
        get: function() {
          return this.val();
        },
        set: function(value) {
          return this.val(value);
        }
      },
      visible: {
        get: function() {
          return this.is(':visible');
        },
        set: function(value) {
          return this[value ? 'show' : 'hide']();
        }
      }
    });
    SIMText = (function(superClass) {
      extend1(SIMText, superClass);

      function SIMText(text) {
        if (text == null) {
          SIMText.__super__.constructor.call(this, window.document.createTextNode(''));
        } else if ('string' === typeof text) {
          SIMText.__super__.constructor.call(this, window.document.createTextNode(text));
        } else if (text.nodeType === 3) {
          SIMText.__super__.constructor.call(this, text);
        } else {
          throw new Error("Invalid arguments.");
        }
      }

      SIMText.prototype.after = SIMElement.prototype.after;

      SIMText.prototype.appendTo = SIMElement.prototype.appendTo;

      SIMText.prototype.before = SIMElement.prototype.before;

      SIMText.prototype.closest = function() {
        return null;
      };

      SIMText.prototype.detach = SIMElement.prototype.detach;

      SIMText.prototype.hasClass = function() {
        return false;
      };

      SIMText.prototype.prependTo = SIMElement.prototype.prependTo;

      SIMText.prototype.insertBefore = SIMElement.prototype.insertBefore;

      SIMText.prototype.insertAfter = SIMElement.prototype.insertAfter;

      SIMText.prototype.inspect = function() {
        return "[SIMText '" + this.__dom.textContent + "']";
      };

      SIMText.prototype.is = function() {
        return false;
      };

      SIMText.prototype.next = SIMElement.prototype.next;

      SIMText.prototype.nextAll = SIMElement.prototype.nextAll;

      SIMText.prototype.parent = SIMElement.prototype.parent;

      SIMText.prototype.prev = SIMElement.prototype.prev;

      SIMText.prototype.prevAll = SIMElement.prototype.prevAll;

      SIMText.prototype.remove = SIMElement.prototype.remove;

      SIMText.prototype.text = SIMElement.prototype.text;

      return SIMText;

    })(SIMBase);
    SIMDocument = (function(superClass) {
      extend1(SIMDocument, superClass);

      function SIMDocument() {
        return SIMDocument.__super__.constructor.apply(this, arguments);
      }

      SIMDocument.prototype.closest = function() {
        return null;
      };

      SIMDocument.prototype.emit = SIMElement.prototype.emit;

      SIMDocument.prototype.height = function() {
        return window.document.documentElement.offsetHeight;
      };

      SIMDocument.prototype.inspect = function() {
        return "[SIMDocument]";
      };

      SIMDocument.prototype.is = function(selector) {
        return selector === 'document';
      };

      SIMDocument.prototype.on = SIMElement.prototype.on;

      SIMDocument.prototype.once = SIMElement.prototype.once;

      SIMDocument.prototype.off = SIMElement.prototype.off;

      SIMDocument.prototype.toString = function() {
        return "<!DOCTYPE html>" + this.__dom.documentElement.outerHTML;
      };

      SIMDocument.prototype.trigger = SIMElement.prototype.trigger;

      SIMDocument.prototype.width = function() {
        return window.document.documentElement.offsetWidth;
      };

      return SIMDocument;

    })(SIMBase);
    SIMWindow = (function(superClass) {
      extend1(SIMWindow, superClass);

      function SIMWindow() {
        return SIMWindow.__super__.constructor.apply(this, arguments);
      }

      SIMWindow.prototype.closest = function() {
        return null;
      };

      SIMWindow.prototype.emit = SIMElement.prototype.emit;

      SIMWindow.prototype.height = function() {
        return window.document.documentElement.clientHeight;
      };

      SIMWindow.prototype.inspect = function() {
        return "[SIMWindow]";
      };

      SIMWindow.prototype.is = function() {
        return false;
      };

      SIMWindow.prototype.on = SIMElement.prototype.on;

      SIMWindow.prototype.once = SIMElement.prototype.once;

      SIMWindow.prototype.off = SIMElement.prototype.off;

      SIMWindow.prototype.open = function() {
        return window.open.apply(window, arguments);
      };

      SIMWindow.prototype.scrollLeft = function() {
        return this.__dom.pageXOffset;
      };

      SIMWindow.prototype.scrollTop = function() {
        return this.__dom.pageYOffset;
      };

      SIMWindow.prototype.toString = function() {
        return this.inspect();
      };

      SIMWindow.prototype.trigger = SIMElement.prototype.trigger;

      SIMWindow.prototype.width = function() {
        return window.document.documentElement.clientWidth;
      };

      return SIMWindow;

    })(SIMBase);
    Object.defineProperties(SIMWindow.prototype, {
      devicePixelRatio: {
        get: function() {
          var ref;
          return (ref = this.__dom.devicePixelRatio) != null ? ref : 1;
        }
      },
      document: {
        get: function() {
          return sim(window.document);
        }
      },
      history: {
        get: function() {
          return window.history;
        }
      },
      location: {
        get: function() {
          return window.location;
        },
        set: function(value) {
          return window.location = value;
        }
      }
    });
    sim.create = function(tag, parent, props) {
      var klass, ref;
      klass = this.prototype instanceof SIMElement ? this : SIMElement;
      if (HAS_COMPONENTS && /@([-a-z0-9_]+)/i.exec(props)) {
        return (function(func, args, ctor) {
          ctor.prototype = func.prototype;
          var child = new ctor, result = func.apply(child, args);
          return Object(result) === result ? result : child;
        })((ref = COMPONENT[RegExp.$1]) != null ? ref : klass, arguments, function(){});
      } else {
        return (function(func, args, ctor) {
          ctor.prototype = func.prototype;
          var child = new ctor, result = func.apply(child, args);
          return Object(result) === result ? result : child;
        })(klass, arguments, function(){});
      }
    };
    sim.one = function() {
      var res;
      res = sim.apply(null, arguments);
      if (res instanceof SIMArray) {
        res = res.first();
      }
      return res;
    };
    sim.array = function() {
      var args;
      args = 1 <= arguments.length ? slice.call(arguments, 0) : [];
      if (args.length === 0) {
        return new SIMArray;
      }
      if (args.length === 1) {
        return new SIMArray(args[0]);
      }
      return new SIMArray(args);
    };
    sim.html = sim.create.bind(SIMElement, 'html', null);
    sim.text = function(text) {
      return new SIMText(text);
    };
    sim.ready = function(handler) {
      var l, len1, listener;
      if (arguments.length === 0) {
        if (sim.isReady) {
          return;
        }
        sim.isReady = true;
        for (l = 0, len1 = READY_LISTENERS.length; l < len1; l++) {
          listener = READY_LISTENERS[l];
          listener();
        }
        READY_LISTENERS = null;
        return;
      }
      if (sim.isReady) {
        return setImmediate(handler);
      }
      READY_LISTENERS.push(handler);
      return this;
    };
    sim.registerComponent = function(name, klass, init) {
      if (init == null) {
        init = false;
      }
      if (!(klass.prototype instanceof SIMElement)) {
        throw new Error("Invalid arguments.");
      }
      COMPONENT[name] = klass;
      HAS_COMPONENTS = true;
      if (init) {
        sim("[sim-component=\"" + name + "\"]");
      }
      return this;
    };
    sim.registerNamespace = function(name, klass) {
      if (!(klass.prototype instanceof SIMElement)) {
        throw new Error("Invalid arguments.");
      }
      NAMESPACE[name] = klass;
      return this;
    };
    sim.css = function(name, style) {
      var elm, key, value;
      if (CSS_SHEET == null) {
        elm = window.document.createElement('style');
        window.document.head.appendChild(elm);
        CSS_SHEET = elm.sheet;
      }
      CSS_SHEET.insertRule(name + " {" + (((function() {
        var results;
        results = [];
        for (key in style) {
          value = style[key];
          results.push(key + ": " + value);
        }
        return results;
      })()).join('; ')) + "}", 0);
      return null;
    };
    sim.cookies = {
      get: function(name) {
        var c, ca, l, len1;
        name += "=";
        ca = window.document.cookie.split(';');
        for (l = 0, len1 = ca.length; l < len1; l++) {
          c = ca[l];
          while (' ' === c.charAt(0)) {
            c = c.substring(1, c.length);
          }
          if (0 === c.indexOf(name)) {
            return c.substring(name.length, c.length);
          }
        }
        return null;
      },
      set: function(name, value, minutes) {
        var date, expires;
        if (value == null) {
          value = "";
          minutes = -1;
        }
        if (minutes) {
          date = new Date();
          date.setTime(date.getTime() + minutes * 60 * 1000);
          expires = "; expires=" + (date.toGMTString());
        } else {
          expires = "";
        }
        return window.document.cookie = name + "=" + value + expires + "; path=/";
      }
    };
    sim.parse = function(html) {
      var wrapper;
      wrapper = window.document.createElement('div');
      wrapper.innerHTML = html;
      return sim.array.apply(sim, wrapper.childNodes);
    };
    sim.render = function(next) {
      var container;
      container = sim.div();
      next.call(container);
      return container.html();
    };
    sim.SIMElement = SIMElement;
    sim.SIMArray = SIMArray;
    sim.SIMDocument = SIMDocument;
    sim.SIMWindow = SIMWindow;
    sim.SIMText = SIMText;
    (function() {
      var fn1, fn2, l, len1, len2, name, q, tag;
      fn1 = function(tag) {
        if (!SIMElement.prototype.hasOwnProperty(tag)) {
          return Object.defineProperty(SIMElement.prototype, tag, {
            enumerable: false,
            configurable: true,
            writable: true,
            value: function() {
              var ref;
              return (ref = sim.create).call.apply(ref, [SIMElement, tag, this].concat(slice.call(arguments)));
            }
          });
        }
      };
      for (l = 0, len1 = TAGS.length; l < len1; l++) {
        tag = TAGS[l];
        if (!sim.hasOwnProperty(tag)) {
          sim[tag] = sim.create.bind(SIMElement, tag, null);
        }
        fn1(tag);
      }
      if (JQUERY) {
        sim.ajax = window.jQuery.ajax.bind(jQuery);
      }
      fn2 = function(name) {
        SIMElement.prototype[name] = function() {
          var ref;
          if (JQUERY == null) {
            throw new Error("jQuery is required in order to use '" + name + "' method.");
          }
          return (ref = this.toJquery())[name].apply(ref, arguments);
        };
        return SIMArray.prototype[name] = function() {
          var ref;
          if (JQUERY == null) {
            throw new Error("jQuery is required in order to use '" + name + "' method.");
          }
          return (ref = this.toJquery())[name].apply(ref, arguments);
        };
      };
      for (q = 0, len2 = JQUERY_POLYFILLS.length; q < len2; q++) {
        name = JQUERY_POLYFILLS[q];
        fn2(name);
      }
      SIMBase.prototype.toJquery = function() {
        if (!JQUERY) {
          throw new Error("jQuery is required in order to use 'toJquery' method.");
        }
        return window.jQuery(this.__dom);
      };
      return SIMArray.prototype.toJquery = function() {
        var elm;
        if (!JQUERY) {
          throw new Error("jQuery is required in order to use 'toJquery' method.");
        }
        return window.jQuery((function() {
          var len3, ref, results, u;
          ref = this;
          results = [];
          for (u = 0, len3 = ref.length; u < len3; u++) {
            elm = ref[u];
            results.push(elm.__dom);
          }
          return results;
        }).call(this));
      };
    })();
    if (NODE) {
      return require('./mock')(sim);
    }
  })(window != null ? window : null);


  /*!
   * simDOM SVG
   * http://simdom.org/
  
   * Released under the MIT license
   * http://simdom.org/license
   */

  install = function(sim) {
    var SIMSVGElement, SVG_TAGS;
    SVG_TAGS = ['a', 'altGlyph', 'altGlyphDef', 'altGlyphItem', 'animate', 'animateMotion', 'animateTransform', 'circle', 'clipPath', 'color-profile', 'cursor', 'defs', 'desc', 'ellipse', 'g', 'linearGradient', 'path', 'radialGradient', 'stop'];
    SIMSVGElement = (function(superClass) {
      extend1(SIMSVGElement, superClass);

      function SIMSVGElement() {
        return SIMSVGElement.__super__.constructor.apply(this, arguments);
      }

      SIMSVGElement.NS = 'http://www.w3.org/2000/svg';

      SIMSVGElement.prototype.addClass = function(name) {
        var ref;
        if (!this.hasClass(name)) {
          this.attr('class', [name].concat(((ref = this.attr('class')) != null ? ref : '').split(' ')));
        }
        return this;
      };

      SIMSVGElement.prototype.hasClass = function(name) {
        var ref;
        return ((ref = this.attr('class')) != null ? ref : '').split(' ').indexOf(name) !== -1;
      };

      SIMSVGElement.prototype.toString = function() {
        var outerHTML, str;
        str = this.__dom.outerHTML;
        if (str == null) {
          outerHTML = function(elm) {
            var attr, attrs, child;
            attrs = (function() {
              var l, len1, ref, results;
              ref = elm.attributes;
              results = [];
              for (l = 0, len1 = ref.length; l < len1; l++) {
                attr = ref[l];
                results.push(attr.name + "=\"" + (attr.value.replace(/&/g, '&amp;').replace(/"/g, '&quot;')) + "\"");
              }
              return results;
            })();
            if (attrs.length) {
              attrs.unshift('');
            }
            return str = "<" + (elm.nodeName.toLowerCase()) + (attrs.join(' ')) + ">" + ((function() {
              var l, len1, ref, results;
              ref = elm.childNodes;
              results = [];
              for (l = 0, len1 = ref.length; l < len1; l++) {
                child = ref[l];
                results.push(outerHTML(child));
              }
              return results;
            })()) + "</" + (elm.nodeName.toLowerCase()) + ">";
          };
          str = outerHTML(this.__dom);
        }
        return str;
      };

      return SIMSVGElement;

    })(sim.SIMElement);
    sim.SIMSVGElement = SIMSVGElement;
    sim.registerNamespace(SIMSVGElement.NS, SIMSVGElement);
    return (function() {
      var l, len1, results, tag;
      sim.svg = sim.create.bind(SIMSVGElement, 'svg', null);
      Object.defineProperty(sim.SIMElement.prototype, 'svg', {
        enumerable: false,
        configurable: true,
        writable: true,
        value: function() {
          var ref;
          return (ref = sim.create).call.apply(ref, [SIMSVGElement, tag, this].concat(slice.call(arguments)));
        }
      });
      results = [];
      for (l = 0, len1 = SVG_TAGS.length; l < len1; l++) {
        tag = SVG_TAGS[l];
        if (!sim.hasOwnProperty(tag.svg)) {
          sim.svg[tag] = sim.create.bind(SIMSVGElement, tag, null);
        }
        results.push((function(tag) {
          if (!SIMSVGElement.prototype.hasOwnProperty(tag)) {
            return Object.defineProperty(SIMSVGElement.prototype, tag, {
              enumerable: false,
              configurable: true,
              writable: true,
              value: function() {
                var ref;
                return (ref = sim.create).call.apply(ref, [SIMSVGElement, tag, this].concat(slice.call(arguments)));
              }
            });
          }
        })(tag));
      }
      return results;
    })();
  };

  (function(window) {
    if (window == null) {
      return module.exports = install;
    } else {
      return install(window.sim);
    }
  })(window != null ? window : null);

  window.SIMElement = sim.SIMElement;

  window.SIMArray = sim.SIMArray;

  window.$ = window.sim;

  ref = ['tab', 'modal', 'tooltip', 'datetimepicker', 'popover', 'dropdown'];
  fn1 = function(fn) {
    SIMElement.prototype[fn] = function() {
      var ref1;
      return (ref1 = jQuery(this.__dom))[fn].apply(ref1, arguments);
    };
    return SIMArray.prototype[fn] = function() {
      var elm, len2, q, ref1, ref2, results;
      ref1 = this;
      results = [];
      for (q = 0, len2 = ref1.length; q < len2; q++) {
        elm = ref1[q];
        results.push((ref2 = jQuery(elm.__dom))[fn].apply(ref2, arguments));
      }
      return results;
    };
  };
  for (l = 0, len1 = ref.length; l < len1; l++) {
    fn = ref[l];
    fn1(fn);
  }

  SIMArray.prototype.sortOn = function(key, custom) {
    return this.sort(function(a, b) {
      if ('function' === typeof key) {
        a = key(a);
        b = key(b);
      } else {
        a = a[key];
        b = b[key];
      }
      if ('function' === typeof custom) {
        return custom(a, b);
      } else if (String.prototype.localeCompare) {
        return String(a).localeCompare(b);
      } else {
        if (a > b) {
          return 1;
        }
        if (a < b) {
          return -1;
        }
        return 0;
      }
    });
  };

  SIMElement.prototype.show = function() {
    this.css('display', '');
    if (this.css('display') === 'none') {
      this.css('display', 'block');
    }
    return this;
  };

  global = self;

  self.global = global;

  html = sim('html');

  console.log("[imt] build: " + (new Date(html.data('build') * 1000)));

  console.log("[imt] server: " + (html.data('server')));


  /*
   * This caused problem when used with target=_blank link.
  try
  	if global.opener?.imt?
  		sim('body').addClass 'with-hidden-aside'
  catch ex
   */

  global.imt = {
    adblock: true,
    admin: html.data('admin') === 'on',
    config: {},
    env: html.data('env'),
    promo: html.data('promo'),
    electron: global.electron,
    browser: 'unknown/unknown',
    connected: true,
    plugins: [],
    dictionaries: {},
    guide: html.data('guide') === 'on',
    user: {
      id: parseInt(html.data('user')),
      language: html.attr('lang'),
      timezone: html.data('timezone')
    },
    company: {
      id: parseInt(html.data('company')),
      timezone: html.data('company-timezone'),
      minInterval: parseInt(html.data('company-min-interval') || 15)
    },
    remotes: [],
    features: {},
    logo: '<svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg" fill-rule="evenodd" clip-rule="evenodd" stroke-linejoin="round" stroke-miterlimit="1.4"><g fill="#fff" fill-rule="nonzero"><path d="M655.4 611V297c-29.3-10.4-60.8-16-93.6-16s-64.3 5.6-93.6 16V798L655.4 611zM468.2 7.8V199c30-7.6 61.2-11.7 93.6-11.7 32.3 0 63.7 4 93.6 11.8V8C625 2.8 593.7 0 561.8 0c-32 0-63.2 2.7-93.6 7.8zM888.2 378.2L1024 242.4C957.3 146.2 861.4 71.7 749 32v205.4c58 33.6 106.3 82.3 139.2 140.8zM242.4 1024L378 888.3C264.3 824 187.3 702 187.3 561.8c0-138.6 75.4-259.7 187.3-324.4V32C156.3 109 0 317.2 0 561.8 0 753.4 96 922.6 242.4 1024z"/></g></svg>',
    "static": function(url) {
      if (/^(http(s)?:)?\/\//.test(url)) {
        return url;
      } else {
        return "" + (html.data('static')) + (url != null ? url : '');
      }
    },
    l: function(dictionary, key, options) {
      var dict, ref1;
      dict = (ref1 = this.dictionaries[dictionary]) != null ? ref1[this.user.language] : void 0;
      if (!dict) {
        return "##" + key;
      }
      return dict.l(key, options);
    },
    cursor: function() {
      var enabled;
      enabled = JSON.parse(imt.localStorage.getItem('config:fakeCursor'));
      imt.localStorage.setItem('config:fakeCursor', JSON.stringify(!enabled));
      if (enabled) {
        sim('.i-presentation-pointer').remove();
        return false;
      }
      attachFakeCursor();
      return true;
    },
    trace: function(event, payload, callback) {
      payload.organization_id = imt.company.id;
      return Loader.trace(event, payload, callback);
    }
  };

  if (imt.electron) {
    sim('html').addClass('electron');
  }

  (sim('meta[property="x-imt-features"]').attr('content') || '').split(',').forEach(function(feature) {
    if (feature) {
      return imt.features[feature] = true;
    }
  });

  if (imt.env !== 'production') {
    imt.features.private_modules = true;
  }

  if (imt.user.id) {
    if (typeof trackJs !== "undefined" && trackJs !== null) {
      trackJs.configure({
        userId: String(imt.user.id)
      });
    }
  }

  sim.ready(function() {
    var ex, i, key, q, ref1, results;
    console.log("[imt] env:", imt.env);
    console.log("[imt] plugins:", imt.plugins.map(function(item) {
      return item.name + " " + item.version;
    }).join(', '));
    if (imt.adblock && !sim.cookies.get('adblock-reported')) {
      sim.cookies.set('adblock-reported', 'yes');
      new Flash({
        text: imt.l('base', 'common.adblock'),
        icon: '.far.fa-info',
        permanent: true,
        closeable: true
      });
    }
    setImmediate(function() {
      var fade, id, pane, tab;
      if (/^#tab:(.*)$/.exec(global.location.hash)) {
        id = RegExp.$1;
        pane = sim(".tab-pane#" + id);
        if (pane) {
          tab = sim(".nav.nav-tabs > li > a[href=\"#" + id + "\"]");
          if (tab.parent().hasClass('active')) {
            tab.emit("show.bs.tab").emit("shown.bs.tab");
          } else {
            fade = pane.hasClass('fade');
            if (fade) {
              pane.parent().children('.tab-pane').removeClass('fade');
            }
            tab.tab('show');
            if (fade) {
              pane.parent().children('.tab-pane').addClass('fade');
              pane.addClass('in');
            }
          }
        }
      } else {
        sim(".nav-tabs > li > a.active").emit("show.bs.tab").emit("shown.bs.tab");
      }
      return sim(document).on('show.bs.tab', function(event) {
        var target;
        target = sim(event.target);
        if ('no' !== target.data('history')) {
          return window.history.replaceState(null, '', target.attr('href').replace(/^#/, '#tab:'));
        }
      });
    });
    sim('#headernav .guide-reset').on('click', function() {
      return Guide.reset();
    });
    if ('standalone' in window.navigator && window.navigator.standalone) {
      sim(window).on('click', 'a[href]', function() {
        if ('_blank' === this.attr('target')) {
          return;
        }
        window.location.href = this.attr('href');
        return false;
      });
    }
    sim(window).on('click', 'a[data-analytics], button[data-analytics]', function(event) {
      var args, ex;
      try {
        args = JSON.parse(this.data('analytics'));
        if (typeof ga === "function") {
          ga.apply(null, args);
        }
      } catch (error) {
        ex = error;
        console.error("Failed to process anchor analytics.", ex);
      }
      return true;
    });
    sim('meta[property="x-imt-analytics"]').each(function() {
      var args, ex;
      try {
        args = JSON.parse(this.attr('content'));
        return typeof ga === "function" ? ga.apply(null, args) : void 0;
      } catch (error) {
        ex = error;
        return console.error("Failed to process meta analytics.", ex);
      }
    });
    try {
      results = [];
      for (i = q = 0, ref1 = imt.localStorage.length - 1; 0 <= ref1 ? q <= ref1 : q >= ref1; i = 0 <= ref1 ? ++q : --q) {
        key = imt.localStorage.key(i);
        if (/^samples:/.test(key)) {
          imt.localStorage.removeItem(key);
          results.push(i--);
        } else {
          results.push(void 0);
        }
      }
      return results;
    } catch (error) {
      ex = error;
    }
  });

  sim(window).on('popstate', function(event) {
    var ref1;
    if (((ref1 = event.state) != null ? ref1.action : void 0) === 'reload') {
      return window.location.reload();
    }
  });

  sim(window).on('message', function(message) {
    var data, entry, ex, len2, q, ref1, results;
    try {
      if (window.location.origin !== message.origin) {
        return;
      }
      if ('string' !== typeof message.data) {
        return;
      }
      data = JSON.parse(message.data);
      switch (data.action) {
        case 'debug':
          if (Array.isArray(data.data)) {
            ref1 = data.data;
            results = [];
            for (q = 0, len2 = ref1.length; q < len2; q++) {
              entry = ref1[q];
              results.push(console.log.apply(console, ["%c[popup:debug]", "color: #a4a9ae"].concat(slice.call(entry))));
            }
            return results;
          }
      }
    } catch (error) {
      ex = error;
    }
  });

  sim(window).openHelp = function(url) {
    var left, top;
    if (/^kb:\/\/(.*)$/i.test(url)) {
      url = "/" + imt.user.language + "/kb/" + RegExp.$1;
    }
    left = (screen.width - 760) / 2;
    top = (screen.height - 800) / 2;
    return window.open(url, 'help', "scrollbars=yes,toolbar=no,location=no,status=no,menubar=no,width=800,height=800,left=" + left + ",top=" + top);
  };

  sim(window).openPopup = function(url, wid) {
    var left, top;
    left = (screen.width - 1200) / 2;
    top = (screen.height - 700) / 2;
    return window.open(url, wid, "scrollbars=yes,toolbar=no,location=no,status=no,menubar=no,width=1200,height=700,left=" + left + ",top=" + top);
  };

  sim(window).on('click', '.i-open-help', function(event) {
    var ref1;
    sim(window).openHelp((ref1 = this.data('url')) != null ? ref1 : this.attr('href'));
    return false;
  });

  sim(window).on('click', '.i-redirect', function(event) {
    var ref1;
    window.location.href = (ref1 = this.data('url')) != null ? ref1 : this.attr('href');
    return false;
  });

  sim(window).on('click', '.i-popup', function(event) {
    sim(window).openPopup(this.attr('href') || this.data('url'));
    return false;
  });

  sim(window).on('click', '.go-back[data-use-history="yes"]', function(event) {
    window.history.back();
    return false;
  });

  sim(window).on('click', '.btn-click-n-wait', function() {
    if (this.prop('disabled')) {
      return false;
    }
    setImmediate((function(_this) {
      return function() {
        _this.prop('disabled', true);
        return _this.empty().i('.far.fa-circle-notch.fa-spin');
      };
    })(this));
    return true;
  });

  sim(window).on('click', '.dropdown-toggle', function(event) {
    return event.preventDefault();
  });

  global.___gcfg = {
    lang: imt.user.language
  };

  global.require = function(module) {
    var crypto;
    switch (module) {
      case 'moment':
      case 'moment-timezone':
        if (!global.moment) {
          throw new Error("Moment is not present.");
        }
        return global.moment;
      case 'crypto':
        crypto = {
          createHash: function(alg) {
            return {
              update: function(data) {
                return {
                  digest: function(enc) {
                    return '';
                  }
                };
              }
            };
          },
          createHmac: function(alg, key) {
            return {
              update: function(data) {
                return {
                  digest: function(enc) {
                    return '';
                  }
                };
              }
            };
          }
        };
        return crypto;
      default:
        throw new Error("Module '" + module + "' is not present.");
    }
    return null;
  };

  global.guid = function() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      var r, v;
      r = Math.random() * 16 | 0;
      v = c === 'x' ? r : r & 0x3 | 0x8;
      return v.toString(16);
    });
  };

  global.nextTick = global.setImmediate = function(callback) {
    return setTimeout(function() {
      return callback();
    }, 1);
  };

  if (!global.requestAnimationFrame) {
    global.requestAnimationFrame = setImmediate;
  }

  global.repeat = function(interval, callback) {
    return setInterval(callback, interval);
  };

  global.unrepeat = function(interval) {
    return clearInterval(interval);
  };

  global.delay = function(interval, callback) {
    return setTimeout(callback, interval);
  };

  global.undelay = function(interval) {
    return clearTimeout(interval);
  };

  global.noop = function() {};

  global.extend = function(a, b) {
    var key, value;
    if (a === void 0) {
      a = {};
    }
    if (b === void 0) {
      return a;
    }
    for (key in b) {
      value = b[key];
      a[key] = value;
    }
    return a;
  };

  global.escapeHtml = function(value) {
    var map;
    map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;'
    };
    return value = String(value).replace(/[&<>]/g, function(tag) {
      return map[tag] || tag;
    });
  };

  global.deepEqual = function(a, b, key) {
    var debug, index, item, len2, q;
    debug = false;
    if (debug) {
      console.log('A', key, ':', a);
      console.log('B', key, ':', b);
    }
    if ((a == null) || (b == null)) {
      if (debug) {
        console.log((a != null) === (b != null), a, b);
      }
      return (a != null) === (b != null);
    }
    switch (typeof a) {
      case 'undefined':
      case 'string':
      case 'number':
      case 'boolean':
      case 'regexp':
      case 'function':
        if (debug) {
          console.log(a === b, a, b);
        }
        return a === b;
      case 'object':
        if (typeof b !== 'object') {
          return false;
        }
        if (a === null) {
          return b === null;
        } else if (a instanceof Array) {
          if (!(b instanceof Array)) {
            return false;
          }
          if (a.length !== b.length) {
            return false;
          }
          if (debug) {
            console.log('--------------------');
          }
          for (index = q = 0, len2 = a.length; q < len2; index = ++q) {
            item = a[index];
            if (!deepEqual(a[index], b[index], index)) {
              return false;
            }
          }
        } else if (a instanceof Date) {
          if (!(b instanceof Date)) {
            return false;
          }
          return a.getTime() === b.getTime();
        } else {
          if (Object.keys(a).filter(function(i) {
            return a[i] != null;
          }).length !== Object.keys(b).filter(function(i) {
            return b[i] != null;
          }).length) {
            return false;
          }
          if (debug) {
            console.log('--------------------');
          }
          for (key in a) {
            if (!deepEqual(a[key], b[key], key)) {
              return false;
            }
          }
        }
        break;
      default:
        return false;
    }
    return true;
  };

  global.ifNaN = function(num, def) {
    num = parseFloat(num);
    if (isNaN(num)) {
      return def;
    } else {
      return num;
    }
  };

  Object.clone = function(obj) {
    if (obj == null) {
      return null;
    }
    return extend({}, obj);
  };

  Object.cloneDeep = function(obj, options) {
    var key, out, value;
    if (obj === void 0) {
      return void 0;
    }
    if (obj === null) {
      return null;
    }
    if ('object' === typeof obj) {
      if (Array.isArray(obj)) {
        return obj.map(function(o) {
          return Object.cloneDeep(o, options);
        });
      } else if (obj instanceof String || obj instanceof Number || obj instanceof Boolean) {
        return out.valueOf();
      } else if (obj instanceof Date) {
        return new Date(obj.getTime());
      } else if (obj instanceof RegExp) {
        return void 0;
      } else {
        out = {};
        for (key in obj) {
          value = obj[key];
          out[key] = Object.cloneDeep(value, options);
        }
        return out;
      }
    } else if ('function' === typeof obj) {
      if (options != null ? options.preserveFunctions : void 0) {
        return obj;
      }
      return void 0;
    }
    return obj;
  };

  if (Object.assign == null) {
    Object.assign = function() {
      var key, len2, q, source, sources, target, value;
      target = arguments[0], sources = 2 <= arguments.length ? slice.call(arguments, 1) : [];
      for (q = 0, len2 = sources.length; q < len2; q++) {
        source = sources[q];
        if (source != null) {
          for (key in source) {
            value = source[key];
            if (Object.prototype.hasOwnProperty.call(source, key)) {
              target[key] = value;
            }
          }
        }
      }
      return target;
    };
  }

  if (Array.isArray == null) {
    Array.isArray = function(value) {
      return value instanceof Array;
    };
  }

  if (!Array.prototype.indexOf) {
    Object.defineProperty(Array.prototype, "indexOf", {
      enumerable: false,
      writable: true,
      value: function(item) {
        return __indexOf.call(this, item);;
      }
    });
  }

  if (!Array.prototype.some) {
    Object.defineProperty(Array.prototype, "some", {
      enumerable: false,
      writable: true,
      value: function(fce, context) {
        var index, item, len2, q, ref1;
        if (context == null) {
          context = null;
        }
        ref1 = this;
        for (index = q = 0, len2 = ref1.length; q < len2; index = ++q) {
          item = ref1[index];
          if (fce.call(context, item, index, this)) {
            return true;
          }
        }
        return false;
      }
    });
  }

  if (!Array.prototype.find) {
    Object.defineProperty(Array.prototype, "find", {
      enumebrable: false,
      writable: true,
      value: function(fce, context) {
        var index, item, len2, q, ref1;
        if (context == null) {
          context = null;
        }
        ref1 = this;
        for (index = q = 0, len2 = ref1.length; q < len2; index = ++q) {
          item = ref1[index];
          if (fce.call(context, item, index, this)) {
            return item;
          }
        }
        return void 0;
      }
    });
  }

  Object.defineProperty(Array.prototype, "contains", {
    enumerable: false,
    writable: true,
    value: function(item) {
      return this.indexOf(item) !== -1;
    }
  });

  Object.defineProperty(Array.prototype, "clear", {
    enumerable: false,
    writable: true,
    value: function(fce) {
      var item, len2, q, ref1;
      if (fce instanceof Function) {
        ref1 = this;
        for (q = 0, len2 = ref1.length; q < len2; q++) {
          item = ref1[q];
          fce(item);
        }
      }
      return this.splice(0, this.length);
    }
  });

  Object.defineProperty(Array.prototype, "clone", {
    enumerable: false,
    writable: true,
    value: function() {
      return this.slice(0);
    }
  });

  Object.defineProperty(Array.prototype, "append", {
    enumerable: false,
    writable: true,
    value: function(array) {
      return this.push.apply(this, array);
    }
  });

  Object.defineProperty(Array.prototype, "prepend", {
    enumerable: false,
    writable: true,
    value: function(array) {
      return this.unshift.apply(this, array);
    }
  });

  Object.defineProperty(Array.prototype, "remove", {
    enumerable: false,
    writable: true,
    value: function(item) {
      var index;
      index = this.indexOf(item);
      if (index === -1) {
        return null;
      }
      return this.splice(index, 1);
    }
  });

  Object.defineProperty(Array.prototype, "last", {
    enumerable: false,
    writable: true,
    value: function() {
      return this[this.length - 1];
    }
  });

  Object.defineProperty(Array.prototype, "toObject", {
    enumerable: false,
    writable: true,
    value: function(key, value) {
      var item, len2, o, q, ref1;
      o = {};
      ref1 = this;
      for (q = 0, len2 = ref1.length; q < len2; q++) {
        item = ref1[q];
        o[item[key]] = value ? item[value] : item;
      }
      return o;
    }
  });

  Object.defineProperty(Array.prototype, "sortOn", {
    enumerable: false,
    writable: true,
    value: function(key, custom) {
      if (Array.isArray(key)) {
        return this.sort(function(a, b) {
          var c, k, len2, q;
          for (q = 0, len2 = key.length; q < len2; q++) {
            k = key[q];
            if (String.prototype.localeCompare) {
              c = String(a[k]).localeCompare(b[k]);
              if (c !== 0) {
                return c;
              }
            } else {
              if (a[k] > b[k]) {
                return 1;
              }
              if (a[k] < b[k]) {
                return -1;
              }
            }
          }
          return 0;
        });
      } else {
        return this.sort(function(a, b) {
          if ('function' === typeof key) {
            a = key(a);
            b = key(b);
          } else {
            a = a[key];
            b = b[key];
          }
          if ('function' === typeof custom) {
            return custom(a, b);
          } else if (String.prototype.localeCompare) {
            return String(a).localeCompare(b);
          } else {
            if (a > b) {
              return 1;
            }
            if (a < b) {
              return -1;
            }
            return 0;
          }
        });
      }
    }
  });

  Object.defineProperty(Function.prototype, "property", {
    enumerable: false,
    writable: true,
    value: function(prop, desc) {
      if (desc) {
        return Object.defineProperty(this.prototype, prop, desc);
      } else {
        return Object.getOwnPropertyDescriptor(this, prop);
      }
    }
  });

  if (!String.prototype.trim) {
    Object.defineProperty(String.prototype, "trim", {
      enumerable: false,
      writable: true,
      value: function() {
        return this.replace(/^\s+|\s+$/g, '');
      }
    });
  }

  Object.defineProperty(String.prototype, "inject", {
    enumerable: false,
    writable: true,
    value: function(index, text) {
      return "" + (this.substr(0, index)) + text + (this.substr(index));
    }
  });

  Object.defineProperty(String.prototype, "format", {
    enumerable: false,
    writable: true,
    value: function(data, escape) {
      return this.replace(/{{([^}]*)}}/g, function(p) {
        var cur, key, value;
        key = p.substr(2, p.length - 4).split('.');
        if (key.length > 1) {
          cur = data;
          while (cur && key.length) {
            cur = cur[key.shift()];
          }
          value = cur != null ? cur : '';
        } else {
          value = data[key[0]];
        }
        if (escape) {
          value = escapeHtml(value);
        }
        return value;
      });
    }
  });

  Object.defineProperty(String.prototype, "capitalize", {
    enumerable: false,
    writable: true,
    value: function() {
      return this.charAt(0).toUpperCase() + this.slice(1);
    }
  });

  Object.defineProperty(Number.prototype, "toRad", {
    enumerable: false,
    writable: true,
    value: function() {
      return this * (Math.PI / 180);
    }
  });

  Object.defineProperty(Number.prototype, "toDeg", {
    enumerable: false,
    writable: true,
    value: function() {
      return this * (180 / Math.PI);
    }
  });

  Object.defineProperty(Number.prototype, "digits", {
    enumerable: false,
    writable: true,
    value: function(length) {
      var dif, i;
      if (length == null) {
        length = 2;
      }
      dif = length - this.toString().length;
      if (dif > 0) {
        return "" + (((function() {
          var q, ref1, results;
          results = [];
          for (i = q = 1, ref1 = dif; 1 <= ref1 ? q <= ref1 : q >= ref1; i = 1 <= ref1 ? ++q : --q) {
            results.push("0");
          }
          return results;
        })()).join("")) + (this.toString());
      } else {
        return this.toString();
      }
    }
  });

  Object.defineProperty(Date.prototype, "getISOTimezoneOffset", {
    enumerable: false,
    writable: true,
    value: function() {
      var tzo;
      tzo = -this.getTimezoneOffset();
      if (tzo === 0) {
        return "Z";
      } else {
        return "" + (tzo < 0 ? '-' : '+') + ((Math.abs(tzo) / 60).digits(2)) + ":" + ((Math.abs(tzo) % 60).digits(2));
      }
    }
  });

  if (Function.prototype.name == null) {
    Object.defineProperty(Function.prototype, 'name', {
      configurable: true,
      writable: true,
      get: function() {
        var name;
        name = this.toString().match(/^\s*function\s*(\S*)\s*\(/)[1];
        Object.defineProperty(this, 'name', {
          value: name
        });
        return name;
      }
    });
  }

  __jsonParse = JSON.parse;

  JSON.parse = jQuery.parseJSON = jQuery.ajaxSettings.converters['text json'] = function(text, fce) {
    return __jsonParse(text, function(key, value) {
      if (typeof value === 'string' && /^\d{4}\-\d\d\-\d\d[tT]\d\d:\d\d:\d\d\.\d{3}Z$/.test(value)) {
        value = new Date(value);
      }
      if (fce) {
        value = fce(key, value);
      }
      return value;
    });
  };

  __dateToString = Date.prototype.toString;

  Date.prototype.toString = Date.prototype.toJSON;

  if (global.jQuery != null) {
    jQuery.fn.reverse = Array.prototype.reverse;
    jQuery.fn.previous = jQuery.fn.prev;
    jQuery.fn.once = jQuery.fn.one;
    jQuery.fn.appendToAtIndex = function(parent, index) {
      if (index === 0) {
        return this.prependTo(parent);
      }
      return jQuery(jQuery(parent).children()[index - 1]).after(this);
    };
  }

  global.EventEmitter = (function() {
    function EventEmitter() {
      this._events = Object.create(null);
    }

    EventEmitter.prototype.destructor = function() {
      return this._events = null;
    };

    EventEmitter.prototype.destroy = function() {
      return this.destructor();
    };

    EventEmitter.prototype.emit = function(event) {
      var args, handler, len2, listeners, q, type;
      args = Array.prototype.slice.call(arguments);
      type = args.shift();
      if (this._events[type]) {
        listeners = this._events[type].clone();
        for (q = 0, len2 = listeners.length; q < len2; q++) {
          handler = listeners[q];
          handler.apply(null, args);
        }
      }
      return this;
    };

    EventEmitter.prototype.on = function(events, handler) {
      var event, len2, q, ref1;
      ref1 = events.split(' ');
      for (q = 0, len2 = ref1.length; q < len2; q++) {
        event = ref1[q];
        if (!this._events[event]) {
          this._events[event] = [];
        }
        if (indexOf.call(this._events[event], handler) < 0) {
          this._events[event].push(handler);
        }
      }
      return this;
    };

    EventEmitter.prototype.once = function(events, handler) {
      var event, fn2, len2, q, ref1, self;
      self = this;
      ref1 = events.split(' ');
      fn2 = function(event) {
        var fce;
        fce = function() {
          self.off(event, fce);
          return handler.apply(null, arguments);
        };
        return self.on(event, fce);
      };
      for (q = 0, len2 = ref1.length; q < len2; q++) {
        event = ref1[q];
        fn2(event);
      }
      return this;
    };


    /*
    	@param {String} [event] Event name.
    	@param {Function} [handler] Event handler function.
    	
    	@return {@}
     */

    EventEmitter.prototype.off = function(events, handler) {
      var event, index, len2, q, ref1;
      ref1 = events.split(' ');
      for (q = 0, len2 = ref1.length; q < len2; q++) {
        event = ref1[q];
        if (!event) {
          this._events = {};
          continue;
        }
        if (this._events[event]) {
          if (!handler) {
            this._events[event] = [];
            continue;
          }
          index = this._events[event].indexOf(handler);
          if (index !== -1) {
            this._events[event].splice(index, 1);
            if (this._events[event].length === 0) {
              delete this._events[event];
            }
          }
        }
      }
      return this;
    };

    return EventEmitter;

  })();

  global.trace = function() {
    return typeof console !== "undefined" && console !== null ? typeof console.log === "function" ? console.log.apply(console, arguments) : void 0 : void 0;
  };

  global.inspect = function() {
    return typeof console !== "undefined" && console !== null ? typeof console.dir === "function" ? console.dir.apply(console, arguments) : void 0 : void 0;
  };

  Error.prototype.toJSON = function() {
    var k, o, ref1, v;
    o = {
      name: this.name,
      message: this.message,
      stack: this.stack
    };
    ref1 = this;
    for (k in ref1) {
      v = ref1[k];
      o[k] = v;
    }
    return o;
  };

  try {
    global.localStorage.setItem('test:support', '1');
    global.localStorage.removeItem('test:support');
    imt.localStorage = global.localStorage;
  } catch (error) {
    ex = error;
    imt.localStorage = {
      _data: Object.create(null),
      length: 0,
      getItem: function(key) {
        var ref1;
        return (ref1 = this._data[key]) != null ? ref1 : null;
      },
      setItem: function(key, value) {
        this._data[key] = value;
        return this.length = Object.keys(this._data).length;
      },
      removeItem: function(key) {
        delete this._data[key];
        return this.length = Object.keys(this._data).length;
      },
      key: function(index) {
        return Object.keys(this._data)[index];
      }
    };
  }

  attachFakeCursor = function() {
    return sim.img('.i-presentation-pointer', function() {
      this.appendTo(sim('body'));
      this.attr('src', imt["static"]('/img/cursor.svg'));
      sim(window).on('mousemove', (function(_this) {
        return function(event) {
          return _this.css({
            left: event.pageX,
            top: event.pageY
          });
        };
      })(this));
      sim(window).on('mousedown', (function(_this) {
        return function(event) {
          return _this.css({
            filter: 'grayscale(1)'
          });
        };
      })(this));
      return sim(window).on('mouseup', (function(_this) {
        return function(event) {
          return _this.css({
            filter: 'none'
          });
        };
      })(this));
    });
  };

  if (JSON.parse(imt.localStorage.getItem('config:fakeCursor'))) {
    attachFakeCursor();
  }

  ANIMATION_FPS = 60;

  ANIMATION_EASING = {
    linear: function(t, b, c, d) {
      return c * t / d + b;
    }
  };


  /*
  Animates properties on object.
  
  @param {Object} object Object to animate properties on.
  @param {Object|String} properties Collection of properties and values to animate.
  @param {*} [value] If `properties` argument is property name, this argument must be final value.
  @param {Number} [duration] Duration in milliseconds. 400ms by default.
  @callback [callback]
   */

  global.animate = function(object, properties, duration, callback) {
    var easing, fces, fn2, interval, p, property, start, value;
    if (arguments.length === 5) {
      p = {};
      p[arguments[1]] = arguments[2];
      duration = arguments[3];
      callback = arguments[4];
      properties = p;
    } else if (arguments.length === 4) {
      if (typeof properties === 'string') {
        p = {};
        p[arguments[1]] = arguments[2];
        duration = arguments[3];
        callback = null;
        properties = p;
      }
    } else if (arguments.length === 3) {
      if (typeof properties === 'string') {
        p = {};
        p[arguments[1]] = arguments[2];
        duration = 400;
        callback = null;
        properties = p;
      }
    }
    if (!properties) {
      setImmediate(function() {
        return typeof callback === "function" ? callback(null) : void 0;
      });
      return;
    }
    start = Date.now();
    easing = ANIMATION_EASING.linear;
    fces = [];
    fn2 = function(property, value) {
      var beginning, change;
      beginning = object[property];
      change = value - beginning;
      object[property] = easing(0, beginning, change, duration, null);
      return fces.push(function(time) {
        return object[property] = easing(Math.min(time, duration), beginning, change, duration, null);
      });
    };
    for (property in properties) {
      value = properties[property];
      fn2(property, value);
    }
    interval = setInterval(function() {
      var fce, len2, q, time;
      time = Date.now() - start;
      for (q = 0, len2 = fces.length; q < len2; q++) {
        fce = fces[q];
        fce(time);
      }
      if (time >= duration) {
        clearInterval(interval);
        return setImmediate(function() {
          return typeof callback === "function" ? callback(false) : void 0;
        });
      }
    }, 1000 / ANIMATION_FPS);
    return {
      stop: function(complete) {
        if (complete == null) {
          complete = false;
        }
        clearInterval(interval);
        if (complete) {
          return setImmediate(function() {
            return typeof callback === "function" ? callback(true) : void 0;
          });
        }
      }
    };
  };

  sim('body > aside').each(function() {
    var calc, container, ct, ih, items, more, panel, render;
    container = sim('#asidenav > .navbar-nav:first-child').first();
    items = container.children();
    if (!items.length) {
      return;
    }
    ct = container.offset().top;
    ih = (items.last().offset().top - ct) + items.last().height();
    panel = null;
    more = sim.button('.nav-item.nav-more.d-flex.w-100', function() {
      var icon;
      icon = this.div('.nav-icon');
      icon.i('.fas.fa-fw.fa-ellipsis-v');
      return this.on('click', function(event) {
        var ref1;
        event.stopPropagation();
        if (((ref1 = Panels.one) != null ? ref1._relative : void 0) === icon) {
          Panels.one.close();
          return false;
        }
        panel = Panels.one = new Panel(icon);
        panel.position = 'bottom';
        panel.offsetY = 20;
        panel.width(250);
        render(panel);
        return false;
      });
    });
    sim.ready(function() {
      return more.div().text(imt.l('base', 'common.more'));
    });
    render = function(panel) {
      return panel.content = sim.div('.list-group.list-group-small', function() {
        var item, len2, q, results;
        results = [];
        for (q = 0, len2 = items.length; q < len2; q++) {
          item = items[q];
          if (!('hidden' === item.css('visibility'))) {
            continue;
          }
          if (item.is('.nav-divider')) {
            continue;
          }
          results.push(this.a('.list-group-item', function() {
            this.attr('href', item.attr('href'));
            this.i('.list-group-icon').addClass(item.find('i').attr('class'));
            return this.div('.list-group-title').text(item.children().last().text());
          }));
        }
        return results;
      });
    };
    calc = function() {
      var h, i, item, oh, prev;
      oh = container.height();
      items.css('visibility', '');
      if (sim(window).width() >= 576 && ih > oh) {
        h = ih;
        i = 1;
        while (h > oh - 43) {
          item = items[items.length - i++];
          if (!item) {
            break;
          }
          h -= item.outerHeight(true);
          item.css('visibility', 'hidden');
        }
        prev = items[items.length - i + 1];
        if (prev) {
          more.css('top', (prev.offset().top - ct) - (prev.is('.nav-divider') ? 12 : 0));
        } else {
          more.css('top', 0);
        }
        container.append(more);
        if (panel) {
          return render(panel);
        }
      } else {
        more.detach();
        return panel != null ? panel.close() : void 0;
      }
    };
    sim(window).on('resize', calc);
    return calc();
  });

  SIGNED_USER_MENU = (ref1 = sim('#signedmenucontent')) != null ? ref1.detach().removeClass('d-none') : void 0;

  sim(document).on('click', '.i-signed-menu', function(event) {
    var panel, ref2, relative;
    if (!SIGNED_USER_MENU) {
      return true;
    }
    event.stopPropagation();
    relative = this.children('.nav-icon').first();
    if (((ref2 = Panels.one) != null ? ref2._relative : void 0) === relative) {
      Panels.one.close();
      return false;
    }
    panel = Panels.one = new Panel(relative);
    panel.position = 'top';
    panel.offsetY = 20;
    panel.width(250);
    panel.content = SIGNED_USER_MENU;
    return false;
  });

  global.browser = {
    mobile: false,
    touch: true,
    mouse: true,
    keyboard: true,
    simulator: false,
    standalone: 'standalone' in window.navigator && window.navigator.standalone
  };

  global.os = {
    mobile: false
  };

  (function() {
    var re, version;
    version = function(s, f) {
      var i, v;
      i = s.indexOf(f);
      if (i === -1) {
        return 0;
      }
      v = parseFloat(s.substr(i + f.length + 1));
      if (isNaN(v)) {
        return 0;
      }
      return v;
    };
    try {
      if (navigator.appName === "Microsoft Internet Explorer") {
        if (navigator.userAgent.match(/IEMobile/i)) {
          browser.mobile = true;
          browser.ie = {
            version: version(navigator.userAgent, 'IEMobile')
          };
          os.mobile = true;
          os.windowsphone = {
            version: version(navigator.userAgent, 'Windows Phone')
          };
          imt.browser = "windowsphone:" + os.windowsphone.version + "/ie:" + browser.ie.version;
        } else {
          browser.ie = {
            version: 0
          };
          os.windows = {
            version: 0
          };
          re = new RegExp("MSIE ([0-9]{1,}[\.0-9]{0,})");
          if (re.exec(navigator.userAgent) != null) {
            browser.ie.version = parseFloat(RegExp.$1);
          }
          imt.browser = "win/ie:" + browser.ie.version;
        }
      } else if (navigator.appName === "Netscape" && navigator.userAgent.match(/Trident/i)) {
        browser.ie = {
          version: 11
        };
        os.windows = {
          version: 0
        };
        imt.browser = "win/ie:" + browser.ie.version;
      } else if (navigator.appName === "Netscape" && navigator.userAgent.match(/Edge/i)) {
        browser.ie = {
          version: 12
        };
        os.windows = {
          version: 0
        };
        imt.browser = "win/ie:" + browser.ie.version;
      } else if (navigator.platform.match(/Win/i)) {
        os.windows = {
          version: 0
        };
        if (navigator.userAgent.match(/OPR/i)) {
          browser.opera = {
            version: version(navigator.userAgent, 'OPR')
          };
          imt.browser = "win/opera:" + browser.opera.version;
        } else if (navigator.userAgent.match(/Opera/i)) {
          browser.opera = {
            version: version(navigator.userAgent, 'Opera')
          };
          imt.browser = "win/opera:" + browser.opera.version;
        } else if (navigator.userAgent.match(/Chrome/i)) {
          browser.chrome = {
            version: version(navigator.userAgent, 'Chrome')
          };
          imt.browser = "win/chrome:" + browser.chrome.version;
        } else if (navigator.userAgent.match(/Safari/i)) {
          browser.safari = {
            version: version(navigator.userAgent, 'Version')
          };
          imt.browser = "win/safari:" + browser.safari.version;
        } else if (navigator.userAgent.match(/Firefox/i)) {
          browser.firefox = {
            version: version(navigator.userAgent, 'Firefox')
          };
          imt.browser = "win/firefox:" + browser.firefox.version;
        } else if (navigator.appName === 'simDOM') {
          imt.browser = "win/simDOM";
          browser.simulator = true;
        } else {
          imt.browser = "win/unknown";
        }
      } else if (navigator.platform.match(/Mac/i)) {
        os.mac = {
          version: 0
        };
        if (navigator.userAgent.match(/OPR/i)) {
          browser.opera = {
            version: version(navigator.userAgent, 'OPR')
          };
          imt.browser = "mac/opera:" + browser.opera.version;
        } else if (navigator.userAgent.match(/Opera/i)) {
          browser.opera = {
            version: version(navigator.userAgent, 'Opera')
          };
          imt.browser = "mac/opera:" + browser.opera.version;
        } else if (navigator.userAgent.match(/Chrome/i)) {
          browser.chrome = {
            version: version(navigator.userAgent, 'Chrome')
          };
          imt.browser = "mac/chrome:" + browser.chrome.version;
        } else if (navigator.userAgent.match(/Safari/i)) {
          browser.safari = {
            version: version(navigator.userAgent, 'Version')
          };
          imt.browser = "mac/safari:" + browser.safari.version;
        } else if (navigator.userAgent.match(/Firefox/i)) {
          browser.firefox = {
            version: version(navigator.userAgent, 'Firefox')
          };
          imt.browser = "mac/firefox:" + browser.firefox.version;
        } else if (navigator.appName === 'simDOM') {
          imt.browser = "mac/simDOM";
          browser.simulator = true;
        } else {
          imt.browser = "mac/unknown";
        }
      } else if (navigator.userAgent.match(/(iPod|iPhone|iPad)/i)) {
        browser.mobile = true;
        browser.mouse = false;
        browser.keyboard = false;
        os.mobile = true;
        os.ios = {
          version: version(navigator.appVersion.replace(/_/g, '.'), 'OS')
        };
        if (navigator.userAgent.match(/CriOS/i)) {
          browser.chrome = {
            version: version(navigator.userAgent, 'CriOS'),
            mobile: true
          };
          imt.browser = "ios:" + os.ios.version + "/chrome:" + browser.chrome.version;
        } else if (navigator.userAgent.match(/AppleWebKit/i)) {
          browser.safari = {
            version: version(navigator.userAgent, 'Version'),
            mobile: true
          };
          imt.browser = "ios:" + os.ios.version + "/safari:" + browser.safari.version;
        } else {
          imt.browser = "ios:" + os.ios.version + "/unknown";
        }
      } else if (navigator.userAgent.match(/Android/i)) {
        browser.mobile = true;
        os.mobile = true;
        os.android = {
          version: version(navigator.userAgent, 'Android')
        };
        if (navigator.userAgent.match(/OPR/i)) {
          browser.opera = {
            version: version(navigator.userAgent, 'OPR')
          };
          imt.browser = "android:" + os.android.version + "/opera:" + browser.opera.version;
        } else if (navigator.userAgent.match(/Chrome/i)) {
          browser.chrome = {
            version: version(navigator.userAgent, 'Chrome'),
            mobile: true
          };
          imt.browser = "android:" + os.android.version + "/chrome:" + browser.chrome.version;
        } else if (navigator.userAgent.match(/Firefox/i)) {
          browser.firefox = {
            version: version(navigator.userAgent, 'Firefox'),
            mobile: true
          };
          imt.browser = "android:" + os.android.version + "/firefox:" + browser.firefox.version;
        } else {
          imt.browser = "android:" + os.android.version + "/stock";
          browser.mouse = false;
        }
      } else if (navigator.userAgent.match(/BlackBerry/i)) {
        browser.mobile = true;
        os.mobile = true;
        os.blackBerry = {
          version: 0
        };
        imt.browser = "blackberry/unknown";
      }
    } catch (error) {
      ex = error;
    }
    if (browser.mobile) {
      sim('html').addClass('mobile');
    }
    if (browser.standalone) {
      sim('html').addClass('standalone');
    }
    if (browser.ie) {
      return sim(document).on('click', 'button[form]', function() {
        sim("#" + (this.attr('form'))).__dom.submit();
        return false;
      });
    }
  })();

  global.Color = (function() {
    function Color(color) {
      var ref2, ref3, ref4, ref5, res;
      this.color = {
        r: 0,
        g: 0,
        b: 0,
        a: 1
      };
      if (typeof color === 'string') {
        if (color.charAt(0) === '#') {
          color = color.replace(/^#?([a-f\d])([a-f\d])([a-f\d])$/, function(m, r, g, b) {
            return r + r + g + g + b + b;
          });
          res = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(color);
          if (res) {
            this.color = {
              r: parseInt(res[1], 16),
              g: parseInt(res[2], 16),
              b: parseInt(res[3], 16),
              a: 1
            };
          }
        } else if (/^rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$/i.exec(color)) {
          this.color = {
            r: parseInt(RegExp.$1),
            g: parseInt(RegExp.$2),
            b: parseInt(RegExp.$3),
            a: 1
          };
        } else if (/^rgba\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+\.?\d*)\s*\)$/i.exec(color)) {
          this.color = {
            r: parseInt(RegExp.$1),
            g: parseInt(RegExp.$2),
            b: parseInt(RegExp.$3),
            a: parseFloat(RegExp.$4)
          };
        }
      } else if (typeof color === 'number') {
        this.color = {
          r: parseInt((ref2 = arguments[0]) != null ? ref2 : 0),
          g: parseInt((ref3 = arguments[1]) != null ? ref3 : 0),
          b: parseInt((ref4 = arguments[2]) != null ? ref4 : 0),
          a: parseFloat((ref5 = arguments[3]) != null ? ref5 : 1)
        };
      } else if (color instanceof Color) {
        this.color = extend({}, color.color);
      }
    }

    Color.property('alpha', {
      get: function() {
        return this.color.a;
      },
      set: function(value) {
        return this.color.a = parseInt(value);
      }
    });

    Color.property('red', {
      get: function() {
        return this.color.r;
      },
      set: function(value) {
        return this.color.r = parseInt(value);
      }
    });

    Color.property('green', {
      get: function() {
        return this.color.g;
      },
      set: function(value) {
        return this.color.g = parseInt(value);
      }
    });

    Color.property('blue', {
      get: function() {
        return this.color.b;
      },
      set: function(value) {
        return this.color.b = parseInt(value);
      }
    });

    Color.property('luminance', {
      get: function() {
        return (0.3 * this.color.r + 0.59 * this.color.g + 0.11 * this.color.b) / 255;
      }
    });

    Color.prototype.clone = function() {
      return this.copy();
    };

    Color.prototype.copy = function() {
      return new Color(this);
    };

    Color.prototype.darker = function(amount) {
      if (!amount) {
        return this;
      }
      return new Color(Math.max(0, this.color.r - amount), Math.max(0, this.color.g - amount), Math.max(0, this.color.b - amount));
    };

    Color.prototype.determineForegroundColor = function() {
      if (this.alpha < .5) {
        return new Color();
      }
      if (this.luminance <= .85) {
        return new Color(255, 255, 255);
      } else {
        return new Color();
      }
    };

    Color.prototype.equal = function(color) {
      if (!(color instanceof Color)) {
        return false;
      }
      return this.red === color.red && this.green === color.green && this.blue === color.blue && this.alpha === color.alpha;
    };

    Color.prototype.isDark = function() {
      return this.luminance <= .85;
    };

    Color.prototype.isLight = function() {
      return this.luminance > .85;
    };

    Color.prototype.lighter = function(amount) {
      if (!amount) {
        return this;
      }
      return new Color(Math.min(255, this.color.r + amount), Math.min(255, this.color.g + amount), Math.min(255, this.color.b + amount));
    };

    Color.prototype.mix = function(color, amount) {
      var a, b, g, r;
      if (amount == null) {
        amount = .5;
      }
      if (!(color instanceof Color)) {
        throw new Error("Color expected.");
      }
      amount = Math.max(0, Math.min(amount, 1));
      r = this.color.r + (color.color.r - this.color.r) * amount;
      g = this.color.g + (color.color.g - this.color.g) * amount;
      b = this.color.b + (color.color.b - this.color.b) * amount;
      a = this.color.a + (color.color.a - this.color.a) * amount;
      return new Color(Math.round(r), Math.round(g), Math.round(b), a);
    };

    Color.prototype.toHex = function() {
      var pad;
      pad = function(n) {
        if (n.length < 2) {
          return "0" + n;
        } else {
          return n;
        }
      };
      return "#" + (pad(this.color.r.toString(16))) + (pad(this.color.g.toString(16))) + (pad(this.color.b.toString(16)));
    };

    Color.prototype.toRGB = function() {
      return "rgb(" + this.color.r + "," + this.color.g + "," + this.color.b + ")";
    };

    Color.prototype.toRGBA = function() {
      return "rgba(" + this.color.r + "," + this.color.g + "," + this.color.b + "," + this.color.a + ")";
    };

    Color.prototype.toString = function() {
      return this.toHex();
    };

    Color.prototype.toJSON = function() {
      return this.toHex();
    };

    Color.prototype.transparent = function(value) {
      return new Color(this.color.r, this.color.g, this.color.b, value);
    };

    Color.prototype.valueOf = function() {
      return this.toHex();
    };

    Color.random = function() {
      var b, g, r;
      r = Math.round(Math.random() * 255);
      g = Math.round(Math.random() * 255);
      b = Math.round(Math.random() * 255);
      return new Color(r, g, b, 1);
    };

    return Color;

  })();

  global.rgb = function(r, g, b) {
    return new Color(r, g, b);
  };

  global.rgba = function(r, g, b, a) {
    return new Color(r, g, b, a);
  };

  global.AJAXDirectives = {
    process: function(elm, directives, region) {
      var action, alert, args, button, dom, len2, len3, len4, method, name, pair, q, ref10, ref11, ref12, ref13, ref14, ref15, ref16, ref17, ref18, ref19, ref2, ref20, ref21, ref22, ref23, ref3, ref4, ref5, ref6, ref7, ref8, ref9, relative, resolve, selector, selectors, target, u, value, what, where, z;
      if (elm) {
        relative = sim(elm.data('relative'));
      }
      if (relative instanceof SIMArray) {
        relative = relative.first();
      }
      resolve = function(selector, inregion) {
        if (inregion == null) {
          inregion = true;
        }
        if (selector === ':scope') {
          return elm;
        } else if (/^body /.test(selector)) {
          return sim(selector);
        } else if (/^< /.test(selector)) {
          selector = selector.substr(2);
          if (relative) {
            if (relative.is(selector)) {
              return relative;
            }
            return relative.closest(selector);
          }
          return elm.closest(selector);
        } else {
          if (inregion && region) {
            return region.find(selector);
          } else {
            return sim(selector);
          }
        }
      };
      if ((global.ga != null) && Array.isArray(directives.analytics)) {
        ref2 = directives.analytics;
        for (q = 0, len2 = ref2.length; q < len2; q++) {
          args = ref2[q];
          ga.apply(null, args);
        }
      }
      if ((ref3 = directives["class"]) != null ? ref3.add : void 0) {
        ref4 = directives["class"].add;
        for (selector in ref4) {
          value = ref4[selector];
          if ((ref5 = resolve(selector)) != null) {
            ref5.addClass(value);
          }
        }
      }
      if ((ref6 = directives["class"]) != null ? ref6.remove : void 0) {
        ref7 = directives["class"].remove;
        for (selector in ref7) {
          value = ref7[selector];
          if ((ref8 = resolve(selector)) != null) {
            ref8.removeClass(value);
          }
        }
      }
      if (directives.updates || directives.update) {
        ref10 = (ref9 = directives.updates) != null ? ref9 : directives.update;
        for (method in ref10) {
          selectors = ref10[method];
          for (selector in selectors) {
            value = selectors[selector];
            if ((ref11 = resolve(selector)) != null) {
              ref11[method](value);
            }
          }
        }
      }
      if (directives.increment) {
        ref12 = directives.increment;
        for (selector in ref12) {
          value = ref12[selector];
          target = resolve(selector);
          target.text(parseFloat(target.text()) + value);
        }
      }
      if (directives.data) {
        ref13 = directives.data;
        for (selector in ref13) {
          pair = ref13[selector];
          target = resolve(selector);
          for (name in pair) {
            value = pair[name];
            target.data(name, value);
          }
        }
      }
      if (directives.append) {
        ref14 = directives.append;
        for (method in ref14) {
          selectors = ref14[method];
          for (selector in selectors) {
            value = selectors[selector];
            target = resolve(selector);
            if (!target) {
              continue;
            }
            if (method === 'html') {
              dom = sim.parse(value);
              target.append(dom);
              dom.hide().fadeIn();
            } else {
              target.write(value);
            }
          }
        }
      }
      if (directives.prepend) {
        ref15 = directives.prepend;
        for (method in ref15) {
          selectors = ref15[method];
          for (selector in selectors) {
            value = selectors[selector];
            target = resolve(selector);
            if (!target) {
              continue;
            }
            if (method === 'html') {
              dom = sim.parse(value);
              target.prepend(dom);
              dom.hide().fadeIn();
            } else {
              target.text(value + target.text());
            }
          }
        }
      }
      if (directives.replace) {
        ref16 = directives.replace;
        for (selector in ref16) {
          value = ref16[selector];
          target = resolve(selector);
          if (!target) {
            continue;
          }
          sim.parse(value).insertBefore(target);
          target.remove();
        }
      }
      if (directives.move) {
        ref17 = directives.move;
        for (what in ref17) {
          where = ref17[what];
          if ((ref18 = resolve(where, false)) != null) {
            ref18.append(resolve(what));
          }
        }
      }
      if (directives.alert) {
        if (directives.alert.html) {
          alert = new Alert;
          alert._body.html(directives.alert.html);
        } else if (directives.alert.text) {
          alert = new Alert(directives.alert.text);
        }
        if (Array.isArray(directives.alert.buttons)) {
          ref19 = directives.alert.buttons;
          for (u = 0, len3 = ref19.length; u < len3; u++) {
            button = ref19[u];
            if (button.redirect) {
              alert._footer.append(sim.a('.btn.btn-sm.btn-primary', function() {
                this.attr('href', button.redirect);
                return this.text(button.label);
              }));
            }
          }
        }
        if (directives.alert.title) {
          alert.title = directives.alert.title;
        }
        alert.show();
      }
      if (directives.flash) {
        new Flash(directives.flash);
      }
      if (directives.action) {
        ref20 = directives.action;
        for (action in ref20) {
          args = ref20[action];
          AJAXDirectives.action[action].apply({
            elm: elm,
            relative: relative
          }, args != null ? args : []);
        }
      }
      if (directives.remove) {
        if (!Array.isArray(directives.remove)) {
          directives.remove = [directives.remove];
        }
        ref21 = directives.remove;
        for (z = 0, len4 = ref21.length; z < len4; z++) {
          selector = ref21[z];
          if ((ref22 = resolve(selector)) != null) {
            ref22.remove();
          }
        }
      }
      if (((ref23 = directives.action) != null ? ref23.redirect : void 0) != null) {
        return false;
      }
      return null;
    }
  };

  AJAXDirectives.action = {
    sort: function() {
      var items, list;
      if (this.relative) {
        if (this.relative.is('.list-group')) {
          list = this.relative;
        } else {
          list = this.relative.closest('.list-group');
        }
      } else {
        list = this.elm.closest('.list-group');
      }
      if (list != null) {
        items = list.children(':not(.list-group-add)').sortOn(function(item) {
          return item.find('.list-group-title').text();
        });
        items.detach().reverse().prependTo(list);
      }
      return null;
    },
    reload: function() {
      return setImmediate(function() {
        return window.location.reload();
      });
    },
    redirect: function(url) {
      return setImmediate(function() {
        return window.location = url;
      });
    }
  };

  CAROUSEL_MAX_SLIDES = 6;

  Carousel = (function(superClass) {
    extend1(Carousel, superClass);

    Carousel.prototype.slides = null;

    Carousel.prototype.position = 1;

    Carousel.prototype.interval = 10000;

    Carousel.prototype._initialized = false;

    Carousel.prototype._width = null;

    Carousel.prototype._timer = null;

    Carousel.prototype._timerStart = null;

    Carousel.prototype._elapsedInterval = null;

    Carousel.prototype._cursorIn = false;

    function Carousel(elm) {
      this._resize = bind(this._resize, this);
      this._moveTo = bind(this._moveTo, this);
      Carousel.__super__.constructor.call(this, elm != null ? elm : 'div');
      this.addClass('i-carousel');
      this.slides = this.children('a').slice(0, CAROUSEL_MAX_SLIDES).map(function(elm) {
        return {
          elm: elm
        };
      });
      this._resize();
      sim(window).on('resize', this._resize);
      this.on('mouseenter', (function(_this) {
        return function() {
          _this._cursorIn = true;
          _this._elapsedInterval = Date.now() - _this._timerStart;
          undelay(_this._timer);
          _this._timerStart = null;
          return _this._timer = null;
        };
      })(this));
      this.on('mouseleave', (function(_this) {
        return function() {
          var interval;
          _this._cursorIn = false;
          interval = _this._elapsedInterval ? _this.interval - _this._elapsedInterval : _this.interval;
          _this._timer = delay(interval, _this._moveTo);
          _this._timerStart = Date.now() - _this._elapsedInterval;
          return _this._elapsedInterval = null;
        };
      })(this));
      this.children('.fa-chevron-left').on('click', (function(_this) {
        return function() {
          return _this._moveTo('right');
        };
      })(this));
      this.children('.fa-chevron-right').on('click', (function(_this) {
        return function() {
          return _this._moveTo('left');
        };
      })(this));
    }

    Carousel.prototype.init = function(options) {
      var self;
      if (this.slides.length < 3) {
        throw new Error("Minimum number of slides is 3.");
      }
      self = this;
      return async.each(this.slides, function(slide, next) {
        var img;
        img = slide.elm.children('img').first();
        img.on('click', function(event) {
          var index, ref2;
          index = (ref2 = this.parent().attr('class').match(/(?:^|\s)i\-carousel\-slide\-(\d+)(?:$|\s)/)) != null ? ref2[1] : void 0;
          if (!index) {
            return false;
          }
          index = parseInt(index);
          if (self.position === index) {
            return true;
          } else {
            self._moveTo(parseInt(index));
          }
          event.stopPropagation();
          return false;
        });
        if (img.__dom.complete) {
          slide.width = img.width();
          slide.height = img.height();
          return next();
        }
        return img.on('load', function() {
          slide.width = img.width();
          slide.height = img.height();
          return next();
        });
      }, (function(_this) {
        return function() {
          _this._initialized = true;
          _this._resize();
          _this._timer = delay(_this.interval, _this._moveTo);
          return _this._timerStart = Date.now();
        };
      })(this));
    };

    Carousel.prototype._moveTo = function(position) {
      if (position && this.position === position) {
        return;
      }
      if (position == null) {
        position = 'right';
      }
      if ('string' === typeof position) {
        if (position === 'left') {
          position = this.position === 1 ? this.slides.length : this.position - 1;
        } else {
          position = this.position === this.slides.length ? 1 : this.position + 1;
        }
      }
      this.slides.forEach(function(slide) {
        return slide.elm.removeClass('i-carousel-to-center i-carousel-from-center');
      });
      this.slides[this.position - 1].elm.addClass('i-carousel-from-center');
      this.removeClass("i-carousel-position-" + this.position);
      this.position = position;
      this.slides[position - 1].elm.addClass('i-carousel-to-center');
      this.addClass("i-carousel-position-" + this.position);
      if (this._timer) {
        undelay(this._timer);
      }
      this._elapsedInterval = null;
      if (!this._cursorIn) {
        this._timer = delay(this.interval, this._moveTo);
        return this._timerStart = Date.now();
      }
    };

    Carousel.prototype._resize = function() {
      var height, len2, q, ref2, results, slide, width;
      if (!this._initialized) {
        return;
      }
      height = this.height();
      ref2 = this.slides;
      results = [];
      for (q = 0, len2 = ref2.length; q < len2; q++) {
        slide = ref2[q];
        width = Math.floor(slide.width * (height / slide.height));
        results.push(slide.elm.css({
          height: height,
          width: width,
          'margin-top': -Math.floor(height / 2),
          'margin-left': -Math.floor(width / 2)
        }));
      }
      return results;
    };

    return Carousel;

  })(SIMElement);

  sim.registerComponent('carousel', Carousel);

  sim.carousel = function(options) {
    return sim('@carousel').each(function() {
      return this.init(options);
    });
  };

  if (typeof Chart !== "undefined" && Chart !== null) {
    Chart.defaults.global.responsive = true;
  }

  if (typeof Chart !== "undefined" && Chart !== null) {
    Chart.defaults.global.maintainAspectRatio = true;
  }

  if (typeof Chart !== "undefined" && Chart !== null) {
    Chart.defaults.global.legend.display = false;
  }

  if (typeof Chart !== "undefined" && Chart !== null) {
    Chart.defaults.global.tooltips.enabled = true;
  }

  if (typeof Chart !== "undefined" && Chart !== null) {
    Chart.defaults.global.tooltips.position = 'nearest';
  }

  if (typeof Chart !== "undefined" && Chart !== null) {
    Chart.defaults.global.tooltips.mode = 'index';
  }

  if (typeof Chart !== "undefined" && Chart !== null) {
    Chart.defaults.global.tooltips.intersect = false;
  }

  if (typeof Chart !== "undefined" && Chart !== null) {
    Chart.defaults.global.tooltips.callbacks.labelColor = function(item, chart) {
      return {
        borderColor: chart.data.datasets[item.datasetIndex].borderColor,
        backgroundColor: chart.data.datasets[item.datasetIndex].borderColor
      };
    };
  }

  if (typeof Chart !== "undefined" && Chart !== null) {
    Chart.defaults.global.hover.mode = 'index';
  }

  if (typeof Chart !== "undefined" && Chart !== null) {
    Chart.defaults.global.hover.intersect = false;
  }

  if (typeof Chart !== "undefined" && Chart !== null) {
    Chart.defaults.doughnut.cutoutPercentage = 85;
  }

  if (typeof Chart !== "undefined" && Chart !== null) {
    Chart.defaults.doughnut.circumference = Math.PI * 1;
  }

  if (typeof Chart !== "undefined" && Chart !== null) {
    Chart.defaults.doughnut.rotation = Math.PI * 1;
  }

  RemoteChart = (function(superClass) {
    extend1(RemoteChart, superClass);

    function RemoteChart(elm) {
      RemoteChart.__super__.constructor.call(this, elm != null ? elm : 'div');
      this.addClass('i-chart');
      if (this.data('height')) {
        this.css('height', (this.data('height')) + "px");
      }
    }

    RemoteChart.prototype.init = function() {
      var self;
      self = this;
      return Loader.load(this.data('store'), (function(_this) {
        return function(err, data, headers, metadata) {
          var axes, axis, fn2, fn3, iml, key, len2, q, ref2, ref3, ref4, ref5, ref6, scales;
          if (err) {
            return new Alert(err.message).show();
          }
          scales = (ref2 = data.options) != null ? ref2.scales : void 0;
          if (scales) {
            axes = [].concat(scales.yAxes || [], scales.xAxes || []);
            fn2 = function(iml) {
              return axis.ticks.callback = function(value) {
                return IML.execute(IML.parse(iml), {
                  value: value
                }, {
                  functions: {
                    format: format
                  }
                });
              };
            };
            for (q = 0, len2 = axes.length; q < len2; q++) {
              axis = axes[q];
              if (!('string' === typeof ((ref3 = axis.ticks) != null ? ref3.callback : void 0))) {
                continue;
              }
              iml = axis.ticks.callback;
              fn2(iml);
            }
          }
          if ((ref4 = data.options) != null ? (ref5 = ref4.tooltips) != null ? ref5.callbacks : void 0 : void 0) {
            ref6 = data.options.tooltips.callbacks;
            fn3 = function(iml) {
              return data.options.tooltips.callbacks[key] = function(item, data) {
                return IML.execute(IML.parse(iml), {
                  item: item,
                  data: data
                }, {
                  functions: {
                    format: format
                  }
                });
              };
            };
            for (key in ref6) {
              iml = ref6[key];
              fn3(iml);
            }
          }
          return _this.canvas(function() {
            var ctx;
            ctx = this.__dom.getContext("2d");
            return new Chart(ctx, data);
          });
        };
      })(this));
    };

    return RemoteChart;

  })(SIMElement);

  sim.registerComponent('remote-chart', RemoteChart);

  sim.ready(function() {
    return sim('@remote-chart').each(function() {
      return this.init();
    });
  });

  CountDown = (function(superClass) {
    extend1(CountDown, superClass);

    function CountDown(elm) {
      CountDown.__super__.constructor.call(this, elm != null ? elm : 'div');
      this.addClass('i-countdown');
    }

    CountDown.prototype.init = function(options) {
      var spacer, time, timer, write;
      time = parseInt(this.data('timestamp'));
      spacer = this.data('spacer');
      write = (function(_this) {
        return function() {
          if (time < Date.now()) {
            unrepeat(timer);
            return _this.empty().data('running', 'true').span('.badge.badge-primary').text(imt.l('base', 'states.running'));
          }
          return _this.html(format(time, 'countdown', {
            timezone: imt.user.timezone,
            spacer: spacer
          }));
        };
      })(this);
      write();
      return timer = repeat(1000, write);
    };

    CountDown.prototype.reset = function(date) {
      this.data('running', null).data('timestamp', +date);
      return this.init();
    };

    return CountDown;

  })(SIMElement);

  sim.registerComponent('countdown', CountDown);

  sim.countdown = function(options) {
    return sim('@countdown').each(function() {
      return this.init(options);
    });
  };

  DIACRITICS_MAP = {};

  String.prototype.removeDiacritics = function() {
    return this.replace(/[^\u0000-\u007E]/g, function(letter) {
      return DIACRITICS_MAP[letter] || letter;
    });
  };

  ref2 = [
    {
      'base': 'A',
      'letters': '\u0041\u24B6\uFF21\u00C0\u00C1\u00C2\u1EA6\u1EA4\u1EAA\u1EA8\u00C3\u0100\u0102\u1EB0\u1EAE\u1EB4\u1EB2\u0226\u01E0\u00C4\u01DE\u1EA2\u00C5\u01FA\u01CD\u0200\u0202\u1EA0\u1EAC\u1EB6\u1E00\u0104\u023A\u2C6F'
    }, {
      'base': 'AA',
      'letters': '\uA732'
    }, {
      'base': 'AE',
      'letters': '\u00C6\u01FC\u01E2'
    }, {
      'base': 'AO',
      'letters': '\uA734'
    }, {
      'base': 'AU',
      'letters': '\uA736'
    }, {
      'base': 'AV',
      'letters': '\uA738\uA73A'
    }, {
      'base': 'AY',
      'letters': '\uA73C'
    }, {
      'base': 'B',
      'letters': '\u0042\u24B7\uFF22\u1E02\u1E04\u1E06\u0243\u0182\u0181'
    }, {
      'base': 'C',
      'letters': '\u0043\u24B8\uFF23\u0106\u0108\u010A\u010C\u00C7\u1E08\u0187\u023B\uA73E'
    }, {
      'base': 'D',
      'letters': '\u0044\u24B9\uFF24\u1E0A\u010E\u1E0C\u1E10\u1E12\u1E0E\u0110\u018B\u018A\u0189\uA779'
    }, {
      'base': 'DZ',
      'letters': '\u01F1\u01C4'
    }, {
      'base': 'Dz',
      'letters': '\u01F2\u01C5'
    }, {
      'base': 'E',
      'letters': '\u0045\u24BA\uFF25\u00C8\u00C9\u00CA\u1EC0\u1EBE\u1EC4\u1EC2\u1EBC\u0112\u1E14\u1E16\u0114\u0116\u00CB\u1EBA\u011A\u0204\u0206\u1EB8\u1EC6\u0228\u1E1C\u0118\u1E18\u1E1A\u0190\u018E'
    }, {
      'base': 'F',
      'letters': '\u0046\u24BB\uFF26\u1E1E\u0191\uA77B'
    }, {
      'base': 'G',
      'letters': '\u0047\u24BC\uFF27\u01F4\u011C\u1E20\u011E\u0120\u01E6\u0122\u01E4\u0193\uA7A0\uA77D\uA77E'
    }, {
      'base': 'H',
      'letters': '\u0048\u24BD\uFF28\u0124\u1E22\u1E26\u021E\u1E24\u1E28\u1E2A\u0126\u2C67\u2C75\uA78D'
    }, {
      'base': 'I',
      'letters': '\u0049\u24BE\uFF29\u00CC\u00CD\u00CE\u0128\u012A\u012C\u0130\u00CF\u1E2E\u1EC8\u01CF\u0208\u020A\u1ECA\u012E\u1E2C\u0197'
    }, {
      'base': 'J',
      'letters': '\u004A\u24BF\uFF2A\u0134\u0248'
    }, {
      'base': 'K',
      'letters': '\u004B\u24C0\uFF2B\u1E30\u01E8\u1E32\u0136\u1E34\u0198\u2C69\uA740\uA742\uA744\uA7A2'
    }, {
      'base': 'L',
      'letters': '\u004C\u24C1\uFF2C\u013F\u0139\u013D\u1E36\u1E38\u013B\u1E3C\u1E3A\u0141\u023D\u2C62\u2C60\uA748\uA746\uA780'
    }, {
      'base': 'LJ',
      'letters': '\u01C7'
    }, {
      'base': 'Lj',
      'letters': '\u01C8'
    }, {
      'base': 'M',
      'letters': '\u004D\u24C2\uFF2D\u1E3E\u1E40\u1E42\u2C6E\u019C'
    }, {
      'base': 'N',
      'letters': '\u004E\u24C3\uFF2E\u01F8\u0143\u00D1\u1E44\u0147\u1E46\u0145\u1E4A\u1E48\u0220\u019D\uA790\uA7A4'
    }, {
      'base': 'NJ',
      'letters': '\u01CA'
    }, {
      'base': 'Nj',
      'letters': '\u01CB'
    }, {
      'base': 'O',
      'letters': '\u004F\u24C4\uFF2F\u00D2\u00D3\u00D4\u1ED2\u1ED0\u1ED6\u1ED4\u00D5\u1E4C\u022C\u1E4E\u014C\u1E50\u1E52\u014E\u022E\u0230\u00D6\u022A\u1ECE\u0150\u01D1\u020C\u020E\u01A0\u1EDC\u1EDA\u1EE0\u1EDE\u1EE2\u1ECC\u1ED8\u01EA\u01EC\u00D8\u01FE\u0186\u019F\uA74A\uA74C'
    }, {
      'base': 'OI',
      'letters': '\u01A2'
    }, {
      'base': 'OO',
      'letters': '\uA74E'
    }, {
      'base': 'OU',
      'letters': '\u0222'
    }, {
      'base': 'OE',
      'letters': '\u008C\u0152'
    }, {
      'base': 'oe',
      'letters': '\u009C\u0153'
    }, {
      'base': 'P',
      'letters': '\u0050\u24C5\uFF30\u1E54\u1E56\u01A4\u2C63\uA750\uA752\uA754'
    }, {
      'base': 'Q',
      'letters': '\u0051\u24C6\uFF31\uA756\uA758\u024A'
    }, {
      'base': 'R',
      'letters': '\u0052\u24C7\uFF32\u0154\u1E58\u0158\u0210\u0212\u1E5A\u1E5C\u0156\u1E5E\u024C\u2C64\uA75A\uA7A6\uA782'
    }, {
      'base': 'S',
      'letters': '\u0053\u24C8\uFF33\u1E9E\u015A\u1E64\u015C\u1E60\u0160\u1E66\u1E62\u1E68\u0218\u015E\u2C7E\uA7A8\uA784'
    }, {
      'base': 'T',
      'letters': '\u0054\u24C9\uFF34\u1E6A\u0164\u1E6C\u021A\u0162\u1E70\u1E6E\u0166\u01AC\u01AE\u023E\uA786'
    }, {
      'base': 'TZ',
      'letters': '\uA728'
    }, {
      'base': 'U',
      'letters': '\u0055\u24CA\uFF35\u00D9\u00DA\u00DB\u0168\u1E78\u016A\u1E7A\u016C\u00DC\u01DB\u01D7\u01D5\u01D9\u1EE6\u016E\u0170\u01D3\u0214\u0216\u01AF\u1EEA\u1EE8\u1EEE\u1EEC\u1EF0\u1EE4\u1E72\u0172\u1E76\u1E74\u0244'
    }, {
      'base': 'V',
      'letters': '\u0056\u24CB\uFF36\u1E7C\u1E7E\u01B2\uA75E\u0245'
    }, {
      'base': 'VY',
      'letters': '\uA760'
    }, {
      'base': 'W',
      'letters': '\u0057\u24CC\uFF37\u1E80\u1E82\u0174\u1E86\u1E84\u1E88\u2C72'
    }, {
      'base': 'X',
      'letters': '\u0058\u24CD\uFF38\u1E8A\u1E8C'
    }, {
      'base': 'Y',
      'letters': '\u0059\u24CE\uFF39\u1EF2\u00DD\u0176\u1EF8\u0232\u1E8E\u0178\u1EF6\u1EF4\u01B3\u024E\u1EFE'
    }, {
      'base': 'Z',
      'letters': '\u005A\u24CF\uFF3A\u0179\u1E90\u017B\u017D\u1E92\u1E94\u01B5\u0224\u2C7F\u2C6B\uA762'
    }, {
      'base': 'a',
      'letters': '\u0061\u24D0\uFF41\u1E9A\u00E0\u00E1\u00E2\u1EA7\u1EA5\u1EAB\u1EA9\u00E3\u0101\u0103\u1EB1\u1EAF\u1EB5\u1EB3\u0227\u01E1\u00E4\u01DF\u1EA3\u00E5\u01FB\u01CE\u0201\u0203\u1EA1\u1EAD\u1EB7\u1E01\u0105\u2C65\u0250'
    }, {
      'base': 'aa',
      'letters': '\uA733'
    }, {
      'base': 'ae',
      'letters': '\u00E6\u01FD\u01E3'
    }, {
      'base': 'ao',
      'letters': '\uA735'
    }, {
      'base': 'au',
      'letters': '\uA737'
    }, {
      'base': 'av',
      'letters': '\uA739\uA73B'
    }, {
      'base': 'ay',
      'letters': '\uA73D'
    }, {
      'base': 'b',
      'letters': '\u0062\u24D1\uFF42\u1E03\u1E05\u1E07\u0180\u0183\u0253'
    }, {
      'base': 'c',
      'letters': '\u0063\u24D2\uFF43\u0107\u0109\u010B\u010D\u00E7\u1E09\u0188\u023C\uA73F\u2184'
    }, {
      'base': 'd',
      'letters': '\u0064\u24D3\uFF44\u1E0B\u010F\u1E0D\u1E11\u1E13\u1E0F\u0111\u018C\u0256\u0257\uA77A'
    }, {
      'base': 'dz',
      'letters': '\u01F3\u01C6'
    }, {
      'base': 'e',
      'letters': '\u0065\u24D4\uFF45\u00E8\u00E9\u00EA\u1EC1\u1EBF\u1EC5\u1EC3\u1EBD\u0113\u1E15\u1E17\u0115\u0117\u00EB\u1EBB\u011B\u0205\u0207\u1EB9\u1EC7\u0229\u1E1D\u0119\u1E19\u1E1B\u0247\u025B\u01DD'
    }, {
      'base': 'f',
      'letters': '\u0066\u24D5\uFF46\u1E1F\u0192\uA77C'
    }, {
      'base': 'g',
      'letters': '\u0067\u24D6\uFF47\u01F5\u011D\u1E21\u011F\u0121\u01E7\u0123\u01E5\u0260\uA7A1\u1D79\uA77F'
    }, {
      'base': 'h',
      'letters': '\u0068\u24D7\uFF48\u0125\u1E23\u1E27\u021F\u1E25\u1E29\u1E2B\u1E96\u0127\u2C68\u2C76\u0265'
    }, {
      'base': 'hv',
      'letters': '\u0195'
    }, {
      'base': 'i',
      'letters': '\u0069\u24D8\uFF49\u00EC\u00ED\u00EE\u0129\u012B\u012D\u00EF\u1E2F\u1EC9\u01D0\u0209\u020B\u1ECB\u012F\u1E2D\u0268\u0131'
    }, {
      'base': 'j',
      'letters': '\u006A\u24D9\uFF4A\u0135\u01F0\u0249'
    }, {
      'base': 'k',
      'letters': '\u006B\u24DA\uFF4B\u1E31\u01E9\u1E33\u0137\u1E35\u0199\u2C6A\uA741\uA743\uA745\uA7A3'
    }, {
      'base': 'l',
      'letters': '\u006C\u24DB\uFF4C\u0140\u013A\u013E\u1E37\u1E39\u013C\u1E3D\u1E3B\u017F\u0142\u019A\u026B\u2C61\uA749\uA781\uA747'
    }, {
      'base': 'lj',
      'letters': '\u01C9'
    }, {
      'base': 'm',
      'letters': '\u006D\u24DC\uFF4D\u1E3F\u1E41\u1E43\u0271\u026F'
    }, {
      'base': 'n',
      'letters': '\u006E\u24DD\uFF4E\u01F9\u0144\u00F1\u1E45\u0148\u1E47\u0146\u1E4B\u1E49\u019E\u0272\u0149\uA791\uA7A5'
    }, {
      'base': 'nj',
      'letters': '\u01CC'
    }, {
      'base': 'o',
      'letters': '\u006F\u24DE\uFF4F\u00F2\u00F3\u00F4\u1ED3\u1ED1\u1ED7\u1ED5\u00F5\u1E4D\u022D\u1E4F\u014D\u1E51\u1E53\u014F\u022F\u0231\u00F6\u022B\u1ECF\u0151\u01D2\u020D\u020F\u01A1\u1EDD\u1EDB\u1EE1\u1EDF\u1EE3\u1ECD\u1ED9\u01EB\u01ED\u00F8\u01FF\u0254\uA74B\uA74D\u0275'
    }, {
      'base': 'oi',
      'letters': '\u01A3'
    }, {
      'base': 'ou',
      'letters': '\u0223'
    }, {
      'base': 'oo',
      'letters': '\uA74F'
    }, {
      'base': 'p',
      'letters': '\u0070\u24DF\uFF50\u1E55\u1E57\u01A5\u1D7D\uA751\uA753\uA755'
    }, {
      'base': 'q',
      'letters': '\u0071\u24E0\uFF51\u024B\uA757\uA759'
    }, {
      'base': 'r',
      'letters': '\u0072\u24E1\uFF52\u0155\u1E59\u0159\u0211\u0213\u1E5B\u1E5D\u0157\u1E5F\u024D\u027D\uA75B\uA7A7\uA783'
    }, {
      'base': 's',
      'letters': '\u0073\u24E2\uFF53\u00DF\u015B\u1E65\u015D\u1E61\u0161\u1E67\u1E63\u1E69\u0219\u015F\u023F\uA7A9\uA785\u1E9B'
    }, {
      'base': 't',
      'letters': '\u0074\u24E3\uFF54\u1E6B\u1E97\u0165\u1E6D\u021B\u0163\u1E71\u1E6F\u0167\u01AD\u0288\u2C66\uA787'
    }, {
      'base': 'tz',
      'letters': '\uA729'
    }, {
      'base': 'u',
      'letters': '\u0075\u24E4\uFF55\u00F9\u00FA\u00FB\u0169\u1E79\u016B\u1E7B\u016D\u00FC\u01DC\u01D8\u01D6\u01DA\u1EE7\u016F\u0171\u01D4\u0215\u0217\u01B0\u1EEB\u1EE9\u1EEF\u1EED\u1EF1\u1EE5\u1E73\u0173\u1E77\u1E75\u0289'
    }, {
      'base': 'v',
      'letters': '\u0076\u24E5\uFF56\u1E7D\u1E7F\u028B\uA75F\u028C'
    }, {
      'base': 'vy',
      'letters': '\uA761'
    }, {
      'base': 'w',
      'letters': '\u0077\u24E6\uFF57\u1E81\u1E83\u0175\u1E87\u1E85\u1E98\u1E89\u2C73'
    }, {
      'base': 'x',
      'letters': '\u0078\u24E7\uFF58\u1E8B\u1E8D'
    }, {
      'base': 'y',
      'letters': '\u0079\u24E8\uFF59\u1EF3\u00FD\u0177\u1EF9\u0233\u1E8F\u00FF\u1EF7\u1E99\u1EF5\u01B4\u024F\u1EFF'
    }, {
      'base': 'z',
      'letters': '\u007A\u24E9\uFF5A\u017A\u1E91\u017C\u017E\u1E93\u1E95\u01B6\u0225\u0240\u2C6C\uA763'
    }
  ];
  for (q = 0, len2 = ref2.length; q < len2; q++) {
    item = ref2[q];
    ref3 = item.letters.split('');
    for (u = 0, len3 = ref3.length; u < len3; u++) {
      letter = ref3[u];
      DIACRITICS_MAP[letter] = item.base;
    }
  }

  sim('.i-differ').each(function() {
    var a, b, diff, len4, line, z;
    a = this.find('.i-differ-a').first();
    b = this.find('.i-differ-b').first();
    diff = JsDiff.diffLines(a.text(), b.text());
    b.empty();
    for (z = 0, len4 = diff.length; z < len4; z++) {
      line = diff[z];
      b.p('.m-0', function() {
        this.text(line.value);
        if (line.added) {
          this.addClass('text-success');
        }
        if (line.removed) {
          return this.addClass('text-danger');
        }
      });
    }
    return null;
  });

  global.EncryptedObject = (function() {
    function EncryptedObject(encrypted) {
      this.encrypted = encrypted;
      if (this.encrypted === null) {
        this.decrypted = {};
      }
    }

    EncryptedObject.prototype.decrypt = function(done) {
      var ref4;
      return Loader.api('decrypt', {
        method: 'POST',
        data: {
          data: (ref4 = this.encrypted) != null ? ref4 : null
        }
      }, (function(_this) {
        return function(err, data) {
          if (err) {
            return done(err);
          }
          _this.decrypted = data;
          return done(null, data);
        };
      })(this));
    };

    EncryptedObject.prototype.toJSON = function() {
      var ref4;
      return (ref4 = this.decrypted) != null ? ref4 : this.encrypted;
    };

    return EncryptedObject;

  })();

  Grid = (function(superClass) {
    extend1(Grid, superClass);

    Grid.prototype._masonry = null;

    Grid.prototype._browser = null;

    Grid.prototype._filter = null;

    Grid.prototype._selected = null;

    Grid.prototype._baseURL = null;

    Grid.prototype._body = null;

    Grid.prototype._offset = 0;

    Grid.prototype._perpage = 20;

    Grid.prototype._loader = null;

    Grid.prototype._more = false;

    Grid.prototype._empty = null;

    function Grid(elm) {
      this.toggleBrowser = bind(this.toggleBrowser, this);
      this.closeBrowser = bind(this.closeBrowser, this);
      var content, ref4, ref5, ref6, ref7, scrollee, scroller, self;
      Grid.__super__.constructor.call(this, elm != null ? elm : 'div');
      self = this;
      this._baseURL = this.data('base-url');
      this.addClass('i-grid');
      this._masonry = new Masonry('.i-grid-body', {
        itemSelector: '.i-grid-item',
        columnWidth: '.i-grid-sizer',
        percentPosition: true,
        transitionDuration: '0.2s'
      });
      this._offset = this._masonry.getItemElements().length;
      this._more = this._offset >= this._perpage;
      this._browser = this.children('.i-grid-browser').first();
      this._filter = this.children('.i-grid-filter').first();
      this._body = this.children('.i-grid-body').first();
      this._empty = this.children('.i-grid-empty').first();
      this._selected = (ref4 = this._filter) != null ? ref4.children('.i-grid-filter-item').map(function(item) {
        return item.data('pkg');
      }) : void 0;
      if (this.data('store')) {
        window.history.replaceState({
          grid: {
            filter: this._selected
          }
        }, '');
      }
      if ((ref5 = this._filter) != null) {
        ref5.find('.i-grid-browser-toggle').on('click', this.toggleBrowser);
      }
      if ((ref6 = this._browser) != null) {
        ref6.on('click', (function(_this) {
          return function(event) {
            if (event.target === event.currentTarget) {
              return _this.toggleBrowser();
            }
          };
        })(this));
      }
      if ((ref7 = this._filter) != null) {
        ref7.on('click', '.i-grid-filter-remove', function(event) {
          var pkg;
          event.stopPropagation();
          pkg = this.parent().remove().data('pkg');
          self._selected.remove(pkg);
          self.redirect();
          return false;
        });
      }
      this.on('click', '[data-pkg]:not(.i-grid-filter-item)', function(event) {
        var pkg;
        event.stopPropagation();
        pkg = {
          name: this.data('pkg'),
          label: this.text()
        };
        if ('yes' === this.data('reset')) {
          self._selected.splice(0, self._selected.length);
        }
        self.closeBrowser();
        self._selected.push(pkg.name);
        self.updateFilters();
        self.redirect();
        return false;
      });
      sim(window).on('popstate', (function(_this) {
        return function(event) {
          var ref8, ref9;
          if (((ref8 = event.state) != null ? ref8.grid : void 0) == null) {
            return;
          }
          _this._selected = (ref9 = event.state.grid.filter) != null ? ref9 : [];
          self.updateFilters();
          return _this.load();
        };
      })(this));
      content = sim('body > .content');
      sim(window).on('scroll', (function(_this) {
        return function() {
          if (sim(window).scrollTop() >= content.height() - sim(window).height()) {
            return _this.load(true);
          }
        };
      })(this));
      scrollee = this.closest('.tab-pane');
      scroller = scrollee != null ? scrollee.parent() : void 0;
      if (scroller != null) {
        scroller.on('scroll', (function(_this) {
          return function() {
            if (scroller.scrollTop() + 100 >= scrollee.height() - scroller.height()) {
              return _this.load(true);
            }
          };
        })(this));
      }
      (scroller != null ? scroller : sim(window)).emit('scroll');
    }

    Grid.prototype.redirect = function() {
      var filter;
      filter = this._selected.sort().join('/');
      window.history.pushState({
        grid: {
          filter: this._selected
        }
      }, '', "" + this._baseURL + (filter ? "/" + filter : ""));
      return this.load();
    };

    Grid.prototype.load = function(more) {
      var col, index, len4, ref4, z;
      if (more == null) {
        more = false;
      }
      if (more && this._loader) {
        return;
      }
      if (more && !this._more) {
        return;
      }
      if (!this.data('store')) {
        return;
      }
      if (this._loader) {
        this._loader.abort();
      }
      if (!more) {
        this._offset = 0;
        this._masonry.remove(this._masonry.getItemElements());
        ref4 = this._masonry.colYs;
        for (index = z = 0, len4 = ref4.length; z < len4; index = ++z) {
          col = ref4[index];
          this._masonry.colYs[index] = 0;
        }
        sim('.i-grid-body').height(0);
      }
      this._loader = Loader.load(this.data('store'), {
        method: 'POST',
        data: {
          filter: this._selected,
          page: {
            offset: this._offset,
            length: this._perpage
          }
        }
      }, (function(_this) {
        return function(err, templates) {
          _this._loader = null;
          if (err) {
            return new Alert(err.message).show();
          }
          if (!more) {
            _this._empty[templates.length === 0 ? 'addClass' : 'removeClass']('in');
          }
          _this._offset += templates.length;
          _this._more = templates.length === _this._perpage;
          templates = templates.map(function(html) {
            return sim.parse(html).first().appendTo(_this._body).__dom;
          });
          return _this._masonry.appended(templates);
        };
      })(this));
      return this;
    };

    Grid.prototype.closeBrowser = function() {
      return this._browser.removeClass('in');
    };

    Grid.prototype.toggleBrowser = function() {
      var self;
      if (this._browser.hasClass('in')) {
        return this.closeBrowser();
      }
      self = this;
      this._browser.find('.i-grid-browser-item').show().filter(function(item) {
        var ref4;
        return ref4 = item.data('pkg'), indexOf.call(self._selected, ref4) >= 0;
      }).hide();
      this._browser.addClass('in');
      return this;
    };

    Grid.prototype.updateFilters = function() {
      var ref4, self;
      self = this;
      return (ref4 = this._filter) != null ? ref4["do"](function() {
        var filter, len4, pkg, ref5, results, z;
        this.children('.i-grid-filter-item').remove();
        ref5 = self._selected;
        results = [];
        for (z = 0, len4 = ref5.length; z < len4; z++) {
          filter = ref5[z];
          pkg = self._browser.find("[data-pkg=\"" + filter + "\"]");
          pkg = {
            name: pkg.data('pkg'),
            label: pkg.text(),
            theme: pkg.data('theme')
          };
          results.push(this.div(".i-grid-filter-item.theme-" + pkg.theme, function() {
            this.data('pkg', pkg.name);
            this.text(pkg.label);
            return this.button('.btn.btn-transparent.btn-xs.i-grid-filter-remove', function() {
              this.attr('type', 'button');
              return this.i('i.fa.fa-times');
            });
          }));
        }
        return results;
      }) : void 0;
    };

    return Grid;

  })(SIMElement);

  sim.registerComponent('grid', Grid);

  sim.ready(function() {
    return sim('@grid');
  });

  sim(document).on('click', '.i-in-place-edit', function(event) {
    var done, keydown, normalize, value;
    if ('true' !== this.attr('contenteditable')) {
      this.attr('contenteditable', true);
      this.addClass('i-in-place-edit-active');
      done = (function(_this) {
        return function() {
          var newval;
          _this.attr('contenteditable', false);
          _this.removeClass('i-in-place-edit-active');
          _this.off('blur', done);
          _this.off('keydown', keydown);
          _this.off('input', normalize);
          newval = _this.text().trim() || imt.l('base', 'common.unnamed');
          if (newval !== value) {
            Loader.load(_this.data('url'), {
              method: 'POST',
              data: {
                data: newval
              }
            }, function(err, directives) {
              if (err) {
                _this.text(value);
                return new Alert(err.message).show();
              }
              if ((directives != null) && 'object' === typeof directives) {
                return AJAXDirectives.process(_this, directives);
              } else {
                return new Flash(imt.l('base', 'inplaceedit.saved'));
              }
            });
          }
          return _this.text(newval);
        };
      })(this);
      keydown = (function(_this) {
        return function(event) {
          switch (event.keyCode) {
            case 13:
              if (_this.data('multiline')) {
                document.execCommand('insertHTML', false, '\n');
                return false;
              }
              done();
              break;
            case 27:
              _this.text(value);
              event.preventDefault();
              done();
          }
          return null;
        };
      })(this);
      normalize = (function(_this) {
        return function() {
          var pos, range, ref4, ref5, sel;
          sel = global.getSelection();
          pos = (ref4 = sel.focusOffset) != null ? ref4 : 9999;
          _this.text(_this.text());
          range = global.document.createRange();
          range.setStart((ref5 = _this.__dom.firstChild) != null ? ref5 : _this.__dom, pos);
          range.collapse(true);
          sel.removeAllRanges();
          return sel.addRange(range);
        };
      })(this);
      value = this.text();
      if (value === imt.l('base', 'common.unnamed')) {
        this.text('');
      }
      this.focus();
      this.on('blur', done);
      this.on('keydown', keydown);
      this.on('input', normalize);
    }
    return true;
  });

  sim(document).on('click', '.i-in-place-rich-edit-insert', function(event) {
    var ref4, ref5;
    if ((ref4 = sim(this.data('target'))) != null) {
      if ((ref5 = ref4.data('codemirror')) != null) {
        ref5.replaceSelection(this.data('insert'));
      }
    }
    return false;
  });

  if (typeof CodeMirror !== "undefined" && CodeMirror !== null) {
    CodeMirror.commands.save = function(instance) {
      return CodeMirror.signal(instance, 'save');
    };
  }

  sim('.i-in-place-rich-edit').each(function() {
    var editor, init, options, save, saver, self, tab, url;
    if (global.onbeforeunload == null) {
      global.onbeforeunload = function() {
        if (sim('.i-in-place-rich-edit-changed').length) {
          return 'There are unsaved changes. Do you really want to leave?';
        }
      };
    }
    self = this;
    url = this.data('url');
    options = {
      readOnly: this.data('readonly') === 'yes',
      lineNumbers: true,
      indentWithTabs: true,
      smartIndent: false,
      indentUnit: 4,
      tabSize: 4,
      mode: this.data('mode') || 'IML',
      gutters: ['CodeMirror-lint-markers'],
      lint: {
        options: {
          asi: true,
          esversion: 6
        }
      }
    };
    if (options.mode === 'pug') {
      options.lineWrapping = true;
    }
    save = function() {
      var data;
      return Loader.load(url, {
        method: 'POST',
        data: {
          data: data = editor.getValue()
        }
      }, function(err, res) {
        if (err) {
          return new Alert(err.message).show();
        }
        if ((res != null) && 'object' === typeof res) {
          AJAXDirectives.process(self, res);
        } else {
          new Flash(imt.l('base', 'inplaceedit.saved'));
        }
        sim(editor.display.wrapper).removeClass('i-in-place-rich-edit-changed');
        return saver.detach();
      });
    };
    editor = null;
    saver = null;
    init = (function(_this) {
      return function() {
        saver = sim.i('.far.fa-save').on('click', save);
        editor = CodeMirror.fromTextArea(_this.__dom, options);
        _this.data('codemirror', editor);
        if (url && !options.readOnly) {
          editor.on('change', function() {
            return sim(editor.display.wrapper).addClass('i-in-place-rich-edit-changed').append(saver);
          });
          return editor.on('save', save);
        }
      };
    })(this);
    tab = this.closest('.tab-pane:not(.active)');
    if (tab) {
      return sim("*[data-toggle=\"tab\"][href=\"#" + (tab.attr('id')) + "\"]").once('shown.bs.tab', function() {
        return init();
      });
    } else {
      return init();
    }
  });

  PREVIEW_PANEL = null;

  sim(document).on('click', '.i-preview', function(event) {
    if (PREVIEW_PANEL) {
      PREVIEW_PANEL.close();
    }
    PREVIEW_PANEL = new Panel(this);
    PREVIEW_PANEL.expandable = true;
    PREVIEW_PANEL.title = 'Inspector';
    PREVIEW_PANEL.loading = true;
    return Loader.load(this.data('url'), function(err, data) {
      if (err) {
        return PREVIEW_PANEL.warn(err);
      }
      PREVIEW_PANEL.loading = false;
      return PREVIEW_PANEL.content = sim.div(function() {
        return this.visualizer({
          source: data
        }).on('resize', PREVIEW_PANEL._resize);
      });
    });
  });

  RemoteList = (function(superClass) {
    extend1(RemoteList, superClass);

    RemoteList.prototype._more = false;

    RemoteList.prototype._offset = 0;

    RemoteList.prototype._last = null;

    function RemoteList(elm) {
      RemoteList.__super__.constructor.call(this, elm != null ? elm : 'table');
      this.addClass('i-remotelist');
    }

    RemoteList.prototype.init = function(options) {
      var scrollee, scroller;
      if (options == null) {
        options = {};
      }
      if (options.autoload == null) {
        options.autoload = this.data('autoload') !== 'false';
      }
      if (options.perpage == null) {
        options.perpage = ifNaN(this.data('perpage'), 50);
      }
      if (options.group == null) {
        options.group = this.data('group') === 'yes';
      }
      if (options.group) {
        if (options.remover == null) {
          options.remover = this.data('group-remover');
        }
      }
      this.options = options;
      sim(window).on('scroll', (function(_this) {
        return function() {
          if (sim(window).scrollTop() >= sim('body > .content').height() - sim(window).height()) {
            if (_this._more) {
              return _this.load(true);
            }
          }
        };
      })(this));
      scrollee = this.closest('.tab-pane');
      scroller = scrollee != null ? scrollee.parent() : void 0;
      if (scroller != null) {
        scroller.on('scroll', (function(_this) {
          return function() {
            if (scroller.scrollTop() >= scrollee.height() - scroller.height()) {
              if (_this._more) {
                return _this.load(true);
              }
            }
          };
        })(this));
      }
      if (options.autoload) {
        return this.load();
      }
    };

    RemoteList.prototype.load = function(more) {
      var loading, self;
      if (more == null) {
        more = false;
      }
      this._more = false;
      if (more) {
        this._offset += this.options.perpage;
      } else {
        this._offset = 0;
      }
      self = this;
      Loader.load(this.data('store'), {
        method: 'POST',
        data: {
          page: {
            offset: this._offset,
            length: this.options.perpage
          }
        }
      }, (function(_this) {
        return function(err, data) {
          var group, len4, results, row, title, z;
          if (err) {
            return new Alert(err.message).show();
          }
          loading.remove();
          if (!more) {
            _this.empty();
          }
          _this._more = data.length >= _this.options.perpage;
          if (data.length) {
            results = [];
            for (z = 0, len4 = data.length; z < len4; z++) {
              row = data[z];
              item = sim.parse(row);
              if (_this.options.group && _this._last) {
                title = item.children('h3').text();
                if (_this._last.hasClass('list-group-group')) {
                  if (_this._last.data('title') === title) {
                    _this._last.append(item);
                    _this._last.find(':scope > .tools > .note').text(imt.l('base', 'common.nmessages', {
                      data: {
                        n: _this._last.data('items') + 1
                      }
                    }));
                    _this._last.data('items', _this._last.data('items') + 1);
                    continue;
                  }
                } else if (_this._last.find('.list-group-title').text() === title) {
                  group = sim.button('.list-group-item.list-group-group.list-group-clickable', function() {
                    this.data('items', 2);
                    this.data('title', item.find('.list-group-title').text());
                    this.i('.list-group-icon.fas.fa-ellipsis-v');
                    this.div('.list-group-title').text(title);
                    return this.div('.list-group-tools', function() {
                      if (self.options.remover) {
                        this.a('.btn.btn-outline-secondary.i-remover', function() {
                          this.i('.far.fa-trash');
                          this.attr('href', self.options.remover);
                          return this.data('grouped', 'yes');
                        });
                      }
                      return this.span('.list-group-note.text-muted').text(imt.l('base', 'common.nmessages', {
                        data: {
                          n: 2
                        }
                      }));
                    });
                  });
                  group.append(_this._last);
                  group.append(item);
                  _this.append(group);
                  _this._last = group;
                  continue;
                }
              }
              _this.append(item);
              results.push(_this._last = item);
            }
            return results;
          }
        };
      })(this));
      return loading = sim.div('.i-loading', function() {
        this.i('.far.fa-spin.fa-circle-notch');
        return this.appendTo(self);
      });
    };

    RemoteList.prototype.refresh = function() {
      return this.load();
    };

    return RemoteList;

  })(SIMElement);

  sim.registerComponent('remote-list', RemoteList);

  sim.remoteList = function(options) {
    return sim('@remote-list').init(options);
  };

  MODAL_SIZES = {
    LARGE: 'modal-lg',
    SMALL: 'modal-sm',
    MEDIUM: null
  };

  global.Modal = (function(superClass) {
    extend1(Modal, superClass);

    Modal.prototype._body = null;

    Modal.prototype._header = null;

    Modal.prototype._foooter = null;

    Modal.prototype._loading = null;

    Modal.prototype.__loading = false;

    Modal.prototype.__status = '';

    function Modal() {
      var self;
      Modal.__super__.constructor.call(this, 'div');
      this.addClass('modal fade');
      this.attr('tabindex', '-1');
      self = this;
      this.append(sim.div('.modal-dialog', function() {
        self._dialog = this;
        return this.div('.modal-content', function() {
          self._content = this;
          this.div('.modal-header', function() {
            self._header = this;
            this.h4('.modal-title').text('Modal');
            return this.button('.close', function() {
              this.attr('type', 'button');
              this.attr('data-dismiss', 'modal');
              return this.html('&times;');
            });
          });
          this.div('.modal-body', function() {
            return self._body = this;
          });
          return this.div('.modal-footer', function() {
            self._footer = this;
            return this.button('.btn.btn-sm.btn-outline-secondary', function() {
              self._close = this;
              this.attr('type', 'button');
              this.attr('data-dismiss', 'modal');
              return this.text(imt.l('base', 'common.close'));
            });
          });
        });
      }));
      this.on('hide.bs.modal', function() {
        return this.emit('before-hide');
      });
      this.on('hidden.bs.modal', function() {
        this.remove();
        this.emit('hide');
        this._body.contents().detach();
        this._footer.empty().append(this._close);
        this.loading = false;
        return this._footer.show();
      });
    }

    Modal.property('theme', {
      get: function() {
        return new Color(this.header.css('backgroundColor'));
      },
      set: function(value) {
        if (!(value instanceof Color)) {
          throw new TypeError("Color expected.");
        }
        return this.header.css({
          color: value.determineForegroundColor(),
          backgroundColor: value.toHex(),
          borderBottomColor: value.darker(30).toHex()
        });
      }
    });

    Modal.property('title', {
      get: function() {
        return this._header.children('h4').text();
      },
      set: function(value) {
        return this._header.children('h4').text(value);
      }
    });

    Modal.property('message', {
      get: function() {
        return this._body.text();
      },
      set: function(value) {
        return this._body.empty().p().text(value);
      }
    });

    Modal.property('loading', {
      get: function() {
        return this.__loading;
      },
      set: function(value) {
        var self;
        if (this.__loading === value) {
          return;
        }
        this.__loading = value;
        if (value) {
          self = this;
          this._body.children().hide();
          return this._loading = sim.div('.i-loading.text-center', function() {
            this.i('.far.fa-circle-notch.fa-spin');
            this.appendTo(self._body);
            if (self._status) {
              return this.append(self._status);
            }
          });
        } else {
          this._loading.remove();
          this._loading = null;
          return this._body.children().show();
        }
      }
    });

    Modal.property('status', {
      get: function() {
        return this.__status;
      },
      set: function(value) {
        var ref4;
        if (this.__status === value) {
          return;
        }
        this.__status = value;
        if (this._status) {
          return this._status.text(value);
        } else {
          this._status = sim.span().text(value);
          return (ref4 = this._loading) != null ? ref4.append(this._status) : void 0;
        }
      }
    });

    Modal.property('content', {
      get: function() {
        return this._body.children();
      },
      set: function(value) {
        var len4, results, z;
        this._body.contents().detach();
        if (value instanceof Array) {
          results = [];
          for (z = 0, len4 = value.length; z < len4; z++) {
            item = value[z];
            if (value != null) {
              if (item instanceof SIMElement) {
                results.push(this._body.append(item));
              } else {
                results.push(this._body.append(value));
              }
            }
          }
          return results;
        } else if (value instanceof SIMElement) {
          return this._body.append(value);
        } else {
          if (value != null) {
            return this._body.append(value);
          }
        }
      }
    });

    Modal.property('size', {
      get: function() {
        if (this._dialog.hasClass('modal-lg')) {
          return MODAL_SIZES.LARGE;
        } else {
          if (this._dialog.hasClass('modal-sm')) {
            return MODAL_SIZES.SMALL;
          } else {
            return MODAL_SIZES.NORMAL;
          }
        }
      },
      set: function(value) {
        value = value.toUpperCase();
        this._dialog.removeClass('modal-lg').removeClass('modal-sm');
        return this._dialog.addClass(MODAL_SIZES[value]);
      }
    });

    Modal.prototype.destructor = function() {
      return Modal.__super__.destructor.call(this);
    };

    Modal.prototype.addButton = function(label, style) {
      var self;
      if (style == null) {
        style = 'default';
      }
      self = this;
      return sim.button(".btn.btn-sm.btn-" + style, function() {
        this.attr('type', 'button');
        this.attr('data-dismiss', 'modal');
        this.text(label);
        return this.appendTo(self._footer);
      });
    };


    /*
    	Hide modal window.
     */

    Modal.prototype.hide = function() {
      if (!this.is(':visible')) {
        return;
      }
      this.modal('hide');
      return this;
    };


    /*
    	Show modal window.
     */

    Modal.prototype.show = function() {
      this.modal('show');
      return this;
    };

    Modal.prototype.warn = function(message, content) {
      var exception;
      this.loading = false;
      exception = sim.div('.i-exception', function() {
        if (message instanceof Error) {
          ex = message;
          this.h5().text(imt.l('base', 'common.error'));
          return this.p(function() {
            var ref4;
            this.text(ex.message);
            if ((ref4 = ex.errors) != null ? ref4.length : void 0) {
              return this.ul('.list-unstyled.i-exception-suberrors', function() {
                var len4, ref5, results, serr, z;
                ref5 = ex.errors;
                results = [];
                for (z = 0, len4 = ref5.length; z < len4; z++) {
                  serr = ref5[z];
                  results.push(this.li(function() {
                    this.text("" + serr.message);
                    return this.prepend(sim.i('.far.fa-fw.fa-angle-right'));
                  }));
                }
                return results;
              });
            }
          });
        } else {
          this.h5().text(imt.l('base', 'common.error'));
          return this.p().text(message);
        }
      });
      if (content) {
        return this.content = [exception, content];
      } else {
        return this.content = exception;
      }
    };

    return Modal;

  })(SIMElement);

  RemoteTable = (function(superClass) {
    extend1(RemoteTable, superClass);

    RemoteTable.prototype.columns = null;

    RemoteTable.prototype.indexed = null;

    RemoteTable.prototype.filters = null;

    RemoteTable.prototype._rowid = null;

    RemoteTable.prototype._more = false;

    RemoteTable.prototype._tbody = null;

    RemoteTable.prototype._thead = null;

    RemoteTable.prototype._offset = 0;

    RemoteTable.prototype._refresh = null;

    RemoteTable.prototype._scroller = null;

    RemoteTable.prototype._scrollee = null;

    RemoteTable.prototype._initialized = false;

    RemoteTable.prototype._globals = null;

    function RemoteTable(elm) {
      var ref4;
      RemoteTable.__super__.constructor.call(this, elm != null ? elm : 'table');
      this._scrollee = this.closest('.tab-pane');
      this._scroller = (ref4 = this._scrollee) != null ? ref4.parent() : void 0;
      this.addClass('i-remotetable');
    }

    RemoteTable.prototype.init = function(options) {
      var content, header, ref4, ref5, ref6, self;
      self = this;
      if (options == null) {
        options = {};
      }
      if (options.on == null) {
        options.on = {};
      }
      if (options.autoload == null) {
        options.autoload = this.data('autoload') !== 'false';
      }
      if (options.refresh == null) {
        options.refresh = this.data('refresh');
      }
      if (options.sort == null) {
        options.sort = this.data('sort');
      }
      if (options.sortdir == null) {
        options.sortdir = this.data('sortdir');
      }
      if (options.perpage == null) {
        options.perpage = ifNaN(this.data('perpage'), 50);
      }
      if (options.max == null) {
        options.max = this.data('max');
      }
      this.options = options;
      if (this.data('refresh-btn')) {
        if ((ref4 = sim("#" + (this.data('refresh-btn')))) != null) {
          ref4.on('click', this.refresh.bind(this));
        }
      }
      if (options.max) {
        options.perpage = parseInt(options.max);
      } else {
        window = sim(window);
        content = sim('body > .content').first();
        window.on('scroll', (function(_this) {
          return function() {
            if (window.scrollTop() >= content.height() - window.height()) {
              if (_this._more) {
                return _this.load(true);
              }
            }
          };
        })(this));
        if ((ref5 = this._scroller) != null) {
          ref5.on('scroll', (function(_this) {
            return function() {
              if (_this._scroller.scrollTop() >= _this._scrollee.height() - _this._scroller.height()) {
                if (_this._more) {
                  return _this.load(true);
                }
              }
            };
          })(this));
        }
      }
      this.filters = [];
      this.indexed = {};
      this.columns = [];
      header = this.find('thead tr');
      if (header.length === 0) {
        header = this.find('tr:first-child');
        if (header.length === 0) {
          header = sim.array(sim.tr());
        }
        this.prepend(sim.thead().append(header));
      }
      this._thead = this.children('thead').first();
      this._tbody = (ref6 = this.children('tbody').first()) != null ? ref6 : this.tbody();
      header.each((function(_this) {
        return function(index, item) {
          _this._rowid = item.data('id');
          return item.children('th').each(function(index, item) {
            var column, name, ref7;
            name = item.data('name');
            column = {
              name: name,
              label: item.text(),
              icon: item.data('icon'),
              type: item.data('type'),
              template: item.data('template'),
              update: (ref7 = item.data('update')) !== 'false' && ref7 !== 'no',
              "class": item.data('class'),
              element: item,
              format: {}
            };
            if (name) {
              if (_this.indexed[name]) {
                console.warn("Found two columns with same name '" + name + "'!");
              }
              _this.indexed[name] = column;
            }
            switch (column.type) {
              case 'date':
              case 'datetime':
              case 'time':
                column.format.timezone = item.data('timezone');
                break;
              case 'currency':
                column.format.currency = item.data('currency');
            }
            return _this.columns.push(column);
          });
        };
      })(this));
      if (options.autoload) {
        this.load();
      }
      this.on('click', '.i-remote-table-expand', function() {
        var filter, key, ref7, value;
        this.enabled = false;
        filter = {};
        ref7 = this.data();
        for (key in ref7) {
          value = ref7[key];
          if (/^filter-(.*)$/.exec(key)) {
            filter[RegExp.$1] = value;
          }
        }
        self.expand(this.closest('tr'), this.data('store'), filter, (function(_this) {
          return function() {
            return _this.enabled = true;
          };
        })(this));
        return false;
      });
      return this;
    };

    RemoteTable.prototype.initColumns = function(columns, metadata) {
      var add, col, cols, i1, iml, j1, key, kv, kvs, len4, len5, len6, name, ref4, self, value, values, z;
      if (this._initialized) {
        return;
      }
      this._initialized = true;
      this._globals = metadata.globals;
      iml = function(template) {
        return IML.execute(IML.parse(template), metadata.globals, {
          functions: {
            format: function(value, type, options) {
              return format(value, type, options || {
                timezone: imt.user.timezone
              });
            },
            l: imt.l.bind(imt),
            "static": imt["static"]
          }
        });
      };
      if (columns != null) {
        add = this.columns.length === 0;
        if (!Array.isArray(columns)) {
          cols = columns;
          columns = [];
          for (name in cols) {
            col = cols[name];
            if (col.name == null) {
              col.name = name;
            }
            columns.push(col);
          }
        }
        for (z = 0, len4 = columns.length; z < len4; z++) {
          col = columns[z];
          if (col.name && (this.indexed[col.name] != null)) {
            for (key in col) {
              value = col[key];
              this.indexed[col.name][key] = value;
            }
          } else if (add) {
            this._thead.children('tr').first().append(sim.th(function() {
              return this.text(iml(col.label || col.name));
            }));
            this.columns.push(col);
            if (col.name) {
              this.indexed[col.name] = col;
            }
            if (col.update == null) {
              col.update = true;
            }
          }
        }
      }
      values = {};
      if (/#filter\:([^#]+)/.exec(window.location.hash)) {
        kvs = RegExp.$1.split('&');
        for (i1 = 0, len5 = kvs.length; i1 < len5; i1++) {
          kv = kvs[i1];
          if (/^([^=]+)\=(.+)$/.exec(kv)) {
            values[decodeURIComponent(RegExp.$1)] = decodeURIComponent(RegExp.$2);
          }
        }
      }
      for (key in values) {
        value = values[key];
        if (/^\s*-?\d+(\.\d+)?\s*$/.test(value)) {
          values[key] = parseFloat(value);
        } else if (/^\s*\d{4}\-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z\s*$/i.test(value)) {
          values[key] = IMTDate.parse(value);
        }
      }
      self = this;
      ref4 = this.columns;
      for (j1 = 0, len6 = ref4.length; j1 < len6; j1++) {
        col = ref4[j1];
        if (col.filter != null) {
          (function(_this) {
            return (function(col) {
              var form, panel;
              panel = null;
              form = new Formula('ColumnFilter');
              form.config = col.filter;
              form.values = values;
              form.build();
              _this.filters.push(form);
              return sim.i('.fa.fa-filter', function() {
                var filter;
                filter = this;
                if (col.filter.filter(function(item) {
                  return values[item.name] != null;
                }).length) {
                  this.addClass('text-primary');
                }
                this.appendTo(col.element);
                return this.on('click', function() {
                  panel = new Panel(filter);
                  panel.title = imt.l('base', 'common.filter');
                  panel.content = form;
                  panel.offsetX = 10;
                  return sim.button('.btn.btn-primary', function() {
                    this.text(imt.l('base', 'common.save'));
                    this.appendTo(panel._footer);
                    return this.on('click', function() {
                      var data, hasFilter;
                      if (form.isValid()) {
                        data = form.toJSON();
                        hasFilter = Object.keys(data).some(function(name) {
                          return (data[name] != null) && data[name] !== '';
                        });
                        if (hasFilter) {
                          filter.addClass('text-primary');
                        } else {
                          filter.removeClass('text-primary');
                        }
                        self.load();
                        panel.close();
                        return self.updateHash();
                      }
                    });
                  });
                });
              });
            });
          })(this)(col);
        }
      }
      return this.load();
    };

    RemoteTable.prototype.loadColumns = function() {
      var ref4;
      return Loader.load((ref4 = this.options.store) != null ? ref4 : this.data('store'), {
        method: 'GET'
      }, (function(_this) {
        return function(err, data, headers, metadata) {
          if (err) {
            return new Alert(err.message).show();
          }
          return _this.initColumns(data, metadata);
        };
      })(this));
    };

    RemoteTable.prototype.expand = function(tr, store, addToFilter, done) {
      var filter, form, len4, ref4, z;
      filter = {};
      ref4 = this.filters;
      for (z = 0, len4 = ref4.length; z < len4; z++) {
        form = ref4[z];
        extend(filter, form.toJSON());
      }
      if (addToFilter) {
        extend(filter, addToFilter);
      }
      return Loader.load(store != null ? store : this.data('store'), {
        method: 'POST',
        data: {
          filter: filter,
          page: {
            offset: 0,
            length: 100
          }
        }
      }, (function(_this) {
        return function(err, data) {
          if (err) {
            return new Alert(err.message).show();
          }
          _this.render(null, data, tr);
          tr.remove();
          return done();
        };
      })(this));
    };

    RemoteTable.prototype.load = function(more) {
      var body, filter, form, k, len4, loading, ref4, ref5, ref6, rows, self, v, z;
      if (more == null) {
        more = false;
      }
      if (!this._initialized) {
        return this.loadColumns();
      }
      this._more = false;
      if (this._refresh) {
        clearTimeout(this._refresh);
        this._refresh = null;
      }
      if (more) {
        this._offset += this.options.perpage;
      } else {
        this._offset = 0;
      }
      self = this;
      filter = {};
      ref4 = this.filters;
      for (z = 0, len4 = ref4.length; z < len4; z++) {
        form = ref4[z];
        extend(filter, form.toJSON());
      }
      rows = this._tbody.children().length;
      body = {
        filter: filter,
        page: {
          offset: this._offset,
          length: this.options.perpage
        }
      };
      if (this.options.body) {
        ref5 = this.options.body;
        for (k in ref5) {
          v = ref5[k];
          body[k] = v;
        }
      }
      Loader.load((ref6 = this.options.store) != null ? ref6 : this.data('store'), {
        method: 'POST',
        data: body
      }, (function(_this) {
        return function(err, data, headers, metadata) {
          var base;
          if (err) {
            return new Alert(err.message).show();
          }
          if (_this.options.sort) {
            data.sort(function(a, b) {
              if (_this.options.sortdir === 'desc') {
                if (a[_this.options.sort] > b[_this.options.sort]) {
                  return -1;
                } else {
                  return 1;
                }
              } else {
                if (a[_this.options.sort] > b[_this.options.sort]) {
                  return 1;
                } else {
                  return -1;
                }
              }
            });
          }
          if (typeof loading !== "undefined" && loading !== null) {
            loading.remove();
          }
          self.find('tr.out').removeClass('out');
          if (!more && !_this._rowid) {
            _this._tbody.children().remove();
          } else if (_this._rowid) {
            _this._tbody.children().each(function(index, item) {
              var i1, len5, row, rowid;
              rowid = item.data('id');
              for (i1 = 0, len5 = data.length; i1 < len5; i1++) {
                row = data[i1];
                if (String(row[_this._rowid]) === rowid) {
                  return;
                }
              }
              return item.remove();
            });
          }
          _this._more = data.length >= _this.options.perpage;
          if (typeof (base = _this.options.on).info === "function") {
            base.info(_this._offset + data.length, metadata != null ? metadata.total : void 0);
          }
          if (data.length) {
            _this.render(rows, data);
          } else {
            _this._tbody.tr().td('.text-center').attr('colspan', self.columns.length).text(imt.l('base', 'remotetable.nodata'));
          }
          if (_this.options.refresh) {
            return _this._refresh = setTimeout(function() {
              return _this.refresh();
            }, _this.options.refresh);
          }
        };
      })(this));
      if (!rows || !this._rowid) {
        return loading = sim.tr('.i-loading', function() {
          var headerHeight;
          if (!more && rows) {
            headerHeight = self._thead.height();
            this.addClass('i-reloading');
            this.css({
              top: headerHeight + "px",
              width: (self.width()) + "px",
              height: (self.height() - headerHeight) + "px"
            });
            self._tbody.children('tr').addClass('out');
          }
          this.td(function() {
            this.attr('colspan', self.columns.length);
            return this.i('.far.fa-spin.fa-circle-notch');
          });
          return this.appendTo(self._tbody);
        });
      }
    };

    RemoteTable.prototype.render = function(rows, data, before) {
      var col, coloffset, colspan, i1, iml, index, j1, k1, len4, len5, len6, len7, ref4, ref5, ref6, ref7, row, rowid, self, skip, td, tds, tempval, tr, z;
      self = this;
      iml = function(template, row) {
        return IML.execute(IML.parse(template), Object.assign({
          data: row
        }, self._globals), {
          functions: {
            format: function(value, type, options) {
              return format(value, type, options || {
                timezone: imt.user.timezone
              });
            },
            l: imt.l.bind(imt),
            "static": imt["static"]
          }
        });
      };
      for (z = 0, len4 = data.length; z < len4; z++) {
        row = data[z];
        tr = null;
        rowid = null;
        if (this._rowid && (row[this._rowid] != null)) {
          rowid = row[this._rowid];
          tr = this.find("tr[data-id=\"" + rowid + "\"]");
          if (!tr.length) {
            tr = null;
          }
        }
        if (!tr) {
          tr = sim.tr();
          if (before) {
            tr.insertBefore(before);
          } else {
            tr.appendTo(this._tbody);
          }
          skip = 0;
          ref4 = this.columns;
          for (index = i1 = 0, len5 = ref4.length; i1 < len5; index = ++i1) {
            col = ref4[index];
            if (skip-- > 0) {
              continue;
            }
            td = tr.td();
            if (col["class"]) {
              td.addClass(iml(col["class"], row));
            }
            if (col.merge && iml(col.merge.condition, row)) {
              skip = (iml(col.merge.span, row) || this.columns.length - index) - 1;
              td.attr('colspan', skip + 1);
            }
          }
          if (rowid) {
            tr.attr('data-id', rowid);
          }
        }
        tds = tr.children('td');
        ref5 = this.columns;
        for (index = j1 = 0, len6 = ref5.length; j1 < len6; index = ++j1) {
          col = ref5[index];
          if (!rows || rows && col.update) {
            if (col.name && col.type && !col.template) {
              row[col.name] = format(row[col.name], col.type, col.format);
            }
          }
        }
        coloffset = 0;
        skip = 0;
        ref6 = this.columns;
        for (index = k1 = 0, len7 = ref6.length; k1 < len7; index = ++k1) {
          col = ref6[index];
          if (!(!rows || rows && col.update)) {
            continue;
          }
          if (skip-- > 0) {
            continue;
          }
          td = tds[index - coloffset];
          colspan = parseInt(td.attr('colspan'));
          if (!isNaN(colspan)) {
            skip = colspan - 1;
            coloffset += colspan - 1;
          }
          if (typeof col.template === 'function') {
            tempval = col.template(row, col);
            if ((ref7 = typeof tempval) === 'string' || ref7 === 'number' || ref7 === 'boolean') {
              td.html(tempval);
            } else {
              td.append(tempval);
            }
          } else if (typeof col.template === 'string') {
            td.html(iml(col.template, row));
          } else if (Array.isArray(col.buttons)) {
            td.div('.btn-group', function() {
              var button, l1, len8, ref8, results;
              ref8 = col.buttons;
              results = [];
              for (l1 = 0, len8 = ref8.length; l1 < len8; l1++) {
                button = ref8[l1];
                if (!button.condition || iml(button.condition, row)) {
                  results.push(this[button.href ? 'a' : 'button']('.btn.btn-xs', function() {
                    var fce, key, name, ref10, ref9, results1, value;
                    if (button.href) {
                      this.attr('href', iml(button.href, row));
                    } else {
                      this.attr('type', 'button');
                    }
                    this.text(iml(button.label, row));
                    if (button["class"] != null) {
                      this.addClass(iml(button["class"], row));
                    }
                    if (button.data) {
                      ref9 = button.data;
                      for (key in ref9) {
                        value = ref9[key];
                        this.data(key, iml(value, row));
                      }
                    }
                    if (button.icon) {
                      if (button.label) {
                        this.prepend(sim.text('\u00A0\u00A0'));
                      }
                      this.prepend(sim.i(".far.fa-" + button.icon));
                    }
                    if (button.on) {
                      ref10 = button.on;
                      results1 = [];
                      for (name in ref10) {
                        fce = ref10[name];
                        results1.push(this.on(name, fce.bind(self._table)));
                      }
                      return results1;
                    }
                  }));
                } else {
                  results.push(void 0);
                }
              }
              return results;
            });
          } else {
            td.text(row[col.name]);
          }
          if (col.icon) {
            td.prepend(sim.i(col.icon + ".mr-2"));
          }
        }
      }
      return sim(window).emit('resize');
    };

    RemoteTable.prototype.refresh = function() {
      return this.load();
    };

    RemoteTable.prototype.updateHash = function() {
      var filter, form, hash, key, len4, ref4, value, z;
      filter = {};
      ref4 = this.filters;
      for (z = 0, len4 = ref4.length; z < len4; z++) {
        form = ref4[z];
        extend(filter, form.toJSON());
      }
      hash = [];
      for (key in filter) {
        value = filter[key];
        if ((value != null) && value !== '') {
          hash.push((encodeURIComponent(key)) + "=" + (encodeURIComponent(value)));
        }
      }
      return window.history.replaceState(null, '', hash.length ? "#filter:" + (hash.join('&')) : '#');
    };

    return RemoteTable;

  })(SIMElement);

  sim.registerComponent('remote-table', RemoteTable);

  sim.ready(function() {
    return sim('@remote-table').each(function() {
      return this.init();
    });
  });

  sim('body').on('click', '.i-remover', function(event) {
    var confirm, data, fa, group, grouped, load, nbsp, redirect, ref4, ref5, ref6, refresh, restore, self, url;
    event.preventDefault();
    event.stopPropagation();
    self = this;
    redirect = this.data('redirect');
    refresh = this.data('refresh');
    confirm = (ref4 = this.data('confirm')) != null ? ref4 : 'yes';
    grouped = this.data('grouped') === 'yes';
    url = (ref5 = this.data('url')) != null ? ref5 : this.attr('href');
    nbsp = this.children('i.mr-2').length ? '' : '&nbsp;&nbsp;';
    if (grouped) {
      group = this.closest('.list-group-group');
      if (!group) {
        return;
      }
    }
    if (this.hasClass('btn') && !this.hasClass('btn-danger')) {
      this.addClass('btn-danger');
      this.data('colored', true);
    } else if (this.hasClass('dropdown-item') && !this.hasClass('dropdown-item-danger')) {
      this.addClass('dropdown-item-danger');
      this.data('colored', true);
    }
    if ((ref6 = this.closest('.dropdown-menu')) != null) {
      ref6.parent().addClass('open');
    }
    restore = (function(_this) {
      return function() {
        if (_this.data('rly')) {
          _this.data('rly', false);
          _this.data('working', false);
          _this.prop('enabled', true);
          _this.empty().append(_this.data('before-rly'));
          if (_this.data('colored')) {
            return _this.removeClass('btn-danger dropdown-item-danger');
          }
        }
      };
    })(this);
    if (confirm === 'no') {
      this.data('before-rly', this.contents());
      this.data('rly', true);
    }
    if (!this.data('rly')) {
      this.data('before-rly', this.contents());
      this.data('rly', true);
      fa = this.data('before-rly').filter('i');
      if (fa.length) {
        this.html("" + nbsp + (imt.l('base', 'remover.really')));
        this.prepend(fa);
      } else {
        this.text(imt.l('base', 'remover.really'));
      }
      this.data('timeout', setTimeout(restore, 5000));
    } else {
      clearTimeout(this.data('timeout'));
      this.data('timeout', null);
      if (this.data('working')) {
        return;
      }
      this.data('working', true);
      this.prop('enabled', false);
      if (confirm !== 'no') {
        if (this.data('before-rly').filter('i').length) {
          this.html("" + nbsp + (imt.l('base', 'remover.deleting')));
          this.prepend(sim.i('.far.fa-circle-notch.fa-spin'));
        } else {
          this.text(imt.l('base', 'remover.deleting'));
        }
      }
      data = {};
      if (grouped) {
        data.ids = group.find(':scope > .list-group-item').map(function(item) {
          return parseInt(item.data('id'));
        });
      }
      load = function(confirmed) {
        if (confirmed == null) {
          confirmed = false;
        }
        if (confirmed) {
          url += '?confirmed=yes';
        }
        return Loader.load(url, {
          method: 'DELETE',
          data: data
        }, function(err, removed) {
          var parent, prompt, ref7, ref8, target;
          if (err) {
            if (err.code === 'IM004') {
              prompt = new Prompt;
              prompt._body.html(err.prompt);
              prompt.show(function(result) {
                if (result) {
                  return load(true);
                }
                return restore();
              });
              return;
            }
            restore();
            return new Alert(err.message).show();
          }
          if (removed) {
            if ((ref7 = self.data('fade')) !== 'false' && ref7 !== 'no') {
              parent = self.closest('.list-group-item');
              if (parent) {
                if ((ref8 = parent.next('.list-group-item-detail')) != null) {
                  ref8.slideUp();
                }
              }
              if (parent == null) {
                parent = self.closest('.alert');
              }
              if (parent == null) {
                parent = self.closest('tr');
              }
              if (parent == null) {
                parent = self.closest('li');
              }
              if (parent != null) {
                parent.fadeOut();
              }
            }
            if ('object' === typeof removed) {
              AJAXDirectives.process(self, removed);
            }
          } else {
            new Alert(imt.l('base', 'remover.failed')).show();
          }
          self.data('working', false);
          if (redirect) {
            self.empty().text(imt.l('base', 'remover.redirecting'));
            return window.location = redirect;
          } else {
            if ('string' === typeof refresh) {
              target = sim(refresh);
              if (target instanceof SIMArray) {
                target = target.first();
              }
              if (target != null) {
                target.refresh();
              }
            }
            return restore();
          }
        });
      };
      load();
    }
    return false;
  });

  SIMElement.prototype.searcher = function() {
    var analyticsTimer, filter, preset, root, self;
    self = this;
    root = sim(this.data('root')).first();
    if (root == null) {
      return;
    }
    analyticsTimer = null;
    filter = function(phrase) {
      var headers, items, words;
      if (phrase == null) {
        phrase = '';
      }
      items = root.find(self.data('item'));
      items.removeClass('d-none');
      words = phrase.trim().toLowerCase().removeDiacritics();
      if (words != null ? words.length : void 0) {
        words = words.split(' ');
        items.each(function() {
          var lookup, text;
          lookup = words.clone();
          text = this.text().toLowerCase().removeDiacritics();
          lookup = lookup.filter(function(word) {
            return text.indexOf(word) === -1;
          });
          if (lookup.length !== 0) {
            return this.addClass('d-none');
          }
        });
        if (self.data('analytics')) {
          undelay(analyticsTimer);
          analyticsTimer = delay(1000, function() {
            if (words.length) {
              return typeof ga === "function" ? ga('send', 'pageview', "/search?ql=" + imt.user.language + "&qc=" + (self.data('analytics')) + "&q=" + (encodeURIComponent(words.join(' ')))) : void 0;
            }
          });
        }
      }
      if (self.data('header')) {
        headers = root.find(self.data('header')).each(function() {
          var sibling;
          sibling = this.next(':not(.d-none)');
          if (sibling && sibling.is(self.data('item'))) {
            return this.removeClass('d-none');
          } else {
            return this.addClass('d-none');
          }
        });
      }
      return sim(window).emit('imt.search');
    };
    preset = function(name) {
      sim(self.data('presets')).removeClass('active');
      sim(self.data('presets')).filter(function(item) {
        return item.attr('href') === ("#" + name);
      }).addClass('active');
      self.val('');
      if (self.data('reset') === name) {
        filter();
      } else {
        filter(name);
      }
      if (sim(window).scrollTop() > root.offset().top - 30) {
        window.scrollTo(0, root.offset().top - 30);
      }
      return window.history.replaceState(null, '', "#filter:" + name);
    };
    this.on('input', function() {
      if (this.data('presets')) {
        sim(this.data('presets')).removeClass('active');
      }
      filter(this.val());
      if (!this.val() && this.data('reset') && this.data('presets')) {
        return sim(this.data('presets') + '[href="#' + this.data('reset') + '"]').addClass('active');
      }
    });
    if (this.data('presets')) {
      sim(this.data('presets')).on('click', function() {
        preset(this.attr('href').substr(1));
        return false;
      });
    }
    if (/^#filter:(.*)$/.exec(sim(window).location.hash)) {
      preset(RegExp.$1);
    }
    if (this.val()) {
      return filter();
    }
  };

  sim('.searcher').each(SIMElement.prototype.searcher);

  initSwitch = function() {
    var ajax, me, swtch;
    this.attr('tabindex', 0);
    this.div('.switch-slider');
    ajax = this.data('ajax') !== 'no';
    if (this.data('status') === 'on') {
      this.addClass('active');
    } else {
      this.removeClass('active');
    }
    me = this;
    swtch = function() {
      if (me.hasClass('disabled') || me.is(':disabled')) {
        return;
      }
      if (me.beforeChange) {
        if (false === me.beforeChange(swtch)) {
          return;
        }
      }
      if (me.data('status') === 'on') {
        if (me.data('stop-url')) {
          me.prop('disabled', true);
          if (!ajax) {
            return window.location.href = me.data('stop-url');
          }
          return Loader.load(me.data('stop-url'), {
            method: 'POST'
          }, function(err, directives) {
            me.prop('disabled', false);
            if (err) {
              return new Alert(err.message).show();
            }
            me.removeClass('active');
            me.data('status', 'off');
            me.emit('change');
            if ('object' === typeof directives) {
              return AJAXDirectives.process(me, directives);
            }
          });
        } else {
          me.removeClass('active');
          me.data('status', 'off');
          return me.emit('change');
        }
      } else {
        if (me.data('start-url')) {
          me.prop('disabled', true);
          if (!ajax) {
            return window.location.href = me.data('stop-url');
          }
          return Loader.load(me.data('start-url'), {
            method: 'POST'
          }, function(err, directives) {
            me.prop('disabled', false);
            if (err) {
              return new Alert(err.message).show();
            }
            if ('object' === typeof directives) {
              AJAXDirectives.process(me, directives);
            }
            me.addClass('active');
            me.data('status', 'on');
            return me.emit('change');
          });
        } else {
          me.addClass('active');
          me.data('status', 'on');
          return me.emit('change');
        }
      }
    };
    this.on('keyup', function(event) {
      if (event.keyCode === 32) {
        swtch();
        event.stopPropagation();
        event.preventDefault();
        return false;
      }
    });
    return this.on('click', function(event) {
      swtch();
      event.stopPropagation();
      event.preventDefault();
      return false;
    });
  };

  sim('.switch').each(initSwitch);

  SIMElement.prototype["switch"] = initSwitch;

  sim(document).on('click', '.i-updater, .i-loader', function(event) {
    var ref4, self, url;
    event.preventDefault();
    self = this;
    url = (ref4 = this.data('url')) != null ? ref4 : this.attr('href');
    Loader.load(url, {
      method: this.hasClass('i-updater') ? 'POST' : 'GET'
    }, function(err, data) {
      var region;
      if (err) {
        return new Alert(err.message).show();
      }
      region = self.closest('.list-group-item');
      if (region == null) {
        region = self.closest('tr');
      }
      AJAXDirectives.process(self, data, region);
      return null;
    });
    return true;
  });

  sim(document).on('click', '.i-uploader', function(event) {
    var existing, file, flash, form, formData, input, len4, ref4, z;
    event.preventDefault();
    form = this.closest('form');
    input = form.find('input[type="file"]')[0].__dom;
    formData = new FormData;
    existing = form.find('.thumbnail > img');
    if (!(input.files instanceof FileList)) {
      return false;
    }
    if (input.files.length === 0) {
      return false;
    }
    ref4 = input.files;
    for (z = 0, len4 = ref4.length; z < len4; z++) {
      file = ref4[z];
      formData.append("file[]", file);
    }
    flash = new Flash({
      text: 'Uploading images...',
      icon: '.far.fa-cog.fa-spin',
      permanent: true
    });
    return Loader.load(this.data('store'), {
      method: 'POST',
      data: formData
    }, (function(_this) {
      return function(err, data) {
        flash.hide();
        if (err) {
          return new Alert(err.message).show();
        }
        AJAXDirectives.process(_this, data, form);
        form.find('.thumbnail > img').filter(function(img) {
          return indexOf.call(existing, img) < 0;
        }).on('error', function() {
          var src;
          this.parent().addClass('i-uploader-loading');
          src = this.attr('src').match(/^(.*?)(?:\?|$)/)[1];
          return delay(1000, (function(_this) {
            return function() {
              return _this.attr('src', src + "?nocache=" + (Date.now()));
            };
          })(this));
        }).on('load', function() {
          return this.parent().removeClass('i-uploader-loading');
        });
        return new Flash("Images were uploaded.");
      };
    })(this));
  });

  sim(document).on('click', '.i-uploader-insert', function(event) {
    return sim('.i-uploader-target').first().data('codemirror').replaceSelection("![alt text](" + (this.data('insert') || this.attr('src')) + ")");
  });

  (function() {
    var cache;
    cache = {};
    return Object.defineProperties(imt.config, {
      showIDs: {
        get: function() {
          var ref4;
          if (typeof Inspector !== "undefined" && Inspector !== null ? (ref4 = Inspector.instance) != null ? ref4.tutorial : void 0 : void 0) {
            return false;
          }
          if (cache['showIDs'] != null) {
            return cache['showIDs'];
          }
          return cache['showIDs'] = 'false' !== imt.localStorage.getItem('config:showIDs');
        },
        set: function(value) {
          if (value == null) {
            value = false;
          }
          cache['showIDs'] = value;
          return imt.localStorage.setItem('config:showIDs', JSON.stringify(value));
        }
      }
    });
  })();

  CONTEXT_MENU = null;

  CONTEXT_MENU_OFFSET = 5;

  CONTEXT_MENU_MARGIN = 10;

  global.ContextMenu = (function(superClass) {
    extend1(ContextMenu, superClass);

    function ContextMenu(menu, x, y) {
      var self;
      ContextMenu.__super__.constructor.call(this, 'div');
      if (CONTEXT_MENU != null) {
        CONTEXT_MENU.destroy();
      }
      self = CONTEXT_MENU = this;
      this.addClass('i-contextmenu');
      this.appendTo(document.body);
      this.on('mouseup', function(event) {
        if (event.which === 3) {
          return;
        }
        if (!self.contains(event.target)) {
          return self.destroy();
        }
      });
      menu = sim.ul('.list-unstyled', function() {
        var fn2, len4, z;
        fn2 = (function(_this) {
          return function(item) {
            return _this.li(function() {
              if (item["default"] === true) {
                this.addClass('i-contextmenu-default');
              }
              return this.a(function() {
                this.attr('href', '#');
                this.text(item.label);
                this.on('click', function(event) {
                  event.preventDefault();
                  event.stopPropagation();
                  self.destroy();
                  if (typeof item.click === "function") {
                    item.click();
                  }
                  return false;
                });
                if (item.icon) {
                  return this.prepend(sim.i(".far.fa-fw.fa-" + item.icon));
                }
              });
            });
          };
        })(this);
        for (z = 0, len4 = menu.length; z < len4; z++) {
          item = menu[z];
          fn2(item);
        }
        return null;
      });
      this.append(menu);
      x += CONTEXT_MENU_OFFSET;
      y += CONTEXT_MENU_OFFSET;
      if (x + menu.outerWidth() + CONTEXT_MENU_MARGIN > sim(window).width()) {
        x = sim(window).width() - menu.outerWidth() - CONTEXT_MENU_MARGIN;
      }
      if (y + menu.outerHeight() + CONTEXT_MENU_MARGIN > sim(window).height()) {
        y = sim(window).height() - menu.outerHeight() - CONTEXT_MENU_MARGIN;
      }
      menu.css({
        left: x,
        top: y
      });
      setImmediate((function(_this) {
        return function() {
          return _this.addClass('in');
        };
      })(this));
    }

    ContextMenu.prototype.destroy = function() {
      CONTEXT_MENU = null;
      this.emit('destroy');
      this.remove();
      return this;
    };

    return ContextMenu;

  })(SIMElement);

  (function() {
    var ref4, store;
    if (browser.simulator) {
      return imt.debug = node.require('debug');
    }
    store = null;
    imt.debug = function(section, color) {
      return function() {
        var args, text;
        args = 1 <= arguments.length ? slice.call(arguments, 0) : [];
        if (!store[section]) {
          return;
        }
        text = ((function() {
          var ref4, results;
          results = [];
          while ((ref4 = typeof args[0]) === 'string' || ref4 === 'number' || ref4 === 'boolean') {
            results.push(args.shift());
          }
          return results;
        })());
        text.unshift("%c[" + section + "]");
        args.unshift("color: " + color);
        args.unshift(text.join(' '));
        return console.log.apply(console, args);
      };
    };
    imt.debug.enable = function(section) {
      store[section] = true;
      return imt.localStorage.setItem('config:debug', JSON.stringify(store));
    };
    imt.debug.disable = function(section) {
      delete store[section];
      return imt.localStorage.setItem('config:debug', JSON.stringify(store));
    };
    imt.debug.isEnabled = function(section) {
      return store[section] === true;
    };
    imt.debug.help = function() {
      var key, results, value;
      results = [];
      for (key in store) {
        value = store[key];
        results.push(console.log("- " + key));
      }
      return results;
    };
    return store = JSON.parse((ref4 = imt.localStorage.getItem('config:debug')) != null ? ref4 : '{}');
  })();

  global.Dictionary = (function() {
    Dictionary.prototype._map = null;

    function Dictionary(name1, mutation1) {
      this.name = name1;
      this.mutation = mutation1;
      this._map = {};
    }

    Dictionary.prototype.l = function(key, options) {
      var index, n, ref4, text;
      text = this._map[key];
      if (text != null) {
        if (Array.isArray(text)) {
          n = parseInt(options != null ? (ref4 = options.data) != null ? ref4.n : void 0 : void 0);
          if (n === 0) {
            index = 0;
          } else if (n === 1) {
            index = 1;
          } else if (n === 2 || n === 3 || n === 4) {
            index = 2;
          } else {
            index = 3;
          }
          if (text[index] == null) {
            console.warn("Keyword '" + key + "[" + index + "]' was not found in dictionary '" + this.name + "'.");
            return "##" + key + "[" + index + "]";
          }
          text = text[index];
        }
        if (options != null ? options.data : void 0) {
          text = text.format(options.data);
        }
      } else if (options != null ? options.optional : void 0) {
        return void 0;
      } else {
        console.warn("Keyword '" + key + "' was not found in dictionary '" + this.name + "'.");
        return "##" + key;
      }
      return text;
    };

    Dictionary.create = function(document, mutation, data) {
      var base, dict, iterate;
      if ((base = imt.dictionaries)[document] == null) {
        base[document] = {};
      }
      imt.dictionaries[document][mutation] = dict = new Dictionary(document, mutation);
      iterate = function(level, prefix) {
        var key, results, value;
        results = [];
        for (key in level) {
          value = level[key];
          if (typeof value === 'object' && !Array.isArray(value)) {
            results.push(iterate(value, "" + prefix + key + "."));
          } else {
            results.push(dict._map["" + prefix + key] = value);
          }
        }
        return results;
      };
      iterate(data, '');
      return null;
    };

    return Dictionary;

  })();

  global.Flash = (function(superClass) {
    extend1(Flash, superClass);

    Flash.active = [];

    function Flash(text, icon, permanent, closeable) {
      var button, link, ref4, self, severity, title;
      if ('object' === typeof text) {
        ref4 = text, text = ref4.text, icon = ref4.icon, permanent = ref4.permanent, closeable = ref4.closeable, severity = ref4.severity, link = ref4.link, button = ref4.button, title = ref4.title;
      }
      Flash.__super__.constructor.call(this, 'div');
      this.addClass('i-flash');
      self = this;
      Flash.add(this);
      if (severity === 'error') {
        this.addClass('i-flash-red');
        if (icon == null) {
          icon = '.far.fa-exclamation-triangle';
        }
      } else {
        if (icon == null) {
          icon = '.far.fa-check-square';
        }
      }
      if (link) {
        this.addClass('i-flash-clickable');
        this.on('click', (function(_this) {
          return function(event) {
            event.stopPropagation();
            _this.hide();
            if (!window.open(link, '_blank')) {
              return window.location.href = link;
            }
          };
        })(this));
      }
      this.div('.i-flash-icon').i(icon).addClass('fa-fw i-flash-icon');
      this.div('.i-flash-body', function() {
        if (title) {
          this.h4().text(title);
        }
        this.p().text(text);
        if (button) {
          return this.a('.btn.btn-outline-light', function() {
            this.text(button.text);
            return this.on('click', function(event) {
              event.stopPropagation();
              self.hide();
              if (!window.open(button.link, '_blank')) {
                return window.location.href = button.link;
              }
            });
          });
        }
      });
      this.css('display', 'none').appendTo(document.body).fadeIn('slow');
      if (!permanent) {
        delay(3000, (function(_this) {
          return function() {
            return _this.hide();
          };
        })(this));
      } else if (closeable) {
        this.div().button('.close').on('click', (function(_this) {
          return function(event) {
            event.stopPropagation();
            return _this.hide();
          };
        })(this));
      }
      Flash.recalc();
    }

    Flash.prototype.close = function() {
      return this.hide();
    };

    Flash.prototype.hide = function() {
      return this.fadeOut('slow', (function(_this) {
        return function() {
          _this.remove();
          _this.emit('close');
          Flash.remove(_this);
          return Flash.recalc();
        };
      })(this));
    };

    Flash.add = function(elm, clue) {
      if (clue) {
        return Flash.active.unshift(elm);
      }
      return Flash.active.push(elm);
    };

    Flash.remove = function(elm) {
      return Flash.active.remove(elm);
    };

    Flash.recalc = function() {
      var flash, len4, ref4, y, z;
      y = 50;
      ref4 = Flash.active;
      for (z = 0, len4 = ref4.length; z < len4; z++) {
        flash = ref4[z];
        flash.css('bottom', y + "px");
        y += flash.outerHeight() + 10;
      }
      return null;
    };

    return Flash;

  })(SIMElement);

  (function() {
    var formatBytes, formatDuration, resolveType;
    resolveType = function(data) {
      if (typeof data === 'object') {
        if (data instanceof Date) {
          return 'datetime';
        }
      } else if (typeof data === 'number') {
        return 'number';
      }
      return null;
    };
    formatBytes = function(bytes) {
      var i, sizes;
      if ((bytes == null) || isNaN(bytes)) {
        return '0';
      }
      sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
      if (bytes === 0) {
        return '0';
      }
      i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
      return ((bytes / Math.pow(1024, i)).toFixed(1)) + " " + sizes[i];
    };
    formatDuration = function(milliseconds, spacer) {
      var d, h, m, o, s, seconds;
      if (spacer == null) {
        spacer = ' ';
      }
      seconds = milliseconds / 1000;
      if (seconds < 1) {
        return imt.l('base', 'time.lts');
      }
      o = [];
      d = Math.floor(seconds / 86400);
      h = Math.floor((seconds % 86400) / 3600);
      m = Math.floor((seconds % 3600) / 60);
      s = Math.floor(seconds % 60);
      if (d) {
        o.push(imt.l('base', 'time.days', {
          data: {
            n: d
          }
        }));
        if (h) {
          o.push(imt.l('base', 'time.hours', {
            data: {
              n: h
            }
          }));
        }
      } else if (h) {
        o.push(imt.l('base', 'time.hours', {
          data: {
            n: h
          }
        }));
        if (m) {
          o.push(imt.l('base', 'time.minutes', {
            data: {
              n: m
            }
          }));
        }
      } else if (m) {
        o.push(imt.l('base', 'time.minutes', {
          data: {
            n: m
          }
        }));
      } else if (s) {
        o.push(imt.l('base', 'time.seconds', {
          data: {
            n: s
          }
        }));
      }
      return o.join(spacer);
    };
    return global.format = function(data, type, options) {
      var codes, m, ref4, ref5, ref6;
      if (options == null) {
        options = {};
      }
      if (type == null) {
        type = resolveType(data);
      }
      switch (type) {
        case 'date':
          if (!data) {
            return '';
          }
          m = moment.tz(data, 'UTC');
          if (options.timezone) {
            m.tz(options.timezone);
          } else {
            m.local();
          }
          return m.format((ref4 = options.format) != null ? ref4 : 'LL');
        case 'datetime':
          if (!data) {
            return '';
          }
          m = moment.tz(data, 'UTC');
          if (options.timezone) {
            m.tz(options.timezone);
          } else {
            m.local();
          }
          return m.format((ref5 = options.format) != null ? ref5 : 'LLL');
        case 'time':
          m = moment(data, 'HH:mm');
          return m.format((ref6 = options.format) != null ? ref6 : 'LT');
        case 'byte':
        case 'bytes':
          return formatBytes(parseInt(data));
        case 'duration':
          if (options.precise) {
            return (parseInt(data)) + " ms";
          } else {
            return formatDuration(parseInt(data), options.spacer);
          }
          break;
        case 'number':
          return Number(data).toLocaleString();
        case 'progress':
          return (Math.max(0, Math.min(100, Math.round(data * 100)))) + "%";
        case 'currency':
          return Number(data).toLocaleString(imt.user.language, {
            style: 'currency',
            currency: 'string' === typeof options ? options : options.currency,
            currencyDisplay: 'symbol'
          });
        case 'markdown':
          codes = [];
          return escapeHtml(data).replace(/\{\{l:([^@]+)@([^\}]+)\}\}/g, function(a, b, c) {
            return imt.l(c, b);
          }).replace(/\[([^\]]*)\]\(([^\)]*)\)/g, function(a, b, c) {
            c = c.replace(/_/g, '%5f');
            if (/^kb:\/\/(.*)$/i.test(c)) {
              c = "/" + imt.user.language + "/kb/" + RegExp.$1;
              return "<a target=\"_blank\" class=\"i-open-help\" href=\"" + c + "\">" + b + "</a>";
            } else {
              return "<a target=\"_blank\" href=\"" + c + "\">" + b + "</a>";
            }
          }).replace(/`([^`]+)`/g, function(a, b) {
            codes.push("<code>" + b + "</code>");
            return "{{code:" + (codes.length - 1) + "}}";
          }).replace(/__([^_]+)__/g, function(a, b) {
            return "<strong>" + b + "</strong>";
          }).replace(/_([^_]+)_/g, function(a, b) {
            return "<em>" + b + "</em>";
          }).replace(/\*\*([^\*]+)\*\*/g, function(a, b) {
            return "<strong>" + b + "</strong>";
          }).replace(/\*([^\*]+)\*/g, function(a, b) {
            return "<em>" + b + "</em>";
          }).replace(/\n/g, function(a, b) {
            return "<br>";
          }).replace(/\{\{code:(\d+)\}\}/g, function(a, b) {
            return codes[b];
          });
        case 'countdown':
          return format(Math.max(0, data - Date.now()), 'duration', options);
        case 'scheduling':
          switch (data.type) {
            case 'immediately':
              return imt.l('base', 'scheduling.immediately');
            case 'indefinitely':
              return imt.l('base', 'scheduling.indefinitely', {
                data: {
                  interval: format(data.interval * 1000, 'duration')
                }
              });
            case 'once':
              return imt.l('base', 'scheduling.once', {
                data: {
                  date: format(data.date, 'datetime')
                }
              });
            case 'daily':
              return imt.l('base', 'scheduling.daily', {
                data: {
                  time: format(data.time, 'time', {
                    timezone: imt.user.timezone
                  })
                }
              });
            case 'weekly':
              return imt.l('base', 'scheduling.weekly', {
                data: {
                  daysofweek: data.days.map(function(day) {
                    return moment.weekdays(day);
                  }).join(', '),
                  time: format(data.time, 'time', {
                    timezone: imt.user.timezone
                  })
                }
              });
            case 'monthly':
              return imt.l('base', 'scheduling.monthly', {
                data: {
                  days: data.days.map(function(day) {
                    return day + ".";
                  }).join(', '),
                  time: format(data.time, 'time', {
                    timezone: imt.user.timezone
                  })
                }
              });
            case 'yearly':
              return imt.l('base', 'scheduling.yearly', {
                data: {
                  days: data.days.map(function(day) {
                    return day + ".";
                  }).join(', '),
                  months: data.months.map(function(month) {
                    return moment.months(month - 1);
                  }).join(', '),
                  time: format(data.time, 'time', {
                    timezone: imt.user.timezone
                  })
                }
              });
            default:
              return '';
          }
          break;
        default:
          return data;
      }
    };
  })();

  global.Point = (function() {
    function Point(x1, y1) {
      this.x = x1 != null ? x1 : 0;
      this.y = y1 != null ? y1 : 0;
    }

    Point.prototype.distance = function(point) {
      return Math.sqrt(Math.pow(this.x - point.x, 2) + Math.pow(this.y - point.y, 2));
    };

    Point.prototype.negative = function() {
      this.x *= -1;
      this.y *= -1;
      return this;
    };


    /*
    	Transform point by provided matrix. Returns itself.
    	
    	@param {Matrix} matrix Matrix.
    	@returns Point
     */

    Point.prototype.transform = function(matrix) {
      var x, y;
      if (!(matrix instanceof Matrix)) {
        throw new TypeError('Matrix expected.');
      }
      x = this.x * matrix._matrix[0][0] + this.y * matrix._matrix[0][1] + matrix._matrix[0][2];
      y = this.x * matrix._matrix[1][0] + this.y * matrix._matrix[1][1] + matrix._matrix[1][2];
      this.x = x;
      this.y = y;
      return this;
    };

    Point.prototype.translate = function(x, y) {
      if (x == null) {
        x = 0;
      }
      if (y == null) {
        y = 0;
      }
      if (x instanceof Point) {
        this.x += x.x;
        this.y += x.y;
      } else {
        this.x += x;
        this.y += y;
      }
      return this;
    };

    return Point;

  })();

  global.Rectangle = (function() {
    Rectangle.prototype.x = 0;

    Rectangle.prototype.y = 0;

    Rectangle.prototype.width = 0;

    Rectangle.prototype.height = 0;

    function Rectangle(x1, y1, width1, height1) {
      this.x = x1 != null ? x1 : 0;
      this.y = y1 != null ? y1 : 0;
      this.width = width1 != null ? width1 : 0;
      this.height = height1 != null ? height1 : 0;
    }

    Rectangle.prototype.contains = function(point) {
      if (!(point instanceof Point)) {
        throw new TypeError('Point expected.');
      }
      return this.x < point.x && (this.x + this.width) > point.x && this.y < point.y && (this.y + this.height) > point.y;
    };

    Rectangle.property('center', {
      get: function() {
        return new Point(this.x + (this.width / 2), this.y + (this.height / 2));
      }
    });


    /*
    	Inflate rectangle with given Point or Rectangle.
    	
    	@param {Point|Rectangle} item Point or Rectangle.
     */

    Rectangle.prototype.inflate = function(item) {
      if (item instanceof Rectangle) {
        this.inflate(new Point(item.x, item.y));
        this.inflate(new Point(item.x + item.width, item.y + item.height));
      } else if (item instanceof Point) {
        if (item.x < this.x) {
          this.width += this.x - item.x;
          this.x = item.x;
        }
        if (item.y < this.y) {
          this.height += this.y - item.y;
          this.y = item.y;
        }
        this.width = Math.max(this.x + this.width, item.x) - this.x;
        this.height = Math.max(this.y + this.height, item.y) - this.y;
      } else {
        throw new TypeError('Point or Rectangle expected.');
      }
      return this;
    };

    Rectangle.prototype.intersect = function(rect) {
      if (!(rect instanceof Rectangle)) {
        throw new TypeError('Rectangle expected.');
      }
      if (rect.x < this.x + this.width && this.x < rect.x + rect.width && rect.y < this.y + this.height) {
        return this.y < rect.y + rect.height;
      }
      return false;
    };

    Rectangle.prototype.scale = function(scale) {
      if (scale == null) {
        scale = 1;
      }
      this.x *= scale;
      this.y *= scale;
      this.width *= scale;
      this.height *= scale;
      return this;
    };

    Rectangle.prototype.toString = function() {
      return "{x: " + (this.x.toFixed(0)) + ", y: " + (this.y.toFixed(0)) + ", width: " + (this.width.toFixed(0)) + ", height: " + (this.height.toFixed(0)) + "}";
    };

    Rectangle.prototype.translate = function(x, y) {
      if (x == null) {
        x = 0;
      }
      if (y == null) {
        y = 0;
      }
      if (x instanceof Point) {
        this.x += x.x;
        this.y += x.y;
      } else {
        this.x += x;
        this.y += y;
      }
      return this;
    };

    return Rectangle;

  })();


  /*
  The Matrix class represents a transformation matrix that determines how to map points from one coordinate space to another. You can perform various graphical transformations on a <code>Context</code> object by providing matrix object to <code>transform</code> method. These transformation functions include translation (x and y repositioning), rotation, scaling, and skewing.
  
  @property {Number} a The value that affects the positioning of pixels along the x axis when scaling or rotating an image.
  @property {Number} b The value that affects the positioning of pixels along the y axis when rotating or skewing an image.
  @property {Number} c The value that affects the positioning of pixels along the x axis when rotating or skewing an image.
  @property {Number} d The value that affects the positioning of pixels along the y axis when scaling or rotating an image.
  @property {Number} tx The distance by which to translate each point along the x axis.
  @property {Number} ty The distance by which to translate each point along the y axis.
  @property {Boolean} isIdentity Return <code>true</code> if matrix values are: a=1, b=0, c=0, d=1, tx=0, ty=0.
   */

  global.Matrix = (function() {
    Matrix.prototype._matrix = null;

    Matrix.property('width', {
      get: function() {
        var ref4, ref5;
        return (ref4 = (ref5 = this._matrix) != null ? ref5[0].length : void 0) != null ? ref4 : 0;
      }
    });

    Matrix.property('height', {
      get: function() {
        var ref4;
        return (ref4 = this._matrix) != null ? ref4.length : void 0;
      }
    });

    Matrix.property('a', {
      get: function() {
        var ref4, ref5;
        return (ref4 = this._matrix) != null ? (ref5 = ref4[0]) != null ? ref5[0] : void 0 : void 0;
      }
    });

    Matrix.property('b', {
      get: function() {
        var ref4, ref5;
        return (ref4 = this._matrix) != null ? (ref5 = ref4[1]) != null ? ref5[0] : void 0 : void 0;
      }
    });

    Matrix.property('c', {
      get: function() {
        var ref4, ref5;
        return (ref4 = this._matrix) != null ? (ref5 = ref4[0]) != null ? ref5[1] : void 0 : void 0;
      }
    });

    Matrix.property('d', {
      get: function() {
        var ref4, ref5;
        return (ref4 = this._matrix) != null ? (ref5 = ref4[1]) != null ? ref5[1] : void 0 : void 0;
      }
    });

    Matrix.property('tx', {
      get: function() {
        var ref4, ref5;
        return (ref4 = this._matrix) != null ? (ref5 = ref4[0]) != null ? ref5[2] : void 0 : void 0;
      }
    });

    Matrix.property('ty', {
      get: function() {
        var ref4, ref5;
        return (ref4 = this._matrix) != null ? (ref5 = ref4[1]) != null ? ref5[2] : void 0 : void 0;
      }
    });

    Matrix.property('isIdentity', {
      get: function() {
        return this.a === 1 && this.b === 0 && this.c === 0 && this.d === 1 && this.tx === 0 && this.ty === 0;
      }
    });


    /*
    	@param {Number} a The value that affects the positioning of pixels along the x axis when scaling or rotating an image.
    	@param {Number} b The value that affects the positioning of pixels along the y axis when rotating or skewing an image.
    	@param {Number} c The value that affects the positioning of pixels along the x axis when rotating or skewing an image.
    	@param {Number} d The value that affects the positioning of pixels along the y axis when scaling or rotating an image.
    	@param {Number} tx The distance by which to translate each point along the x axis.
    	@param {Number} ty The distance by which to translate each point along the y axis.
    	
    	Creates a new Matrix object with the specified parameters. If you do not provide any parameters to the new Matrix() constructor, it creates an identity matrix with the following values: a=1, b=0, c=0, d=1, tx=0, ty=0.
     */

    function Matrix(a, b, c, d, tx, ty) {
      if (a == null) {
        a = 1;
      }
      if (b == null) {
        b = 0;
      }
      if (c == null) {
        c = 0;
      }
      if (d == null) {
        d = 1;
      }
      if (tx == null) {
        tx = 0;
      }
      if (ty == null) {
        ty = 0;
      }
      if (a instanceof Array) {
        this._matrix = a;
      } else {
        this._matrix = [[a, c, tx], [b, d, ty], [0, 0, 1]];
      }
    }

    Matrix.prototype.clone = function() {

      /*
      		Returns a new Matrix object that is a clone of this matrix, with an exact copy of the contained object.
      		
      		@returns Matrix
       */
      return new Matrix(this.a, this.b, this.c, this.d, this.tx, this.ty);
    };


    /*
    	Concatenates a matrix with the current matrix, effectively combining the geometric effects of the two. In mathematical terms, concatenating two matrixes is the same as combining them using matrix multiplication.
    
    	For example, if matrix m1 scales an object by a factor of four, and matrix m2 rotates an object by 1.5707963267949 radians (Math.PI/2), then m1.concat(m2) transforms m1 into a matrix that scales an object by a factor of four and rotates the object by Math.PI/2 radians.
    	
    	This method replaces the source matrix with the concatenated matrix. If you want to concatenate two matrixes without altering either of the two source matrixes, first copy the source matrix by using the clone() method.
    	
    	@param {Matrix} The matrix to be concatenated to the source matrix.
    	@returns Matrix
     */

    Matrix.prototype.concat = function(matrix) {
      var i, j, k, result, sum;
      result = [];
      i = 0;
      while (i < this.height) {
        result[i] = [];
        j = 0;
        while (j < matrix.width) {
          sum = 0;
          k = 0;
          while (k < this.width) {
            sum += this._matrix[i][k] * matrix.matrix[k][j];
            k++;
          }
          result[i][j] = sum;
          j++;
        }
        i++;
      }
      this._matrix = result;
      return this;
    };


    /*
    	Sets each matrix property to a value that causes a null transformation. An object transformed by applying an identity matrix will be identical to the original.
    
    	After calling the identity() method, the resulting matrix has the following properties: a=1, b=0, c=0, d=1, tx=0, ty=0.
    	
    	@return Matrix
     */

    Matrix.prototype.identity = function() {
      this._matrix = [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
      return this;
    };


    /*
    	Performs the opposite transformation of the original matrix. You can apply an inverted matrix to an object to undo the transformation performed when applying the original matrix.
     */

    Matrix.prototype.invert = function() {
      var a, b, c, d, tx, ty;
      a = this.a;
      b = this.b;
      c = this.c;
      d = this.d;
      tx = this.tx;
      ty = this.ty;
      if (a !== 0) {
        a = 1 / a;
      }
      if (b !== 0) {
        b = 1 / b;
      }
      if (c !== 0) {
        c = 1 / c;
      }
      if (d !== 0) {
        d = 1 / d;
      }
      if (tx !== 0) {
        tx = -tx;
      }
      if (ty !== 0) {
        ty = -ty;
      }
      this._matrix = [[a, c, tx], [b, d, ty], [0, 0, 1]];
      return this;
    };


    /*
    	Applies a rotation transformation to the Matrix object.
    	
    	@param {Number} angle The rotation angle in radians.
    	@returns Matrix
     */

    Matrix.prototype.rotate = function(angle) {
      this._matrix = [[Math.cos(angle), Math.sin(angle), 0], [-Math.sin(angle), Math.cos(angle), 0], [0, 0, 1]];
      return this;
    };


    /*
    	Applies a scaling transformation to the matrix. The x axis is multiplied by sx, and the y axis it is multiplied by sy.
    	
    	@param {Number} sx A multiplier used to scale the object along the x axis.
    	@param {Number} [sy] A multiplier used to scale the object along the x axis.
    	@returns Matrix
     */

    Matrix.prototype.scale = function(sx, sy) {
      this._matrix = [[sx, 0, 0], [0, sy != null ? sy : sx, 0], [0, 0, 1]];
      return this;
    };

    Matrix.prototype.translate = function(dx, dy) {

      /*
      		Translates the matrix along the x and y axes, as specified by the dx and dy parameters.
      		
      		@param {Number} dx The amount of movement along the x axis to the right, in pixels.
      		@param {Number} dy The amount of movement down along the y axis, in pixels.
      		@returns Matrix
       */
      this._matrix = [[1, 0, dx], [0, 1, dy], [0, 0, 1]];
      return this;
    };

    return Matrix;

  })();

  LOADER_STORE = {};

  PARSERS = {
    manifest: function(key, value, headers) {
      var mdl, pkg, ver;
      if (/^rpc:\/\/(?:([^\/@]*)(?:@(\d+))?\/)?([^\/]+)$/.exec(value)) {
        pkg = RegExp.$1;
        ver = RegExp.$2;
        mdl = RegExp.$3;
        value = "rpc://" + (pkg || encodeURIComponent(headers['package-name'])) + "@" + (ver || headers['package-version']) + "/" + mdl;
      }
      return value;
    }
  };


  /*
  Loader
  
  Options:
  - `method` - HTTP method. Default is based on type of loader method.
  - `parser` - Function to call as second argument to JSON.parse
   */

  global.Loader = (function() {
    function Loader() {}


    /*
    	Raw ajax request.
    	
    	@param {String} url URL address.
    	@param {Object} [options] Request options.
    	@callback callback Callback to call when request is complete.
    		@param {Error} err Error on error, otherwise null.
     */

    Loader.ajax = function(url, options, callback) {
      var queue, ref4, ref5, ref6, ref7;
      if (url == null) {
        setImmediate(function() {
          return callback(new Error("Loader: Can't load empty URL."));
        });
      }
      if (options instanceof Function) {
        callback = options;
        options = {};
      }
      if (options.store != null) {
        queue = [callback];
        if (LOADER_STORE[options.store]) {
          if (LOADER_STORE[options.store].loaded) {
            setImmediate(function() {
              return callback(null, LOADER_STORE[options.store].data, LOADER_STORE[options.store].headers);
            });
          } else {
            LOADER_STORE[options.store].queue.push(callback);
          }
          return;
        }
        LOADER_STORE[options.store] = {
          loaded: false,
          queue: queue
        };
      }
      if (options.method == null) {
        options.method = 'GET';
      }
      if ((ref4 = options.method) === 'POST' || ref4 === 'DELETE') {
        if (options.data instanceof FormData) {
          options.contentType = false;
        } else {
          if (options.contentType == null) {
            options.contentType = 'application/json; charset=utf-8';
          }
        }
      } else {
        options.contentType = void 0;
      }
      return sim.ajax({
        url: url,
        async: (ref5 = options.async) != null ? ref5 : true,
        type: options.method,
        data: options.data,
        processData: !(options.data instanceof FormData),
        dataType: options.parser ? 'text' : (ref6 = options.dataType) != null ? ref6 : 'json',
        contentType: options.contentType,
        cache: (ref7 = options.cache) != null ? ref7 : false,
        headers: options.headers,
        success: function(data, status, xhr) {
          var hdrs, headers, len4, match, method, re, results, z;
          headers = {};
          hdrs = xhr.getAllResponseHeaders();
          re = /^x\-imt\-([^:]*):\s*(.*)/gm;
          while (match = re.exec(hdrs)) {
            headers[match[1]] = match[2];
          }
          if (options.parser) {
            if ('string' === typeof options.parser) {
              options.parser = PARSERS[options.parser];
            }
            if ('function' === typeof options.parser) {
              data = JSON.parse(data, function(key, value) {
                return options.parser(key, value, headers);
              });
            }
          }
          if (options.postProcess != null) {
            data = options.postProcess(data);
          }
          if (options.store != null) {
            LOADER_STORE[options.store] = {
              loaded: true,
              data: data,
              headers: headers
            };
            results = [];
            for (z = 0, len4 = queue.length; z < len4; z++) {
              method = queue[z];
              results.push(method(null, data, headers));
            }
            return results;
          } else {
            return callback(null, data, headers);
          }
        },
        error: function(xhr, status, err) {
          var len4, method, results, z;
          err = new Error("Connection error. " + err);
          if (options.store != null) {
            delete LOADER_STORE[options.store];
            results = [];
            for (z = 0, len4 = queue.length; z < len4; z++) {
              method = queue[z];
              results.push(method(err));
            }
            return results;
          } else {
            return callback(err);
          }
        }
      });
    };

    Loader.api = function(source, options, callback) {
      var base, done;
      if (options instanceof Function) {
        callback = options;
        options = {};
      }
      done = function(err, data, headers) {
        var args, e, entry, i1, len4, len5, ref4, ref5, z;
        if (err) {
          return callback(err);
        }
        if (Array.isArray(data.debug)) {
          ref4 = data.debug;
          for (z = 0, len4 = ref4.length; z < len4; z++) {
            entry = ref4[z];
            if (typeof IMTDevTool !== "undefined" && IMTDevTool !== null ? IMTDevTool.connected : void 0) {
              IMTDevTool.pushLiveStreamEvent(entry);
            }
            if (!(typeof IMTDevTool !== "undefined" && IMTDevTool !== null ? IMTDevTool.connected : void 0) || IMTDevTool.settings.console) {
              console.log.apply(console, ["%c[rpc:debug]", "color: #a4a9ae"].concat(slice.call(entry)));
            }
          }
        }
        if (Array.isArray(data.log)) {
          ref5 = data.log;
          for (i1 = 0, len5 = ref5.length; i1 < len5; i1++) {
            entry = ref5[i1];
            if (typeof IMTDevTool !== "undefined" && IMTDevTool !== null ? IMTDevTool.connected : void 0) {
              IMTDevTool.pushLiveStreamEvent(entry);
            }
            if (!(typeof IMTDevTool !== "undefined" && IMTDevTool !== null ? IMTDevTool.connected : void 0) || IMTDevTool.settings.console) {
              console.log("[rpc:log] " + entry);
            }
          }
        }
        if (data.code === 'OK') {
          args = [null];
          if (headers['multiple-results'] === 'yes') {
            args = args.concat(data.response);
          } else {
            args.push(data.response);
          }
          args.push(headers);
          args.push(data.metadata);
          return callback.apply(null, args);
        } else {
          e = new Error(data.message);
          e.name = data.name;
          e.code = data.code;
          if (data.stack != null) {
            e.stack = data.stack;
          }
          if (data.suberrors != null) {
            e.errors = data.suberrors;
          }
          if (data.prompt != null) {
            e.prompt = data.prompt;
          }
          return callback(e);
        }
      };
      if (options.headers == null) {
        options.headers = {};
      }
      if ((base = options.headers)['x-imt-language'] == null) {
        base['x-imt-language'] = imt.user.language;
      }
      if (options.data instanceof FormData) {
        return this.ajax("/api/" + source, options, done);
      } else {
        return this.json("/api/" + source, options, done);
      }
    };

    Loader.imt = function(source, options, callback) {
      if (options instanceof Function) {
        callback = options;
        options = {};
      }
      return this.json("/imt/" + imt.user.language + "/" + (source === '/' ? '' : source), options, function(err, data, headers) {
        var e;
        if (err) {
          return callback(err);
        }
        if (data.code === 'OK') {
          return callback(null, data.response, headers);
        } else {
          e = new Error(data.message);
          e.name = data.name;
          e.code = data.code;
          if (data.stack != null) {
            e.stack = data.stack;
          }
          return callback(e);
        }
      });
    };

    Loader.iql = function(selector, options, callback) {
      var host, ref4;
      if (options instanceof Function) {
        callback = options;
        options = {};
      }
      options.method = 'POST';
      options.dataType = 'json';
      options.contentType = 'text/iql';
      options.data = selector;
      if (options.headers == null) {
        options.headers = {};
      }
      options.headers['accept-language'] = imt.user.language;
      if (options.indexes) {
        options.headers['x-imt-iql-indexes'] = options.indexes;
      }
      host = window.location.hostname.split('.');
      if ((ref4 = host[0]) === 'www' || ref4 === 'admin') {
        host.shift();
      }
      host.unshift('iql');
      return this.ajax("//" + (host.join('.')) + "/query", options, callback);
    };

    Loader.rpc = function(source, options, callback) {
      var cur, data, key, len4, param, params, qs, ref4, ref5, ref6, ref7, value, z;
      if (options instanceof Function) {
        callback = options;
        options = {};
      }
      if ((!options.method || options.method === 'GET') && ((ref4 = options.headers) != null ? ref4['x-imt-remote-formula'] : void 0) === 'yes') {
        options.method = 'OPTIONS';
      }
      if (options.method !== 'OPTIONS') {
        options.method = 'POST';
      }
      data = (ref5 = options.data) != null ? ref5 : {};
      cur = source.indexOf('?');
      if (cur !== -1) {
        try {
          params = {};
          ref6 = source.match(/(\?|\&)[^\&\#\=]+=[^\&\#]+/g);
          for (z = 0, len4 = ref6.length; z < len4; z++) {
            param = ref6[z];
            qs = /^[\?\&]([^=]+)=(.*)$/g.exec(param);
            if (params[qs[1]] != null) {
              if (!Array.isArray(params[qs[1]])) {
                params[qs[1]] = [params[qs[1]]];
              }
              params[qs[1]].push(qs[2]);
            } else {
              params[qs[1]] = qs[2];
            }
          }
          for (key in params) {
            value = params[key];
            if (((ref7 = options.headers) != null ? ref7['x-imt-validate-schema'] : void 0) === 'yes') {
              data.data[key] = value;
              data.schema.push({
                name: key,
                type: 'text'
              });
            } else {
              data[key] = value;
            }
          }
        } catch (error) {
          ex = error;
          console.warn("Failed to parse query string to post data.");
        }
        source = source.substr(0, cur);
      }
      options.data = data;
      if (options.headers == null) {
        options.headers = {};
      }
      return this.api("rpc/" + source, options, callback);
    };


    /*
    	It is possible to call method with `options.store = 'key'` to save results to internal store. If the method is called again with same `store` key, result will be returned from internal store no matter if url or data has changed. If there will be call with `store` key during the loading process, it will be queued and result will propagate to all callbacks.
     */

    Loader.json = function(source, options, callback) {
      var ref4, ref5;
      if (options instanceof Function) {
        callback = options;
        options = {};
      }
      if ((ref4 = options.method) === 'POST' || ref4 === 'DELETE') {
        options.data = JSON.stringify(options.data);
      }
      options.dataType = 'json';
      options.contentType = (ref5 = options.method) === 'POST' || ref5 === 'DELETE' ? "application/json; charset=utf-8" : null;
      return this.ajax(source, options, callback);
    };

    Loader.image = function(source, options, callback) {
      var image;
      if (options instanceof Function) {
        callback = options;
        options = {};
      }
      image = new global.Image();
      if (options.crossOrigin != null) {
        image.crossOrigin = options.crossOrigin;
      }
      image.onload = function() {
        return callback(null, image);
      };
      image.onerror = function() {
        return callback(new Error("Failed to load image '" + source + "'"));
      };
      return image.src = source;
    };

    Loader.load = function(source, options, callback) {
      if (options instanceof Function) {
        callback = options;
        options = {};
      }
      if (/^api:\/\/(.*)$/i.exec(source)) {
        return this.api(RegExp.$1, options, callback);
      } else if (/^rpc:\/\/(.*)$/i.exec(source)) {
        return this.rpc(RegExp.$1, options, callback);
      } else if (/^iql:\/\/(.*)$/i.exec(source)) {
        return this.iql(RegExp.$1, options, callback);
      } else {
        return this.json(source, options, callback);
      }
    };

    Loader.font = function(name, text, size, callback) {
      var canvas, check, context, started, timer;
      canvas = document.createElement('canvas');
      context = canvas.getContext('2d');
      started = Date.now();
      context.font = "40px " + name;
      context.textAlign = 'left';
      context.textBaseline = "middle";
      check = function() {
        if (Math.round(context.measureText(text).width) === size) {
          clearInterval(timer);
          return callback(null);
        }
        if (Date.now() - started > 10000) {
          clearInterval(timer);
          console.warn(name, "got:", Math.round(context.measureText(text).width), "expect:", size);
          return callback(new Error("Font " + name + " failed to load in 10s."));
        }
      };
      timer = setInterval(check, 10);
      return check();
    };

    Loader.trace = function(event, payload, callback) {
      var options;
      options = {
        method: 'POST',
        data: {
          event_name: event,
          payload: payload
        }
      };
      return this.api('trace', options, callback);
    };

    return Loader;

  })();

  global.Alert = (function(superClass) {
    extend1(Alert, superClass);

    function Alert(message, title) {
      if (title == null) {
        title = 'Integromat';
      }
      Alert.__super__.constructor.call(this);
      this.message = message;
      this.title = title;
    }

    return Alert;

  })(Modal);

  sim(window).on('click', '.i-open-alert', function() {
    new Alert(this.data('message')).show();
    return false;
  });

  global.Prompt = (function(superClass) {
    extend1(Prompt, superClass);

    function Prompt(message, title) {
      if (title == null) {
        title = 'Integromat';
      }
      Prompt.__super__.constructor.call(this);
      this._yes = sim.button('.btn.btn-primary.btn-sm[type="button"][data-dismiss="modal"]').text(imt.l('base', 'common.yes'));
      this._close.text(imt.l('base', 'common.no'));
      this.message = message;
      this.title = title;
    }

    Prompt.prototype.show = function(callback) {
      var noClicked, yesClicked;
      yesClicked = false;
      noClicked = false;
      this._footer.append(this._yes);
      this._yes.once('click', function() {
        return yesClicked = true;
      });
      this._close.once('click', function() {
        return noClicked = true;
      });
      this.once('before-hide', (function(_this) {
        return function() {
          _this._yes.remove();
          if (yesClicked) {
            return callback(true);
          } else if (noClicked) {
            return callback(false);
          } else {
            return callback(null);
          }
        };
      })(this));
      return Prompt.__super__.show.call(this);
    };

    return Prompt;

  })(Modal);

  PANEL_PADDING = 10;

  PANEL_MARGIN = 10;

  PANEL_WIDTH = 400;

  PANEL_ONE = null;


  /*
  @event destroy
  @event close
  @event expand
  @event compress
  @event move
  @event load Emitted on some panels when it's content is loaded.
   */

  global.Panel = (function(superClass) {
    extend1(Panel, superClass);

    Panel.prototype.offsetX = 0;

    Panel.prototype.offsetY = 0;

    Panel.prototype._relative = null;

    Panel.prototype._loading = null;

    Panel.prototype._arrow = null;

    Panel.prototype._body = null;

    Panel.prototype._footer = null;

    Panel.prototype._savedWidth = null;

    Panel.prototype._status = null;

    Panel.prototype._bg = null;

    Panel.prototype._expanded = false;

    Panel.prototype._hidden = false;

    Panel.prototype._aside = null;

    Panel.prototype.__loading = false;

    Panel.prototype.__status = '';

    Panel.prototype.__modal = false;

    Panel.prototype.__expandable = false;

    Panel.prototype.__help = null;

    Panel.prototype.__closeable = true;

    Panel.prototype.__position = 'right';

    Panel.property('closeable', {
      get: function() {
        return this.__closeable;
      },
      set: function(value) {
        if (this.__closeable === value) {
          return;
        }
        this.__closeable = value;
        if (!value) {
          return this._header.children('.close').remove();
        }
      }
    });

    Panel.property('content', {
      get: function() {
        return this._body.children();
      },
      set: function(value) {
        var len4, z;
        this._body.contents().detach();
        if (value instanceof Array) {
          for (z = 0, len4 = value.length; z < len4; z++) {
            item = value[z];
            if (value != null) {
              if (item instanceof SIMElement) {
                this._body.append(item);
              } else {
                this._body.append(value);
              }
            }
          }
        } else if (value instanceof SIMElement) {
          this._body.append(value);
        } else {
          if (value != null) {
            this._body.append(value);
          }
        }
        return this._move();
      }
    });

    Panel.property('expandable', {
      get: function() {
        return this.__expandable;
      },
      set: function(value) {
        if (this.__expandable === value) {
          return;
        }
        return this.__expandable = value;
      }
    });

    Panel.property('gradient', {
      set: function(value) {
        return this._header.css('background', "linear-gradient(115deg, " + (value[0].toHex()) + " 0%, " + (value[1].toHex()) + " 100%)");
      }
    });

    Panel.property('help', {
      get: function() {
        return this.__help;
      },
      set: function(value) {
        if (/^kb:\/\/(.*)$/i.test(value)) {
          value = "/" + imt.user.language + "/kb/" + RegExp.$1;
        }
        return this.__help = value;
      }
    });

    Panel.property('loading', {
      get: function() {
        return this.__loading;
      },
      set: function(value) {
        var ref4, ref5, self;
        if (this.__loading === value) {
          return;
        }
        this.__loading = value;
        if (value) {
          self = this;
          this.addClass('cursor-progress');
          this._scroll.hide();
          this._header.hide();
          this._footer.hide();
          if ((ref4 = this._aside) != null) {
            ref4.hide();
          }
          this._savedWidth = this.outerWidth();
          this.width('auto');
          this._loading = sim.div('.i-loading', function() {
            this.i('.far.fa-circle-notch.fa-spin');
            this.appendTo(self);
            if (self._status) {
              return this.append(self._status);
            }
          });
        } else {
          this.removeClass('cursor-progress');
          this._scroll.show();
          this._header.show();
          this._footer.show();
          if ((ref5 = this._aside) != null) {
            ref5.show();
          }
          this.width(this._savedWidth);
          this._loading.remove();
          this._loading = null;
        }
        return this._move();
      }
    });

    Panel.property('modal', {
      get: function() {
        return this.__modal;
      },
      set: function(value) {
        var self;
        if (this.__modal === value) {
          return;
        }
        this.__modal = value;
        self = this;
        if (value) {
          this.addClass('i-panel-modal');
          return this._bg = sim.div('.i-panel-bg', function() {
            this.appendTo(document.body);
            this.append(self);
            return this.on('click', function(event) {
              event.stopPropagation();
              return false;
            });
          });
        } else {
          this.removeClass('i-panel-modal');
          self.appendTo(document.body);
          this._bg.remove();
          return this._bg = null;
        }
      }
    });

    Panel.property('position', {
      get: function() {
        return this.__position;
      },
      set: function(value) {
        if (this.__position === value) {
          return;
        }
        this.__position = value;
        return this._move();
      }
    });

    Panel.property('title', {
      get: function() {
        return this._header.find('h1').text();
      },
      set: function(value) {
        var self;
        this._header.empty();
        if (value != null) {
          self = this;
          this._header.h1().text(value);
          if (this.__expandable) {
            this._header.button('.expand', function() {
              this.attr('type', 'button');
              this.i('.far.fa-expand-arrows');
              return this.on('click', function() {
                return self._expand();
              });
            });
          }
          if (this.__help) {
            this._header.button('.help', function() {
              this.attr('type', 'button');
              this.i('.fas.fa-question');
              return this.on('click', function(event) {
                event.preventDefault();
                event.stopPropagation();
                sim(window).openHelp(self.__help);
                return false;
              });
            });
          }
          if (this.__closeable) {
            return this._header.button('.close', function() {
              this.attr('type', 'button');
              this.i('.far.fa-times');
              return this.on('click', function() {
                return self._close();
              });
            });
          }
        }
      }
    });

    Panel.property('status', {
      get: function() {
        return this.__status;
      },
      set: function(value) {
        var ref4;
        if (this.__status === value) {
          return;
        }
        this.__status = value;
        if (this._status) {
          return this._status.text(value);
        } else {
          this._status = sim.span().text(value);
          return (ref4 = this._loading) != null ? ref4.append(this._status) : void 0;
        }
      }
    });

    function Panel(_relative) {
      var ref10, ref4, ref5, ref6, ref7, ref8, ref9;
      this._relative = _relative;
      this._resize = bind(this._resize, this);
      this._move = bind(this._move, this);
      this._expand = bind(this._expand, this);
      this._close = bind(this._close, this);
      Panel.__super__.constructor.call(this, 'div');
      Panels.push(this);
      this.data('panel', this);
      this.addClass('i-panel');
      this._arrow = sim.div('.i-arrow');
      this._arrow.visible = this._relative != null;
      this.append(this._arrow);
      this._header = sim.div('.i-panel-header.gradient');
      this.append(this._header);
      this._scroll = sim.div('.i-panel-scroll');
      this.append(this._scroll);
      this._body = sim.div('.i-panel-body');
      this._scroll.append(this._body);
      this._footer = sim.div('.i-panel-footer');
      this.append(this._footer);
      this.css({
        width: PANEL_WIDTH + "px"
      });
      if (this._relative != null) {
        if ((typeof Surface !== "undefined" && Surface !== null) && this._relative instanceof Surface.DisplayObject) {
          this.appendTo(document.body);
          this._relative.on('move', this._move);
          this._relative.on('detach', this._close);
          this._relative.stage.on('move', this._move);
          this._relative.stage.surface.camera.on('zoom', this._move);
          if (this._relative.theme != null) {
            this._header.addClass("theme-" + (this._relative.theme.toHex().substr(1)));
          }
        } else {
          if (this._relative.closest('.modal')) {
            this.appendTo(this._relative.closest('.modal'));
          } else {
            this.appendTo(document.body);
          }
          if ((ref4 = this._relative.closest('.i-paper')) != null) {
            ref4.on('close', this._close);
          }
          if ((ref5 = this._relative.closest('.i-panel')) != null) {
            if ((ref6 = ref5.data('panel')) != null) {
              ref6.on('move', this._move);
            }
          }
          if ((ref7 = this._relative.closest('.i-panel')) != null) {
            if ((ref8 = ref7.data('panel')) != null) {
              ref8.on('close', this._close);
            }
          }
          if ((ref9 = this._relative.closest('.i-panel')) != null) {
            if ((ref10 = ref9.data('panel')) != null) {
              ref10._scroll.on('scroll', this._move);
            }
          }
          if (this._relative.closest('.i-panel')) {
            this.addClass('i-panel-nested');
          }
        }
      } else {
        this.appendTo(document.body);
      }
      sim(window).on('resize scroll', this._move);
      setImmediate((function(_this) {
        return function() {
          _this.addClass('in');
          _this._move();
          return Guide.refresh();
        };
      })(this));
    }

    Panel.prototype.destroy = function() {
      var ref10, ref11, ref4, ref5, ref6, ref7, ref8, ref9;
      if (this._destroyed) {
        return;
      }
      this._destroyed = true;
      Panels.splice(Panels.indexOf(this), 1);
      if (this._relative != null) {
        if ((typeof Surface !== "undefined" && Surface !== null) && this._relative instanceof Surface.DisplayObject) {
          this._relative.off('move', this._move);
          this._relative.off('detach', this._close);
          this._relative.stage.off('move', this._move);
          this._relative.stage.surface.camera.off('zoom', this._move);
        } else {
          if ((ref4 = this._relative.closest('.i-paper')) != null) {
            ref4.off('close', this._close);
          }
          if ((ref5 = this._relative.closest('.i-panel')) != null) {
            if ((ref6 = ref5.data('panel')) != null) {
              ref6.off('move', this._move);
            }
          }
          if ((ref7 = this._relative.closest('.i-panel')) != null) {
            if ((ref8 = ref7.data('panel')) != null) {
              ref8.off('close', this._close);
            }
          }
          if ((ref9 = this._relative.closest('.i-panel')) != null) {
            if ((ref10 = ref9.data('panel')) != null) {
              ref10._scroll.off('scroll', this._move);
            }
          }
        }
      }
      sim(window).off('resize scroll', this._move);
      if ((ref11 = this._bg) != null) {
        ref11.remove();
      }
      this.removeClass('in');
      return delay(100, (function(_this) {
        return function() {
          _this.emit('destroy');
          return _this.remove();
        };
      })(this));
    };

    Panel.prototype.aside = function(ctx) {
      this._aside = sim.div('.i-panel-aside', ctx);
      if (this.loading) {
        this._aside.hide();
      }
      this.addClass('i-panel-has-aside');
      this.prepend(this._aside);
      return this._aside;
    };

    Panel.prototype.close = function() {
      return this._close();
    };

    Panel.prototype._close = function() {
      this.emit('close');
      this.destroy();
      return delay(500, function() {
        return Guide.refresh();
      });
    };

    Panel.prototype._expand = function() {
      if (this._expanded) {
        this._expanded = false;
        this._header.find('.expand i').addClass('fa-expand-arrows').removeClass('fa-compress');
        this.emit('compress');
        return this.stop().animate({
          width: this._savedWidth
        }, {
          duration: 'fast',
          progress: this._move,
          complete: this._move
        });
      } else {
        this._expanded = true;
        this._header.find('.expand i').removeClass('fa-expand-arrows').addClass('fa-compress');
        this.emit('expand');
        this._savedWidth = this.outerWidth();
        return this.stop().animate({
          width: Math.min(this._savedWidth * 2, sim(window).width() - PANEL_PADDING * 2)
        }, {
          duration: 'fast',
          progress: this._move,
          complete: this._move
        });
      }
    };


    /*
    	Align the panel next to the node.
     */

    Panel.prototype._move = function() {
      var coords, left, offset, position, ref4, ref5, requiredWidth;
      if (this._relative != null) {
        position = this.position;
        if ((typeof Surface !== "undefined" && Surface !== null) && this._relative instanceof Surface.DisplayObject) {
          coords = this._relative.documentCoords;
          offset = position === 'top' || position === 'bottom' ? 0 : this.offsetX * ((ref4 = (ref5 = this._relative.stage) != null ? ref5.scale : void 0) != null ? ref4 : 1);
        } else {
          coords = new Point(this._relative.offset().left + this._relative.outerWidth() / 2, this._relative.offset().top + this._relative.outerHeight() / 2);
          offset = position === 'top' || position === 'bottom' ? (this.loading ? 0 : this.offsetX) : this._relative.outerWidth() / 2 + this.offsetX;
        }
        requiredWidth = this.outerWidth() + offset;
        this._arrow.removeClass('i-arrow-left i-arrow-right i-arrow-top i-arrow-bottom');
        if (position === 'top' || position === 'bottom') {
          left = coords.x - requiredWidth / 2;
          if (left > sim(window).width() - requiredWidth - PANEL_MARGIN) {
            left = sim(window).width() - requiredWidth - PANEL_MARGIN;
          }
          if (left < PANEL_MARGIN) {
            left = PANEL_MARGIN;
          }
          this._arrow.addClass("i-arrow-" + position).css('left', (coords.x - left) + "px");
          this.css('left', left + "px");
        } else {
          if (position === 'left' && coords.x - requiredWidth < PANEL_MARGIN) {
            position = 'auto';
          }
          if (position === 'right' && sim(window).width() - coords.x < requiredWidth + PANEL_MARGIN && coords.x > requiredWidth) {
            position = 'auto';
          }
          if (position === 'auto') {
            position = coords.x > sim(window).width() - coords.x ? 'left' : 'right';
          }
          if (position === 'left') {
            left = coords.x - requiredWidth;
            if (left > sim(window).width() - this.outerWidth() - PANEL_MARGIN) {
              left = sim(window).width() - this.outerWidth() - PANEL_MARGIN;
            }
            if (left < PANEL_MARGIN) {
              left = PANEL_MARGIN;
            }
            this._arrow.addClass('i-arrow-left');
            this.css('left', left + "px");
          } else {
            left = coords.x + offset;
            if (left < PANEL_MARGIN) {
              left = PANEL_MARGIN;
            }
            if (left > sim(window).width() - this.outerWidth() - PANEL_MARGIN) {
              left = sim(window).width() - this.outerWidth() - PANEL_MARGIN;
            }
            this._arrow.addClass('i-arrow-right');
            this.css('left', left + "px");
          }
        }
      } else {
        this.css('left', ((sim(window).width() - this.outerWidth()) / 2) + "px");
      }
      this._resize();
      return this.emit('move');
    };

    Panel.prototype._resize = function() {
      var coords, footer, header, height, modal, offset, position, ref10, ref11, ref4, ref5, ref6, ref7, ref8, ref9, scroll, top;
      position = this.position;
      if (this._relative != null) {
        if ((typeof Surface !== "undefined" && Surface !== null) && this._relative instanceof Surface.DisplayObject) {
          coords = this._relative.documentCoords;
          if (position === 'left' || position === 'right') {
            coords.y += this.offsetY * ((ref4 = (ref5 = this._relative.stage) != null ? ref5.scale : void 0) != null ? ref4 : 1);
          }
        } else {
          if (!this._hidden && !this._relative.is(':visible')) {
            this._hidden = true;
            return this.hide();
          }
          if (this._hidden && this._relative.is(':visible')) {
            this._hidden = false;
            return this.show();
          }
          coords = new Point(this._relative.offset().left + this._relative.outerWidth() / 2, this._relative.offset().top + this._relative.outerHeight() / 2);
          modal = (ref6 = this._relative.closest('.modal')) != null ? ref6 : this._relative.closest('.i-panel');
          coords.y -= sim(window).scrollTop();
        }
      }
      scroll = 'auto';
      header = this._header.is(':visible') ? this._header.outerHeight() : 0;
      footer = this._footer.is(':visible') ? this._footer.outerHeight() : 0;
      height = (this._body.is(':visible') ? this._body.outerHeight(true) : 0) + header + footer;
      if (this._loading) {
        height = Math.max(this._loading.outerHeight(true), height);
      }
      if (this._relative != null) {
        if (position === 'top') {
          offset = this.offsetY * ((ref7 = (ref8 = this._relative.stage) != null ? ref8.scale : void 0) != null ? ref7 : 1);
          top = coords.y - height - offset;
        } else if (position === 'bottom') {
          offset = this.offsetY * ((ref9 = (ref10 = this._relative.stage) != null ? ref10.scale : void 0) != null ? ref9 : 1);
          top = coords.y + offset;
        } else {
          top = coords.y - height / 2;
        }
        if (top + height > sim(window).height() - PANEL_MARGIN) {
          top = sim(window).height() - height - PANEL_MARGIN;
        }
        if (position === 'bottom' && top < coords.y + offset) {
          top = coords.y + offset;
          height = sim(window).height() - PANEL_MARGIN - top;
          scroll = (height - (header + footer)) + "px";
        }
        if (top < PANEL_MARGIN) {
          top = PANEL_MARGIN;
          if (position === 'top') {
            height = coords.y - PANEL_MARGIN - offset;
            scroll = (height - (header + footer)) + "px";
          }
        }
      } else {
        top = (sim(window).height() - height) / 2;
      }
      if (height > sim(window).height() - PANEL_MARGIN * 2) {
        top = PANEL_MARGIN;
        height = sim(window).height() - PANEL_MARGIN * 2;
        scroll = (height - (header + footer)) + "px";
      }
      this._scroll.css('height', scroll);
      this.css({
        top: top + "px",
        height: height + "px"
      });
      if ((ref11 = this._aside) != null) {
        ref11.css('height', height + "px");
      }
      if ((this._relative != null) && (position === 'left' || position === 'right')) {
        return this._arrow.css('top', (coords.y - top) + "px");
      }
    };

    Panel.prototype.warn = function(message, content) {
      var exception;
      this.loading = false;
      exception = sim.div('.i-exception', function() {
        if (message instanceof Error) {
          ex = message;
          this.h5().text(imt.l('base', 'common.error'));
          return this.p(function() {
            var ref4;
            this.text(ex.message);
            if ((ref4 = ex.errors) != null ? ref4.length : void 0) {
              return this.ul('.list-unstyled.i-exception-suberrors', function() {
                var len4, ref5, results, serr, z;
                ref5 = ex.errors;
                results = [];
                for (z = 0, len4 = ref5.length; z < len4; z++) {
                  serr = ref5[z];
                  results.push(this.li(function() {
                    this.text("" + serr.message);
                    return this.prepend(sim.i('.far.fa-fw.fa-angle-right'));
                  }));
                }
                return results;
              });
            }
          });
        } else {
          this.h5().text(imt.l('base', 'common.error'));
          return this.p().text(message);
        }
      });
      if (content) {
        return this.content = [exception, content];
      } else {
        return this.content = exception;
      }
    };

    return Panel;

  })(SIMElement);

  global.Panels = [];

  global.Panels.byType = function(type) {
    var len4, name, panel, ref4, z;
    ref4 = this;
    for (z = 0, len4 = ref4.length; z < len4; z++) {
      panel = ref4[z];
      name = panel.constructor.name.toLowerCase();
      if (/^(.*)panel$/.exec(name)) {
        name = RegExp.$1;
      }
      if (name === type) {
        return panel;
      }
    }
    return null;
  };

  Object.defineProperty(Panels, 'one', {
    get: function() {
      return PANEL_ONE;
    },
    set: function(panel) {
      if (PANEL_ONE != null) {
        PANEL_ONE.close();
      }
      PANEL_ONE = panel;
      return panel.once('destroy', function() {
        if (PANEL_ONE === panel) {
          return PANEL_ONE = null;
        }
      });
    }
  });

  sim(window).on('click', function(event) {
    if (!Panels.one) {
      return;
    }
    if (sim(event.target).closest('.i-panel')) {
      return;
    }
    if (sim(event.target).closest('.dropdown-menu')) {
      return;
    }
    return Panels.one.close();
  });

  sim(document).on('keyup', function(event) {
    var ref4;
    if (event.keyCode === 27) {
      if ((ref4 = Panels[Panels.length - 1]) != null ? ref4.closeable : void 0) {
        return Panels[Panels.length - 1].close();
      }
    }
  });

}).call(this);
