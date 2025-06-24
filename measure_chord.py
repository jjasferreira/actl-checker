import argparse
import os
import sys
import time
import csv
import re
from datetime import datetime
from typing import OrderedDict

from chord_preprocessor import dir_path, preprocess_log_from_dir
from trace_parser import parse_trace_file
from parser import parse_ast
from ast_nodes import Formula

def validate_or_create_dir(path: str) -> str:
    if os.path.isdir(path):
        return path
    if not os.path.exists(path):
        os.makedirs(path)
        return path

    raise argparse.ArgumentTypeError(f"'{path}' is not a valid directory")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate properties on multiple Chord log files and store aggregated results in CSV format."
    )

    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")

    parser.add_argument("-d", "--directory", type=dir_path, required=True, help="Path to the directory with directories containing log files")
    parser.add_argument("-p", "--processed", type=validate_or_create_dir, required=True, help="Path to processed logs directory")
    parser.add_argument("-properties", "--properties", type=dir_path, required=True, help="Path to directory with properties to evaluate")
    parser.add_argument("-o", "--output", type=validate_or_create_dir, required=True, help="Path to destination output")

    parser.add_argument("-n", "--max-lines", type=int, default=None, 
                        help="Maximum number of lines to process (default: all)")
    parser.add_argument("-s", "--step", type=int, default=None, 
                        help="Step in increment of lines to process")
    parser.add_argument("-l", "--line", type=int, default=None, nargs="*",
                        help="Line numbers to process")

    parser.add_argument("-r", "--responsibility", action="store_true", help="Include responsibility actions in log")
    
    args = parser.parse_args()

    if not ( args.line or (args.step and args.max_lines)):
        print(f"Error: You must specify either --line, or both --step and --max-lines", file=sys.stderr)
        parser.print_usage()
        sys.exit(1)


    return args


def printv(message : str, verbose : bool):
    if verbose:
        print(message)

def parse_properties(properties_dir: str, verbose : bool = False) -> OrderedDict[str, Formula]:

    formulas = OrderedDict()
    for entry in os.scandir(properties_dir):
        if not entry.is_file():
            printv(f"Skipping property file: {entry.path}", verbose)
            continue

        with open(entry, "r") as file:
            input_text = file.read()


        try:
            formulas[os.path.splitext(os.path.basename(entry.path))[0]] = parse_ast(input_text)
        except Exception as e:
            print(f"Error parsing input: {e}", file=sys.stderr)
            printv(f"Skipping property file: {entry.path}", verbose)

    return formulas



def append_timing_rows(rows : list[dict], filename : str):
    if not rows:
        return

    file_exists = os.path.isfile(filename)
    with open(filename, "a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=rows[0].keys())
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)

def update_symlink(latest_file_path : str, symlink_path : str):
    if os.path.islink(symlink_path) or os.path.exists(symlink_path):
        os.remove(symlink_path)
    os.symlink(latest_file_path, symlink_path)


def create_iterator(args) -> list[int] | range | None:
    if args.line:
        return args.line
    elif args.step and args.max_lines:
        return range(args.step, args.max_lines + 1, args.step)
    return None



