# Usage
## Read flows from an MITMProxy dump file
```shell
$ mitmproxy -s dump_permission_failure.py \
  --set vs_dump_flows=dumpfile.out \
  --no-server
  -r ./myflows.out
```

## Run MITMProxy live
```shell
$ mitmproxy -s dump_permission_failure.py \
  --set console_eventlog_verbosity=debug \
  --set vs_dump_flows=dumpfile.out
```

# Testing and Dev

## Run unit tests
```shell
python test.py
```

## Debug tips
- Read flows from file: `--rfile/-r <file>`
- Probably use: `--no-server`
- Increase event log verbosity using: `--set console_eventlog_verbosity=debug`
- See MITMProxy event log using: `Shift+E`

