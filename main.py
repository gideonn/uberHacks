import json
import requests
import re
import time
import threading
from twilio.rest import Client


class Uber:

    def __init__(self, config_file):
        self.lat = 0
        self.lon = 0
        self.start_loc = []
        self.end_loc = []
        self.configDict = self.loadConfig(config_file)
        self.currPrice = 0.0
        self.threshold = 0.0


    def loadConfig(self, config_file):
        try:
            config = json.load(open('config1.json'))
            print("Config loaded!")
        except:
            print("Couldn't load config. Exiting...")
            exit(-1)

        return config


    def urlify(self, s):
        # Remove all non-word characters (everything except numbers and letters)
        s = re.sub(r"[^\w\s]", '', s)

        # Replace all runs of whitespace with a single dash
        s = re.sub(r"\s+", '+', s)

        return s


    def getUserLocationsAndThreshold(self):
        add1 = self.urlify(input("Enter the \"FROM\" address: "))
        add2 = self.urlify(input("Enter the \"TO\" address: "))

        self.threshold = float(input("Enter the threshold amount:"))
        from_lat, from_lon = self.getLatLonFromAdd(add1)
        to_lat, to_lon = self.getLatLonFromAdd(add2)

        self.start_loc = [from_lat, from_lon]
        self.end_loc = [to_lat, to_lon]

        return True


    def getLatLonFromAdd(self, address):
        resp = requests.get('https://maps.googleapis.com/maps/api/geocode/json?address=' + address + '&key=' + self.configDict['geoKey']).json()

        # print(resp)

        lat = resp['results'][0]['geometry']['location']['lat']
        lon = resp['results'][0]['geometry']['location']['lng']

        print("Lat and Longitude of address: ", resp['results'][0]['formatted_address'], " is: ", lat, lon)
        return lat, lon


    #loc1 and loc2 are list. Indexes 0 and 1 are latitude and longitude
    def getPrice(self, prodID):
        headers = {'Authorization': "Bearer " + self.configDict['uber_access_token'],'Accept - Language':'en_US',
                   'Content-Type':'application/json'}
        payload = {'product_id':'712b9d70-1254-4268-a275-33e487a4a54c','seats':'1','start_latitude': self.start_loc[0], 'start_longitude': self.start_loc[1],'end_latitude':self.end_loc[0],'end_longitude':self.end_loc[1]}

        try:
            r = requests.post("https://api.uber.com/v1.2/requests/estimate", data=json.dumps(payload), headers=headers)
            if r.status_code == 200:
                data = r.json()
                print("Current price of Uber POOL is ", data['fare']['value'])
                self.currPrice = float(data['fare']['value'])
                return r
            else:
                print("Error in calling Uber cab lookup API")
                exit(-1)
        except:
            print("Couldn't call API, exiting...")
            exit(-1)


    def checkAndBookCab(self):
        try:
            while True:
                if self.currPrice <= self.threshold:
                    print("Current price : $", self.currPrice, " is less than the set threshold: $", self.threshold)
                    decision = input("Should I go ahead and book the cab?")
                    if decision == 'Y':
                        resp = self.confirmCab()
                        #if resp == success, send an SMS notification

                        #sleep for 15 seconds, fetch the cab booked details and send an SMS with that info
                        details = self.getCabDetails()
                    else:
                        print("Okay, not booking the cab. Retrying in a while...")
                        #TODO
                        # print("Do you want to update the threshold value ?")
                        self.getPrice('')
                        #Ask to update threshold value
                else:
                    print("Current price :", self.currPrice, " is more than the set threshold: ", self.threshold)
                    print("Retrying in a while...")
                print("Press Ctrl+C to exit anytime you want the script to stop...")
                time.sleep(self.configDict['freq_check'])
        except:
            exit(0)

    def notifyUser(cell, message):
        pass


    def confirmCab(self):
        pass


    def getCabDetails(self):
        pass



if __name__ == '__main__':
    config_file = 'config.json'
    # configDict = loadConfig(config_file)

    uber_inst = Uber(config_file)
    uber_inst.getUserLocationsAndThreshold()
    uber_inst.getPrice('todo-prodID')

    uber_inst.checkAndBookCab()

