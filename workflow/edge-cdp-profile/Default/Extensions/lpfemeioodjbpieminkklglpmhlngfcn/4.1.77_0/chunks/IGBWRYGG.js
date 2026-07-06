import{f as r}from"./E4I5EUY3.js";import{i as o}from"./3PS7M655.js";var n=class{constructor(t){o(this,"module");this.module=t.split("/").map(s=>`[${s}]`).join("")}info(...t){if(r)return;let s=this.getCallStack()}error(...t){if(r)return;let s=this.getCallStack()}warn(...t){if(r)return;let s=this.getCallStack()}debug(...t){if(r)return;let s=this.getCallStack()}getCallStack(){var s;let t=new Error().stack;if(t){let a=t.split(`
`).slice(2).join(`
`);return(s=a==null?void 0:a.split(/\n/))==null?void 0:s[1]}return""}},l=n;export{l as a};
