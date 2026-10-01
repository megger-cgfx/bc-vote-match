#!/usr/bin/env bash
set -u
cd .
fetch() { python3 agents/fetch_source.py --party ndp "$@" >/dev/null 2>&1; echo "done: $*"; }

fetch --url "https://bcndp.ca/releases/action-you-david-eby-releases-plan-help-people-get-ahead" --type platform --title "Action For You: David Eby releases plan to help people get ahead" --published "2024-10-03"
fetch --url "https://www.bcndp.ca/actionplan" --type platform --title "An Action Plan for You (platform landing page)"
fetch --url "https://bcndp.ca/releases/david-eby-and-bc-ndp-will-build-new-school-campbell-river" --type release --title "David Eby and the BC NDP will build a new school in Campbell River"
fetch --url "https://bcndp.ca/releases/eby-deliver-transportation-infrastructure-including-building-skytrain-langley-ubc" --type release --title "Eby to deliver transportation infrastructure, including building Skytrain from Langley to UBC"
fetch --url "https://coastalfront.ca/read/bc-ndp-unveils-29b-platform-amid-massive-deficit-and-fiscal-concerns" --type media --title "BC NDP Unveils $2.9B Platform Amid Massive Deficit (Coastal Front)"
fetch --url "https://cheknews.ca/b-c-ndp-to-unveil-election-platform-conservatives-promise-to-end-insurance-monopoly-1217385" --type media --title "B.C. NDP unveils election platform, focusing on 'tough challenges' and John Rustad (CHEK News)"
echo "ALL DONE 2"
