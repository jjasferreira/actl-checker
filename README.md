### Parsing and Evaluation

#### Parse formula:

- the formula can be provided as a string or a file path

```cmd
python parse_formula.py -f formula.actl [-d]
python parse_formula.py --formula formula.actl [--debug]
```

#### Parse log:

- the log can be provided as a string or a file path

```cmd
python parse_log.py -l log.log [-d] [-n] [-i]
python parse_log.py --log log.log [--debug] [--num-lines] [--ignore-non-operations]
```

#### Parse formula and log and evaluate formula on log:

- both the formula and the log can be provided as strings or file paths

```cmd
python main.py -f formula.actl -l log.log [-d] [-n]
python main.py --formula formula.actl --log log.log [--debug] [--num-lines]
```
