from flickrapi import shorturl
import datetime
import flickrapi
import pbserver

def upload(path):

    API_KEY = pbserver.config.get('flickr', 'api_key')
    API_SECRET = pbserver.config.get('flickr', 'api_secret')
    TOKEN = pbserver.config.get('flickr', 'auth_token')
    
    if not TOKEN:
        raise ValueError('invalid or missing token')
    
    flickr = flickrapi.FlickrAPI(API_KEY, API_SECRET, token=TOKEN)

    params = {
        'filename': path,
        'title': '%s' % datetime.datetime.now(),
        'is_public': pbserver.config.get('flickr', 'is_public'),
        'format': 'etree',
    }
    
    tags = pbserver.config.get('flickr', 'tags')
    if tags:
        params['tags'] = tags

    resp = flickr.upload(**params)
    photo_id = resp.find('photoid').text

    photoset_id = pbserver.config.get('flickr', 'photoset')
    if photoset_id:
        flickr.photosets_addPhoto(photoset_id=photoset_id, photo_id=photo_id)

    return shorturl.url(photo_id)
    

if __name__ == '__main__':
    
    API_KEY = pbserver.config.get('flickr', 'api_key')
    API_SECRET = pbserver.config.get('flickr', 'api_secret')

    flickr = flickrapi.FlickrAPI(API_KEY, API_SECRET)

    (token, frob) = flickr.get_token_part_one(perms='write')
    if not token:
        raw_input("Press ENTER after you authorized this program")
        
    print "auth_token:", flickr.get_token_part_two((token, frob))