import os
import re

def patch(decompiled_dir: str) -> bool:
    print(f"[*] Starting WhatsApp Kosher patch (Precision Sniper Mode v9 - LOCALS FIX)...")
    
    # ביצוע הפאצ'ים
    photos = _patch_profile_photos(decompiled_dir)
    newsletter = _patch_newsletter_launcher(decompiled_dir)
    tabs = _patch_home_tabs(decompiled_dir)
    spi = _patch_secure_pending_intent(decompiled_dir)

    results = [photos, newsletter, tabs, spi]
    
    if all(results):
        print("\n[SUCCESS] All patches applied successfully!")
        return True
    elif any(results):
        print("\n[!] PARTIAL SUCCESS: Some patches failed. Check logs.")
        return True 
    else:
        print("\n[FAILURE] All patches failed.")
        return False

# ---------------------------------------------------------
# 1. חסימת תמונות פרופיל
# Based on extracted file: LX/0lK.smali
# ---------------------------------------------------------
def _patch_profile_photos(root_dir):
    anchor = 'contactPhotosBitmapManager/getphotofast/'
    print(f"\n[1] Scanning for Photo Manager ({anchor})...")
    
    target_file = _find_file_by_string(root_dir, anchor)
    if not target_file:
        print("    [-] File not found.")
        return False

    try:
        with open(target_file, 'r', encoding='utf-8') as f: content = f.read()
        
        # Regex מותאם ל-locals/registers
        # תופס: מתודה שמקבלת Context ומחזירה Bitmap, פלוס שורת locals/registers
        
        # A04 Target: (Context, Obj, String, F, I, J, Z, Z) -> Bitmap
        # השימוש ב-L[^;]+; מאפשר לתפוס כל שם של אובייקט (LX/0IB)
        bitmap_regex = r"(\.method public final \w+\(Landroid\/content\/Context;L[^;]+;Ljava\/lang\/String;FIJZZ\)Landroid\/graphics\/Bitmap;)(\s+(?:\.locals|\.registers) \d+)"
        
        if re.search(bitmap_regex, content):
            # הזרקה: const/4 v0, 0x0 return-object v0
            content = re.sub(bitmap_regex, r"\1\2\n    const/4 v0, 0x0\n    return-object v0", content)
            print("    [+] Public Bitmap decoder (A04) blocked.")
        else:
            print("    [-] Public Bitmap decoder signature not found (Check logs vs file).")

        # A07 Target: (Obj, Z) -> InputStream
        stream_regex = r"(\.method public final \w+\(L[^;]+;Z\)Ljava\/io\/InputStream;)(\s+(?:\.locals|\.registers) \d+)"
        
        if re.search(stream_regex, content):
            content = re.sub(stream_regex, r"\1\2\n    const/4 v0, 0x0\n    return-object v0", content)
            print("    [+] Stream loader (A07) blocked.")
        else:
            print("    [-] Stream loader signature not found.")
        
        with open(target_file, 'w', encoding='utf-8') as f: f.write(content)
        return True

    except Exception as e:
        print(f"    [-] Error: {e}")
        return False

# ---------------------------------------------------------
# 2. נטרול ניוזלטר (Newsletter)
# Based on extracted file: LX/AhT.smali
# ---------------------------------------------------------
def _patch_newsletter_launcher(root_dir):
    anchor = "NewsletterLinkLauncher/type not handled"
    print(f"\n[2] Scanning for Newsletter Launcher ({anchor})...")
    
    target_file = _find_file_by_string(root_dir, anchor)
    if not target_file:
        print("    [-] File not found.")
        return False

    try:
        with open(target_file, 'r', encoding='utf-8') as f: content = f.read()
        
        injection = "\n    return-void"
        
        # A01 Target: (Context, Uri) -> Void
        entry_regex = r"(\.method public final \w+\(Landroid\/content\/Context;Landroid\/net\/Uri;\)V)(\s+(?:\.locals|\.registers) \d+)"
        
        if re.search(entry_regex, content):
            content = re.sub(entry_regex, r"\1\2" + injection, content)
            print("    [+] Deep Link entry (A01) killed.")
        else:
            print("    [-] Deep Link entry signature not found.")

        # A02 Target: (Context, Uri, Obj, Integer, Long, String, Int, Long) -> Void
        main_regex = r"(\.method public final \w+\(Landroid\/content\/Context;Landroid\/net\/Uri;L[^;]+;Ljava\/lang\/Integer;Ljava\/lang\/Long;Ljava\/lang\/String;IJ\)V)(\s+(?:\.locals|\.registers) \d+)"
        
        if re.search(main_regex, content):
            content = re.sub(main_regex, r"\1\2" + injection, content)
            print("    [+] Main Logic (A02) killed.")
        else:
            print("    [-] Main Logic signature not found.")

        with open(target_file, 'w', encoding='utf-8') as f: f.write(content)
        return True
    except Exception as e:
        print(f"    [-] Error: {e}")
        return False

# ---------------------------------------------------------
# 3. הסרת טאב העדכונים (Home Tabs)
# ---------------------------------------------------------
def _patch_home_tabs(root_dir):
    anchor = "Tried to set badge for invalid tab id"
    print(f"\n[3] Scanning for Home Tabs ({anchor})...")
    
    target_file = _find_file_by_string(root_dir, anchor)
    if not target_file:
        print("    [-] File not found.")
        return False

    try:
        with open(target_file, 'r', encoding='utf-8') as f: content = f.read()
        
        # זיהוי טעינת 300 (0x12c) והחלפה ל-0 (0x0)
        # זה הפתרון הבטוח שמונע שגיאות רגיסטרים
        updates_regex = r"(const/16 [vp]\d+, )0x12c(\s+.*?Ljava/util/AbstractCollection;->add)"
        
        if re.search(updates_regex, content, re.DOTALL):
            content = re.sub(updates_regex, r"\g<1>0x0\2", content, count=1, flags=re.DOTALL)
            print("    [+] Home Tabs: Updates tab ID swapped to 0x0.")
        else:
            print("    [-] Home Tabs: Pattern not found.")

        with open(target_file, 'w', encoding='utf-8') as f: f.write(content)
        return True

    except Exception as e:
        print(f"    [-] Error: {e}")
        return False

# ---------------------------------------------------------
# 4. תיקון SecurePendingIntent
# ---------------------------------------------------------
def _patch_secure_pending_intent(root_dir):
    anchor = "Please set reporter for SecurePendingIntent library"
    print(f"\n[4] Scanning for SecurePendingIntent ({anchor})...")
    
    target_file = _find_file_by_string(root_dir, anchor)
    if not target_file:
        print("    [i] File not found (might be non-issue).")
        return True 

    try:
        with open(target_file, 'r', encoding='utf-8') as f: content = f.read()
        
        pattern = r"(if-nez [vp]\d+, (:cond_\w+))(\s+.*?)(const-string [vp]\d+, \"Please set reporter)"
        
        if re.search(pattern, content, re.DOTALL):
            content = re.sub(pattern, r"goto \2\3\4", content, count=1, flags=re.DOTALL)
            print("    [+] Check bypassed (if-nez -> goto).")
            with open(target_file, 'w', encoding='utf-8') as f: f.write(content)
        else:
            print("    [-] Pattern not found.")
        
        return True

    except Exception as e:
        print(f"    [-] Error: {e}")
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
