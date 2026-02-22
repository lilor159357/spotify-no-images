import os
import re
import shutil
import xml.etree.ElementTree as ET

# =========================================================================
# פונקציות עזר (Helpers)
# =========================================================================

def get_package_name(manifest_path: str) -> str:
    """קורא את ה-AndroidManifest.xml כדי לחלץ את שם החבילה."""
    try:
        tree = ET.parse(manifest_path)
        root = tree.getroot()
        return root.get('package')
    except Exception as e:
        print(f"[-] Could not parse package name from manifest: {e}")
        return None

def get_main_activity_smali_path(manifest_path: str) -> str:
    """מוצא אוטומטית את מסך הפתיחה (דרך activity או activity-alias)."""
    try:
        tree = ET.parse(manifest_path)
        root = tree.getroot()
        ns = {'android': 'http://schemas.android.com/apk/res/android'}
        
        def is_main_launcher(element):
            is_main = False
            is_launcher = False
            for intent_filter in element.iter('intent-filter'):
                for action in intent_filter.iter('action'):
                    if action.get(f"{{{ns['android']}}}name") == "android.intent.action.MAIN":
                        is_main = True
                for category in intent_filter.iter('category'):
                    if category.get(f"{{{ns['android']}}}name") == "android.intent.category.LAUNCHER":
                        is_launcher = True
            return is_main and is_launcher

        target_activity_name = None

        # 1. חיפוש ב-activity רגיל
        for activity in root.iter('activity'):
            if is_main_launcher(activity):
                target_activity_name = activity.get(f"{{{ns['android']}}}name")
                break
        
        # 2. חיפוש ב-alias (נפוץ ב-Bit ובאפליקציות גדולות)
        if not target_activity_name:
            for alias in root.iter('activity-alias'):
                if is_main_launcher(alias):
                    target_activity_name = alias.get(f"{{{ns['android']}}}targetActivity")
                    break
                    
        if target_activity_name:
            if target_activity_name.startswith("."):
                target_activity_name = root.get('package') + target_activity_name
            return target_activity_name.replace('.', '/') + ".smali"

    except Exception as e:
        print(f"[-] Could not parse main activity from manifest: {e}")
    return None

# =========================================================================
# הפונקציה הראשית (Patch)
# =========================================================================

