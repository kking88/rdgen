import io
from pathlib import Path
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.core.files.base import ContentFile
import os
import re
import requests
import base64
import json
import uuid
import pyzipper
from django.conf import settings as _settings
from django.db.models import Q
from .forms import GenerateForm
from .models import GithubRun
from PIL import Image
from urllib.parse import quote

def yn(flag: bool) -> str:
    return 'Y' if flag else 'N'

def apply_manual_settings(raw_text, target):
    for line in raw_text.splitlines():
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        if "=" not in text:
            continue
        k, value = text.split("=", 1)
        key = k.strip()
        val = value.strip()
        if key:
            target[key] = val

def trim_trailing_slash(value):
    text = value.strip()
    while text.endswith("/"):
        text = text[:-1]
    return text

def sanitize_server_profiles(raw_text):
    text = raw_text.strip()
    if not text:
        return []
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Server profiles JSON invalid: {exc.msg}") from exc

    if not isinstance(data, list):
        raise ValueError("Server profiles JSON must be a JSON array")

    profiles = []
    for idx, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Server profile #{idx} must be an object")

        name = str(item.get("name", "")).strip() or f"Server {idx}"
        id_server = trim_trailing_slash(str(item.get("idServer", "")).strip())
        relay_server = trim_trailing_slash(str(item.get("relayServer", "")).strip())
        api_server = trim_trailing_slash(str(item.get("apiServer", "")).strip())
        key = str(item.get("key", "")).strip()

        if not id_server:
            raise ValueError(f"Server profile #{idx} is missing idServer")

        profiles.append({
            "name": name,
            "idServer": id_server,
            "relayServer": relay_server,
            "apiServer": api_server,
            "key": key,
        })
    return profiles

def encode_server_profiles_b64(profiles):
    if not profiles:
        return ""
    raw = json.dumps(profiles, ensure_ascii=False, separators=(",", ":"))
    return base64.b64encode(raw.encode("utf-8")).decode("ascii")

