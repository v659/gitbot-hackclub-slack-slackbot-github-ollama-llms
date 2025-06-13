from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def slack_events():
    data = request.json
    if data and "challenge" in data:
        return jsonify({"challenge": data["challenge"]})
    return "OK", 200

if __name__ == "__main__":
    app.run(port=3000)
