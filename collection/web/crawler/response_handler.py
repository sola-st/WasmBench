from mitmproxy import ctx
from datetime import date
from hashlib import sha256
from urllib.parse import urlparse

recent_js_files = []
out_dir = "./results/"

def info(msg):
    ctx.log.info("[!] " + msg)

def response(flow):
    global recent_js_files

    recent_js_files = recent_js_files[-100:]
    domain = urlparse(flow.request.url).netloc

    if "wasm" in flow.request.url or flow.response.headers.get("content-type", "") in ["application/wasm", "application/octet-stream"]:
        buffer = flow.response.get_content()
        if buffer[0:4] == b'\x00asm':
            hash = sha256(buffer).hexdigest()
            filename = domain.replace(".", "_") + "_" + hash[:16] 
            info("Detected WebAssembly module! Hash: %s" % hash)
            with open(out_dir + filename + ".wasm", 'wb') as out:
                out.write(buffer)
                info("Wrote bytes to %s" % filename)
            with open(out_dir + filename + ".meta", 'w') as out:
                out.write("file: " + filename + ".wasm" + "\n")
                out.write("url: " + flow.request.url + "\n")
                out.write("date: " + str(date.today()) + "\n")
                out.write("content-type: " + flow.response.headers.get("content-type", "") + "\n")
                out.write("related-js: " + \
                        str([item[1] for item in recent_js_files if True or item[0] == domain]) + "\n")
                out.write("method: crawler-mitmproxy\n")
                info("Wrote metadata file")

    elif flow.request.url.endswith(".js"):
        recent_js_files += [(domain, flow.request.url)]
        text = flow.response.get_text()
        if "WebAssembly" in text:
            hash = sha256(bytes(text, "utf-8")).hexdigest()
            filename = domain.replace(".", "_") + "_" + hash[:16] + "_" + flow.request.url.split("/")[-1]
            info("Detected WebAssembly keyword in JavaScript!")
            with open(out_dir + filename, 'w') as out:
                out.write(text)
                out.write("\n//src_url:" + flow.request.url)
                info("Wrote text to %s" % filename)

