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
        page    = await browser.new_page()

        print("Navigating to WeBox login page...")
        await page.goto("https://www.webox.com/login", wait_until="networkidle")
        await page.wait_for_timeout(3000)

        # Save screenshot for debugging
        await page.screenshot(path="debug_login.png")
        print("Login page loaded. Attempting to fill credentials...")

        # Try multiple possible selectors for email field
        email_selectors = [
            'input[type="email"]',
            'input[name="email"]',
            'input[placeholder*="email" i]',
            'input[placeholder*="Email" i]',
            'input[type="text"]',
        ]

        email_filled = False
        for selector in email_selectors:
            try:
                el = await page.query_selector(selector)
                if el:
                    await el.fill(WEBOX_EMAIL)
                    print(f"Email filled using selector: {selector}")
                    email_filled = True
                    break
            except Exception as e:
                print(f"Selector {selector} failed: {e}")
                continue

        if not email_filled:
            print("ERROR: Could not find email input field")
            await browser.close()
            return

        # Try multiple possible selectors for password field
        password_selectors = [
            'input[type="password"]',
            'input[name="password"]',
            'input[placeholder*="password" i]',
            'input[placeholder*="Password" i]',
        ]

        password_filled = False
        for selector in password_selectors:
            try:
                el = await page.query_selector(selector)
                if el:
                    await el.fill(WEBOX_PASSWORD)
                    print(f"Password filled using selector: {selector}")
                    password_filled = True
                    break
            except Exception as e:
                print(f"Selector {selector} failed: {e}")
                continue

        if not password_filled:
            print("ERROR: Could not find password input field")
            await browser.close()
            return

        # Try multiple possible selectors for submit button
        submit_selectors = [
            'button[type="submit"]',
            'button:has-text("Sign in")',
            'button:has-text("Log in")',
            'button:has-text("Login")',
            'input[type="submit"]',
        ]

        for selector in submit_selectors:
            try:
                el = await page.query_selector(selector)
                if el:
                    await el.click()
                    print(f"Submit clicked using selector: {selector}")
                    break
            except Exception:
                continue

        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(3000)
        await page.screenshot(path="debug_after_login.png")
        print(f"After login URL: {page.url}")

        print("Navigating to Box Meal menu...")
        await page.goto("https://www.webox.com/welcome/boxMeal", wait_until="networkidle")
        await page.wait_for_timeout(4000)
        await page.screenshot(path="debug_menu.png")

        # Extract page text as fallback
        page_text = await page.inner_text("body")
        print(f"Page text preview: {page_text[:500]}")

        # Try to find menu items
        items = []
        possible_cards = await page.query_selector_all(
            '[class*="meal"], [class*="dish"], [class*="menu"], [class*="food"], [class*="item"], [class*="card"]'
        )
        print(f"Found {len(possible_cards)} possible menu cards")

        for card in possible_cards[:50]:
            try:
                text = await card.inner_text()
                text = text.strip()
                if len(text) > 5 and "$" in text:
                    items.append(text)
            except Exception:
                continue

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
            for item in items:
                lines.append(f"- {item}")
        else:
            lines.append("_(Menu data could not be extracted — see debug screenshots in Actions artifacts)_")

        lines += [
            "",
            "---",
            f"_Scraped automatically on {datetime.now().strftime('%Y-%m-%d %H:%M')} PST_",
        ]

        with open(OUTPUT_FILE, "w") as f:
            f.write("\n".join(lines))

        print(f"Done — {len(items)} items written to {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(scrape_menu())
