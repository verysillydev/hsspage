#!/bin/bash
# Rebuild the web version and push it live to yoniverseproductions.com
set -e
cd "$(dirname "$0")"

echo "==> building web version"
python3 build_site.py web

echo "==> syncing into the Vercel project folder (keeping the .vercel link)"
# wipe every built page, not just one, or a new page silently never ships
find yoniverse-work -mindepth 1 -maxdepth 1 ! -name '.vercel' -exec rm -rf {} +
cp -R deploy/. yoniverse-work/

echo "==> pages being deployed:"
find yoniverse-work -name index.html -not -path '*/.vercel/*' | sed 's|yoniverse-work|  |'

echo "==> deploying to production"
cd yoniverse-work
npx --yes vercel@latest deploy --prod --yes

echo
echo "Live at https://yoniverseproductions.com/our-work and /packages"
