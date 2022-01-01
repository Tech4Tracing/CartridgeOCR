#!/bin/bash
cd ../data/
wget \
     --level=inf \
     --limit-rate=20K \
     --recursive \
     --page-requisites \
     --user-agent=Mozilla \
     --no-parent \
     --convert-links \
     --adjust-extension \
     https://afte.org/laravel.php/gallery/index

#--wait=2 \
#     --no-clobber \
#     -e robots=off \
     
