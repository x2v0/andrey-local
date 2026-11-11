"""Download full React SPA, intercept ALL assets, patch hardcoded URLs."""
import asyncio
from playwright.async_api import async_playwright
import pathlib, os, re, urllib.parse
from bs4 import BeautifulSoup

TARGET = "https://iskusstvo-zaboty-o-t-qqkkaff.gamma.site/"
ASSETS_DIR = pathlib.Path("assets")
ASSETS_DIR.mkdir(exist_ok=True)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        # Мобильный профиль для правильного React-состояния
        c = await b.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
            viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True
        )
        
        # Перехватчик всех запросов
        async def handle_route(route):
            url = route.request.url
            if url.startswith("data:") or url.startswith("blob:"):
                return await route.continue_()
            
            try:
                # Делаем реальный запрос к серверу
                response = await route.fetch()
                body = await response.body()
                
                if response.ok and url.startswith("http"):
                    parsed = urllib.parse.urlparse(url)
                    path = parsed.path.lstrip("/")
                    if not path: path = "index"
                    
                    # Сохраняем, сохраняя структуру папок (например _next/static/chunks/...)
                    filepath = ASSETS_DIR / path
                    filepath.parent.mkdir(parents=True, exist_ok=True)
                    
                    if not filepath.exists():
                        with open(filepath, "wb") as f:
                            f.write(body)
                            
                # Возвращаем ответ браузеру, чтобы сайт загрузился нормально
                await route.fulfill(response=response)
            except Exception:
                await route.continue_()

        await c.route("**/*", handle_route)
        
        page = await c.new_page()
        print("Navigating and intercepting ALL assets...")
        await page.goto(TARGET, wait_until="networkidle", timeout=90000)
        await page.wait_for_timeout(5000)
        
        # Получаем финальный HTML
        html = await page.content()
        await b.close()

    print("Patching HTML and JS...")
    soup = BeautifulSoup(html, "html.parser")

    # 1. Внедряем <base href="./">, чтобы React видел корень
    if not soup.find("base"):
        base_tag = soup.new_tag("base", href="./")
        soup.head.insert(0, base_tag)

    # 2. Убираем бейдж
    for d in soup.find_all(class_="css-2upw6"): d.decompose() 
    for a in soup.find_all("a", attrs={"data-id": "made-with-gamma-btn"}): a.decompose()

    # 3. Патчим HTML (заменяем домен на локальные пути)
    html_str = str(soup)
    html_str = html_str.replace("https://assets.gammahosted.com/5s9bbrdpq/", "./")
    html_str = html_str.replace("https://assets.gammahosted.com/", "./")
    
    pathlib.Path("index.html").write_text(html_str, encoding="utf-8")

    # 4. САМОЕ ВАЖНОЕ: Патчим JS-файлы (меняем жесткие ссылки внутри кода)
    print("Patching JS files (removing hardcoded CDN links)...")
    js_patched = 0
    for js_file in ASSETS_DIR.rglob("*.js"):
        try:
            content = js_file.read_text(encoding="utf-8", errors="ignore")
            orig = content
            # Заменяем все упоминания серверов Gamma на локальный корень
            content = content.replace("https://assets.gammahosted.com/5s9bbrdpq/", "./")
            content = content.replace("https://assets.gammahosted.com/", "./")
            # Иногда Next.js использует абсолютные пути от корня
            content = content.replace('"/_next/', '"./_next/') 
            if content != orig:
                js_file.write_text(content, encoding="utf-8")
                js_patched += 1
        except Exception:
            pass
            
    print(f"✅ index.html generated. Patched {js_patched} JS files.")

if __name__ == "__main__":
    asyncio.run(main())
