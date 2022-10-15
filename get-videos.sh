#!/usr/bin/env bash

jo -p -a `find $1 -name '*.mp4' -or -name '*.m4v' -or -name '*.avi'`

