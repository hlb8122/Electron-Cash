def telegram_executor(handle: str):
    QDesktopServices.openUrl(QUrl("https://t.me/" + handle))
