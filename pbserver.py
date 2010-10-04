from gevent import http, pywsgi
from geventwebsocket.handler import WebSocketHandler
from pb import PhotoBooth
import ConfigParser
import flickr
import json
import mimetypes
import os
import qrcode
import re
import sys
import time

config = ConfigParser.ConfigParser()
config.read('photobooth.conf')

pwd = os.path.abspath(os.path.dirname(__file__))
strips_path = os.path.join(pwd, 'static', 'photos', 'strips')
photos_path = os.path.join(pwd, 'static', 'photos', 'raw')
templates_path = os.path.join(pwd, 'templates')
templates = {}

# create photo booth

photo_booth = PhotoBooth()
photo_booth.lomo_darkness = config.getfloat('photobooth', 'lomo_darkness')
photo_booth.lomo_saturation = config.getfloat('photobooth', 'lomo_saturation')

# template stuff

def autoload_templates():
    for filename in os.listdir(templates_path):
        load_template(path, cache=True)

def load_template(filename, cache=False):
    path = os.path.join(templates_path, filename)
    template = templates.get(path, None)
    if not template:
        f = open(path)
        template = f.read()
        f.close()
        if cache:
            templates[filename] = template
    return template

# websocket utils

def send(ws, params):
    ws.send(json.dumps(params))

# apps

def websocket_app(environ, start_response):
    
    path = environ["PATH_INFO"].rstrip('/')
    
    if not path:
        
        start_response("200 OK", [('Content-Type', 'text/html')])
        return load_template('base.html')
    
    elif path == '/init':
        
        data = {'photos': []}
        
        for filename in os.listdir(strips_path):
            data['photos'].append(filename)
        
        start_response("200 OK", [('Content-Type', 'application/json')])
        return json.dumps(data)
    
    elif path == '/pb':
        
        ws = environ["wsgi.websocket"]
        #message = ws.wait()
        
        # create new photo set
        photoset = photo_booth.new_set()
        
        send(ws, {'action': 'preset'})
        
        # take each photo
        count = config.getint('photobooth', 'count')
        for i in xrange(count):
            
            # pre-photo message
            send(ws, {
                'action': 'prephoto',
                'index': i,
                'count': count,
            })
            
            # take photo
            photo_booth.take_photo(photoset)
            
            # post-photo message
            send(ws, {
                'action': 'postphoto',
                'index': i,
                'count': count,
                'filename': path.split('/')[-1],
                'localPath': path,
            })
            
        send(ws, {'action': 'postset'})
        
        # combine into photo strip and delete originals
        strip_path = photo_booth.printout(photoset)
        photo_booth.cleanup(photoset)
        
        # upload to Flickr if enabled
        if config.get('photobooth', 'upload') == '1':
            send(ws, {'action': 'processing'})
            flickr_url = flickr.upload(strip_path)
            time.sleep(2)
        
        # return final response
        ws.send(json.dumps({
            'action': 'strip',
            'photoId': photoset['id'],
            'localPath': strip_path,
            'flickrUrl': flickr_url,
            'qrCodeUrl': qrcode.image_url(flickr_url),
        }))
        
        # close websocket connection
        ws.send(json.dumps({'action': 'close'}))
    
    start_response("404 NOT FOUND", [('Content-Type', 'text/plain')])
    return []
    
def static_app(request):

    path = os.path.join(pwd, 'static', request.uri.strip('/'))

    if not os.path.exists(path):
        request.add_output_header('Content-Type', 'text/plain')
        request.send_reply(404, "NOT FOUND", '')

    f = open(path)
    data = f.read()
    f.close()

    ct = mimetypes.guess_type(path)[0]
    
    request.add_output_header('Content-Type', ct or 'text/plain')
    request.send_reply(200, "OK", data)



if __name__ == '__main__':

    def serve_photobooth():
        server = pywsgi.WSGIServer(('127.0.0.1', 8000), websocket_app, handler_class=WebSocketHandler)
        server.serve_forever()

    def serve_photos():
        http.HTTPServer(('127.0.0.1', 8001), static_app).serve_forever()
    
    args = sys.argv[1:]
    command = args[0] if args else None
    
    if command == 'app':
        serve_photobooth()
        
    elif command == 'static':
        serve_photos()
    
    else:
        print "Usage: pbserver.py (app|static)"
    