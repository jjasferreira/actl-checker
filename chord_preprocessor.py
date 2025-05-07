import argparse
import os
from trace_parser import parse_trace_file 
from ast_nodes import Trace, ActionType, Event, BeginEvent, EndEvent
from datetime import timedelta
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


def process_membership(event : Event , current_members: set[str], membership_intervals : list[Event],
                       membership_operations : dict[str, Event], stable_intervals : list[Event]):



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

        else:
            assert event.action_type in (ActionType.LEAVE, ActionType.FAIL), f"Expected LEAVE or FAIL, got {event.action_type}"

            assert node in current_members, f"Node \"{event.values[0]}\" cannot leave because it is not a member: {event}, {current_members: }"

            current_members.remove(node)

            membership_intervals.append(EndEvent(ActionType.MEMBER, [],
                                f"Membership{len(membership_intervals) // 2}-{node}",
                                time = event.get_time() + timedelta(milliseconds=1)))

def process(trace : Trace) -> tuple[list[Event], list[Event], list[Event]]:
    
    if len(trace.events) == 0:
        return [], [], []

    stores = {}
    readonly_intervals = []

    current_members = set()
    membership_intervals = []

    membership_operations = {}
    stable_intervals = []


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
    for instant in trace.events:
        for event in instant:
            event_counter += 1

            if event.action_type == ActionType.STORE:
                process_readonly(event, stores, readonly_intervals)

            elif event.action_type in (ActionType.JOIN, ActionType.LEAVE, ActionType.FAIL):
                process_membership(event, current_members, membership_intervals, membership_operations, stable_intervals)

            #TODO:
            # process_successors

    print("Members")
    pprint(membership_intervals)

    print("\n\nReadonly")
    pprint(readonly_intervals)

    print("\n\nStable")
    pprint(stable_intervals)

    print("Processed events: ", event_counter)

    return membership_intervals, readonly_intervals, stable_intervals



#TODO: 
# parse successors file
# def process_successors

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

    if args.file:
        trace = parse_trace_file(args.file, args.num_lines)


        membership_intervals, readonly_intervals, stable_intervals =  process(trace)

        with open(args.output, "w") as output_file:

            trace_events = flatten(trace.events)
            complete_events = trace_events + membership_intervals + readonly_intervals + stable_intervals
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
