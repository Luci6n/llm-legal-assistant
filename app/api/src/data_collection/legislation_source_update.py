import os
import json

# URLs
SUBSIDIARY_LEGISLATION_URL = "https://lom.agc.gov.my/subsid.php?type=pua"
PRINCIPAL_UPDATED_ACT_URL = "https://lom.agc.gov.my/principal.php?type=updated"
PRINCIPAL_REVISED_ACT_URL = "https://lom.agc.gov.my/principal.php?type=revised"
AMENDMENT_ACT_URL = "https://lom.agc.gov.my/principal.php?type=amendment"

# Map each directory keyword → URL
url_map = {
    "subsidiary_legislation": SUBSIDIARY_LEGISLATION_URL,
    "principal": [PRINCIPAL_UPDATED_ACT_URL, PRINCIPAL_REVISED_ACT_URL],  # could store as list
    "amendment": AMENDMENT_ACT_URL,
}

BASE_DIR = "../../../../data/raw/legislation"

# Folder → URL
targets = [
    (os.path.join(BASE_DIR, "act", "amendment", "metadata"), AMENDMENT_ACT_URL),
    (os.path.join(BASE_DIR, "act", "principal", "updated", "metadata"), PRINCIPAL_UPDATED_ACT_URL),
    (os.path.join(BASE_DIR, "act", "principal", "revised", "metadata"), PRINCIPAL_REVISED_ACT_URL),
    (os.path.join(BASE_DIR, "subsidiary_legislation", "metadata"), SUBSIDIARY_LEGISLATION_URL),
    # Optionally add ordinance/federal_constitution when URLs available
]

def update_metadata_json(metadata_dir, url):
    if not os.path.exists(metadata_dir):
        print(f"⚠️ Skipping missing folder: {metadata_dir}")
        return
    
    for file in os.listdir(metadata_dir):
        if not file.endswith(".json"):
            continue
        path = os.path.join(metadata_dir, file)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            data["source_url"] = url   # ✅ unified key

            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            print(f"✅ Updated {file} with source_url")
        except Exception as e:
            print(f"❌ Failed to update {path}: {e}")

# Run for all targets
for metadata_dir, url in targets:
    update_metadata_json(metadata_dir, url)