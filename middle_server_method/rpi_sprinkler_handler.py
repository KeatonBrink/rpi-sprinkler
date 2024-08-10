from flask import Flask, render_template, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
# import RPi.GPIO as GPIO
from datetime import datetime, timedelta
import configparser
import os
import requests
from time import sleep
import json

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
    server_url = config['server_address'] + '/rpi-polling'

    try:
        curStat = sprinkler_status["status"]

        payload = {"SprinklerStatus": curStat}
        headers = {"Content-Type": "application/json"}

        response = requests.post(server_url, data=json.dumps(payload), headers=headers)
        print(response.json())
        # headers = {'Content-Type': 'application/json'}
        # data = json.dumps({'SprinklerStatus': curStat})
        
        # print(data)
        # response = requests.post(server_url + '/rpi-polling', headers=headers, data=data)

        print("Sprinkler status: ", sprinkler_status)

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
        if response['setSprinkler'] == 1:
            turn_on_sprinkler()
        elif response['setSprinkler'] == 2:
            turn_off_sprinkler()
        elif response['setSprinkler'] != 0:
            print(f"Error getting response {response['setSprinkler']}")
    except Exception as e:
        print(f"Error getting response from server: {e}")

    print("End of get_update_from_server")

def post_logs():
    # Post the logs to the server
    # This can be done using a POST request to the server
    # The logs should be sent as a JSON object with the key "logs"
    # Example request: {"logs": ["Log 1", "Log 2", "Log 3"]}
    # The server should respond with a success message
    # Example response: {"message": "Logs received"}
    # The logs should be cleared after being sent
    server_url = config['server_address']

    try:
        headers = {'Content-Type': 'application/json'}
        data = json.dumps(session_logs)
        response = requests.post(server_url + '/rpi-logs', headers=headers, data=data)

        if response.status_code != 200:
            print("Error posting logs to server")
            print(response.status_code)
            print(response.text)
            return

    except Exception as e:
        print(f"Error posting logs to server: {e}")
    

if __name__ == '__main__':
    # Setup the scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(schedule_sprinklers, 'cron', hour=config['start_time'])  # Run daily at 6 AM
    scheduler.start()
    
    try:
        while True:
            get_update_from_server()
            post_logs()
            sleep(int(config['polling_frequency']))
            
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()