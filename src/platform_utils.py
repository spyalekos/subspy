"""
SubsPy - Platform Utilities
Cross-platform helper functions for data directories, document paths, etc.
"""

import os
import sys
import platform


def get_platform() -> str:
    """
    Detect the current platform.
    Returns: 'android', 'windows', 'macos', or 'linux' (includes Raspberry Pi).
    """
    # Android detection
    if 'ANDROID_ROOT' in os.environ or 'ANDROID_DATA' in os.environ:
        return 'android'
    if hasattr(sys, 'getandroidapilevel'):
        return 'android'

    system = platform.system()
    if system == 'Windows':
        return 'windows'
    if system == 'Darwin':
        return 'macos'
    return 'linux'


def is_raspberry_pi() -> bool:
    """Check if running on a Raspberry Pi."""
    try:
        with open('/proc/device-tree/model', 'r') as f:
            return 'raspberry pi' in f.read().lower()
    except (FileNotFoundError, PermissionError):
        return False


def get_data_dir(app_name: str = "SubsPy") -> str:
    """
    Get the appropriate data directory for the current platform.

    - Android: FLET_APP_STORAGE_DATA
    - Windows: %APPDATA%/SubsPy
    - macOS: ~/Library/Application Support/SubsPy
    - Linux/RPi: ~ (home directory, for backward compatibility)
    """
    plat = get_platform()

    if plat == 'android':
        return os.environ.get('FLET_APP_STORAGE_DATA', os.path.expanduser('~'))

    if plat == 'windows':
        base = os.environ.get('APPDATA', os.path.expanduser('~'))
        return os.path.join(base, app_name)

    if plat == 'macos':
        return os.path.expanduser('~')

    # Linux / Raspberry Pi — keep home dir for backward compatibility
    return os.path.expanduser('~')


def get_documents_dir() -> str:
    """
    Get the appropriate directory for saving documents (PDFs, exports).

    - Android: FLET_APP_STORAGE_DATA
    - Windows: %USERPROFILE%/Downloads (fallback to home)
    - macOS/Linux: ~/Downloads (fallback to home)
    """
    plat = get_platform()

    if plat == 'android':
        return os.environ.get('FLET_APP_STORAGE_DATA', os.path.expanduser('~'))

    if plat == 'windows':
        downloads = os.path.join(
            os.environ.get('USERPROFILE', os.path.expanduser('~')),
            'Downloads'
        )
    else:
        downloads = os.path.expanduser('~/Downloads')

    if os.path.exists(downloads):
        return downloads

    return os.path.expanduser('~')


def open_file_with_default_app(filepath: str) -> None:
    """
    Open a file with the system's default application.
    Raises an exception if opening fails.
    """
    import subprocess

    plat = get_platform()

    if plat == 'windows':
        os.startfile(filepath)
    elif plat == 'macos':
        subprocess.run(['open', filepath], check=True)
    elif plat == 'android':
        # On Android, Flet handles file opening differently;
        # for now, silently skip (user sees the path in the snackbar)
        pass
    else:
        # Linux / Raspberry Pi
        subprocess.run(['xdg-open', filepath], check=True)
