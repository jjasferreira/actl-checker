DEBUG = False

from abc import ABC, abstractmethod
from collections import defaultdict
from enum import Enum
from typing import Any, TypeAlias
from datetime import datetime
import sys

# get_possible_values and get_possible_actions are not used, as well as forallquantifier and existsquantifier

VarCollection : TypeAlias = dict[tuple["ActionType", int], list[str]]

class ActionType(Enum):
    LOOKUP = "LOOKUP"
    STORE = "STORE"
    FINDNODE = "FINDNODE"
    JOIN = "JOIN"
    LEAVE = "LEAVE"
    FAIL = "FAIL"
    IDEAL = "IDEAL"
    STABLE = "STABLE"
    READONLY = "READONLY"
    MEMBER = "MEMBER"
    RESPONSIBLE = "RESPONSIBLE"

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_

class ActionValue():
    def __init__(self, action_type: ActionType, interval_value: "IntervalValue", input_values: list[str], output_values: list[str]):
        self.action_type = action_type
        self.interval_value = interval_value
        self.input_values = input_values
        self.output_values = output_values

    def get_action_type(self) -> ActionType:
        return self.action_type

    def get_interval_value(self) -> "IntervalValue":
        return self.interval_value

    def get_input_values(self) -> list[str]:
        return self.input_values

    def get_output_values(self) -> list[str]:
        return self.output_values
        self.output_values = output_values

    # Completes the action's end time point and sets the output values if missing
    def complete_end(self, interval_end: int, output_values: list[str]) -> bool:
        if self.interval_value.end != float("inf") or self.output_values != []:
            return False
        else:
            self.interval_value.set_end(interval_end)
            self.output_values = output_values
            return True

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, ActionValue) and
            self.action_type == other.action_type and
            self.interval_value == other.interval_value and
            self.input_values == other.input_values and
            self.output_values == other.output_values)

    def __repr__(self) -> str:
        # return f"ActionValue({self.action_type}, {self.interval_value}, {self.input_values}, {self.output_values})"
        return f"({self.interval_value.begin, self.interval_value.end}, ({', '.join(self.input_values)}), ({', '.join(self.output_values)}))"

class Event(ABC):
    @abstractmethod
    def __init__(self, action_type: ActionType, id: str | None, values: str | list[str], time: datetime | None):
        self.action_type = action_type
        self.id = id
        self.values = values if isinstance(values, list) else [values]
        self.time = time
    
    def get_action_type(self) -> ActionType:
        return self.action_type
    
    def get_id(self) -> str:
        assert self.id is not None, f"Event.get_id(): Event id is None for {self}"
        return self.id

    def get_time(self) -> datetime:
        assert self.time is not None, f"Event.get_time(): Event time is None for {self}"
        return self.time

    def matches(self, other: object) -> bool:
        if type(self) != type(other):
            return False
        else:
            return self.action_type == other.action_type and self.values == other.values
    
    def entry_str(self) -> str:
        time_str = self.get_time().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        action_type_str = self.action_type_str()
        id_str = self.get_id()
        values_str = ', '.join(self.values)
        return f"{time_str}, {action_type_str}, {id_str}, {values_str}"

    @abstractmethod
    def action_type_str(self) -> str:
        pass

    def __hash__(self) -> int:
        return hash((self.action_type, self.id, tuple(self.values), self.time))

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, type(self)) and
            self.action_type == other.action_type and 
            self.values == other.values and 
            self.id == other.id and 
            self.time == other.time)

    def __repr__(self):
        # return f"({self.time}, {self.id}, {self.action_type}, {self.values})"
        return f"⟨{self.action_type.name.lower()}⟩_{self.id} ({', '.join(self.values)})"

class BeginEvent(Event):
    def __init__(self, action_type, id, values, time):
        super().__init__(action_type, id, values, time)

    def action_type_str(self) -> str:
        return self.get_action_type().value

    def __repr__(self) -> str:
        # return f"BeginEvent{super().__repr__()}"
        return f"B {super().__repr__()}"

