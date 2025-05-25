from abc import ABC, abstractmethod
from collections import defaultdict
from enum import Enum
from typing import Any, TypeAlias
from datetime import datetime
import sys

IntervalCollection : TypeAlias = dict["ActionType", list["IntervalValue"]]
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
        return value.upper() in cls._value2member_map_ 

    @classmethod
    def _missing_(cls, value):
        if not isinstance(value, str):
            return None

        value = value.upper()
        for member in cls:
            if member.value == value:
                return member

        return None


class Event(ABC):
    @abstractmethod
    def __init__(self, action_type : ActionType, values : str | list[str], id : str | None, time : datetime | None):
        self.action_type = action_type
        self.values = values if isinstance(values, list) else [values]
        self.id = id
        self.time = time

    def get_time(self) -> datetime:
        assert self.time is not None, f"Event.get_time(): Event time is None for {self}"
        return self.time

    def get_id(self) -> str:
        assert self.id is not None, f""
        return self.id

    def get_type(self) -> ActionType:
        return self.action_type

    def matches(self, other) -> bool:
        if type(self) != type(other):
            return False
        else:
            return self.action_type == other.action_type and self.values == other.values


    def __repr__(self):
        return f"({self.time}, {self.id}, {self.action_type}, {self.values})"

class BeginEvent(Event):
    def __init__(self, action_type : ActionType, values : str | list[str], id : str | None, time : datetime | None):
        super().__init__(action_type, values, id, time)

    def __repr__(self):
        return f"BeginEvent{super().__repr__()}"

class EndEvent(Event):
    def __init__(self, action_type : ActionType, values : str | list[str], id : str | None, time : datetime | None):
        super().__init__(action_type, values, id, time)

    def __repr__(self):
        return f"EndEvent{super().__repr__()}"

class Trace:
    def __init__(self, events : list[list[Event]] | None = None, 
                 intervals : IntervalCollection | None = None, 
                 inputs : VarCollection | None = None,
                 outputs : VarCollection | None = None):

        if events is None:
            events = []
        if intervals is None:
            intervals = defaultdict(list)
        if inputs is None:
            inputs = defaultdict(list)
        if outputs is None:
            outputs = defaultdict(list)
         
        self.events = events
        self.intervals = intervals
        self.inputs = inputs
        self.outputs = outputs

    def __len__(self) -> int:
        return len(self.events)

    def insert_event(self, event : Event) -> int:
        if len(self.events) == 0 or self.events[-1][0].get_time() < event.get_time():
            self.events.append([event])
        else:
            assert self.events[-1][0].get_time() == event.get_time(), f"Trace events not ordered: {self.events[-1][0].get_time()} < {event.get_time()}\nlast event: {self.events[-1][0]}\n inserting: {event}"

            self.events[-1].append(event)

        return len(self.events) - 1

    def insert_interval(self, action_type : ActionType, interval_value: "IntervalValue"):
        # TODO: use defaultdict or setdefault?
        # self.intervals[action_type].append(interval_value)
        self.intervals.setdefault(action_type, []).append(interval_value)

    def insert_input(self, action_type : ActionType, index : int, input_Value: str):
        self.insert_value(self.inputs, action_type, index, input_Value)

    def insert_output(self, action_type : ActionType, index : int, output_value: str):
        self.insert_value(self.outputs, action_type, index, output_value)

    def insert_value(self, vars : VarCollection, action_type : ActionType, index : int, value: str): 
        vars[(action_type, index)].append(value)

    def get_inputs(self,  action_type : ActionType, index : int) -> list[str]:
        return self.inputs[(action_type, index)]

    def get_outputs(self,  action_type : ActionType, index : int) -> list[str]:
        return self.outputs[(action_type, index)]

    def get_intervals(self,  action_type : ActionType) -> list["IntervalValue"]:
        return self.intervals[action_type]

    def get_actions(self, action_type : ActionType) -> list[tuple["IntervalValue", list[str], list[str]]]:
        actions = []

        intervals = self.intervals[action_type]

        for interval in intervals:
            for event in self.events[interval.begin]:
                if isinstance(event, BeginEvent) and event.action_type == action_type:
                    inputs = event.values
                    outputs = []
                    if interval.end != float("inf"):
                        assert isinstance(interval.end, int), f"Interval end boundary should be an index of Trace.events: \"{interval.end}\""
                        for end_event in self.events[interval.end]:
                            if isinstance(event, BeginEvent) and end_event.id == event.id:
                                outputs = end_event.values
                                break

                    actions.append((interval, inputs, outputs))

        return actions


    def complete_event(self, event : Event, t : int) -> None | Event: 
        assert event.id is None

        if t < 0 or t >= len(self.events):
            return None

        for candidate in self.events[t]:
            if candidate.matches(event):
                return candidate
        return None

    def __repr__(self):
        events = ""
        for (i, event_list) in enumerate(self.events):
            events += f"\nInstant {i}: "
            for event in event_list:
                events += f"\n\t{event}"

        outputs = "\n".join([f"{action_type}: {values}" for action_type, values in self.outputs.items()])
        inputs = "\n".join([f"{action_type}: {values}" for action_type, values in self.inputs.items()])
        intervals = "\n".join([f"{action_type}: {values}" for action_type, values in self.intervals.items()])

        return f"Trace(Events: {events};\nInputs: {inputs};\nOutputs: {outputs};\nIntervals: {intervals})"

