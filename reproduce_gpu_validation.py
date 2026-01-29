import subprocess
import os
import sys

# Mocking the Config logic to find ffmpeg
def find_ffmpeg():
    FFMPEG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ffmpeg')
    local_bin = os.path.join(FFMPEG_DIR, 'ffmpeg.exe')
    if os.path.exists(local_bin):
        return local_bin
    
    import shutil
    system_bin = shutil.which('ffmpeg')
    if system_bin:
        return system_bin
    return "ffmpeg"

ffmpeg_bin = find_ffmpeg()
print(f"Using FFmpeg: {ffmpeg_bin}")

print("Attempting runtime validation...")
cmd = [
    ffmpeg_bin,
    '-y',
    '-f', 'lavfi', '-i', 'color=c=black:s=640x360:d=1',
    '-c:v', 'hevc_nvenc',
    '-f', 'null', '-'
]

try:
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True,
        timeout=10
    )
    print("SUCCESS")
except subprocess.CalledProcessError as e:
    print("FAILURE")
    print("STDOUT:", e.stdout)
    print("STDERR:", e.stderr)
except Exception as e:
    print(f"EXCEPTION: {e}")
