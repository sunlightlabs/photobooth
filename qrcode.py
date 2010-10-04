from urllib import urlencode

BASE_URL = "http://chart.apis.google.com/chart"

def image_url(s):
    params = {
        'cht': 'qr',
        'chs': '200x200',
        'chl': s,
        'chld': 'Q|4',
    }
    return "%s?%s" % (BASE_URL, urlencode(params))