def generator_view(request):
    if request.method == 'POST':
        form = GenerateForm(request.POST, request.FILES)
        if form.is_valid():
            platform = form.cleaned_data['platform']
            version = form.cleaned_data['version']
            delayFix = form.cleaned_data['delayFix']
            cycleMonitor = form.cleaned_data['cycleMonitor']
            xOffline = form.cleaned_data['xOffline']
            hidecm = form.cleaned_data['hidecm']
            removeNewVersionNotif = form.cleaned_data['removeNewVersionNotif']
            server = form.cleaned_data['serverIP']
            key = form.cleaned_data['key']
            apiServer = form.cleaned_data['apiServer']
            relayServer = form.cleaned_data['relayServer'].strip()
            iceServers = form.cleaned_data['iceServers'].strip()
            customRendezvousServer = form.cleaned_data['customRendezvousServer'].strip()
            proxyUrl = form.cleaned_data['proxyUrl'].strip()
            proxyUsername = form.cleaned_data['proxyUsername'].strip()
            proxyPassword = form.cleaned_data['proxyPassword'].strip()
            urlLink = form.cleaned_data['urlLink']
            downloadLink = form.cleaned_data['downloadLink']
            updateCheckUrl = form.cleaned_data['updateCheckUrl'].strip()
            allowCustomClientUpdate = form.cleaned_data['allowCustomClientUpdate']
            serverProfilesRaw = form.cleaned_data['serverProfilesJson']
            try:
                serverProfiles = sanitize_server_profiles(serverProfilesRaw)
            except ValueError as exc:
                form.add_error('serverProfilesJson', str(exc))
                return render(request, 'generator.html', {'form': form})
            if updateCheckUrl and not (
                updateCheckUrl.startswith('http://') or updateCheckUrl.startswith('https://')
            ):
                form.add_error('updateCheckUrl', 'Update check API URL must start with http:// or https://')
                return render(request, 'generator.html', {'form': form})
            primaryProfile = serverProfiles[0] if serverProfiles else None
            if not server and primaryProfile:
                server = primaryProfile['idServer']
            if not key and primaryProfile and primaryProfile['key']:
                key = primaryProfile['key']
            if not apiServer and primaryProfile and primaryProfile['apiServer']:
                apiServer = primaryProfile['apiServer']
            if not server:
                server = 'rs-ny.rustdesk.com' #default rustdesk server
            if not key:
                key = 'OeVuKk5nlHiXp+APNn0Y3pC1Iwpwn44JGqrQCsWqmBw=' #default rustdesk key
            if not apiServer:
                apiServer = server+":21114"
            serverProfilesB64 = encode_server_profiles_b64(serverProfiles)
            if not urlLink:
                urlLink = "https://rustdesk.com"
            if not downloadLink:
                downloadLink = "https://rustdesk.com/download"
            direction = form.cleaned_data['direction']
            installation = form.cleaned_data['installation']
            settings = form.cleaned_data['settings']
            appname = form.cleaned_data['appname']
            if not appname:
                appname = "rustdesk"
            filename = form.cleaned_data['exename']
            compname = form.cleaned_data['compname']
            if not compname:
                compname = "Purslane Ltd"
            androidappid = form.cleaned_data['androidappid']
            if not androidappid:
                androidappid = "com.carriez.flutter_hbb"
            compname = compname.replace("&","\\&")
            permPass = form.cleaned_data['permanentPassword']
            theme = form.cleaned_data['theme']
            themeDorO = form.cleaned_data['themeDorO']
            #runasadmin = form.cleaned_data['runasadmin']
            passApproveMode = form.cleaned_data['passApproveMode']
            denyLan = form.cleaned_data['denyLan']
            enableDirectIP = form.cleaned_data['enableDirectIP']
            directAccessPort = form.cleaned_data['directAccessPort'].strip()
            ipWhitelist = form.cleaned_data['ipWhitelist'].strip()
            forceAlwaysRelay = form.cleaned_data['forceAlwaysRelay']
            allowWebSocket = form.cleaned_data['allowWebSocket']
            disableUDP = form.cleaned_data['disableUDP']
            allowInsecureTLSFallback = form.cleaned_data['allowInsecureTLSFallback']
            autoClose = form.cleaned_data['autoClose']
            autoDisconnectTimeout = form.cleaned_data['autoDisconnectTimeout'].strip()
            allowAutoUpdate = form.cleaned_data['allowAutoUpdate']
            allowNumericOneTimePassword = form.cleaned_data['allowNumericOneTimePassword']
            allowOnlyConnWindowOpen = form.cleaned_data['allowOnlyConnWindowOpen']
            allowAutoRecordIncoming = form.cleaned_data['allowAutoRecordIncoming']
            allowAutoRecordOutgoing = form.cleaned_data['allowAutoRecordOutgoing']
            temporaryPasswordLength = form.cleaned_data['temporaryPasswordLength'].strip()
            enableAbr = form.cleaned_data['enableAbr']
            allowAlwaysSoftwareRender = form.cleaned_data['allowAlwaysSoftwareRender']
            allowLinuxHeadless = form.cleaned_data['allowLinuxHeadless']
            enableHwcodec = form.cleaned_data['enableHwcodec']
            removeSetupServerTip = form.cleaned_data['removeSetupServerTip']
            permissionsDorO = form.cleaned_data['permissionsDorO']
            policyDorO = form.cleaned_data['policyDorO']
            permissionsType = form.cleaned_data['permissionsType']
            enableKeyboard = form.cleaned_data['enableKeyboard']
            enableClipboard = form.cleaned_data['enableClipboard']
            enableFileTransfer = form.cleaned_data['enableFileTransfer']
            enableAudio = form.cleaned_data['enableAudio']
            enableTCP = form.cleaned_data['enableTCP']
            enableRemoteRestart = form.cleaned_data['enableRemoteRestart']
            enableRecording = form.cleaned_data['enableRecording']
            enableBlockingInput = form.cleaned_data['enableBlockingInput']
            enableRemoteModi = form.cleaned_data['enableRemoteModi']
            removeWallpaper = form.cleaned_data['removeWallpaper']
            defaultManual = form.cleaned_data['defaultManual']
            overrideManual = form.cleaned_data['overrideManual']
            enablePrinter = form.cleaned_data['enablePrinter']
            enableCamera = form.cleaned_data['enableCamera']
            enableTerminal = form.cleaned_data['enableTerminal']
            fileTransferMaxFiles = form.cleaned_data['fileTransferMaxFiles'].strip()
            defaultConnectPassword = form.cleaned_data['defaultConnectPassword'].strip()
            enableDirectxCapture = form.cleaned_data['enableDirectxCapture']
            enableTrustedDevices = form.cleaned_data['enableTrustedDevices']
            presetAddressBookName = form.cleaned_data['presetAddressBookName'].strip()
            presetAddressBookTag = form.cleaned_data['presetAddressBookTag'].strip()
            presetAddressBookAlias = form.cleaned_data['presetAddressBookAlias'].strip()
            presetAddressBookPassword = form.cleaned_data['presetAddressBookPassword'].strip()
            presetAddressBookNote = form.cleaned_data['presetAddressBookNote'].strip()
            presetDeviceUsername = form.cleaned_data['presetDeviceUsername'].strip()
            presetDeviceName = form.cleaned_data['presetDeviceName'].strip()
            presetNote = form.cleaned_data['presetNote'].strip()
            displayName = form.cleaned_data['displayName'].strip()
            avatar = form.cleaned_data['avatar'].strip()
            presetDeviceGroupName = form.cleaned_data['presetDeviceGroupName'].strip()
            presetUserName = form.cleaned_data['presetUserName'].strip()
            presetStrategyName = form.cleaned_data['presetStrategyName'].strip()
            hideServerSettings = form.cleaned_data['hideServerSettings']
            hideSecuritySettings = form.cleaned_data['hideSecuritySettings']
            hideNetworkSettings = form.cleaned_data['hideNetworkSettings']
            hideProxySettings = form.cleaned_data['hideProxySettings']
            hideWebSocketSettings = form.cleaned_data['hideWebSocketSettings']
            hideRemotePrinterSettings = form.cleaned_data['hideRemotePrinterSettings']
            hideStopService = form.cleaned_data['hideStopService']
            hideUsernameOnCard = form.cleaned_data['hideUsernameOnCard']
            hideHelpCards = form.cleaned_data['hideHelpCards']
            hideTray = form.cleaned_data['hideTray']
            oneWayClipboardRedirection = form.cleaned_data['oneWayClipboardRedirection']
            allowLogonScreenPassword = form.cleaned_data['allowLogonScreenPassword']
            oneWayFileTransfer = form.cleaned_data['oneWayFileTransfer']
            allowHttps21114 = form.cleaned_data['allowHttps21114']
            useRawTcpForApi = form.cleaned_data['useRawTcpForApi']
            allowHostnameAsID = form.cleaned_data['allowHostnameAsID']
            registerDevice = form.cleaned_data['registerDevice']
            hidePoweredByMe = form.cleaned_data['hidePoweredByMe']
            mainWindowAlwaysOnTop = form.cleaned_data['mainWindowAlwaysOnTop']
            disableChangePermanentPassword = form.cleaned_data['disableChangePermanentPassword']
            disableChangeID = form.cleaned_data['disableChangeID']
            disableUnlockPin = form.cleaned_data['disableUnlockPin']
            removePresetPasswordWarning = form.cleaned_data['removePresetPasswordWarning']

            if all(char.isascii() for char in filename):
                filename = re.sub(r'[^\w\s-]', '_', filename).strip()
                filename = filename.replace(" ","_")
            else:
                filename = "rustdesk"
            if not all(char.isascii() for char in appname):
                appname = "rustdesk"
            myuuid = str(uuid.uuid4())
            configured_genurl = str(getattr(_settings, "GENURL", "")).strip()
            if configured_genurl:
                full_url = configured_genurl.rstrip("/")
            else:
                protocol = _settings.PROTOCOL
                host = request.get_host()
                full_url = f"{protocol}://{host}"
            try:
                iconfile = form.cleaned_data.get('iconfile')
                if not iconfile:
                    iconfile = form.cleaned_data.get('iconbase64')
                iconlink_url, iconlink_uuid, iconlink_file = save_png(iconfile,myuuid,full_url,"icon.png")
            except:
                print("failed to get icon, using default")
                iconlink_url = "false"
                iconlink_uuid = "false"
                iconlink_file = "false"
            try:
                logofile = form.cleaned_data.get('logofile')
                if not logofile:
                    logofile = form.cleaned_data.get('logobase64')
                logolink_url, logolink_uuid, logolink_file = save_png(logofile,myuuid,full_url,"logo.png")
            except:
                print("failed to get logo")
                logolink_url = "false"
                logolink_uuid = "false"
                logolink_file = "false"

            ###create the custom.txt json here and send in as inputs below
            decodedCustom = {}
            if direction != "Both":
                decodedCustom['conn-type'] = direction
            if installation == "installationN":
                decodedCustom['disable-installation'] = 'Y'
            if settings == "settingsN":
                decodedCustom['disable-settings'] = 'Y'
            if appname.upper != "rustdesk".upper and appname != "":
                decodedCustom['app-name'] = appname
            decodedCustom['override-settings'] = {}
            decodedCustom['default-settings'] = {}
            if permPass != "":
                decodedCustom['password'] = permPass
            if theme != "system":
                if themeDorO == "default":
                    if platform == "windows-x86":
                        decodedCustom['default-settings']['allow-darktheme'] = 'Y' if theme == "dark" else 'N'
                    else:
                        decodedCustom['default-settings']['theme'] = theme
                elif themeDorO == "override":
                    if platform == "windows-x86":
                        decodedCustom['override-settings']['allow-darktheme'] = 'Y' if theme == "dark" else 'N'
                    else:
                        decodedCustom['override-settings']['theme'] = theme
            decodedCustom['enable-lan-discovery'] = 'N' if denyLan else 'Y'
            if permissionsDorO == "default":
                decodedCustom['default-settings']['access-mode'] = permissionsType
                decodedCustom['default-settings']['enable-keyboard'] = 'Y' if enableKeyboard else 'N'
                decodedCustom['default-settings']['enable-clipboard'] = 'Y' if enableClipboard else 'N'
                decodedCustom['default-settings']['enable-file-transfer'] = 'Y' if enableFileTransfer else 'N'
                decodedCustom['default-settings']['enable-audio'] = 'Y' if enableAudio else 'N'
                decodedCustom['default-settings']['enable-tunnel'] = 'Y' if enableTCP else 'N'
                decodedCustom['default-settings']['enable-remote-restart'] = 'Y' if enableRemoteRestart else 'N'
                decodedCustom['default-settings']['enable-record-session'] = 'Y' if enableRecording else 'N'
                decodedCustom['default-settings']['enable-block-input'] = 'Y' if enableBlockingInput else 'N'
                decodedCustom['default-settings']['allow-remote-config-modification'] = 'Y' if enableRemoteModi else 'N'
                decodedCustom['default-settings']['direct-server'] = 'Y' if enableDirectIP else 'N'
                decodedCustom['default-settings']['verification-method'] = 'use-permanent-password' if hidecm else 'use-both-passwords'
                decodedCustom['default-settings']['approve-mode'] = passApproveMode
                decodedCustom['default-settings']['allow-hide-cm'] = 'Y' if hidecm else 'N'
                decodedCustom['default-settings']['allow-remove-wallpaper'] = 'Y' if removeWallpaper else 'N'
                decodedCustom['default-settings']['enable-remote-printer'] = 'Y' if enablePrinter else 'N'
                decodedCustom['default-settings']['enable-camera'] = 'Y' if enableCamera else 'N'
                decodedCustom['default-settings']['enable-terminal'] = 'Y' if enableTerminal else 'N'
            else:
                decodedCustom['override-settings']['access-mode'] = permissionsType
                decodedCustom['override-settings']['enable-keyboard'] = 'Y' if enableKeyboard else 'N'
                decodedCustom['override-settings']['enable-clipboard'] = 'Y' if enableClipboard else 'N'
                decodedCustom['override-settings']['enable-file-transfer'] = 'Y' if enableFileTransfer else 'N'
                decodedCustom['override-settings']['enable-audio'] = 'Y' if enableAudio else 'N'
                decodedCustom['override-settings']['enable-tunnel'] = 'Y' if enableTCP else 'N'
                decodedCustom['override-settings']['enable-remote-restart'] = 'Y' if enableRemoteRestart else 'N'
                decodedCustom['override-settings']['enable-record-session'] = 'Y' if enableRecording else 'N'
                decodedCustom['override-settings']['enable-block-input'] = 'Y' if enableBlockingInput else 'N'
                decodedCustom['override-settings']['allow-remote-config-modification'] = 'Y' if enableRemoteModi else 'N'
                decodedCustom['override-settings']['direct-server'] = 'Y' if enableDirectIP else 'N'
                decodedCustom['override-settings']['verification-method'] = 'use-permanent-password' if hidecm else 'use-both-passwords'
                decodedCustom['override-settings']['approve-mode'] = passApproveMode
                decodedCustom['override-settings']['allow-hide-cm'] = 'Y' if hidecm else 'N'
                decodedCustom['override-settings']['allow-remove-wallpaper'] = 'Y' if removeWallpaper else 'N'
                decodedCustom['override-settings']['enable-remote-printer'] = 'Y' if enablePrinter else 'N'
                decodedCustom['override-settings']['enable-camera'] = 'Y' if enableCamera else 'N'
                decodedCustom['override-settings']['enable-terminal'] = 'Y' if enableTerminal else 'N'

            policy_target = decodedCustom['default-settings'] if policyDorO == "default" else decodedCustom['override-settings']
            policy_target['allow-websocket'] = yn(allowWebSocket)
            policy_target['disable-udp'] = yn(disableUDP)
            policy_target['allow-insecure-tls-fallback'] = yn(allowInsecureTLSFallback)
            policy_target['allow-auto-disconnect'] = yn(autoClose)
            policy_target['allow-auto-update'] = yn(allowAutoUpdate)
            policy_target['allow-numeric-one-time-password'] = yn(allowNumericOneTimePassword)
            policy_target['allow-only-conn-window-open'] = yn(allowOnlyConnWindowOpen)
            policy_target['allow-auto-record-incoming'] = yn(allowAutoRecordIncoming)
            policy_target['allow-auto-record-outgoing'] = yn(allowAutoRecordOutgoing)
            policy_target['enable-abr'] = yn(enableAbr)
            policy_target['allow-always-software-render'] = yn(allowAlwaysSoftwareRender)
            policy_target['allow-linux-headless'] = yn(allowLinuxHeadless)
            policy_target['enable-hwcodec'] = yn(enableHwcodec)
            policy_target['enable-directx-capture'] = yn(enableDirectxCapture)
            policy_target['enable-trusted-devices'] = yn(enableTrustedDevices)
            policy_target['force-always-relay'] = yn(forceAlwaysRelay)
            policy_target['hide-server-settings'] = yn(hideServerSettings)
            policy_target['hide-security-settings'] = yn(hideSecuritySettings)
            policy_target['hide-network-settings'] = yn(hideNetworkSettings)
            policy_target['hide-proxy-settings'] = yn(hideProxySettings)
            policy_target['hide-websocket-settings'] = yn(hideWebSocketSettings)
            policy_target['hide-remote-printer-settings'] = yn(hideRemotePrinterSettings)
            policy_target['hide-stop-service'] = yn(hideStopService)
            policy_target['hide-username-on-card'] = yn(hideUsernameOnCard)
            policy_target['hide-help-cards'] = yn(hideHelpCards)
            policy_target['hide-tray'] = yn(hideTray)
            policy_target['one-way-clipboard-redirection'] = yn(oneWayClipboardRedirection)
            policy_target['allow-logon-screen-password'] = yn(allowLogonScreenPassword)
            policy_target['one-way-file-transfer'] = yn(oneWayFileTransfer)
            policy_target['allow-https-21114'] = yn(allowHttps21114)
            policy_target['use-raw-tcp-for-api'] = yn(useRawTcpForApi)
            policy_target['allow-hostname-as-id'] = yn(allowHostnameAsID)
            policy_target['register-device'] = yn(registerDevice)
            policy_target['hide-powered-by-me'] = yn(hidePoweredByMe)
            policy_target['main-window-always-on-top'] = yn(mainWindowAlwaysOnTop)
            policy_target['disable-change-permanent-password'] = yn(disableChangePermanentPassword)
            policy_target['disable-change-id'] = yn(disableChangeID)
            policy_target['disable-unlock-pin'] = yn(disableUnlockPin)
            policy_target['remove-preset-password-warning'] = yn(removePresetPasswordWarning)
            if apiServer:
                policy_target['api-server'] = apiServer
            if relayServer:
                policy_target['relay-server'] = relayServer
            if iceServers:
                policy_target['ice-servers'] = iceServers
            if customRendezvousServer:
                policy_target['custom-rendezvous-server'] = customRendezvousServer
            if proxyUrl:
                policy_target['proxy-url'] = proxyUrl
            if proxyUsername:
                policy_target['proxy-username'] = proxyUsername
            if proxyPassword:
                policy_target['proxy-password'] = proxyPassword
            if presetAddressBookName:
                policy_target['preset-address-book-name'] = presetAddressBookName
            if presetAddressBookTag:
                policy_target['preset-address-book-tag'] = presetAddressBookTag
            if presetAddressBookAlias:
                policy_target['preset-address-book-alias'] = presetAddressBookAlias
            if presetAddressBookPassword:
                policy_target['preset-address-book-password'] = presetAddressBookPassword
            if presetAddressBookNote:
                policy_target['preset-address-book-note'] = presetAddressBookNote
            if presetDeviceUsername:
                policy_target['preset-device-username'] = presetDeviceUsername
            if presetDeviceName:
                policy_target['preset-device-name'] = presetDeviceName
            if presetNote:
                policy_target['preset-note'] = presetNote
            if displayName:
                policy_target['display-name'] = displayName
            if avatar:
                policy_target['avatar'] = avatar
            if presetDeviceGroupName:
                policy_target['preset-device-group-name'] = presetDeviceGroupName
            if presetUserName:
                policy_target['preset-user-name'] = presetUserName
            if presetStrategyName:
                policy_target['preset-strategy-name'] = presetStrategyName

            if directAccessPort.isdigit():
                policy_target['direct-access-port'] = directAccessPort
            if autoDisconnectTimeout.isdigit():
                policy_target['auto-disconnect-timeout'] = autoDisconnectTimeout
            if temporaryPasswordLength.isdigit():
                policy_target['temporary-password-length'] = temporaryPasswordLength
            if fileTransferMaxFiles.isdigit():
                policy_target['file-transfer-max-files'] = fileTransferMaxFiles
            if defaultConnectPassword:
                policy_target['default-connect-password'] = defaultConnectPassword
            if ipWhitelist:
                whitelist_items = []
                for item in re.split(r'[\n,;]+', ipWhitelist):
                    text = item.strip()
                    if text:
                        whitelist_items.append(text)
                if whitelist_items:
                    policy_target['whitelist'] = ",".join(whitelist_items)

            apply_manual_settings(defaultManual, decodedCustom['default-settings'])
            apply_manual_settings(overrideManual, decodedCustom['override-settings'])
            
            decodedCustomJson = json.dumps(decodedCustom)

            string_bytes = decodedCustomJson.encode("ascii")
            base64_bytes = base64.b64encode(string_bytes)
            encodedCustom = base64_bytes.decode("ascii")

            # #github limits inputs to 10, so lump extras into one with json
            # extras = {}
            # extras['genurl'] = _settings.GENURL
            # #extras['runasadmin'] = runasadmin
            # extras['urlLink'] = urlLink
            # extras['downloadLink'] = downloadLink
            # extras['delayFix'] = 'true' if delayFix else 'false'
            # extras['rdgen'] = 'true'
            # extras['cycleMonitor'] = 'true' if cycleMonitor else 'false'
            # extras['xOffline'] = 'true' if xOffline else 'false'
            # extras['removeNewVersionNotif'] = 'true' if removeNewVersionNotif else 'false'
            # extras['compname'] = compname
            # extras['androidappid'] = androidappid
            # extra_input = json.dumps(extras)

            ####from here run the github action, we need user, repo, access token.
            if platform == 'windows':
                url = 'https://api.github.com/repos/'+_settings.GHUSER+'/'+_settings.REPONAME+'/actions/workflows/generator-windows.yml/dispatches'
            if platform == 'windows-x86':
                url = 'https://api.github.com/repos/'+_settings.GHUSER+'/'+_settings.REPONAME+'/actions/workflows/generator-windows-x86.yml/dispatches'
            elif platform == 'linux':
                url = 'https://api.github.com/repos/'+_settings.GHUSER+'/'+_settings.REPONAME+'/actions/workflows/generator-linux.yml/dispatches'
            elif platform == 'android':
                url = 'https://api.github.com/repos/'+_settings.GHUSER+'/'+_settings.REPONAME+'/actions/workflows/generator-android.yml/dispatches'
            elif platform == 'macos':
                url = 'https://api.github.com/repos/'+_settings.GHUSER+'/'+_settings.REPONAME+'/actions/workflows/generator-macos.yml/dispatches'
            else:
                url = 'https://api.github.com/repos/'+_settings.GHUSER+'/'+_settings.REPONAME+'/actions/workflows/generator-windows.yml/dispatches'

            #url = 'https://api.github.com/repos/'+_settings.GHUSER+'/rustdesk/actions/workflows/test.yml/dispatches'  
            inputs_raw = {
                "server":server,
                "key":key,
                "apiServer":apiServer,
                "custom":encodedCustom,
                "uuid":myuuid,
                "iconlink_url":iconlink_url,
                "iconlink_uuid":iconlink_uuid,
                "iconlink_file":iconlink_file,
                "logolink_url":logolink_url,
                "logolink_uuid":logolink_uuid,
                "logolink_file":logolink_file,
                "appname":appname,
                "genurl":_settings.GENURL,
                "urlLink":urlLink,
                "downloadLink":downloadLink,
                "updateCheckUrl": updateCheckUrl,
                "allowCustomClientUpdate": 'true' if allowCustomClientUpdate else 'false',
                "delayFix": 'true' if delayFix else 'false',
                "rdgen":'true',
                "cycleMonitor": 'true' if cycleMonitor else 'false',
                "xOffline": 'true' if xOffline else 'false',
                "removeNewVersionNotif": 'true' if removeNewVersionNotif else 'false',
                "removeSetupServerTip": 'true' if removeSetupServerTip else 'false',
                "compname": compname,
                "androidappid":androidappid,
                "filename":filename,
                "serverProfilesB64": serverProfilesB64
            }

            temp_json_path = f"data_{uuid.uuid4()}.json"
            zip_filename = f"secrets_{uuid.uuid4()}.zip"
            zip_path = "temp_zips/%s" % (zip_filename)
            Path("temp_zips").mkdir(parents=True, exist_ok=True)

            with open(temp_json_path, "w") as f:
                json.dump(inputs_raw, f)

            with pyzipper.AESZipFile(zip_path, 'w', compression=pyzipper.ZIP_LZMA, encryption=pyzipper.WZ_AES) as zf:
                zf.setpassword(_settings.ZIP_PASSWORD.encode())
                zf.write(temp_json_path, arcname="secrets.json")

            # 4. Cleanup the plain JSON file immediately
            if os.path.exists(temp_json_path):
                os.remove(temp_json_path)

            zipJson = {}
            zipJson['url'] = full_url
            zipJson['file'] = zip_filename

            zip_url = json.dumps(zipJson)
            with open(zip_path, "rb") as zip_file:
                zip_data = base64.b64encode(zip_file.read()).decode("ascii")

            data = {
                "ref":_settings.GHBRANCH,
                "inputs":{
                    "version":version,
                    "zip_url":zip_url,
                    "zip_data":zip_data
                }
            } 
            #print(data)
            headers = {
                'Accept':  'application/vnd.github+json',
                'Content-Type': 'application/json',
                'Authorization': 'Bearer '+_settings.GHBEARER,
                'X-GitHub-Api-Version': '2022-11-28'
            }
            create_github_run(myuuid)
            response = requests.post(url, json=data, headers=headers)
            print(response)
            if response.status_code == 204 or response.status_code == 200:
                return render(request, 'waiting.html', {'filename':filename, 'uuid':myuuid, 'status':"Starting generator...please wait", 'platform':platform})
            else:
                return JsonResponse({"error": "Something went wrong"})
    else:
        form = GenerateForm()
    #return render(request, 'maintenance.html')
    return render(request, 'generator.html', {'form': form})


