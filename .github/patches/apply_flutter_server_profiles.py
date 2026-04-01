#!/usr/bin/env python3
import base64
import json
import re
import sys
from pathlib import Path

TARGET_FILE = Path("flutter/lib/mobile/widgets/dialog.dart")

HELPER_START = "// RDGEN_SERVER_PROFILES_BEGIN"
HELPER_END = "// RDGEN_SERVER_PROFILES_END"

SETUP_START = "  // RDGEN_SERVER_PROFILES_SETUP_BEGIN"
SETUP_END = "  // RDGEN_SERVER_PROFILES_SETUP_END"

WIDGET_START = "                  // RDGEN_SERVER_PROFILES_WIDGET_BEGIN"
WIDGET_END = "                  // RDGEN_SERVER_PROFILES_WIDGET_END"

ERR_MSGS_BLOCK = """  final errMsgs = [
    idServerMsg,
    relayServerMsg,
    apiServerMsg,
  ];
"""

ID_SERVER_WIDGET_ANCHOR = """                  buildField(translate('ID Server'), idCtrl, idServerMsg.value,
                      autofocus: true),
"""


def _replace_or_insert_marked_block(text, start_marker, end_marker, block, insert_anchor=None, before_anchor=True):
    pattern = re.compile(rf"{re.escape(start_marker)}.*?{re.escape(end_marker)}", re.S)
    if pattern.search(text):
        return pattern.sub(block, text, count=1)

    if insert_anchor is None:
        raise RuntimeError(f"Could not find markers {start_marker}/{end_marker} and no insert anchor provided")

    if insert_anchor not in text:
        raise RuntimeError(f"Insert anchor not found: {insert_anchor}")

    if before_anchor:
        return text.replace(insert_anchor, f"{block}\n{insert_anchor}", 1)
    return text.replace(insert_anchor, f"{insert_anchor}\n{block}", 1)


def _sanitize_profiles(raw_profiles):
    if not isinstance(raw_profiles, list):
        raise ValueError("serverProfilesB64 payload must decode to a JSON array")

    profiles = []
    for idx, item in enumerate(raw_profiles, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"profile #{idx} must be a JSON object")

        name = str(item.get("name", "")).strip()
        id_server = str(item.get("idServer", "")).strip()
        relay_server = str(item.get("relayServer", "")).strip()
        api_server = str(item.get("apiServer", "")).strip()
        key = str(item.get("key", "")).strip()

        if not id_server:
            raise ValueError(f"profile #{idx} is missing idServer")

        profiles.append(
            {
                "name": name if name else id_server,
                "idServer": id_server,
                "relayServer": relay_server,
                "apiServer": api_server,
                "key": key,
            }
        )
    return profiles


def _build_helper_block(encoded_profiles):
    return f"""{HELPER_START}
class _RdgenServerProfile {{
  final String name;
  final String idServer;
  final String relayServer;
  final String apiServer;
  final String key;

  const _RdgenServerProfile({{
    required this.name,
    required this.idServer,
    required this.relayServer,
    required this.apiServer,
    required this.key,
  }});
}}

List<_RdgenServerProfile> _rdgenBuiltInServerProfiles() {{
  const String b64 = '{encoded_profiles}';
  if (b64.isEmpty) {{
    return const [];
  }}
  try {{
    final decoded = utf8.decode(base64Decode(b64));
    final parsed = jsonDecode(decoded);
    if (parsed is! List) {{
      return const [];
    }}
    final result = <_RdgenServerProfile>[];
    for (final item in parsed) {{
      if (item is! Map) {{
        continue;
      }}
      final idServer = (item['idServer'] ?? '').toString().trim();
      if (idServer.isEmpty) {{
        continue;
      }}
      final name = (item['name'] ?? '').toString().trim();
      result.add(_RdgenServerProfile(
        name: name.isEmpty ? idServer : name,
        idServer: idServer,
        relayServer: (item['relayServer'] ?? '').toString().trim(),
        apiServer: (item['apiServer'] ?? '').toString().trim(),
        key: (item['key'] ?? '').toString().trim(),
      ));
    }}
    return result;
  }} catch (_) {{
    return const [];
  }}
}}
{HELPER_END}"""


