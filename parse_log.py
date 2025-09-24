DEBUG = False

import os
import sys
import argparse
from datetime import datetime

from ast_nodes import (
    Trace,
    ActionType,
    ActionValue,
)

EMPTY_VALUE = "no_value"

class LogParsingError(Exception):
    def __init__(self, line: str, id: str,):
        self.line = line
        self.id = id
        super().__init__()

    def __str__(self):
        return f"Error parsing log line with id '{self.id}':\n> {self.line.strip()}"

    def display(self, line_number: int) -> str:
        return f"Line {line_number}: {self}"

class MissingIntervalError(LogParsingError):
    def __str__(self) -> str:
        return f"End event '{self.id}' does not match any ongoing action.\n> {self.line.strip()}"

class DuplicateEndEventError(LogParsingError):
    def __init__(self, line: str, id: str, action_value: ActionValue):
        super().__init__(line, id)
        self.action_value = action_value

    def __str__(self) -> str:
        return f"End event '{self.id}' matches action that already terminated: '{self.action_value}'\n> {self.line.strip()}"

def parse_log_line(line: str, trace: Trace, ongoing_actions: dict[str, ActionValue], ignore_non_operations: bool) -> None:
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

    date, full_event_action_type, id = components[0:3]
    values = components[3:]

    time = datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f")

    if "Remove" in full_event_action_type:
        #TODO:
        # Convert to store
        # Add bottom value to components if beginning of action
        return

    event_action_type = full_event_action_type.removeprefix("Reply").removeprefix("End")

    if ActionType.has_value(event_action_type.upper()):
        action_type = ActionType(event_action_type.upper())
    else:
        print(f"Unknown event action type: {full_event_action_type}", file=sys.stderr)
        return

    # NOTE: Ignore non operations in log 
    if ignore_non_operations and action_type in (ActionType.IDEAL, ActionType.STABLE, ActionType.READONLY, ActionType.MEMBER, ActionType.RESPONSIBLE):
        return

    # Begin event
    if full_event_action_type == event_action_type:
        action_value = trace.insert_begin_event(action_type, id, values, time)
        ongoing_actions[id] = action_value

    # End event
    elif action_type == ActionType.FAIL or full_event_action_type.startswith("Reply") or "End" in full_event_action_type:
        #if action_type == ActionType.FAIL:
        #    values = []
        #if action_type == ActionType.LOOKUP and len(values) == 1:
        #    values.append(EMPTY_VALUE)
        action_value = ongoing_actions.pop(id, None)
        if action_value is None:
            raise MissingIntervalError(line, id)

        success = trace.insert_end_event(action_value, id, values, time)
        if not success:
            raise DuplicateEndEventError(line, id, action_value)

def parse_log(log: str, max_lines: int | None, ignore_non_operations: bool = False) -> Trace:
    trace = Trace()
    ongoing_actions: dict[str, ActionValue] = {}
    line_number = 1
    for line in log.splitlines():
        if max_lines is not None and line_number > max_lines:
            break
        try:
            parse_log_line(line, trace, ongoing_actions, ignore_non_operations)
        except TraceParsingError as e:
            print(e.display(line_number), file=sys.stderr)
            sys.exit(1)
        line_number += 1
    return trace

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
    parser = argparse.ArgumentParser(description="Parse a log from string or file")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug output")
    parser.add_argument("-l", "--log", type=handle_input, help="Path to log file or log string")
    parser.add_argument("-n", "--num-lines", type=int, default=None, help="Maximum number of lines to process (default: all)")
    parser.add_argument("-i", "--ignore-non-operations", dest="ignore_non_operations", type=bool, default=False, help="Ignore non-operation events (default: False)")
    args = parser.parse_args()

    global DEBUG
    DEBUG = args.debug
    if args.log is not None:
        log = args.log
    # If we do not have a log, read from stdin
    else:
        print("Enter log (Ctrl+D to end input):", file=sys.stderr)
        log = sys.stdin.read().strip()
    if not log:
        print("Error: No input provided.", file=sys.stderr)
        sys.exit(1)
    trace = parse_log(args.log, args.num_lines, args.ignore_non_operations)

    # Print the trace that was parsed from the log
    if DEBUG:
        actions_str = ""
        for (action_type, values) in trace.actions.items():
            actions_str += f"\n{action_type.name.lower()}:"
            for value in values:
                actions_str += f"\n{value}"
        inputs_str = "\n".join([f"{action_type.name.lower()} {[i]}: {', '.join(values)}" for (action_type, i), values in trace.input_values.items()])
        outputs_str = "\n".join([f"{action_type.name.lower()} {[i]}: {', '.join(values)}" for (action_type, i), values in trace.output_values.items()])
        print(f"{'-'*50}\nParsed trace action occurrences: {actions_str}\n{'-'*50}\nParsed trace input values:\n{inputs_str}\n{'-'*50}\nParsed trace output values:\n{outputs_str}")
    events_str = ""
    for (i, event_set) in enumerate(trace.events):
            events_str += f"\n{i}: {{ "
            for event in event_set:
                events_str += f"{event}"
            events_str += " }"
    print(f"{'-'*50}\nParsed trace events:{events_str}\n{'-'*50}")

if __name__ == "__main__":
    main()