class EndEvent(Event):
    def __init__(self, action_type, id, values, time):
        super().__init__(action_type, id, values, time)

    def action_type_str(self) -> str:
        if self.action_type in (ActionType.STORE, ActionType.LOOKUP, ActionType.LEAVE, ActionType.JOIN):
            return "Reply" + self.get_action_type().value
        else:
            return "End" + self.get_action_type().value

    def __repr__(self) -> str:
        # return f"EndEvent{super().__repr__()}"
        return f"E {super().__repr__()}"

class Trace:
    def __init__(self, events: list[set[Event]] | None = None,
        actions: dict["ActionType", list["ActionValue"]] | None = None, 
        input_values: VarCollection | None = None,
        output_values: VarCollection | None = None):

        if events is None:
            events = []
        self.events = events
        if actions is None:
            actions = defaultdict(list)
        self.actions = actions

        #NOTE: input and output values used only for variable quantifiers, which are currently not used
        if input_values is None:
            input_values = defaultdict(list) # { (LOOKUP, 63) : list[str] }
        self.input_values = input_values
        if output_values is None:
            output_values = defaultdict(list)
        self.output_values = output_values

    def __len__(self) -> int:
        return len(self.events)

    # Returns the total number of events in the trace
    def get_length(self) -> int:
        return sum(len(event_set) for event_set in self.events)

    def insert_event(self, event: Event) -> int:
        if len(self.events) == 0 or next(iter(self.events[-1])).get_time() < event.get_time():
            self.events.append({event}) # new time point
        else:
            assert next(iter(self.events[-1])).get_time() == event.get_time(), f"Trace events not ordered: {next(iter(self.events[-1])).get_time()} > {event.get_time()}"
            self.events[-1].add(event) # same time point
        return len(self.events) - 1

    def insert_begin_event(self, action_type: ActionType, id: str, input_values: list[str], time: datetime) -> ActionValue:
        # Insert event into trace
        event = BeginEvent(action_type, id, input_values, time)
        begin_timepoint = self.insert_event(event)
        # Insert action occurrence
        interval_value = IntervalValue(begin_timepoint)
        action_value = ActionValue(action_type, interval_value, input_values, [])
        self.actions.setdefault(action_type, []).append(action_value)
        # Insert input values
        for (i, value) in enumerate(input_values):
            self.input_values[(action_type, i)].append(value)
        return action_value

    def insert_end_event(self, action_value: ActionValue, id: str, output_values: list[str], time: datetime) -> bool:
        # Insert event into trace
        event = EndEvent(action_value.get_action_type(), id, output_values, time)
        end_timepoint = self.insert_event(event)
        # Insert output values
        for (i, value) in enumerate(output_values):
            self.output_values[(action_value.get_action_type(), i)].append(value)
        # Update action occurrence
        return action_value.complete_end(end_timepoint, output_values)

    def get_input_values(self, action_type: ActionType, index: int) -> list[str]:
        return self.input_values[(action_type, index)]

    def get_output_values(self, action_type: ActionType, index: int) -> list[str]:
        return self.output_values[(action_type, index)]

    def find_occurrences(self, action_type: ActionType) -> list[ActionValue]:
        return self.actions[action_type]

    def complete_event(self, event: Event, timepoint: int) -> None | Event: 
        assert event.id is None
        if timepoint < 0 or timepoint >= len(self.events):
            return None
        for candidate in self.events[timepoint]:
            if candidate.matches(event):
                return candidate
        return None

    def __repr__(self) -> str:
        events_str = ""
        for (i, event_set) in enumerate(self.events):
            events_str += f"\n {i}: {{ "
            for event in event_set:
                events_str += f"{event}"
            events_str += " }"
        
        actions_str = ""
        for (action_type, values) in self.actions.items():
            actions_str += f"\n{action_type.name.lower()}:"
            for value in values:
                actions_str += f"\n{value}"

        inputs_str = "\n".join([f"{action_type.name.lower()} {[i]}: {', '.join(values)}" for (action_type, i), values in self.input_values.items()])
        outputs_str = "\n".join([f"{action_type.name.lower()} {[i]}: {', '.join(values)}" for (action_type, i), values in self.output_values.items()])

        return f"\nTrace(\nEvents:{events_str}\n\nAction Occurrences:{actions_str}\n\nInput Values:\n{inputs_str}\n\nOutput Values:\n{outputs_str})"