class Formula(ABC):
    @abstractmethod
    def evaluate(self, trace : Trace, store : dict[str, str], interval_store : "dict[str, IntervalValue]") -> Any:
        pass

    def get_possible_values(self, trace : Trace, store : dict[str, str], interval_store : dict[str, "IntervalValue"], 
                            var : "Var") -> list[str]:
        return []


    def get_possible_actions(self, trace : Trace, store : dict[str, str], interval_store : dict[str, "IntervalValue"], 
                            interval : "Interval") -> list["Action"]:
        return []


class Var(Formula):
    def __init__(self, label):
        self.label = label

    def evaluate(self, _trace : Trace, store, _interval_store):
        if self.label not in store:
            raise ValueError(f"Variable {self.label} not found in store")

        return store[self.label]


    def __repr__(self):
        return f"Var({self.label})"


class IntervalValue(Formula):
    def __init__(self, begin : int, end : int | None = None): 
        self.begin = begin
        
        if end is None:
            self.end = float("inf")
        else: 
            self.end = end
   
    def complete_end(self, end : int) -> bool:
        if self.end != float("inf"):
            return False
        else:
            self.end = end
            return True

    def evaluate(self, _trace, _store, _interval_store):
        return self

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, IntervalValue)
            and self.begin == other.begin
            and self.end == other.end
        )

    def __repr__(self):
        return f"({self.begin}, {self.end})"

class Interval(Formula):
    def __init__(self, label):
        self.label = label

    def evaluate(self, _trace : Trace, _store, interval_store) -> IntervalValue:
        if self.label not in interval_store:
            raise ValueError(f"Interval {self.label} not found in interval store")
        return interval_store[self.label]

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Interval)
            and self.label == other.label
        )

    def __repr__(self):
        return f"Interval({self.label})"

class UnaryExpr(Formula, ABC):
    @abstractmethod
    def __init__(self, expression):
        self.expression = expression

    def get_possible_values(self, trace : Trace, store : dict[str, str], interval_store : dict[str, IntervalValue],
                            target_var : Var) -> list[str]:
        return self.expression.get_possible_values(trace, store, interval_store, target_var)


    def get_possible_actions(self, trace : Trace, store : dict[str, str], interval_store : dict[str, "IntervalValue"], 
                            interval : "Interval") -> list["Action"]:
        return self.expression.get_possible_actions(trace, store, interval_store, interval)

