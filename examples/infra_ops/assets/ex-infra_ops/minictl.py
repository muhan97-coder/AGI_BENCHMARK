#!/usr/bin/env python3
"""minictl -- a miniature, docker-free service runtime (SEALED, do not modify).

This stands in for ``docker compose`` at 1/1000 scale so the infra_ops grading
shape can be taught without pulling a single container image. It reads a stack
file, resolves every image against a *pinned local registry*, starts each
service as a local process, publishes host ports and mounts host directories.

The layered failure modes of the scored infra_ops cards are all reproduced:

  stack file does not parse        -> ``config`` fails
  floating / unpinned image tag    -> visible in ``config`` output
  image tag not in the registry    -> ``up`` fails (stands in for an unpullable tag)
  service config syntax error      -> ``conftest`` fails (stands in for ``nginx -t``)
  published port mismatch          -> ``port`` prints nothing
  content directory not mounted    -> web service refuses to start

Stack file (JSON; keys starting with "//" are comments)::

    {"services": {"web": {"image": "miniweb:1.25.4",
                          "config": "./site.conf",
                          "ports": ["8391:80"],
                          "volumes": ["./html:/usr/share/site:ro"],
                          "depends_on": ["cache"]},
                  "cache": {"image": "minicache:7.2.4"}}}

Service config file (nginx-flavoured; every directive ends with ``;``)::

    server {
      listen 80;
      root /usr/share/site;
      index index.html;
    }

Subcommands
  config [-q]          parse + validate the stack file   (~ docker compose config)
  conftest SERVICE     validate one service's config file (~ nginx -t)
  up                   start every service                (~ docker compose up -d)
  ps --status running --services                          (~ docker compose ps)
  port SERVICE CPORT   print the host address publishing CPORT
  exec SERVICE CMD...  run a client command inside a service (cache-cli ping)
  down                 stop everything and drop the state file
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import socketserver
import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.join(HERE, ".minictl")
# The only "images" this host can run. Anything else is an unpullable tag.
REGISTRY = {"miniweb:1.25.4": "web", "minicache:7.2.4": "cache"}
CONF_KEYS = ("listen", "root", "index")
START_TIMEOUT_S = 5.0


class StackError(Exception):
    """The stack file is malformed (never a runtime failure)."""


class ConfError(Exception):
    """A service config file is malformed."""


# --------------------------------------------------------------------------- stack


def _split_mapping(text, what, parts):
    bits = str(text).split(":")
    if len(bits) < parts:
        raise StackError("%s %r must look like %s" % (what, text, "A:B" if parts == 2 else "A:B[:ro]"))
    return bits


def load_stack(path):
    """Parse and validate the stack file. Executes nothing."""
    try:
        with open(path) as fh:
            raw = json.load(fh)
    except FileNotFoundError:
        raise StackError("stack file not found: %s" % path)
    except ValueError as err:
        raise StackError("stack file is not valid JSON: %s" % err)
    if not isinstance(raw, dict) or not isinstance(raw.get("services"), dict) or not raw["services"]:
        raise StackError("stack file must define a non-empty 'services' object")
    services = {}
    for name, svc in raw["services"].items():
        if name.startswith("//"):
            continue
        if not isinstance(svc, dict):
            raise StackError("service %s: must be an object" % name)
        image = svc.get("image")
        if not isinstance(image, str) or ":" not in image:
            raise StackError("service %s: 'image' must be a name:tag string" % name)
        ports = []
        for spec in svc.get("ports") or []:
            host, container = _split_mapping(spec, "port mapping", 2)[:2]
            try:
                ports.append((int(host), int(container)))
            except ValueError:
                raise StackError("service %s: port mapping %r is not numeric" % (name, spec))
        volumes = []
        for spec in svc.get("volumes") or []:
            bits = _split_mapping(spec, "volume mapping", 2)
            volumes.append((bits[0], bits[1]))
        services[name] = {
            "image": image, "ports": ports, "volumes": volumes,
            "config": svc.get("config"), "depends_on": list(svc.get("depends_on") or []),
        }
    for name, svc in services.items():
        for dep in svc["depends_on"]:
            if dep not in services:
                raise StackError("service %s: depends_on unknown service %r" % (name, dep))
    return services


def start_order(services):
    ordered, seen = [], set()

    def visit(name, trail):
        if name in ordered:
            return
        if name in trail:
            raise StackError("dependency cycle: %s" % " -> ".join(list(trail) + [name]))
        for dep in services[name]["depends_on"]:
            visit(dep, trail | {name})
        if name not in seen:
            seen.add(name)
            ordered.append(name)

    for name in services:
        visit(name, frozenset())
    return ordered


def parse_conf(path):
    """Parse a service config file. Raises ConfError with a line number."""
    try:
        with open(path) as fh:
            lines = fh.read().splitlines()
    except FileNotFoundError:
        raise ConfError("config file not found: %s" % path)
    conf, depth, seen_block = {}, 0, False
    for lineno, raw in enumerate(lines, 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if line.endswith("{"):
            head = line[:-1].strip()
            if head != "server":
                raise ConfError("line %d: unknown block %r (expected 'server')" % (lineno, head))
            depth += 1
            seen_block = True
            continue
        if line == "}":
            depth -= 1
            if depth < 0:
                raise ConfError("line %d: unbalanced '}'" % lineno)
            continue
        if depth != 1:
            raise ConfError("line %d: directive %r outside the server block" % (lineno, line))
        if not line.endswith(";"):
            raise ConfError("line %d: directive %r is missing its terminating ';'" % (lineno, line))
        bits = line[:-1].split()
        if len(bits) != 2:
            raise ConfError("line %d: directive %r must be 'key value;'" % (lineno, line))
        key, value = bits
        if key not in CONF_KEYS:
            raise ConfError("line %d: unknown directive %r (known: %s)"
                            % (lineno, key, ", ".join(CONF_KEYS)))
        conf[key] = value
    if depth != 0:
        raise ConfError("unbalanced '{' -- the server block is never closed")
    if not seen_block:
        raise ConfError("no server block found")
    missing = [k for k in CONF_KEYS if k not in conf]
    if missing:
        raise ConfError("server block is missing directive(s): %s" % ", ".join(missing))
    try:
        conf["listen"] = int(conf["listen"])
    except ValueError:
        raise ConfError("listen %r is not a port number" % conf["listen"])
    return conf


# --------------------------------------------------------------------------- state


def state_path(project):
    return os.path.join(STATE_DIR, project + ".json")


def read_state(project):
    try:
        with open(state_path(project)) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {"project": project, "services": {}}


def write_state(project, state):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(state_path(project), "w") as fh:
        json.dump(state, fh, indent=1)


def alive(pid):
    if not pid:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def accepts(port):
    try:
        with socket.create_connection(("127.0.0.1", int(port)), timeout=1.0):
            return True
    except OSError:
        return False


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


# --------------------------------------------------------------------------- servers


class _CacheHandler(socketserver.StreamRequestHandler):
    def handle(self):
        for raw in self.rfile:
            word = raw.strip().upper()
            if word == b"PING":
                self.wfile.write(b"PONG\n")
            elif word:
                self.wfile.write(b"ERR unknown command\n")
            self.wfile.flush()


class _WebHandler(BaseHTTPRequestHandler):
    """Serves the mounted directory. Deliberately tiny and version-portable."""

    server_version = "miniweb/1.25.4"
    directory = "."
    index = "index.html"

    def do_GET(self):
        rel = self.path.split("?", 1)[0].lstrip("/")
        if rel in ("", "/") or rel.endswith("/"):
            rel += self.index
        root = os.path.abspath(self.directory)
        full = os.path.normpath(os.path.join(root, rel))
        if not full.startswith(root + os.sep) or not os.path.isfile(full):
            self.send_error(404, "Not Found")
            return
        with open(full, "rb") as fh:
            body = fh.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *a):
        sys.stderr.write("[miniweb] " + (fmt % a) + "\n")


def serve(kind, port, directory, index):
    if kind == "web":
        handler = type("WebHandler", (_WebHandler,),
                       {"directory": os.path.abspath(directory), "index": index})
        ThreadingHTTPServer(("127.0.0.1", port), handler).serve_forever()
    elif kind == "cache":
        socketserver.ThreadingTCPServer.allow_reuse_address = True
        socketserver.ThreadingTCPServer(("127.0.0.1", port), _CacheHandler).serve_forever()
    else:
        raise SystemExit("unknown service kind: %s" % kind)


# --------------------------------------------------------------------------- commands


def resolve_runtime(name, svc, stack_dir):
    """Work out how to start one service. Raises StackError with the reason."""
    kind = REGISTRY.get(svc["image"])
    if kind is None:
        raise StackError("service %s: image %r not found in the pinned local registry "
                         "(available: %s)" % (name, svc["image"], ", ".join(sorted(REGISTRY))))
    if kind == "web":
        if not svc["config"]:
            raise StackError("service %s: web image needs a 'config' file" % name)
        conf = parse_conf(os.path.join(stack_dir, svc["config"]))
        host_ports = [h for h, c in svc["ports"] if c == conf["listen"]]
        if not host_ports:
            raise StackError("service %s: nothing publishes the container port it listens on "
                             "(listen %s, ports %s)"
                             % (name, conf["listen"], svc["ports"] or "none"))
        mounted = [h for h, c in svc["volumes"] if c == conf["root"]]
        if not mounted:
            raise StackError("service %s: no volume mounts the config root %r "
                             "(mounts: %s)" % (name, conf["root"], svc["volumes"] or "none"))
        directory = os.path.abspath(os.path.join(stack_dir, mounted[0]))
        if not os.path.isdir(directory):
            raise StackError("service %s: mount source %r does not exist" % (name, mounted[0]))
        return {"kind": kind, "host_port": host_ports[0], "container_port": conf["listen"],
                "directory": directory, "index": conf["index"]}
    container_port = 6379
    host_ports = [h for h, c in svc["ports"] if c == container_port]
    return {"kind": kind, "host_port": host_ports[0] if host_ports else free_port(),
            "container_port": container_port, "directory": None, "index": None}


def cmd_config(args):
    try:
        services = load_stack(args.stack)
    except (StackError, ConfError) as err:
        print("stack invalid: %s" % err, file=sys.stderr)
        return 1
    if not args.quiet:
        print("services:")
        for name in start_order(services):
            svc = services[name]
            print("  %s:" % name)
            print("    image: %s" % svc["image"])
            for host, container in svc["ports"]:
                print("    published: %d->%d" % (host, container))
            for host, container in svc["volumes"]:
                print("    mount: %s->%s" % (host, container))
    return 0


def cmd_conftest(args):
    try:
        services = load_stack(args.stack)
        svc = services[args.service]
    except StackError as err:
        print("stack invalid: %s" % err, file=sys.stderr)
        return 1
    except KeyError:
        print("no such service: %s" % args.service, file=sys.stderr)
        return 1
    if not svc["config"]:
        print("service %s has no config file" % args.service, file=sys.stderr)
        return 1
    path = os.path.join(os.path.dirname(os.path.abspath(args.stack)), svc["config"])
    try:
        conf = parse_conf(path)
    except ConfError as err:
        print("conftest %s FAILED: %s" % (args.service, err), file=sys.stderr)
        return 1
    print("conftest %s ok: %s" % (args.service, json.dumps(conf, sort_keys=True)))
    return 0


def cmd_up(args):
    stack_dir = os.path.dirname(os.path.abspath(args.stack))
    try:
        services = load_stack(args.stack)
        order = start_order(services)
    except StackError as err:
        print("stack invalid: %s" % err, file=sys.stderr)
        return 1
    cmd_down(args)
    os.makedirs(STATE_DIR, exist_ok=True)
    state = {"project": args.project, "stack": args.stack, "services": {}}
    failures = 0
    for name in order:
        entry = {"image": services[name]["image"], "status": "failed",
                 "pid": None, "host_port": None, "container_port": None, "error": None}
        try:
            plan = resolve_runtime(name, services[name], stack_dir)
        except (StackError, ConfError) as err:
            entry["error"] = str(err)
            print(str(err), file=sys.stderr)
            state["services"][name] = entry
            failures += 1
            continue
        entry.update(host_port=plan["host_port"], container_port=plan["container_port"])
        log_path = os.path.join(STATE_DIR, "%s-%s.log" % (args.project, name))
        argv = [sys.executable, os.path.abspath(__file__), "__serve", "--kind", plan["kind"],
                "--port", str(plan["host_port"])]
        if plan["directory"]:
            argv += ["--dir", plan["directory"], "--index", plan["index"]]
        with open(log_path, "wb") as log:
            proc = subprocess.Popen(argv, stdout=log, stderr=log, start_new_session=True)
        entry["pid"] = proc.pid
        entry["log"] = os.path.relpath(log_path, HERE)
        deadline = time.time() + START_TIMEOUT_S
        while time.time() < deadline:
            if accepts(plan["host_port"]):
                entry["status"] = "running"
                break
            if proc.poll() is not None:
                break
            time.sleep(0.1)
        if entry["status"] != "running":
            entry["error"] = "service did not accept connections on port %d (see %s)" % (
                plan["host_port"], entry["log"])
            print("%s: %s" % (name, entry["error"]), file=sys.stderr)
            failures += 1
        else:
            print("%s: running (image %s, published %d->%d)"
                  % (name, entry["image"], entry["host_port"], entry["container_port"]))
        state["services"][name] = entry
    write_state(args.project, state)
    return 1 if failures else 0


def cmd_ps(args):
    state = read_state(args.project)
    for name, entry in state["services"].items():
        running = entry.get("status") == "running" and alive(entry.get("pid")) \
            and accepts(entry.get("host_port"))
        if args.status == "running" and not running:
            continue
        print(name if args.services else "%-8s %-18s %s" % (
            name, entry.get("image"), "running" if running else "exited"))
    return 0


def cmd_port(args):
    state = read_state(args.project)
    entry = state["services"].get(args.service)
    if not entry or entry.get("status") != "running":
        return 1
    if int(entry.get("container_port") or -1) != int(args.container_port):
        return 1
    print("127.0.0.1:%d" % entry["host_port"])
    return 0


def cmd_exec(args):
    state = read_state(args.project)
    entry = state["services"].get(args.service)
    if not entry or entry.get("status") != "running":
        print("service %s is not running" % args.service, file=sys.stderr)
        return 1
    argv = list(args.argv)
    if argv[:1] != ["cache-cli"]:
        print("this runtime only ships the cache-cli client", file=sys.stderr)
        return 1
    try:
        with socket.create_connection(("127.0.0.1", entry["host_port"]), timeout=2.0) as sock:
            sock.sendall((" ".join(argv[1:]) + "\n").encode())
            reply = sock.makefile("rb").readline().decode().strip()
    except OSError as err:
        print("cache-cli: %s" % err, file=sys.stderr)
        return 1
    print(reply)
    return 0


def cmd_down(args):
    state = read_state(args.project)
    for entry in state.get("services", {}).values():
        pid = entry.get("pid")
        if alive(pid):
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                pass
    for entry in state.get("services", {}).values():
        deadline = time.time() + 3.0
        while alive(entry.get("pid")) and time.time() < deadline:
            time.sleep(0.05)
    try:
        os.remove(state_path(args.project))
    except OSError:
        pass
    return 0


def main(argv):
    ap = argparse.ArgumentParser(prog="minictl", description=__doc__.splitlines()[0])
    ap.add_argument("--project", default="minictl")
    ap.add_argument("--stack", default=os.path.join(HERE, "stack", "stack.json"))
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("config"); p.add_argument("-q", "--quiet", action="store_true")
    p.set_defaults(func=cmd_config)
    p = sub.add_parser("conftest"); p.add_argument("service"); p.set_defaults(func=cmd_conftest)
    sub.add_parser("up").set_defaults(func=cmd_up)
    p = sub.add_parser("ps")
    p.add_argument("--status", default=None); p.add_argument("--services", action="store_true")
    p.set_defaults(func=cmd_ps)
    p = sub.add_parser("port"); p.add_argument("service"); p.add_argument("container_port")
    p.set_defaults(func=cmd_port)
    p = sub.add_parser("exec"); p.add_argument("service"); p.add_argument("argv", nargs="+")
    p.set_defaults(func=cmd_exec)
    sub.add_parser("down").set_defaults(func=cmd_down)
    p = sub.add_parser("__serve")
    p.add_argument("--kind", required=True); p.add_argument("--port", type=int, required=True)
    p.add_argument("--dir"); p.add_argument("--index", default="index.html")
    p.set_defaults(func=lambda a: serve(a.kind, a.port, a.dir, a.index))
    args = ap.parse_args(argv)
    return args.func(args) or 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