class Formula(ABC):
    @abstractmethod
    def evaluate(self, trace: Trace, store: dict[str, str], interval_store: "dict[str, IntervalValue]") -> Any:
        pass

    def get_possible_values(self, trace: Trace, store: dict[str, str], interval_store: dict[str, "IntervalValue"], var: "Variable") -> list[str]:
        return []

    def get_possible_actions(self, trace: Trace, store: dict[str, str], interval_store: dict[str, "IntervalValue"], interval: "Interval") -> list["Action"]:
        return []

class Variable(Formula):
    def __init__(self, label: str):
        self.label = label

    def evaluate(self, _trace, store, _interval_store) -> str:
        if self.label not in store:
            raise ValueError(f"Variable {self.label} not found in store")
        return store[self.label]

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, Variable) and
            self.label == other.label)

    def __repr__(self) -> str:
        # return f"Variable({self.label})"
        return f"{self.label}"

class IntervalValue(Formula):
    def __init__(self, begin: int, end: int | None = None):
        self.begin = begin
        if end is None:
            self.end = float("inf")
        else: 
            self.end = end

    def set_end(self, end: int) -> bool:
        if self.end != float("inf"):
            return False
        else:
            self.end = end
            return True

    def evaluate(self, _trace, _store, _interval_store) -> "IntervalValue":
        return self

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, IntervalValue) and
            self.begin == other.begin and
            self.end == other.end)

    def __repr__(self) -> str:
        return f"IntervalValue({self.begin}, {self.end})"

class Interval(Formula):
    def __init__(self, label: str):
        self.label = label

    def evaluate(self, _trace, _store, interval_store) -> IntervalValue:
        if self.label not in interval_store:
            raise ValueError(f"Interval {self.label} not found in interval store")
        return interval_store[self.label]

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, Interval) and
            self.label == other.label)

    def __repr__(self) -> str:
        # return f"Interval({self.label})"
        return f"{self.label}"

class UnaryExpr(Formula, ABC):
    @abstractmethod
    def __init__(self, expression: Formula):
        self.expression = expression

    def get_possible_values(self, trace, store, interval_store, variable) -> list[str]:
        return self.expression.get_possible_values(trace, store, interval_store, variable)

    def get_possible_actions(self, trace, store, interval_store, interval) -> list["Action"]:
        return self.expression.get_possible_actions(trace, store, interval_store, interval)

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, type(self)) and
            self.expression == other.expression)

class Not(UnaryExpr):
    def __init__(self, expression):
        super().__init__(expression)

    def evaluate(self, trace, store, interval_store) -> bool:
        result = self.expression.evaluate(trace, store, interval_store)
        assert isinstance(result, bool), f"\"Not\" operator expected boolean result from {self.expression}, but got {result} of type {type(result)}"
        return not result

    def __repr__(self) -> str:
        return f"¬{self.expression}"

class BinaryExpr(Formula, ABC):
    @abstractmethod
    def __init__(self, left: Formula, right: Formula):
        self.left = left
        self.right = right

    def get_possible_values(self, trace, store, interval_store, target_var: Variable) -> list[str]:
        possible_values = self.left.get_possible_values(trace, store, interval_store, target_var)
        possible_values.extend(self.right.get_possible_values(trace, store, interval_store, target_var))
        return possible_values

    def get_possible_actions(self, trace, store, interval_store, interval) -> list["Action"]:
        possible_actions = self.left.get_possible_actions(trace, store, interval_store, interval)
        possible_actions.extend(self.right.get_possible_actions(trace, store, interval_store, interval))
        return possible_actions

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, type(self)) and
            self.left == other.left and
            self.right == other.right)

