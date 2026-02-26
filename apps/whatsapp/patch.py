import os
import sys

# ==============================================================================
# סקריפט איסוף מידע (Forensics) עבור סביבת GITHUB ACTIONS
# ==============================================================================

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
    הפונקציה הראשית. מוצאת את הקבצים ומדפיסה את תוכנם ללוג.
    """
    print(">>> WhatsApp Forensics Script (GitHub Actions Mode) Running <<<", flush=True)
    print("This script will find and print the content of the target files for debugging.\n", flush=True)

    # --- 1. איתור וקריאת קובץ התמונות ---
    photo_anchor = 'contactPhotosBitmapManager/getphotofast/'
    print(f"[1] Searching for Photos file using anchor: '{photo_anchor}'", flush=True)
    
    photo_file_path = find_file_by_string(decompiled_dir, photo_anchor)
    
    if photo_file_path:
        print(f"    [+] Found Photos file: {photo_file_path}", flush=True)
        try:
            with open(photo_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print("\n" + "="*20 + " START OF PHOTO FILE CONTENT " + "="*20, flush=True)
            sys.stdout.flush()
            print(content)
            sys.stdout.flush()
            print("="*20 + "  END OF PHOTO FILE CONTENT  " + "="*20 + "\n", flush=True)
        except Exception as e:
            print(f"    [-] ERROR reading Photos file: {e}", flush=True)
    else:
        print("    [-] Photos file NOT FOUND.", flush=True)

    # --- 2. איתור וקריאת קובץ הניוזלטר ---
    newsletter_anchor = "NewsletterLinkLauncher/type not handled"
    print(f"[2] Searching for Newsletter file using anchor: '{newsletter_anchor}'", flush=True)

    newsletter_file_path = find_file_by_string(decompiled_dir, newsletter_anchor)

    if newsletter_file_path:
        print(f"    [+] Found Newsletter file: {newsletter_file_path}", flush=True)
        try:
            with open(newsletter_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print("\n" + "="*20 + " START OF NEWSLETTER FILE CONTENT " + "="*20, flush=True)
            sys.stdout.flush()
            print(content)
            sys.stdout.flush()
            print("="*20 + "  END OF NEWSLETTER FILE CONTENT  " + "="*20 + "\n", flush=True)
        except Exception as e:
            print(f"    [-] ERROR reading Newsletter file: {e}", flush=True)
    else:
        print("    [-] Newsletter file NOT FOUND.", flush=True)

    print(">>> Forensics script finished. Please copy the entire log output. <<<", flush=True)


def patch(decompiled_dir: str) -> bool:
    """
    הפונקציה שה-runner הראשי קורא לה.
    היא מפעילה את איסוף המידע ומחזירה True כדי שה-Action ימשיך.
    """
    run_forensics(decompiled_dir)
    print("\n[i] Forensics complete. Continuing build process...", flush=True)
    return True
