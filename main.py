DEBUG = False

import os
import sys
import argparse

from ast_nodes import Formula
from parse_formula import parse_formula
from parse_log import parse_log

def handle_input(value: str) -> str:
    # If the value is a file path, return its content
    if os.path.isfile(value):
        try:
            with open(value, "r") as file:
                content = file.read()
        except OSError as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)
        if not content:
            print("Error: Input file is empty.", file=sys.stderr)
            sys.exit(1)
        return content
    # If the value is a string, return it directly
    return value

def main():
    parser = argparse.ArgumentParser(description="Provide a formula and a log to evaluate the formula on the log")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("-f", "--formula", type=handle_input, help="Path to formula file or formula string")
    parser.add_argument("-l", "--log", type=handle_input, help="Path to log file or log string")
    parser.add_argument("-n", "--num-lines", type=int, default=None, help="Maximum number of lines to process (default: all)")
    args = parser.parse_args()

    global DEBUG
    DEBUG = args.debug
    if args.formula is not None:
        formula = args.formula
    else:
    # If we do not have a formula, read from stdin
        print("Enter formula (Ctrl+D to end input):", file=sys.stderr)
        formula = sys.stdin.read().strip()
    if not formula:
        print("Error: No input provided.", file=sys.stderr)
        sys.exit(1)
    ast = parse_formula(formula)
    if args.log is not None:
        log = args.log
    # If we do not have a log, read from stdin
    else:
        print("Enter log (Ctrl+D to end input):", file=sys.stderr)
        log = sys.stdin.read().strip()
    if not log:
        print("Error: No input provided.", file=sys.stderr)
        sys.exit(1)
    trace = parse_log(args.log, args.num_lines)

    # Print the AST and the trace that were parsed from the formula and the log respectively
    if DEBUG:
        events_str = ""
        for (i, event_set) in enumerate(trace.events):
            events_str += f"\n{i}: {{ "
            for event in event_set:
                events_str += f"{event}"
            events_str += " }"
        print(f"{'-'*50}\nParsed formula:\n{ast}\n{'-'*50}\nParsed trace events:{events_str}")
    # Evaluate the formula on the trace
    store = {}
    interval_store = {}
    result = ast.evaluate(trace, store, interval_store)
    result_str = "The formula does not hold on the log"
    if result:
        result_str = "the formula holds on the trace"
    print(f"{'-'*50}\nEvaluation:\n{result} - {result_str}\n{'-'*50}")

if __name__ == "__main__":
    main()
