#!/bin/bash
# Utility script to start a lot of instances. Each instances stdout
# will be redirected to log_i. The variables below should be customized
# to set up the seed list, seed list offset, number of instances, etc.

# Port of the first instance. Other instances will be assigned subsequent ports.
PORT=31337
# Offset into the seed file (0 = start at first URL)
OFFSET=0
# Maximum number of pages to visit
PAGE_COUNT=50000
# Number of instances to start
INSTANCES=20
# Concurrency of each started puppeteer instance (leave at 8)
PUPP_CONCURRENCY=8
# Seed file
FILE="tranco"
# Recursion depth
REC_DEPTH=7
# Recursion breadth
REC_BREADTH=3
# Whether to call a notification script (can be used to send an email or sim.)
NOTIFY=1
# Output directory, where results willl be moved to *after* the crawler has finished.
OUT_DIR=results_${FILE}_to_$(( ($OFFSET + $PAGE_COUNT)/1000 ))k_d${REC_DEPTH}b${REC_BREADTH}
# Chunk sizes (do not modify)
CHUNK=$(( $PAGE_COUNT / $INSTANCES + 1 ))

echo "Starting $INSTANCES instances with 8 threads each. CHUNK_SIZE is $CHUNK. OFFSET is $OFFSET."
echo "Target directory is $OUT_DIR."
echo "Press ENTER to continue..."

read _

for i in $(seq 0 $(( $INSTANCES - 1 ))); do
	./run.sh -v -i $FILE -d $REC_DEPTH -b $REC_BREADTH -j $PUPP_CONCURRENCY -p $(( $PORT + $i )) -s $(( $OFFSET + $i * $CHUNK )) -e $(( $OFFSET + $i * $CHUNK + $CHUNK)) 2>&1 | tee "log_$i" &
	pids[${i}]=$!
done

[[ "$NOTIFY" = "1" ]] && python ../notify.py "@everyone :cyclone: **Crawler started**. Settings: \`$FILE:$OFFSET..$(( $OFFSET + $PAGE_COUNT )) r=$REC_DEPTH d=$REC_BREADTH #insts=$INSTANCES\`."

for pid in ${pids[*]}; do
	wait $pid
done

echo "All jobs finished."

[[ "$NOTIFY" = "1" ]] && python ../notify.py "@everyone :white_check_mark: **Crawler finished**. Files: $(ls results/ | wc -l). Modules: $(ls results/*.wasm | wc -l). B64: $(ls results/*.b64 | wc -l). Results in: $OUT_DIR"

mv results "$OUT_DIR"