def check_for_file(request):
    filename = request.GET['filename']
    uuid = request.GET['uuid']
    platform = request.GET['platform']
    gh_run = GithubRun.objects.filter(Q(uuid=uuid)).first()
    status = gh_run.status

    #if file_exists:
    if status == "Success":
        return render(request, 'generated.html', {'filename': filename, 'uuid':uuid, 'platform':platform})
    else:
        return render(request, 'waiting.html', {'filename':filename, 'uuid':uuid, 'status':status, 'platform':platform})

def download(request):
    filename = request.GET['filename']
    uuid = request.GET['uuid']
    #filename = filename+".exe"
    file_path = os.path.join('exe',uuid,filename)
    with open(file_path, 'rb') as file:
        response = HttpResponse(file, headers={
            'Content-Type': 'application/vnd.microsoft.portable-executable',
            'Content-Disposition': f'attachment; filename="{filename}"'
        })

    return response

def get_png(request):
    filename = request.GET['filename']
    uuid = request.GET['uuid']
    #filename = filename+".exe"
    file_path = os.path.join('png',uuid,filename)
    with open(file_path, 'rb') as file:
        response = HttpResponse(file, headers={
            'Content-Type': 'application/vnd.microsoft.portable-executable',
            'Content-Disposition': f'attachment; filename="{filename}"'
        })

    return response

