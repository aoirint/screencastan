import subprocess
from dataclasses import dataclass
import re
from typing import (
  Tuple,
)

class NoActiveWindowError(Exception):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

def get_active_window_id() -> str:
  args = [
    'xdotool',
    'getactivewindow',
  ]
  proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

  output = proc.stdout.decode('utf-8')
  error = proc.stderr.decode('utf-8')

  if len(error) != 0:
    raise NoActiveWindowError()

  return output.strip()


class NoSuchWindowError(Exception):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

class UnsupportedCommandOutputError(Exception):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

@dataclass
class WindowGeometry:
  window_id: str
  screen: str
  x: int
  y: int
  width: int
  height: int

def get_window_geometry(window_id: str) -> WindowGeometry:
  args = [
    'xdotool',
    'getwindowgeometry',
    window_id,
  ]
  proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

  output = proc.stdout.decode('utf-8')
  error = proc.stderr.decode('utf-8')

  if len(error) != 0:
    raise NoSuchWindowError()

  output = output.strip()

  lines = output.split('\n')
  if len(lines) != 3:
    raise UnsupportedCommandOutputError('Number of output lines must be 3.')

  position_line = lines[1].strip()
  position_line_match = re.match(r'^Position:\s*(-?\d+),(-?\d+)\s*\(screen:\s*(\d+)\)$', position_line)
  if not position_line_match:
    raise UnsupportedCommandOutputError(f'Invalid position line format: {position_line}')

  x = int(position_line_match.group(1))
  y = int(position_line_match.group(2))
  screen = int(position_line_match.group(3))

  geometry_line = lines[2].strip()
  geometry_line_match = re.match(r'^Geometry:\s*(\d+)x(\d+)$', geometry_line)
  if not geometry_line_match:
    raise UnsupportedCommandOutputError('Invalid geometry line format.')

  width = int(geometry_line_match.group(1))
  height = int(geometry_line_match.group(2))

  return WindowGeometry(
    window_id=window_id,
    screen=screen,
    x=x,
    y=y,
    width=width,
    height=height,
  )

def get_window_pid(window_id: str) -> int:
  args = [
    'xdotool',
    'getwindowgeometry',
    window_id,
  ]
  proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

  output = proc.stdout.decode('utf-8').strip()
  error = proc.stderr.decode('utf-8')

  if len(error) != 0:
    raise NoSuchWindowError()

  return int(output)
