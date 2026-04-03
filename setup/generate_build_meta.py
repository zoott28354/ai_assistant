import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
SETUP_DIR = ROOT_DIR / "setup"
sys.path.insert(0, str(ROOT_DIR))

from core.app_meta import (  # noqa: E402
    APP_COPYRIGHT,
    APP_NAME,
    APP_PUBLISHER,
    APP_SLUG,
    APP_URL,
    APP_VERSION,
)


def version_tuple(version: str) -> tuple[int, int, int, int]:
    parts = [int(part) for part in version.split(".")]
    while len(parts) < 4:
        parts.append(0)
    return tuple(parts[:4])


def write_version_info() -> None:
    version = version_tuple(APP_VERSION)
    content = f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={version},
    prodvers={version},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [
          StringStruct('CompanyName', '{APP_PUBLISHER}'),
          StringStruct('FileDescription', '{APP_NAME} local desktop app'),
          StringStruct('FileVersion', '{APP_VERSION}'),
          StringStruct('InternalName', '{APP_SLUG}'),
          StringStruct('LegalCopyright', '{APP_COPYRIGHT}'),
          StringStruct('OriginalFilename', '{APP_SLUG}.exe'),
          StringStruct('ProductName', '{APP_NAME}'),
          StringStruct('ProductVersion', '{APP_VERSION}'),
        ]
      )
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""
    (SETUP_DIR / "version_info.py").write_text(content, encoding="utf-8")


def write_inno_meta() -> None:
    content = f"""#define MyAppName "{APP_NAME}"
#define MyAppVersion "{APP_VERSION}"
#define MyAppPublisher "{APP_PUBLISHER}"
#define MyAppURL "{APP_URL}"
#define MyAppExeName "{APP_SLUG}.exe"
#define MyOutputBaseFilename "{APP_SLUG}_Setup_v" + MyAppVersion
"""
    (SETUP_DIR / "app_meta.iss").write_text(content, encoding="utf-8")


def main() -> None:
    os.makedirs(SETUP_DIR, exist_ok=True)
    write_version_info()
    write_inno_meta()
    print("Build metadata generated.")


if __name__ == "__main__":
    main()
