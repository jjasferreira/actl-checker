import argparse
import os
import sys
from ast_nodes import Formula
from parser import parse_ast
from trace_parser import parse_trace_file

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
    
    #TODO: change trace to log?
    parser.add_argument("-t", "--trace", type=file_path, help="Path to trace file")
    parser.add_argument("-n", "--num-lines", type=int, default=None, 
                        help="Maximum number of lines to process (default: all)")

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

    if args.trace:
        trace = parse_trace_file(args.trace, args.num_lines)
        var_store = {}
        interval_store = {}
        print(f"\nEvaluating formula on trace '{args.trace}' with {trace.get_length()} events:\n")
        print(ast)
        result = ast.evaluate(trace, var_store, interval_store)
        print(f"\nResult: {result}")
        print(f"\nOccurrences: {trace.occurrence_counter}")
    else:
        print(f"Formula:\n{ast}")
    

if __name__ == "__main__":
    main()
