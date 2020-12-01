#!/bin/bash
# Command line arguments will be forwarded to crawler.js.
# Run with -h/--help to see available options.

mkdir -p results

# Parse port from args
PORT=31337
for i in "$@"
do
	if [ -n "$READ_PORT" ]; then
		PORT="$i"
		break
	fi
	case $i in
		-p|--port)
			READ_PORT=1
            ;;
		-m|--manual)
			MANUAL=1
            ;;
	esac
done

echo -n "Started crawler with args '$@' @ " >> log
date >> log

echo "Starting mitmproxy on port $PORT."
MITMDUMP="./bin/mitmdump"
[ -e "$MITMDUMP" ] || {
    echo -e "\nCould not find mitmdump binary."
    echo "Please download mitmproxy and symlink or copy the mitmdump executable to bin/!";
    exit 1;
}

if [ -n "$MANUAL" ]; then
    echo "Starting in MANUAL mode."
    "$MITMDUMP" -p $PORT -s response_handler.py | grep --color=always "\[!\]" & 
else
    "$MITMDUMP" -p $PORT -s response_handler.py -q & 
fi

# Wait for proxy to start
sleep 3

echo "Starting crawler."
node --unhandled-rejections=strict crawler.js "$@" 

# After crawler has stopped running...
echo "Crawler terminated, stopping mitmproxy..."
kill $(jobs -p)

echo -n "Crawler with args '$@' terminated @" >> log
date >> log
echo "Done."