class Not(UnaryExpr):
    def __init__(self, expr):
        super().__init__(expr)

    def evaluate(self, trace : Trace, store, interval_store):
        result = self.expression.evaluate(trace, store, interval_store)
        
        assert isinstance(result, bool), f"\"Not\" operator expected boolean result from {self.expression}, but got {result} of type {type(result)}"

        return not result

    def __repr__(self):
        return f"¬{self.expression}"

class BinaryExpr(Formula, ABC):
    @abstractmethod
    def __init__(self, left : Formula, right : Formula):
        self.left = left
        self.right = right

    def get_possible_values(self, trace : Trace, store : dict[str, str], interval_store : dict[str, IntervalValue],
                            target_var : Var) -> list[str]:
        possible_values = self.left.get_possible_values(trace, store, interval_store, target_var)
        possible_values.extend(self.right.get_possible_values(trace, store, interval_store, target_var))
        return possible_values

    def get_possible_actions(self, trace : Trace, store : dict[str, str], interval_store : dict[str, "IntervalValue"], 
                            interval : "Interval") -> list["Action"]:
        possible_actions = self.left.get_possible_actions(trace, store, interval_store, interval)
        possible_actions.extend(self.right.get_possible_actions(trace, store, interval_store, interval))
        return possible_actions


class Equal(BinaryExpr):
    def __init__(self, left, right):
        super().__init__(left, right)

    def evaluate(self, trace : Trace, store, interval_store) -> Any:
        left =  self.left.evaluate(trace, store, interval_store) 
        right = self.right.evaluate(trace, store, interval_store)

        return left == right

    def __repr__(self):
        return f"({self.left} == {self.right})"


class NAryExpr(Formula, ABC):
    @abstractmethod
    def __init__(self, *expressions : Formula):
        assert len(expressions) > 1, f"\"{self.__class__.__name__}\" requires at least two expressions, but got {len(expressions)}"
        self.expressions = expressions


    def get_possible_values(self, trace : Trace, store : dict[str, str], interval_store : dict[str, IntervalValue],
                            target_var : Var) -> list[str]:
        possible_values = []

        for expression in self.expressions:
            possible_values.extend(expression.get_possible_values(trace, store, interval_store, target_var))

        return possible_values

    def get_possible_actions(self, trace : Trace, store : dict[str, str], interval_store : dict[str, "IntervalValue"], 
                            interval : "Interval") -> list["Action"]:

        possible_actions = []

        for expression in self.expressions:
            possible_actions.extend(expression.get_possible_actions(trace, store, interval_store, interval))

        return possible_actions

class And(NAryExpr):
    def __init__(self, *expressions : Formula):
        super().__init__(*expressions)
    
    def evaluate(self, trace : Trace, store, interval_store) -> Any:
        for expression in self.expressions:
            result = expression.evaluate(trace, store, interval_store)

            assert isinstance(result, bool), f"\"And\" operator expected boolean result from {expression}, but got {result} of type {type(result)}"
            
            if not result:
                return False

        return True

    def __repr__(self):
        return " ∧ ".join(map(str, self.expressions))

class Or(NAryExpr):
    def __init__(self, *expressions : Formula):
        super().__init__(*expressions)
    
    def evaluate(self, trace : Trace, store, interval_store) -> Any:
        for expression in self.expressions:
            result = expression.evaluate(trace, store, interval_store)
            assert isinstance(result, bool), f"\"Or\" operator expected boolean result from {expression}, but got {result} of type {type(result)}"
            if result:
                return True
        return False

    def __repr__(self):
        return " v ".join(map(str, self.expressions))

class Implies(BinaryExpr):
    def __init__(self, left, right):
        super().__init__(left, right)

    def evaluate(self, trace : Trace, store, interval_store) -> Any:
        left = self.left.evaluate(trace, store, interval_store) 
        right = self.right.evaluate(trace, store, interval_store)

        return (not left) or right

    def __repr__(self):
        return f"({self.left} => {self.right})"


