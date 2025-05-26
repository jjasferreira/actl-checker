import os
import sys
import argparse
from datetime import datetime

from ast_nodes import (
    Trace,
    BeginEvent,
    EndEvent,
    ActionType,
    IntervalValue,
)

EMPTY_VALUE = "no_value"

class TraceParsingError(Exception):
    def __init__(self,  line : str, event_id: str,):
        self.line = line
        self.event_id = event_id
        super().__init__()


    def __str__(self):
        return f"Error parsing error event '{self.event_id}'\n> {self.line.strip()}"

    def display(self, line_number: int) -> str:
        return f"Line {line_number}: {self}"

class MissingIntervalError(TraceParsingError):
    def __str__(self) -> str:
        return f"End event '{self.event_id}' does not match any ongoing action.\n> {self.line.strip()}"

class DuplicateEndEventError(TraceParsingError):
    def __init__(self, line : str, event_id: str, interval_value: IntervalValue):
        super().__init__(line, event_id)
        self.interval_value = interval_value

    def __str__(self) -> str:
        return f"End event '{self.event_id}' matches action that already terminated: '{self.interval_value}'\n> {self.line.strip()}"


def parse_trace_line(line : str, trace : Trace, ongoing_actions : dict[str, IntervalValue], ignore_non_operations : bool) -> None:
                line = line.strip()

                if not line or line.startswith("#"):
                    return 

                # WARNING: Incorrectly mapped double commas to empty strings in the list
                # components = [x.strip() for x in line.split(",")]

                # NOTE: Now removes empty strings from the list
                # TODO: double check logs to confirm it is the desired behaviour
                components = [x.strip() for x in line.split(",") if x.strip()]
                # components = list(map(lambda x: x.strip(","), line.strip().split(", ")))


                if len(components) < 3:
                    print(f"Skipping invalid line (less than 3 fields): {line}", file=sys.stderr)
                    return

                time, event_type, event_id = components[0:3]
                values = components[3:]

                date =  datetime.strptime(time, "%Y-%m-%d %H:%M:%S.%f")

                if "Remove" in event_type:
                    #TODO:
                    # Convert to store
                    # Add bottom value to components if beginning of action
                    return


                stripped_event_type = event_type.removeprefix("Reply").removeprefix("End")

                if ActionType.has_value(stripped_event_type):
                    action_type = ActionType(stripped_event_type.upper())
                else:
                    print(f"Unknown event type: {event_type}", file=sys.stderr)
                    return


                # NOTE: Ignore non operations in log 
                if ignore_non_operations and action_type in (ActionType.IDEAL, ActionType.STABLE, ActionType.READONLY, 
                                  ActionType.MEMBER, ActionType.RESPONSIBLE):
                    return

                if not (event_type.startswith("Reply") or "End" in event_type):
                    event = BeginEvent(action_type, values, event_id, date)
                    
                    #NOTE: temporary value that will be overwritten
                    temporary_begin_position = 0 

                    interval_value = IntervalValue(temporary_begin_position)
                    ongoing_actions[event_id] = interval_value

                    trace.insert_interval(action_type, interval_value)

                    for (i, value) in enumerate(values):
                        trace.insert_input(action_type, i, value)

                    position = trace.insert_event(event)

                    #NOTE: overwrites temporary value with correct positon
                    interval_value.set_begin(position)


                if action_type == ActionType.FAIL or event_type.startswith("Reply") or "End" in event_type:
                    if action_type == ActionType.FAIL:
                        values = []

                    if action_type == ActionType.LOOKUP and len(values) == 1:
                        values.append(EMPTY_VALUE)

                    event = EndEvent(action_type, values, event_id, date)

                    interval_value = ongoing_actions.pop(event_id, None)

                    if interval_value is None:
                        raise MissingIntervalError(line, event_id)

                    for (i, value) in enumerate(values):
                        trace.insert_output(action_type, i, value)

                    position = trace.insert_event(event)

                    success =  interval_value.complete_end(position)

                    if not success:
                        raise DuplicateEndEventError(line, event_id, interval_value)


def parse_trace_string(log : str, ignore_non_operations : bool = False) -> Trace:

    trace = Trace()

    ongoing_actions : dict[str, IntervalValue] = {}

    line_number = 1

    for line in log.splitlines():

        try:
            parse_trace_line(line, trace, ongoing_actions, ignore_non_operations)
        except TraceParsingError as e:
            print(e.display(line_number), file=sys.stderr)
            sys.exit(1)

        line_number += 1

    return trace


def parse_trace_file(file_path: str, max_lines : int | None, ignore_non_operations : bool = False) -> Trace:

    trace = Trace()

    ongoing_actions : dict[str, IntervalValue] = {}

    line_number = 1
    try:
        with open(file_path, "r") as file:
            for line in file:
                
                if max_lines is not None and line_number > max_lines:
                    break

                try:
                    parse_trace_line(line, trace, ongoing_actions, ignore_non_operations)
                except TraceParsingError as e:
                    print(e.display(line_number), file=sys.stderr)
                    sys.exit(1)

                line_number += 1

    except Exception as e:
        print(f"Error parsing trace file: {e}", file=sys.stderr)
        sys.exit(1)

    return trace


# NOTE: Function defined in main.py, redefined to avoid circular import
def validate_file_path(path: str) -> str:
    if os.path.isfile(path):
        return path
    raise argparse.ArgumentTypeError(f"file_path: '{path}' is not a valid file")

def main():
    parser = argparse.ArgumentParser(description="Parse a trace file and generate Trace, var_store, and interval_store.")
    parser.add_argument("-f", "--file", type=validate_file_path, required=True, help="Path to the trace file")
    parser.add_argument("-n", "--num-lines", type=int, default=None, 
                        help="Maximum number of lines to process (default: all)")

    parser.add_argument("--ignore", dest="ignore_non_operations", type=bool, default=False, 
                        help="Maximum number of lines to process (default: all)")

    args = parser.parse_args()

    trace = parse_trace_file(args.file, args.num_lines, args.ignore_non_operations)

    print("Trace:", trace)

if __name__ == "__main__":
    main()
