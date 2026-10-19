from flask import Flask, request, jsonify, send_from_directory
from agent.core import FoodAgent
app = Flask(__name__, static_folder="static")
SESSIONS = {}

@app.get("/")
def index(): return send_from_directory("static", "index.html")

@app.post("/api/location")
def set_loc():
    d = request.get_json(force=True)
    ag = SESSIONS.setdefault(d.get("session", "default"), FoodAgent())
    if d.get("lat") is not None and d.get("lon") is not None:
        ag.set_location(d["lat"], d["lon"])
        return jsonify(ok=True, place=(ag.state["location"] or {}).get("place"))
    elif d.get("city"):
        from agent.tools import set_location_from_name
        res = set_location_from_name(ag.state, d["city"])
        return jsonify(ok=True, place=(ag.state["location"] or {}).get("place"), res=res)
    return jsonify(error="No coordinates or city provided"), 400

@app.post("/api/chat")
def chat():
    d = request.get_json(force=True)
    ag = SESSIONS.setdefault(d.get("session", "default"), FoodAgent())
    if d.get("lat") is not None and d.get("lon") is not None:
        ag.set_location(d["lat"], d["lon"])
    elif d.get("city") and not ag.state["location"]:
        from agent.tools import set_location_from_name
        set_location_from_name(ag.state, d["city"])
    try:
        reply, trace = ag.chat(d["message"])
        return jsonify(reply=reply, trace=trace, profile=ag.state["profile"],
                       place=(ag.state["location"] or {}).get("place"),
                       places=ag.state.pop("last_results", []))
    except Exception as e:
        return jsonify(error=str(e)), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
