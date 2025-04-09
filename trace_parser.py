import os
import sys
import argparse
from ast_nodes import (
    Trace,
    BeginEvent,
    EndEvent,
    ActionType,
    IntervalValue,
)


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


def parse_trace_line(line : str, trace : Trace, ongoing_actions : dict[str, IntervalValue]) -> None:
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

                if "Remove" in event_type:
                    #TODO:
                    # Convert to store
                    # Add bottom value to components if beginning of action
                    return


                try:
                    stripped_event_type = event_type.removeprefix("Reply").removeprefix("End")
                    action_type = ActionType[stripped_event_type]
                except KeyError:
                    print(f"Unknown event type: {event_type}", file=sys.stderr)
                    return


                # HACK:temporary 
                # Ignore until log preprocessing adds ids
                if action_type in (ActionType.Ideal, ActionType.Stable, ActionType.ReadOnly, 
                                  ActionType.Member, ActionType.Responsible):
                    return


                event = None
                if not (event_type.startswith("Reply") or "End" in event_type):
                    event = BeginEvent(action_type, values, event_id)
                    interval_value = IntervalValue(len(trace))
                    ongoing_actions[event_id] = interval_value

                    trace.insert_interval(action_type, interval_value)

                    for (i, value) in enumerate(values):
                        trace.insert_input(action_type, i, value)


                if action_type == ActionType.Fail or event_type.startswith("Reply") or "End" in event_type:
                    event = EndEvent(action_type, values, event_id)

                    interval_value = ongoing_actions.pop(event_id, None)

                    if interval_value is None:
                        raise MissingIntervalError(line, event_id)

                    success =  interval_value.complete_end(len(trace))

                    if not success:
                        raise DuplicateEndEventError(line, event_id, interval_value)


                    for (i, value) in enumerate(values):
                        trace.insert_output(action_type, i, value)

                # NOTE: Event is never None, assert just for type checking
                assert event is not None

                trace.append_event(event)

def parse_trace_string(log : str) -> Trace:

    trace = Trace()

    ongoing_actions : dict[str, IntervalValue] = {}

    line_number = 0

    for line in log.splitlines():
        line_number += 1

        try:
            parse_trace_line(line, trace, ongoing_actions)
        except TraceParsingError as e:
            print(e.display(line_number), file=sys.stderr)
            sys.exit(1)

    return trace


def parse_trace_file(file_path: str, max_lines : int | None) -> Trace:

    trace = Trace()

    ongoing_actions : dict[str, IntervalValue] = {}

    line_number = 0
    try:
        with open(file_path, "r") as file:
            for line in file:
                
                if max_lines is not None and line_number >= max_lines:
                    break

                line_number += 1

                try:
                    parse_trace_line(line, trace, ongoing_actions)
                except TraceParsingError as e:
                    print(e.display(line_number), file=sys.stderr)
                    sys.exit(1)

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


    args = parser.parse_args()

    trace = parse_trace_file(args.file, args.num_lines)

    print("Trace:", trace)

if __name__ == "__main__":
    main()
