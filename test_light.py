"""Hardware-free checks of argument validation and HID framing/failure handling."""
import importlib.machinery
import importlib.util
import unittest
from unittest.mock import patch

loader = importlib.machinery.SourceFileLoader('light', str(__import__('pathlib').Path(__file__).with_name('falchion-light')))
spec = importlib.util.spec_from_loader(loader.name, loader)
light = importlib.util.module_from_spec(spec)
loader.exec_module(light)

class LightTests(unittest.TestCase):
    def test_wave_chunk_sequence(self):
        packets = light.effect_payloads('wave', bytes([51, 102, 153]), 50, 'slow')
        self.assertEqual(len(packets), 3)
        self.assertEqual(packets[0], bytes.fromhex('51 2c 04 02 ff 32 01 00 02') + bytes(6))
        self.assertEqual(packets[1], bytes.fromhex('51 2c 04 01') + bytes(11))
        self.assertEqual(packets[2], bytes.fromhex('51 2c 04 00') + bytes(11))

    def test_static_payload_unchanged(self):
        self.assertEqual(light.effect_payloads('static', bytes([51, 102, 153]), 50, 'medium'),
                         [bytes.fromhex('51 2c 00 00 80 32 00 00 02 33 66 99')])

    def test_color(self):
        self.assertEqual(light.color('#336699'), bytes([51, 102, 153]))
        for bad in ['123', 'gg0000', '00000000', '-10000']:
            with self.assertRaises(Exception):
                light.color(bad)

    def exchange(self, reply):
        payload = b'\x51\x2c\x00'
        with patch.object(light.select, 'select', side_effect=[([], [], []), ([], [9], []), ([9], [], [])]), patch.object(light.os, 'write', return_value=65) as write, patch.object(light.os, 'read', return_value=reply):
            result = light.exchange(9, payload)
            self.assertEqual(write.call_args.args[1], b'\0' + payload + bytes(61))
            self.assertEqual(write.call_count, 1)
            return result

    def test_framing_and_reply(self):
        self.assertEqual(self.exchange(b'\x51\x2c\x00' + bytes(61))[0], 0x51)

    def test_reject_negative_or_unrelated_reply(self):
        for reply in [b'', b'\x51\xff', b'\x12\x00']:
            with self.assertRaises(RuntimeError):
                self.exchange(reply)

    def test_timeout_does_not_retry_write(self):
        with patch.object(light.select, 'select', side_effect=[([], [], []), ([], [9], []), ([], [], [])]), patch.object(light.os, 'write', return_value=65) as write:
            with self.assertRaises(RuntimeError):
                light.exchange(9, b'\x12\0')
            self.assertEqual(write.call_count, 1)

if __name__ == '__main__':
    unittest.main()
