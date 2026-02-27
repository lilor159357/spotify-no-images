import os
import re

def patch(decompiled_dir: str) -> bool:
    print(f"[*] Starting WhatsApp Kosher patch (Precision Sniper Mode v16 - METHOD ISOLATION)...")
    
    # ביצוע הפאצ'ים
    photos = _patch_profile_photos(decompiled_dir)
    newsletter = _patch_newsletter_launcher(decompiled_dir)
    tabs = _patch_home_tabs(decompiled_dir)
    spi = _patch_secure_pending_intent(decompiled_dir)


    results = [photos, newsletter, tabs, spi]
    
    if all(results):
        print("\n[SUCCESS] All patches and clone were applied successfully!")
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
# 3. הסרת טאב העדכונים (Home Tabs) - METHOD ISOLATION
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
        
        # מחלקים את הקובץ לבלוקים של מתודות, כדי למנוע זליגה של ה-Regex ממתודה למתודה
        method_pattern = re.compile(r'(\.method.*?\.end method)', re.DOTALL)
        
        new_content = content
        patch_applied = False
        
        # סורקים כל מתודה בנפרד
        for method_match in method_pattern.finditer(content):
            method_body = method_match.group(1)
            
            # מחפשים את המתודה הספציפית שבתוכה מתבצעת בניית הרשימה
            # היא חייבת להכיל גם 0x12c, גם 0x258, וגם הוספה ל-Collection
            if "0x12c" in method_body and "0x258" in method_body and "AbstractCollection;->add" in method_body:
                
                # עכשיו אנחנו בטוחים ב-100% שאנחנו בתוך מתודה A05
                # נחפש את ה-12c, ואת ה-add הראשון שבא אחריו. 
                updates_regex = r"(const/16\s+[vp]\d+,\s*0x12c.*?)((?:invoke-virtual|invoke-interface)\s*\{[vp]\d+,\s*[vp]\d+\},\s*Ljava/util/AbstractCollection;->add\(Ljava/lang/Object;\)Z)"
                
                if re.search(updates_regex, method_body, re.DOTALL):
                    # מחליפים בהערה
                    new_method_body = re.sub(updates_regex, r"\1# \2", method_body, count=1, flags=re.DOTALL)
                    
                    # מעדכנים את הקובץ המלא עם המתודה הערוכה
                    new_content = new_content.replace(method_body, new_method_body)
                    patch_applied = True
                    print("    [+] Home Tabs: 'Updates' tab (0x12c) REMOVED from the target method.")
                    break # מצאנו וטיפלנו, אפשר לעצור את הלולאה
        
        if patch_applied:
            with open(target_file, 'w', encoding='utf-8') as f: f.write(new_content)
            return True
        else:
            print("    [-] Home Tabs: Target method found, but regex failed to match 0x12c block.")
            return False

    except Exception as e:
        print(f"    [-] Error: {e}")
        return False

# ---------------------------------------------------------
# 4. תיקון SecurePendingIntent (עם Forensic Dump)
# ---------------------------------------------------------
def _patch_secure_pending_intent(root_dir):
    anchor = "Please set reporter for SecurePendingIntent library"
    print(f"\n[4] Scanning for SecurePendingIntent ({anchor})...")
    
    target_file = _find_file_by_string(root_dir, anchor)
    if not target_file:
        print("    [i] File not found (optional, skipping).")
        return True 

    # --- FORENSICS: Create output dir ---
    forensics_dir = os.path.join(root_dir, "forensics_output")
    os.makedirs(forensics_dir, exist_ok=True)
    
    # Save the file name for later dumping
    filename = os.path.basename(target_file)
    dump_path = os.path.join(forensics_dir, f"DEBUG_{filename}")

    try:
        with open(target_file, 'r', encoding='utf-8') as f: content = f.read()
        
        # --- FORENSICS: Dump original file ---
        with open(dump_path, 'w', encoding='utf-8') as f: f.write(content)
        print(f"    [DUMP] Original file dumped to: {dump_path}")

        # התבנית תופסת:
        # 1. if-nez והלייבל
        # 2. שם הלייבל בנפרד
        # 3. כל הקוד שבאמצע (Non-greedy)
        # 4. שורת השגיאה
        pattern = re.compile(r"(if-nez [vp]\d+, (:cond_\w+))([\s\S]+?)(const-string [vp]\d+, \"Please set reporter)", re.DOTALL)

        def replacement_logic(match):
            full_match = match.group(0)
            condition_line = match.group(1) # if-nez v0, :cond_24
            label_target = match.group(2)   # :cond_24
            middle_code = match.group(3)    # הקוד שבאמצע
            error_line = match.group(4)     # const-string...

            # הדפסת דיבאג כדי להבין מה הסקריפט "רואה" באמצע
            print(f"    [?] Examining block around: {condition_line}")
            
            # בדיקה חכמה וספציפית:
            # 1. האם יש return באמצע? (סימן למלכודת לוגית)
            # 2. האם יש הגדרת תווית (:cond_...) בתחילת שורה? (סימן שהקפיצה היא לפה)
            is_trap = "return" in middle_code or "goto" in middle_code or re.search(r'^\s*:[a-zA-Z0-9_]+', middle_code, re.MULTILINE)
            
            if is_trap:
                print(f"    [i] Trap detected! logic found inside block.")
                print(f"        --- TRAP CONTENT START ---")
                print(f"{middle_code}")
                print(f"        --- TRAP CONTENT END ---")
                return match.group(0) # מחזיר את המקור בלי לגעת
            
            # אם הגענו לפה, הדרך נקייה
            print(f"    [+] CLEAN PATH FOUND! Patching: '{condition_line}' -> 'goto {label_target}'")
            return f"goto {label_target}{middle_code}{error_line}"

        # מריצים את ההחלפה
        new_content, num_subs = pattern.subn(replacement_logic, content)
        
        if new_content != content:
            with open(target_file, 'w', encoding='utf-8') as f: f.write(new_content)
            print(f"    [SUCCESS] Fixed {num_subs} checks in SecurePendingIntent.")
            return True
        else:
            print("    [-] Target pattern not found (or logic prevented bad patch). Check logs above.")
            return False

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
