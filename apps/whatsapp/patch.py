import os
import re

def patch(decompiled_dir: str) -> bool:
    print(f"[*] Starting WhatsApp Kosher patch (Precision Sniper Mode)...")
    
    # ביצוע הפאצ'ים
    photos = _patch_profile_photos(decompiled_dir)
    newsletter = _patch_newsletter_launcher(decompiled_dir)
    tabs = _patch_home_tabs(decompiled_dir)
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
# 1. חסימת תמונות פרופיל - זיהוי כירורגי לפי פרמטרים
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
        
        # --- זיהוי A04 (Bitmap) ---
        # הטריק: אנחנו מחפשים את סיומת הפרמטרים הייחודית: FIJZZ
        # F=Float, I=Int, J=Long, Z=Boolean, Z=Boolean
        # L[^;]+; תופס את האובייקט LX/0IB לא משנה מה שמו
        bmp_fingerprint = r"(\.method.*? \w+\(Landroid\/content\/Context;L[^;]+;Ljava\/lang\/String;FIJZZ\)Landroid\/graphics\/Bitmap;\s*\.registers \d+)"
        
        if re.search(bmp_fingerprint, content):
            content = re.sub(bmp_fingerprint, r"\1\n    const/4 v0, 0x0\n    return-object v0", content, count=1)
            print("[+] Profile Photos: Specific Bitmap loader (A04) identified and blocked.")
        else:
            print("[-] Profile Photos: Specific Bitmap signature (FIJZZ) not found. Trying fallback...")
            # Fallback: אם הוא לא מוצא את הספציפי, נסה לחסום כל מה שמחזיר Bitmap בקובץ הזה
            fallback_regex = r"(\.method .*? \w+\(.*?\).*?Landroid\/graphics\/Bitmap;\s*\.registers \d+)"
            content, count = re.subn(fallback_regex, r"\1\n    const/4 v0, 0x0\n    return-object v0", content)
            print(f"[i] Fallback: Blocked {count} generic Bitmap methods.")

        # --- זיהוי A07 (InputStream) ---
        # הטריק: אובייקט אחד ואחריו בולאן (Z)
        stream_fingerprint = r"(\.method.*? \w+\(L[^;]+;Z\)Ljava\/io\/InputStream;\s*\.registers \d+)"
        
        if re.search(stream_fingerprint, content):
            content = re.sub(stream_fingerprint, r"\1\n    const/4 v0, 0x0\n    return-object v0", content, count=1)
            print("[+] Profile Photos: Specific Stream loader (A07) identified and blocked.")
        else:
            print("[-] Profile Photos: Specific Stream signature not found.")

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

        # חסימת Deep Links (Context, Uri)
        entry_regex = r"(\.method public final \w+\(Landroid\/content\/Context;Landroid\/net\/Uri;\)V\s*\.registers \d+)"
        if re.search(entry_regex, content):
            content = re.sub(entry_regex, r"\1" + injection, content, count=1)
            print("[+] Newsletter: Entry point (Deep Links) killed.")
        else:
             print("[-] Newsletter: Entry point signature not found.")

        # חסימת Main Logic - חתימה עם הרבה פרמטרים שמסתיימת ב-IJ
        main_regex = r"(\.method public final \w+\(Landroid\/content\/Context;Landroid\/net\/Uri;.*?IJ\)V\s*\.registers \d+)"
        if re.search(main_regex, content):
            content = re.sub(main_regex, r"\1" + injection, content, count=1)
            print("[+] Newsletter: Main logic launcher killed.")
        else:
            print("[-] Newsletter: Main logic signature not found.")

        with open(target_file, 'w', encoding='utf-8') as f: f.write(content)
        return True
    except Exception as e:
        print(f"[-] Error patching newsletter launcher: {e}")
        return False

# ---------------------------------------------------------
# 3. הסרת לשונית העדכונים (0x12c) בלבד
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
        
        # מזהה 0x12c = עדכונים
        updates_regex = r"(const/16 [vp]\d+, 0x12c\s+.*?)(invoke-virtual \{[vp]\d+, [vp]\d+\}, Ljava/util/AbstractCollection;->add\(Ljava/lang/Object;\)Z)"
        
        if re.search(updates_regex, content, re.DOTALL):
            content = re.sub(updates_regex, r"\1# \2", content, count=1, flags=re.DOTALL)
            print("[+] Home Tabs: Updates/Channels tab (0x12c) removed.")
        else:
            print("[-] Home Tabs: Updates tab pattern not found.")

        with open(target_file, 'w', encoding='utf-8') as f: f.write(content)
        return True

    except Exception as e:
        print(f"[-] Error patching home tabs: {e}")
        return False

# ---------------------------------------------------------
# 4. תיקון קריסת SecurePendingIntent
# ---------------------------------------------------------
def _patch_secure_pending_intent(root_dir):
    anchor = "Please set reporter for SecurePendingIntent library"
    # לא מדפיסים לוגים אם הקובץ לא נמצא, זה תיקון אופציונלי
    
    target_file = _find_file_by_string(root_dir, anchor)
    if not target_file:
        return True 

    try:
        with open(target_file, 'r', encoding='utf-8') as f: content = f.read()
        
        pattern = r"(if-nez [vp]\d+, (:cond_\w+))(\s+.+?Please set reporter for SecurePendingIntent library)"
        if re.search(pattern, content, re.DOTALL):
            new_content = re.sub(pattern, r"goto \2\3", content, count=1, flags=re.DOTALL)
            with open(target_file, 'w', encoding='utf-8') as f: f.write(new_content)
            print(f"[+] SecurePendingIntent patched.")
            return True
        return True

    except Exception as e:
        print(f"[-] Error patching SecurePendingIntent: {e}")
        return False

# ---------------------------------------------------------
# פונקציות עזר
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
