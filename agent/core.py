"""The plan-act loop. The LLM decides each next step from tool results (ReAct-style)."""
import json
from .llm import llm_call
from .tools import TOOLS, REGISTRY, reverse_geocode

SYSTEM = """You are FoodieAgent, a friendly and smart food-finding assistant.
Rules:
1. Location:
   - Check the context: if 'User location' is already known, NEVER ask for their location!
   - If User location is NOT shared yet, and the user mentions a city/landmark/place in their message (e.g. 'Phagwara', 'Athouli', 'Kapurthala', etc.), immediately call set_location_from_name to locate them.
   - Only ask for location if both GPS and text location are completely unknown.
2. Memory & Preferences:
   - Check 'Memory (profile)': NEVER ask about preferences already saved in Memory! For example, if veg/non-veg (diet) is already saved, DO NOT ask about veg or non-veg again.
   - If mood, diet, dine_mode, or spice are mentioned, save them immediately with save_preference.
   - Ask at most 1-2 unanswered questions at a time (e.g. dine-in vs takeaway, spice level, or travel distance).
3. Finding Food:
   - When you have the user's craving and location is known, call find_restaurants. Call find_restaurants at most twice.
4. Recommendations:
   - Present the top spots with: name, distance, cuisine, why it fits, and Google Maps link.
   - If direct_dish_map is present, share it so the user can see all matching dish spots on Google Maps.
   - End with a friendly follow-up.
Only recommend places returned by tools; never invent fictitious place names. Keep replies concise, helpful, and friendly."""

class FoodAgent:
    def __init__(self):
        self.messages, self.state = [], {"profile": {}, "location": None}

    def set_location(self, lat, lon):
        self.state["location"] = {"lat": float(lat), "lon": float(lon), "place": reverse_geocode(lat, lon)}

    def _context(self):
        loc = self.state["location"]
        ctx = f"\nUser location: {loc['place']} ({loc['lat']:.4f},{loc['lon']:.4f})." if loc else "\nUser location: NOT shared yet."
        return SYSTEM + ctx + f"\nMemory (profile): {json.dumps(self.state['profile'])}"

    def chat(self, text, max_steps=6):
        self.messages.append({"role": "user", "content": text})
        trace = []
        for step in range(1, max_steps + 1):
            window = self.messages[-30:]
            while window and window[0]["role"] != "user": window = window[1:]   # never start on an orphan tool msg
            provider, msg, errs = llm_call([{"role": "system", "content": self._context()}] + window, TOOLS)
            clean = {"role": "assistant", "content": msg.get("content") or ""}
            if msg.get("tool_calls"): clean["tool_calls"] = msg["tool_calls"]
            self.messages.append(clean)
            if not msg.get("tool_calls"):
                trace.append({"step": step, "provider": provider, "tool": None, "note": "final answer", "errors": errs})
                return clean["content"], trace
            for tc in msg["tool_calls"]:
                name, raw = tc["function"]["name"], tc["function"].get("arguments") or "{}"
                args = raw
                try:
                    args = json.loads(raw)
                    result = REGISTRY[name](self.state, **args)
                except Exception as e:                                        # tool failure goes back to the LLM so it can recover
                    result = {"error": str(e)}
                trace.append({"step": step, "provider": provider, "tool": name, "args": args,
                              "result": json.dumps(result)[:400], "errors": errs})
                self.messages.append({"role": "tool", "tool_call_id": tc["id"], "content": json.dumps(result)})
        
        # If max steps reached with tools, generate final response without tools
        try:
            provider, msg, errs = llm_call([{"role": "system", "content": self._context() + "\nSummarize the recommendations found and provide the map links now."}] + self.messages[-10:], tools=[])
            final_content = msg.get("content") or "Here are the top nearby dining spots found for you!"
            trace.append({"step": max_steps + 1, "provider": provider, "tool": None, "note": "final summary", "errors": errs})
            return final_content, trace
        except Exception:
            return "I have found the top places around your location! Check out the map links above.", trace