class Quantifier(Formula, ABC):
    @abstractmethod
    def __init__(self, vars : Var | list[Var], expression : Formula):
        self.vars = vars if isinstance(vars, list) else [vars]
        self.expression = expression

    def get_possible_values(self, trace: Trace, store: dict[str, str], interval_store: dict[str, "IntervalValue"], var: Var) -> list[str]:
        if var in self.vars:
            return []
        else:
            return self.expression.get_possible_values(trace, store, interval_store, var)


    def get_possible_actions(self, trace : Trace, store : dict[str, str], interval_store : dict[str, "IntervalValue"], 
                            interval : "Interval") -> list["Action"]:
        return self.expression.get_possible_actions(trace, store, interval_store, interval)

    def evaluate_naively(self, trace : Trace, var_store : dict[str, str], interval_store : dict[str, IntervalValue],
                        short_circuit_on : bool):
        return self.evaluate_naively_recursive(trace, var_store, interval_store, short_circuit_on, 0)


    def evaluate_naively_recursive(self, trace : Trace, var_store : dict[str, str], interval_store : dict[str, IntervalValue],
                     short_circuit_on : bool, var_idx : int) -> bool:

        if var_idx >= len(self.vars):
            result =  self.expression.evaluate(trace, var_store, interval_store)
            # print(f"Base case Evaluating: {self.expr} with {var_store} -> {result}")
            return result

        else:

            #TODO: check if var is not bound in current store?
            var = self.vars[var_idx]

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

class Exists(Quantifier):
    def __init__(self, vars, expr):
        super().__init__(vars, expr)
    
    def evaluate(self, trace : Trace, var_store : dict[str, str], interval_store : dict[str, IntervalValue]): 
        return self.evaluate_naively(trace, var_store, interval_store, True)

    def __repr__(self):
        var_str = ", ".join(map(str, self.vars))
        return f"∃({var_str}). ({self.expression})"

class ForAll(Quantifier):
    def __init__(self, vars, expr):
        super().__init__(vars, expr)

    def evaluate(self, trace : Trace, var_store : dict[str, str], interval_store : dict[str, IntervalValue]): 
        return self.evaluate_naively(trace, var_store, interval_store, False)

    def __repr__(self):
        var_str = ", ".join(map(str, self.vars))
        return f"∀({var_str}). ({self.expression})"



class ActionQuantifier(Formula, ABC):
    @abstractmethod
    def __init__(self, action : "Action", expression : Formula):
        self.action = action
        # self.vars = vars if isinstance(vars, list) else [vars]
        self.expression = expression
    
        assert isinstance(action, Action), f"Expected Action, but got '{action}' of {type(action)}"

    # def get_possible_values(self, trace: Trace, store: dict[str, str], interval_store: dict[str, "IntervalValue"], var: Var) -> list[str]:
    #     if var in self.vars:
    #         return []
    #     else:
    #         return self.expr.get_possible_values(trace, store, interval_store, var)


    def get_possible_actions(self, trace : Trace, store : dict[str, str], interval_store : dict[str, "IntervalValue"], 
                            interval : "Interval") -> list["Action"]:
        return self.expression.get_possible_actions(trace, store, interval_store, interval)

    def evaluate_naively(self, trace : Trace, var_store : dict[str, str], interval_store : dict[str, IntervalValue],
                        short_circuit_on : bool):

            action = self.action
            possible_actions = trace.get_actions(action.get_type())

            for (interval_value, inputs, outputs) in possible_actions:

                #TODO: Mismatched number of inputs and outputs between formula and trace action
                if len(inputs) < len(action.input) or len(outputs) < len(action.output):
                    print(f"Warning: Possible action {action} has more inputs or outputs than action in trace: {interval_value, inputs, outputs}", file=sys.stderr)
                    continue

                new_interval_store = interval_store.copy()
                new_interval_store[action.interval.label] = interval_value

                new_var_store = var_store.copy()
                for (var, value) in zip(action.input, inputs):
                    if isinstance(var, Wildcard):
                        continue
                    assert var.label not in new_var_store, f"Variable {var.label} is already bound to: {new_var_store[var.label]}"
                    new_var_store[var.label] = value

                for (var, value) in zip(action.output, outputs):
                    if isinstance(var, Wildcard):
                        continue
                    assert var.label not in new_var_store, f"Variable {var.label} is already bound to: {new_var_store[var.label]}"
                    new_var_store[var.label] = value


                result = self.expression.evaluate(trace, new_var_store, new_interval_store)
                if result == short_circuit_on:
                    return short_circuit_on
            
            return not short_circuit_on


