import os
import re

def run_clone(decompiled_dir: str, clone_config: dict) -> bool:
    """
    Apply a perfect MT-Manager style clone.
    Edits ONLY the Manifest, apktool.yml, and strings.xml.
    Does NOT touch Smali files.
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

    # 2. Edit AndroidManifest.xml (The exact MT Manager logic)
    manifest_path = os.path.join(decompiled_dir, "AndroidManifest.xml")
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Step A: Change main package definition
        content = re.sub(rf'package="{re.escape(old_pkg)}"', f'package="{new_pkg}"', content)

        # Step B: Normalize relative class names (e.g., .MainActivity -> com.whatsapp.MainActivity)
        # This protects internal code references from being broken by the new package name.
        component_tags = ["activity", "service", "receiver", "provider", "activity-alias", "application"]
        for tag in component_tags:
            pattern = r'(<' + tag + r'[^>]*?android:name=")(\.[^"]+)(")'
            content = re.sub(pattern, lambda m: m.group(1) + old_pkg + m.group(2) + m.group(3), content)
            
            # Same for targetActivity in activity-alias
            if tag == "activity-alias":
                target_pattern = r'(<' + tag + r'[^>]*?android:targetActivity=")(\.[^"]+)(")'
                content = re.sub(target_pattern, lambda m: m.group(1) + old_pkg + m.group(2) + m.group(3), content)

        # Step C: The MT Manager "Prefix Engine"
        # We need to add the new package prefix to ANY identifier that belongs to a 3rd party (Google/Facebook/etc).
        def prefix_replacer(match):
            attr_name = match.group(1)      # android:name or android:authorities
            original_value = match.group(2) # The value inside the quotes
            
            # If it's exactly the old package, swap it
            if original_value == old_pkg:
                return f'{attr_name}="{new_pkg}"'
                
            # If it starts with the old package (e.g. com.whatsapp.permission.X), swap the prefix
            if original_value.startswith(old_pkg + "."):
                return f'{attr_name}="{new_pkg}{original_value[len(old_pkg):]}"'
                
            # DO NOT PREFIX internal android system identifiers
            if original_value.startswith("android.") or original_value.startswith("com.android.") or original_value.startswith("androidx."):
                # Actually, MT Manager DOES prefix androidx authorities!
                if attr_name == "android:authorities":
                     return f'{attr_name}="{new_pkg}_{original_value}"'
                return match.group(0)

            # --- THE CRITICAL FIX FOR FIREBASE / CRASHES ---
            # If the identifier is a 3rd party library (com.google, com.facebook), 
            # MT Manager prefixes it!
            # Example: com.google.firebase.messaging.FirebaseMessagingService -> com.whatsapp.kosher_com.google.firebase...
            return f'{attr_name}="{new_pkg}_{original_value}"'

        # Apply the prefix replacer to all critical attributes across the entire manifest
        content = re.sub(r'(android:name|android:authorities)="(?!' + re.escape(old_pkg) + r'://)([^"]+)"', prefix_replacer, content)

        # Step D: Fix explicit Intent Actions (Some are hardcoded in smali to look for com.whatsapp)
        # Even though we prefixed 3rd party stuff, we must rename com.whatsapp intent actions to the new package.
        content = re.sub(r'(android:name)="(com\.whatsapp\.[^"]+)"', lambda m: f'{m.group(1)}="{m.group(2).replace(old_pkg, new_pkg)}"', content)
        
        # Save the manifest
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
