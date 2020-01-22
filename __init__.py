from flask import Flask, render_template, send_file, request
import subprocess, json

app = Flask(
	__name__, 
	static_folder="./build/static",
	template_folder="./build")

@app.route("/")
def index():
	return render_template("index.html")

def convert_to_query_str(sql_query_obj_str):
	o = json.loads(sql_query_obj_str)
	return o["function"]+','+o["country"]+','+o["region"]+','+o["city"]

@app.route("/database", methods=["POST"])
def database():
	f_path = "/var/www/jlm_app/jlm_app/formatted_sql.py"
	sql_query_str = convert_to_query_str(request.get_data())

	proc = subprocess.Popen(
		[f_path,sql_query_str], 
		stdout=subprocess.PIPE)
	output = proc.stdout.read()
	return output

@app.route(
	"/web_search_city_locations", 
	methods=["GET","POST"])
def cities():
	f_path = "/var/www/jlm_app/jlm_app/cities.py"

	proc = subprocess.Popen(
		[f_path,request.get_data()],
		stdout=subprocess.PIPE)
	output = proc.stdout.read()
	return output

@app.route("/vertex_cover")
def vertex_cover():
	f_path = "/var/www/jlm_app/jlm_app/vertexCover.png"
	proc = subprocess.Popen(
		"/var/www/jlm_app/jlm_app/vertex_cover.py")

	sStdout, sStdErr = proc.communicate()
	bites = open(f_path, "rb")

	return send_file(
		bites,
		attachment_filename="vertexCover.png",
		mimetype="image/png",cache_timeout=0)



