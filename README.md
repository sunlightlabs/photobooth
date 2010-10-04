# Photo Booth

## Installation

* Copy photobooth.example.conf to photobooth.conf
* Install the Python packages found in requirements.txt
* Install [PIL](http://www.pythonware.com/products/pil/)

## Settings

count
	The number of photos to take for a single strip.

upload
	1 to upload to Flickr (see settings below) or 0 to keep photos locally.

lomo_darkness
	Darkness setting of the lomo filter.

lomo_saturation
	Saturation setting of the lomo filter.

## Flickr upload

* [Create an API](http://www.flickr.com/services/api/) key for your account
* Edit photobooth.conf and set *api_key* and *api_secret* with the values from your Flickr API key
* Get your API token by running the following command from the photobooth directory:

	python flickr.py

* Copy the *auth_token* and paste into *auth_token* in photobooth.conf

Other settings Flickr settings:

is_public
	A value of 1 will make the uploaded photo public while 0 will keep it private.

photoset
	The ID of the Flickr photoset to which the photo will be added. Leave blank to not add to a photoset.

tags
	Tags to be added to the photo.

## Dry run

From the photobooth directory, run:

	python pb.py

If everything works, you should be prompted for each photo. The paths of the photos and the final strip will be printed to the screen. Photo strips will not be uploaded to Flickr when run with this command.

## Running it for real

Okay, so I don't know of a good way to server the static files from the same server as the WebSocket handler. The only way to get around this in the short time that I had was to run two separate servers: one for WebSocket and the other for static media. Open up two terminal sessions. In the first, run:

	python pbserver.py static

And in the second, run:

	python pbserver.py app

If everything worked, you can go to http://127.0.0.1:8000 and use the photobooth!
