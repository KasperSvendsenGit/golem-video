This is a sample program that uses golem.network to transcode videos using HandBrake.

As this is a sample, the configuration is limited. The video job can accept any HandBrake default preset.

The front-end is terrible, I know that. I'm bad at front-end to begin with and I also did this with Python Flask to try something new.

**web server**
flask run

**golem job**
video.py [-h] [--subnet-tag SUBNET_TAG] [--log-file LOG_FILE] input_file --presets "A,B,C"

example:
video.py input.mp4 --presets "Fast 480p30"
