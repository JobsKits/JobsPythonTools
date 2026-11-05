"""Complete GUI catalog; native diagnostic details retain the OS language. Created by Jobs."""
LANGUAGES = [('zh_CN','简体中文'),('zh_TW','繁體中文'),('bo','བོད་ཡིག'),('en','English'),('ja','日本語'),('fr','Français'),('es','Español'),('de','Deutsch'),('ru','Русский'),('ko','한국어')]
# Each row has the same ten explicitly translated entries, in LANGUAGES order.
ROWS = {
'subtitle': ('有线网络进入 · Wi-Fi 热点输出','有線網路輸入 · Wi-Fi 熱點輸出','སྐུད་ལྡན་དྲ་རྒྱ་ནང་འཇུག · Wi-Fi ཕྱིར་གཏོང་','Wired connection in · Wi-Fi hotspot out','有線接続から Wi-Fi ホットスポットへ','Connexion filaire → point d’accès Wi-Fi','Conexión por cable → punto de acceso Wi-Fi','Kabelverbindung → WLAN-Hotspot','Проводная сеть → точка доступа Wi-Fi','유선 연결 입력 · Wi-Fi 핫스팟 출력'),
'input': ('流量入口','流量入口','གཞི་གྲངས་ནང་འཇུག','TRAFFIC IN','受信側','ENTRÉE','ENTRADA','EINGANG','ВХОДЯЩИЙ ТРАФИК','트래픽 입력'),
'output': ('流量出口','流量出口','གཞི་གྲངས་ཕྱིར་གཏོང་','TRAFFIC OUT','送信側','SORTIE','SALIDA','AUSGANG','ИСХОДЯЩИЙ ТРАФИК','트래픽 출력'),
'checking': ('正在检查设备…','正在檢查裝置…','སྒྲིག་ཆས་ཞིབ་བཤེར་བྱེད་བཞིན…','Checking devices…','デバイスを確認中…','Vérification des appareils…','Comprobando dispositivos…','Geräte werden geprüft…','Проверка устройств…','장치 확인 중…'),
'ready': ('可以分享','可以分享','མཉམ་སྤྱོད་བྱེད་ཆོག','Ready to share','共有できます','Prêt à partager','Listo para compartir','Bereit zum Teilen','Готово к раздаче','공유 준비 완료'),
'on': ('热点正在分享','熱點正在分享','དྲ་རྒྱ་མཉམ་སྤྱོད་བྱེད་བཞིན','Hotspot is sharing','ホットスポット共有中','Point d’accès actif','Punto de acceso activo','Hotspot ist aktiv','Точка доступа работает','핫스팟 공유 중'),
'blocked': ('暂时无法分享','暫時無法分享','གནས་སྐབས་མཉམ་སྤྱོད་མི་ཐུབ','Sharing unavailable','共有できません','Partage indisponible','No se puede compartir','Teilen nicht möglich','Раздача недоступна','공유할 수 없음'),
'unknown': ('状态尚未确认','狀態尚未確認','གནས་ཚུལ་ད་དུང་མ་ངེས','State not confirmed','状態を確認できません','État non confirmé','Estado sin confirmar','Status nicht bestätigt','Состояние не подтверждено','상태 확인 안 됨'),
'start': ('开启分享','開啟分享','མཉམ་སྤྱོད་འགོ་འཛུགས','Start sharing','共有を開始','Activer le partage','Iniciar uso compartido','Teilen starten','Включить раздачу','공유 시작'),
'stop': ('停止分享','停止分享','མཉམ་སྤྱོད་མཚམས་འཇོག','Stop sharing','共有を停止','Arrêter le partage','Detener uso compartido','Teilen beenden','Остановить раздачу','공유 중지'),
'refresh': ('重新检查','重新檢查','ཡང་བསྐྱར་ཞིབ་བཤེར','Check again','再確認','Vérifier à nouveau','Volver a comprobar','Erneut prüfen','Проверить снова','다시 확인'),
'settings': ('打开系统设置','開啟系統設定','མ་ལག་སྒྲིག་འགོད་ཁ་ཕྱེ','Open system settings','システム設定を開く','Ouvrir les réglages système','Abrir ajustes del sistema','Systemeinstellungen öffnen','Открыть настройки системы','시스템 설정 열기'),
'light': ('白天','白天','ཉིན་མོ','Light','ライト','Clair','Claro','Hell','Светлая','밝게'),
'dark': ('黑夜','黑夜','མཚན་མོ','Dark','ダーク','Sombre','Oscuro','Dunkel','Тёмная','어둡게'),
'system': ('跟随系统','跟隨系統','མ་ལག་ལྟར','System','システム','Système','Sistema','System','Системная','시스템 설정'),
'language': ('语言','語言','སྐད་ཡིག','Language','言語','Langue','Idioma','Sprache','Язык','언어'),
'ssid': ('热点名称','熱點名稱','དྲ་ཚིགས་མིང་','Hotspot name','ホットスポット名','Nom du point d’accès','Nombre del punto de acceso','Hotspot-Name','Имя точки доступа','핫스팟 이름'),
'password': ('热点密码（8–63 位 ASCII）','熱點密碼（8–63 位 ASCII）','གསང་ཚིག (ASCII 8–63)','Password (8–63 ASCII characters)','パスワード（ASCII 8～63文字）','Mot de passe (8–63 caractères ASCII)','Contraseña (8–63 caracteres ASCII)','Passwort (8–63 ASCII-Zeichen)','Пароль (8–63 символа ASCII)','비밀번호 (ASCII 8–63자)'),
'credentials': ('填写有效的热点名称和密码后即可分享。','填寫有效的熱點名稱和密碼後即可分享。','དྲ་ཚིགས་མིང་དང་གསང་ཚིག་འགེངས་རོགས།','Enter a valid hotspot name and password.','有効な名前とパスワードを入力してください。','Saisissez un nom et un mot de passe valides.','Introduce un nombre y una contraseña válidos.','Gültigen Namen und gültiges Passwort eingeben.','Введите допустимые имя и пароль.','유효한 이름과 비밀번호를 입력하세요.'),
'mac_setup': ('MacOS 首次使用：在系统“互联网共享”中选好此入口 → Wi-Fi，并设置名称和密码。App 使用系统保存的配置。','MacOS 首次使用：在系統「網際網路共享」選好此入口 → Wi-Fi，並設定名稱和密碼。App 使用系統儲存的設定。','MacOS ཐོག་མར་མ་ལག་གི་དྲ་རྒྱ་མཉམ་སྤྱོད་ནང་ནང་འཇུག → Wi-Fi དང་མིང་གསང་ཚིག་སྒྲིག་རོགས།','First use on MacOS: configure this input → Wi-Fi, name and password in Internet Sharing. The app uses the saved system configuration.','MacOS の初回はインターネット共有で入力 → Wi-Fi、名前、パスワードを設定してください。保存済みのシステム設定を使用します。','Sur MacOS, configurez d’abord cette entrée → Wi-Fi, le nom et le mot de passe dans Partage Internet. Les réglages système sont utilisés.','En MacOS, configura primero esta entrada → Wi-Fi, nombre y contraseña en Compartir Internet. Se usa la configuración del sistema.','Unter MacOS zuerst diesen Eingang → WLAN, Namen und Passwort in Internetfreigabe einstellen. Die gespeicherten Systemeinstellungen werden verwendet.','На MacOS сначала настройте этот вход → Wi-Fi, имя и пароль в общем доступе к Интернету. Используются настройки системы.','MacOS에서는 먼저 인터넷 공유에서 이 입력 → Wi-Fi, 이름과 비밀번호를 설정하세요. 저장된 시스템 설정을 사용합니다.'),
'no_input': ('没有可用的有线／USB 网络','沒有可用的有線／USB 網路','སྐུད་ལྡན་དང་ USB དྲ་རྒྱ་མེད','No wired / USB network available','有線／USB ネットワークがありません','Aucun réseau filaire / USB disponible','No hay red por cable / USB disponible','Kein Kabel-/USB-Netzwerk verfügbar','Нет проводной / USB-сети','사용 가능한 유선 / USB 네트워크 없음'),
'no_wifi': ('没有可用的 Wi-Fi 出口','沒有可用的 Wi-Fi 出口','Wi-Fi ཕྱིར་གཏོང་མེད','No Wi-Fi output available','Wi-Fi 出力がありません','Aucune sortie Wi-Fi disponible','No hay salida Wi-Fi disponible','Kein WLAN-Ausgang verfügbar','Нет выхода Wi-Fi','사용 가능한 Wi-Fi 출력 없음'),
'disconnected': ('未连接','未連線','མ་མཐུད','Disconnected','未接続','Déconnecté','Desconectado','Getrennt','Нет подключения','연결 안 됨'),
'connected': ('已连接','已連線','མཐུད་ཟིན','Connected','接続済み','Connecté','Conectado','Verbunden','Подключено','연결됨'),
'counter_note': ('显示网卡总流量，包含电脑自身流量；不等于热点独占流量。未知值显示 —。','顯示網卡總流量，包含電腦自身流量；不等於熱點獨佔流量。未知值顯示 —。','དྲ་བྱང་གི་ཁྱོན་བསྡོམས་གཞི་གྲངས་ཡིན། དྲ་ཚིགས་གཅིག་པུའི་གྲངས་མིན། མ་ཤེས་པ —།','Adapter totals include this computer’s traffic; they are not hotspot-only traffic. Unknown values: —.','アダプター全体の通信量です。PC 自身の通信も含み、共有専用ではありません。不明な値は —。','Totaux des cartes, trafic du PC inclus ; ce ne sont pas les seuls échanges du point d’accès. Inconnu : —.','Totales del adaptador, incluido el tráfico del PC; no son exclusivos del punto de acceso. Desconocido: —.','Adapter-Gesamtverkehr einschließlich PC-Daten, kein reiner Hotspot-Verkehr. Unbekannte Werte: —.','Общий трафик адаптеров, включая трафик компьютера, а не только точки доступа. Неизвестно: —.','어댑터 전체 트래픽으로 PC 자체 트래픽도 포함하며 핫스팟 전용이 아닙니다. 알 수 없는 값: —.'),
'details': ('系统诊断详情','系統診斷詳情','མ་ལག་ཞིབ་བཤེར་ཞིབ་ཕྲ','System diagnostics','システム診断','Diagnostic système','Diagnóstico del sistema','Systemdiagnose','Диагностика системы','시스템 진단'),
'waiting': ('等待系统响应…','等待系統回應…','མ་ལག་གི་ལན་སྒུག་བཞིན…','Waiting for the system…','システムの応答待ち…','En attente du système…','Esperando al sistema…','Warten auf das System…','Ожидание ответа системы…','시스템 응답 대기 중…'),
'error': ('操作未完成，请检查下方诊断。','操作未完成，請檢查下方診斷。','བྱ་བ་མ་འགྲུབ། ཞིབ་བཤེར་ལ་གཟིགས།','Operation incomplete. Check the diagnostics below.','操作を完了できません。診断を確認してください。','Opération incomplète. Consultez le diagnostic.','Operación incompleta. Consulta el diagnóstico.','Vorgang unvollständig. Diagnose prüfen.','Операция не завершена. Проверьте диагностику.','작업이 완료되지 않았습니다. 진단을 확인하세요.'),
'show': ('显示窗口','顯示視窗','སྒེའུ་ཁུང་སྟོན','Show window','ウィンドウを表示','Afficher la fenêtre','Mostrar ventana','Fenster anzeigen','Показать окно','창 표시'),
'hide': ('收起到状态栏／托盘','收起至狀態列／系統匣','གནས་ཚུལ་སྡེར་བསྡུ','Hide to menu bar / tray','メニューバー／トレイに収納','Réduire dans la barre système','Minimizar a la bandeja','In Menüleiste / Infobereich ausblenden','Свернуть в меню / трей','메뉴 막대 / 트레이로 숨기기'),
'quit': ('退出','結束','ཕྱིར་འཐོན','Quit','終了','Quitter','Salir','Beenden','Выход','종료'),
'quit_question': ('热点仍在运行。退出时如何处理？','熱點仍在執行。結束時如何處理？','དྲ་ཚིགས་འཁོར་བཞིན་ཡོད། ཕྱིར་འཐོན་དུས་ཇི་ལྟར་བྱེད།','The hotspot is running. What should happen when quitting?','共有中です。終了時の動作を選んでください。','Le point d’accès est actif. Que faire en quittant ?','El punto de acceso está activo. ¿Qué hacer al salir?','Der Hotspot ist aktiv. Verhalten beim Beenden wählen.','Точка доступа работает. Что сделать при выходе?','핫스팟이 실행 중입니다. 종료할 때 어떻게 할까요?'),
'leave': ('保留分享并退出','保留分享並結束','མཉམ་སྤྱོད་བཞག་ནས་འཐོན','Leave sharing on and quit','共有を続けて終了','Quitter sans arrêter','Salir y seguir compartiendo','Weiter teilen und beenden','Выйти, оставив раздачу','공유를 유지하고 종료'),
'stop_quit': ('停止分享并退出','停止分享並結束','མཉམ་སྤྱོད་བཀག་ནས་འཐོན','Stop sharing and quit','共有を停止して終了','Arrêter et quitter','Detener y salir','Teilen stoppen und beenden','Остановить и выйти','공유 중지 후 종료'),
'cancel': ('取消','取消','ཕྱིར་འཐེན','Cancel','キャンセル','Annuler','Cancelar','Abbrechen','Отмена','취소'),
'local': ('本地设备检测 · 不上传数据','本機裝置偵測 · 不上傳資料','རང་སའི་སྒྲིག་ཆས་ཞིབ་བཤེར · གཞི་གྲངས་མི་གཏོང་','Local device checks · no uploads','ローカルで確認 · データ送信なし','Vérification locale · aucun envoi','Comprobación local · sin subidas','Lokale Prüfung · kein Upload','Локальная проверка · без отправки данных','로컬 장치 확인 · 데이터 업로드 없음'),
'demo': ('界面演示 · 不操作系统网络','介面示範 · 不操作系統網路','འཆར་ངོས་དཔེ་སྟོན · མ་ལག་དྲ་རྒྱ་མི་འགྱུར','Interface demo · no system network changes','画面デモ · ネットワーク変更なし','Démo · aucun changement réseau','Demostración · sin cambios de red','Oberflächen-Demo · keine Netzwerkänderungen','Демо интерфейса · сеть не меняется','화면 데모 · 시스템 네트워크 변경 없음'),
'help': ('连接网线或 USB 网络 → 打开 Wi-Fi → 检查系统共享配置。','連接網路線或 USB 網路 → 開啟 Wi-Fi → 檢查系統共享設定。','སྐུད་ལྡན་དྲ་རྒྱ་མཐུད → Wi-Fi ཁ་ཕྱེ → མཉམ་སྤྱོད་སྒྲིག་འགོད་ཞིབ་བཤེར།','Connect Ethernet or USB networking → enable Wi-Fi → check system sharing settings.','有線／USB 接続 → Wi-Fi を有効化 → システム共有設定を確認。','Branchez le réseau filaire/USB → activez le Wi-Fi → vérifiez le partage système.','Conecta Ethernet o USB → activa Wi-Fi → revisa los ajustes de uso compartido.','Ethernet/USB verbinden → WLAN aktivieren → Freigabeeinstellungen prüfen.','Подключите Ethernet/USB → включите Wi-Fi → проверьте общий доступ.','이더넷 또는 USB 연결 → Wi-Fi 켜기 → 시스템 공유 설정 확인.'),
'permission': ('需要系统权限或配置支持，请打开系统设置检查。','需要系統權限或設定支援，請開啟系統設定檢查。','མ་ལག་གི་ཆོག་མཆན་དང་སྒྲིག་འགོད་ཞིབ་བཤེར་རོགས།','System permission or configuration is required. Check system settings.','システム権限または設定が必要です。システム設定を確認してください。','Autorisation ou configuration système requise. Vérifiez les réglages.','Se requiere permiso o configuración del sistema. Revisa los ajustes.','Systemberechtigung oder Konfiguration erforderlich. Einstellungen prüfen.','Нужны разрешение или настройка системы. Проверьте параметры.','시스템 권한 또는 설정이 필요합니다. 시스템 설정을 확인하세요.'),
'unsupported': ('当前系统或驱动不支持热点。','目前系統或驅動程式不支援熱點。','མ་ལག་འདིས་དྲ་ཚིགས་རྒྱབ་སྐྱོར་མི་བྱེད།','This system or driver does not support a hotspot.','このシステムまたはドライバーは共有に対応していません。','Ce système ou pilote ne permet pas le partage.','El sistema o controlador no admite un punto de acceso.','System oder Treiber unterstützt keinen Hotspot.','Система или драйвер не поддерживает точку доступа.','시스템 또는 드라이버가 핫스팟을 지원하지 않습니다.'),
'wifi_off': ('Wi-Fi 未开启或无线电不可用。','Wi-Fi 未開啟或無線電無法使用。','Wi-Fi ཁ་ཕྱེ་མེད་དམ་སྐུད་མེད་མི་ཐུབ།','Wi-Fi is off or its radio is unavailable.','Wi-Fi がオフ、または無線機能を使用できません。','Wi-Fi désactivé ou radio indisponible.','Wi-Fi apagado o radio no disponible.','WLAN ausgeschaltet oder Funk nicht verfügbar.','Wi-Fi выключен или радиомодуль недоступен.','Wi-Fi가 꺼져 있거나 무선 장치를 사용할 수 없습니다.'),
'route': ('当前互联网没有通过选中的有线／USB 接口进入。','目前網際網路未經所選有線／USB 介面進入。','དྲ་རྒྱ་བདམས་པའི་སྐུད་ལྡན་མཐུད་ཁ་ནས་ཡོང་མེད།','Internet access is not using the selected wired / USB interface.','インターネットの入力が選択した有線／USB 接続ではありません。','Internet n’utilise pas l’interface filaire / USB sélectionnée.','Internet no usa la interfaz por cable / USB seleccionada.','Internetzugang nutzt nicht den gewählten Kabel-/USB-Adapter.','Интернет не использует выбранный проводной / USB-интерфейс.','인터넷이 선택한 유선 / USB 인터페이스를 사용하지 않습니다.'),
}
ROWS['permissions'] = ('授权辅助功能','授權輔助使用','རམ་འདེགས་ནུས་པའི་ཆོག་མཆན','Grant accessibility access','アクセシビリティを許可','Autoriser l’accessibilité','Autorizar accesibilidad','Bedienungshilfen erlauben','Разрешить универсальный доступ','손쉬운 사용 권한 허용')
CATALOG = {locale: {key: values[index] for key, values in ROWS.items()} for index,(locale,_) in enumerate(LANGUAGES)}
assert all(len(values) == len(LANGUAGES) for values in ROWS.values())

def tr(locale, key):
    return CATALOG.get(locale, CATALOG['en']).get(key, CATALOG['en'].get(key, key))

def issue_key(code):
    lower = code.lower()
    if any(word in lower for word in ('no_upstream','no_input','wired','no_ethernet','input_missing','upstream_missing')):
        return 'no_input'
    if any(word in lower for word in ('no_wifi','wifi_missing','no_wireless')):
        return 'no_wifi'
    if any(word in lower for word in ('radio','wifi_off','wifi_disabled')):
        return 'wifi_off'
    if any(word in lower for word in ('route','internet','offline','upstream_down','wifi_input')):
        return 'route'
    if any(word in lower for word in ('unsupported','capability','driver')):
        return 'unsupported'
    if any(word in lower for word in ('permission','access','config','setup','policy','privilege')):
        return 'permission'
    return 'unknown'
