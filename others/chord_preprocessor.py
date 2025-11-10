import sys
import argparse
import os
from trace_parser import parse_trace_file 
from ast_nodes import Trace, ActionType, Event, BeginEvent, EndEvent
from datetime import datetime, timedelta
from pprint import pprint

from typing import TypeVar
T = TypeVar("T")

def process_readonly(event : Event, store_operations : dict[str, Event], readonly_intervals : list[Event]):
    assert event.action_type == ActionType.STORE, f"Expected STORE, got {event.action_type}"

    if isinstance(event, BeginEvent):
        store_operations[event.get_id()] = event
        if len(store_operations) == 1:
            readonly_intervals.append(EndEvent(ActionType.READONLY, [], f"ReadOnly{len(readonly_intervals) // 2}",
                                       time = event.get_time() - timedelta(milliseconds=1)))
    else:
        assert isinstance(event, EndEvent), f"Expected EndEvent, got {event} of type {type(event)}"
        assert event.get_id() in store_operations, f"Event {event} not found in ongoing store operations:\n[stores ]"

        del store_operations[event.get_id()]
        if len(store_operations) == 0:
            readonly_intervals.append(BeginEvent(ActionType.READONLY, [], f"ReadOnly{len(readonly_intervals) // 2}",
                            time = event.get_time() + timedelta(milliseconds=1)))


# Returns the node that joined or left
def process_membership(event : Event , current_members: dict[str, BeginEvent], membership_intervals : list[Event],
                       membership_operations : dict[str, Event], stable_intervals : list[Event]) -> str | None:

    assert event.action_type in (ActionType.JOIN, ActionType.LEAVE, ActionType.FAIL), f"Expected JOIN, LEAVE or FAIL, got {event.action_type}"


    if isinstance(event, BeginEvent):
        membership_operations[event.get_id()] = event
        if len(membership_operations) == 1:
            stable_intervals.append(EndEvent(ActionType.STABLE, [], f"Stable{len(stable_intervals) // 2}",
                                       time = event.get_time() - timedelta(milliseconds=1)))

    else:
        assert isinstance(event, EndEvent), f"Expected EndEvent, got {event} of type {type(event)}"
        assert event.get_id() in membership_operations, f"Event {event} not found in ongoing store operations:\n[stores ]"

        start_event = membership_operations.pop(event.get_id())
       
        assert len(start_event.values) > 0, f"Membership operation {start_event} has no arguments, expected node as argument"

        node = start_event.values[0]

        if len(membership_operations) == 0:
            stable_intervals.append(BeginEvent(ActionType.STABLE, [], f"Stable{len(stable_intervals) // 2}",
                                       time = event.get_time() + timedelta(milliseconds=1)))

        if event.action_type == ActionType.JOIN:

            assert node not in current_members, f"Node \"{event.values[0]}\" cannot join because it is already member: {event}, {current_members: }"


            begin_event = BeginEvent(ActionType.MEMBER, [node],
                       f"Membership{len(membership_intervals) // 2}-{node}",
                       time = event.get_time() + timedelta(milliseconds=1))

            membership_intervals.append(begin_event)

            current_members[node] = begin_event

            return node

        else:
            assert event.action_type in (ActionType.LEAVE, ActionType.FAIL), f"Expected LEAVE or FAIL, got {event.action_type}"

            assert node in current_members, f"Node \"{event.values[0]}\" cannot leave because it is not a member: {event}, {current_members: }"

            begin_interval = current_members.pop(node)

            membership_intervals.append(EndEvent(ActionType.MEMBER, [],
                                begin_interval.get_id(),
                                time = event.get_time() + timedelta(milliseconds=1)))
            return node

    return None


# Circular Order
def between(a: str, b: str, c: str) -> bool:
    if a == c:
        return True

    if a < c:
        return a < b and b <= c
    else:
        return a < b or b <= c

def is_ideal(pointers: dict[str, str], ordered_members: list[str]) -> bool:

    for (i, node) in enumerate(ordered_members):

        # Node joined but no pointer information yet
        if not node in pointers:
            pointers[node] = node
        
        # Node has correct successor
        correct_successor = pointers[node] == ordered_members[(i + 1) % len(ordered_members)]

        if (not correct_successor):
            return False

    return True

def update_ideal_intervals(time : datetime, successor_pointers: dict[str, str],
                       current_members: dict[str, BeginEvent], ideal_intervals : list[Event]):

    ordered_members = sorted(current_members)

    currently_ideal = is_ideal(successor_pointers, ordered_members)

    if currently_ideal and (len(ideal_intervals) == 0 or type(ideal_intervals[-1]) is EndEvent):
        ideal_intervals.append(BeginEvent(ActionType.IDEAL, [],
                                f"Ideal{len(ideal_intervals) // 2}",
                                time = time))

    elif not currently_ideal and len(ideal_intervals) > 0 and type(ideal_intervals[-1]) is BeginEvent:
        ideal_intervals.append(EndEvent(ActionType.IDEAL, [],
                                f"Ideal{len(ideal_intervals) // 2}",
                                time = time))

