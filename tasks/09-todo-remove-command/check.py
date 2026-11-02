import os, sys
sys.path.insert(0, os.getcwd())
import subprocess, sys, os, tempfile
f = os.path.join(tempfile.mkdtemp(), "t.json")
def run(*a):
    r = subprocess.run([sys.executable, "todo.py", "--file", f, *a], capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr
assert run("add", "milk")[1] == "added 1\n"
assert run("add", "eggs")[1] == "added 2\n"
assert run("add", "tea")[1] == "added 3\n"
assert run("done", "2")[1] == "done 2\n"
assert run("remove", "2") == (0, "removed 2\n", "")
assert run("list")[1] == "[ ] 1 milk\n[ ] 3 tea\n", run("list")
code, out, err = run("remove", "2")
assert code == 1 and "no such id: 2" in err and out == ""
assert run("remove", "99")[0] == 1
assert run("add", "bread")[1] == "added 4\n"
assert run("remove", "4")[1] == "removed 4\n"
assert run("add", "jam")[1] == "added 5\n"
assert run("done", "1")[1] == "done 1\n"
assert run("list")[1] == "[x] 1 milk\n[ ] 3 tea\n[ ] 5 jam\n"
print("ok")
