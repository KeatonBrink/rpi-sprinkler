import calendar
import configparser
import datetime
import json
import os
import requests
import sys

from time import sleep
import RPi.GPIO as GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)


class SprinklerState:
  def init(self):
    pass

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

# Runs sprinkler
def run_sprinkler(config):
  pin = int(config['gpio_starter'])
  led = int(config['gpio_led1'])
  runtime = float(config['runtime_min'])
  with open(config['log_file'],'a') as log_file:
    try:
      GPIO.setup((pin, led), GPIO.OUT)
      log_file.write('%s: Starting sprinkler\n' % datetime.datetime.now())
      GPIO.output((pin,led), GPIO.HIGH)
      sleep(runtime * 60) 
      log_file.write('%s: Stopping sprinkler\n' % datetime.datetime.now())
      GPIO.output((pin,led), GPIO.LOW)
    except Exception as ex:
      log_file.write('%s: An error has occurred: %s \n' % (datetime.datetime.now(), ex.message))  
      GPIO.output((pin,led), GPIO.LOW)

# Main method
#   1.  Reads config file
#   2.  Checks past 24 hours of rainfall
#   3.  Runs sprinkler if rainfall falls below threshold
def main(): 
  # Load configuration file  
  config = load_config()
    
  with open(config['log_file'],'a') as log_file:
    # Get past 24 hour precip
    rainfall = get_precip_in_window(config)
    if rainfall is None:
      log_file.write('%s: Error getting rainfall amount, setting to 0.0 mm\n' % datetime.datetime.now())
      rainfall = 0.0
    else:
      log_file.write('%s: Rainfall: %f in\n' % (datetime.datetime.now(), rainfall))
    
  # If this is less than rain_threshold_mm run sprinkler
  if rainfall <= float(config['rain_threshold_mm']):
    run_sprinkler(config)
    
# Runs without checking rainfall
def force_run():
  config = load_config()
  run_sprinkler(config)
  
# Sets all GPIO pins to GPIO.LOW.  Should be run when the 
# raspberry pi starts.
def init():
    config = load_config()
    pin = int(config['gpio_starter'])
    led = int(config['gpio_led1'])
    GPIO.setup((pin, led), GPIO.OUT)
    GPIO.output((pin,led), GPIO.LOW)      
    
if __name__ == "__main__":
  if len(sys.argv) == 1:
    # Standard mode
    main()
  elif len(sys.argv) == 2 and sys.argv[1] == 'force':
    # Runs sprinkler regardless of rainfall
    force_run()
  elif len(sys.argv) == 2 and sys.argv[1] == 'init':
    # Sets pin and led GPIOs to GPIO.LOW
    init()
  else:
    print("Unknown inputs", sys.argv)
        
        
    
    
    
    
