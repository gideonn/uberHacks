import json
import requests
import re

def loadConfig(config_file):
    try:
        config = json.load(open('config1.json'))
        print("Config loaded!")
    except:
        print("Couldn't load config. Exiting...")
        exit(-1)

    return config


def urlify(s):
    # Remove all non-word characters (everything except numbers and letters)
    s = re.sub(r"[^\w\s]", '', s)

    # Replace all runs of whitespace with a single dash
    s = re.sub(r"\s+", '+', s)

    return s


def getUserLocations(geoKey):
    add1 = urlify(input("Enter the \"FROM\" address:"))
    add2 = urlify(input("Enter the \"TO\" address:"))

    from_lat, from_lon = getLatLonFromAdd(add1, geoKey)
    to_lat, to_lon = getLatLonFromAdd(add2, geoKey)

    return [from_lat,from_lon],[to_lat,to_lon]


def getLatLonFromAdd(address, geoKey):
    resp = requests.get('https://maps.googleapis.com/maps/api/geocode/json?address=' + address + '&key=' + geoKey).json()

    print(resp)

    lat = resp['results'][0]['geometry']['location']['lat']
    lon = resp['results'][0]['geometry']['location']['lng']

    print("Lat and Longitude of address: ", resp['results'][0]['formatted_address'], " is: ", lat, lon)
    return lat, lon


#loc1 and loc2 are list. Indexes 0 and 1 are latitude and longitude
def getReqObject(start_loc,end_loc, access_token, prodID):
    headers = {'Authorization': "Bearer " + access_token,'Accept - Language':'en_US',
               'Content-Type':'application/json'}
    payload = {'product_id':'712b9d70-1254-4268-a275-33e487a4a54c','seats':'1','start_latitude': start_loc[0], 'start_longitude': start_loc[1],'end_latitude':end_loc[0],'end_longitude':end_loc[1]}

    r = requests.post("https://api.uber.com/v1.2/requests/estimate", data=json.dumps(payload), headers=headers)

    return r


def getPrice(r):
    data = r.json()
    print("Current price of Uber POOL is ", data['fare']['value'])


def isBelowThreshold():
    pass

if __name__ == '__main__':
    config_file = 'config.json'
    configDict = loadConfig(config_file)

    start_loc, end_loc = getUserLocations(configDict['geoKey'])
    reqObj = getReqObject(start_loc, end_loc, configDict['access_token'],'todo-prodID')

    getPrice(reqObj)
