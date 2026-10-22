"""Guard the diagnostic profile; these checks do not establish FBE decryption."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class A17DebugTest(unittest.TestCase):
    def test_diagnostic_startup(self):
        device = (ROOT / 'device.mk').read_text()
        for name in ('TW_INCLUDE_CRYPTO', 'TW_INCLUDE_CRYPTO_FBE', 'TW_INCLUDE_FBE_METADATA_DECRYPT'):
            self.assertRegex(device, rf'(?m)^{name} := false$')
        self.assertNotIn('    qcom_decrypt', device)
        init = (ROOT / 'recovery/root/init.recovery.qcom.rc').read_text()
        self.assertNotIn('import /init.recovery.qcom_decrypt.rc', init)
        self.assertNotIn('exec u:r:recovery:s0 -- /system/bin/fix-invalid-vintf-manifest.sh', init)
        service = (ROOT / 'recovery/root/init.recovery.service.rc').read_text()
        self.assertIn('service recovery /system/bin/recovery\n    disabled', service)
        self.assertNotRegex(service, r'(?m)^\s+start recovery$')
        fstab = (ROOT / 'recovery/root/system/etc/recovery.fstab').read_text()
        for line in fstab.splitlines():
            if line.strip() and not line.lstrip().startswith('#'):
                self.assertNotIn(line.split()[1], ('/data', '/metadata'))

    def test_selected_prebuilts(self):
        self.assertIn('TARGET_PREBUILT_KERNEL := $(DEVICE_PATH)/prebuilt/Image', (ROOT / 'BoardConfig.mk').read_text())
        self.assertIn('$(LOCAL_PATH)/prebuilt/modules', (ROOT / 'device.mk').read_text())
        image = ROOT / 'prebuilt/Image'
        if not image.exists():
            self.skipTest('Local kernel/modules must be restored from the saved diagnostic image')
        with image.open('rb') as stream:
            self.assertEqual(stream.read(60)[56:60], b'ARMd')
        modules = list((ROOT / 'prebuilt/modules').rglob('*.ko'))
        self.assertTrue(modules)
        for module in modules:
            with module.open('rb') as stream:
                header = stream.read(20)
            self.assertEqual(header[:6], b'\x7fELF\x02\x01')
            self.assertEqual(int.from_bytes(header[18:20], 'little'), 183)


if __name__ == '__main__':
    unittest.main()
