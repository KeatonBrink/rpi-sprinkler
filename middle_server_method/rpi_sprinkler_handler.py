from flask import Flask, render_template, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
# import RPi.GPIO as GPIO
from datetime import datetime, timedelta
import configparser
import os
import requests
from time import sleep

# Shared state
sprinkler_status = {"status": "off"}

# Loads configuration file
def load_config(filename='config'):
  config = configparser.RawConfigParser()
  this_dir = os.path.abspath(os.path.dirname(__file__))
  config.read(this_dir + '/' + filename)
  if config.has_section('SprinklerConfig'):
      return {name:val for (name, val) in config.items('SprinklerConfig')}
  else:
      print('Unable to read file %s with section SprinklerConfig' % filename)
      print('Make sure a file named config lies in the directory %s' % this_dir)
      raise Exception('Unable to find config file')
config = load_config()
session_logs = []

current_job = None

# GPIO setup
# GPIO.setmode(GPIO.BCM)
# GPIO.setup(int(config['gpio_starter']), GPIO.OUT)  # Example GPIO pin for sprinkler 1



def turn_on_sprinkler():
    with open(config['log_file'],'a') as log_file:
        try:
            # GPIO.output(int(config['gpio_starter']), GPIO.HIGH)
            sprinkler_status["status"] = "on"
            print(f"Sprinkler turned on at {datetime.now()}")
            msg = f'{datetime.now()}: Starting sprinkler\n'
            log_file.write(msg)
            session_logs.append(msg)
        except Exception as ex:
            msg = f'{datetime.now()}: An error has occurred: {ex.message}\n'
            log_file.write(msg)
            session_logs.append(msg)  

def turn_off_sprinkler():
    with open(config['log_file'],'a') as log_file:
        try:
            # GPIO.output(int(config['gpio_starter']), GPIO.LOW)
            sprinkler_status["status"] = "off"
            print(f"Sprinkler turned off at {datetime.now()}")
            msg = f'{datetime.now()}: Stopping sprinkler\n'
            log_file.write(msg)
            session_logs.append(msg)
        except Exception as ex:
            msg = f'{datetime.now()}: An error has occurred: {ex.message}\n'
            session_logs.append(msg)  
            log_file.write(msg)


def schedule_sprinklers():
    today = datetime.today()
    if today.day % 2 == 1 or today.weekday() == 5:  # Odd days and Saturdays
        turn_on_sprinkler()
        # Schedule to turn off after 1 hour
        scheduler.add_job(turn_off_sprinkler, 'date', run_date=datetime.now() + (timedelta(hours=1) * config['water_duration']))

def get_update_from_server():
    print("Start get update from server")
    # Get the latest status from the server
    # This can be done using a GET request to the server
    # The server should return the status of the sprinkler
    # as a JSON object with the key "status"
    # Example response: {"status": "on"}
    # The response should be stored in the sprinkler_status variable
    # sprinkler_status = {"status": "on"}
    # Http request to the server
    server_url = config['server_address']

    # Here is the go code:
    # type Request struct {
	# 	IsSprinklerOn bool `json:"isSprinklerOn"`
	# }

	# var request Request

	# err := json.NewDecoder(r.Body).Decode(&request)
	# if err != nil {
	# 	http.Error(w, err.Error(), http.StatusBadRequest)
	# 	gologger.QueueMessage("Error decoding request")
	# 	return
	# }

	# s.isSprinklerOn = request.IsSprinklerOn

	# // The request will contain
	# // 0 if nothing should change
	# // 1 if the sprinkler should be on
	# // 2 if the sprinkler should be off
	# userRequestJson, err := json.Marshal(userRequest)
	# if err != nil {
	# 	http.Error(w, err.Error(), http.StatusInternalServerError)
	# 	gologger.QueueMessage("Error marshalling user request to JSON")
	# 	return
	# }
	# w.Header().Set("Content-Type", "application/json")
	# w.WriteHeader(http.StatusOK)
	# w.Write(userRequestJson)
	# userRequest.SetSprinkler = 0

    # Here is the python code:
    # First, send the expected json for the current status of the sprinkler
    print(sprinkler_status["status"] == "on")
    response = requests.get(server_url+'/rpi-polling', params={'sprinklerStatus': sprinkler_status["status"]})

    if response.status_code != 200:
        print("Error getting response from server")
        print(response.status_code)
        print(response.text)
        return

    print(response)
    # Then, get the response from the server
    response = response.json()
    print(response)
    # If the response is different from the current status, change the status of the sprinkler
    if response['isSprinklerOn'] == 1:
        turn_on_sprinkler()
    elif response['isSprinklerOn'] == 2:
        turn_off_sprinkler()

    print("End of get_update_from_server")
    

if __name__ == '__main__':
    # Setup the scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(schedule_sprinklers, 'cron', hour=config['start_time'])  # Run daily at 6 AM
    scheduler.start()
    
    # Start the Flask server
    try:
        while True:
            get_update_from_server()
            sleep(int(config['polling_frequency']))
            
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()