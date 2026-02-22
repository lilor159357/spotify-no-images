import os
import re
import shutil
import xml.etree.ElementTree as ET

def get_package_name(manifest_path: str) -> str:
    """קורא את ה-AndroidManifest.xml כדי לחלץ את שם החבילה של האפליקציה."""
    try:
        tree = ET.parse(manifest_path)
        root = tree.getroot()
        return root.get('package')
    except Exception as e:
        print(f"[-] Could not parse package name from manifest: {e}")
        return None

def get_main_activity_smali_path(manifest_path: str) -> str:
    """סורק את ה-AndroidManifest.xml כדי למצוא אוטומטית את מסך הפתיחה (MainActivity)."""
    try:
        tree = ET.parse(manifest_path)
        root = tree.getroot()
        ns = {'android': 'http://schemas.android.com/apk/res/android'}
        
        for activity in root.iter('activity'):
            is_main = False
            is_launcher = False
            for intent_filter in activity.iter('intent-filter'):
                for action in intent_filter.iter('action'):
                    if action.get(f"{{{ns['android']}}}name") == "android.intent.action.MAIN":
                        is_main = True
                for category in intent_filter.iter('category'):
                    if category.get(f"{{{ns['android']}}}name") == "android.intent.category.LAUNCHER":
                        is_launcher = True
            
            if is_main and is_launcher:
                activity_name = activity.get(f"{{{ns['android']}}}name")
                if activity_name:
                    # טיפול בשם אקטיביטי יחסי (למשל ".MainActivity")
                    if activity_name.startswith("."):
                        activity_name = root.get('package') + activity_name
                    # המרה מפורמט ג'אווה לפורמט נתיב קובץ סמאלי
                    return activity_name.replace('.', '/') + ".smali"
    except Exception as e:
        print(f"[-] Could not parse main activity from manifest: {e}")
    return None