def update_responsibility_intervals(time : datetime, successor_pointers: dict[str, str],
                        current_responsibilities : dict[str, set[str]],
                        responsibility_begin_events: dict[tuple[str, str], Event],
                        responsibility_intervals : list[Event], 
                        all_keys : set[str]) -> dict[str, set[str]]:

    new_responsibilities = {}

    # Obtain responsibilities of each node
    for (node, succ) in successor_pointers.items():

        if succ == node:
            new_responsibilities[node] = all_keys
            continue

        new_keys = new_responsibilities.setdefault(succ, set())

        for key in all_keys:
            if between(node, key, succ):
                new_keys.add(key)



    # Check if the responsibilities have changed and update the intervals
    for (node, succ) in successor_pointers.items():

        prev_keys = current_responsibilities.get(succ, set())
        new_keys = new_responsibilities.get(succ) 

        assert new_keys is not None, f"succ {succ} not found in new responsibilities: {new_responsibilities}"

        # Terminate responsibility intervals for removed keys
        for key in prev_keys - new_keys:
            begin_event = responsibility_begin_events.pop((succ, key), None)

            assert begin_event is not None, f"BeginEvent of Responsibility of node: {succ} and key: {key} not found in ongoing responsibilities: {responsibility_begin_events}"


            responsibility_intervals.append(EndEvent(ActionType.RESPONSIBLE, [],
                                    begin_event.get_id(),
                                    time = time))


    # Create responsibility intervals for new keys
    # NOTE: Separate loop to order the end events before the begin events
    for (node, succ) in successor_pointers.items():

        prev_keys = current_responsibilities.get(succ, set())
        new_keys = new_responsibilities.get(succ) 

        assert new_keys is not None, f"succ {succ} not found in new responsibilities: {new_responsibilities}"

        # Create responsibility intervals for new keys
        for key in new_keys - prev_keys:
            begin_event = BeginEvent(ActionType.RESPONSIBLE, [succ, key],
                                    f"Responsible-{len(responsibility_intervals)}-{succ}-{key}",
                                    time = time)

            responsibility_intervals.append(begin_event)
            responsibility_begin_events[(succ, key)] = begin_event


    return new_responsibilities


def process_successors(time : datetime,
                       successor_pointers: dict[str, str],
                       current_members: dict[str, BeginEvent], 
                       ideal_intervals : list[Event],
                       current_responsibilities : dict[str, set[str]],
                       responsibility_begin_events: dict[tuple[str, str], Event],
                       responsibility_intervals : list[Event], 
                       all_keys : set[str],
                       process_responsibility : bool) -> dict[str, set[str]]:

    update_ideal_intervals(time, successor_pointers, current_members, ideal_intervals)

    if process_responsibility:
        new_responsibilities =  update_responsibility_intervals(time, successor_pointers,
                            current_responsibilities,
                            responsibility_begin_events,
                            responsibility_intervals,
                            all_keys)
    else:
        new_responsibilities = current_responsibilities

    return new_responsibilities


