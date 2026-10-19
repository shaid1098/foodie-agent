---
name: foodie_agent
description: >-
  Hyper-local food recommendation workflow. Use when users ask for food, restaurants,
  dishes (e.g. biryani, pizza, thali, momos), dining places, or local culinary recommendations.
---

# FoodieAgent Skill Guide

This skill guides the agent in generating hyper-local, accurate food recommendations formatted in **Google AI Mode**.

## Workflow

### 1. Identify Geographic Location
- Extract GPS coordinates or city / neighborhood (e.g., *Athouli*, *Phagwara*, *Law Gate / LPU*, *Kapurthala*).
- If location is unknown, ask the user once. Never re-ask if already set.

### 2. Multi-Source Search & Verification
- Query local places with distance calculation and coordinates.
- Verify whether the user wants Vegetarian, Non-Vegetarian, Dine-in, or Takeaway.

### 3. Google AI Mode Card Output
For each top recommendation, output:
- **Badge:** (e.g., `🏆 Top Pick for Authentic Hyderabadi`, `🔥 Local Favorite & Budget Pick`)
- **Name & Rating:** Name, star rating, review count, price tier (`₹200–400`)
- **Status & Address:** Open status, road distance with driving time, real street address
- **Direct Action Links:** Directions link (`https://www.google.com/maps/dir/?api=1&destination=LAT,LON`), Call link, Google Maps link
- **Curated Insights:**
  - **💫 The Vibe:** Ambiance and setting
  - **🎯 Why It Wins:** Signature dish attributes
  - **💡 Insider Tip:** Local customer advice
- **Interactive All-Places Map:** Provide a direct Google Maps search link for all matching dishes in that locality.