def create_github_run(myuuid):
    new_github_run = GithubRun(
        uuid=myuuid,
        status="Starting generator...please wait"
    )
    new_github_run.save()

def update_github_run(request):
    data = json.loads(request.body)
    myuuid = data.get('uuid')
    mystatus = data.get('status')
    GithubRun.objects.filter(Q(uuid=myuuid)).update(status=mystatus)
    return HttpResponse('')

def resize_and_encode_icon(imagefile):
    maxWidth = 200
    try:
        with io.BytesIO() as image_buffer:
            for chunk in imagefile.chunks():
                image_buffer.write(chunk)
            image_buffer.seek(0)

            img = Image.open(image_buffer)
            imgcopy = img.copy()
    except (IOError, OSError):
        raise ValueError("Uploaded file is not a valid image format.")

    # Check if resizing is necessary
    if img.size[0] <= maxWidth:
        with io.BytesIO() as image_buffer:
            imgcopy.save(image_buffer, format=imagefile.content_type.split('/')[1])
            image_buffer.seek(0)
            return_image = ContentFile(image_buffer.read(), name=imagefile.name)
        return base64.b64encode(return_image.read())

    # Calculate resized height based on aspect ratio
    wpercent = (maxWidth / float(img.size[0]))
    hsize = int((float(img.size[1]) * float(wpercent)))

    # Resize the image while maintaining aspect ratio using LANCZOS resampling
    imgcopy = imgcopy.resize((maxWidth, hsize), Image.Resampling.LANCZOS)

    with io.BytesIO() as resized_image_buffer:
        imgcopy.save(resized_image_buffer, format=imagefile.content_type.split('/')[1])
        resized_image_buffer.seek(0)

        resized_imagefile = ContentFile(resized_image_buffer.read(), name=imagefile.name)

    # Return the Base64 encoded representation of the resized image
    resized64 = base64.b64encode(resized_imagefile.read())
    #print(resized64)
    return resized64
 
