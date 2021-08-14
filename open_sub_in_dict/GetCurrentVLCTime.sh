#!/bin/bash

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

	echo "vlc_filename: ${vlc_filename}"
	notify-send "Time is Captured" "$vlc_filename: $timecode"
	echo $vlc_filename, $timecode >>~/Dokumente/Dictionnary/VLC_saved_time.txt
	/home/mani/Dokumente/active_vocabulary/open_sub_in_dict/Sub_learner.py "$vlc_filename" "$timecode"
else
	echo "no data from vlc"
	notify-send "no data from vlc"
fi