class Equal(BinaryExpr):
    def __init__(self, left, right):
        super().__init__(left, right)

    def evaluate(self, trace, store, interval_store) -> bool:
        left =  self.left.evaluate(trace, store, interval_store) 
        right = self.right.evaluate(trace, store, interval_store)
        return left == right

    def __repr__(self) -> str:
        return f"({self.left} = {self.right})"

class Implies(BinaryExpr):
    def __init__(self, left, right):
        super().__init__(left, right)

    def evaluate(self, trace, store, interval_store) -> bool:
        left = self.left.evaluate(trace, store, interval_store)
        right = self.right.evaluate(trace, store, interval_store)
        return (not left) or right

    def __repr__(self) -> str:
        return f"({self.left} => {self.right})"

class NAryExpr(Formula, ABC):
    @abstractmethod
    def __init__(self, *expressions: Formula):
        self.expressions = expressions
        assert len(expressions) > 1, f"\"{self.__class__.__name__}\" requires at least two expressions, but got {len(expressions)}"

    def get_possible_values(self, trace, store, interval_store, target_var) -> list[str]:
        possible_values = []
        for expression in self.expressions:
            possible_values.extend(expression.get_possible_values(trace, store, interval_store, target_var))
        return possible_values

    def get_possible_actions(self, trace, store, interval_store, interval) -> list["Action"]:
        possible_actions = []
        for expression in self.expressions:
            possible_actions.extend(expression.get_possible_actions(trace, store, interval_store, interval))
        return possible_actions

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, type(self)) and
            self.expressions == other.expressions)

class And(NAryExpr):
    def __init__(self, *expressions):
        super().__init__(*expressions)

    def evaluate(self, trace, store, interval_store) -> bool:
        for expression in self.expressions:
            result = expression.evaluate(trace, store, interval_store)
            assert isinstance(result, bool), f"\"And\" operator expected boolean result from {expression}, but got {result} of type {type(result)}"
            if not result:
                return False
        return True

    def __repr__(self) -> str:
        return " ∧ ".join(map(str, self.expressions))

class Or(NAryExpr):
    def __init__(self, *expressions):
        super().__init__(*expressions)

    def evaluate(self, trace, store, interval_store) -> bool:
        for expression in self.expressions:
            result = expression.evaluate(trace, store, interval_store)
            assert isinstance(result, bool), f"\"Or\" operator expected boolean result from {expression}, but got {result} of type {type(result)}"
            if result:
                return True
        return False

    def __repr__(self) -> str:
        return " v ".join(map(str, self.expressions))

class Quantifier(Formula, ABC):
    @abstractmethod
    def __init__(self, variables: Variable | list[Variable], expression: Formula):
        self.variables = variables if isinstance(variables, list) else [variables]
        self.expression = expression

    def get_possible_values(self, trace, store, interval_store, var) -> list[str]:
        if var in self.variables:
            return []
        else:
            return self.expression.get_possible_values(trace, store, interval_store, var)

    def get_possible_actions(self, trace, store, interval_store, interval) -> list["Action"]:
        return self.expression.get_possible_actions(trace, store, interval_store, interval)

    def evaluate_naively(self, trace: Trace, store: dict[str, str], interval_store: dict[str, IntervalValue], short_circuit_on: bool) -> bool:
        return self.evaluate_naively_recursive(trace, store, interval_store, short_circuit_on, 0)

    def evaluate_naively_recursive(self, trace: Trace, store: dict[str, str], interval_store: dict[str, IntervalValue], short_circuit_on: bool, var_idx: int) -> bool:

        if var_idx >= len(self.variables):
            result =  self.expression.evaluate(trace, var_store, interval_store)
            # print(f"Base case Evaluating: {self.expr} with {var_store} -> {result}")
            return result

        else:

            #TODO: check if var is not bound in current store?
            var = self.variables[var_idx]

            possible_values = self.expression.get_possible_values(trace, var_store, interval_store, var)
    
            # print(f"{var = } {possible_values = }")

            #TODO: Double check if it is handled correctly:
            # if no possible values exist then
            # return False for Exists
            # evaluate the expression for ForAll 
            if not possible_values:
                print(f"Warning: No possible values found for {var}.", file=sys.stderr)

                if short_circuit_on: # == True
                    return False

                result = self.evaluate_naively_recursive(trace, var_store, interval_store, short_circuit_on, var_idx + 1)

                return result

            for value in possible_values:                    
                new_store = var_store.copy()
                new_store[var.label] = value

                result = self.evaluate_naively_recursive(trace, new_store, interval_store, short_circuit_on, var_idx + 1)
                # print(f"Recursive case Evaluating {var_idx = }, {var = }, { value = }: {self.expr} with {var_store} -> {result}")
                if result == short_circuit_on:
                    return short_circuit_on
            else:

                # print(f"Recursive case COMPLETED Evaluating {var_idx = }, {var = }: {self.expr} with {var_store}")
                return not short_circuit_on

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, type(self)) and
            self.vars == other.vars and
            self.expression == other.expression)

