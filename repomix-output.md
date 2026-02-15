This file is a merged representation of the entire codebase, combined into a single document by Repomix.

# File Summary

## Purpose
This file contains a packed representation of the entire repository's contents.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Files are sorted by Git change count (files with more changes are at the bottom)

# Directory Structure
```
.github/workflows/apk_patcher.yml
apkmcli
apkmirror.py
download.py
patcher.py
README.md
requirements.txt
version.txt
```

# Files

## File: apkmcli
```
#!/usr/bin/env python3

import sys

from apkmirror import APKMirror

apkm = APKMirror(timeout=3, results=5)

search_query = input("Search:\n -> ")
results = apkm.search(search_query)

for result in enumerate(results):
    print(f"[{result[0]}] {result[1]['name']}")

download_id = int(input("Enter number to get details, or 99 to exit:\n -> "))

if download_id == 99:
    sys.exit("Exit")

app_details = apkm.get_app_details(results[download_id]["link"])

print(f"This app is for \"{app_details['architecture']}\" devices, running {app_details['android_version']} with {app_details['dpi']} DPI")

ask_download = input("Do you want to download it? (y/n)\n -> ")

if ask_download.lower() in ("y", ""):
    app_link = app_details["download_link"]
    print(f"Trying to get direct link, if the script cant get it, download by visiting this (not direct url): {app_link}")

    direct_link = apkm.get_download_link(app_link)

    print("Got the link i neded, trying to get a direct link...")
    sys.exit(f"Done. Direct url: {apkm.get_direct_download_link(direct_link)}")

else:
    sys.exit("Exit")
```

## File: apkmirror.py
```python
import time
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

import cloudscraper


class APKMirror:
    def __init__(
        self, timeout: int = None, results: int = None, user_agent: str = None
    ):
        self.timeout = timeout if timeout else 5
        self.results = results if results else 5

        self.user_agent = (
            user_agent
            if user_agent
            else "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0"
        )
        self.headers = {"User-Agent": self.user_agent}

        self.base_url = "https://www.apkmirror.com"
        self.base_search = f"{self.base_url}/?post_type=app_release&searchtype=apk&s="

        self.scraper = cloudscraper.create_scraper()

    def search(self, query):
        print("[search] Sleeping...")

        time.sleep(self.timeout)

        search_url = self.base_search + quote_plus(query)
        resp = self.scraper.get(search_url, headers=self.headers)

        print(f"[search] Status: {resp.status_code}")

        soup = BeautifulSoup(resp.text, "html.parser")
        apps = []
        appRow = soup.find_all("div", {"class": "appRow"})

        for app in appRow:
            try:
                app_dict = {
                    "name": app.find("h5", {"class": "appRowTitle"}).text.strip(),
                    "link": self.base_url
                    + app.find("a", {"class": "downloadLink"})["href"],
                    "image": self.base_url
                    + app.find("img", {"class": "ellipsisText"})["src"]
                    .replace("h=32", "h=512")
                    .replace("w=32", "w=512"),
                }

                apps.append(app_dict)

            except AttributeError:
                pass

        return apps[: self.results]

    def get_app_details(self, app_link):
        print("[get_app_details] Sleeping...")

        time.sleep(self.timeout)

        resp = self.scraper.get(app_link, headers=self.headers)

        print(f"[get_app_details] Status: {resp.status_code}")

        soup = BeautifulSoup(resp.text, "html.parser")

        data = soup.find_all("div", {"class": ["table-row", "headerFont"]})[1]

        architecture = data.find_all(
            "div",
            {
                "class": [
                    "table-cell",
                    "rowheight",
                    "addseparator",
                    "expand",
                    "pad",
                    "dowrap",
                ]
            },
        )[1].text.strip()
        android_version = data.find_all(
            "div",
            {
                "class": [
                    "table-cell",
                    "rowheight",
                    "addseparator",
                    "expand",
                    "pad",
                    "dowrap",
                ]
            },
        )[2].text.strip()
        dpi = data.find_all(
            "div",
            {
                "class": [
                    "table-cell",
                    "rowheight",
                    "addseparator",
                    "expand",
                    "pad",
                    "dowrap",
                ]
            },
        )[3].text.strip()
        download_link = (
            self.base_url + data.find_all("a", {"class": "accent_color"})[0]["href"]
        )

        return {
            "architecture": architecture,
            "android_version": android_version,
            "dpi": dpi,
            "download_link": download_link,
        }

    def get_download_link(self, app_download_link):
        print("[get_download_link] Sleeping...")

        time.sleep(self.timeout)

        resp = self.scraper.get(app_download_link, headers=self.headers)

        print(f"[get_download_link] Status: {resp.status_code}")

        soup = BeautifulSoup(resp.text, "html.parser")

        return self.base_url + str(
            soup.find_all("a", {"class": "downloadButton"})[0]["href"]
        )

    def get_direct_download_link(self, app_download_url):
        print("[get_direct_download_link] Sleeping...")

        time.sleep(self.timeout)

        resp = self.scraper.get(app_download_url, headers=self.headers)

        print(f"[get_direct_download_link] Status: {resp.status_code}")

        soup = BeautifulSoup(resp.text, "html.parser")
        data = soup.find(
            "a",
            {
                "rel": "nofollow",
                "data-google-interstitial": "false",
                "href": lambda href: href
                and "/wp-content/themes/APKMirror/download.php" in href,
            },
        )["href"]

        return self.base_url + str(data)
```

