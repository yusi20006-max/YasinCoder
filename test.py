import subprocess
import sys

tests=[

["info"],

["models"],

["project"],

["brain"],

["search","database"],

["explain","database.py"]

]

ok=0
fail=0

for test in tests:

    print("="*60)

    print("TEST"," ".join(test))

    r=subprocess.run(

        [sys.executable,"main.py"]+test,

        capture_output=True,

        text=True

    )

    print(r.stdout)

    if r.stderr:

        print(r.stderr)

    if r.returncode==0:

        ok+=1

    else:

        fail+=1

print("="*60)
print("PASSED",ok)
print("FAILED",fail)
