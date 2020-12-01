#!/bin/bash
for package in $(cat ../packages.txt)
do
    wapm install "$package"
done
