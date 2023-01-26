#!/bin/bash

# TODO (0) STRUCT UPDATE and move to the right directory
# TODO (1) dynamic paths 
# Script to link to a shortcut

# 

vlc_request=$(curl -u :vlc http://localhost:8080/requests/status.xml)

if [ 0 -eq $? ]; then
	vlc_seconds=$(xmllint --xpath "//root/time/text()" - <<<"$vlc_request")
	vlc_state=$(xmllint --xpath "//root/state/text()" - <<<"$vlc_request")
	if [[ "$vlc_state" == "playing" ]]; then
		curl -u :vlc http://localhost:8080/requests/status.xml?command=pl_pause
		# password is set to "vlc", replace if you have a different password 
	fi
	vlc_filename=$(xmllint --xpath 'string(//root/information/category[@name="meta"]/info[@name="filename"])' - <<<"$vlc_request")
	echo "vlc_seconds: ${vlc_seconds}"
	hour=$(bc <<<"$vlc_seconds/3600")
	min=$(bc <<<"($vlc_seconds - $hour*3600)/60")
	sec=$(bc <<<"($vlc_seconds - $hour*3600 - $min*60)")

	hour=$(printf "%02d\n" $hour)
	min=$(printf "%02d\n" $min)
	sec=$(printf "%02d\n" $sec)

	timecode="${hour}:${min}:${sec}"

	notify-send "Time is Captured" "$vlc_filename: $timecode"
	# TODO (0) fix this path to be dynamic
	echo $vlc_filename, $timecode >>~/Dokumente/Dictionnary/VLC_saved_time.txt
	echo /home/mani/Dokumente/active_vocabulary/open_sub_in_dict/LearnFromSubtitles.py "$vlc_filename" "$timecode"
	# TODO (0) fix this path to be dynamic
	/home/parkdepot/Dokumente/Algorithms/german_active_vocab/open_sub_in_dict/LearnFromSubtitles.py "$vlc_filename" "$timecode"
else
	echo "no data from vlc"
	notify-send "no data from vlc"
fi
