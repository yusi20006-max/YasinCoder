import os
import sys

print("="*60)
print("YasinCoder Doctor")
print("="*60)

print("Python :",sys.version)

folders=[

"commands",

"core",

"providers",

"prompts"

]

for folder in folders:

    if os.path.isdir(folder):

        print("[ OK ]",folder)

    else:

        print("[FAIL]",folder)

files=[

"main.py",

"router.py",

"agent.py",

"project.py",

"config.py",

"ai_client.py"

]

for file in files:

    if os.path.isfile(file):

        print("[ OK ]",file)

    else:

        print("[FAIL]",file)