## File: download.py
```python
import sys
import os
import re
import cloudscraper
from apkmirror import APKMirror

# Configuration
PACKAGE_NAME = "com.bnhp.payments.paymentsapp"
VERSION_FILE = "version.txt"
OUTPUT_FILENAME = "latest.apk"

def get_local_version():
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, 'r') as f:
            return f.read().strip()
    return "0.0.0"

def extract_version_from_title(title):
    # Regex to find version numbers (e.g., "6.1", "10.0.0", "1.2.3-release")
    match = re.search(r"(\d+(?:\.\d+)+)", title)
    return match.group(1) if match else "0.0.0"

def set_github_output(key, value):
    # Writes to GITHUB_OUTPUT environment variable if it exists
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"{key}={value}\n")
    else:
        print(f"[Output] {key}={value}")

def main():
    apkm = APKMirror(timeout=10, results=5)
    
    print(f"[*] Initializing APKMirror check for: {PACKAGE_NAME}")
    
    # 1. Get Local Version
    local_version = get_local_version()
    print(f"[*] Local Version: {local_version}")

    # 2. Search APKMirror
    print("[*] Searching APKMirror...")
    try:
        results = apkm.search(PACKAGE_NAME)
    except Exception as e:
        print(f"[-] Search failed: {e}")
        sys.exit(1)

    if not results:
        print("[-] No results found on APKMirror.")
        sys.exit(1)

    # 3. Analyze Latest Result
    # APKMirror search usually returns the latest release first
    latest_result = results[0]
    app_title = latest_result['name']
    remote_version = extract_version_from_title(app_title)
    
    print(f"[*] Found latest release: {app_title}")
    print(f"[*] Detected Remote Version: {remote_version}")

    # 4. Compare Versions
    if remote_version == local_version:
        print("[i] Versions match. No update needed.")
        set_github_output("update_needed", "false")
        sys.exit(0)

    print(f"[!] Update detected! ({local_version} -> {remote_version})")
    
    # 5. Start Download Flow
    app_release_url = latest_result["link"]
    
    try:
        print("[*] Getting variant details...")
        details = apkm.get_app_details(app_release_url)
        variant_download_url = details["download_link"]
        
        print(f"[*] Variant: {details['architecture']} / Android {details['android_version']}")

        print("[*] Getting download page...")
        download_button_page = apkm.get_download_link(variant_download_url)

        print("[*] Extracting direct link...")
        direct_link = apkm.get_direct_download_link(download_button_page)
        
        print(f"[*] Downloading to {OUTPUT_FILENAME}...")
        
        # Headers are critical for APKMirror
        headers = {
            "User-Agent": apkm.user_agent,
            "Referer": download_button_page
        }

        # Reuse the scraper session
        response = apkm.scraper.get(direct_link, stream=True, headers=headers)
        
        if response.status_code == 200:
            with open(OUTPUT_FILENAME, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            print(f"[+] Download complete: {OUTPUT_FILENAME}")
            
            # Update local version file
            with open(VERSION_FILE, "w") as f:
                f.write(remote_version)
            
            set_github_output("update_needed", "true")
            set_github_output("new_version", remote_version)
        else:
            print(f"[-] Download failed with status: {response.status_code}")
            sys.exit(1)

    except Exception as e:
        print(f"[-] Error during download process: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## File: README.md
```markdown
# bit-updates
automatically patch bit to work on third party installer
```

## File: requirements.txt
```
bs4
cloudscraper
requests
```

## File: version.txt
```
0.0.0
```

## File: patcher.py
```python
import os
import re
import sys

