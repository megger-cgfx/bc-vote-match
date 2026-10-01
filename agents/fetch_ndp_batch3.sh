#!/usr/bin/env bash
set -u
cd .
fetch() { python3 agents/fetch_source.py --party ndp "$@" >/dev/null 2>&1 && echo "OK  $*" || echo "FAIL $*"; }

fetch --url "https://vancouversun.com/business/david-eby-bets-big-on-potential-for-more-major-projects-in-build-b-c-strong-platform" --type media --title "David Eby bets big on potential for more major projects in Build B.C. Strong platform (Vancouver Sun)" --published "2026-09-23"
fetch --url "https://vancouver.citynews.ca/2026/09/25/b-c-s-eby-says-ndp-would-tax-new-unsold-condos-raise-speculation-vacancy-fees/" --type media --title "Eby says NDP would tax new, unsold condos, raise speculation, vacancy fees (CityNews)" --published "2026-09-25"
fetch --url "https://www.ctvnews.ca/vancouver/article/eby-says-bc-ndp-would-tax-new-unsold-condos-and-raise-speculation-vacancy-fees" --type media --title "Eby says B.C. NDP would tax new, unsold condos and raise speculation, vacancy fees (CTV News)" --published "2026-09-25"
fetch --url "https://infonews.ca/news/4372098/bc-ndp-unveils-election-platform-focusing-on-tough-challenges-and-john-rustad" --type media --title "B.C. NDP unveils election platform, focusing on tough challenges and John Rustad (InfoNews)" --published "2024-10-03"
fetch --url "https://westernstandard.news/news/cost-of-living-what-is-each-party-promising-british-columbians/58635" --type media --title "COST OF LIVING: What is each party promising British Columbians? (Western Standard)"
fetch --url "https://itsryanclayton.substack.com/p/ndp-promises" --type media --title "New democratic promises - analysis of the NDP platform (Substack, Ryan Clayton)"
echo "BATCH3 DONE"
