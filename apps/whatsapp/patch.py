import os
import re

def patch(decompiled_dir: str) -> bool:
    print(f"[*] Starting WhatsApp Kosher patch (Precision Sniper Mode v16 - METHOD ISOLATION)...")
    
    # ביצוע הפאצ'ים
    photos = _patch_profile_photos(decompiled_dir)
    newsletter = _patch_newsletter_launcher(decompiled_dir)
    tabs = _patch_home_tabs(decompiled_dir)
    spi = _patch_secure_pending_intent(decompiled_dir)
    
    # +++ כאן קוראים לפונקציית השכפול שהוספנו +++
    clone = _clone_whatsapp(decompiled_dir)

    # +++ חובה להוסיף את clone לרשימת התוצאות כדי שהמערכת תדע אם זה הצליח +++
    results = [photos, newsletter, tabs, spi, clone]
    
    if all(results):
        print("\n[SUCCESS] All patches and clone were applied successfully!")
        return True
    else:
        print("\n[FAILURE] One or more critical patches failed. Check logs.")
        return False
        
def _clone_whatsapp(root_dir):
    print("\n[5] Cloning WhatsApp (Changing Package Name)...")
    manifest_path = os.path.join(root_dir, "AndroidManifest.xml")
    apktool_yml_path = os.path.join(root_dir, "apktool.yml")
    
    if not os.path.exists(manifest_path):
        print("    [-] AndroidManifest.xml not found.")
        return False

    old_pkg = "com.whatsapp"
    new_pkg = "com.whatsapp.kosher" # אתה יכול לשנות לכל שם חבילה שתרצה

    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 1. שינוי שם החבילה הראשי
        content = re.sub(rf'package="{old_pkg}"', f'package="{new_pkg}"', content)

        # 2. תיקון נתיבי מחלקות (Classes) שמתחילים בנקודה
        # מחליף ".MainActivity" ל-"com.whatsapp.MainActivity"
        # זה קריטי כי שינינו את ה-package למעלה, והקוד עצמו עדיין נמצא בנתיב הישן
        content = re.sub(
            r'(<(?:activity|service|receiver|provider|activity-alias)[^>]*?android:name=")(\.[^"]+)(")',
            lambda m: m.group(1) + old_pkg + m.group(2) + m.group(3),
            content
        )

        # 3. תיקון Provider Authorities (קריטי כדי שהאפליקציות לא יתנגשו בהתקנה)
        content = content.replace(f'authorities="{old_pkg}', f'authorities="{new_pkg}')

        # 4. תיקון הרשאות מותאמות אישית של וואטסאפ
        content = content.replace(f'"{old_pkg}.permission.', f'"{new_pkg}.permission.')
        content = content.replace(f'"{old_pkg}.intent.', f'"{new_pkg}.intent.')

        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        # 5. עדכון apktool.yml (למקרה ש-apktool דורס הגדרות)
        if os.path.exists(apktool_yml_path):
            with open(apktool_yml_path, 'r', encoding='utf-8') as f:
                yml_content = f.read()
            yml_content = re.sub(r'renameManifestPackage:.*', f'renameManifestPackage: {new_pkg}', yml_content)
            with open(apktool_yml_path, 'w', encoding='utf-8') as f:
                f.write(yml_content)

        # 6. אופציונלי: שינוי שם האפליקציה שמוצג על המסך (כדי שתבדיל ביניהם)
        strings_path = os.path.join(root_dir, "res", "values", "strings.xml")
        if os.path.exists(strings_path):
            with open(strings_path, 'r', encoding='utf-8') as f:
                strings_content = f.read()
            # משנה את שם האפליקציה ל-WhatsApp 2
            strings_content = re.sub(r'<string name="app_name">WhatsApp</string>', r'<string name="app_name">WhatsApp 2</string>', strings_content)
            with open(strings_path, 'w', encoding='utf-8') as f:
                f.write(strings_content)

        print(f"    [+] Successfully cloned. Package changed to: {new_pkg}")
        return True

    except Exception as e:
        print(f"    [-] Error cloning WhatsApp: {e}")
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
