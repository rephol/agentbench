import os, sys
sys.path.insert(0, os.getcwd())
import subprocess, sys
def run(*a):
    r = subprocess.run([sys.executable, "greet.py", *a], capture_output=True, text=True)
    return r.returncode, r.stdout
assert run("bob") == (0, "Hello, bob!\n")
assert run("bob", "--times", "2") == (0, "Hello, bob!\nHello, bob!\n")
assert run("bob", "--shout") == (0, "HELLO, BOB!\n")
assert run("--shout", "al", "--times", "2") == (0, "HELLO, AL!\nHELLO, AL!\n")
code, out = run("--help")
assert "--shout" in out
print("ok")
