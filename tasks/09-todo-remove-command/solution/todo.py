import argparse
import json
import os
import sys


def load(path):
    if not os.path.exists(path):
        return {"next_id": 1, "items": []}
    with open(path) as f:
        return json.load(f)


def save(path, data):
    with open(path, "w") as f:
        json.dump(data, f)


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--file", default=os.environ.get("TODO_FILE", "todo.json"))
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("text")
    sub.add_parser("list")
    d = sub.add_parser("done")
    d.add_argument("id", type=int)
    r = sub.add_parser("remove")
    r.add_argument("id", type=int)
    args = p.parse_args(argv)

    data = load(args.file)
    if args.cmd == "add":
        item = {"id": data["next_id"], "text": args.text, "done": False}
        data["next_id"] += 1
        data["items"].append(item)
        save(args.file, data)
        print(f"added {item['id']}")
    elif args.cmd == "list":
        for it in data["items"]:
            print(f"[{'x' if it['done'] else ' '}] {it['id']} {it['text']}")
    elif args.cmd == "remove":
        for it in data["items"]:
            if it["id"] == args.id:
                data["items"].remove(it)
                save(args.file, data)
                print(f"removed {it['id']}")
                break
        else:
            print(f"no such id: {args.id}", file=sys.stderr)
            sys.exit(1)
    elif args.cmd == "done":
        for it in data["items"]:
            if it["id"] == args.id:
                it["done"] = True
                save(args.file, data)
                print(f"done {it['id']}")
                break
        else:
            print(f"no such id: {args.id}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
