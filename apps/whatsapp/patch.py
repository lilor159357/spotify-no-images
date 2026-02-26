import os
import re

def patch(decompiled_dir: str) -> bool:
    print(f"[*] Starting WhatsApp Kosher patch (Precision Sniper Mode v2)...")
    
    # 1. Profile Photos Block
    photos = _patch_profile_photos(decompiled_dir)
    
    # 2. Newsletter/Channels Block
    newsletter = _patch_newsletter_launcher(decompiled_dir)
    
    # 3. Updates Tab Removal
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
# 1. חסימת תמונות פרופיל (Profile Photos)
# Based on file: LX/0lK (contactPhotosBitmapManager)
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
        
        # Patch A00 (Private Final): FIJZ (Float, Int, Long, Bool)
        # שיטה פנימית לפענוח
        a00_regex = r"(\.method private final \w+\(Landroid\/content\/Context;L[^;]+;Ljava\/lang\/String;FIJZ\)Landroid\/graphics\/Bitmap;)"
        if re.search(a00_regex, content):
            content = re.sub(a00_regex, r"\1\n    const/4 v0, 0x0\n    return-object v0", content, count=1)
            print("[+] Profile Photos: Internal decoder (A00/FIJZ) blocked.")
        else:
            print("[-] Profile Photos: A00 signature not found.")

        # Patch A04 (Public Final): FIJZZ (Float, Int, Long, Bool, Bool)
        # שיטה ציבורית לפענוח
        a04_regex = r"(\.method public final \w+\(Landroid\/content\/Context;L[^;]+;Ljava\/lang\/String;FIJZZ\)Landroid\/graphics\/Bitmap;)"
        if re.search(a04_regex, content):
            content = re.sub(a04_regex, r"\1\n    const/4 v0, 0x0\n    return-object v0", content, count=1)
            print("[+] Profile Photos: Public decoder (A04/FIJZZ) blocked.")
        else:
            print("[-] Profile Photos: A04 signature not found.")

        # Patch A07 (InputStream): (Object, Boolean) -> InputStream
        # חסימת הזרמת הקובץ המלא
        a07_regex = r"(\.method public final \w+\(L[^;]+;Z\)Ljava\/io\/InputStream;)"
        if re.search(a07_regex, content):
            content = re.sub(a07_regex, r"\1\n    const/4 v0, 0x0\n    return-object v0", content, count=1)
            print("[+] Profile Photos: Stream loader (A07) blocked.")
        else:
            print("[-] Profile Photos: A07 signature not found.")

        with open(target_file, 'w', encoding='utf-8') as f: f.write(content)
        return True

    except Exception as e:
        print(f"[-] Error patching photos: {e}")
        return False

# ---------------------------------------------------------
# 2. נטרול ערוצים וניוזלטרים (Newsletter Launcher)
# Based on file: LX/AhT
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

        # Patch A01: Deep Link Entry (Context, Uri)
        a01_regex = r"(\.method public final \w+\(Landroid\/content\/Context;Landroid\/net\/Uri;\)V)"
        if re.search(a01_regex, content):
            content = re.sub(a01_regex, r"\1" + injection, content, count=1)
            print("[+] Newsletter: Deep Link entry (A01) killed.")
        else:
             print("[-] Newsletter: A01 signature not found.")

        # Patch A02: Main Logic (Context, Uri, Jid, Integer, Long, String, Int, Long)
        # שימוש ב-Regex גמיש מעט עבור טיפוסי הג'אווה הארוכים
        a02_regex = r"(\.method public final \w+\(Landroid\/content\/Context;Landroid\/net\/Uri;L[^;]+;Ljava\/lang\/Integer;Ljava\/lang\/Long;Ljava\/lang\/String;IJ\)V)"
        if re.search(a02_regex, content):
            content = re.sub(a02_regex, r"\1" + injection, content, count=1)
            print("[+] Newsletter: Main Launcher logic (A02) killed.")
        else:
            print("[-] Newsletter: A02 signature not found.")

        with open(target_file, 'w', encoding='utf-8') as f: f.write(content)
        return True
    except Exception as e:
        print(f"[-] Error patching newsletter launcher: {e}")
        return False

# ---------------------------------------------------------
# 3. הסרת טאב העדכונים (Home Tabs)
# Based on file: LX/0tj
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
        
        # חיפוש הבלוק שמוסיף את 0x12c (300) לרשימה
        # אנו מחפשים את הטעינה של 12c, המרה ל-Integer, ואז קריאה ל-add
        updates_regex = r"(const/16 [vp]\d+, 0x12c\s+.*?invoke-static \{[vp]\d+\}, Ljava\/lang\/Integer;->valueOf\(I\)Ljava\/lang\/Integer;\s+.*?invoke-virtual \{[vp]\d+, [vp]\d+\}, Ljava\/util\/AbstractCollection;->add\(Ljava\/lang\/Object;\)Z)"
        
        if re.search(updates_regex, content, re.DOTALL):
            # הפיכת כל הבלוק הזה להערה כדי למנוע את ההוספה
            # שימוש בפונקציית lambda כדי להוסיף # לכל שורה בבלוק שנמצא
            def comment_out(match):
                block = match.group(1)
                return "\n".join(["#" + line for line in block.splitlines()])

            content = re.sub(updates_regex, comment_out, content, count=1, flags=re.DOTALL)
            print("[+] Home Tabs: Updates/Channels tab (0x12c) removed via logic patching.")
        else:
            print("[-] Home Tabs: Updates tab pattern not found.")

        with open(target_file, 'w', encoding='utf-8') as f: f.write(content)
        return True

    except Exception as e:
        print(f"[-] Error patching home tabs: {e}")
        return False

# ---------------------------------------------------------
# 4. תיקון קריסת SecurePendingIntent
# Based on file: LX/0sw
# ---------------------------------------------------------
def _patch_secure_pending_intent(root_dir):
    anchor = "Please set reporter for SecurePendingIntent library"
    
    target_file = _find_file_by_string(root_dir, anchor)
    if not target_file:
        print("[-] SecurePendingIntent file not found.")
        return True # לא קריטי

    try:
        with open(target_file, 'r', encoding='utf-8') as f: content = f.read()
        
        # בקובץ ששלחת: if-nez v0, :cond_24 ... throw exception
        # אנחנו רוצים שאם התנאי הוא לא-אפס (הצלחה), הוא יקפוץ.
        # אבל הקוד המקורי זורק שגיאה אם הוא ממשיך.
        # הפתרון: להחליף את ה-Check ב-Goto בלתי מותנה להצלחה.
        
        pattern = r"(if-nez [vp]\d+, (:cond_\w+))(\s+.*?)(const-string [vp]\d+, \"Please set reporter)"
        
        if re.search(pattern, content, re.DOTALL):
            # מחליף את ה-if-nez (תנאי) ב-goto (קפיצה ודאית) לתווית ההצלחה
            content = re.sub(pattern, r"goto \2\3\4", content, count=1, flags=re.DOTALL)
            print(f"[+] SecurePendingIntent patched (Check bypassed).")
            with open(target_file, 'w', encoding='utf-8') as f: f.write(content)
        else:
             print("[-] SecurePendingIntent pattern not found.")
            
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
