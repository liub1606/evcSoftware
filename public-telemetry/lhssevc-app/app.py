# run command: flask run -h localhost -p 8080

from flask import Flask, Response, request, jsonify
from time import time_ns

app = Flask(
	__name__,
	static_url_path='',
	static_folder="static"
)
records = []


@app.get("/")
def index():
	return app.send_static_file("index.html"), 200

# @app.post("/new-entry")
# def new_entry():
# 	global entry
# 	print(request.json)
# 	entry = request.json
# 	return Response(status=200)

@app.post("/new-entries")
def new_entry():
	global records
	print(request.json)
	records += request.json["records"]
	return Response(status=200)

@app.get("/get-entries")
def get_entry():
	start_str = request.args.get("start")
	if start_str is None:
		return Response(status=422)
	start = int(start_str)
	return jsonify({"records": records[start:], "upto": len(records)}), 200
