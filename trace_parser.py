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



def parse_trace(file_path: str, max_lines : int | None) -> tuple[Trace, dict[str, str], dict[str, IntervalValue]]:
    trace = Trace()
    var_store : dict[str, str] = {}
    interval_store : dict[str, IntervalValue] = {}

    ongoing_actions : dict[str, IntervalValue] = {}

    line_count = 0
    try:
        with open(file_path, "r") as file:
            for line in file:
                if max_lines is not None and line_count >= max_lines:
                    break
                line_count += 1

                line = line.strip()
                if not line or line.startswith("#"):
                    continue



                # WARNING: Incorrectly mapped double commas to empty strings in the list
                # components = [x.strip() for x in line.split(",")]


                # NOTE: Now removes empty strings from the list
                # TODO: double check logs to confirm it is the desired behaviour
                components = [x.strip() for x in line.split(",") if x.strip()]
                # components = list(map(lambda x: x.strip(","), line.strip().split(", ")))


                if len(components) < 3:
                    print(f"Skipping invalid line (less than 3 fields): {line}", file=sys.stderr)
                    continue

                time, event_type, event_id = components[0:3]
                values = components[2:-1]

                if "Remove" in event_type:
                    #TODO:
                    # Convert to store
                    # Add bottom value to components if beginning of action
                    continue


                try:
                    stripped_event_type = event_type.removeprefix("Reply").removeprefix("End")
                    action_type = ActionType[stripped_event_type]
                except KeyError:
                    print(f"Unknown event type: {event_type}", file=sys.stderr)
                    continue


                # HACK:temporary 
                # Ignore until log preprocessing adds ids
                if action_type in (ActionType.Ideal, ActionType.Stable, ActionType.ReadOnly, 
                                  ActionType.Member, ActionType.Responsible):
                    continue


                event = None
                if not (event_type.startswith("Reply") or "End" in event_type):
                    event = BeginEvent(action_type, values, event_id)
                    interval_value = IntervalValue(len(trace))
                    ongoing_actions[event_id] = interval_value

                    #TODO: use event_id instead of len(interval_store)??
                    interval_store[f"interval_{len(interval_store)}"] = interval_value


                if action_type == ActionType.Fail or event_type.startswith("Reply") or "End" in event_type:
                    event = EndEvent(action_type, values, event_id)

                    interval_value = ongoing_actions.pop(event_id, None)

                    assert interval_value is not None, f"Line: {line_count}| End event {event_id} does not match any ongoing action"
                    success =  interval_value.complete_end(len(trace))

                    assert success, f"Line: {line_count}| End event {event_id} matches action that already terminated: {interval_value}"

                # NOTE: Event is never None, assert just for type checking
                assert event is not None

                trace.append(event)

                for value in values:
                    # TODO:
                    # what should be the key?
                    # any key will do?
                    var_store[f"var{len(var_store)}"] = value
                    #var_store[value] = value
                

    except Exception as e:
        print(f"Error parsing trace file: {e}", file=sys.stderr)
        sys.exit(1)

    return trace, var_store, interval_store


# NOTE: Function defined in main.py, redefined to avoid circular import
def file_path(path: str) -> str:
    if os.path.isfile(path):
        return path
    raise argparse.ArgumentTypeError(f"file_path: '{path}' is not a valid file")

def main():
    parser = argparse.ArgumentParser(description="Parse a trace file and generate Trace, var_store, and interval_store.")
    parser.add_argument("-f", "--file", type=file_path, required=True, help="Path to the trace file")
    parser.add_argument("-n", "--num-lines", type=int, default=None, 
                        help="Maximum number of lines to process (default: all)")


    args = parser.parse_args()

    trace, var_store, interval_store = parse_trace(args.file, args.num_lines)

    print("Trace:", trace)
    print("Variable Store:", var_store)
    print("Interval Store:", interval_store)

if __name__ == "__main__":
    main()
