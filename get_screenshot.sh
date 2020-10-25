#!/bin/bash

FILE_PREFIX=$(date +%Y%m%d-%H-%M-%S)
FILE_NAME="${FILE_PREFIX}_screenshot.png" 

import -window memberbooth $FILE_NAME && echo "Screenshot saved to ${FILE_NAME}"
