import os
import re
import shutil

def patch(decompiled_dir: str) -> bool:
    print(f" Scanning for Spotify target files in {decompiled_dir}...")
    
    # מיקום התיקייה הנוכחית של הסקריפט (apps/spotify)
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    payload_dir = os.path.join(current_script_dir, "updater_payload")

    # ==========================================
    # 1. החלת הפאצ'ים (מחיקת תמונות, וידאו, ו-ShareWorker)
    # ==========================================
    target_worker_file = "sharehousekeepingworker.smali"
    for root, dirs, files in os.walk(decompiled_dir):
        for filename in files:
            if filename.lower() == target_worker_file:
                try:
                    os.remove(os.path.join(root, filename))
                    print(f" Deleted {filename}")
                except Exception as e:
                    print(f" Failed to delete {filename}: {e}")

        if "EsImage$ImageData.smali" in files:
            file_path = os.path.join(root, "EsImage$ImageData.smali")
            with open(file_path, 'r', encoding='utf-8') as f: content = f.read()
            new_content = re.sub(
                r"(\.method public final getData\(\)L.*?;.*?)(\.line \d+.*?iget-object\d+,\d+, Lcom\/spotify\/image\/esperanto\/proto\/EsImage\$ImageData;->.*?:L.*?;)(.*?.end method)",
                r"\1\n    const/4 v0, 0x0\n    return-object v0\n\3", content, flags=re.DOTALL)
            if new_content != content:
                with open(file_path, 'w', encoding='utf-8') as f: f.write(new_content)
                print(" Patched EsImage$ImageData")

        if "VideoSurfaceView.smali" in files:
            file_path = os.path.join(root, "VideoSurfaceView.smali")
            with open(file_path, 'r', encoding='utf-8') as f: content = f.read()
            new_content = re.sub(
                r"(\.method public getTextureView\(\)Landroid\/view\/TextureView;.*?)(\.line \d+.*?iget-object\d+,\d+, Lcom\/spotify\/betamax\/player\/VideoSurfaceView;->.*?:Landroid\/view\/TextureView;)(.*?.end method)",
                r"\1\n    const/4 v0, 0x0\n    return-object v0\n\3", content, flags=re.DOTALL)
            if new_content != content:
                with open(file_path, 'w', encoding='utf-8') as f: f.write(new_content)
                print(" Patched VideoSurfaceView")

    # ==========================================
    # 2. העתקת קבצי ה-Updater לתוך ה-APK
    # ==========================================
    if os.path.exists(payload_dir):
        try:
            # העתקת כל תיקיית Smali
            src_smali = os.path.join(payload_dir, "smali")
            dst_smali = os.path.join(decompiled_dir, "smali")
            shutil.copytree(src_smali, dst_smali, dirs_exist_ok=True)
            
            # העתקת תיקיית ה-Res (עבור ה-XML)
            src_res = os.path.join(payload_dir, "res")
            dst_res = os.path.join(decompiled_dir, "res")
            shutil.copytree(src_res, dst_res, dirs_exist_ok=True)
            
            print(" Updater payload files copied successfully.")
        except Exception as e:
            print(f" Failed to copy updater payload: {e}")
            return False
    else:
        print(" Updater payload directory not found in repo! Skipping updater injection.")

    # ==========================================
    # 3. עדכון ה-AndroidManifest.xml
    # ==========================================
    manifest_path = os.path.join(decompiled_dir, "AndroidManifest.xml")
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_content = f.read()

        # הוספת הרשאת התקנה אם לא קיימת
        if "android.permission.REQUEST_INSTALL_PACKAGES" not in manifest_content:
            manifest_content = manifest_content.replace(
                '<application', 
                '<uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES"/>\n    <application'
            )

        # הוספת הסרוויס וה-Provider
        manifest_components = """
        <service android:name="com.spotify.updater.DownloadService" />
        <provider
            android:name="com.spotify.updater.GenericFileProvider"
            android:authorities="com.spotify.music.provider"
            android:exported="false"
            android:grantUriPermissions="true">
            <meta-data
                android:name="android.support.FILE_PROVIDER_PATHS"
                android:resource="@xml/provider_paths" />
        </provider>
"""
        if "com.spotify.updater.GenericFileProvider" not in manifest_content:
            manifest_content = manifest_content.replace(
                '</application>', 
                f'{manifest_components}\n    </application>'
            )

        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(manifest_content)
        print(" AndroidManifest.xml updated successfully.")
    except Exception as e:
        print(f" Failed to patch AndroidManifest.xml: {e}")
        return False

    # ==========================================
    # 4. הפעלת ה-Updater בכניסה לאפליקציה (SpotifyMainActivity)
    # ==========================================
    main_activity_patched = False
    for root, dirs, files in os.walk(decompiled_dir):
        if "SpotifyMainActivity.smali" in files:
            main_activity_path = os.path.join(root, "SpotifyMainActivity.smali")
            try:
                with open(main_activity_path, 'r', encoding='utf-8') as f:
                    main_smali = f.read()
                
                # בידוד כל הבלוק של פונקציית onCreate מתחילתה ועד סופה
                method_pattern = re.compile(r"(\.method.*?onCreate\(Landroid/os/Bundle;\)V)(.*?)(\.end method)", re.DOTALL)
                match = method_pattern.search(main_smali)
                
                if match:
                    method_signature = match.group(1)
                    method_body = match.group(2)
                    end_method = match.group(3)
                    
                    if "Lcom/spotify/updater/Updater;->check" not in method_body:
                        # חיפוש ה-return-void *האחרון* בתוך גוף הפונקציה (מהסוף להתחלה)
                        last_return_idx = method_body.rfind("return-void")
                        
                        if last_return_idx != -1:
                            # קוד ההזרקה
                            updater_call = "\n    # Inject Updater check\n    invoke-static {p0}, Lcom/spotify/updater/Updater;->check(Landroid/content/Context;)V\n\n    "
                            
                            # חותכים את גוף הפונקציה לשניים בנקודת ה-return-void האחרונה, ושותלים את הקוד באמצע
                            new_method_body = (
                                method_body + 
                                updater_call + 
                                method_body
                            )
                            
                            # מרכיבים חזרה את כל קובץ ה-Smali
                            new_main_smali = main_smali + method_signature + new_method_body + end_method + main_smali
                            
                            with open(main_activity_path, 'w', encoding='utf-8') as f:
                                f.write(new_main_smali)
                                
                            main_activity_patched = True
                            print(" Updater call injected before the LAST return-void in SpotifyMainActivity.onCreate()")
                        else:
                            print(" Could not find 'return-void' inside onCreate()")
                    else:
                        print(" Updater call already exists in SpotifyMainActivity.smali (Skipping injection)")
                        main_activity_patched = True
                else:
                    print(" Could not find onCreate() method in SpotifyMainActivity.smali")
                    
            except Exception as e:
                print(f" Failed to process SpotifyMainActivity: {e}")
            break # מצאנו את הקובץ, אפשר לצאת מהלולאה החיצונית
            
    if not main_activity_patched:
        print(" Warning: Could not inject Updater into SpotifyMainActivity.")

    return True