def process_intervals(trace : Trace, 
                      successor_changes : list[tuple[datetime, str, str]],
                      keys : set[str],
                      process_responsibility : bool,
                      verbose : bool = False) \
    -> tuple[list[Event], list[Event], list[Event], list[Event], list[Event]]:
    
    if len(trace.events) == 0:
        return [], [], [], [], []

    # Readonly regimen information
    stores = {}
    readonly_intervals = []

    # Membership information
    current_members : dict[str, BeginEvent] = {}
    membership_intervals = []

    membership_operations = {}
    stable_intervals = []

    # Ideal state information
    successor_pointers = {}
    ideal_intervals = []

    # Responsibility information
    current_responsibilities : dict[str, set[str]] = {}
    responsibility_begin_events: dict[tuple[str, str], Event] = {}
    responsibility_intervals : list[Event] = []


    first_event = trace.events[0][0]
    initial_timestamp = first_event.get_time() - timedelta(milliseconds=1)

    # Initial member
    initial_member = first_event.values[0]

    begin_event = BeginEvent(ActionType.MEMBER, [initial_member],
                        f"Membership{len(membership_intervals) // 2}-{initial_member}",
                        time = initial_timestamp)

    membership_intervals.append(begin_event)
    current_members[initial_member] = begin_event

    # Initially in a readonly  regimen
    readonly_intervals.append(BeginEvent(ActionType.READONLY, [], f"ReadOnly{len(readonly_intervals) // 2}",
                        time = initial_timestamp))

    # Initially in a stable  regimen
    stable_intervals.append(BeginEvent(ActionType.STABLE, [], f"Stable{len(stable_intervals) // 2}",
                        time = initial_timestamp))

    # Initial check for ideal state and responsibility
    current_responsibilities = process_successors(initial_timestamp,
                                                  successor_pointers,
                                                  current_members,
                                                  ideal_intervals,
                                                  current_responsibilities,
                                                  responsibility_begin_events,
                                                  responsibility_intervals,
                                                  keys,
                                                  process_responsibility) 

    event_counter = 0
    successor_changes_idx = 0
    for instant in trace.events:

        while successor_changes_idx < len(successor_changes) and \
            instant[0].get_time() > successor_changes[successor_changes_idx][0]:

            time, node, successor = successor_changes[successor_changes_idx]
            successor_pointers[node] = successor

            current_responsibilities = process_successors(time,
                                                          successor_pointers,
                                                          current_members,
                                                          ideal_intervals,
                                                          current_responsibilities,
                                                          responsibility_begin_events,
                                                          responsibility_intervals,
                                                          keys,
                                                          process_responsibility) 
            
            successor_changes_idx += 1

        for event in instant:
            event_counter += 1


            if event.action_type == ActionType.STORE:
                process_readonly(event, stores, readonly_intervals)

            elif event.action_type in (ActionType.JOIN, ActionType.LEAVE, ActionType.FAIL):
                membership_change_node = process_membership(event, 
                                                            current_members, 
                                                            membership_intervals,
                                                            membership_operations,
                                                            stable_intervals)

                # If a node joined or left, update the ideal and responsibility intervals
                if membership_change_node is not None:
                    new_time = event.get_time() + timedelta(milliseconds=1)
                    current_responsibilities = process_successors(new_time,
                                                          successor_pointers,
                                                          current_members,
                                                          ideal_intervals,
                                                          current_responsibilities,
                                                          responsibility_begin_events,
                                                          responsibility_intervals,
                                                          keys,
                                                          process_responsibility) 

    # print("Members")
    # pprint(membership_intervals)
    #
    # print("\n\nReadonly")
    # pprint(readonly_intervals)
    #
    # print("\n\nStable")
    # pprint(stable_intervals)
    #
    #
    # print("\n\nIdeal")
    # pprint(ideal_intervals)
    #
    # print("\n\nResponsibilities")
    # pprint(responsibility_intervals)


    if verbose:
        print()
        print("Members", len(membership_intervals))
        print("Readonly", len(readonly_intervals))
        print("Stable", len(stable_intervals))
        print("Ideal", len(ideal_intervals))
        print("Responsibilities", len(responsibility_intervals))

        print("Processed events: ", event_counter)
        print("Key count: ", len(keys))

    
    return membership_intervals, readonly_intervals, stable_intervals, ideal_intervals, responsibility_intervals



def parse_successors(file_path: str) -> list[tuple[datetime, str, str]]:
    successor_changes = []

    try:
        with open(file_path, "r") as file:
            for line in file:

                components = line.strip().split(', ')

                assert len(components) == 4, f"Invalid line in successors file: {line.strip()}, expected 4 arguments but got {len(components)}"
                
                time, _, member, succ = components
                date =  datetime.strptime(time, "%Y-%m-%d %H:%M:%S.%f")

                successor_changes.append((date, member, succ))


    except Exception as e:
        print(f"Error parsing trace file: {e}", file=sys.stderr)
        sys.exit(1)

    return successor_changes

def get_keys(trace: Trace) -> set[str]:
    keys = set()

    for events in trace.events:
        for event in events:
            if len(event.values) > 0:
                keys.add(event.values[0])

            if event.get_type() is ActionType.STORE and type(event) is BeginEvent:
                keys.add(event.values[1])

            if event.get_type() is ActionType.LOOKUP and type(event) is BeginEvent:
                keys.add(event.values[1])

            if event.get_type() is ActionType.FINDNODE:
                keys.add(event.values[1])

    return keys

def file_path(path: str) -> str:
    if os.path.isfile(path):
        return path
    raise argparse.ArgumentTypeError(f"Aborting: '{path}' is not a valid file")


def dir_path(path: str) -> str:
    if os.path.isdir(path):
        return path
    raise argparse.ArgumentTypeError(f"Aborting: '{path}' is not a valid directory")

def find_log_file(directory : str):
    """Finds the first .log file that does NOT end with 'successor.log'"""
    for file in os.listdir(directory):
        if file.endswith(".log") and not file.endswith("successor.log"):
            return os.path.join(directory, file)
    raise FileNotFoundError("No log file found (expected a .log file not ending in 'successor.log')")