class ExistsAction(ActionQuantifier):
    def __init__(self, action : "Action", expression : Formula):
        super().__init__(action, expression)
    
    def evaluate(self, trace : Trace, var_store : dict[str, str], interval_store : dict[str, IntervalValue]): 
        return self.evaluate_naively(trace, var_store, interval_store, True)

    def __repr__(self):
        return f"∃({self.action}). ({self.expression})"

class ForAllAction(ActionQuantifier):
    def __init__(self, action : "Action", expression : Formula):
        super().__init__(action, expression)

    def evaluate(self, trace : Trace, var_store : dict[str, str], interval_store : dict[str, IntervalValue]): 
        return self.evaluate_naively(trace, var_store, interval_store, False)

    def __repr__(self):
        return f"∀({self.action}). ({self.expression})"

class Action(Formula):
    def __init__(self, action_type: ActionType, interval : Interval, inputs : Var | list[Var], outputs : Var | list[Var]):
        self.action_type = action_type
        self.interval = interval
        self.input = inputs if isinstance(inputs, list) else [inputs]
        self.output = outputs if isinstance(outputs, list) else [outputs]

        for var in self.input + self.output:
            assert isinstance(var, Var), f"Expected Var, but got '{var}' of {type(var)}. During initialization of Action {self}."


        assert isinstance(interval, Interval), f"Expected Interval, but got '{interval}' of {type(interval)}. During initialization of Action {self}."
    
    def get_type(self) -> ActionType:
        return self.action_type

    def evaluate(self, 
                 trace : Trace,
                 var_store : dict[str, str],
                 interval_store : dict[str, IntervalValue]) -> Any:

        action_interval = self.interval.evaluate(trace, var_store, interval_store)

        bound_input = [x.evaluate(trace, var_store, interval_store) for x in self.input]
        bound_output = [x.evaluate(trace, var_store, interval_store) for x in self.output]

        begin_event = BeginEvent(self.action_type, bound_input, None, None)
        end_event = EndEvent(self.action_type, bound_output, None, None)

        completed_begin_event = trace.complete_event(begin_event, action_interval.begin)

        if completed_begin_event is None:
            return False

        completed_end_event = trace.complete_event(end_event, action_interval.end)

        # NOTE:
        # Handle infinite intervals
        # end_event is not None iff t2 = "inf"
        if completed_end_event is None:
            return action_interval.end == float("inf")
            
        # TODO: 
        # Handle with infinite intervals
        # if t2 = "inf" then no end event should match its id
        # if evaluated_interval.end is not None:
    
        return (completed_end_event is not None) and completed_end_event.id == completed_begin_event.id

    def get_possible_values(self, trace : Trace, store : dict[str, str], interval_store : dict[str, IntervalValue],
                            var : Var) -> list[str]:
        possible_values = []
        # print(f"{var = } {self.input = } {self.output = } ")
        # print(f"{ trace = }")

        for (i, action_var) in enumerate(self.input):
            if action_var.label == var.label:
                possible_values.extend(trace.get_inputs(self.action_type, i))

        for (i, action_var) in enumerate(self.output):
            if action_var.label == var.label:
                possible_values.extend(trace.get_outputs(self.action_type, i))

        return possible_values

    def get_possible_actions(self, trace : Trace, store : dict[str, str], interval_store : dict[str, "IntervalValue"], 
                            interval : "Interval") -> list["Action"]:

        if self.interval.label == interval.label:
            return [self]
        else:
            return []

    def __repr__(self):
        type_str = self.action_type.name.lower()
        input_str = ", ".join(map(str, self.input))
        output_str = ", ".join(map(str, self.output))

        return f"{type_str}[{self.interval}] ({input_str}) -> ({output_str})"



