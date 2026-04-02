from django import forms
from PIL import Image

class GenerateForm(forms.Form):
    #Platform
    platform = forms.ChoiceField(choices=[('windows','Windows 64Bit'),('windows-x86','Windows 32Bit'),('linux','Linux'),('android','Android'),('macos','macOS')], initial='windows')
    version = forms.ChoiceField(choices=[('master','nightly'),('1.4.6','1.4.6'),('1.4.5','1.4.5'),('1.4.4','1.4.4'),('1.4.3','1.4.3'),('1.4.2','1.4.2'),('1.4.1','1.4.1'),('1.4.0','1.4.0'),('1.3.9','1.3.9'),('1.3.8','1.3.8'),('1.3.7','1.3.7'),('1.3.6','1.3.6'),('1.3.5','1.3.5'),('1.3.4','1.3.4'),('1.3.3','1.3.3')], initial='1.4.6')
    help_text="'master' is the development version (nightly build) with the latest features but may be less stable"
    delayFix = forms.BooleanField(initial=True, required=False)

    #General
    exename = forms.CharField(label="Name for EXE file", required=True)
    appname = forms.CharField(label="Custom App Name", required=False)
    direction = forms.ChoiceField(widget=forms.RadioSelect, choices=[
        ('incoming', 'Incoming Only'),
        ('outgoing', 'Outgoing Only'),
        ('both', 'Bidirectional')
    ], initial='both')
    installation = forms.ChoiceField(label="Disable Installation", choices=[
        ('installationY', 'No, enable installation'),
        ('installationN', 'Yes, DISABLE installation')
    ], initial='installationY')
    settings = forms.ChoiceField(label="Disable Settings", choices=[
        ('settingsY', 'No, enable settings'),
        ('settingsN', 'Yes, DISABLE settings')
    ], initial='settingsY')
    androidappid = forms.CharField(label="Custom Android App ID (replaces 'com.carriez.flutter_hbb')", required=False)

    #Custom Server
    serverIP = forms.CharField(label="Host", required=False)
    apiServer = forms.CharField(label="API Server", required=False)
    key = forms.CharField(label="Key", required=False)
    relayServer = forms.CharField(label="Relay Server", required=False)
    iceServers = forms.CharField(label="ICE Servers", required=False)
    customRendezvousServer = forms.CharField(label="Custom rendezvous server option", required=False)
    proxyUrl = forms.CharField(label="Proxy URL", required=False)
    proxyUsername = forms.CharField(label="Proxy Username", required=False)
    proxyPassword = forms.CharField(label="Proxy Password", required=False)
    urlLink = forms.CharField(label="Custom URL for links", required=False)
    downloadLink = forms.CharField(label="Custom URL for downloading new versions", required=False)
    updateCheckUrl = forms.CharField(label="Custom URL for update check API", required=False)
    allowCustomClientUpdate = forms.BooleanField(initial=False, required=False)
    compname = forms.CharField(label="Company name",required=False)
    serverProfilesJson = forms.CharField(label="Built-in server profiles JSON", widget=forms.Textarea, required=False)

    #Visual
    iconfile = forms.FileField(label="Custom App Icon (in .png format)", required=False, widget=forms.FileInput(attrs={'accept': 'image/png'}))
    logofile = forms.FileField(label="Custom App Logo (in .png format)", required=False, widget=forms.FileInput(attrs={'accept': 'image/png'}))
    iconbase64 = forms.CharField(required=False)
    logobase64 = forms.CharField(required=False)
    theme = forms.ChoiceField(choices=[
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('system', 'Follow System')
    ], initial='system')
    themeDorO = forms.ChoiceField(choices=[('default', 'Default'),('override', 'Override')], initial='default')

    #Security
    passApproveMode = forms.ChoiceField(choices=[('password','Accept sessions via password'),('click','Accept sessions via click'),('password-click','Accepts sessions via both')],initial='password-click')
    permanentPassword = forms.CharField(widget=forms.PasswordInput(), required=False)
    #runasadmin = forms.ChoiceField(choices=[('false','No'),('true','Yes')], initial='false')
    denyLan = forms.BooleanField(initial=False, required=False)
    enableDirectIP = forms.BooleanField(initial=False, required=False)
    directAccessPort = forms.CharField(label="Direct access port", required=False)
    ipWhitelist = forms.CharField(widget=forms.Textarea, required=False)
    forceAlwaysRelay = forms.BooleanField(initial=False, required=False)
    allowWebSocket = forms.BooleanField(initial=True, required=False)
    disableUDP = forms.BooleanField(initial=False, required=False)
    allowInsecureTLSFallback = forms.BooleanField(initial=False, required=False)
    #ipWhitelist = forms.BooleanField(initial=False, required=False)
    autoClose = forms.BooleanField(initial=False, required=False)
    autoDisconnectTimeout = forms.CharField(label="Auto disconnect timeout (min)", required=False)
    allowAutoUpdate = forms.BooleanField(initial=True, required=False)
    allowNumericOneTimePassword = forms.BooleanField(initial=False, required=False)
    allowOnlyConnWindowOpen = forms.BooleanField(initial=False, required=False)
    allowAutoRecordIncoming = forms.BooleanField(initial=False, required=False)
    allowAutoRecordOutgoing = forms.BooleanField(initial=False, required=False)
    temporaryPasswordLength = forms.CharField(label="Temporary password length", required=False)
    enableAbr = forms.BooleanField(initial=True, required=False)
    allowAlwaysSoftwareRender = forms.BooleanField(initial=False, required=False)
    allowLinuxHeadless = forms.BooleanField(initial=False, required=False)
    enableHwcodec = forms.BooleanField(initial=True, required=False)
    enableUdpPunch = forms.BooleanField(initial=True, required=False)
    enableIpv6Punch = forms.BooleanField(initial=True, required=False)
    removeSetupServerTip = forms.BooleanField(initial=True, required=False)

    #Permissions
    permissionsDorO = forms.ChoiceField(choices=[('default', 'Default'),('override', 'Override')], initial='default')
    policyDorO = forms.ChoiceField(choices=[('default', 'Default'),('override', 'Override')], initial='override')
    permissionsType = forms.ChoiceField(choices=[('custom', 'Custom'),('full', 'Full Access'),('view','Screen share')], initial='custom')
    enableKeyboard =  forms.BooleanField(initial=True, required=False)
    enableClipboard = forms.BooleanField(initial=True, required=False)
    enableFileTransfer = forms.BooleanField(initial=True, required=False)
    enableAudio = forms.BooleanField(initial=True, required=False)
    enableTCP = forms.BooleanField(initial=True, required=False)
    enableRemoteRestart = forms.BooleanField(initial=True, required=False)
    enableRecording = forms.BooleanField(initial=True, required=False)
    enableBlockingInput = forms.BooleanField(initial=True, required=False)
    enableRemoteModi = forms.BooleanField(initial=False, required=False)
    hidecm = forms.BooleanField(initial=False, required=False)
    enablePrinter = forms.BooleanField(initial=True, required=False)
    enableCamera = forms.BooleanField(initial=True, required=False)
    enableTerminal = forms.BooleanField(initial=True, required=False)
    fileTransferMaxFiles = forms.CharField(label="File transfer max files", required=False)
    defaultConnectPassword = forms.CharField(label="Default connect password", required=False)
    enableDirectxCapture = forms.BooleanField(initial=False, required=False)
    enableTrustedDevices = forms.BooleanField(initial=False, required=False)
    presetAddressBookName = forms.CharField(label="Preset address book name", required=False)
    presetAddressBookTag = forms.CharField(label="Preset address book tag", required=False)
    presetAddressBookAlias = forms.CharField(label="Preset address book alias", required=False)
    presetAddressBookPassword = forms.CharField(label="Preset address book password", required=False)
    presetAddressBookNote = forms.CharField(label="Preset address book note", required=False)
    presetDeviceUsername = forms.CharField(label="Preset device username", required=False)
    presetDeviceName = forms.CharField(label="Preset device name", required=False)
    presetNote = forms.CharField(label="Preset note", required=False)
    displayName = forms.CharField(label="Display name", required=False)
    avatar = forms.CharField(label="Avatar", required=False)
    presetDeviceGroupName = forms.CharField(label="Preset device group name", required=False)
    presetUserName = forms.CharField(label="Preset user name", required=False)
    presetStrategyName = forms.CharField(label="Preset strategy name", required=False)

    #Other
    removeWallpaper = forms.BooleanField(initial=True, required=False)
    hideServerSettings = forms.BooleanField(initial=False, required=False)
    hideSecuritySettings = forms.BooleanField(initial=False, required=False)
    hideNetworkSettings = forms.BooleanField(initial=False, required=False)
    hideProxySettings = forms.BooleanField(initial=False, required=False)
    hideWebSocketSettings = forms.BooleanField(initial=False, required=False)
    hideRemotePrinterSettings = forms.BooleanField(initial=False, required=False)
    hideStopService = forms.BooleanField(initial=False, required=False)
    hideUsernameOnCard = forms.BooleanField(initial=False, required=False)
    hideHelpCards = forms.BooleanField(initial=False, required=False)
    hideTray = forms.BooleanField(initial=False, required=False)
    oneWayClipboardRedirection = forms.BooleanField(initial=False, required=False)
    allowLogonScreenPassword = forms.BooleanField(initial=False, required=False)
    oneWayFileTransfer = forms.BooleanField(initial=False, required=False)
    allowHttps21114 = forms.BooleanField(initial=False, required=False)
    useRawTcpForApi = forms.BooleanField(initial=False, required=False)
    allowHostnameAsID = forms.BooleanField(initial=False, required=False)
    registerDevice = forms.BooleanField(initial=True, required=False)
    hidePoweredByMe = forms.BooleanField(initial=False, required=False)
    mainWindowAlwaysOnTop = forms.BooleanField(initial=False, required=False)
    disableChangePermanentPassword = forms.BooleanField(initial=False, required=False)
    disableChangeID = forms.BooleanField(initial=False, required=False)
    disableUnlockPin = forms.BooleanField(initial=False, required=False)
    removePresetPasswordWarning = forms.BooleanField(initial=False, required=False)
    allowAskForNote = forms.BooleanField(initial=False, required=False)
    allowD3DRender = forms.BooleanField(initial=False, required=False)
    allowRemoteCMModification = forms.BooleanField(initial=False, required=False)
    collapseToolbar = forms.BooleanField(initial=False, required=False)
    disableAudioViewer = forms.BooleanField(initial=False, required=False)
    disableClipboardViewer = forms.BooleanField(initial=False, required=False)
    disableDiscoveryPanel = forms.BooleanField(initial=False, required=False)
    disableFloatingWindow = forms.BooleanField(initial=False, required=False)
    disableGroupPanel = forms.BooleanField(initial=False, required=False)
    displaysAsIndividualWindows = forms.BooleanField(initial=False, required=False)
    enableConfirmClosingTabs = forms.BooleanField(initial=False, required=False)
    enableFileCopyPaste = forms.BooleanField(initial=False, required=False)
    enableFlutterHttpOnRust = forms.BooleanField(initial=False, required=False)
    enableOpenNewConnectionsInTabs = forms.BooleanField(initial=False, required=False)
    filterAbByIntersection = forms.BooleanField(initial=False, required=False)
    followRemoteCursor = forms.BooleanField(initial=False, required=False)
    followRemoteWindow = forms.BooleanField(initial=False, required=False)
    hideAbTagsPanel = forms.BooleanField(initial=False, required=False)
    i444 = forms.BooleanField(initial=False, required=False)
    keepScreenOn = forms.BooleanField(initial=False, required=False)
    keepAwakeDuringIncomingSessions = forms.BooleanField(initial=False, required=False)
    keepAwakeDuringOutgoingSessions = forms.BooleanField(initial=False, required=False)
    lockAfterSessionEnd = forms.BooleanField(initial=False, required=False)
    preElevateService = forms.BooleanField(initial=False, required=False)
    privacyMode = forms.BooleanField(initial=False, required=False)
    reverseMouseWheel = forms.BooleanField(initial=False, required=False)
    showMonitorsToolbar = forms.BooleanField(initial=False, required=False)
    showQualityMonitor = forms.BooleanField(initial=False, required=False)
    showRemoteCursor = forms.BooleanField(initial=False, required=False)
    showVirtualJoystick = forms.BooleanField(initial=False, required=False)
    showVirtualMouse = forms.BooleanField(initial=False, required=False)
    swapLeftRightMouse = forms.BooleanField(initial=False, required=False)
    syncAbTags = forms.BooleanField(initial=False, required=False)
    syncAbWithRecentSessions = forms.BooleanField(initial=False, required=False)
    syncInitClipboard = forms.BooleanField(initial=False, required=False)
    touchMode = forms.BooleanField(initial=False, required=False)
    useAllMyDisplaysForRemoteSession = forms.BooleanField(initial=False, required=False)
    useTextureRender = forms.BooleanField(initial=False, required=False)
    viewOnly = forms.BooleanField(initial=False, required=False)
    zoomCursor = forms.BooleanField(initial=False, required=False)

    defaultManual = forms.CharField(widget=forms.Textarea, required=False)
    overrideManual = forms.CharField(widget=forms.Textarea, required=False)

    #custom added features
    cycleMonitor = forms.BooleanField(initial=False, required=False)
    xOffline = forms.BooleanField(initial=False, required=False)
    removeNewVersionNotif = forms.BooleanField(initial=False, required=False)

    def clean_iconfile(self):
        print("checking icon")
        image = self.cleaned_data['iconfile']
        if image:
            try:
                # Open the image using Pillow
                img = Image.open(image)

                # Check if the image is a PNG (optional, but good practice)
                if img.format != 'PNG':
                    raise forms.ValidationError("Only PNG images are allowed.")

                # Get image dimensions
                width, height = img.size

                # Check for square dimensions
                if width != height:
                    raise forms.ValidationError("Custom App Icon dimensions must be square.")
                
                return image
            except OSError:  # Handle cases where the uploaded file is not a valid image
                raise forms.ValidationError("Invalid icon file.")
            except Exception as e: # Catch any other image processing errors
                raise forms.ValidationError(f"Error processing icon: {e}")
