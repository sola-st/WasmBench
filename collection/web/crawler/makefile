
install: install_mitmproxy  
	npm i puppeteer puppeteer-cluster yargs performance-now

install_mitmproxy:
	mkdir -p bin
	wget https://snapshots.mitmproxy.org/5.1.1/mitmproxy-5.1.1-linux.tar.gz
	tar xzf mitmproxy-5.1.1-linux.tar.gz
	mv mitmdump bin/
	rm mitmproxy mitmweb mitmproxy-*.tar.gz

