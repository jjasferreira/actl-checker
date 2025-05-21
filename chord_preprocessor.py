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
def process_membership(event : Event , current_members: set[str], membership_intervals : list[Event],
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

            current_members.add(node)

            membership_intervals.append(BeginEvent(ActionType.MEMBER, [node],
                                f"Membership{len(membership_intervals) // 2}-{node}",
                                time = event.get_time() + timedelta(milliseconds=1)))
            return node

        else:
            assert event.action_type in (ActionType.LEAVE, ActionType.FAIL), f"Expected LEAVE or FAIL, got {event.action_type}"

            assert node in current_members, f"Node \"{event.values[0]}\" cannot leave because it is not a member: {event}, {current_members: }"

            current_members.remove(node)

            membership_intervals.append(EndEvent(ActionType.MEMBER, [],
                                f"Membership{len(membership_intervals) // 2}-{node}",
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
                           current_members: set[str], ideal_intervals : list[Event]):

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

def update_responsibility_intervals( successor_pointers: dict[str, str],
                       current_members: set[str],
                       current_responsibilities : dict[str, list[Event]], responsability_intervals : list[Event]):
    pass

def process_successors(successor_change: tuple[datetime, str, str], successor_pointers: dict[str, str],
                       current_members: set[str], ideal_intervals : list[Event],
                       current_responsibilities : dict[str, list[Event]], responsability_intervals : list[Event]):

    time, node, successor = successor_change
    successor_pointers[node] = successor

    update_ideal_intervals(time, successor_pointers, current_members, ideal_intervals)



def process(trace : Trace, successor_changes : list[tuple[datetime, str, str]]) -> tuple[list[Event], list[Event], list[Event], list[Event]]:
    
    if len(trace.events) == 0:
        return [], [], [], []

    stores = {}
    readonly_intervals = []

    current_members = set()
    membership_intervals = []

    membership_operations = {}
    stable_intervals = []

    successor_pointers = {}
    ideal_intervals = []
    current_responsibilities = {}
    responsibility_intervals = []

    first_event = trace.events[0][0]
    initial_timestamp = first_event.get_time() - timedelta(milliseconds=1)

    # Initial member
    initial_member = first_event.values[0]
    current_members.add(initial_member)
    membership_intervals.append(BeginEvent(ActionType.MEMBER, [initial_member],
                        f"Membership{len(membership_intervals) // 2}-{initial_member}",
                        time = initial_timestamp))


    # Initially in a readonly  regimen
    readonly_intervals.append(BeginEvent(ActionType.READONLY, [], f"ReadOnly{len(readonly_intervals) // 2}",
                        time = initial_timestamp))

    # Initially in a stable  regimen
    stable_intervals.append(BeginEvent(ActionType.STABLE, [], f"Stable{len(stable_intervals) // 2}",
                        time = initial_timestamp))

    event_counter = 0
    successor_changes_idx = 0
    for instant in trace.events:

        while successor_changes_idx < len(successor_changes) and \
            instant[0].get_time() > successor_changes[successor_changes_idx][0]:

            process_successors(successor_changes[successor_changes_idx], successor_pointers, current_members, ideal_intervals, current_responsibilities, responsibility_intervals)
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
                    update_ideal_intervals(new_time, successor_pointers, current_members, ideal_intervals)

                    # update_responsibility_intervals(successor_pointers, current_members, current_responsibilities, responsibility_intervals)



    print("Members")
    pprint(membership_intervals)

    print("\n\nReadonly")
    pprint(readonly_intervals)

    print("\n\nStable")
    pprint(stable_intervals)


    print("\n\nIdeal")
    pprint(ideal_intervals)

    print("\n\nResponsibilities")
    pprint(responsibility_intervals)

    print("Processed events: ", event_counter)

    return membership_intervals, readonly_intervals, stable_intervals, ideal_intervals



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

def file_path(path: str) -> str:
    if os.path.isfile(path):
        return path
    raise argparse.ArgumentTypeError(f"file_path: '{path}' is not a valid file")


def main():
    parser = argparse.ArgumentParser(description="Preprocess a chord log file.")
    parser.add_argument("-f", "--file", type=file_path, required=True, help="Path to the chord log file")
    parser.add_argument("-s", "--successors", type=file_path, help="Path to the chord successors file")
    parser.add_argument("-o", "--output", type=str, required=True, help="Path to destination output")
    parser.add_argument("-n", "--num-lines", type=int, default=None, 
                        help="Maximum number of lines to process (default: all)")

    args = parser.parse_args()

    trace = parse_trace_file(args.file, args.num_lines)

    if args.successors:
        successor_changes = parse_successors(args.successors)
    else:
        successor_changes = []

    membership_intervals, readonly_intervals, stable_intervals, ideal_intervals =  process(trace, successor_changes)

    with open(args.output, "w") as output_file:

        trace_events = flatten(trace.events)
        complete_events = trace_events + membership_intervals + readonly_intervals + stable_intervals + ideal_intervals
        complete_events.sort(key=lambda x: x.get_time())

        for event in complete_events:
            if event.action_type == ActionType.FAIL and isinstance(event, EndEvent):
                continue


            time = event.get_time().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

            event_type = event.get_type().value

            if isinstance(event, EndEvent):
                if event.action_type in (ActionType.STORE, ActionType.LOOKUP, ActionType.STORE, ActionType.LEAVE, ActionType.JOIN):
                    event_type = "Reply" + event_type 
                else:
                    event_type = "End" + event_type 

            id = event.get_id()
            values = ', '.join(event.values)
            log_entry = f"{time}, {event_type}, {id}, {values}"

            output_file.write(log_entry + "\n")


def flatten(lst: list[list[T]]) -> list[T]:
    return [item for sublist in lst for item in sublist]

if __name__ == "__main__":
    main()
