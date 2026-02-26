import os
import re

def patch(decompiled_dir: str) -> bool:
    print(f"[*] Starting WhatsApp Kosher patch (Precision Sniper Mode v12 - FINAL TAB FIX)...")
    
    # ביצוע הפאצ'ים
    photos = _patch_profile_photos(decompiled_dir)
    newsletter = _patch_newsletter_launcher(decompiled_dir)
    tabs = _patch_home_tabs(decompiled_dir)
    spi = _patch_secure_pending_intent(decompiled_dir)

    results =[photos, newsletter, tabs, spi]
    
    if all(results):
        print("\n[SUCCESS] All patches were applied successfully!")
        return True
    else:
        print("\n[FAILURE] One or more critical patches failed. Check logs.")
        return False

# ---------------------------------------------------------
# 1. חסימת תמונות פרופיל
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
        original_content = content
        
        declaration_pattern = r"(\s+(?:\.locals|\.registers) \d+)"

        bitmap_regex = r"(\.method public final \w+\(Landroid\/content\/Context;L[^;]+;Ljava\/lang\/String;FIJZZ\)Landroid\/graphics\/Bitmap;)" + declaration_pattern
        content = re.sub(bitmap_regex, r"\1\2\n    const/4 v0, 0x0\n    return-object v0", content)

        stream_regex = r"(\.method public final \w+\(L[^;]+;Z\)Ljava\/io\/InputStream;)" + declaration_pattern
        content = re.sub(stream_regex, r"\1\2\n    const/4 v0, 0x0\n    return-object v0", content)
        
        if content != original_content:
            print("    [+] Photo loaders blocked successfully.")
            with open(target_file, 'w', encoding='utf-8') as f: f.write(content)
            return True
        else:
            print("    [-] Photo loader signatures not found.")
            return False

    except Exception as e:
        print(f"    [-] Error: {e}")
        return False

# ---------------------------------------------------------
# 2. נטרול ניוזלטר (Newsletter Launcher)
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
        original_content = content
        
        injection = "\n    return-void"
        declaration_pattern = r"(\s+(?:\.locals|\.registers) \d+)"
        
        entry_regex = r"(\.method public final \w+\(Landroid\/content\/Context;Landroid\/net\/Uri;\)V)" + declaration_pattern
        content = re.sub(entry_regex, r"\1\2" + injection, content)

        main_regex = r"(\.method public final \w+\(Landroid\/content\/Context;Landroid\/net\/Uri;L[^;]+;Ljava\/lang\/Integer;Ljava\/lang\/Long;Ljava\/lang\/String;IJ\)V)" + declaration_pattern
        content = re.sub(main_regex, r"\1\2" + injection, content)

        if content != original_content:
            print("    [+] Newsletter launcher methods killed.")
            with open(target_file, 'w', encoding='utf-8') as f: f.write(content)
            return True
        else:
            print("    [-] Newsletter launcher signatures not found.")
            return False

    except Exception as e:
        print(f"    [-] Error: {e}")
        return False

# ---------------------------------------------------------
# 3. הסרת טאב העדכונים (Home Tabs) - FIXED REGEX
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
        
        # FIX: Regex עמיד יותר שלא מסתמך על רווחים בלבד, אלא תופס הכל עד ה-add
        # מחפש את טעינת המספר 300 (0x12c), ותופס כל קוד שבא אחריו עד להוספה לרשימה
        updates_regex = r"(const/16 [vp]\d+, 0x12c.*?)(invoke-virtual \{[vp]\d+, [vp]\d+\}, Ljava/util/AbstractCollection;->add\(Ljava/lang/Object;\)Z)"
        
        if re.search(updates_regex, content, re.DOTALL):
            # הופך את שורת ההוספה (add) להערה (#) ובכך מנטרל את הוספת הטאב
            content = re.sub(updates_regex, r"\1# \2", content, count=1, flags=re.DOTALL)
            print("    [+] Home Tabs: 'Updates' tab REMOVED from list.")
            with open(target_file, 'w', encoding='utf-8') as f: f.write(content)
            return True
        else:
            print("    [-] Home Tabs: Exact removal pattern not found.")
            # Debug output for analysis
            if "0x12c" in content and "AbstractCollection;->add" in content:
                 print("        [i] Debug: Found components but regex failed. Check manually.")
            return False

    except Exception as e:
        print(f"    [-] Error: {e}")
        return False

# ---------------------------------------------------------
# 4. תיקון SecurePendingIntent (אופציונלי)
# ---------------------------------------------------------
def _patch_secure_pending_intent(root_dir):
    anchor = "Please set reporter for SecurePendingIntent library"
    print(f"\n[4] Scanning for SecurePendingIntent ({anchor})...")
    
    target_file = _find_file_by_string(root_dir, anchor)
    if not target_file:
        print("    [i] File not found (optional, skipping).")
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