class Exists(Quantifier):
    def __init__(self, variables, expression):
        super().__init__(variables, expression)

    def evaluate(self, trace, store, interval_store) -> bool:
        return self.evaluate_naively(trace, store, interval_store, True)

    def __repr__(self) -> str:
        variables_str = ", ".join(map(str, self.variables))
        return f"∃({variables_str}). ({self.expression})"

class ForAll(Quantifier):
    def __init__(self, variables, expression):
        super().__init__(variables, expression)

    def evaluate(self, trace, store, interval_store) -> bool: 
        return self.evaluate_naively(trace, store, interval_store, False)

    def __repr__(self) -> str:
        variables_str = ", ".join(map(str, self.variables))
        return f"∀({variables_str}). ({self.expression})"

class ActionQuantifier(Formula, ABC):

    @abstractmethod
    def __init__(self, action: "Action", expression: Formula):
        assert isinstance(action, Action), f"Expected Action, but got '{action}' of {type(action)}"
        self.action = action
        self.expression = expression

    #def get_possible_values(self, trace, store, interval_store, var) -> list[str]:
    #    if var in self.vars:
    #        return []
    #    else:
    #        return self.expr.get_possible_values(trace, store, interval_store, var)

    def get_possible_actions(self, trace, store, interval_store, interval) -> list["Action"]:
        return self.expression.get_possible_actions(trace, store, interval_store, interval)

    def evaluate_naively(self, trace: Trace, store: dict[str, str], interval_store: dict[str, IntervalValue], short_circuit_on: bool) -> bool:
        action = self.action
        occurrences = trace.find_occurrences(action.get_action_type())
        # For each occurrence of the action in the trace
        for occurrence in occurrences:
            interval_value = occurrence.interval_value
            input_values = occurrence.input_values
            output_values = occurrence.output_values

            # TODO: Mismatched number of inputs and outputs between formula and trace action
            if len(input_values) < len(action.inputs) or len(output_values) < len(action.outputs):
                print(f"Warning: Occurrence {occurrence} has less input or output values than action in formula: {action}", file=sys.stderr)
                continue

            # New domain variable environment
            skip_occurrence = False
            new_store = store.copy()
            for (variable, value) in zip(action.inputs, input_values):
                if isinstance(variable, Wildcard):
                    continue
                if variable.label in new_store:
                    if new_store[variable.label] != value:
                        skip_occurrence = True
                        break
                else:
                    new_store[variable.label] = value
            if skip_occurrence:
                continue
            for (variable, value) in zip(action.outputs, output_values):
                if isinstance(variable, Wildcard):
                    continue
                if variable.label in new_store:
                    if new_store[variable.label] != value:
                        skip_occurrence = True
                        break
                else:
                    new_store[variable.label] = value
            if skip_occurrence:
                continue

            # New interval variable environment
            new_interval_store = interval_store.copy()
            new_interval_store[action.interval.label] = interval_value
            # Evaluate the inner expression
            DEBUG and print(f"{new_store = }, {new_interval_store = }")
            result = self.expression.evaluate(trace, new_store, new_interval_store)
            if result == short_circuit_on:
                return short_circuit_on
        return not short_circuit_on

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, type(self)) and
            self.action == other.action and
            self.expression == other.expression)

