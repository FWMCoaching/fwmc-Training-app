#!/bin/sh
# Builds index.html (GitHub Pages) and artifact-body.html (claude.ai preview)
# from the single shared _body.html, so the two can never drift apart.
set -e
cd "$(dirname "$0")"

# "Stand: <Datum, Uhrzeit>" in every footer (Fabian, 2026-10-02), so it's
# easy to see whether the newest version is open. Stamped at build time.
STAND=$(TZ=Europe/Berlin date "+%d.%m.%Y, %H:%M")
body() { sed "s|__APP_STAND__|$STAND|g" _body.html; }

{
cat <<'EOF'
<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>FWMC Online-Training</title>
<meta name="description" content="FWMC Online-Training von Fabian Westermann Mentalcoaching – Visual Training und Atemtraining, direkt im Browser.">
<meta name="robots" content="noindex, nofollow">
<meta name="theme-color" content="#007094">
<link rel="manifest" href="./manifest.json">
<link rel="icon" href="./icon-192.png">
<link rel="apple-touch-icon" href="./icon-512.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="FWMC Online-Training">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<link rel="apple-touch-startup-image" media="screen and (device-width: 430px) and (device-height: 932px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)" href="./splash/apple-splash-1290-2796.png">
<link rel="apple-touch-startup-image" media="screen and (device-width: 393px) and (device-height: 852px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)" href="./splash/apple-splash-1179-2556.png">
<link rel="apple-touch-startup-image" media="screen and (device-width: 428px) and (device-height: 926px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)" href="./splash/apple-splash-1284-2778.png">
<link rel="apple-touch-startup-image" media="screen and (device-width: 390px) and (device-height: 844px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)" href="./splash/apple-splash-1170-2532.png">
<link rel="apple-touch-startup-image" media="screen and (device-width: 375px) and (device-height: 812px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)" href="./splash/apple-splash-1125-2436.png">
<link rel="apple-touch-startup-image" media="screen and (device-width: 414px) and (device-height: 896px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)" href="./splash/apple-splash-1242-2688.png">
<link rel="apple-touch-startup-image" media="screen and (device-width: 414px) and (device-height: 896px) and (-webkit-device-pixel-ratio: 2) and (orientation: portrait)" href="./splash/apple-splash-828-1792.png">
<link rel="apple-touch-startup-image" media="screen and (device-width: 375px) and (device-height: 667px) and (-webkit-device-pixel-ratio: 2) and (orientation: portrait)" href="./splash/apple-splash-750-1334.png">
<link rel="apple-touch-startup-image" media="screen and (device-width: 440px) and (device-height: 956px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)" href="./splash/apple-splash-1320-2868.png">
<link rel="apple-touch-startup-image" media="screen and (device-width: 402px) and (device-height: 874px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)" href="./splash/apple-splash-1206-2622.png">
<link rel="apple-touch-startup-image" media="screen and (device-width: 1024px) and (device-height: 1366px) and (-webkit-device-pixel-ratio: 2) and (orientation: portrait)" href="./splash/apple-splash-2048-2732.png">
<link rel="apple-touch-startup-image" media="screen and (device-width: 834px) and (device-height: 1194px) and (-webkit-device-pixel-ratio: 2) and (orientation: portrait)" href="./splash/apple-splash-1668-2388.png">
<link rel="apple-touch-startup-image" media="screen and (device-width: 820px) and (device-height: 1180px) and (-webkit-device-pixel-ratio: 2) and (orientation: portrait)" href="./splash/apple-splash-1640-2360.png">
<link rel="apple-touch-startup-image" media="screen and (device-width: 810px) and (device-height: 1080px) and (-webkit-device-pixel-ratio: 2) and (orientation: portrait)" href="./splash/apple-splash-1620-2160.png">
<link rel="apple-touch-startup-image" media="screen and (device-width: 744px) and (device-height: 1133px) and (-webkit-device-pixel-ratio: 2) and (orientation: portrait)" href="./splash/apple-splash-1488-2266.png">
<link rel="preload" href="./fonts/public-sans.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="./fonts/magra-700.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="./styles.css">
</head>
<body>
<script>try{var f=localStorage.getItem("fwmc-test-bottomnav");if(!navigator.webdriver||(f&&f!=="false"))document.body.classList.add("has-bottom-nav")}catch(e){}</script>
EOF
body
cat <<'EOF'

<script src="./app.js" defer></script>
</body>
</html>
EOF
} > index.html

{
echo '<title>FWMC Online-Training</title>'
echo '<link rel="stylesheet" href="styles.css">'
echo
body
echo
echo '<script src="app.js" defer></script>'
} > artifact-body.html

echo "built index.html + artifact-body.html"
