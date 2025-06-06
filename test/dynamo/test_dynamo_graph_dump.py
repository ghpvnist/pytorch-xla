import os
import sys

import torch
import torch_xla
import torch_xla.core.xla_model as xm
import torch_xla.utils.utils as xu
import torch_xla.debug.metrics as met
import torch._dynamo as dynamo
import torchvision
import unittest


class DynamoGraphDumpTest(unittest.TestCase):

  def fn_simple(self, x, y):
    a = torch.cos(x)
    b = torch.sin(y)
    return a + b

  @dynamo.optimize('openxla')
  def fn_simple_dynamo(self, x, y):
    return self.fn_simple(x, y)

  def test_dump_graph_with_dynamo_execution(self):
    save_file = os.getenv('XLA_SAVE_TENSORS_FILE')
    if not save_file:
      assert False, "This test should be run with XLA_SAVE_TENSORS_FILE"
    save_file += '.0'
    device = torch_xla.device()
    xla_x = torch.tensor(100.0).to(device)
    xla_y = torch.tensor(200.0).to(device)
    res_xla_dynamo = self.fn_simple_dynamo(xla_x, xla_y)
    with open(save_file, 'rb') as f:
      lines = f.readlines()
      current_line = len(lines)
      self.assertIn('Graph Hash:', lines[-5].decode())
    with open(save_file, 'rb') as f:
      res_xla_dynamo_2 = self.fn_simple_dynamo(xla_x, xla_y)
      lines = f.readlines()
      new_line = len(lines)
      self.assertIn('Graph Hash:', lines[-5].decode())
    self.assertGreater(new_line, current_line)


if __name__ == '__main__':
  test = unittest.main()
  sys.exit(0 if test.result.wasSuccessful() else 1)