class ExistsAction(ActionQuantifier):
    def __init__(self, action, expression):
        super().__init__(action, expression)
    
    def evaluate(self, trace, store, interval_store) -> bool: 
        return self.evaluate_naively(trace, store, interval_store, True)

    def __repr__(self) -> str:
        return f"∃ {self.action} . {self.expression}"

class ForAllAction(ActionQuantifier):
    def __init__(self, action, expression):
        super().__init__(action, expression)

    def evaluate(self, trace, store, interval_store) -> bool: 
        return self.evaluate_naively(trace, store, interval_store, False)

    def __repr__(self) -> str:
        return f"∀ {self.action} . {self.expression}"

class Action(Formula):
    def __init__(self, action_type: ActionType, interval: Interval, inputs: Variable | list[Variable], outputs: Variable | list[Variable]):
        self.action_type = action_type
        self.interval = interval
        self.inputs = inputs if isinstance(inputs, list) else [inputs]
        self.outputs = outputs if isinstance(outputs, list) else [outputs]
        assert isinstance(interval, Interval), f"Expected Interval, but got '{interval}' of {type(interval)}, during initialization of Action {self}"
        for variable in self.inputs + self.outputs:
            assert isinstance(variable, Variable), f"Expected Variable, but got '{variable}' of {type(variable)}, during initialization of Action {self}"

    def get_action_type(self) -> ActionType:
        return self.action_type

    def evaluate(self, trace, store, interval_store) -> bool:
        eval_interval = self.interval.evaluate(trace, store, interval_store)
        eval_inputs = [variable.evaluate(trace, store, interval_store) for variable in self.inputs]
        eval_outputs = [variable.evaluate(trace, store, interval_store) for variable in self.outputs]

        # Create begin and end events with missing id and time, to be completed by the trace
        begin_event = BeginEvent(self.action_type, None, eval_inputs, None)
        completed_begin_event = trace.complete_event(begin_event, eval_interval.begin)
        if completed_begin_event is None:
            return False
        end_event = EndEvent(self.action_type, None, eval_outputs, None)
        completed_end_event = trace.complete_event(end_event, action_interval.end)

        # NOTE:
        # Handle infinite intervals
        # end_event is not None iff t_e = "inf"
        if completed_end_event is None:
            return action_interval.end == float("inf")
            
        # TODO: 
        # Handle with infinite intervals
        # if t2 = "inf" then no end event should match its id
        # if evaluated_interval.end is not None:
    
        return (completed_end_event is not None) and completed_end_event.id == completed_begin_event.id

    def get_possible_values(self, trace, store, interval_store, var) -> list[str]:
        possible_values = []
        for (i, variable) in enumerate(self.inputs):
            if variable.label == var.label:
                possible_values.extend(trace.get_inputs(self.action_type, i))
        for (i, variable) in enumerate(self.outputs):
            if variable.label == var.label:
                possible_values.extend(trace.get_outputs(self.action_type, i))
        return possible_values

    def get_possible_actions(self, trace, store, interval_store, interval) -> list["Action"]:
        if self.interval.label == interval.label:
            return [self]
        else:
            return []

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, Action) and
            self.action_type == other.action_type and 
            self.interval == other.interval and 
            self.inputs == other.inputs and 
            self.outputs == other.outputs)

    def __repr__(self) -> str:
        action_type_str = self.action_type.name.lower()
        inputs_str = ", ".join(map(str, self.inputs))
        outputs_str = ", ".join(map(str, self.outputs))
        return f"{action_type_str}[{self.interval}] ({inputs_str}) -> ({outputs_str})"