def process_log_dir(
    log_dir: os.DirEntry, 
    iterator: list[int] | range, 
    properties: OrderedDict[str, Formula], 
    processed_dir: str,
    include_responsibility: bool,
    property_map: dict[str, list[str]], 
    output_filename: str,
    node_pattern : re.Pattern,
    verbose: bool
):
        if not log_dir.is_dir():
            printv(f"Skipping log file: {log_dir.path}", verbose)
            return

        printv(f"Using log directory: {log_dir.path}", verbose)


        node_result = node_pattern.search(log_dir.name)
        if node_result is None:
            printv(f"Skipping log directory without nodes in name: {log_dir.path}", verbose)
            return

        nodes = node_result.group(1)
        fail = "Faults" in log_dir.name 
        leave = "Leave" in log_dir.name 

        timing_data = []
        prev = 0

        for max_lines in iterator:
            preprocess_destination = f"{os.path.join(processed_dir, os.path.basename(log_dir.path))}-{max_lines}.log"

            printv(f"\nPreprocessing for {max_lines = }, file destination: {preprocess_destination}", verbose)
            
            # TODO: currently never skips preprocessing
            # Check if time gain is useful
            if False and os.path.isfile(preprocess_destination):
                printv(f"Skipping preprocessing, file already exists: {preprocess_destination}", verbose)
                
            else:
                preprocess_log_from_dir(log_dir.path,
                                        preprocess_destination,
                                        max_lines,
                                        include_responsibility,
                                        verbose)

            printv(f"Parsing trace file: {preprocess_destination}", verbose)

            start_time = time.perf_counter()
            # NOTE: Line limit used for preprocessing, not required here
            trace = parse_trace_file(preprocess_destination, None)
            parse_time = time.perf_counter() - start_time

            printv(f"Parse time: {parse_time:.4f} seconds (wall-clock)", verbose)

            if prev is not None and trace.get_length() <= prev: 
                printv(f"Skipping trace with length {trace.get_length()} (previous: {prev})", verbose)
                break


            for (name, formula) in properties.items():
                # If property requires a particular departure operation and the log does not contain it, skip
                if name in property_map and not any([ x in log_dir.name for x in property_map[name]]):
                    printv(f"Skipping property {name} for log {log_dir.name}", verbose)
                    continue


                var_store = {}
                interval_store = {}

                printv(f"\nEvaluating formula \"{name}\" on trace '{log_dir.path}' with {trace.get_length()} events", verbose)


                start_wall = time.perf_counter()

                try:
                    result = formula.evaluate(trace, var_store, interval_store)
                except Exception as e:
                    message =  f"Error evaluating formula {name} on {log_dir.name}: {e}"
                    print(message, file=sys.stderr)
                    printv(message,verbose)

                    #TODO: record failures in csv

                    continue

                end_wall = time.perf_counter()

                eval_time = end_wall - start_wall

                printv(f"Result: {result}", verbose)
                printv(f"Evaluation time: {eval_time:.4f} seconds (wall-clock)", verbose)
                

                timing_data.append({
                    "log_name": os.path.basename(log_dir.path),
                    "property": name,
                    "original_trace_length": max_lines,
                    "processed_trace_length": trace.get_length(),
                    "parse_time": parse_time,
                    "eval_time": eval_time,
                    "total_time": eval_time + parse_time,
                    "result": result,
                    "nodes": nodes,
                    "fail": fail,
                    "leave": leave,
                    "timestamp": datetime.now().isoformat(),
                })

            prev = max_lines
            

            append_timing_rows(timing_data, output_filename)
            timing_data.clear()


def make_output_filename(output_dir: str, max_lines: int | None, step: int | None) -> str:
    max_lines_str = str(max_lines) if max_lines is not None else "all"
    step_str = f"step{step}" if step is not None else "nostep"
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    filename = f"timing_data_{max_lines_str}_{step_str}_{timestamp}.csv"
    return os.path.join(output_dir, filename)

def main():
    args = parse_args()
    verbose = args.verbose

    iterator = create_iterator(args)
    assert isinstance(iterator, range) or isinstance(iterator, list), "Iterator must be a range or list"

    properties = parse_properties(args.properties)

    property_map = {
        "responsability_transfer": ["Leave"],
        "responsability_transfer_v1": ["Leave"],
        "responsability_transfer_v2": ["Leave"],
    }

    output_filename = make_output_filename(args.output, args.max_lines, args.step)

    print(f"Results will be written to: \"{output_filename}\"")

    printv(f"Using directory of logs: {args.directory}", verbose)
    
    node_pattern = re.compile(r"(\d+)nodes")

    for entry in os.scandir(args.directory):
        process_log_dir(entry, 
                        iterator,
                        properties,
                        args.processed,
                        args.responsibility,
                        property_map,
                        output_filename,
                        node_pattern,
                        verbose)


    print("\nMeasurements complete.")
    print(f"Results written to: \"{output_filename}\"")


    latest_path = os.path.join(os.path.dirname(os.path.abspath(output_filename)), "latest.csv")
    update_symlink(os.path.abspath(output_filename), latest_path)
    print(f"\nUpdated symlink to latest results: {latest_path}")
    print(f"Points to: {output_filename}")



if __name__ == "__main__":
    main()
