import subprocess
import json
import time
from pathlib import Path

# path to UAssetGUI executable [v1.0.0.0-alpha.3]
uAssetGUIPath = Path("UAssetGUI/UAssetGUI.exe")
# path to original asset
originalAsset = Path("test_assets/C_PlayerTalentGrowthOriginal.uasset")
# path to asset that was modded manually and confirmed to work
manuallyModdedAsset = Path("test_assets/C_PlayerTalentGrowthModded.uasset")
# path to folder where we gonna put JSONs
jsonFolder = Path("json")
# create it if not exist
jsonFolder.mkdir(parents=True, exist_ok=True)

# target path to json of original uasset
origJson = jsonFolder / "orig.json"
# target path to json of modded uasset
moddedJson = jsonFolder / "mod.json"
# target path to exported uasset
targetAsset = Path("test_assets/C_PlayerTalentGrowthRebuild.uasset")

# serialize uasset to json
subprocess.Popen([uAssetGUIPath, 'tojson', originalAsset, origJson, "VER_UE4_26"])

# load json
with open(origJson,'r') as f:
    data = json.load(f)

# get list of curve values
values = data["Exports"][0]["Data"][0]["Value"][0]["Value"]

# Plan is to set new values for last dot on curve, 
# and change previous point data to what the last point was.
# This will save most of original curve and then extend it with new last dot.

# calculate index of last two items
index_last = len(values) - 1
index_prev_last = index_last - 1

# get last dot data
time_last = values[index_last]["Value"][0]["Time"]
value_last = values[index_last]["Value"][0]["Value"]

# change previous dot data to last dot data
values[index_prev_last]["Value"][0]["Time"] = time_last
values[index_prev_last]["Value"][0]["Value"] = value_last

# change last dot data to extended values
values[index_last]["Value"][0]["Time"] = 1000.0
values[index_last]["Value"][0]["Value"] = 1000.0

# save modded json to file
with open(moddedJson, 'w') as f:
    json.dump(data, f)

# create uasset from modded json
subprocess.Popen([uAssetGUIPath, 'fromjson', moddedJson, targetAsset, "VER_UE4_26"])

# give it a second to catch up before tests
time.sleep(1)

# now let's test it.

import hashlib

# Grabbing hashes
sha1MM = hashlib.sha1()
with open(manuallyModdedAsset, 'rb') as f:
    d = f.read()
    sha1MM.update(d)

sha1O = hashlib.sha1()
with open(originalAsset, 'rb') as f:
    d = f.read()
    sha1O.update(d)

sha1M = hashlib.sha1()
with open(targetAsset, 'rb') as f:
    d = f.read()
    sha1M.update(d)

# Suprisingly in this case, .uasset files should be the same, magic happens in .uexp
assert sha1MM.hexdigest() == sha1O.hexdigest() == sha1M.hexdigest(), "[ERROR], .uasset hashes was not the same"

# Grabbing .uexp hashes
sha1MM = hashlib.sha1()
with open(Path("test_assets/C_PlayerTalentGrowthModded.uexp"), 'rb') as f:
    d = f.read()
    sha1MM.update(d)

sha1O = hashlib.sha1()
with open(Path("test_assets/C_PlayerTalentGrowthOriginal.uexp"), 'rb') as f:
    d = f.read()
    sha1O.update(d)

sha1M = hashlib.sha1()
with open(Path("test_assets/C_PlayerTalentGrowthRebuild.uexp"), 'rb') as f:
    d = f.read()
    sha1M.update(d)

# Moment of truth, check if rebuild asset is EXACTLY the same as manually modded valid asset
assert sha1MM.hexdigest() == sha1M.hexdigest(), "[ERROR], .uexp hashes of modded files was different"

# Just to double check that we actually changed something
assert sha1O.hexdigest() != sha1M.hexdigest(), "[ERROR], .uexp hash of modded asset is the same as original"