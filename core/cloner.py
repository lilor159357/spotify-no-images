import os
import re

def run_clone(decompiled_dir: str, clone_config: dict) -> bool:
    """
    Apply a generic cloning patch to the decompiled APK.
    Mimics MT Manager logic: 
    1. Keeps Class names pointing to original package.
    2. Renames Permissions, Authorities, and Actions to new package.
    3. Handles 3rd party prefixes (google, androidx, etc).
    """
    old_pkg = clone_config.get("old_pkg")
    new_pkg = clone_config.get("new_pkg")
    app_name_suffix = clone_config.get("app_name_suffix", " (Cloned)")

    if not all([old_pkg, new_pkg]):
        print("[-] [Cloner] 'old_pkg' and 'new_pkg' are required.")
        return False
        
    print(f"\n[*] [Cloner] Applying clone: {old_pkg} -> {new_pkg}")
    
    manifest_path = os.path.join(decompiled_dir, "AndroidManifest.xml")
    apktool_yml_path = os.path.join(decompiled_dir, "apktool.yml")
    
    if not os.path.exists(manifest_path):
        print("    [-] [Cloner] AndroidManifest.xml not found.")
        return False

    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # ---------------------------------------------------------
        # שלב 1: החלפת הגדרת החבילה הראשית
        # ---------------------------------------------------------
        content = re.sub(rf'package="{re.escape(old_pkg)}"', f'package="{new_pkg}"', content)

        # ---------------------------------------------------------
        # שלב 2: טיפול ברכיבי קוד (Activities, Services, Providers)
        # המטרה: להשאיר אותם מצביעים על ה-Package המקורי כי הקוד לא זז!
        # ---------------------------------------------------------
        # רשימת התגיות שמכילות הפניות לקוד (Classes)
        component_tags = ["activity", "service", "receiver", "provider", "activity-alias", "application"]
        
        for tag in component_tags:
            # הרג'קס הזה מחפש android:name בתוך התגיות הנ"ל
            # אם הוא מוצא שם יחסי (מתחיל בנקודה), הוא משלים אותו לשם המקורי המלא
            # דוגמה: .Main -> com.whatsapp.Main (ולא kosher!)
            pattern = r'(<' + tag + r'[^>]*?android:name=")(\.[^"]+)(")'
            content = re.sub(pattern, lambda m: m.group(1) + old_pkg + m.group(2) + m.group(3), content)

        # ---------------------------------------------------------
        # פונקציית עזר לתיקון מזהים (Permissions, Authorities)
        # ---------------------------------------------------------
        def fix_identifier(value):
            # אם זהה בדיוק לישן -> החלף לחדש
            if value == old_pkg:
                return new_pkg
            # אם מתחיל בישן (למשל com.whatsapp.permission...) -> החלף קידומת
            if value.startswith(old_pkg + "."):
                return new_pkg + value[len(old_pkg):]
            # אם זה מזהה צד-שלישי (גוגל, פייסבוק וכו') ולא של אנדרואיד -> הוסף קידומת כדי למנוע התנגשות
            if not (value.startswith("android.") or value.startswith("com.android.")):
                 return f'{new_pkg}_{value}'
            # אחרת אל תיגע
            return value

        # ---------------------------------------------------------
        # שלב 3: החלפת Authorities (תמיד מחליפים)
        # ---------------------------------------------------------
        content = re.sub(
            r'android:authorities="([^"]+)"',
            lambda m: f'android:authorities="{fix_identifier(m.group(1))}"',
            content
        )

        # ---------------------------------------------------------
        # שלב 4: החלפת שמות בתגיות מזהות (לא קוד)
        # כאן אנחנו כן רוצים לשנות ל-kosher
        # ---------------------------------------------------------
        identifier_tags = ["permission", "uses-permission", "action", "meta-data", "package", "uses-library"] 
        
        for tag in identifier_tags:
             # מחפש android:name בתוך התגיות הללו בלבד
             pattern = r'(<' + tag + r'[^>]*?android:name=")([^"]+)(")'
             
             def replacer(m):
                 prefix_xml = m.group(1)
                 original_val = m.group(2)
                 suffix_xml = m.group(3)
                 return prefix_xml + fix_identifier(original_val) + suffix_xml
                 
             content = re.sub(pattern, replacer, content)

        # ---------------------------------------------------------
        # שלב 5: תיקון Schemes (עבור Deep Links)
        # ---------------------------------------------------------
        content = re.sub(
            r'(android:scheme=")([^"]+)(")',
            lambda m: m.group(1) + m.group(2).replace(old_pkg, new_pkg) + m.group(3),
            content
        )

        # שמירת הקובץ
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        # ---------------------------------------------------------
        # שלב 6: עדכון apktool.yml (הנחיה ל-Build מחדש)
        # ---------------------------------------------------------
        if os.path.exists(apktool_yml_path):
            with open(apktool_yml_path, 'r', encoding='utf-8') as f:
                yml_content = f.read()
            
            if "renameManifestPackage:" in yml_content:
                yml_content = re.sub(r'renameManifestPackage:.*', f'renameManifestPackage: {new_pkg}', yml_content)
            else:
                # מוסיף את השורה בסוף אם לא קיימת
                yml_content += f'\nrenameManifestPackage: {new_pkg}\n'
                
            with open(apktool_yml_path, 'w', encoding='utf-8') as f:
                f.write(yml_content)

        # ---------------------------------------------------------
        # שלב 7: שינוי שם האפליקציה (Strings)
        # ---------------------------------------------------------
        strings_path = os.path.join(decompiled_dir, "res", "values", "strings.xml")
        if os.path.exists(strings_path):
            with open(strings_path, 'r', encoding='utf-8') as f:
                strings_content = f.read()
            
            # מחליף את שם האפליקציה רק אם הוא מדויק (כדי לא לשבור משפטים אחרים)
            # משתמש ב-Regex עדין יותר
            strings_content = re.sub(r'(<string name="app_name">)(.*?)(</string>)', rf'\1\2{app_name_suffix}\3', strings_content)
            
            with open(strings_path, 'w', encoding='utf-8') as f:
                f.write(strings_content)

        print(f"    [+] [Cloner] Clone applied successfully.")
        return True

    except Exception as e:
        print(f"    [-] [Cloner] Error: {e}")
        return False
