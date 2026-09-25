#!/bin/sh
# Builds index.html (GitHub Pages) and artifact-body.html (claude.ai preview)
# from the single shared _body.html, so the two can never drift apart.
set -e
cd "$(dirname "$0")"

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
<link rel="stylesheet" href="./styles.css">
</head>
<body>
EOF
cat _body.html
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
cat _body.html
echo
echo '<script src="app.js" defer></script>'
} > artifact-body.html

echo "built index.html + artifact-body.html"