def patch(decompiled_dir: str) -> bool:
    print(f"[*] Starting Bit App patch process in {decompiled_dir}...")
    
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    payload_dir = os.path.join(current_script_dir, "updater_payload")
    manifest_path = os.path.join(decompiled_dir, "AndroidManifest.xml")

    # ---------------------------------------------------------------------
    # חלק 1: עקיפת בדיקות אבטחה של Bit (Sideload / Installer Check)
    # ---------------------------------------------------------------------
    print("[*] Applying Bit specific security bypass...")
    
    bit_target_file = "AppInitiationViewModel.smali"
    bit_patched = False

    for root, dirs, files in os.walk(decompiled_dir):
        if bit_target_file in files:
            file_path = os.path.join(root, bit_target_file)
            print(f"[+] Found Bit target file: {file_path}")

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # מחפש את הלוגיקה שבודקת את מקור ההתקנה (ArraysKt.contains)
                # אם נמצא, הוא קופץ לכישלון (if-nez). אנחנו נשנה את זה לקפיצה להצלחה (goto).
                pattern = re.compile(
                    r"(invoke-static \{[vp]\d+, [vp]\d+\}, Lkotlin\/collections\/ArraysKt.*?;->contains\(.*?\).*?move-result ([vp]\d+).*?)if-nez \2, (:cond_\w+)",
                    re.DOTALL
                )

                if pattern.search(content):
                    # החלפת if-nez ב-goto כדי לעקוף את הבדיקה
                    new_content = pattern.sub(r"\1goto \3", content)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print("[+] Bit Patch: Sideload check bypassed (Regex Method).")
                    bit_patched = True
                else:
                    # ניסיון שני - פאצ' פשוט יותר אם הרגקס נכשל
                    print("[!] Complex regex failed, trying fallback...")
                    if "Lkotlin/collections/ArraysKt" in content and "contains" in content:
                        fallback_pattern = re.compile(r"(if-nez p1, (:cond_\w+))")
                        if fallback_pattern.search(content):
                            new_content = fallback_pattern.sub(r"goto \2", content, count=1)
                            if new_content != content:
                                with open(file_path, 'w', encoding='utf-8') as f:
                                    f.write(new_content)
                                print("[+] Bit Patch: Sideload check bypassed (Fallback Method).")
                                bit_patched = True

            except Exception as e:
                print(f"[-] Error patching Bit logic: {str(e)}")

    if not bit_patched:
        print("[-] WARNING: Could not apply Bit security bypass. The app might crash on launch.")
    
    # ---------------------------------------------------------------------
    # חלק 2: הזרקת מנגנון העדכון האוניברסלי
    # ---------------------------------------------------------------------
    print("\n[*] Applying Universal Updater patch...")
    
    app_id = os.path.basename(current_script_dir) # יזהה 'bit' אוטומטית

    # זיהוי דינמי של הריפו (עבור הפורק שלך)
    github_repo_env = os.getenv('GITHUB_REPOSITORY')
    if github_repo_env:
        repo_owner, repo_name = github_repo_env.split('/')
    else:
        # ברירת מחדל לבדיקות מקומיות
        repo_owner = "lilor159357"
        repo_name = "app-store"

    print(f"[i] Detected Repo: {repo_owner}/{repo_name}")

    version_txt_url = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/refs/heads/main/apps/{app_id}/version.txt"
    download_prefix = f"https://github.com/{repo_owner}/{repo_name}/releases/download/{app_id}-v"
    download_middle = f"/{app_id}-patched-"

    package_name = get_package_name(manifest_path)
    if not package_name:
        print("[-] CRITICAL: Failed to get package name. Skipping updater.")
        return bit_patched # מחזירים את סטטוס הפאץ' של ביט לפחות

    provider_authority = f"{package_name}.provider"
    target_activity_smali = get_main_activity_smali_path(manifest_path)

    print(f"[i] App ID: {app_id}")
    print(f"[i] Package Name: {package_name}")
    print(f"[i] Main Activity: {target_activity_smali}")

    if not os.path.exists(payload_dir):
        print("[!] Warning: Updater payload directory not found! Skipping updater.")
        return bit_patched

    # -- א. העתקת קבצים והחלפת פלייסחולדרים --
    try:
        # מציאת אינדקס smali פנוי
        max_dex = max(
            [int(d.replace("smali_classes", "")) for d in os.listdir(decompiled_dir) if d.startswith("smali_classes") and d.replace("smali_classes", "").isdigit()]
            or [0]
        )
        next_smali_dir = f"smali_classes{max_dex + 1}"
        
        dst_smali_root = os.path.join(decompiled_dir, next_smali_dir, "storeautoupdater")
        src_updater_files = os.path.join(payload_dir, "smali", "storeautoupdater")
        
        if os.path.exists(src_updater_files):
            shutil.copytree(src_updater_files, dst_smali_root, dirs_exist_ok=True)
        else:
            print("[-] CRITICAL: 'storeautoupdater' directory not found in payload.")
            return bit_patched

        src_res = os.path.join(payload_dir, "res")
        dst_res = os.path.join(decompiled_dir, "res")
        shutil.copytree(src_res, dst_res, dirs_exist_ok=True)
        
        print(f"[+] Updater copied to {next_smali_dir}/storeautoupdater.")

        # החלפה בקבצים
        for smali_file in os.listdir(dst_smali_root):
            smali_path = os.path.join(dst_smali_root, smali_file)
            if os.path.isfile(smali_path) and smali_path.endswith('.smali'):
                with open(smali_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                content = content.replace("__PROVIDER_AUTHORITY__", provider_authority)
                content = content.replace("__VERSION_TXT_URL__", version_txt_url)
                content = content.replace("__RELEASE_DOWNLOAD_PREFIX__", download_prefix)
                content = content.replace("__RELEASE_DOWNLOAD_MIDDLE__", download_middle)
                
                with open(smali_path, 'w', encoding='utf-8') as f:
                    f.write(content)
        print("[+] Placeholders replaced.")

    except Exception as e:
        print(f"[-] Updater setup failed: {e}")
        return bit_patched

    # -- ב. עדכון מניפסט --
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_content = f.read()

        if 'android.permission.REQUEST_INSTALL_PACKAGES' not in manifest_content:
            manifest_content = manifest_content.replace(
                '<application', 
                '<uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES"/>\n    <application'
            )

        manifest_components = f"""
        <service android:name="storeautoupdater.DownloadService" />
        <provider
            android:name="storeautoupdater.GenericFileProvider"
            android:authorities="{provider_authority}"
            android:exported="false"
            android:grantUriPermissions="true">
            <meta-data
                android:name="android.support.FILE_PROVIDER_PATHS"
                android:resource="@xml/provider_paths" />
        </provider>
"""
        if 'android:name="storeautoupdater.GenericFileProvider"' not in manifest_content:
            manifest_content = manifest_content.replace(
                '</application>', 
                f'{manifest_components}\n    </application>'
            )

        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(manifest_content)
        print("[+] Manifest updated.")
    except Exception as e:
        print(f"[-] Manifest patch failed: {e}")
        return bit_patched

    # -- ג. הזרקה למסך הראשי --
    if target_activity_smali:
        main_patched = False
        target_filename = os.path.basename(target_activity_smali)

        for root, _, files in os.walk(decompiled_dir):
            if target_filename in files:
                full_path = os.path.join(root, target_filename)
                # וידוא נתיב
                if target_activity_smali.replace('/', os.sep) not in full_path:
                    continue

                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        main_content = f.read()

                    if "Lstoreautoupdater/Updater;->check" in main_content:
                        print("[i] Updater already injected.")
                        main_patched = True
                    else:
                        method_ptrn = re.compile(r"(\.method.*?onCreate\(Landroid/os/Bundle;\)V)(.*?)(\.end method)", re.DOTALL)
                        match = method_ptrn.search(main_content)
                        
                        if match:
                            body = match.group(2)
                            last_ret = body.rfind("return-void")
                            if last_ret != -1:
                                inj = "\n    move-object v0, p0\n    invoke-static {v0}, Lstoreautoupdater/Updater;->check(Landroid/content/Context;)V\n    "
                                new_body = body[:last_ret] + inj + body[last_ret:]
                                new_all = match.group(1) + new_body + match.group(3)
                                main_content = main_content.replace(match.group(0), new_all, 1)
                                with open(full_path, 'w', encoding='utf-8') as f:
                                    f.write(main_content)
                                main_patched = True
                                print(f"[+] Injected updater into {target_filename}")
                except Exception as e:
                    print(f"[-] Injection error: {e}")
                break
        
        if not main_patched:
            print("[!] Failed to inject updater code into MainActivity.")
    else:
        print("[!] Could not find Main Activity to inject updater.")

    return bit_patched