class IntervalPredicate(Formula, ABC):
    @abstractmethod
    def __init__(self, left: Interval, right: Interval):
        assert isinstance(left, Interval), f"Expected Interval, but got '{left}' of {type(left)}"
        assert isinstance(right, Interval), f"Expected Interval, but got '{right}' of {type(right)}"
        self.left = left
        self.right = right
    
    def __eq__(self, other: object) -> bool:
        return (isinstance(other, type(self)) and
            self.left == other.left and 
            self.right == other.right)

class Before(IntervalPredicate):
    def __init__(self, left, right):
        super().__init__(left, right)

    def evaluate(self, trace, store, interval_store) -> bool:
        left = self.left.evaluate(trace, store, interval_store)
        right = self.right.evaluate(trace, store, interval_store)
        return left.end < right.begin

    def __repr__(self) -> str:
        return f"Before({self.left}, {self.right})"

class Meets(IntervalPredicate):
    def __init__(self, left, right):
        super().__init__(left, right)

    def evaluate(self, trace, store, interval_store) -> bool:
        left = self.left.evaluate(trace, store, interval_store)
        right = self.right.evaluate(trace, store, interval_store)
        return left.end == right.begin

    def __repr__(self) -> str:
        return f"Meets({self.left}, {self.right})"

class Overlaps(IntervalPredicate):
    def __init__(self, left, right):
        super().__init__(left, right)

    def evaluate(self, trace, store, interval_store) -> bool:
        left = self.left.evaluate(trace, store, interval_store)
        right = self.right.evaluate(trace, store, interval_store)
        return left.begin < right.begin < left.end < right.end

    def __repr__(self) -> str:
        return f"Overlaps({self.left}, {self.right})"

class Starts(IntervalPredicate):
    def __init__(self, left, right):
        super().__init__(left, right)

    def evaluate(self, trace, store, interval_store) -> bool:
        left = self.left.evaluate(trace, store, interval_store)
        right = self.right.evaluate(trace, store, interval_store)
        return left.begin == right.begin and left.end < right.end

    def __repr__(self) -> str:
        return f"Starts({self.left}, {self.right})"

class During(IntervalPredicate):
    def __init__(self, left, right):
        super().__init__(left, right)

    def evaluate(self, trace, store, interval_store) -> bool:
        left = self.left.evaluate(trace, store, interval_store)
        right = self.right.evaluate(trace, store, interval_store)
        return right.begin < left.begin and left.end < right.end

    def __repr__(self) -> str:
        return f"During({self.left}, {self.right})"

class Finishes(IntervalPredicate):
    def __init__(self, left, right):
        super().__init__(left, right)

    def evaluate(self, trace, store, interval_store) -> bool:
        left = self.left.evaluate(trace, store, interval_store)
        right = self.right.evaluate(trace, store, interval_store)
        return left.end == right.end and right.begin < left.begin

    def __repr__(self) -> str:
        return f"Finishes({self.left}, {self.right})"

class Equals(IntervalPredicate):
    def __init__(self, left, right):
        super().__init__(left, right)

    def evaluate(self, trace, store, interval_store) -> bool:
        left = self.left.evaluate(trace, store, interval_store)
        right = self.right.evaluate(trace, store, interval_store)
        return left == right

    def __repr__(self) -> str:
        return f"Equals({self.left}, {self.right})"

class Constant(Formula):
    def __init__(self, label: str):
        self.label = label
    
    def evaluate(self, _trace, _store, _interval_store) -> str:
        return self.label

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, Constant) and
            self.label == other.label)

    def __repr__(self) -> str:
        return f"Constant({self.label})"

class Wildcard(Variable):
    def __init__(self):
        super().__init__("-")

    def evaluate(self, _trace, _store, _interval_store) -> bool:
        raise ValueError("Wildcard should not be evaluated directly")

    def __eq__(self, other: object) -> bool:
        return False

    def __repr__(self) -> str:
        return f"Wildcard({self.label})"
