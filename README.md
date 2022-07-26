# recommendation-machine

play your recommendations.

## Usage

1. install dependencies from `requirements.txt` (i do this in a `venv`)
	- `pip install -r requirements.txt`
2. set configuration in `.env` file
	1. `mv .env.sample .env`
	2. set `WATCH_COMMAND` your preferred command to watch videos with `%(url)s` being replaced with the video url
		- e.g., `mpv %(url)s` would translate to `mpv https://youtube.com/watch?v=dQw...XcQ`
		- url is quoted automatically with `shlex.quote`
	3. set `LASTFM_SESSION_ID` to your last.fm session id cookie.  To find this:
		1. open [last.fm](https://www.last.fm) and log in (i did this on firefox so i can't guarantee it works for chrome et al.).
		2. open the web inspector (press F12)
		3. select the "Storage" tab
		4. select Cookies/last.fm from the left sidebar if it isn't already
		5. scroll down until you see the `sessionid` cookie
		6. select it, and copy it from the right panel (right-click or ctrl+c)
		7. paste this into the `.env` file, removing the `sessionid:` prefix
		8. ![visual of the instructions above](https://raw.githubusercontent.com/suaviloquence/recommendation-machine/dev/doc/find_session_id.png)
3. run `python recommendation_machine.py` 

## License

GPL3
