import os
import re

def patch(decompiled_dir: str) -> bool:
    print(f"[*] Starting WhatsApp Kosher patch (Precision Sniper Mode v8 - ROBUST)...")
    
    photos = _patch_profile_photos(decompiled_dir)
    newsletter = _patch_newsletter_launcher(decompiled_dir)
    tabs = _patch_home_tabs(decompiled_dir)
    spi = _patch_secure_pending_intent(decompiled_dir)

    results = [photos, newsletter, tabs, spi]
    
    if all(results):
        print("\n[SUCCESS] All patches applied successfully!")
        return True
    elif any(results):
        print("\n[!] PARTIAL SUCCESS: Some patches failed. See detailed logs above.")
        return True 
    else:
        print("\n[FAILURE] All patches failed.")
        return False

# ---------------------------------------------------------
# 1. חסימת תמונות פרופיל (Profile Photos) - Robust Regex
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
        
        # Regex V8: מתמקד רק בטיפוסים החשובים, ומתעלם מהשאר.
        # קבוצה 1: כל החתימה עד לרגיסטרים
        # קבוצה 2: שורת הרגיסטרים
        bitmap_regex = r"(\.method public[\s\S]*?\(Landroid\/content\/Context;[\s\S]*?\)Landroid\/graphics\/Bitmap;)([\s\S]*?\.registers \d+)"
        
        matches = list(re.finditer(bitmap_regex, content))
        print(f"    [*] Found {len(matches)} potential public Bitmap loaders via robust scan.")
        
        patched_count = 0
        new_content = content

        for match in matches:
            full_match = match.group(0)
            method_sig = match.group(1)
            
            clean_name = re.search(r'\s(\S+)\(', method_sig).group(1) if re.search(r'\s(\S+)\(', method_sig) else "UNKNOWN"
            
            if 'F' in method_sig and 'J' in method_sig:
                print(f"    [+] BLOCKING TARGET: '{clean_name}' (Matches Heuristics F+J)")
                replacement = f"{full_match}\n    const/4 v0, 0x0\n    return-object v0"
                new_content = new_content.replace(full_match, replacement)
                patched_count += 1
            else:
                print(f"    [.] Ignoring: '{clean_name}' (Does not match heuristics)")

        if patched_count == 0 and len(matches) > 0:
            print(f"    [!] Warning: Found {len(matches)} targets but none matched heuristics. No patch applied.")
        elif len(matches) == 0:
            print("    [-] No public methods returning Bitmap and taking Context were found.")


        # Stream Loader (A07)
        stream_regex = r"(\.method.*? \w+\(L[^;]+;Z\)Ljava\/io\/InputStream;)([\s\S]*?\.registers \d+)"
        if re.search(stream_regex, new_content):
            new_content = re.sub(stream_regex, r"\1\2\n    const/4 v0, 0x0\n    return-object v0", new_content)
            print("    [+] Stream loader (A07) blocked.")
        else:
            print("    [-] Stream loader signature not found.")
        
        with open(target_file, 'w', encoding='utf-8') as f: f.write(new_content)
        return True

    except Exception as e:
        print(f"    [-] Error: {e}")
        return False

# ---------------------------------------------------------
# 2. נטרול ניוזלטר (Newsletter) - Robust Regex
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
        
        # Regex V8: מחפש כל מתודה שמקבלת (בסדר הזה) Context ו-Uri, ומחזירה void
        launcher_regex = r"(\.method[\s\S]*?\(Landroid\/content\/Context;Landroid\/net\/Uri;[\s\S]*?\)V)([\s\S]*?\.registers \d+)"
        
        matches = list(re.finditer(launcher_regex, content))
        print(f"    [*] Found {len(matches)} launcher entry points via robust scan.")
        
        if matches:
            for match in matches:
                clean_name = re.search(r'\s(\S+)\(', match.group(1)).group(1)
                print(f"    [+] BLOCKING: '{clean_name}'")

            content, count = re.subn(launcher_regex, r"\1\2" + injection, content)
            print(f"    [+] Applied patches: {count}")
        else:
            print("    [-] No matching methods found.")

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
        
        updates_regex = r"(const/16 [vp]\d+, )0x12c(\s+.*?Ljava/util/AbstractCollection;->add)"
        
        if re.search(updates_regex, content, re.DOTALL):
            content = re.sub(updates_regex, r"\g<1>0x0\2", content, count=1, flags=re.DOTALL)
            print("    [+] Home Tabs: Found 0x12c (Updates) -> Swapped to 0x0.")
        else:
            print("    [-] Pattern not found.")

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
