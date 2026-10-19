# FoodieAgent – location-aware food recommendation agent (CSE476 CA1, Topic T13)

**Run:** `pip install -r requirements.txt` → copy `.env.example` to `.env` and add keys → `python app.py` → open http://localhost:5000
(Free keys: console.groq.com and aistudio.google.com.) Demo notebook: `demo.ipynb`.

**Tools.** `find_restaurants` searches real places around the shared GPS location (OpenStreetMap Overpass), filters by taste/cuisine/veg,
and returns straight-line and road distance (OSRM). `save_preference` stores mood, diet, budget, spice level, etc. A third helper, `get_profile`, reads memory back.

**Memory.** Two layers: the full conversation history (so earlier turns are used later) and a structured profile (diet, budget, mood, allergies)
injected into the system prompt every step, so the agent never re-asks what it already knows.

**Agent loop.** `agent/core.py`: the LLM picks a tool, sees the result, and decides the next step (ask follow-up → save → search → answer), up to 6 steps.
**Failover.** `agent/llm.py`: Groq first (2 retries), then Gemini; the trace shows which provider answered.

**Google AI Mode UI & Interactive Cards.**
- Returns rich restaurant cards with hero food photos, ratings, review counts, price tiers, and full street addresses.
- Features dedicated action buttons: `🧭 Directions` (turn-by-turn navigation), `📞 Call`, and `🌐 Google Maps`.
- Curated insights: `The Vibe`, `Why It Wins`, and `Insider Tip`.
- Antigravity Custom Agent integration in `.agents/agents/foodie_agent.md` and `.agents/skills/foodie_agent/SKILL.md`.

**One honest failure.** Overpass public API occasionally hits 504 gateway timeouts on large rural radius queries.
Fix: Added Nominatim bounded viewbox search fallback and smart dish fallback with direct Google Maps dish search links.

**Who did what:** (if group) ...
