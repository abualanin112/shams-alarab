import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def ensure_directory(path: str) -> None:
    """Ensure a directory exists."""
    os.makedirs(path, exist_ok=True)

def get_output_path(input_path: str, output_dir: str = None, suffix: str = "_processed") -> str:
    """
    Generate an output file path.
    """
    input_path = Path(input_path)
    filename = input_path.stem + suffix + input_path.suffix
    
    if output_dir:
        ensure_directory(output_dir)
        return str(Path(output_dir) / filename)
    
    return str(input_path.parent / filename)

def find_srt_file(video_path: str) -> str | None:
    """
    Look for a matching .srt file using priority levels:
    1. Exact match (<stem>.srt)
    2. Language suffix (<stem>_<lang>.srt) - e.g., _eng, _ar, _en
    3. Prefix-based case-insensitive fallback
    """
    video_path = Path(video_path)
    stem = video_path.stem
    directory = video_path.parent
    
    # Priority 1: Exact Match (Case-Sensitive first)
    exact_match = directory / f"{stem}.srt"
    if exact_match.exists():
        return str(exact_match)
        
    # Priority 2: Language Suffixes
    suffixes = ['_eng', '_ar', '_en', '_ar_auto']
    candidates_p2 = []
    for suffix in suffixes:
        path = directory / f"{stem}{suffix}.srt"
        if path.exists():
            candidates_p2.append(path)
    
    if candidates_p2:
        if len(candidates_p2) > 1:
            logger.warning(f"Multiple suffix matches found for {stem}. Choosing first lexicographically.")
        candidates_p2.sort()
        return str(candidates_p2[0])

    # Priority 3: Prefix fallback (Case-Insensitive)
    candidates_p3 = []
    try:
        # Search for any .srt file in the same directory
        for item in directory.glob("*.srt"):
            if item.name.lower().startswith(stem.lower()):
                candidates_p3.append(item)
    except Exception as e:
        logger.error(f"Error searching for SRT files: {e}")
        
    if candidates_p3:
        if len(candidates_p3) > 1:
            logger.warning(f"Multiple prefix matches found for {stem}. Choosing first lexicographically.")
        candidates_p3.sort()
        return str(candidates_p3[0])
        
    return None

def wait_for_file_release(path: str, codec: str = "software", max_wait_base: float = 10.0, min_size_mb: float = 0.5) -> bool:
    """
    Waits for a file to be released by the OS/Drivers using a rename probe.
    - Uses os.replace(path, path) as the definitive signal of unlock.
    - Scales max_wait based on codec (NVENC gets 2.5x).
    - Uses cause-aware logging.
    """
    import time
    abs_path = os.path.abspath(path)
    p = Path(abs_path)
    
    # 1. Determine Max Wait
    # NVENC combined with MP4 muxer often keeps file handles open longer.
    multiplier = 2.5 if codec and any(c in codec.lower() for c in ["nvenc", "h264_nvenc", "hevc_nvenc"]) else 1.0
    max_wait = max_wait_base * multiplier
    
    start_time = time.time()
    attempt = 0
    
    logger.info(f"Probing file release for: {p.name} (Max wait: {max_wait}s, Codec: {codec})")
    
    while (time.time() - start_time) < max_wait:
        attempt += 1
        if p.exists():
            try:
                # A. Basic Size Check
                size_mb = p.stat().st_size / (1024 * 1024)
                if size_mb < min_size_mb:
                    logger.debug(f"File exists but too small ({size_mb:.2f}MB) on attempt {attempt}")
                else:
                    # B. The Golden Signal: Rename Probe
                    # On Windows, os.replace only succeeds if NO handle is held.
                    os.replace(abs_path, abs_path)
                    
                    elapsed = time.time() - start_time
                    logger.info(f"File unlocked after {elapsed:.2f}s (rename-probe success) on attempt {attempt}")
                    return True
                    
            except (OSError, PermissionError) as e:
                # PermissionError means the file is still locked
                logger.debug(f"File still locked on attempt {attempt}: {e}")
        else:
            logger.debug(f"File not yet visible on attempt {attempt}")

        # Exponential Backoff (starts small)
        wait_time = min(0.1 * (1.5 ** attempt), 2.0)
        time.sleep(wait_time)
        
    elapsed = time.time() - start_time
    logger.error(f"File release timeout after {elapsed:.2f}s for {abs_path}")
    return False

def validate_output_video(path: str, codec: str = "software", min_size_mb: float = 0.5) -> bool:
    """
    Validates the generated video file using a Windows-safe rename probe.
    """
    return wait_for_file_release(path, codec=codec, min_size_mb=min_size_mb)

def safe_replace(src: str, dst: str, max_retries: int = 5, base_wait: float = 1.0) -> None:
    """
    Robustly replace a file, retrying on Access Denied errors.
    Strategies:
    1. Clear Read-Only attribute on destination.
    2. Try direct os.replace (atomic-ish).
    3. Try "Trash" method: rename dst -> dst.trash, move src -> dst, delete dst.trash.
    4. Try shutil.move (copy-delete fallback).
    """
    import time
    import shutil
    import stat
    import random
    
    src = os.path.abspath(src)
    dst = os.path.abspath(dst)
    
    def clear_readonly(path):
        if os.path.exists(path):
            try:
                os.chmod(path, stat.S_IWRITE)
            except:
                pass

    for attempt in range(1, max_retries + 1):
        try:
            # Strategy 0: Pre-flight cleanup
            clear_readonly(dst)
            
            # Strategy 1: Direct Replace
            if os.path.exists(dst):
                try:
                    os.replace(src, dst)
                    logger.info(f"File replaced successfully (Direct): {dst}")
                    return
                except (PermissionError, OSError):
                    # Strategy 2: The "Trash" Dance
                    # Useful if 'dst' is locked for deletion but allows renaming (common with AV)
                    trash_path = f"{dst}.{int(time.time())}_{random.randint(1000,9999)}.trash"
                    
                    try:
                        os.rename(dst, trash_path)
                        # If rename worked, dst is gone from its path.
                        try:
                            os.replace(src, dst)
                            logger.info(f"File replaced successfully (Trash Swap): {dst}")
                            
                            # Cleanup trash
                            try:
                                os.remove(trash_path)
                            except OSError:
                                logger.warning(f"Could not delete trash file: {trash_path}. It will remain.")
                            return
                        except Exception as e_move:
                            # Rollback!
                            os.rename(trash_path, dst)
                            raise e_move
                    except OSError:
                        # Rename failed too, fallback to wait/retry
                        pass
            else:
                # Destination doesn't exist, just move
                os.replace(src, dst)
                return

        except (PermissionError, OSError) as e:
            is_access_error = getattr(e, 'winerror', 0) in [5, 32] or isinstance(e, PermissionError)
            
            if is_access_error and attempt < max_retries:
                wait_time = base_wait * (1.5 ** (attempt - 1))
                logger.warning(f"Replace failed (Locked). Retrying {attempt}/{max_retries} in {wait_time:.2f}s...")
                time.sleep(wait_time)
            else:
                if attempt == max_retries:
                    logger.error(f"Final replace failed after {attempt} attempts: {e}")
                    # Last Ditch: shutil.move (might work if cross-device logic helps, though unlikely here)
                    try:
                        logger.info("Attempting last-ditch shutil.move...")
                        shutil.move(src, dst)
                        logger.info("shutil.move succeeded!")
                        return
                    except Exception as e_shutil:
                        logger.error(f"shutil.move also failed: {e_shutil}")
                    
                raise e
