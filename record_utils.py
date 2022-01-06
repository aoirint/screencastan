from dataclasses import dataclass
import subprocess
import time
import threading
from contextlib import contextmanager
from typing import (
  Tuple,
  List,
)

@dataclass
class RecordingContext:
  is_alive: bool = True
  proc: subprocess.Popen = None
  thread: threading.Thread = None

  def stop(self):
    self.proc.terminate()

@dataclass
class AudioTrack:
  source_name: str
  track_name: str

@contextmanager
def record(
    window_id: str,
    video_size: Tuple[int, int],
    framerate: int,
    audio_tracks: List[AudioTrack],
    output_path: str,
) -> RecordingContext:
  if len(video_size) != 2:
    raise ValueError('Invalid argument shape for video_size. length must be 2.')

  proc = None
  try:
    video_size_str = 'x'.join(map(str, video_size))
    framerate_str = str(framerate)
    
    # https://nyanshiba.com/blog/obs-studio#hevc_nvenc
    # cvargs = '-c:v hevc_nvenc -preset:v p7 -profile:v main10 -rc:v constqp -rc-lookahead 1 -spatial-aq 0 -temporal-aq 1 -weighted_pred 0 -init_qpI 21 -init_qpP 21 -init_qpB 24 -b_ref_mode 1 -dpb_size 4 -multipass 2 -g 60 -bf 3 -pix_fmt yuv420p10le -color_range tv -color_primaries bt709 -color_trc bt709 -colorspace bt709 -movflags +faststart'

    # https://nyanshiba.com/blog/obs-studio#h264_nvenc
    cvargs = '-c:v h264_nvenc -preset:v p7 -profile:v high -rc:v vbr -rc-lookahead 1 -spatial-aq 0 -temporal-aq 1 -cq 23 -weighted_pred 0 -coder cabac -b_ref_mode 2 -dpb_size 4 -multipass 0 -g 120 -bf 2 -pix_fmt yuv420p -color_range tv -color_primaries bt709 -color_trc bt709 -colorspace bt709 -movflags +faststart'

    cvargs = [
      '-framerate',
      framerate_str,
      *(cvargs.split(' ')),
    ]

    vargs = [
      '-f',
      'x11grab',
      '-video_size',
      video_size_str,
      '-window_id',
      window_id,
      '-i',
      ':0.0+0,0',
    ]

    aargs = []
    for track_index, track in enumerate(audio_tracks):
      aargs += [
        '-f',
        'pulse',
        '-i',
        track.source_name,
      ]
    caargs = [
      '-acodec',
      'aac',
    ]

    fargs = [
      '-filter_complex',
      f'{"".join([ f"[{1+track_index}]" for track_index in range(len(audio_tracks)) ])} amerge=inputs={len(audio_tracks)} [m]',
    ]

    margs = []
    margs += [
      '-map',
      '0:v:0',
    ]
    margs += [
      '-map',
      f'[m]:a',
      f'-metadata:s:a:0',
      f'title=All Audio',
    ]
    for track_index, track in enumerate(audio_tracks):
      margs += [
        '-map',
        f'{1+track_index}:a',
        f'-metadata:s:a:{1+track_index}',
        f'title={track.track_name}',
      ]

    args = [
      'ffmpeg',
      '-y',
      *vargs,
      *aargs,
      *cvargs,
      *caargs,
      *fargs,
      *margs,
      output_path,
    ]

    import sys
    proc = subprocess.Popen(args=args, stderr=sys.stderr)

    context = RecordingContext()
    context.proc = proc

    def on_process_closed():
      context.is_alive = False
      print('Recording process closed')

    def watch_process():
      while True:
        if proc.poll() is not None:
          on_process_closed()
          break

        time.sleep(0.01)

    thread = threading.Thread(target=watch_process)
    context.thread = thread

    thread.start()

    yield context
  finally:
    if proc is not None:
      proc.terminate()
