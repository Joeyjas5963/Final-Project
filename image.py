import googlemaps

KEY = 'AIzaSyBa7_tGiDTn4v4PQAYwWc5umPhg0vaIN3E'

HEAD = 'https://maps.googleapis.com/maps/api/staticmap?'


def combine(dct):
    return '|' + str(dct['lat']) + ',' + str(dct['lng'])


def map_image(d, o):

    gmaps = googlemaps.Client(key=KEY)

    dest = gmaps.geocode(d)
    origin = gmaps.geocode(o)

    dest_add = dest[0]['formatted_address']
    origin_add = origin[0]['formatted_address']

    directions = gmaps.directions(dest_add, origin_add, transit_mode='train')[0]

    path = combine(directions['legs'][0]['start_location'])

    steps = directions['legs'][0]['steps']

    for step in steps:
        path += combine(step['end_location'])

    link = HEAD + 'size=400x400&path=color:0x0000ff|weight:5' + path + '&key=' + KEY

    return link

def main():

    d = 'Millis, MA'
    o = 'Boston, MA'
    link = map_image(d, o)
    print(link)


main()