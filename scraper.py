import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright

WEBOX_EMAIL    = os.environ["WEBOX_EMAIL"]
WEBOX_PASSWORD = os.environ["WEBOX_PASSWORD"]
OUTPUT_FILE    = "webox_menu.md"

async def scrape_menu():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page    = await context.new_page()

        # Step 1: Go to homepage and log in via the login form
        print("Going to WeBox homepage...")
        await page.goto("https://www.webox.com", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        await page.screenshot(path="debug_01_homepage.png")
        print(f"URL: {page.url}")

        # Step 2: Check if already on menu page (auto-logged in)
        if "boxMeal" in page.url or "welcome" in page.url:
            print("Already logged in — skipping login step")
        else:
            print("Need to log in...")

            # Try clicking Sign In link
            try:
                await page.click('a[href*="login"], a:has-text("Sign In"), button:has-text("Sign In")', timeout=5000)
                await page.wait_for_timeout(2000)
            except Exception:
                print("Could not click Sign In, trying direct navigation...")

            # Try filling login form using name attributes (we know them from logs)
            try:
                # username field has name="username"
                await page.fill('input[name="username"]', WEBOX_EMAIL, timeout=10000)
                await page.fill('input[name="password"]', WEBOX_PASSWORD, timeout=10000)
                print("Credentials filled")

                # Submit
                await page.keyboard.press("Enter")
                await page.wait_for_load_state("networkidle")
                await page.wait_for_timeout(3000)
            except Exception as e:
                print(f"Login form error: {e}")

        await page.screenshot(path="debug_02_after_login.png")
        print(f"After login URL: {page.url}")

        # Step 3: Navigate to menu page
        print("Navigating to Box Meal menu...")
        await page.goto("https://www.webox.com/welcome/boxMeal", wait_until="networkidle")
        await page.wait_for_timeout(5000)
        await page.screenshot(path="debug_03_menu.png")
        print(f"Menu URL: {page.url}")

        # Step 4: Print page text to understand structure
        page_text = await page.inner_text("body")
        print(f"Page text preview:\n{page_text[:2000]}")

        # Step 5: Try many different selectors to find menu items
        items = []

        # Strategy 1: look for price patterns in text
        all_elements = await page.query_selector_all("*")
        price_elements = []
        for el in all_elements[:500]:
            try:
                text = (await el.inner_text()).strip()
                if "$" in text and len(text) < 200 and len(text) > 3:
                    price_elements.append(text)
            except Exception:
                continue

        print(f"Found {len(price_elements)} elements containing $")
        for el in price_elements[:5]:
            print(f"  Sample: {el[:100]}")

        # Use price elements as menu items
        seen = set()
        for text in price_elements:
            if text not in seen:
                seen.add(text)
                items.append(text)

        await browser.close()

        # Write output
        today = datetime.now().strftime("%B %d, %Y")
        lines = [
            f"# WeBox Menu — {today}",
            "",
            "**Order cutoff:** Lunch 10:00 AM PST / Dinner 3:00 PM PST",
            "",
            "## Available dishes",
            "",
        ]

        if items:
            for item in items[:50]:
                lines.append(f"- {item}")
            print(f"Written {len(items)} items")
        else:
            lines.append("_(Menu items not found — check debug screenshots)_")
            print("No items found")

        lines += ["", "---", f"_Scraped on {datetime.now().strftime('%Y-%m-%d %H:%M')} PST_"]

        with open(OUTPUT_FILE, "w") as f:
            f.write("\n".join(lines))

if __name__ == "__main__":
    asyncio.run(scrape_menu())
