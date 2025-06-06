import sys
import torch
import torch_xla
from torch_xla import runtime as xr
import torch_xla.core.xla_model as xm


def _mp_fn(index):
  device = torch_xla.device()
  if xm.xla_device_hw(device) in ['TPU', 'NEURON']:
    world_size = xr.world_size()
    ordinal = xr.global_ordinal()
    value = torch.tensor([ordinal] * 100, dtype=torch.int32, device=device)
    pairs = []
    for i in range(1, world_size):
      pairs.append([i - 1, i])
    pairs.append([world_size - 1, 0])
    result_tensor = xm.collective_permute(value, pairs)

    result = result_tensor.cpu().tolist()
    expected = [ordinal - 1] * 100 if ordinal != 0 else [world_size - 1] * 100

    if result != expected:
      print(f"Wrong result from core {ordinal}: {result}", file=sys.stderr)
      sys.exit(1)
  else:
    print(f"Default device {device} is not a supported device", file=sys.stderr)


if __name__ == '__main__':
  torch_xla.launch(_mp_fn, args=())
