#!/usr/bin/env python3
"""0.3.4 read-only Nintendo DS ROM preflight; NEVER patches, boots or submits."""
import argparse
import json
import struct
import subprocess
from pathlib import Path

MAX_ROM = 1024 * 1024 * 1024


def crc16(data):
    crc = 0xFFFF
    for value in data:
        crc ^= value
        for _ in range(8):
            crc = (crc >> 1) ^ (0xA001 if crc & 1 else 0)
    return crc


def word(data, offset):
    return struct.unpack_from('<I', data, offset)[0]


def ensure(condition, reason):
    if not condition:
        raise ValueError(reason)


def segment(header, file_length, header_size, name, at, allowed):
    offset, entry, ram, size = struct.unpack_from('<4I', header, at)
    ensure(size > 0 and size % 4 == 0, name + ': size or alignment')
    ensure(offset % 4 == 0 and offset >= header_size, name + ': file offset')
    ensure(offset <= file_length and size <= file_length - offset, name + ': truncated')
    ensure(ram % 4 == 0 and any(low <= ram < high and size <= high - ram
                                  for low, high in allowed), name + ': RAM range')
    pc = entry & ~1  # Thumb entry bit
    ensure(ram <= pc < ram + size, name + ': entry point')
    return {'name': name, 'file_offset': offset, 'file_bytes': size,
            'load_address': f'0x{ram:08X}', 'entry': f'0x{entry:08X}'}


def inspect_rom(path):
    file_length = path.stat().st_size
    ensure(0x200 <= file_length <= MAX_ROM, 'outside bounded ROM file size')
    with path.open('rb') as source:
        header = source.read(0x1000)
    ensure(len(header) >= 0x200, 'truncated header')
    unit_code = header[0x12]
    ensure(unit_code in (0, 2, 3), 'unsupported NDS unit code')
    header_size = word(header, 0x84)
    ensure(0x200 <= header_size <= min(file_length, 0x4000)
           and header_size % 0x200 == 0, 'invalid header size')
    if unit_code in (2, 3):
        ensure(header_size >= 0x1000, 'TWL requires extended header')
    header_crc = struct.unpack_from('<H', header, 0x15E)[0]
    ensure(header_crc == crc16(header[:0x15E]), 'invalid header CRC16')
    ranges9 = [(0x02000000, 0x03000000)]
    ranges7 = ranges9 + [(0x037C0000, 0x03810000)]
    segments = [segment(header, file_length, header_size, 'ARM9', 0x20, ranges9),
                segment(header, file_length, header_size, 'ARM7', 0x30, ranges7)]
    if unit_code in (2, 3):
        for name, at in (('ARM9i', 0x1C0), ('ARM7i', 0x1D0)):
            if word(header, at + 12):
                segments.append(segment(header, file_length, header_size,
                                        name, at, [(0x02000000, 0x04000000)]))
    for i, first in enumerate(segments):
        for second in segments[i + 1:]:
            a, b = first['file_offset'], second['file_offset']
            ensure(a + first['file_bytes'] <= b or b + second['file_bytes'] <= a,
                   'overlapping file segments: ' + first['name'] + '/' + second['name'])
    declared_used = word(header, 0x80)
    if declared_used:
        ensure(declared_used <= file_length, 'declared used ROM size > file')
        ensure(all(seg['file_offset'] + seg['file_bytes'] <= declared_used
                   for seg in segments), 'segment past declared ROM used size')
    banner = word(header, 0x68)
    if banner:
        ensure(banner >= header_size and banner + 0x840 <= file_length,
               'truncated standard banner')
    return {
        'status': 'STRUCTURE_PASS_RETAIL_MONITOR_NOT_PROVEN',
        'version': '0.3.4-preflight',
        'scope': 'read-only header checks; NOT a game compatibility verdict',
        'rom_bytes': file_length, 'unit_code': unit_code,
        'mode': 'NTR' if unit_code == 0 else 'TWL-capable',
        'header_bytes': header_size, 'segments': segments,
        'official_hash': None, 'auth': 'NOT_IMPLEMENTED',
        'official_awards': 0, 'retail_monitor_ready': False,
        'unverified': [
            'Real Flipnote Lenny permissions and ARM7/ARM9 startup',
            'Game BSS/heap/overlay ranges and true resident-memory reservation',
            'nds-bootstrap/cardengine integration and no interference with saves/audio',
            'Per-frame main RAM/DTCM capture, cache, MPU and pointer correctness',
            'Networking, server identification, login, sessions and RA client approval',
        ],
    }


def attach_hash(result, executable, path):
    command = [str(executable.resolve()), str(path.resolve())]
    proc = subprocess.run(command, capture_output=True, text=True, timeout=30,
                          check=True)
    payload = json.loads(proc.stdout)
    ensure(payload.get('status') == 'PASS' and
           payload.get('algorithm') == 'official_rcheevos_nintendo_ds' and
           payload.get('submitted') is False and
           payload.get('game_resolved') is False and
           isinstance(payload.get('hash'), str) and
           len(payload['hash']) == 32 and
           all(ch in '0123456789abcdefABCDEF' for ch in payload['hash']),
           'unexpected local read-only hash tool output')
    result['official_hash'] = {'algorithm': payload['algorithm'],
                               'console_id': payload.get('console_id'),
                               'hash': payload['hash'].lower(),
                               'game_resolved': False, 'submitted': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original_nds', type=Path)
    parser.add_argument('--hash-tool', type=Path,
                        help='optional trusted dsirb_nds_hash from the 0.3.3 build')
    arguments = parser.parse_args()
    try:
        result = inspect_rom(arguments.original_nds)
        if arguments.hash_tool:
            attach_hash(result, arguments.hash_tool, arguments.original_nds)
    except (OSError, ValueError, struct.error, subprocess.SubprocessError,
            json.JSONDecodeError) as error:
        print(json.dumps({'status': 'BLOCKED', 'reason': str(error),
                          'rom_modified': False, 'submitted': False}))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
