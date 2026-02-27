#!/usr/bin/env python3
import os
import re
import xml.etree.ElementTree as ET

def run_clone(decompiled_dir: str, clone_config: dict) -> bool:
    """
    Apply a perfect MT-Manager style clone.
    - Uses true XML parsing for AndroidManifest.xml (No brittle Regex).
    - Resolves relative classes to absolute before package change.
    - Smartly prefixes Authorities, Permissions, and Actions.
    - Automatically finds and replaces updated identifiers inside Smali files!
    """
    old_pkg = clone_config.get("old_pkg")
    new_pkg = clone_config.get("new_pkg")
    app_name_suffix = clone_config.get("app_name_suffix", " (Cloned)")

    if not all([old_pkg, new_pkg]):
        print("[-] [Cloner] 'old_pkg' and 'new_pkg' are required in clone_config.")
        return False
        
    print(f"\n[*] [Cloner] Starting Smart Clone: {old_pkg} -> {new_pkg}")
    
    # Setup XML namespaces for Android
    # This prevents ElementTree from saving 'ns0:name' instead of 'android:name'
    ET.register_namespace('android', 'http://schemas.android.com/apk/res/android')
    ns_android = 'http://schemas.android.com/apk/res/android'
    attr_name = f'{{{ns_android}}}name'
    attr_auth = f'{{{ns_android}}}authorities'
    attr_target = f'{{{ns_android}}}targetActivity'

    # Dictionary to keep track of strings that MUST be changed in Smali files
    smali_replacements = {}

    def get_cloned_identifier(value: str) -> str:
        """
        Mimics MT Manager's logic for renaming identifiers to avoid conflicts.
        """
        if not value:
            return value
            
        # 1. If it contains the old package name, just replace it
        if old_pkg in value:
            new_val = value.replace(old_pkg, new_pkg)
            smali_replacements[value] = new_val
            return new_val
            
        # 2. Safe prefixes (System/Google/AndroidX) - DO NOT TOUCH
        safe_prefixes = ("android.", "androidx.", "com.android.", "com.google.")
        if value.startswith(safe_prefixes):
            return value
            
        # 3. Third-party conflicts (e.g., com.facebook.permission, com.sec...)
        # Prefix them with new_pkg + "_" to make them unique to this clone
        new_val = f"{new_pkg}_{value}"
        smali_replacements[value] = new_val
        return new_val

    # ==========================================
    # 1. Edit AndroidManifest.xml safely via XML
    # ==========================================
    manifest_path = os.path.join(decompiled_dir, "AndroidManifest.xml")
    if os.path.exists(manifest_path):
        try:
            tree = ET.parse(manifest_path)
            root = tree.getroot()

            # Step A: Resolve relative paths (MUST do before changing the package)
            # e.g., ".MainActivity" -> "com.whatsapp.MainActivity"
            components =['application', 'activity', 'activity-alias', 'service', 'receiver', 'provider']
            for tag in components:
                for elem in root.iter(tag):
                    # Fix android:name
                    name = elem.get(attr_name)
                    if name and name.startswith('.'):
                        elem.set(attr_name, old_pkg + name)
                        
                    # Fix android:targetActivity (for activity-alias)
                    target = elem.get(attr_target)
                    if target and target.startswith('.'):
                        elem.set(attr_target, old_pkg + target)

            # Step B: Change Root Package
            root.set('package', new_pkg)

            # Step C: Update Authorities (Critical for <provider>)
            for provider in root.iter('provider'):
                auths = provider.get(attr_auth)
                if auths:
                    # Providers can have multiple authorities separated by ';'
                    new_auths = ";".join([get_cloned_identifier(a) for a in auths.split(';')])
                    provider.set(attr_auth, new_auths)

            # Step D: Update Permissions, Uses-Permissions, Actions, and Categories
            tags_to_check =['permission', 'uses-permission', 'uses-permission-sdk-23', 'action', 'category']
            for tag in tags_to_check:
                for elem in root.iter(tag):
                    val = elem.get(attr_name)
                    if val:
                        # Protect standard intent actions/categories
                        if val.startswith("android.intent."):
                            continue
                        elem.set(attr_name, get_cloned_identifier(val))

            # Step E: Write back Manifest
            tree.write(manifest_path, encoding='utf-8', xml_declaration=True)
            print("    [+] AndroidManifest.xml parsed and modified successfully.")
            
        except ET.ParseError as e:
            print(f"[-] [Cloner] Failed to parse AndroidManifest.xml: {e}")
            return False
    else:
        print("[-] [Cloner] AndroidManifest.xml not found!")
        return False

    # ==========================================
    # 2. Patch Smali Files (CRITICAL FOR CLONES)
    # ==========================================
    if smali_replacements:
        print(f"    [*] Found {len(smali_replacements)} unique identifiers to patch in Smali code...")
        patched_files = 0
        
        # Walk through all directories starting with 'smali' (smali, smali_classes2, etc.)
        for root_dir, dirs, files in os.walk(decompiled_dir):
            if "smali" not in root_dir.split(os.sep):
                continue
                
            for file in files:
                if file.endswith(".smali"):
                    filepath = os.path.join(root_dir, file)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    original_content = content
                    for old_str, new_str in smali_replacements.items():
                        # We replace exactly inside quotes to avoid partial class name replacements.
                        # e.g., "com.whatsapp.provider.media" -> "com.whatsapp.kosher.provider.media"
                        content = content.replace(f'"{old_str}"', f'"{new_str}"')
                        
                    if content != original_content:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        patched_files += 1
                        
        print(f"    [+] Patched {patched_files} Smali files to prevent Provider/Permission crashes.")

    # ==========================================
    # 3. Update apktool.yml (Manifest Renaming)
    # ==========================================
    apktool_yml_path = os.path.join(decompiled_dir, "apktool.yml")
    if os.path.exists(apktool_yml_path):
        with open(apktool_yml_path, 'r', encoding='utf-8') as f:
            yml_content = f.read()
            
        # Instruct apktool to change the package ID during the build process
        if "renameManifestPackage:" in yml_content:
            yml_content = re.sub(r'renameManifestPackage:.*', f'renameManifestPackage: {new_pkg}', yml_content)
        else:
            yml_content += f'\nrenameManifestPackage: {new_pkg}\n'
            
        with open(apktool_yml_path, 'w', encoding='utf-8') as f:
            f.write(yml_content)
        print("    [+] apktool.yml configured for new package.")

    # ==========================================
    # 4. Change App Name in strings.xml
    # ==========================================
    strings_path = os.path.join(decompiled_dir, "res", "values", "strings.xml")
    if os.path.exists(strings_path):
        try:
            with open(strings_path, 'r', encoding='utf-8') as f:
                strings_content = f.read()
                
            # Regex is perfectly safe here as strings.xml is flat
            new_content = re.sub(
                r'(<string name="app_name">)(.*?)(</string>)', 
                rf'\1\2{app_name_suffix}\3', 
                strings_content
            )
            
            if new_content != strings_content:
                with open(strings_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"    [+] App name updated (added suffix: '{app_name_suffix}').")
        except Exception as e:
             print(f"    [-] Could not update strings.xml: {e}")

    print("    [+] [Cloner] Clone applied successfully!")
    return True
