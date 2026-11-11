"""Radical Next.js vendoring: patch publicPath and download missing files."""
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
        print("Navigating...")
        await page.goto(TARGET, wait_until="networkidle", timeout=90000)
        
        for _ in range(10):
            await page.mouse.wheel(0, 2000)
            await page.wait_for_timeout(800)
            
        await page.wait_for_timeout(5000)
        html = await page.content()
        
        # Принудительно скачиваем nomodule скрипты (0c0hxoamwjsbw.js)
        soup = BeautifulSoup(html, "html.parser")
        import urllib.request
        for script in soup.find_all("script", nomodule=True):
            src = script.get("src")
            if src and src.startswith("http"):
                try:
                    req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req) as r:
                        data = r.read()
                    path = urllib.parse.urlparse(src).path.lstrip("/")
                    if path.startswith("5s9bbrdpq/"): path = path[len("5s9bbrdpq/"):]
                    filepath = ROOT / path
                    filepath.parent.mkdir(parents=True, exist_ok=True)
                    with open(filepath, "wb") as f:
                        f.write(data)
                except: pass
                
        await b.close()

    print("Radically patching ALL files...")
    
    # ВОТ ИСПРАВЛЕННАЯ РЕГУЛЯРКА (одинарные слэши)
    cdn_regex = re.compile(r'https?://assets\.gammahosted\.com(?:/5s9bbrdpq)?')

    html_str = cdn_regex.sub('', html)
    pathlib.Path("index.html").write_text(html_str, encoding="utf-8")

    patched_count = 0
    for filepath in ROOT.rglob("*"):
        if filepath.is_file() and filepath.suffix in [".js", ".css", ".json"]:
            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")
                if "gammahosted.com" in content:
                    content = cdn_regex.sub('', content)
                    filepath.write_text(content, encoding="utf-8")
                    patched_count += 1
            except Exception:
                pass

    print(f"✅ Done. Patched {patched_count} JS/CSS/JSON files.")

if __name__ == "__main__":
    from bs4 import BeautifulSoup
    import urllib.request
    asyncio.run(main())
