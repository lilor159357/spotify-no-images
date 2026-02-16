import os
import re

def _remove_profile_installer_manifest(decompiled_dir: str) -> bool:
    """
    Removes the ProfileInstallerInitializer meta-data from AndroidManifest.xml.
    
    Why: On Android 9 (API 28), androidx.startup initializes ProfileInstaller, 
    which calls 'Trace.isEnabled()'. This method was added in API 29, causing 
    a java.lang.NoSuchMethodError crash on startup.
    """
    manifest_path = os.path.join(decompiled_dir, "AndroidManifest.xml")
    
    if not os.path.exists(manifest_path):
        print("[-] CRITICAL: AndroidManifest.xml not found.")
        return False

    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Regex to match the specific meta-data tag responsible for the crash
        # Matches: <meta-data ... name="...ProfileInstallerInitializer" ... />
        crash_tag_pattern = re.compile(
            r'<meta-data\s+[^>]*android:name="androidx\.profileinstaller\.ProfileInstallerInitializer"[^>]*/>',
            re.IGNORECASE
        )

        if crash_tag_pattern.search(content):
            print("[i] Found crashing ProfileInstallerInitializer tag in Manifest.")
            # Remove the tag by replacing it with an empty string
            new_content = crash_tag_pattern.sub('', content)
            
            with open(manifest_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("[+] PATCH SUCCESS: Removed ProfileInstallerInitializer (Fixed Android 9 crash).")
            return True
        else:
            print("[?] ProfileInstallerInitializer tag not found. App might already be patched.")
            return True 

    except Exception as e:
        print(f"[-] Error patching Manifest: {str(e)}")
        return False

def _bypass_sideload_check_smali(decompiled_dir: str) -> bool:
    """
    Patches AppInitiationViewModel.smali to bypass the installer verification.
    """
    target_filename = "AppInitiationViewModel.smali"
    file_found = False

    print(f"[*] Searching for {target_filename}...")

    for root, dirs, files in os.walk(decompiled_dir):
        if target_filename in files:
            file_path = os.path.join(root, target_filename)
            file_found = True
            print(f"[+] Found file at: {file_path}")

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Regex: match invoke-static ArraysKt->contains ... if-nez
                pattern = re.compile(
                    r"(invoke-static \{[vp]\d+, [vp]\d+\}, Lkotlin\/collections\/ArraysKt.*?;->contains\(.*?\).*?move-result ([vp]\d+).*?)if-nez \2, (:cond_\w+)",
                    re.DOTALL
                )

                match = pattern.search(content)

                if match:
                    print(f"[i] Logic found! Target label is: {match.group(3)}")
                    # Force jump to success
                    new_content = pattern.sub(r"\1goto \3", content)

                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)

                    print("[+] PATCH SUCCESS: Sideload check bypassed (Method 1).")
                    return True

                else:
                    print("[!] Complex regex failed, trying simple search fallback...")
                    # Fallback heuristic
                    if "Lkotlin/collections/ArraysKt" in content and "contains" in content:
                        fallback_pattern = re.compile(r"(if-nez p1, (:cond_\w+))")
                        if fallback_pattern.search(content):
                            new_content = fallback_pattern.sub(r"goto \2", content, count=1)
                            if new_content != content:
                                with open(file_path, 'w', encoding='utf-8') as f:
                                    f.write(new_content)
                                print("[+] PATCH SUCCESS: Sideload check bypassed (Fallback Method).")
                                return True

                    print("[-] Pattern not found in SMALI.")
                    return False

            except Exception as e:
                print(f"[-] Error reading/writing file: {str(e)}")
                return False

    if not file_found:
        print(f"[-] CRITICAL: {target_filename} not found.")
        return False
    
    return False

def patch(decompiled_dir: str) -> bool:
    """
    Main entry point for the patcher framework.
    """
    print("=== Applying Bit App Patches ===")
    
    # 1. Fix the Android 9 Crash
    manifest_fixed = _remove_profile_installer_manifest(decompiled_dir)
    
    # 2. Bypass Sideload/Installer Check
    sideload_fixed = _bypass_sideload_check_smali(decompiled_dir)

    # Return True only if both critical operations succeed (or didn't fail catastrophically)
    return manifest_fixed and sideload_fixed