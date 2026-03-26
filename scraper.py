import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright

WEBOX_EMAIL    = os.environ["WEBOX_EMAIL"]
WEBOX_PASSWORD = os.environ["WEBOX_PASSWORD"]
OUTPUT_FILE    = "menu.md"

async def scrape_menu():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page    = await browser.new_page()

        print("Logging in to WeBox...")
        await page.goto("https://www.webox.com/login", wait_until="networkidle")
        await page.fill('input[type="email"]',    WEBOX_EMAIL)
        await page.fill('input[type="password"]', WEBOX_PASSWORD)
        await page.click('button[type="submit"]')
        await page.wait_for_load_state("networkidle")

        print("Navigating to Box Meal menu...")
        await page.goto("https://www.webox.com/welcome/boxMeal", wait_until="networkidle")
        await page.wait_for_timeout(3000)

        # --- Cutoff times ------------------------------------------------
        cutoff_text = ""
        try:
            cutoff_el = await page.query_selector('[class*="cutoff"], [class*="deadline"], [class*="time"]')
            if cutoff_el:
                cutoff_text = await cutoff_el.inner_text()
        except Exception:
            cutoff_text = "Check site for cutoff times (typically Lunch 10AM / Dinner 3PM)"

        # --- Menu items --------------------------------------------------
        items = []
        meal_cards = await page.query_selector_all('[class*="meal-card"], [class*="dish"], [class*="menu-item"], [class*="food-item"]')

        for card in meal_cards:
            try:
                name_el  = await card.query_selector('[class*="name"], [class*="title"], h3, h4')
                price_el = await card.query_selector('[class*="price"]')
                tag_els  = await card.query_selector_all('[class*="tag"], [class*="diet"], [class*="label"]')

                name  = (await name_el.inner_text()).strip()  if name_el  else "Unknown dish"
                price = (await price_el.inner_text()).strip() if price_el else "N/A"
                tags  = [await t.inner_text() for t in tag_els]

                if name and name != "Unknown dish":
                    items.append({"name": name, "price": price, "tags": tags})
            except Exception:
                continue

        await browser.close()

        # --- Write output ------------------------------------------------
        today = datetime.now().strftime("%B %d, %Y")
        lines = [
            f"# WeBox Menu — {today}",
            "",
            f"**Order cutoff:** {cutoff_text.strip() if cutoff_text else 'Lunch 10AM / Dinner 3PM PST'}",
            "",
            "## Available dishes",
            "",
        ]

        if items:
            for item in items:
                tag_str = ", ".join(item["tags"]) if item["tags"] else "no tags"
                lines.append(f"- **{item['name']}** | {item['price']} | {tag_str}")
        else:
            lines.append("_(Menu data could not be extracted — WeBox may have updated their page structure. Check the site directly.)_")

        lines += [
            "",
            "---",
            f"_Scraped automatically on {datetime.now().strftime('%Y-%m-%d %H:%M')} PST_",
        ]

        with open(OUTPUT_FILE, "w") as f:
            f.write("\n".join(lines))

        print(f"Menu saved to {OUTPUT_FILE} — {len(items)} items found.")

if __name__ == "__main__":
    asyncio.run(scrape_menu())
