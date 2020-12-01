const puppeteer = require('puppeteer');
const now = require('performance-now');
const { Cluster } = require('puppeteer-cluster')
const fs = require('fs');
const { promisify } = require('util');
const yargs = require('yargs')

const readFileAsync = promisify(fs.readFile);

const argv = yargs
    .scriptName('bsc-wasm-spider')
    .option('manual', { alias: 'm', default: false, description: 'Enable manual mode', type: 'boolean'})
    .option('workers', { alias: 'j', default: 8, description: 'Worker/Thread count', type: 'number'})
    .option('depth', { alias: 'd', default: 1, description: 'Crawler URL recursion depth', type: 'number'})
    .option('breadth', { alias: 'b', default: 3, description: 'Crawler URL recursion breadth / branching factor', type: 'number'})
    .option('seed-list', { alias: 'i', description: 'Crawler seed list', type: 'string'})
    .option('start', { alias: 's', default: 0, description: 'Seed list start index', type: 'number'})
    .option('end', { alias: 'e', default: -1, description: 'Seed list end index (exclusive)', type: 'number'})
    .option('port', { alias: 'p', default: 31337, description: 'Proxy port', type: 'number'})
    .option('verbose', { alias: 'v', default: false, description: 'Verbose log output', type: 'boolean'})
    .help().alias('help', 'h')
    .argv;
const MANUAL_MODE = argv.manual;
const MAX_RECURSION_DEPTH = argv.depth;
const MAX_RECURSION_BREADTH = argv.breadth;
const WAIT_TIME = 5000;
const LOAD_EVENT_TIMEOUT = 30000;
const WORKERS = argv.workers;
const USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.0 Safari/537.36";

var queue_remaining = 0;
var completed_success = 0;
var completed_error = 0;
const start = now();

process.setMaxListeners(WORKERS);

