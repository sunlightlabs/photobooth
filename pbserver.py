import ConfigParser
import json
import mimetypes
import os
import re
import sys
import time

from gevent import http, pywsgi
from tornado import web, websocket    
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application
import flickr
import qrcode

from pb import PhotoBooth

def ensure_path(path):
    if not os.path.exists(path):
        os.makedirs(path)

config = ConfigParser.ConfigParser()
config.read('photobooth.conf')

pwd = os.path.abspath(os.path.dirname(__file__))

static_path = os.path.join(pwd, 'static')

strips_path = os.path.join(static_path, 'photos', 'strips')
ensure_path(strips_path)

photos_path = os.path.join(static_path, 'photos', 'raw')
ensure_path(photos_path)

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

class PhotoboothHandler(web.RequestHandler):
    def get(self):
        self.finish(load_template('base.html'))
        
class PhotoboothInitHandler(web.RequestHandler):
    def get(self):
        data = {'photos': []}
        for filename in os.listdir(strips_path):
            if not filename.startswith('.'):
                data['photos'].append(filename)
        self.finish(data)

class PhotoboothWebSocket(websocket.WebSocketHandler):
    
    def open(self):
        print "opened"
    
    def on_close(self):
        print "closed"
    
    def send(self, params):
        self.write_message(json.dumps(params))
    
    def on_message(self, message):
        
        # create new photo set
        photoset = photo_booth.new_set()
        
        self.send({'action': 'preset'})
        
        # take each photo
        count = config.getint('photobooth', 'count')
        for i in xrange(count):
            
            # pre-photo message
            self.send({
                'action': 'prephoto',
                'index': i,
                'count': count,
            })
            
            # take photo
            photo_booth.take_photo(photoset)
            photo_path = photoset['photos'][-1]
            
            # post-photo message
            self.send({
                'action': 'postphoto',
                'index': i,
                'count': count,
                'filename': photo_path.split('/')[-1],
                'localPath': photo_path,
            })
            
        self.send({'action': 'postset'})
        
        # combine into photo strip and delete originals
        strip_path = photo_booth.printout(photoset)
        photo_booth.cleanup(photoset)
        
        # upload to Flickr if enabled
        if config.get('photobooth', 'upload') == '1':
            self.send({'action': 'processing'})
            flickr_url = flickr.upload(strip_path)
            time.sleep(2)
        else:
            flickr_url = None
        
        # return final response
        self.send({
            'action': 'strip',
            'photoId': photoset['id'],
            'localPath': strip_path,
            'flickrUrl': flickr_url or '',
            'qrCodeUrl': qrcode.image_url(flickr_url or 'http://sunlightlabs.com/photobooth/'),
        })
        
        # close websocket connection
        self.send({'action': 'close'})
    
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
        
        urls = [
            ("/", PhotoboothHandler),
            ("/init", PhotoboothInitHandler),
            ("/pb", PhotoboothWebSocket),
            ("/(.*)", web.StaticFileHandler, {'path': static_path}),
        ]
        
        server = HTTPServer(Application(urls))
        server.bind(8000)
        server.start(4)
        IOLoop.instance().start()
    
    serve_photobooth()