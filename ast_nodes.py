from abc import ABC, abstractmethod
from collections import defaultdict
from enum import Enum
from typing import Any, TypeAlias

import sys

IntervalCollection : TypeAlias = dict["ActionType", list["IntervalValue"]]
VarCollection : TypeAlias = dict[tuple["ActionType", int], list[str]]


class ActionType(Enum):
    Lookup = 1
    Store = 2
    FindNode = 3
    Join = 4
    Leave = 5
    Fail = 6
    Ideal = 7
    Stable = 8
    ReadOnly = 9
    Member = 10
    Responsible = 11

class Event(ABC):
    @abstractmethod
    def __init__(self, action_type : ActionType, values, id):
        self.action_type = action_type
        self.values = values if isinstance(values, list) else [values]
        self.id = id

    def matches(self, other):
        if not isinstance(other, Event):
            return False
        else:
            return self.action_type == other.action_type and self.values == other.values

class BeginEvent(Event):
    def __init__(self, action_type : ActionType, values : list[str], id):
        super().__init__(action_type, values, id)

    def __repr__(self):
        return f"BeginEvent({self.id}, {self.action_type}, {self.values})"

class EndEvent(Event):
    def __init__(self, action_type : ActionType, values, id ):
        super().__init__(action_type, values, id)

    def __repr__(self):
        return f"EndEvent({self.id}, {self.action_type}, {self.values})"

