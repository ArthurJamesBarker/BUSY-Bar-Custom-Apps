"""Read physical BUSY Bar controls from the release-firmware status stream."""

from __future__ import annotations

import time
from collections.abc import Callable, Iterator

from websocket import WebSocketTimeoutException, create_connection

BTN_OK, BTN_BACK, BTN_START = 0, 1, 2
ACT_RELEASE = 1
SW_APPS = 3


def _read_varint(data: bytes, offset: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while offset < len(data):
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, offset
        shift += 7
        if shift > 70:
            break
    raise ValueError("Invalid protobuf varint")


def _fields(data: bytes) -> Iterator[tuple[int, int, int | bytes]]:
    offset = 0
    while offset < len(data):
        key, offset = _read_varint(data, offset)
        number, wire_type = key >> 3, key & 7
        if wire_type == 0:
            value, offset = _read_varint(data, offset)
        elif wire_type == 1:
            value = data[offset : offset + 8]
            offset += 8
        elif wire_type == 2:
            length, offset = _read_varint(data, offset)
            value = data[offset : offset + length]
            offset += length
        elif wire_type == 5:
            value = data[offset : offset + 4]
            offset += 4
        else:
            raise ValueError(f"Unsupported protobuf wire type: {wire_type}")
        yield number, wire_type, value


def _zigzag(value: int) -> int:
    return (value >> 1) ^ -(value & 1)


def _input_event(data: bytes) -> tuple | None:
    for number, wire_type, value in _fields(data):
        if wire_type != 2 or not isinstance(value, bytes):
            continue
        if number == 1:
            button = action = 0
            for field, _, item in _fields(value):
                if field == 1 and isinstance(item, int):
                    button = item
                elif field == 2 and isinstance(item, int):
                    action = item
            return "button", button, action
        if number == 2:
            position = 0
            for field, _, item in _fields(value):
                if field == 1 and isinstance(item, int):
                    position = item
            return "switch", position
        if number == 3:
            delta = 0
            for field, _, item in _fields(value):
                if field == 1 and isinstance(item, int):
                    delta = _zigzag(item)
            return "encoder", delta
    return None


def events_from_state(data: bytes) -> Iterator[tuple]:
    """Yield input tuples from one protobuf BSB_State.State frame."""
    for number, wire_type, update in _fields(data):
        if number != 2 or wire_type != 2 or not isinstance(update, bytes):
            continue
        for field, update_wire_type, value in _fields(update):
            if field == 11 and update_wire_type == 2 and isinstance(value, bytes):
                event = _input_event(value)
                if event:
                    yield event


def stream_input_events(
    ws_url: str,
    on_event: Callable[[tuple], None],
    should_stop: Callable[[], bool],
    on_status: Callable[[str], None] = print,
) -> None:
    """Reconnect as needed and forward physical input until asked to stop."""
    while not should_stop():
        socket = None
        try:
            socket = create_connection(ws_url, timeout=5, enable_multithread=True)
            socket.settimeout(1)
            socket.send('{"enable":true}')
            on_status(f"Listening for controls at {ws_url.split('?')[0]}")
            while not should_stop():
                try:
                    opcode, data = socket.recv_data(control_frame=False)
                except WebSocketTimeoutException:
                    continue
                if opcode != 2 or not data:
                    continue
                for event in events_from_state(data):
                    on_event(event)
        except Exception as error:
            if should_stop():
                return
            message = str(error).split(" -+-+- ", 1)[0]
            on_status(f"Control connection lost: {message}; retrying in 2s")
            time.sleep(2)
        finally:
            if socket is not None:
                try:
                    socket.close()
                except Exception:
                    pass
