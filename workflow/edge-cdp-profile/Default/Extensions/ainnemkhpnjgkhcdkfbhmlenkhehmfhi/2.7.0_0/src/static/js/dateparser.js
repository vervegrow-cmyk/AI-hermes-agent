(function() {
  global.IMTDate = {
    timezone: 'UTC',
    parse: function(value, timezone) {
      var ampm, d, day, dd, fraction, hour, minute, month, offset, ref, ref1, ref2, ref3, ref4, second, time, timestamp, year;
      if (value instanceof Date) {
        return value;
      }
      if (typeof value === 'number') {
        value = String(value);
      }
      if (typeof value !== 'string') {
        return null;
      }
      value = value.trim();
      timezone || (timezone = IMTDate.timezone);
      if (/^\d+$/.test(value)) {
        return new Date(parseInt(value));
      }
      hour = 0;
      minute = 0;
      second = 0;
      fraction = 0;
      offset = null;
      dd = function(val, digs) {
        if (digs == null) {
          digs = 2;
        }
        return "" + ("0".repeat(digs - String(val).length)) + val;
      };
      if (/^(\d{4})[\-\/](\d{1,2})[\-\/](\d{1,2})[T\s]?(.+)?$/i.exec(value)) {
        year = parseInt(RegExp.$1);
        month = parseInt(RegExp.$2);
        day = parseInt(RegExp.$3);
        time = (ref = RegExp.$4) != null ? ref.trim() : void 0;
        if (month > 12) {
          d = day;
          day = month;
          month = d;
        }
      }
      if (/^(\d{1,2})[\.\-]\s?(\d{1,2})[\.\-]\s?(\d{4})\s*(.+)?$/i.exec(value)) {
        year = parseInt(RegExp.$3);
        month = parseInt(RegExp.$2);
        day = parseInt(RegExp.$1);
        time = (ref1 = RegExp.$4) != null ? ref1.trim() : void 0;
        if (month > 12) {
          d = day;
          day = month;
          month = d;
        }
      }
      if (/^(\d{1,2})\/(\d{1,2})\/(\d{4})\s*(.+)?$/i.exec(value)) {
        year = parseInt(RegExp.$3);
        month = parseInt(RegExp.$1);
        day = parseInt(RegExp.$2);
        time = (ref2 = RegExp.$4) != null ? ref2.trim() : void 0;
        if (month > 12) {
          d = day;
          day = month;
          month = d;
        }
      }
      if (time && /^(.+)?([+\-])(\d\d):?(\d\d)$/i.exec(time)) {
        offset = (parseInt(RegExp.$3) * 60 * 60 + parseInt(RegExp.$4) * 60) * 1000;
        if (RegExp.$2 === '-') {
          offset *= -1;
        }
        time = (ref3 = RegExp.$1) != null ? ref3.trim() : void 0;
      }
      if (time && /^(.+)?(Z|UTC|GMT)$/i.exec(time)) {
        offset || (offset = 0);
        time = (ref4 = RegExp.$1) != null ? ref4.trim() : void 0;
      }
      if (time && /^(\d{1,2}):(\d{1,2})(?:\:(\d{1,2})(?:\.(\d+))?)?$/i.exec(time)) {
        hour = parseInt(RegExp.$1);
        minute = parseInt(RegExp.$2);
        second = parseInt(RegExp.$3 || 0);
        fraction = parseInt((RegExp.$4 || 0).toString().substr(0, 3));
      } else if (time && /^(\d{1,2})(?:\:(\d{1,2}))?\s*(AM|PM)$/i.exec(time)) {
        hour = parseInt(RegExp.$1);
        minute = parseInt(RegExp.$2 || 0);
        ampm = RegExp.$3.toLowerCase();
        if (ampm === 'am' && hour === 12) {
          hour = 0;
        } else if (ampm === 'pm' && hour !== 12) {
          hour += 12;
        }
      } else if (time) {
        return null;
      }
      if (year) {
        timestamp = Date.UTC(year, month - 1, day, hour, minute, second, fraction);
        if (isNaN(timestamp)) {
          return null;
        }
        if (offset != null) {
          return new Date(timestamp - offset);
        } else if (timezone && timezone !== 'UTC') {
          return moment.tz(year + "-" + (dd(month)) + "-" + (dd(day)) + "T" + (dd(hour)) + ":" + (dd(minute)) + ":" + (dd(second)) + "." + (dd(fraction, 3)), timezone).toDate();
        } else {
          return new Date(timestamp);
        }
      }
      return null;
    },
    parseTime: function(value, timezone) {
      var ampm, fraction, hour, minute, second;
      timezone || (timezone = IMTDate.timezone);
      if (value instanceof Date) {
        value = moment(value).tz(timezone).format('HH:mm:ss.SSS');
      }
      if (typeof value !== 'string') {
        return null;
      }
      value = value.trim();
      hour = 0;
      minute = 0;
      second = 0;
      fraction = 0;
      if (value && /^(\d{1,2}):(\d{1,2})(?:\:(\d{1,2})(?:\.(\d{1,3}))?)?$/i.exec(value)) {
        hour = parseInt(RegExp.$1);
        minute = parseInt(RegExp.$2);
        second = parseInt(RegExp.$3 || 0);
        fraction = parseInt(RegExp.$4 || 0);
      } else if (/^(\d{1,2})(?:\:(\d{1,2}))?\s*(AM|PM)$/i.exec(value)) {
        hour = parseInt(RegExp.$1);
        minute = parseInt(RegExp.$2 || 0);
        ampm = RegExp.$3.toLowerCase();
        if (ampm === 'am' && hour === 12) {
          hour = 0;
        } else if (ampm === 'pm' && hour !== 12) {
          hour += 12;
        }
      } else {
        value = IMTDate.parse(value, timezone);
        if (value) {
          return IMTDate.parseTime(value, timezone);
        }
        return null;
      }
      if (hour >= 24) {
        return null;
      }
      if (minute >= 60) {
        return null;
      }
      if (second >= 60) {
        return null;
      }
      if (fraction >= 1000) {
        return null;
      }
      return fraction + second * 1000 + minute * 60 * 1000 + hour * 60 * 60 * 1000;
    },
    timeToString: function(number) {
      var dd, fraction, hour, minute, second, txt;
      if ('number' !== typeof number) {
        return null;
      }
      if (number >= 86400000) {
        return null;
      }
      dd = function(val, digs) {
        if (digs == null) {
          digs = 2;
        }
        return "" + ("0".repeat(digs - String(val).length)) + val;
      };
      hour = Math.floor(number / 3600000);
      number = number % 3600000;
      minute = Math.floor(number / 60000);
      number = number % 60000;
      second = Math.floor(number / 1000);
      fraction = number % 1000;
      txt = '' + dd(hour);
      txt += ':' + dd(minute);
      if (second || fraction) {
        txt += ':' + dd(second);
      }
      if (fraction) {
        txt += '.' + dd(fraction, 3);
      }
      return txt;
    }
  };
}).call(this);
