"""Download FULL Next.js app, strip CDN prefix, patch links."""
import asyncio
from playwright.async_api import async_playwright
import pathlib, os, re, urllib.parse

TARGET = "https://iskusstvo-zaboty-o-t-qqkkaff.gamma.site/"
ROOT = pathlib.Path(".")

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        c = await b.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
            viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True
        )
        
        async def handle_route(route):
            url = route.request.url
            if url.startswith("data:") or url.startswith("blob:"):
                return await route.continue_()
            try:
                response = await route.fetch()
                body = await response.body()
                if response.ok and url.startswith("http"):
                    parsed = urllib.parse.urlparse(url)
                    path = parsed.path.lstrip("/")
                    
                    # ГЛАВНЫЙ ФИКС: Срезаем префикс /5s9bbrdpq/ из пути сохранения!
                    if path.startswith("5s9bbrdpq/"):
                        path = path[len("5s9bbrdpq/"):]
                        
                    if not path: path = "index.html"
                    
                    filepath = ROOT / path
                    filepath.parent.mkdir(parents=True, exist_ok=True)
                    
                    if not filepath.exists():
                        with open(filepath, "wb") as f:
                            f.write(body)
                            
                await route.fulfill(response=response)
            except Exception:
                await route.continue_()

        await c.route("**/*", handle_route)
        page = await c.new_page()
        print("Navigating and downloading the ENTIRE Next.js app...")
        await page.goto(TARGET, wait_until="networkidle", timeout=90000)
        
        # Прокручиваем, чтобы триггернуть ленивую загрузку скриптов
        for _ in range(8):
            await page.mouse.wheel(0, 1000)
            await page.wait_for_timeout(1000)
            
        await page.wait_for_timeout(5000)
        html = await page.content()
        await b.close()

    print("Patching HTML...")
    html_str = html.replace("https://assets.gammahosted.com/5s9bbrdpq", "")
    html_str = html_str.replace("https://assets.gammahosted.com", "")
    html_str = html_str.replace("url('/**/')", "none").replace('url("/**/")', "none")
    
    pathlib.Path("index.html").write_text(html_str, encoding="utf-8")
    print("✅ index.html generated. Structure is correct now.")

if __name__ == "__main__":
    asyncio.run(main())
