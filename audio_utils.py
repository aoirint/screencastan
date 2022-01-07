from dataclasses import dataclass
import subprocess
import re
from typing import (
  List,
  Optional,
)

class InvalidCommandStateError(Exception):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

@dataclass
class Sink:
  is_default: bool
  index: int
  name: str
  data_type: str
  num_channels: int
  frequency: str

def get_sinks() -> List[Sink]:
  sinks = []

  args = [
    'pacmd',
    'list-sinks'
  ]
  proc = subprocess.run(args=args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  output = proc.stdout.decode('utf-8')
  error = proc.stderr.decode('utf-8')

  if len(error) != 0:
    raise InvalidCommandStateError('Error in pacmd')

  while True:
    output = output.strip()

    default_index_match = re.search(r'^\s*(\*)?\s*index:\s*(\d+)$', output, flags=re.MULTILINE)
    if not default_index_match:
      # no more sink
      break

    is_default = default_index_match.group(1) is not None
    index = int(default_index_match.group(2))

    output = output[default_index_match.end():]

    name_match = re.search(r'^\s*name:\s*<(.+)>$', output, flags=re.MULTILINE)
    if name_match:
      name = name_match.group(1)

      output = output[name_match.end():]
    else:
      # no name info
      name = None

    sample_match = re.search(r'^\s*sample spec:\s*(.+)\s*(\d+)ch\s*(\d+)Hz$', output, flags=re.MULTILINE)
    if sample_match:
      data_type = sample_match.group(1) # s16le
      num_channels = int(sample_match.group(2)) # 2
      frequency = int(sample_match.group(3)) # 48000

      output = output[sample_match.end():]
    else:
      # no channel map info
      data_type = None
      num_channels = None
      frequency = None

    sinks.append(Sink(
      is_default=is_default,
      index=index,
      name=name,
      data_type=data_type,
      num_channels=num_channels,
      frequency=frequency,
    ))

  return sinks

def get_default_sink() -> Optional[Sink]:
  for sink in get_sinks():
    if sink.is_default:
      return sink

  return None


@dataclass
class Source:
  is_default: bool
  index: int
  name: str
  data_type: str
  num_channels: int
  frequency: str

def get_sources() -> List[Sink]:
  sources = []

  args = [
    'pacmd',
    'list-sources'
  ]
  proc = subprocess.run(args=args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  output = proc.stdout.decode('utf-8')
  error = proc.stderr.decode('utf-8')

  if len(error) != 0:
    raise InvalidCommandStateError('Error in pacmd')

  while True:
    output = output.strip()

    default_index_match = re.search(r'^\s*(\*)?\s*index:\s*(\d+)$', output, flags=re.MULTILINE)
    if not default_index_match:
      # no more sink
      break

    is_default = default_index_match.group(1) is not None
    index = int(default_index_match.group(2))

    output = output[default_index_match.end():]

    name_match = re.search(r'^\s*name:\s*<(.+)>$', output, flags=re.MULTILINE)
    if name_match:
      name = name_match.group(1)

      output = output[name_match.end():]
    else:
      # no name info
      name = None

    sample_match = re.search(r'^\s*sample spec:\s*(.+)\s*(\d+)ch\s*(\d+)Hz$', output, flags=re.MULTILINE)
    if sample_match:
      data_type = sample_match.group(1) # s16le
      num_channels = int(sample_match.group(2)) # 2
      frequency = int(sample_match.group(3)) # 48000

      output = output[sample_match.end():]
    else:
      # no channel map info
      data_type = None
      num_channels = None
      frequency = None

    sources.append(Sink(
      is_default=is_default,
      index=index,
      name=name,
      data_type=data_type,
      num_channels=num_channels,
      frequency=frequency,
    ))

  return sources

def get_default_source() -> Optional[Source]:
  for source in get_sources():
    if source.is_default:
      return source

  return None
