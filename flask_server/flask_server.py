from flask import Flask, render_template, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import RPi.GPIO as GPIO
from datetime import datetime, timedelta
import configparser
import os
from time import sleep

app = Flask(__name__)

production = False

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

# GPIO setup
if production:
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(int(config['gpio_starter']), GPIO.OUT)  # Example GPIO pin for sprinkler 1



def turn_on_sprinkler():
    with open(config['log_file'],'a') as log_file:
        try:
            if production:
                GPIO.output(int(config['gpio_starter']), GPIO.HIGH)
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
            if production:
                GPIO.output(int(config['gpio_starter']), GPIO.LOW)
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

@app.route('/')
def index():
    return render_template('index.html', status=sprinkler_status["status"], logs=session_logs[::-1])

@app.route('/template/style.css')
def css():
    return render_template('style.css')

@app.route('/sprinkler', methods=['POST'])
def control_sprinkler():
    action = request.json.get('action')
    if action == 'on':
        turn_on_sprinkler()
        return jsonify({"status": "Sprinkler turned on"})
    elif action == 'off':
        turn_off_sprinkler()
        return jsonify({"status": "Sprinkler turned off"})
    else:
        return jsonify({"status": "Invalid action"}), 400
    
@app.route('/logs', methods=['GET'])
def get_logs():
    return jsonify(session_logs[::-1])

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify(sprinkler_status)

@app.route("/all_records", methods=['GET'])
def get_records():
    with open(config['log_file'],'r') as log_file:
        return jsonify(log_file.readlines()[::-1])

if __name__ == '__main__':
    # Setup the scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(schedule_sprinklers, 'cron', hour=config['start_time'])  # Run daily at 6 AM
    scheduler.start()
    
    # Start the Flask server
    try:
        app.run(host='0.0.0.0', port=5000)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()