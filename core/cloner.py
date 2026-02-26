import os
import re

def run_clone(decompiled_dir: str, clone_config: dict) -> bool:
    """
    Apply a generic cloning patch to the decompiled APK.
    
    Args:
        decompiled_dir: Path to the apktool-decompiled directory.
        clone_config: A dictionary with 'old_pkg', 'new_pkg', 'app_name_suffix'.
    
    Returns:
        True if cloning was successful, False otherwise.
    """
    old_pkg = clone_config.get("old_pkg")
    new_pkg = clone_config.get("new_pkg")
    app_name_suffix = clone_config.get("app_name_suffix", " (Cloned)")

    if not all([old_pkg, new_pkg]):
        print("[-] [Cloner] 'old_pkg' and 'new_pkg' are required in clone_config.")
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

        # 1. שינוי שם החבילה הראשי
        content = re.sub(rf'package="{re.escape(old_pkg)}"', f'package="{new_pkg}"', content)

        # 2. תיקון נתיבי מחלקות (Classes) שמתחילים בנקודה
        content = re.sub(
            r'(<(?:activity|service|receiver|provider|activity-alias)[^>]*?android:name=")(\.[^"]+)(")',
            lambda m: m.group(1) + old_pkg + m.group(2) + m.group(3),
            content
        )

        # 3. תיקון הרשאות ו-Authorities
        def prefix_replacer(match):
            attr_name = match.group(1)
            original_value = match.group(2)
            
            if original_value == old_pkg:
                return f'{attr_name}="{new_pkg}"'
            if original_value.startswith(old_pkg + "."):
                return f'{attr_name}="{new_pkg}{original_value[len(old_pkg):]}"'
            if not (original_value.startswith("android.") or original_value.startswith("com.android.")):
                 return f'{attr_name}="{new_pkg}_{original_value}"'
            return match.group(0)

        content = re.sub(r'(android:name|android:authorities)="(?!' + re.escape(old_pkg) + r'://)([^"]+)"', prefix_replacer, content)
        content = re.sub(r'(android:name)="(com\.whatsapp\.[^"]+)"', lambda m: f'{m.group(1)}="{m.group(2).replace(old_pkg, new_pkg)}"', content)

        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        # 4. עדכון apktool.yml
        if os.path.exists(apktool_yml_path):
            with open(apktool_yml_path, 'r', encoding='utf-8') as f:
                yml_content = f.read()
            # ודא שיש שורה כזו לפני שמנסים להחליף
            if "renameManifestPackage:" in yml_content:
                yml_content = re.sub(r'renameManifestPackage:.*', f'renameManifestPackage: {new_pkg}', yml_content)
            else:
                yml_content += f'\nrenameManifestPackage: {new_pkg}\n'
            with open(apktool_yml_path, 'w', encoding='utf-8') as f:
                f.write(yml_content)

        # 5. שינוי שם האפליקציה (אם קיים)
        strings_path = os.path.join(decompiled_dir, "res", "values", "strings.xml")
        if os.path.exists(strings_path):
            with open(strings_path, 'r', encoding='utf-8') as f:
                strings_content = f.read()
            # מחפש את app_name ומוסיף לו את הסיומת
            strings_content = re.sub(r'(<string name="app_name">)(.*?)(</string>)', rf'\1\2{app_name_suffix}\3', strings_content)
            with open(strings_path, 'w', encoding='utf-8') as f:
                f.write(strings_content)

        print(f"    [+] [Cloner] Successfully applied clone.")
        return True

    except Exception as e:
        print(f"    [-] [Cloner] Error during cloning: {e}")
        return False