class Trace:
    def __init__(self, events : list[Event] | None = None, 
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

    def append_event(self, event : Event):
        self.events.append(event)

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
    def complete_event(self, event : Event, t : int) -> None | Event: 
        assert event.id is None

        if t < 0 or t >= len(self.events):
            return None

        candidate = self.events[t]
        if candidate.matches(event):
            return candidate
        else:
            return None

    def __repr__(self):
        return  f"Trace(Events: {self.events};\nInputs: {self.inputs};\nOutputs: {self.outputs};\nIntervals: {self.intervals})"


class Formula(ABC):
    @abstractmethod
    def evaluate(self, trace : Trace, store : dict[str, str], interval_store : "dict[str, IntervalValue]") -> Any:
        pass

    def get_possible_values(self, trace : Trace, store : dict[str, str], interval_store : dict[str, "IntervalValue"], 
                            var : "Var") -> list[str]:
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
    #TODO: explicit types in init, int or datetime
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

class Interval(Var):
    def __init__(self, label):
        self.label = label

    def evaluate(self, _trace : Trace, _store, interval_store) -> IntervalValue:
        if self.label not in interval_store:
            raise ValueError(f"Interval {self.label} not found in interval store")
        return interval_store[self.label]

    def __repr__(self):
        return f"{self.label}"



class UnaryExpr(Formula, ABC):
    @abstractmethod
    def __init__(self, expr):
        self.expr = expr

    def get_possible_values(self, trace : Trace, store : dict[str, str], interval_store : dict[str, IntervalValue],
                            target_var : str) -> list[str]:
        return self.expr.get_possible_values(trace, store, interval_store, target_var)

class Not(UnaryExpr):
    def __init__(self, expr):
        super().__init__(expr)

    def evaluate(self, trace : Trace, store, interval_store):
        return not self.expr.evaluate(trace, store, interval_store)

    def __repr__(self):
        return f"¬({self.expr})"

class BinaryExpr(Formula, ABC):
    @abstractmethod
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def get_possible_values(self, trace : Trace, store : dict[str, str], interval_store : dict[str, IntervalValue],
                            target_var : str) -> list[str]:
        possible_values = self.left.get_possible_values(trace, store, interval_store, target_var)
        possible_values.extend(self.right.get_possible_values(trace, store, interval_store, target_var))
        return possible_values

class Equal(BinaryExpr):
    def __init__(self, left, right):
        super().__init__(left, right)

    def evaluate(self, trace : Trace, store, interval_store) -> Any:
        return self.left.evaluate(trace, store, interval_store) == self.right.evaluate(trace, store, interval_store)

    def __repr__(self):
        return f"({self.left} == {self.right})"

class And(BinaryExpr):
    def __init__(self, left, right):
        super().__init__(left, right)
    
    def evaluate(self, trace : Trace, store, interval_store) -> Any:
        return self.left.evaluate(trace, store, interval_store) and self.right.evaluate(trace, store, interval_store)

    def __repr__(self):
        return f"({self.left} ∧ {self.right})"

class Or(BinaryExpr):
    def __init__(self, left, right):
        super().__init__(left, right)

    def evaluate(self, trace : Trace, store, interval_store) -> Any:
        return self.left.evaluate(trace, store, interval_store) or self.right.evaluate(trace, store, interval_store)

    def __repr__(self):
        return f"({self.left} v {self.right})"

class Implies(BinaryExpr):
    def __init__(self, left, right):
        super().__init__(left, right)

    def evaluate(self, trace : Trace, store, interval_store) -> Any:
        return not self.left.evaluate(trace, store, interval_store) or self.right.evaluate(trace, store, interval_store)

    def __repr__(self):
        return f"({self.left} => {self.right})"


class Quantifier(Formula, ABC):
    @abstractmethod
    def __init__(self, vars : Var | list[Var], expr : Formula):
        self.vars = vars if isinstance(vars, list) else [vars]
        self.expr = expr

    def get_possible_values(self, trace: Trace, store: dict[str, str], interval_store: dict[str, "IntervalValue"], var: Var) -> list[str]:
        if var in self.vars:
            return []
        else:
            return self.expr.get_possible_values(trace, store, interval_store, var)


    def evaluate_naively(self, trace : Trace, var_store : dict[str, str], interval_store : dict[str, IntervalValue],
                        short_circuit_on : bool):
        return self.evaluate_naively_recursive(trace, var_store, interval_store, short_circuit_on, 0)


    def evaluate_naively_recursive(self, trace : Trace, var_store : dict[str, str], interval_store : dict[str, IntervalValue],
                     short_circuit_on : bool, var_idx : int) -> bool:

        if var_idx >= len(self.vars):
            result =  self.expr.evaluate(trace, var_store, interval_store)
            # print(f"Base case Evaluating: {self.expr} with {var_store} -> {result}")
            return result

        else:

            #TODO: check if var is not bound in current store?
            var = self.vars[var_idx]

            possible_values = self.expr.get_possible_values(trace, var_store, interval_store, var)
    
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

            if isinstance(var, Var):
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
            else: 
                assert isinstance(var, Interval), f"Unexpected quantifiable type: {type(var)}"
                
                raise NotImplementedError("Interval quantification not implemented")

class Exists(Quantifier):
    def __init__(self, vars, expr):
        super().__init__(vars, expr)
    
    def evaluate(self, trace : Trace, var_store : dict[str, str], interval_store : dict[str, IntervalValue]): 
        return self.evaluate_naively(trace, var_store, interval_store, True)

    def __repr__(self):
        var_str = ", ".join(map(str, self.vars))
        return f"∃({var_str}). ({self.expr})"

class ForAll(Quantifier):

    def __init__(self, vars, expr):
        super().__init__(vars, expr)

    def evaluate(self, trace : Trace, var_store : dict[str, str], interval_store : dict[str, IntervalValue]): 
        return self.evaluate_naively(trace, var_store, interval_store, False)

    def __repr__(self):
        var_str = ", ".join(map(str, self.vars))
        return f"∀({var_str}). ({self.expr})"




class Action(Formula):
    def __init__(self, action_type: ActionType, interval : Interval, inputs : Var | list[Var], outputs : Var | list[Var]):
        self.action_type = action_type
        self.interval = interval
        self.input = inputs if isinstance(inputs, list) else [inputs]
        self.output = outputs if isinstance(outputs, list) else [outputs]

    def evaluate(self, 
                 trace : Trace,
                 var_store : dict[str, str],
                 interval_store : dict[str, IntervalValue]) -> Any:

        action_interval = self.interval.evaluate(trace, var_store, interval_store)

        bound_input = [x.evaluate(trace, var_store, interval_store) for x in self.input]
        bound_output = [x.evaluate(trace, var_store, interval_store) for x in self.output]

        begin_event = BeginEvent(self.action_type, bound_input, None)
        end_event = EndEvent(self.action_type, bound_output, None)

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

    def __repr__(self):
        type_str = self.action_type.name.lower()
        input_str = ", ".join(map(str, self.input))
        output_str = ", ".join(map(str, self.output))

        return f"{type_str}[{self.interval}] ({input_str}) -> ({output_str})"



class IntervalPredicate(Formula, ABC):
    @abstractmethod
    def __init__(self, left : Interval, right : Interval):
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
    def __init__(self, left, right):
        super().__init__(left, right)

    def evaluate(self, trace : Trace, store, interval_store) -> Any:
        left = self.left.evaluate(trace, store, interval_store)
        right = self.right.evaluate(trace, store, interval_store)
        return left.end == right.begin

    def __repr__(self):
        return f"Meets({self.left}, {self.right})"

class Overlaps(IntervalPredicate):
    def __init__(self, left, right):
        super().__init__(left, right)

    def evaluate(self, trace : Trace, store, interval_store) -> Any:
        left = self.left.evaluate(trace, store, interval_store)
        right = self.right.evaluate(trace, store, interval_store)
        return left.begin < right.begin < left.end < right.end

    def __repr__(self):
        return f"Overlaps({self.left}, {self.right})"

class Starts(IntervalPredicate):
    def __init__(self, left, right):
        super().__init__(left, right)

    def evaluate(self, trace : Trace, store, interval_store) -> Any:
        left = self.left.evaluate(trace, store, interval_store)
        right = self.right.evaluate(trace, store, interval_store)
        return left.begin == right.begin and left.end < right.end

    def __repr__(self):
        return f"Starts({self.left}, {self.right})"

class During(IntervalPredicate):
    def __init__(self, left, right):
        super().__init__(left, right)

    def evaluate(self, trace : Trace, store, interval_store) -> Any:
        left = self.left.evaluate(trace, store, interval_store)
        right = self.right.evaluate(trace, store, interval_store)
        return right.begin < left.begin and left.end < right.end

    def __repr__(self):
        return f"During({self.left}, {self.right})"

class Finishes(IntervalPredicate):
    def __init__(self, left, right):
        super().__init__(left, right)

    def evaluate(self, trace : Trace, store, interval_store) -> Any:
        left = self.left.evaluate(trace, store, interval_store)
        right = self.right.evaluate(trace, store, interval_store)
        return left.end == right.end and right.begin < left.begin

    def __repr__(self):
        return f"Finishes({self.left}, {self.right})"

class Equals(IntervalPredicate):
    def __init__(self, left, right):
        super().__init__(left, right)

    def evaluate(self, trace : Trace, store, interval_store) -> Any:
        left = self.left.evaluate(trace, store, interval_store)
        right = self.right.evaluate(trace, store, interval_store)
        return left == right

    def __repr__(self):
        return f"Equals({self.left}, {self.right})"
