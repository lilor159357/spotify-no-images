import os
import re

def patch(decompiled_dir: str) -> bool:
    print(f"[*] Starting WhatsApp Kosher patch (Precision Sniper Mode v6 - FINAL)...")
    
    # 1. Profile Photos Block (Only PUBLIC methods)
    photos = _patch_profile_photos(decompiled_dir)
    
    # 2. Newsletter/Channels Block
    newsletter = _patch_newsletter_launcher(decompiled_dir)
    
    # 3. Updates Tab Removal (Safe ID Swap)
    tabs = _patch_home_tabs(decompiled_dir)
    
    # 4. Anti-Crash Fix
    spi = _patch_secure_pending_intent(decompiled_dir)

    results = [photos, newsletter, tabs, spi]
    
    if all(results):
        print("[SUCCESS] All patches applied successfully!")
        return True
    elif any(results):
        print("[!] PARTIAL SUCCESS: Some patches failed. Check logs.")
        return True 
    else:
        print("[FAILURE] All patches failed.")
        return False

# ---------------------------------------------------------
# 1. חסימת תמונות פרופיל
# השינוי ב-v6: סינון קפדני למתודות public בלבד.
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
        
        # Regex מעודכן: מחייב את המילה "public" בהגדרת המתודה.
        # קבוצה 1: חתימת המתודה (חייבת להיות public)
        # קבוצה 2: שורת הרגיסטרים
        bitmap_regex = r"(\.method public.*? \w+\(Landroid\/content\/Context;.*?\)Landroid\/graphics\/Bitmap;)(\s+\.registers \d+)"
        
        matches = list(re.finditer(bitmap_regex, content))
        patched_count = 0
        
        if matches:
            for match in matches:
                full_match = match.group(0)
                method_sig = match.group(1)
                registers_line = match.group(2)
                
                # Heuristic: F (Float) and J (Long) - מוודא שזה המפענח הכבד
                if 'F' in method_sig and 'J' in method_sig:
                    print(f"    -> Blocking PUBLIC decoder: {method_sig.split('(')[0]}")
                    
                    # הזרקת הקוד *אחרי* הרגיסטרים
                    replacement = f"{method_sig}{registers_line}\n    const/4 v0, 0x0\n    return-object v0"
                    content = content.replace(full_match, replacement)
                    patched_count += 1
            
            if patched_count == 0:
                print("    [!] Warning: Public decoder not found via heuristics. Searching broader signature...")
                # Fallback למקרה שהחתימה השתנתה מעט, אבל עדיין Public + Bitmap
                content = re.sub(bitmap_regex, r"\1\2\n    const/4 v0, 0x0\n    return-object v0", content)

        # חסימת הסטרים (A07) - נשאר זהה
        stream_regex = r"(\.method.*? \w+\(L[^;]+;Z\)Ljava\/io\/InputStream;)(\s+\.registers \d+)"
        if re.search(stream_regex, content):
            content = re.sub(stream_regex, r"\1\2\n    const/4 v0, 0x0\n    return-object v0", content)
            print("[+] Stream loader blocked.")
        
        with open(target_file, 'w', encoding='utf-8') as f: f.write(content)
        return True

    except Exception as e:
        print(f"[-] Error patching photos: {e}")
        return False

# ---------------------------------------------------------
# 2. נטרול ניוזלטר (Newsletter)
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
        # תופס: מתודה (Context, Uri) + רגיסטרים
        launcher_regex = r"(\.method.*? \w+\(Landroid\/content\/Context;Landroid\/net\/Uri;.*?\)V)(\s+\.registers \d+)"
        
        if re.search(launcher_regex, content):
            content, count = re.subn(launcher_regex, r"\1\2" + injection, content)
            print(f"[+] Blocked {count} Newsletter launcher entry points.")
        else:
            print("[-] Newsletter launcher signatures not found.")

        with open(target_file, 'w', encoding='utf-8') as f: f.write(content)
        return True
    except Exception as e:
        print(f"[-] Error patching newsletter launcher: {e}")
        return False

# ---------------------------------------------------------
# 3. הסרת טאב העדכונים (Home Tabs) - ID Swap
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
        
        # זיהוי טעינת 300 (0x12c) והחלפה ל-0
        updates_regex = r"(const/16 [vp]\d+, )0x12c(\s+.*?Ljava/util/AbstractCollection;->add)"
        
        if re.search(updates_regex, content, re.DOTALL):
            content = re.sub(updates_regex, r"\g<1>0x0\2", content, count=1, flags=re.DOTALL)
            print("[+] Home Tabs: Updates tab ID swapped to 0x0.")
        else:
            print("[-] Home Tabs: Updates tab pattern not found.")

        with open(target_file, 'w', encoding='utf-8') as f: f.write(content)
        return True

    except Exception as e:
        print(f"[-] Error patching home tabs: {e}")
        return False

# ---------------------------------------------------------
# 4. תיקון SecurePendingIntent (Anti-Crash)
# ---------------------------------------------------------
def _patch_secure_pending_intent(root_dir):
    anchor = "Please set reporter for SecurePendingIntent library"
    
    target_file = _find_file_by_string(root_dir, anchor)
    if not target_file:
        return True 

    try:
        with open(target_file, 'r', encoding='utf-8') as f: content = f.read()
        
        pattern = r"(if-nez [vp]\d+, (:cond_\w+))(\s+.*?)(const-string [vp]\d+, \"Please set reporter)"
        
        if re.search(pattern, content, re.DOTALL):
            content = re.sub(pattern, r"goto \2\3\4", content, count=1, flags=re.DOTALL)
            print(f"[+] SecurePendingIntent patched.")
            with open(target_file, 'w', encoding='utf-8') as f: f.write(content)
        
        return True

    except Exception as e:
        print(f"[-] Error patching SecurePendingIntent: {e}")
        return False

# ---------------------------------------------------------
# Helpers
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
