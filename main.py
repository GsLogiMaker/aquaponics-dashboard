
from flask import Flask

app = Flask(__name__)

@app.route("/")
def index() -> str:
	return """

	<h1>Aquaponics System Control</h1>
	
	System <button>On</button><button>Off</button>
	
	"""


if __name__ == "__main__":
	app.run(debug=True)