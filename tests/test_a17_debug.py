"""Preserve normal recovery decryption/startup while selecting the compatible kernel."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class A17DebugTest(unittest.TestCase):
    def test_normal_decryption_preserved(self):
        device = (ROOT / 'device.mk').read_text()
        for name in ('TW_INCLUDE_CRYPTO', 'TW_INCLUDE_CRYPTO_FBE', 'TW_INCLUDE_FBE_METADATA_DECRYPT', 'BOARD_USES_QCOM_FBE_DECRYPTION'):
            self.assertRegex(device, rf'(?m)^{name} := true$')
        self.assertIn('    qcom_decrypt', device)
        self.assertIn('    qcom_decrypt_fbe', device)
        init = (ROOT / 'recovery/root/init.recovery.qcom.rc').read_text()
        self.assertIn('import /init.recovery.qcom_decrypt.rc', init)
        self.assertFalse((ROOT / 'recovery/root/init.recovery.service.rc').exists())
        fstab = (ROOT / 'recovery/root/system/etc/recovery.fstab').read_text()
        rows = {line.split()[1]: line for line in fstab.splitlines() if line.strip() and not line.lstrip().startswith('#')}
        self.assertIn('/metadata', rows)
        self.assertIn('fileencryption=', rows['/data'])
        self.assertIn('metadata_encryption=', rows['/data'])

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
