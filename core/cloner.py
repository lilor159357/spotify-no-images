import os
import re

def run_clone(decompiled_dir: str, clone_config: dict) -> bool:
    """
    Apply a perfect MT-Manager style clone.
    - Changes the main package.
    - Resolves relative classes (e.g., .Main -> com.whatsapp.Main).
    - Prefixes permissions and authorities to prevent conflicts.
    - LEAVES 3rd party class names (like com.google.firebase) ALONE.
    """
    old_pkg = clone_config.get("old_pkg")
    new_pkg = clone_config.get("new_pkg")
    app_name_suffix = clone_config.get("app_name_suffix", " (Cloned)")

    if not all([old_pkg, new_pkg]):
        print("[-] [Cloner] 'old_pkg' and 'new_pkg' are required.")
        return False
        
    print(f"\n[*] [Cloner] Applying Smart Manifest Clone: {old_pkg} -> {new_pkg}")
    
    # 1. Update apktool.yml
    apktool_yml_path = os.path.join(decompiled_dir, "apktool.yml")
    if os.path.exists(apktool_yml_path):
        with open(apktool_yml_path, 'r', encoding='utf-8') as f:
            yml_content = f.read()
        if "renameManifestPackage:" in yml_content:
            yml_content = re.sub(r'renameManifestPackage:.*', f'renameManifestPackage: {new_pkg}', yml_content)
        else:
            yml_content += f'\nrenameManifestPackage: {new_pkg}\n'
        with open(apktool_yml_path, 'w', encoding='utf-8') as f:
            f.write(yml_content)

    # 2. Edit AndroidManifest.xml
    manifest_path = os.path.join(decompiled_dir, "AndroidManifest.xml")
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Step A: Change main package definition
        content = re.sub(rf'package="{re.escape(old_pkg)}"', f'package="{new_pkg}"', content)

        # Step B: Normalize relative class names (e.g., .MainActivity -> com.whatsapp.MainActivity)
        # This MUST happen before we touch anything else.
        component_tags = ["activity", "service", "receiver", "provider", "activity-alias", "application"]
        for tag in component_tags:
            pattern = r'(<' + tag + r'[^>]*?android:name=")(\.[^"]+)(")'
            content = re.sub(pattern, lambda m: m.group(1) + old_pkg + m.group(2) + m.group(3), content)
            
            if tag == "activity-alias":
                target_pattern = r'(<' + tag + r'[^>]*?android:targetActivity=")(\.[^"]+)(")'
                content = re.sub(target_pattern, lambda m: m.group(1) + old_pkg + m.group(2) + m.group(3), content)

        # Step C: The MT Manager "Identifier Prefix Engine"
        # ONLY apply prefixes to specific identifiers that cause installation conflicts.
        # NEVER apply prefixes to android:name of activities/services/receivers!
        def fix_identifier(value):
            if value == old_pkg:
                return new_pkg
            if value.startswith(old_pkg + "."):
                return new_pkg + value[len(old_pkg):]
            if not (value.startswith("android.") or value.startswith("com.android.") or value.startswith("androidx.")):
                 return f'{new_pkg}_{value}'
            return value

        # 1. Fix Authorities (Critical for Providers)
        content = re.sub(
            r'android:authorities="([^"]+)"',
            lambda m: f'android:authorities="{fix_identifier(m.group(1))}"',
            content
        )

        # 2. Fix Permissions, Actions, and Categories
        identifier_tags = ["permission", "uses-permission", "action", "category"] 
        for tag in identifier_tags:
             pattern = r'(<' + tag + r'[^>]*?android:name=")([^"]+)(")'
             def replacer(m):
                 # Specifically protect standard android actions/categories from being prefixed
                 val = m.group(2)
                 if val.startswith("android.intent."):
                     return m.group(0)
                 return m.group(1) + fix_identifier(val) + m.group(3)
             content = re.sub(pattern, replacer, content)

        # Step D: Fix explicit Intent Actions inside the app's internal logic
        content = re.sub(r'(android:name)="(com\.whatsapp\.[^"]+)"', lambda m: f'{m.group(1)}="{m.group(2).replace(old_pkg, new_pkg)}"', content)
        
        # Step E: Fix Deep Link Schemes
        content = re.sub(
            r'(android:scheme=")([^"]+)(")',
            lambda m: m.group(1) + m.group(2).replace(old_pkg, new_pkg) + m.group(3),
            content
        )

        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(content)

    # 3. Change App Name in strings.xml
    strings_path = os.path.join(decompiled_dir, "res", "values", "strings.xml")
    if os.path.exists(strings_path):
        try:
            with open(strings_path, 'r', encoding='utf-8') as f:
                strings_content = f.read()
            strings_content = re.sub(r'(<string name="app_name">)(.*?)(</string>)', rf'\1\2{app_name_suffix}\3', strings_content)
            with open(strings_path, 'w', encoding='utf-8') as f:
                f.write(strings_content)
        except Exception:
             pass

    print(f"    [+] [Cloner] Clone applied successfully.")
    return True