def find_successor_file(directory : str):
    """Finds the first file that ends with 'successor.log'"""
    for file in os.listdir(directory):
        if file.endswith("successor.log"):
            return os.path.join(directory, file)
    raise FileNotFoundError("No successor file found (expected a file ending in 'successor.log')")




def get_log_files(log_path: str | None, 
                  successors_path: str | None, 
                  dir_path: str | None,
                  verbose: bool = False) -> tuple[str, str | None]:

    if dir_path:
        if log_path:
            print("Warning: \"--file\" overrides log file from \"--directory\"")
        else:
            log_path = find_log_file(dir_path)
        if successors_path:
            print("Warning: \"--successors\" overrides successor file from \"--directory\"")
        else:
            successors_path = find_successor_file(dir_path)
    
    if not log_path:
        raise ValueError("The path to the chord log file must be specified if --directory is not used.")

    if verbose:
        print(f"\nUsing log file: {log_path}")
        print(f"Using successors file: {successors_path}\n" if successors_path else "Not using a successors file\n")
    return log_path, successors_path


def load_trace_data(log_path : str, successors_path : str | None, num_lines : int | None) \
        -> tuple[Trace, list[tuple[datetime, str, str]]]:

    trace = parse_trace_file(log_path, num_lines, True)
    successor_changes = parse_successors(successors_path) if successors_path else []
    return trace, successor_changes

def flatten(lst: list[list[T]]) -> list[T]:
    return [item for sublist in lst for item in sublist]

def preprocess_trace(trace : Trace, 
                     successor_changes : list[tuple[datetime, str, str]],
                     process_responsibility : bool,
                     verbose : bool = False):

    trace_events = flatten(trace.events)

    keys = get_keys(trace)
    membership, readonly, stable, ideal, responsibility = process_intervals(trace, successor_changes, keys, process_responsibility, verbose)

    filtered = filter(
        lambda e: not (e.action_type == ActionType.FAIL and isinstance(e, EndEvent)), trace_events
    )
    all_events = list(filtered) + membership + readonly + stable + ideal + responsibility
    all_events.sort(key=lambda x: (x.get_time(), isinstance(x, EndEvent), x.entry_str()))

    return all_events

def write_processed_log(events, output_path, verbose = False):

    with open(output_path, "w") as f:
        for i, event in enumerate(events):
            f.write(event.entry_str() + "\n")
            if verbose and (len(events) // 10 != 0 and (i + 1) % (len(events) // 10) == 0):
                print(f"\tWrote {i + 1}/{len(events)} events...")



def preprocess_log(log_path: str, 
                   output_path: str, 
                   successors_path: str | None = None,
                   num_lines: int | None = None,
                   process_responsibility: bool = False,
                   verbose: bool = True) -> None:

    if verbose:
        print(f"\nUsing log file: {log_path}")
        print(f"Using successors file: {successors_path}\n" if successors_path else "Not using a successors file\n")

    trace, successor_changes = load_trace_data(log_path, successors_path, num_lines)

    if verbose:
        print(f"Preprocessing {trace.get_length()} events")


    complete_events = preprocess_trace(trace, successor_changes, process_responsibility, verbose)

    if verbose:
        print(f"\nPreprocessing generated {len(complete_events)} events")
        print(f"Writing {len(complete_events)} events to {output_path}:")

    write_processed_log(complete_events, output_path, verbose)

    if verbose:
        print(f"Wrote {len(complete_events)} events to {output_path}")


def preprocess_log_from_dir(directory: str,
                            output_path: str, 
                            num_lines: int | None = None,
                            process_responsibility: bool = False,
                            verbose: bool = False) -> None:

    log_path, successors_path = get_log_files(None, None, directory, verbose)
    preprocess_log(log_path, output_path, successors_path, num_lines, process_responsibility, verbose)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preprocess a chord log file to add regimen and state information.")
    parser.add_argument("-f", "--file", type=file_path, help="Path to the chord log file")
    parser.add_argument("-s", "--successors", type=file_path, help="Path to the chord successors file")
    parser.add_argument("-d", "--directory", type=dir_path, help="Path to the directory with log and successors file")
    parser.add_argument("-o", "--output", type=str, required=True, help="Path to destination output")

    parser.add_argument("-n", "--num-lines", type=int, default=None, 
                        help="Maximum number of lines to process (default: all)")

    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")

    parser.add_argument("-r", "--responsibility", action="store_true", help="Add responsibility actions to log")

    return parser.parse_args()


def main():
    args = parse_args()

    log_path, successors_path = get_log_files(log_path=args.file,
                                              successors_path=args.successors,
                                              dir_path=args.directory,
                                              verbose=args.verbose)
        
    preprocess_log(log_path, 
                   args.output, 
                   successors_path=successors_path,
                   num_lines=args.num_lines,
                   process_responsibility=args.responsibility,
                   verbose=args.verbose)


if __name__ == "__main__":
    main()
