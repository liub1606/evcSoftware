from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from time import time_ns

app = Flask(
	__name__,
	static_url_path='',
	static_folder="tel-interface/dist/"
)
CORS(app)
records = []


@app.route("/", methods=["GET"])
def root():
	return app.send_static_file("index.html")

@app.route("/new-entries", methods=["POST"])
def new_entry():
	global records
	print(request.json)
	records += request.json["records"]
	return '', 200

@app.route("/get-entries", methods=["GET"])
def get_entry():
	start_str = request.args.get("start")
	if start_str is None:
		return 418 # ik this is the wrong response but it brings me so much joy... im sure nobody in the future will spend hours debugging because of this one choice :3
	start = int(start_str)
	return jsonify({"records": records[start:], "upto": len(records)}), 200
