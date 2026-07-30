import os
import requests

def download_file(url, path):
    if os.path.exists(path):
        print(f"✅ {path} already exists")
        return

    print(f"⬇️ Downloading {path}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        print(f"✅ Downloaded {path}")
    except Exception as e:
        print(f"❌ Failed to download {path}: {e}")
