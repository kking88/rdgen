#!/usr/bin/env python3
import re
import sys
from pathlib import Path


OFFICIAL_UPDATE_CHECK_URL = "https://api.rustdesk.com/version/latest"


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def find_existing_path(candidates):
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return path
    return None


def replace_literal(path: Path, old: str, new: str, label: str) -> bool:
    if not path.exists():
        print(f"[WARN] skip {label}: file not found: {path}")
        return False

    text = path.read_text(encoding="utf-8")
    if old in text:
        text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")
        print(f"[OK] {label}")
        return True
    if new in text:
        print(f"[SKIP] {label}: already patched")
        return True

    print(f"[WARN] skip {label}: pattern not found")
    return False


def replace_regex(path: Path, pattern: str, repl: str, label: str, flags=re.S) -> bool:
    if not path.exists():
        print(f"[WARN] skip {label}: file not found: {path}")
        return False

    text = path.read_text(encoding="utf-8")
    new_text, count = re.subn(pattern, repl, text, count=1, flags=flags)
    if count > 0:
        path.write_text(new_text, encoding="utf-8")
        print(f"[OK] {label}")
        return True

    print(f"[WARN] skip {label}: pattern not found")
    return False


def patch_update_check_url(update_check_url: str) -> None:
    if not update_check_url:
        print("[SKIP] custom update check url is empty")
        return

    if not re.match(r"^https?://", update_check_url):
        raise ValueError("updateCheckUrl must start with http:// or https://")

    target = find_existing_path(
        [
            "libs/hbb_common/src/lib.rs",
            "hbb_common/src/lib.rs",
        ]
    )
    if target is None:
        print("[WARN] skip update check url patch: hbb_common lib.rs not found")
        return

    replace_literal(
        target,
        OFFICIAL_UPDATE_CHECK_URL,
        update_check_url,
        "replace update check endpoint",
    )


def patch_allow_custom_client_update() -> None:
    common_rs = Path("src/common.rs")
    replace_regex(
        common_rs,
        r"(pub fn check_software_update\(\)\s*\{\s*)if is_custom_client\(\)\s*\{\s*return;\s*\}\s*",
        r"\1",
        "enable update check for custom client in src/common.rs",
    )

    replace_literal(
        Path("flutter/lib/common.dart"),
        "if (!bind.isCustomClient()) {",
        "if (true) { // RDGEN_ALLOW_CUSTOM_CLIENT_UPDATE",
        "enable update event handler for custom client in flutter/lib/common.dart",
    )

    replace_regex(
        Path("flutter/lib/desktop/pages/desktop_home_page.dart"),
        r"if\s*\(\s*!bind\.isCustomClient\(\)\s*&&\s*",
        "if (",
        "show desktop update card for custom client",
    )


def main():
    update_check_url = sys.argv[1].strip() if len(sys.argv) >= 2 else ""
    allow_custom_client_update = parse_bool(sys.argv[2]) if len(sys.argv) >= 3 else False

    print(f"updateCheckUrl={update_check_url or '<empty>'}")
    print(f"allowCustomClientUpdate={'true' if allow_custom_client_update else 'false'}")

    patch_update_check_url(update_check_url)
    if allow_custom_client_update:
        patch_allow_custom_client_update()
    else:
        print("[SKIP] allowCustomClientUpdate is false")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print(f"[ERROR] {exc}")
        raise SystemExit(1)