class IntervalPredicate(Formula, ABC):
    @abstractmethod
    def __init__(self, left : Interval, right : Interval):
        assert isinstance(left, Interval), f"Expected Interval, but got '{left}' of {type(left)}"
        assert isinstance(right, Interval), f"Expected Interval, but got '{right}' of {type(right)}"

        self.left = left
        self.right = right

class Before(IntervalPredicate):
    def __init__(self, left : Interval, right : Interval):
        super().__init__(left, right)

    def evaluate(self, trace : Trace, store, interval_store) -> Any:
        left = self.left.evaluate(trace, store, interval_store)
        right = self.right.evaluate(trace, store, interval_store)
        return left.end < right.begin

    def __repr__(self):
        return f"Before({self.left}, {self.right})"

class Meets(IntervalPredicate):
    def __init__(self, left : Interval, right : Interval):
        super().__init__(left, right)

    def evaluate(self, trace : Trace, store, interval_store) -> Any:
        left = self.left.evaluate(trace, store, interval_store)
        right = self.right.evaluate(trace, store, interval_store)
        return left.end == right.begin

    def __repr__(self):
        return f"Meets({self.left}, {self.right})"

class Overlaps(IntervalPredicate):
    def __init__(self, left : Interval, right : Interval):
        super().__init__(left, right)

    def evaluate(self, trace : Trace, store, interval_store) -> Any:
        left = self.left.evaluate(trace, store, interval_store)
        right = self.right.evaluate(trace, store, interval_store)
        return left.begin < right.begin < left.end < right.end

    def __repr__(self):
        return f"Overlaps({self.left}, {self.right})"

class Starts(IntervalPredicate):
    def __init__(self, left : Interval, right : Interval):
        super().__init__(left, right)

    def evaluate(self, trace : Trace, store, interval_store) -> Any:
        left = self.left.evaluate(trace, store, interval_store)
        right = self.right.evaluate(trace, store, interval_store)
        return left.begin == right.begin and left.end < right.end

    def __repr__(self):
        return f"Starts({self.left}, {self.right})"

class During(IntervalPredicate):
    def __init__(self, left : Interval, right : Interval):
        super().__init__(left, right)

    def evaluate(self, trace : Trace, store, interval_store) -> Any:
        left = self.left.evaluate(trace, store, interval_store)
        right = self.right.evaluate(trace, store, interval_store)
        return right.begin < left.begin and left.end < right.end

    def __repr__(self):
        return f"During({self.left}, {self.right})"

class Finishes(IntervalPredicate):
    def __init__(self, left : Interval, right : Interval):
        super().__init__(left, right)

    def evaluate(self, trace : Trace, store, interval_store) -> Any:
        left = self.left.evaluate(trace, store, interval_store)
        right = self.right.evaluate(trace, store, interval_store)
        return left.end == right.end and right.begin < left.begin

    def __repr__(self):
        return f"Finishes({self.left}, {self.right})"

class Equals(IntervalPredicate):
    def __init__(self, left : Interval, right : Interval):
        super().__init__(left, right)

    def evaluate(self, trace : Trace, store, interval_store) -> Any:
        left = self.left.evaluate(trace, store, interval_store)
        right = self.right.evaluate(trace, store, interval_store)
        return left == right

    def __repr__(self):
        return f"Equals({self.left}, {self.right})"

class Constant(Formula):
    def __init__(self, label : str):
        self.label = label
    
    def evaluate(self, _trace : Trace, _store, _interval_store) -> Any:
        return self.label

    def __repr__(self):
        return f"Constant({self.label})"

class Wildcard(Var):
    def __init__(self):
        super().__init__("-")

    def evaluate(self, _trace : Trace, _store, _interval_store) -> Any:
        raise ValueError("Wildcard should not be evaluated directly")

    def __repr__(self):
        return f"Wildcard"
