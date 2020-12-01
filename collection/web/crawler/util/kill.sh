#!/bin/sh
echo "This will kill all node and chrome processes on your machine. ENTER to continue."
read _
killall node -s SIGKILL
killall chrome -s SIGKILL
killall mitmdump -s SIGKILL