def patch(decompiled_dir: str) -> bool:
    print(f"[*] Starting UNIVERSAL updater patch process in {decompiled_dir}...")
    
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    payload_dir = os.path.join(current_script_dir, "updater_payload")
    manifest_path = os.path.join(decompiled_dir, "AndroidManifest.xml")

    # חילוץ אוטומטי של שם האפליקציה (לפי שם התיקייה שבה נמצא ה-patch.py הזה)
    app_id = os.path.basename(current_script_dir)

    # הכתובות הדינמיות של הריפו שלך
    repo_owner = "cfopuser"
    repo_name = "app-store"
    
    version_txt_url = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/refs/heads/main/apps/{app_id}/version.txt"
    download_prefix = f"https://github.com/{repo_owner}/{repo_name}/releases/download/{app_id}-v"
    download_middle = f"/{app_id}-patched-"

    # ==========================================
    # 0. קבלת נתונים דינמיים מה-Manifest
    # ==========================================
    package_name = get_package_name(manifest_path)
    if not package_name:
        print("[-] CRITICAL: Failed to get package name. Aborting.")
        return False
    
    provider_authority = f"{package_name}.provider"
    target_activity_smali = get_main_activity_smali_path(manifest_path)
    
    print(f"[i] App ID: {app_id}")
    print(f"[i] Detected Package Name: {package_name}")
    print(f"[i] Using Provider Authority: {provider_authority}")
    print(f"[i] Detected Main Activity: {target_activity_smali}")

    # ==========================================
    # 1. העתקת קבצי ה-Updater + החלפת פלייסחולדרים
    # ==========================================
    if not os.path.exists(payload_dir):
        print("[!] Warning: Updater payload directory not found! Skipping updater injection.")
        return False

    try:
        # יצירת תיקיית smali_classes חדשה ופנויה עבור העדכון
        max_dex = max(
            [int(d.replace("smali_classes", "")) for d in os.listdir(decompiled_dir) if d.startswith("smali_classes") and d.replace("smali_classes", "").isdigit()]
            or [0]
        )
        next_smali_dir = f"smali_classes{max_dex + 1}"
        
        # העתקה לתיקיית storeautoupdater
        dst_smali_root = os.path.join(decompiled_dir, next_smali_dir, "storeautoupdater")
        src_updater_files = os.path.join(payload_dir, "smali", "storeautoupdater")
        
        if os.path.exists(src_updater_files):
            shutil.copytree(src_updater_files, dst_smali_root, dirs_exist_ok=True)
        else:
            print("[-] CRITICAL: 'storeautoupdater' directory not found in payload/smali.")
            return False
            
        # העתקת משאבי ה-XML
        src_res = os.path.join(payload_dir, "res")
        dst_res = os.path.join(decompiled_dir, "res")
        shutil.copytree(src_res, dst_res, dirs_exist_ok=True)
        
        print(f"[+] Updater payload files copied to {next_smali_dir}/storeautoupdater.")

        # מעבר על קבצי הסמאלי והחלפת הפלייסחולדרים בזמן אמת
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
        print(f"[+] Replaced all dynamic placeholders successfully.")

    except Exception as e:
        print(f"[-] Failed to copy or patch updater payload: {e}")
        return False

    # ==========================================
    # 2. עדכון ה-AndroidManifest.xml
    # ==========================================
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_content = f.read()

        # הרשאת התקנת אפליקציות
        if 'android.permission.REQUEST_INSTALL_PACKAGES' not in manifest_content:
            manifest_content = manifest_content.replace(
                '<application', 
                '<uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES"/>\n    <application'
            )

        # הזרקת הסרוויס והפרובידר עם החבילה המיוחדת שלנו
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
        print("[+] AndroidManifest.xml updated successfully.")
    except Exception as e:
        print(f"[-] Failed to patch AndroidManifest.xml: {e}")
        return False

    # ==========================================
    # 3. הפעלת ה-Updater בכניסה לאפליקציה (MainActivity)
    # ==========================================
    if not target_activity_smali:
        print("[!] Warning: Could not detect Main Activity automatically.")
        return False

    main_activity_patched = False
    target_filename = os.path.basename(target_activity_smali)

    for root, _, files in os.walk(decompiled_dir):
        if target_filename in files:
            # בדיקה האם זה באמת הנתיב הנכון למקרה שיש כמה קבצים עם אותו שם
            full_path = os.path.join(root, target_filename)
            if target_activity_smali.replace('/', os.sep) not in full_path:
                continue

            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    main_smali_content = f.read()

                # בודק אם הזרקנו כבר
                if "Lstoreautoupdater/Updater;->check" in main_smali_content:
                    print("[i] Updater call already exists. No changes needed.")
                    main_activity_patched = True
                else:
                    # מחפש את מתודת onCreate
                    method_pattern = re.compile(r"(\.method.*?onCreate\(Landroid/os/Bundle;\)V)(.*?)(\.end method)", re.DOTALL)
                    match = method_pattern.search(main_smali_content)
                    
                    if match:
                        method_body = match.group(2)
                        # מחפש את ה-return-void האחרון לפני סגירת הפונקציה
                        last_return_idx = method_body.rfind("return-void")
                        
                        if last_return_idx != -1:
                            updater_call = (
                                "\n\n    # --- START INJECTION (Universal Updater) ---\n"
                                "    move-object v0, p0\n"
                                "    invoke-static {v0}, Lstoreautoupdater/Updater;->check(Landroid/content/Context;)V\n"
                                "    # --- END INJECTION ---\n\n    "
                            )
                            
                            new_method_body = method_body[:last_return_idx] + updater_call + method_body[last_return_idx:]
                            new_full_method = match.group(1) + new_method_body + match.group(3)
                            main_smali_content = main_smali_content.replace(match.group(0), new_full_method, 1)

                            with open(full_path, 'w', encoding='utf-8') as f:
                                f.write(main_smali_content)
                                
                            main_activity_patched = True
                            print(f"[+] Updater call injected successfully into {target_activity_smali}")
                        else:
                            print(f"[-] Could not find 'return-void' in {target_filename} onCreate().")
                    else:
                        print(f"[-] Could not find onCreate() in {target_filename}.")
            except Exception as e:
                print(f"[-] Failed to process {target_filename}: {e}")
            break
            
    if not main_activity_patched:
        print(f"[-] Error: Failed to patch {target_activity_smali}.")
        return False

    return True
