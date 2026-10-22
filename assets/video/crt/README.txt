Footage for the rear wall's CRTs goes in this folder (any of .mp4 .mov .mkv .webm .avi .m4v
.mpg .mpeg .gif). Files are used in name order (currently the director's clips 01-08).

Then run:

    python tools/make_crt_video.py

It writes canvas/: stream.mp4 (every clip, one after another, as one clean 960 x 540 stream at the
film's 30 fps) and manifest.json (which screen starts on which clip). Every CRT is its own monitor
playing the stream from its own clip, in the approved treatment (cold tint, light scanlines; see
docs/look.md, the lyric section, "Footage"). The canvas folder must travel with the project to the
render machine, or be made there with the tool. While a line of the lyric is on the CRTs it takes
priority.
