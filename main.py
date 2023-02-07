
import json
from flask import Flask, request
from flask import Flask, render_template
import paho.mqtt.client as mqtt

app = Flask(__name__)

client_tower01 = mqtt.Client()
client_status = mqtt.Client()

humidity:str = ""
message_log:str = ""
pump_status:str = ""

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
	global pump_status
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
		pump_status=pump_status,
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


@app.route('/humidity', methods=['GET'])
def _get_humidity():
	global humidity
	return str(humidity)


@app.route('/pump_status', methods=['GET'])
def _get_pump_status():
	global pump_status
	return str(pump_status)


@app.route('/state', methods=['GET'])
def _get_state():
	global humidity
	global pump_status
	return {"humidity": humidity, "pump_status": pump_status}


@app.route('/system_on', methods=['POST'])
def _on_system_on():
	assert request.method == 'POST'
	system_on()


@app.route('/led_on', methods=['POST'])
def _on_led_on():
	assert request.method == 'POST'
	led_on()


@app.route('/led_off', methods=['POST'])
def _on_led_off():
	assert request.method == 'POST'
	led_off()


def _on_got_tower_message(client, userdata, msg):
	"""
	Handles messages received.
	"""
	global message_log
	global pump_status

	ignore = ["tele/tower_01_pump/STATE", "tele/tower_01_pump/SENSOR", "stat/tower_01_pump/STATUS8",
		"tele/tower_01_monitor/STATE", "tele/tower_01_monitor/SENSOR", "stat/tower_01_monitor/STATUS8", 
		"stat/tower_01_monitor/STATUS8", "cmnd/tower_01_monitor/status",
		"tele/tower01_led/STATE", "tele/tower01_led/SENSOR", "stat/tower01_led/STATUS8"]
	if "tower01" in msg.topic or "tower_01" in msg.topic:
		message_log = f"{message_log}\n{msg.payload.decode('UTF-8')}"
			
	# Extract the pump status from the JSON payload if the topic is correct
	print(msg.topic, msg.payload.decode('UTF-8'))
	if msg.topic == "stat/tower_01_pump/POWER":
		print("PUMP", msg.payload.decode('UTF-8'), msg.payload)
		pump_status = msg.payload.decode('UTF-8')
		message_log = f"{message_log}\n{msg.payload.decode('UTF-8')}"


def _on_got_status_message(client, userdata, msg):
	global humidity
	# Extract the humidity value from the JSON payload
	payload = json.loads(msg.payload)
	humidity = payload.get("StatusSNS", {}).get("ANALOG", {}).get("A0", "N/A")
    

if __name__ == "__main__":
	main()