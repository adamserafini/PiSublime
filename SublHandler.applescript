on open location input_url
	do shell script "
	URL=" & quoted form of input_url & "
	FILE_PATH=$(echo \"$URL\" | sed -n 's/.*url=file:\\/\\/\\([^&]*\\).*/\\1/p')
	LINE=$(echo \"$URL\" | sed -n 's/.*line=\\([0-9]*\\).*/\\1/p')
	if [ -n \"$FILE_PATH\" ]; then
		if [ -n \"$LINE\" ]; then
			/Applications/Sublime\\ Text.app/Contents/SharedSupport/bin/subl \"$FILE_PATH:$LINE\"
		else
			/Applications/Sublime\\ Text.app/Contents/SharedSupport/bin/subl \"$FILE_PATH\"
		fi
	fi
	"
end open location
