import os
import re

def patch(decompiled_dir: str) -> bool:
    """
    Applies 'Kosher' patches to WhatsApp:
    1. Blocks Profile Photos (Thumbnails & Full View) - Robust version.
    2. Kills Newsletter/Channel Links Launcher.
    3. Removes ONLY Updates and Channels Tabs (Leaves Communities active).
    4. Fixes SecurePendingIntent Crash (LX/0sw).
    """
    print(f"[*] Starting WhatsApp Kosher patch & Crash Fixes...")
    
    photos_patched = _patch_profile_photos(decompiled_dir)
    newsletter_launcher_patched = _patch_newsletter_launcher(decompiled_dir)
    tabs_patched = _patch_home_tabs(decompiled_dir)
    spi_patched = _patch_secure_pending_intent(decompiled_dir)

    if photos_patched and newsletter_launcher_patched and tabs_patched and spi_patched:
        print("[SUCCESS] All patches applied successfully!")
        return True
    elif photos_patched or newsletter_launcher_patched or tabs_patched or spi_patched:
        print("[!] PARTIAL SUCCESS: Some patches failed. Check logs.")
        return True 
    else:
        print("[FAILURE] All patches failed.")
        return False

# ---------------------------------------------------------
# 1. חסימת תמונות פרופיל (גרסה עמידה לשינויי גרסאות)
# ---------------------------------------------------------
def _patch_profile_photos(root_dir):
    anchor = 'contactPhotosBitmapManager/getphotofast/'
    print(f"[*] Scanning for Photo Manager using anchor: '{anchor}'...")
    
    target_file = _find_file_by_string(root_dir, anchor)
    if not target_file:
        print("[-] Photo Manager file not found.")
        return False

    try:
        with open(target_file, 'r', encoding='utf-8') as f: content = f.read()
        
        # מחפש כל מתודה שמחזירה תמונה (Bitmap) בקובץ הזה והופך אותה ל-Null
        bmp_regex = r"(\.method (?:public|protected|private) (?:final )?\w+\([^)]*\)Landroid/graphics/Bitmap;\s*\.registers \d+)"
        content, bmp_subs = re.subn(bmp_regex, r"\1\n    const/4 v0, 0x0\n    return-object v0", content)
        
        # מחפש כל מתודה שמחזירה זרם נתונים (InputStream) בקובץ הזה והופך אותה ל-Null
        stream_regex = r"(\.method (?:public|protected|private) (?:final )?\w+\([^)]*\)Ljava/io/InputStream;\s*\.registers \d+)"
        content, stream_subs = re.subn(stream_regex, r"\1\n    const/4 v0, 0x0\n    return-object v0", content)

        if bmp_subs > 0 or stream_subs > 0:
            print(f"[+] Profile Photos: Blocked {bmp_subs} Bitmap loaders and {stream_subs} Stream loaders.")
        else:
            print("[-] Profile Photos: No methods matched the regex.")

        with open(target_file, 'w', encoding='utf-8') as f: f.write(content)
        return True
    except Exception as e:
        print(f"[-] Error patching photos: {e}")
        return False

# ---------------------------------------------------------
# 2. חיסול מנגנון פתיחת הערוצים (Launcher)
# ---------------------------------------------------------
def _patch_newsletter_launcher(root_dir):
    anchor = "NewsletterLinkLauncher/type not handled"
    print(f"[*] Scanning for Newsletter Launcher using anchor: '{anchor}'...")
    
    target_file = _find_file_by_string(root_dir, anchor)
    if not target_file:
        print("[-] Newsletter Launcher file not found.")
        return False

    try:
        with open(target_file, 'r', encoding='utf-8') as f: content = f.read()
        injection = "\n    return-void"

        # חסימת Deep Links (פונקציה שמקבלת Uri)
        entry_regex = r"(\.method public final \w+\(Landroid/content/Context;Landroid/net/Uri;\)V\s*\.registers \d+)"
        content = re.sub(entry_regex, r"\1" + injection, content)

        # חסימת הפעולה המרכזית של פתיחת הערוץ
        main_regex = r"(\.method public final \w+\(Landroid/content/Context;Landroid/net/Uri;[^)]*\)V\s*\.registers \d+)"
        content = re.sub(main_regex, r"\1" + injection, content)

        print("[+] Newsletter Launcher logic killed.")
        with open(target_file, 'w', encoding='utf-8') as f: f.write(content)
        return True
    except Exception as e:
        print(f"[-] Error patching newsletter launcher: {e}")
        return False

# ---------------------------------------------------------
# 3. הסרת הלשוניות (טאבים) מהמסך הראשי
# ---------------------------------------------------------
def _patch_home_tabs(root_dir):
    anchor = "Tried to set badge for invalid tab id"
    print(f"[*] Scanning for Home Tabs Manager using anchor: '{anchor}'...")
    
    target_file = _find_file_by_string(root_dir, anchor)
    if not target_file:
        print("[-] Home Tabs Manager file not found.")
        return False

    try:
        with open(target_file, 'r', encoding='utf-8') as f: content = f.read()
        
        # 0xc8 = 200 = Updates / Status
        # 0x1f4 = 500 = Channels
        # הורדנו מפה את 0x12c (300) כדי שהקהילות יישארו פעילות!
        tabs_to_hide = {"0xc8": "Updates", "0x1f4": "Channels"}
        
        for hex_id, name in tabs_to_hide.items():
            regex = rf"(const/16 [vp]\d+, {hex_id}\s+.*?)(invoke-virtual \{{\[vp\]\d+, \[vp\]\d+\}}, Ljava/util/AbstractCollection;->add\(Ljava/lang/Object;\)Z)"
            
            if re.search(regex, content, re.DOTALL):
                content = re.sub(regex, r"\1# \2", content, flags=re.DOTALL)
                print(f"[+] Home Tabs: {name} tab ({hex_id}) removed.")
            else:
                print(f"[-] Home Tabs: {name} tab pattern not found.")

        with open(target_file, 'w', encoding='utf-8') as f: f.write(content)
        return True

    except Exception as e:
        print(f"[-] Error patching home tabs: {e}")
        return False

# ---------------------------------------------------------
# 4. תיקון SecurePendingIntent
# ---------------------------------------------------------
def _patch_secure_pending_intent(root_dir):
    anchor = "Please set reporter for SecurePendingIntent library"
    print(f"[*] Scanning for SecurePendingIntent logic using anchor: '{anchor}'...")
    
    target_file = _find_file_by_string(root_dir, anchor)
    if not target_file:
        print("[-] SecurePendingIntent file not found.")
        return False

    try:
        with open(target_file, 'r', encoding='utf-8') as f: content = f.read()
        
        pattern = r"(if-nez [vp]\d+, (:cond_\w+))(\s+.+?Please set reporter for SecurePendingIntent library)"
        if re.search(pattern, content, re.DOTALL):
            new_content = re.sub(pattern, r"goto \2\3", content, count=1, flags=re.DOTALL)
            with open(target_file, 'w', encoding='utf-8') as f: f.write(new_content)
            print(f"[+] SecurePendingIntent patched.")
            return True
        else:
            return False

    except Exception as e:
        print(f"[-] Error patching SecurePendingIntent: {e}")
        return False

# ---------------------------------------------------------
# פונקציית עזר
# ---------------------------------------------------------
def _find_file_by_string(root_dir, search_string):
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".smali"):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        if search_string in f.read():
                            return path
                except:
                    continue
    return None
