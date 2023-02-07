
import json
from flask import Flask, request
from flask import Flask, render_template
import paho.mqtt.client as mqtt

MESSAGE_LOG_MAX_LENGTH:int = 2000

app = Flask(__name__)

client_tower01 = mqtt.Client()
client_status = mqtt.Client()

humidity:str = ""
message_log:str = ""
is_new_message:bool = False
is_pump_on:bool = False
is_system_on:bool = False
is_led_on:bool = False

def main():
	global client_tower01
	global client_status

	client_tower01.on_message = _on_got_tower_message
	client_tower01.connect("192.168.1.125", port=1883)
	client_tower01.subscribe("#")
	client_tower01.loop_start()

	client_status.connect("192.168.1.125", port=1883)
	client_status.subscribe("stat/tower_01_monitor/STATUS8")
	client_status.on_message = _on_got_status_message
	client_status.loop_start()

	app.run()


@app.route("/", methods=["GET","POST"])
def index() -> str:
	"""
	The webpage ui for the aquaponics system.
	"""
	global is_pump_on
	global message_log

	if request.method == 'POST':
		if 'system_on' in request.form:
			system_on()
		elif 'system_off' in request.form:
			system_off()
		elif 'led_on' in request.form:
			led_on()
		elif 'led_off' in request.form:
			led_off()

	return render_template(
		"index.html",
		pump_status=is_pump_on,
		message_log=message_log,
	)


def led_off():
	"""
	Turns the aquaponics sun lamp off.
	"""
	client_tower01.publish("cmnd/tower01_led/POWER", payload="OFF")


def led_on():
	"""
	Turns the aquaponics sun lamp on.
	"""
	client_tower01.publish("cmnd/tower01_led/POWER", payload="ON")


def pump_off():
	"""
	Turns the aquaponics pump off.
	"""
	client_tower01.publish("cmnd/tower_01_pump/POWER", payload="OFF")


def pump_on():
	"""
	Turns the aquaponics pump on.
	"""
	client_tower01.publish("cmnd/tower_01_pump/POWER", payload="ON")


def system_off():
	"""
	Turns the aquaponics system off.
	"""
	client_tower01.publish("tower_01/enabled", payload=False)


def system_on():
	"""
	Turns the aquaponics system on.
	"""
	client_tower01.publish("tower_01/enabled", payload=True)


@app.route('/message', methods=['GET'])
def _get_message():
	global message_log
	return message_log


@app.route('/state', methods=['GET'])
def _get_state():
	global humidity
	global is_pump_on
	global is_new_message
	global is_system_on
	global is_led_on

	payload = {
		"humidity": humidity,
		"is_new_message": is_new_message,
		"is_pump_on": is_pump_on,
		"is_system_on": is_system_on,
		"is_led_on": is_led_on,
	}
	is_new_message = False
	return payload


@app.route('/led_off', methods=['POST'])
def _on_led_off():
	assert request.method == 'POST'
	led_off()
	return 200


@app.route('/led_on', methods=['POST'])
def _on_led_on():
	assert request.method == 'POST'
	led_on()
	return 200


@app.route('/pump_off', methods=['POST'])
def _on_pump_off():
	assert request.method == 'POST'
	pump_off()
	return 200


@app.route('/pump_on', methods=['POST'])
def _on_pump_on():
	assert request.method == 'POST'
	pump_on()
	return 200


@app.route('/system_off', methods=['POST'])
def _on_system_off():
	assert request.method == 'POST'
	system_off()
	return 200


@app.route('/system_on', methods=['POST'])
def _on_system_on():
	assert request.method == 'POST'
	system_on()
	return 200


def _on_got_tower_message(client, userdata, msg):
	"""
	Handles messages received.
	"""
	global message_log
	global is_new_message
	global is_pump_on
	global is_system_on
	global is_led_on
	global MESSAGE_LOG_MAX_LENGTH

	message_log = f"{msg.topic}: {msg.payload.decode('UTF-8')}\n{message_log}"
	message_log = message_log[:min(len(message_log), MESSAGE_LOG_MAX_LENGTH)]
	is_new_message = True
			
	# Extract the pump status
	if msg.topic == "stat/tower_01_pump/POWER":
		is_pump_on = msg.payload.decode('UTF-8') == "ON"

	# Extract the system status 
	if msg.topic == "tower_01/enabled":
		is_system_on = msg.payload.decode('UTF-8') == "True" \
			or msg.payload.decode('UTF-8') == "ON"
	
	# Extract the LED status 
	if msg.topic == "stat/tower01_led/POWER":
		is_led_on = msg.payload.decode('UTF-8') == "ON"


def _on_got_status_message(client, userdata, msg):
	global humidity
	# Extract the humidity value from the JSON payload
	payload = json.loads(msg.payload)
	humidity = payload.get("StatusSNS", {}).get("ANALOG", {}).get("A0", "N/A")
	humidity = min((719 - float(humidity))/421 * 100, 100)
    

if __name__ == "__main__":
	main()