# engine/polyfills.py

class JSPolyfills:
    @staticmethod
    def generate(proxy: str | None = None, debug: bool = False) -> str:
        proxy_line = (
            'const HttpsProxyAgent = require("https-proxy-agent").HttpsProxyAgent;'
            f' const proxyAgent = new HttpsProxyAgent("{proxy}");'
            if proxy
            else "let proxyAgent;"
        )
        debug_js = "true" if debug else "false"
        return f'''
globalThis.window = globalThis;
globalThis.parent = globalThis;

globalThis.navigator = {{
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Node.js",
    platform: "Win32",
    language: "en-US",
    hardwareConcurrency: 4,
}};

globalThis.location = {{
    href: "https://html5.haxball.com/headless",
    origin: "https://html5.haxball.com",
    protocol: "https:",
    host: "html5.haxball.com",
    hostname: "html5.haxball.com",
    pathname: "/headless",
}};

globalThis.document = {{
    createElement: () => ({{ setAttribute: () => {{}}, appendChild: () => {{}}, style: {{}} }}),
    getElementById: () => null,
    body: {{ appendChild: () => {{}} }}
}};

globalThis.pako = require("pako");

const perf_hooks = require("perf_hooks");
const _nodePerf = perf_hooks.performance;
globalThis.performance = new Proxy(_nodePerf, {{
    get(target, prop) {{
        if (prop in target) return target[prop];
        if (prop === 'timing') return {{ navigationStart: Date.now() }};
        if (prop === 'navigation') return {{ type: 0 }};
        return undefined;
    }}
}});

const WSMod = require("ws");
globalThis.WebSocket = WSMod;
var WebSocket = WSMod;

{proxy_line}

const _CryptoMod = require("@peculiar/webcrypto");
const crypto = new _CryptoMod.Crypto();
globalThis.crypto = crypto;

globalThis.JSON5 = require("json5");

if (!console.debug) console.debug = console.log;

let promiseResolve = null;
const HBInitPromise = new Promise((resolve) => {{ promiseResolve = resolve; }});

const debug = {debug_js};
globalThis.onHBLoaded = (cb) => cb;

// Use xhr2 (same as haxball.js) for XMLHttpRequest
const XHR2 = require("xhr2");
globalThis.XMLHttpRequest = XHR2;

// Real WebRTC via node-datachannel (same as haxball.js)
try {{
    const dcPolyfill = require("node-datachannel/polyfill");
    globalThis.RTCPeerConnection = dcPolyfill.RTCPeerConnection;
    globalThis.RTCIceCandidate = dcPolyfill.RTCIceCandidate;
    globalThis.RTCSessionDescription = dcPolyfill.RTCSessionDescription;
    globalThis.RTCDataChannel = dcPolyfill.RTCDataChannel;
}} catch (e) {{
    console.error("node-datachannel not available, WebRTC will not work:", e.message);
}}
'''
