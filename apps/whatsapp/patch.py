# העתק את כל הקוד הזה לקובץ apps/whatsapp/patch.py

import os
import sys

def find_file_by_string(root_dir, search_string):
    """פונקציית עזר למציאת קובץ לפי מחרוזת."""
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".smali"):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        if search_string in f.read():
                            return path
                except Exception:
                    continue
    return None

def run_forensics(decompiled_dir):
    """
    הפונקציה הראשית. מוצאת את הקבצים, ושומרת את תוכנם לקבצי טקסט
    בתוך תיקייה שתיארז כ-artifact.
    """
    print(">>> WhatsApp Forensics Script (v2 - Artifact Mode) Running <<<", flush=True)
    
    # הגדרת תיקיית הפלט עבור קבצי הטקסט
    FORENSICS_DIR = "forensics_output"
    output_path = os.path.join(decompiled_dir, FORENSICS_DIR)

    try:
        print(f"[*] Creating forensics output directory at: {output_path}", flush=True)
        os.makedirs(output_path, exist_ok=True)
    except Exception as e:
        print(f"[-] FATAL: Could not create forensics directory: {e}", flush=True)
        return

    # --- 1. איתור ושמירת קובץ התמונות ---
    photo_anchor = 'contactPhotosBitmapManager/getphotofast/'
    print(f"[1] Searching for Photos file using anchor: '{photo_anchor}'", flush=True)
    photo_file_path = find_file_by_string(decompiled_dir, photo_anchor)
    
    if photo_file_path:
        print(f"    [+] Found Photos file: {photo_file_path}", flush=True)
        try:
            with open(photo_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            output_file = os.path.join(output_path, "photos_content.txt")
            with open(output_file, 'w', encoding='utf-8') as f_out:
                f_out.write(f"Source File: {photo_file_path}\n\n")
                f_out.write(content)
            
            print(f"    [+] Photos file content saved to '{output_file}'", flush=True)
        except Exception as e:
            print(f"    [-] ERROR processing Photos file: {e}", flush=True)
    else:
        print("    [-] Photos file NOT FOUND.", flush=True)

    # --- 2. איתור ושמירת קובץ הניוזלטר ---
    newsletter_anchor = "NewsletterLinkLauncher/type not handled"
    print(f"[2] Searching for Newsletter file using anchor: '{newsletter_anchor}'", flush=True)
    newsletter_file_path = find_file_by_string(decompiled_dir, newsletter_anchor)

    if newsletter_file_path:
        print(f"    [+] Found Newsletter file: {newsletter_file_path}", flush=True)
        try:
            with open(newsletter_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            output_file = os.path.join(output_path, "newsletter_content.txt")
            with open(output_file, 'w', encoding='utf-8') as f_out:
                f_out.write(f"Source File: {newsletter_file_path}\n\n")
                f_out.write(content)

            print(f"    [+] Newsletter file content saved to '{output_file}'", flush=True)
        except Exception as e:
            print(f"    [-] ERROR processing Newsletter file: {e}", flush=True)
    else:
        print("    [-] Newsletter file NOT FOUND.", flush=True)

    print("\n>>> Forensics files created. Check for the 'forensics-data' artifact in the GitHub Actions summary page after the run completes. <<<", flush=True)

def patch(decompiled_dir: str) -> bool:
    """
    הפונקציה שה-runner הראשי קורא לה.
    """
    run_forensics(decompiled_dir)
    print("\n[i] Forensics complete. The build will now continue as normal.", flush=True)
    return True
