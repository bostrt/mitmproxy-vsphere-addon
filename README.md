## Read flows from a file
```shell
$ mitmproxy -s dump-permission-failure.py \
  --set console_eventlog_verbosity=debug \
  --set vs_dump_flows=dumpfile.out \
  -r ./myflows.out
```

## Run MITMProxy live with script
```shell
$ mitmproxy -s dump-permission-failure.py \
  --set console_eventlog_verbosity=debug \
  --set vs_dump_flows=dumpfile.out
```