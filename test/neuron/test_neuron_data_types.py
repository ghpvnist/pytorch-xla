import sys

import torch
import torch_xla
import torch_xla.core.xla_model as xm
import unittest


class NeuronXlaDataTypeTest(unittest.TestCase):

  def _test_datatypes(self, dtype, op_xla_dtype, op):
    t1 = torch.tensor([2, 3], dtype=dtype, device='xla')
    t2 = torch.tensor([2, 3], dtype=dtype, device='xla')

    t3 = op(t1, t2)

    self.assertEqual(t3.dtype, dtype)

    hlo_text = torch_xla._XLAC._get_xla_tensors_text([t3])
    device_data_irs = [
        line for line in hlo_text.split('\n') if 'xla::device_data' in line
    ]
    self.assertEqual(len(device_data_irs), 2)
    for device_data_ir in device_data_irs:
      self.assertIn(op_xla_dtype, device_data_ir)

  def test_datatypes(self):
    test_cases = [(torch.float, "f32", torch.floor_divide),
                  (torch.double, "f32", torch.floor_divide),
                  (torch.int16, "s32", torch.add),
                  (torch.int32, "s32", torch.add),
                  (torch.int64, "s64", torch.add),
                  (torch.uint16, "u32", torch.add),
                  (torch.uint32, "u32", torch.add),
                  (torch.uint64, "u64", torch.add)]

    for dtype, op_xla_dtype, op in test_cases:
      with self.subTest(dtype=dtype, op_xla_dtype=op_xla_dtype, op=op):
        self._test_datatypes(dtype, op_xla_dtype, op)


if __name__ == '__main__':
  test = unittest.main()
  sys.exit(0 if test.result.wasSuccessful() else 1)
