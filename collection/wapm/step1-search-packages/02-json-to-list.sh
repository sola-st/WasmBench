#!/bin/bash
egrep -o ': "(.*)"' result.json | cut -d'"' -f2 > packages.txt
