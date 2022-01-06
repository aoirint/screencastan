import time

from window_utils import (
  get_active_window_id,
  get_window_pid,
  get_window_geometry,
)
from audio_utils import (
  get_default_sink,
  get_default_source,
)

from record_utils import (
  AudioTrack,
  record,
)

window_id = get_active_window_id()
geometry = get_window_geometry(window_id=window_id)

# Speaker
default_sink = get_default_sink()

# Mic
default_source = get_default_source()

audio_tracks = [
  AudioTrack(
    source_name=default_sink.name + '.monitor',
    track_name='Desktop Audio',
  ),
  AudioTrack(
    source_name=default_source.name,
    track_name='Mic',
  ),
]

with record(
  window_id=window_id,
  video_size=(geometry.width, geometry.height),
  framerate=30,
  audio_tracks=audio_tracks,
  output_path='output.mkv',
) as recording:
  while not recording.is_recording:
    time.sleep(0.01)

  print('Wait 5 seconds')
  time.sleep(5)
