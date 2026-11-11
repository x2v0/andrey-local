"""Download full React SPA and rewrite paths."""
import asyncio
from playwright.async_api import async_playwright
import pathlib, os, re, urllib.request, urllib.parse
from bs4 import BeautifulSoup

TARGET = "https://iskusstvo-zaboty-o-t-qqkkaff.gamma.site/"
ASSETS_DIR = pathlib.Path("assets")
ASSETS_DIR.mkdir(exist_ok=True)

def download(url, folder):
    if url.startswith("data:") or not url.startswith("http"):
        return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read()
        
        # Создаем структуру папок
        parsed = urllib.parse.urlparse(url)
        filename = os.path.basename(parsed.path) or "index"
        if not filename.endswith(('.js', '.css', '.woff2', '.woff', '.ttf', '.png', '.jpg', '.jpeg', '.webp', '.svg')):
            filename += ".bin"
        
        folder_path = ASSETS_DIR / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        filepath = folder_path / filename
        
        # Если файл уже есть, не качаем
        if not filepath.exists():
            with open(filepath, "wb") as f:
                f.write(data)
        return str(filepath).replace("\\", "/")
    except Exception as e:
        return None

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        c = await b.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = await c.new_page()
        print("Navigating...")
        await page.goto(TARGET, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(5000)
        html = await page.content()
        await b.close()

    soup = BeautifulSoup(html, "html.parser")
    
    # 1. Скачиваем скрипты
    print("Downloading scripts...")
    for s in soup.find_all("script"):
        src = s.get("src")
        if src:
            local_path = download(src, "js")
            if local_path:
                s["src"] = local_path
                
    # 2. Скачиваем стили
    print("Downloading css...")
    for l in soup.find_all("link", rel="stylesheet"):
        href = l.get("href")
        if href:
            local_path = download(href, "css")
            if local_path:
                l["href"] = local_path

    # 3. Скачиваем картинки
    print("Downloading images...")
    for img in soup.find_all("img"):
        src = img.get("src")
        if src:
            local_path = download(src, "images")
            if local_path:
                img["src"] = local_path
            if "srcset" in img.attrs:
                del img["srcset"]

    # 4. Убираем noindex и badge
    for m in soup.find_all("meta", attrs={"name": "robots"}): m.decompose()
    for a in soup.find_all("a", attrs={"data-id": "made-with-gamma-btn"}): a.decompose()

    pathlib.Path("index.html").write_text(str(soup), encoding="utf-8")
    print("✅ index.html generated.")

if __name__ == "__main__":
    asyncio.run(main())
