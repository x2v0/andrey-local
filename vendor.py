"""Download FULL Next.js app, preserving exact paths, and patch ALL links."""
import asyncio
from playwright.async_api import async_playwright
import pathlib, os, re, urllib.parse

TARGET = "https://iskusstvo-zaboty-o-t-qqkkaff.gamma.site/"
ROOT = pathlib.Path(".")

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        # Мобильный профиль, чтобы HTML сразу был мобильным
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
                    if not path: path = "index.html"
                    
                    # Сохраняем ровно по тому пути, который запрашивает Next.js (включая _next/)
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
        
        # Прокручиваем страницу вниз, чтобы загрузились "ленивые" скрипты (зум, анимации)
        for _ in range(8):
            await page.mouse.wheel(0, 1000)
            await page.wait_for_timeout(1000)
            
        await page.wait_for_timeout(5000)
        html = await page.content()
        await b.close()

    print("Patching HTML and ALL JS files...")
    
    # 1. Патчим index.html
    html_str = html.replace("https://assets.gammahosted.com/5s9bbrdpq", "")
    html_str = html_str.replace("https://assets.gammahosted.com", "")
    html_str = html_str.replace("url('/**/')", "none").replace('url("/**/")', "none")
    pathlib.Path("index.html").write_text(html_str, encoding="utf-8")

    # 2. Патчим ВСЕ скачанные JS и CSS файлы (убираем CDN из кода)
    js_patched = 0
    for filepath in ROOT.rglob("*"):
        if filepath.is_file() and filepath.suffix in [".js", ".css"]:
            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")
                if "assets.gammahosted.com" in content:
                    content = content.replace("https://assets.gammahosted.com/5s9bbrdpq", "")
                    content = content.replace("https://assets.gammahosted.com", "")
                    filepath.write_text(content, encoding="utf-8")
                    js_patched += 1
            except Exception:
                pass

    print(f"✅ index.html generated. Patched {js_patched} JS/CSS files.")

if __name__ == "__main__":
    asyncio.run(main())
