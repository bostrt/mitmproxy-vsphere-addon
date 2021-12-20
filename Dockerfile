FROM docker.io/mitmproxy/mitmproxy

WORKDIR /addon

COPY . .

RUN pip install -r requirements.txt

ENTRYPOINT ["mitmweb", "--listen-host", "0.0.0.0", "--web-host", "0.0.0.0", "--no-web-open-browser", "-k", "-s", "dump_permission_failure.py", "--set", "vs_dump_flows=/tmp/dumpfile.out"]