#the following is used when accessed from an external source, like the rustdesk api server
def startgh(request):
    #print(request)
    data_ = json.loads(request.body)
    ####from here run the github action, we need user, repo, access token.
    url = 'https://api.github.com/repos/'+_settings.GHUSER+'/'+_settings.REPONAME+'/actions/workflows/generator-'+data_.get('platform')+'.yml/dispatches'  
    data = {
        "ref": _settings.GHBRANCH,
        "inputs":{
            "server":data_.get('server'),
            "key":data_.get('key'),
            "apiServer":data_.get('apiServer'),
            "custom":data_.get('custom'),
            "uuid":data_.get('uuid'),
            "iconlink":data_.get('iconlink'),
            "logolink":data_.get('logolink'),
            "appname":data_.get('appname'),
            "extras":data_.get('extras'),
            "filename":data_.get('filename')
        }
    } 
    headers = {
        'Accept':  'application/vnd.github+json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer '+_settings.GHBEARER,
        'X-GitHub-Api-Version': '2022-11-28'
    }
    response = requests.post(url, json=data, headers=headers)
    print(response)
    return HttpResponse(status=204)

def save_png(file, uuid, domain, name):
    file_save_path = "png/%s/%s" % (uuid, name)
    Path("png/%s" % uuid).mkdir(parents=True, exist_ok=True)

    if isinstance(file, str):  # Check if it's a base64 string
        try:
            header, encoded = file.split(';base64,')
            decoded_img = base64.b64decode(encoded)
            file = ContentFile(decoded_img, name=name) # Create a file-like object
        except ValueError:
            print("Invalid base64 data")
            return None  # Or handle the error as you see fit
        except Exception as e:  # Catch general exceptions during decoding
            print(f"Error decoding base64: {e}")
            return None
        
    with open(file_save_path, "wb+") as f:
        for chunk in file.chunks():
            f.write(chunk)
    # imageJson = {}
    # imageJson['url'] = domain
    # imageJson['uuid'] = uuid
    # imageJson['file'] = name
    #return "%s/%s" % (domain, file_save_path)
    return domain, uuid, name

