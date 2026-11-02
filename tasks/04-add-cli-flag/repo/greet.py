import argparse


def main(argv=None):
    p = argparse.ArgumentParser(description="Print a greeting.")
    p.add_argument("name")
    p.add_argument("--times", type=int, default=1, help="repeat the greeting")
    args = p.parse_args(argv)
    for _ in range(args.times):
        print(f"Hello, {args.name}!")


if __name__ == "__main__":
    main()
