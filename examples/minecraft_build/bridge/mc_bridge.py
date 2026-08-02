"""Thin Python client for mc_bridge.js.

Wraps the Node bridge as a subprocess and speaks its line-delimited JSON-RPC
protocol. One method per primitive, one round trip per call, no added logic:
if the bridge returns an error frame this raises BridgeError carrying the same
code/message/detail. Deciding what to do about that error is the agent's job.

    from mc_bridge import McBridge

    with McBridge() as mc:
        mc.connect("127.0.0.1", 25565, "builder_a")
        print(mc.get_position())
        mc.place_block(0, -60, 0, "stone_bricks")
        print(mc.read_region(0, -60, 0, 0, -60, 2))
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any, Optional

BRIDGE_JS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mc_bridge.js")


class BridgeError(RuntimeError):
    """An error frame returned by the bridge (or a dead bridge process)."""

    def __init__(self, code: str, message: str, detail: Optional[dict] = None):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.detail = detail or {}


class McBridge:
    """Owns one `node mc_bridge.js` subprocess, which owns one bot."""

    def __init__(self, node: str = "node", script: str = BRIDGE_JS, stderr=None):
        self._next_id = 0
        script = os.path.abspath(script)  # a bare filename would give cwd=""
        self._proc = subprocess.Popen(
            [node, script],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=stderr if stderr is not None else sys.stderr,
            text=True,
            bufsize=1,
            cwd=os.path.dirname(script),
        )

    # -- transport ---------------------------------------------------------
    def _call(self, method: str, **params: Any) -> Any:
        if self._proc.poll() is not None:
            raise BridgeError("BRIDGE_DEAD", f"bridge exited with code {self._proc.returncode}")
        if self._proc.stdin is None or self._proc.stdin.closed:
            raise BridgeError("BRIDGE_DEAD", "bridge stdin is closed; this client was already closed")
        self._next_id += 1
        req_id = self._next_id
        self._proc.stdin.write(json.dumps({"id": req_id, "method": method, "params": params}) + "\n")
        self._proc.stdin.flush()

        line = self._proc.stdout.readline()
        if not line:
            raise BridgeError("BRIDGE_DEAD", f"bridge closed stdout during {method}")
        frame = json.loads(line)
        if frame.get("id") != req_id:
            raise BridgeError("PROTOCOL_DESYNC", f"expected id {req_id}, got {frame.get('id')}", frame)
        if not frame.get("ok"):
            err = frame.get("error", {})
            raise BridgeError(err.get("code", "UNKNOWN"), err.get("message", ""), err.get("detail"))
        return frame.get("result")

    # -- primitives --------------------------------------------------------
    def connect(self, host: str, port: int, username: str, version: str = "1.19.2", timeout_ms: int = 60000) -> dict:
        return self._call("connect", host=host, port=port, username=username, version=version, timeout_ms=timeout_ms)

    def disconnect(self) -> dict:
        return self._call("disconnect")

    def get_position(self) -> dict:
        return self._call("get_position")

    def get_inventory(self) -> dict:
        return self._call("get_inventory")

    def read_region(self, x1: int, y1: int, z1: int, x2: int, y2: int, z2: int) -> dict:
        return self._call("read_region", x1=x1, y1=y1, z1=z1, x2=x2, y2=y2, z2=z2)

    def place_block(
        self,
        x: int,
        y: int,
        z: int,
        block_name: str,
        face: Optional[dict] = None,
        look: Optional[dict] = None,
    ) -> dict:
        """Place `block_name` at (x, y, z).

        `face` is the unit axis vector of the neighbour face to click
        (e.g. {"x": 0, "y": 1, "z": 0} to click the top of the block below) and
        `look` is the world point to face first. Both determine a directional
        block's axis/facing, so both are yours to choose; omit them and the
        bridge clicks the first solid neighbour in a fixed, documented order.
        """
        params: dict = {"x": x, "y": y, "z": z, "blockName": block_name}
        if face is not None:
            params["face"] = face
        if look is not None:
            params["look"] = look
        return self._call("place_block", **params)

    def withdraw_from_chest(self, x: int, y: int, z: int, item_name: str, count: int) -> dict:
        return self._call("withdraw_from_chest", x=x, y=y, z=z, itemName=item_name, count=count)

    # -- lifecycle ---------------------------------------------------------
    def close(self) -> None:
        """Close stdin so the bridge quits its bot and exits; kill it if it won't.

        Always reaps the child: a killed process that is never waited on stays
        a zombie for the life of the interpreter.
        """
        if self._proc.poll() is None:
            try:
                if self._proc.stdin is not None and not self._proc.stdin.closed:
                    self._proc.stdin.close()
                self._proc.wait(timeout=15)
            except Exception:
                self._proc.kill()
                self._proc.wait()

    def __enter__(self) -> "McBridge":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
