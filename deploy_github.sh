#!/bin/bash
# Rebuild the web version and publish it to the gh-pages branch of the
# GitHub repo, which is what GitHub Pages actually serves. main stays the
# source (build_site.py, assets); this branch is build output only, and
# gets force-pushed fresh every time, not accumulated history.
set -e
cd "$(dirname "$0")"

REPO="https://github.com/verysillydev/hsspage.git"
DOMAIN="homeservicestudios.com"

echo "==> building web version"
python3 build_site.py web

echo "==> tagging the custom domain and disabling Jekyll processing"
echo "$DOMAIN" > deploy/CNAME
touch deploy/.nojekyll

echo "==> publishing deploy/ to gh-pages"
cd deploy
rm -rf .git
git init -q -b gh-pages
git add -A
git -c user.name="$(git -C .. config user.name)" \
    -c user.email="$(git -C .. config user.email)" \
    commit -q -m "Deploy $(date -u +%Y-%m-%dT%H:%M:%SZ)"
git push -f "$REPO" HEAD:gh-pages
cd ..

echo
echo "Pushed to gh-pages. Live at https://$DOMAIN once Pages/DNS are set up."
