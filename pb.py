from PIL import Image, ImageEnhance, ImageColor, ImageDraw
import json
import os
import subprocess
import uuid

PWD = os.path.abspath(os.path.dirname(__file__))

class PhotoBooth(object):
    
    def __init__(self, size=None, padding=20):
        
        if not size:
            size = (320, 240)
        
        self.size = size
        self.padding = padding
        
        mask = Image.open(os.path.join(PWD, 'mask.jpg'))
        mask = mask.resize(self.size)
        self.lomo_mask = mask
        
        self.lomo_darkness = 0.8
        self.lomo_saturation = 1.6
    
    def new_set(self):
        guid = uuid.uuid4().hex[:16]
        return {'id': guid, 'photos': []}
        
    def take_photo(self, photoset):
        
        filename = "%s-%s.jpg" % (photoset['id'], len(photoset['photos']) + 1)
        path = os.path.join(PWD, 'static', 'photos', 'raw', filename)
        subprocess.call(['isightcapture', path])
        
        photoset['photos'].append(path)
        
        return path
    
    def printout(self, photoset):
        
        count = len(photoset['photos'])
        width = self.size[0] + (self.padding * 2)
        height = (self.size[1] * count) + (self.padding * (count + 1))
        
        master = Image.new("RGB", (width, height))
        
        draw = ImageDraw.Draw(master)
        draw.rectangle(((0, 0), (width - 1, height - 1)), fill="#FFF", outline="#999")
        del draw
        
        for i, path in enumerate(photoset['photos']):
            im = Image.open(path)
            im = im.resize(self.size)
            im = self.lomoize(im)
            offset_x = self.padding
            offset_y = self.padding + (self.size[1] * i) + (self.padding * i)
            master.paste(im, (offset_x, offset_y))
            del im
            
        filename = "static/photos/strips/%s.jpg" % photoset['id']
        path = os.path.abspath(filename)
        
        master.save(path)
        del master
        
        return path
    
    def lomoize(self, image, darkness=None, saturation=None):
        darker = ImageEnhance.Brightness(image).enhance(darkness or self.lomo_darkness)
        saturated = ImageEnhance.Color(image).enhance(saturation or self.lomo_saturation)
        lomoized = Image.composite(saturated, darker, self.lomo_mask)
        return lomoized
    
    def cleanup(self, photoset):
        for path in photoset['photos']:
            os.unlink(path)


if __name__ == '__main__':
    
    pb = PhotoBooth()
    photoset = pb.new_set()
    
    for i in xrange(4):
        print "Pose for photo %s" % i
        pb.take_photo(photoset)
    
    # "print" photo strip and display filesystem path
    print photoset
    print pb.printout(photoset)
    
    pb.cleanup(photoset)