def patch_smali(decompiled_dir):
    target_filename = "AppInitiationViewModel.smali"
    file_found = False
    patch_applied = False

    print(f"[*] Searching for {target_filename}...")

    for root, dirs, files in os.walk(decompiled_dir):
        if target_filename in files:
            file_path = os.path.join(root, target_filename)
            file_found = True
            print(f"[+] Found file at: {file_path}")

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Regex Explanation:
                # 1. invoke-static ... ArraysKt...->contains
                #    Matches the function call.
                # 2. .*?
                #    Matches any debug lines (like .line 90) between instructions.
                # 3. move-result ([vp]\d+)
                #    Captures the register (e.g., p1).
                # 4. .*?
                #    Matches debug lines between move-result and if-nez (THE FIX).
                # 5. if-nez \2, (:cond_\w+)
                #    Matches the check on the captured register.
                
                # We group everything before 'if-nez' into group 1 so we can restore it.
                pattern = re.compile(
                    r"(invoke-static \{[vp]\d+, [vp]\d+\}, Lkotlin\/collections\/ArraysKt.*?;->contains\(.*?\).*?move-result ([vp]\d+).*?)if-nez \2, (:cond_\w+)",
                    re.DOTALL
                )
                
                match = pattern.search(content)
                
                if match:
                    print(f"[i] Logic found! Target label is: {match.group(3)}")
                    
                    # Replace 'if-nez' with 'goto' to bypass the check
                    # \1 puts back the invoke, lines, move-result, and lines
                    # goto \3 puts the jump to the success label
                    new_content = pattern.sub(r"\1goto \3", content)
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    print("[+] PATCH APPLIED SUCCESSFULLY: Sideload check bypassed.")
                    patch_applied = True
                    break 
                
                else:
                    print("[!] Complex regex failed, trying simple search fallback...")
                    
                    # Fallback logic: simpler string replacement
                    # Assumes register p1 based on common compilation patterns
                    if "Lkotlin/collections/ArraysKt" in content and "contains" in content:
                        print("[i] Found ArraysKt->contains usage. Attempting heuristic patch...")
                        
                        # Look for if-nez p1 appearing shortly after the contains call
                        # This regex allows for intervening lines/whitespace
                        fallback_pattern = re.compile(r"(if-nez p1, (:cond_\w+))")
                        if fallback_pattern.search(content):
                             # Only replace the if-nez associated with p1
                             new_content = fallback_pattern.sub(r"goto \2", content, count=1)
                             
                             if new_content != content:
                                 with open(file_path, 'w', encoding='utf-8') as f:
                                     f.write(new_content)
                                 print("[+] Simple fallback patch applied successfully.")
                                 patch_applied = True
                                 break

                    print("[-] Pattern not found. Dumping snippet for debugging:")
                    lines = content.splitlines()
                    for i, line in enumerate(lines):
                        if "contains" in line and "ArraysKt" in line:
                            print(f"Line {i}: {line}")
                            # Print context
                            for j in range(1, 6):
                                if i + j < len(lines):
                                    print(f"Line {i+j}: {lines[i+j]}")

            except Exception as e:
                print(f"[-] Error reading/writing file: {str(e)}")
                sys.exit(1)

    if not file_found:
        print(f"[-] CRITICAL: {target_filename} not found.")
        sys.exit(1)

    if not patch_applied:
        print("[-] CRITICAL: File found but patch logic could not be applied.")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python patcher.py <decompiled_directory>")
        sys.exit(1)
        
    directory = sys.argv[1]
    patch_smali(directory)
