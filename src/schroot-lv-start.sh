#!/bin/bash

LV_SESSION_FILE=/var/lib/schroot/session/lv

# check to make sure that the last schroot session shut down correctly
if [ -e $LV_SESSION_FILE ]; then
	rm -f $LV_SESSION_FILE
fi

# start the session
/usr/bin/schroot --begin-session --session-name=lv -c labview
