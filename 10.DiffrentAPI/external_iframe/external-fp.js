window.onload = () => {
    const fp = {
        userAgent: navigator.userAgent,
        language: navigator.language,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        platform: navigator.platform,
        hardwareConcurrency: navigator.hardwareConcurrency,
        screen: {
            width: screen.width,
            height: screen.height,
            colorDepth: screen.colorDepth
        },
        timestamp: new Date().toISOString()
    };
    window.parent.postMessage(fp, "http://localhost:8000");  // указываем origin родителя
};
