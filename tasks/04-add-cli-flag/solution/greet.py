import argparse


def main(argv=None):
    p = argparse.ArgumentParser(description="Print a greeting.")
    p.add_argument("name")
    p.add_argument("--times", type=int, default=1, help="repeat the greeting")
    p.add_argument("--shout", action="store_true", help="print in upper case")
    args = p.parse_args(argv)
    for _ in range(args.times):
        msg = f"Hello, {args.name}!"
        print(msg.upper() if args.shout else msg)


if __name__ == "__main__":
    main()
