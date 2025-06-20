# Parse local options first, and rewrite the sys.argv[].
# We need to do that before import "common", as otherwise we get an error for
# unrecognized arguments.
import argparse
import sys

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--replicated', action='store_true')
parser.add_argument('--long_test', action='store_true')
parser.add_argument('--max_diff_count', type=int, default=25)
parser.add_argument('--verbosity', type=int, default=0)
FLAGS, leftovers = parser.parse_known_args()
sys.argv = [sys.argv[0]] + leftovers

# Normal imports section starts here.
import torch
import torch_xla
import torch_xla.utils.utils as xu
import torch_xla.core.xla_model as xm
import torch_xla.debug.metrics as met
import unittest


class TestOperationsHlo(unittest.TestCase):

  def setUp(self):
    super(TestOperationsHlo, self).setUp()

  def tearDown(self):
    super(TestOperationsHlo, self).tearDown()

  def test_expand(self):
    a = torch.rand(1, 5, device='xla')
    b = a.expand(5, 5)
    hlo_text = torch_xla._XLAC._get_xla_tensors_text([b])
    assert 'aten::expand' in hlo_text

  def test_special_scalars_addcdiv_addcmul(self):
    a = torch.rand(5, 5).to('xla')
    b = torch.rand(5, 5).to('xla')
    c = torch.rand(5, 5).to('xla')
    for op in [torch.addcdiv, torch.addcmul]:
      out = op(a, b, c, value=1.0)
      hlo_text = torch_xla._XLAC._get_xla_tensors_text([out])
      instructions = hlo_text.split('\n')
      const_hlo = instructions[1]
      root_hlo = instructions[5]
      assert 'prim::Constant()' in const_hlo
      assert 'xla::device_data()' not in const_hlo
      assert 'f32' in root_hlo
      assert 'f64' not in root_hlo

  def test_div_by_f64(self):
    mod = torch.nn.MultiheadAttention(768, 12, batch_first=True)
    mod.to('xla')
    a = torch.rand(1, 512, 768).to('xla')
    b, _ = mod(a, a, a, need_weights=False)
    b.sum().backward()
    hlo_text = torch_xla._XLAC._get_xla_tensors_text(
        [p.grad for p in mod.parameters() if p.requires_grad])
    assert 'f64' not in hlo_text

  def test_dropout_by_u8_mask(self):
    mod = torch.nn.Dropout().to('xla')
    a = torch.rand(20, 16, dtype=torch.bfloat16).to('xla')
    b = mod(a)
    hlo_text = torch_xla._XLAC._get_xla_tensors_hlo([b])
    assert 'u8' in hlo_text


if __name__ == '__main__':
  torch.set_default_dtype(torch.float32)
  torch.manual_seed(42)
  torch_xla._XLAC._xla_set_mat_mul_precision('highest')
  test = unittest.main(verbosity=FLAGS.verbosity, exit=False)
  if xu.getenv_as('METRICS_DEBUG', bool, defval=False):
    print(met.metrics_report())
  sys.exit(0 if test.result.wasSuccessful() else 1)
