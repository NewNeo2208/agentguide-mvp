# AgentGuide MVP — WeBox

A structured profile that AI agents read before ordering on WeBox.
Reduces token usage by eliminating exploratory browsing.

---

## Files in this repo

| File | What it does |
|---|---|
| `webox.json` | Static profile: ordering flow, cutoffs, friction points, agent instructions |
| `webox_menu.md` | Today's menu — updated daily by the scraper |
| `scraper.py` | Logs into WeBox, grabs today's menu, updates webox_menu.md |
| `.github/workflows/daily_scrape.yml` | Runs scraper automatically every morning at 8AM PST |

---

## How agents use this

**Step 1** — Agent fetches the profile before doing anything:
```
GET https://raw.githubusercontent.com/YOUR_USERNAME/agentguide-mvp/main/webox.json
```

**Step 2** — Agent reads today's menu from the URL in the profile:
```
GET https://raw.githubusercontent.com/YOUR_USERNAME/agentguide-mvp/main/webox_menu.md
```

**Step 3** — Agent plans the full order from the data, then executes in one clean session.

---

## Agent prompt to use this

Add this to your agent's system prompt or task instruction:

```
Before ordering anything on WeBox:
1. Fetch https://raw.githubusercontent.com/YOUR_USERNAME/agentguide-mvp/main/webox.json
2. Read the agent_instructions field
3. Fetch today's menu from the today_menu.url field
4. Plan the full order from the menu data
5. Only then open WeBox and place the order directly
```

---

## Setup

See the scraper repo for full setup instructions on running the daily menu scraper.