def save_custom_client(request):
    file = request.FILES['file']
    myuuid = request.POST.get('uuid')
    file_save_path = "exe/%s/%s" % (myuuid, file.name)
    Path("exe/%s" % myuuid).mkdir(parents=True, exist_ok=True)
    with open(file_save_path, "wb+") as f:
        for chunk in file.chunks():
            f.write(chunk)

    return HttpResponse("File saved successfully!")

def cleanup_secrets(request):
    # Pass the UUID as a query param or in JSON body
    data = json.loads(request.body)
    my_uuid = data.get('uuid')
    
    if not my_uuid:
        return HttpResponse("Missing UUID", status=400)

    # 1. Find the files in your temp directory matching the UUID
    temp_dir = os.path.join('temp_zips')
    
    # We look for any file starting with 'secrets_' and containing the uuid
    for filename in os.listdir(temp_dir):
        if my_uuid in filename and filename.endswith('.zip'):
            file_path = os.path.join(temp_dir, filename)
            try:
                os.remove(file_path)
                print(f"Successfully deleted {file_path}")
            except OSError as e:
                print(f"Error deleting file: {e}")

    return HttpResponse("Cleanup successful", status=200)

def get_zip(request):
    filename = request.GET['filename']
    #filename = filename+".exe"
    file_path = os.path.join('temp_zips',filename)
    with open(file_path, 'rb') as file:
        response = HttpResponse(file, headers={
            'Content-Type': 'application/vnd.microsoft.portable-executable',
            'Content-Disposition': f'attachment; filename="{filename}"'
        })

    return response
