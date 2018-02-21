import json
from pprint import pprint
import requests
import re
import time
import threading
from twilio.rest import Client


class Uber:

    def __init__(self, config_file):
        self.lat = 0
        self.lon = 0
        self.currPrice = 0.0
        self.threshold = 0.0
        self.start_loc = []
        self.end_loc = []
        self.fare_id = ""
        self.product_id = ""
        self.request_id = ""
        self.cabsDict = {}
        self.configDict = self.loadConfig(config_file)
        pprint(self.configDict)
        self.TwilioClient = Client(self.configDict['twilio_account_sid'], self.configDict['twilio_auth_token'])


    def loadConfig(self, config_file):
        try:
            config = json.load(open(config_file))
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

        print("Fetching available cabs in the area...")
        availCabs = self.getAllCabs()
        print('*' * 10, "Select the Cab Type:", '*' * 10)
        for cab_type in self.cabsDict.keys():
            print(cab_type)
        print('*' *50)
        reqCabType = str.lower(input("Enter the name of the cab that you want to request: "))
        self.product_id = self.cabsDict[reqCabType]

        return True


    def getLatLonFromAdd(self, address):
        resp = requests.get(
            'https://maps.googleapis.com/maps/api/geocode/json?address=' + address + '&key=' + self.configDict[
                'geoKey']).json()

        lat = resp['results'][0]['geometry']['location']['lat']
        lon = resp['results'][0]['geometry']['location']['lng']

        print("Lat and Longitude of address: ", resp['results'][0]['formatted_address'], " is: ", lat, lon)
        return lat, lon


    def getAllCabs(self):
        headers = {'Authorization': "Bearer " + self.configDict['uber_access_token'], 'Accept - Language': 'en_US',
                   'Content-Type': 'application/json'}
        url = "https://sandbox-api.uber.com/v1.2/products?latitude={}&longitude={}".format(self.start_loc[0], self.start_loc[1])
        # print(url)
        r = requests.get(url, headers=headers)
        # print(r.text)
        data = r.json()

        for entries in data['products']:
            self.cabsDict[str.lower(entries['display_name'])] = entries['product_id']


    def getPrice(self):
        headers = {'Authorization': "Bearer " + self.configDict['uber_access_token'], 'Accept - Language': 'en_US',
                   'Content-Type': 'application/json'}
        payload = {'product_id': self.product_id, 'seats': '1',
                   'start_latitude': self.start_loc[0], 'start_longitude': self.start_loc[1],
                   'end_latitude': self.end_loc[0], 'end_longitude': self.end_loc[1]}

        r = requests.post("https://sandbox-api.uber.com/v1.2/requests/estimate", data=json.dumps(payload), headers=headers)
        if r.status_code == 200:
            data = r.json()
            print("Current price of Uber POOL is $", data['fare']['value'])
            self.currPrice = float(data['fare']['value'])
            self.fare_id = data['fare']['fare_id']
            return r
        else:
            print("Error in calling Uber cab lookup API")
            exit(-1)


    def checkAndBookCab(self):
        while True:
            if self.currPrice <= self.threshold:
                print("Current price : $", self.currPrice, " is less than the set threshold: $", self.threshold)
                message = "Current price : $" + str(self.currPrice) + " is less than the set threshold: $" + str(
                    self.threshold)
                self.notifyUser(message)
                decision = str.lower(input("Should I go ahead and book the cab(yes/no)? "))
                if decision == 'y' or decision == 'yes':
                    while True:
                        resp = self.confirmCab()
                        # if resp == success, send an SMS notification
                        if resp is True:
                            # sleep for 30 seconds, fetch the cab booked details and send an SMS with that info
                            print("Waiting 30s for the cab confirmation...")
                            time.sleep(30)
                            sts = self.getCabDetails()
                            break
                        else:
                            print("Couldn't book requested cab, retrying in 30s...\nYou can press Ctrl+C to quit anytime.")
                            time.sleep(30)
                else:
                    print("Okay, not booking the cab. Retrying in a while...")
                    # TODO
                    # print("Do you want to update the threshold value ?")
                    self.getPrice()
                    # Ask to update threshold value
            else:
                print("Current price :", self.currPrice, " is more than the set threshold: ", self.threshold)
                message = "Current price :" + str(self.currPrice) + " is more than the set threshold: " + str(
                    self.threshold)
                self.notifyUser(message)

                print("Retrying in a while...")
            print("Press Ctrl+C to exit anytime you want the script to stop...")
            time.sleep(self.configDict['freq_check'])


    def notifyUser(self, msg):
        print("Value of notif: ".format(self.configDict['enable_notif']))
        if self.configDict['enable_notif'] == "True":
            message = self.TwilioClient.messages.create(
                to=self.configDict['cellno'],
                from_=self.configDict['twilio_cellno'],
                body=msg)
        else:
            print("Notification not enabled in config. Message is: ".format(msg))

    def confirmCab(self):
        headers = {'Authorization': "Bearer " + self.configDict['uber_access_token'],
                   'Content-Type': 'application/json'}
        payload = {'product_id': '712b9d70-1254-4268-a275-33e487a4a54c', 'start_latitude': self.start_loc[0],
                   'start_longitude': self.start_loc[1], 'end_latitude': self.end_loc[0],
                   'end_longitude': self.end_loc[1], 'seat_count': '1',
                   'fare_id': self.fare_id}
        url = "https://sandbox-api.uber.com/v1.2/requests"
        print("DEBUG | Fare ID: ", self.fare_id)
        r = requests.post(url, data=json.dumps(payload), headers=headers)
        print("DEBUG confirmCab", r.json())
        data = r.json()
        pprint("DATA FOR CONFIRM CAB:")
        pprint(data)
        if r.status_code == 200:
            self.request_id = data['request_id']
            print("Request ID is: ", self.request_id)
            print("Fare ID is: ", self.fare_id)
            message = "Booked the cab, fetching details..."
            self.notifyUser(message)
            return True
        elif data['errors'][0]['code'] == 'current_trip_exists':
            self.getCabDetails()
        else:
            print("DEBUG | Book cab failed: ", data)
            return False


    def getCabDetails(self):
        headers = {'Authorization': "Bearer " + self.configDict['uber_access_token']}

        while True:
            r = requests.get("https://sandbox-api.uber.com/v1.2/requests/current", headers=headers)
            data = r.json()
            print("DEBUG getCabDetails: ", data)
            if data['status'] == 'accepted':
                message = "Here are the details of the booking...\n Current booking status: {},\nSurge multiplier: {},\nDriver Phone: {},\nRating: {},\nName: {},\nCar Make: {},\nLicense Plate: {},\nPickup ETA: {}" \
                    .format(data['status'], data['surge_multiplier'], data['driver']['phone_number'],
                            data['driver']['rating'], data['driver']['name'], data['vehicle']['make'],
                            data['vehicle']['license_plate'], data['pickup']['eta'])
                self.notifyUser(message)
                return True
            elif data['status'] == 'processing':
                self.debug_acceptRide()
                time.sleep(5)
            else:
                print("Ride not confirmed yet, rechecking again...")
                message = "Ride not confirmed yet, rechecking again in 20 seconds..."
                print("DEBUG | FareID: ", self.fare_id)
                self.notifyUser(message)
                self.debug_acceptRide()
                time.sleep(20)


    def debug_acceptRide(self):
        headers = {'Authorization': "Bearer " + self.configDict['uber_access_token'], 'Content-Type': 'application/json'}
        payload = {'status': 'accepted'}
        print("Accepting ride with request no. {}, ".format(self.request_id))
        url = "https://sandbox-api.uber.com/v1.2/sandbox/requests/{}".format(self.request_id)
        r = requests.post(url, data=json.dumps(payload), headers=headers)
        print("ACCEPT CAB CODE: ", r.status_code)


    def cancelRide(self):
        headers = {'Content-Type': 'application/json', 'Authorization': "Bearer " + self.configDict['uber_access_token']}
        payload = {'fare_id': self.fare_id, 'product_id': self.product_id, 'start_latitude': self.start_loc[0], 'start_longitude': self.start_loc[1], 'end_latitude': self.end_loc[0], 'end_longitude': self.end_loc[1] }
        print("Cancelling ride with request no. {}, ".format(self.request_id))
        r = requests.post("https://sandbox-api.uber.com/v1.2/requests", data=json.dumps(payload), headers=headers)
        print(r.json())

if __name__ == '__main__':
    config_file = '../config/config1.json'
    # configDict = loadConfig(config_file)

    uber_inst = Uber(config_file)
    uber_inst.getUserLocationsAndThreshold()
    uber_inst.getPrice()

    uber_inst.checkAndBookCab()
    uber_inst.cancelRide()