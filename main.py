import argparse
import os
import sys
from ast_nodes import Formula
from parser import parse_ast

def parse_input(input_text: str) -> Formula:
    try:
        return parse_ast(input_text)
    except Exception as e:
        print(f"Error parsing input: {e}", file=sys.stderr)
        sys.exit(1)


def file_path(path: str) -> str:
    if os.path.isfile(path):
        return path
    raise argparse.ArgumentTypeError(f"file_path: '{path}' is not a valid file")


def main():
    parser = argparse.ArgumentParser(description="Parse a DSL and generate its AST.")
    parser.add_argument("-f", "--file", type=file_path, help="Path to an input file")
    parser.add_argument("-e", "--expr", type=str, help="Expression to parse if no file is provided")
    args = parser.parse_args()


    if args.file is not None:
        try:
            with open(args.file, "r") as file:
                input_text = file.read()
        except OSError as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)

        if not input_text:
            print("Error: Input file is empty.", file=sys.stderr)
            sys.exit(1)
    elif args.expr is not None:
        input_text = args.expr
    else:
        print("Enter DSL input to parse (Ctrl+D to end input):", file=sys.stderr)
        input_text = sys.stdin.read().strip()

    if not input_text:
        print("Error: No input provided.", file=sys.stderr)
        sys.exit(1)
    

    ast = parse_input(input_text)
    print(ast)

if __name__ == "__main__":
    main()