```

## File: .github/workflows/apk_patcher.yml
```yaml
name: Patch and Sign APK

on:
  schedule:
    - cron: '0 4 * * *' # Runs daily at 4 AM UTC
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: write # Needed to push version.txt changes

    steps:
      - name: Checkout Repository
        uses: actions/checkout@v3

      - name: Setup Java
        uses: actions/setup-java@v3
        with:
          distribution: 'temurin'
          java-version: '17'

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install Dependencies
        run: |
          pip install -r requirements.txt

      - name: Check APKMirror and Download
        id: check_version
        run: python download.py

      - name: Download Tools (Apktool & UberSigner)
        if: steps.check_version.outputs.update_needed == 'true'
        run: |
          wget https://github.com/iBotPeaches/Apktool/releases/download/v2.12.1/apktool_2.12.1.jar -O apktool.jar
          wget https://github.com/patrickfav/uber-apk-signer/releases/download/v1.3.0/uber-apk-signer-1.3.0.jar -O ubersigner.jar

      - name: Decode APK
        if: steps.check_version.outputs.update_needed == 'true'
        run: |
          echo "Processing downloaded APK..."
          java -jar apktool.jar d -f latest.apk -o build_output

      - name: Apply Python Patch
        if: steps.check_version.outputs.update_needed == 'true'
        run: |
          python patcher.py build_output

      - name: Repack APK
        if: steps.check_version.outputs.update_needed == 'true'
        run: |
          java -jar apktool.jar b build_output -o patched_unsigned.apk

      - name: Decode Keystore
        if: steps.check_version.outputs.update_needed == 'true'
        env:
          RELEASE_KEYSTORE: ${{ secrets.RELEASE_KEYSTORE }}
        run: echo "$RELEASE_KEYSTORE" | base64 --decode > my_keystore.jks

      - name: Sign with UberApkSigner
        if: steps.check_version.outputs.update_needed == 'true'
        run: |
          java -jar ubersigner.jar \
            -a patched_unsigned.apk \
            --ks my_keystore.jks \
            --ksAlias ${{ secrets.KEY_ALIAS }} \
            --ksKeyPass ${{ secrets.KEY_PASSWORD }} \
            --ksPass ${{ secrets.KEYSTORE_PASSWORD }} \
            -o release \
            --overwrite

      - name: Commit Updated Version
        if: steps.check_version.outputs.update_needed == 'true'
        run: |
          git config --global user.name 'github-actions[bot]'
          git config --global user.email 'github-actions[bot]@users.noreply.github.com'
          git add version.txt
          git commit -m "Update patched version to ${{ steps.check_version.outputs.new_version }}" || echo "No changes to commit"
          git push

      - name: Upload Patched APK
        if: steps.check_version.outputs.update_needed == 'true'
        uses: actions/upload-artifact@v4
        with:
          name: Patched-Bit-${{ steps.check_version.outputs.new_version }}
          path: release/*.apk
```
