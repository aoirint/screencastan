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
  is_recording: bool = False
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
    # cvargs = '-c:v h264_nvenc -preset:v p7 -profile:v high -rc:v vbr -rc-lookahead 1 -spatial-aq 0 -temporal-aq 1 -cq 23 -weighted_pred 0 -coder cabac -b_ref_mode 2 -dpb_size 4 -multipass 0 -g 120 -bf 2 -pix_fmt yuv420p -color_range tv -color_primaries bt709 -color_trc bt709 -colorspace bt709 -movflags +faststart'
    # cvargs = '-c:v h264_nvenc -preset:v p6 -profile:v high -rc:v vbr -rc-lookahead 1 -spatial-aq 0 -temporal-aq 1 -cq 23 -weighted_pred 0 -coder cabac -b_ref_mode 2 -dpb_size 4 -multipass 0 -g 120 -bf 2 -pix_fmt yuv420p -color_range tv -color_primaries bt709 -color_trc bt709 -colorspace bt709 -movflags +faststart'
    cvargs = '-c:v h264_nvenc -preset:v p6 -profile:v high -rc:v cbr -b:v 2500K -rc-lookahead 1 -spatial-aq 0 -temporal-aq 1 -cq 23 -weighted_pred 0 -coder cabac -b_ref_mode 2 -dpb_size 4 -multipass 0 -g 120 -bf 2 -pix_fmt yuv420p -color_range tv -color_primaries bt709 -color_trc bt709 -colorspace bt709 -movflags +faststart'

    cvargs = cvargs.split(' ')

    vargs = [
      '-f',
      'x11grab',
      '-thread_queue_size',
      '1024',
      '-use_wallclock_as_timestamps',
      '1',
      '-framerate',
      framerate_str,
      '-video_size',
      video_size_str,
      '-window_id',
      window_id,
      # '-draw_mouse',
      # '0',
      '-i',
      ':0.0+0,0',
    ]

    aargs = []
    has_audio = len(audio_tracks) > 0

    for track_index, track in enumerate(audio_tracks):
      aargs += [
        '-f',
        'pulse',
        '-thread_queue_size',
        '1024',
        '-use_wallclock_as_timestamps',
        '1',
        '-i',
        track.source_name,
      ]

    caargs = []
    fargs = []
    if has_audio:
      caargs += [
        '-acodec',
        'aac',
        # '-af',
        # 'aresample=async=1', # https://trac.ffmpeg.org/ticket/4203
      ]

      audio_filter_list = " ".join([ f"[{1+track_index}:a] aresample=async=1 [r{1+track_index}];" for track_index in range(len(audio_tracks)) ])
      audio_merge_list = "".join([ f"[{1+track_index}]" for track_index in range(len(audio_tracks)) ]) # [1][2]
      fargs += [
        '-filter_complex',
        f'{audio_filter_list} {audio_merge_list} amerge=inputs={len(audio_tracks)} [m]',
      ]

    margs = []
    margs += [
      '-map',
      '0:v:0',
    ]

    if has_audio:
      margs += [
        '-map',
        f'[m]:a',
        f'-metadata:s:a:0',
        f'title=All Audio',
      ]
    for track_index, track in enumerate(audio_tracks):
      margs += [
        '-map',
        # f'{1+track_index}:a',
        f'[r{1+track_index}]',
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
      '-vsync',
      '0',
      output_path,
    ]

    import sys
    proc = subprocess.Popen(args=args, stderr=subprocess.PIPE)

    context = RecordingContext()
    context.proc = proc

    def on_process_closed():
      context.is_recording = False
      context.is_alive = False
      print('Recording process closed')

    def on_recording_started():
      context.is_recording = True
      print('Recording started')

    def watch_process():
      while True:
        if proc.poll() is not None:
          on_process_closed()
          break

        # Block until process closed
        for line_bytes in proc.stderr:
          line = line_bytes.decode('utf-8').strip()

          if line == 'Press [q] to stop, [?] for help':
            on_recording_started()

          print(line, file=sys.stderr)

        time.sleep(0.01)

    thread = threading.Thread(target=watch_process)
    context.thread = thread

    thread.start()

    yield context
  finally:
    if proc is not None:
      proc.terminate()