def _build_setup_block():
    return f"""{SETUP_START}
  final builtInProfiles = _rdgenBuiltInServerProfiles();
  String? selectedProfileName;
  if (builtInProfiles.isNotEmpty) {{
    _RdgenServerProfile? matchedProfile;
    for (final profile in builtInProfiles) {{
      if (profile.idServer == idCtrl.text.trim()) {{
        matchedProfile = profile;
        break;
      }}
    }}
    final initialProfile = matchedProfile ?? builtInProfiles.first;
    selectedProfileName = initialProfile.name;
    if (idCtrl.text.trim().isEmpty &&
        relayCtrl.text.trim().isEmpty &&
        apiCtrl.text.trim().isEmpty &&
        keyCtrl.text.trim().isEmpty) {{
      idCtrl.text = initialProfile.idServer;
      relayCtrl.text = initialProfile.relayServer;
      apiCtrl.text = initialProfile.apiServer;
      keyCtrl.text = initialProfile.key;
    }}
  }}
{SETUP_END}"""


def _build_widget_block():
    return f"""{WIDGET_START}
                  if (builtInProfiles.isNotEmpty) ...[
                    DropdownButtonFormField<String>(
                      value: selectedProfileName,
                      decoration: InputDecoration(
                        labelText: 'Built-in server profile',
                      ),
                      isExpanded: true,
                      items: builtInProfiles
                          .map((profile) => DropdownMenuItem<String>(
                                value: profile.name,
                                child: Text(profile.name),
                              ))
                          .toList(),
                      onChanged: isInProgress
                          ? null
                          : (value) {{
                              if (value == null) return;
                              _RdgenServerProfile? selected;
                              for (final profile in builtInProfiles) {{
                                if (profile.name == value) {{
                                  selected = profile;
                                  break;
                                }}
                              }}
                              final selectedProfile = selected;
                              if (selectedProfile == null) return;
                              setState(() {{
                                selectedProfileName = selectedProfile.name;
                                idCtrl.text = selectedProfile.idServer;
                                relayCtrl.text = selectedProfile.relayServer;
                                apiCtrl.text = selectedProfile.apiServer;
                                keyCtrl.text = selectedProfile.key;
                              }});
                            }},
                    ),
                    SizedBox(height: 8),
                  ],
{WIDGET_END}"""


def main():
    if len(sys.argv) < 2:
        print("Usage: apply_flutter_server_profiles.py <serverProfilesB64>")
        return 1

    encoded_payload = sys.argv[1].strip()
    if not encoded_payload:
        print("serverProfilesB64 is empty, skip patch")
        return 0

    try:
        decoded_payload = base64.b64decode(encoded_payload).decode("utf-8")
        raw_profiles = json.loads(decoded_payload)
        profiles = _sanitize_profiles(raw_profiles)
    except Exception as exc:
        print(f"Invalid server profiles payload: {exc}")
        return 1

    if not profiles:
        print("No valid profiles after sanitize, skip patch")
        return 0

    encoded_profiles = base64.b64encode(
        json.dumps(profiles, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).decode("ascii")

    if not TARGET_FILE.exists():
        print(f"Target file not found: {TARGET_FILE}")
        return 1

    text = TARGET_FILE.read_text(encoding="utf-8")

    helper_block = _build_helper_block(encoded_profiles)
    setup_block = _build_setup_block()
    widget_block = _build_widget_block()

    text = _replace_or_insert_marked_block(
        text,
        HELPER_START,
        HELPER_END,
        helper_block,
        insert_anchor="void _showSuccess() {",
        before_anchor=True,
    )

    text = _replace_or_insert_marked_block(
        text,
        SETUP_START,
        SETUP_END,
        setup_block,
        insert_anchor=ERR_MSGS_BLOCK,
        before_anchor=False,
    )

    text = _replace_or_insert_marked_block(
        text,
        WIDGET_START,
        WIDGET_END,
        widget_block,
        insert_anchor=ID_SERVER_WIDGET_ANCHOR,
        before_anchor=True,
    )

    TARGET_FILE.write_text(text, encoding="utf-8")
    print("Applied built-in server profile dropdown patch to flutter server dialog")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