(async () => {
    if(MANUAL_MODE){
        const browser = await puppeteer.launch({
            devtools: true,
            defaultViewport: {width: 1200, height: 800},
            args: [
                '--disable-http2', 
                '--enable-features=NetworkService',
                '--proxy-server=127.0.0.1:' + argv.port,
                '--ignore-certificate-errors',
            ]
        });
    } else {
        if(!fs.existsSync(argv["seed-list"])){
            console.error("Input file does not exist.");
            process.exit(1);
        }

        console.log(`${timestamp()}Workers: ${WORKERS}; Recursion: d=${MAX_RECURSION_DEPTH}, b=${MAX_RECURSION_BREADTH}.`);

        const cluster = await Cluster.launch({
            concurrency: Cluster.CONCURRENCY_CONTEXT,
            maxConcurrency: WORKERS,
            workerCreationDelay: 200,
            retryLimit: 1,
            timeout: 30000,
            puppeteerOptions: {
                args: [
                    '--disable-http2',
                    '--proxy-server=127.0.0.1:' + argv.port,
                    '--ignore-certificate-errors',
                ]
            },
            monitor: false,
        });

        cluster.on("taskerror", (err, data) => {
            console.error(`${timestamp()}Error crawling ${data.url}: ${err.message}`);
            if(err.message.includes("Timeout hit")){
                completed_success++;
                queue_remaining--;
            } else {
                completed_error++;
                // NOTE we do not account for retries, these numbers are mostly inaccurate.
            }
        });

        cluster.task(async ({ page, data }) => {
            if(argv.verbose) console.log(`${timestamp()}puppeteer@${argv.port}: Visiting ${data.url}. Remaining in queue: ${queue_remaining}`);
            const { url, recursion } = data;
            await page.setUserAgent(USER_AGENT);

            // callback for transparent hooks below
            await page.exposeFunction('wasmModuleCallback', (buf, loc, dom) => {
                if(!buf || buf.length == 0) return;

                const fname = dom.split(".").join("_") + "_" + buf.substring(0, 16) + ".wasm.b64";
                const date = new Date();
                var meta = "";
                meta += "file: " + fname + "\n";
                meta += "url: " + loc + "\n";
                meta += "date: " + date.getFullYear() + "-" + date.getMonth() + "-" + date.getDate() + "\n";
                meta += "content-type: unknown-hook\n";
                meta += "related-js: []\n";
                meta += "method: crawler-instantiate-hook\n";

                fs.writeFileSync("results/" + fname, buf);
                fs.writeFileSync("results/" + fname + ".meta", meta);
                if(argv.verbose) console.log(`${timestamp()}Detected .wasm module via hook.`);
            });

            await page.evaluateOnNewDocument(() => {
                function toBase64(buf){
                    const arr = new Uint8Array(buf);
                    const bin = String.fromCharCode.apply(null, arr);
                    const b64 = window.btoa(bin);
                    return b64;
                }
                // set up transparent hooks on Wasm functions
                // replace instantiate
                let original_instantiate = WebAssembly.instantiate;
                WebAssembly.instantiate = function(bufferSource) {
                    // Instantiate can be called with an WebAssembly.Module as
                    // argument. In that case, we have already intercepted the
                    // construction of that object. Check whether byteLength
                    // is defined to see if the given argument is an ArrayBuffer.
                    if(bufferSource.byteLength) {
                        wasmModuleCallback(toBase64(bufferSource), window.location.href, window.location.hostname);
                    }
                    return original_instantiate.call(WebAssembly, ...arguments);
                };
                // replace instantiateStreaming
                WebAssembly.instantiateStreaming = async function(source, obj){
                    let response = await source;
                    let body = await response.arrayBuffer();
                    return WebAssembly.instantiate(body, obj);
                }
                //replace compile
                let original_compile = WebAssembly.compile;
                WebAssembly.compile = function(bufferSource) {
                    wasmModuleCallback(toBase64(bufferSource), window.location.href, window.location.hostname);
                    return original_compile.call(WebAssembly, ...arguments);
                };
                // replace compileStreaming
                WebAssembly.compileStreaming = async function(source){
                    let response = await source;
                    let body = await response.arrayBuffer();
                    return WebAssembly.compile(body);
                };
                // Proxy constructor (called when invoking `new WebAssembly.Module(...)`)
                WebAssembly.Module = new Proxy(WebAssembly.Module, {
                    construct: function(target, args) {
                        wasmModuleCallback(toBase64(...args), window.location.href, window.location.hostname);
                        return new target(...args);
                    }
                });
            });
            await page.goto(url, {waitUntil: ["networkidle0", "domcontentloaded"], timeout: LOAD_EVENT_TIMEOUT});
            await page.waitFor(WAIT_TIME);

            if(recursion < MAX_RECURSION_DEPTH){
                const elems = (await page.evaluate(() => {
                    return [...document.querySelectorAll('a')].map(elem => elem.href);
                }));

                // Add a maximum of M_R_BREADTH random urls to the queue.
                for(let i = 0; elems && elems.length > 0 && i < MAX_RECURSION_BREADTH; i++){
                    let t = elems.splice(Math.floor(Math.random() * elems.length), 1)[0];
            
                    // ignore javascript:void(0) etc.
                    if(t.startsWith("javascript:")){
                        i--;
                        continue;
                    }

                    cluster.queue({
                        url: t,
                        recursion: recursion + 1
                    });

                    queue_remaining++;
                }
            }
            queue_remaining--;
            completed_success++;
        });

        const start = argv.start;
        const end = argv.end;
        console.log(`${timestamp()}Queuing ${argv["seed-list"]} from index ${start} to ${end}.`)

        var urls = (await readFileAsync(argv["seed-list"])).toString().split("\n");
        var i = 0;
        for (var url of urls){ 
            if(i >= start && (i < end || end == -1) && url.length > 0){
                if(!(url.startsWith("http://") || url.startsWith("https://"))) {
                    url = "http://" + url;
                }
                cluster.queue({ url: url, recursion: 0 });
                queue_remaining++;
            }
            i++;
        }
        await cluster.idle();
        await cluster.close();

        if(argv.verbose) console.log(`${timestamp()}puppeteer@${argv.port}: Done. Time: ${(now() - start) / 1000}s. Rem.: ${queue_remaining}. OK.: ${completed_success}. Err.: ${completed_error}`);
    }
})();

function timestamp() {
    const date = new Date();
    return "[" + date.getFullYear() + "-" + date.getMonth() + "-" + date.getDate() + " " + date.getHours() + ":" + date.getMinutes() + ":" + date.getSeconds() + "] ";
}

