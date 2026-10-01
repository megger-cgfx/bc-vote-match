#!/usr/bin/env bash
set -u
cd .
fetch() { python3 agents/fetch_source.py --party ndp "$@" >/dev/null 2>&1; echo "done: $*"; }

fetch --url "https://www.bcndp.ca/action-for-you" --type policy --title "Results for You"
fetch --url "https://www.bcndp.ca/releases" --type other --title "Media Centre (news releases)"
fetch --url "https://www.bcndp.ca/latest/our-platform-out-heres-why-you-should-get-behind-it" --type platform --title "Our platform is out. Here's why you should get behind it."
fetch --url "https://www.bcndp.ca/latest/climate-change-real-and-happening-now-heres-how-were-taking-action-people" --type policy --title "Climate change is real - here's how we're taking action for people"
fetch --url "https://www.bcndp.ca/releases/david-eby-shares-middle-class-tax-cut-plan-families" --type release --title "David Eby shares middle-class tax cut plan with families"
fetch --url "https://www.bcndp.ca/releases/onebc-platform-would-raise-deficit-10-billion-force-massive-cuts" --type release --title "OneBC Platform would raise deficit by $10 billion, force massive cuts"
fetch --url "https://www.bcndp.ca/releases/rustads-semi-costed-platform-fails-impress" --type release --title "Rustad's semi-costed platform fails to impress"
fetch --url "https://bcballot.ca/platforms/" --type media --title "BC election platforms 2026: Compare the party platforms (bcballot.ca)"
fetch --url "https://vancouversun.com/business/david-eby-bets-big-on-potential-for-more-major-projects-in-build-b-c-strong-platform" --type media --title "David Eby bets big on potential for more major projects in 'Build B.C. Strong' platform (Vancouver Sun)"
fetch --url "https://vancouver.citynews.ca/2026/09/25/b-c-s-eby-says-ndp-would-tax-new-unsold-condos-raise-speculation-vacancy-fees/" --type media --title "Eby says NDP would tax new, unsold condos, raise speculation, vacancy fees (CityNews)"
fetch --url "https://www.ctvnews.ca/vancouver/article/eby-says-bc-ndp-would-tax-new-unsold-condos-and-raise-speculation-vacancy-fees" --type media --title "Eby says B.C. NDP would tax new, unsold condos and raise speculation, vacancy fees (CTV)"
fetch --url "https://infonews.ca/news/4372098/bc-ndp-unveils-election-platform-focusing-on-tough-challenges-and-john-rustad" --type media --title "B.C. NDP unveils election platform, focusing on 'tough challenges' and John Rustad (InfoNews)"
fetch --url "https://westernstandard.news/news/cost-of-living-what-is-each-party-promising-british-columbians/58635" --type media --title "COST OF LIVING: What is each party promising British Columbians? (Western Standard)"
fetch --url "https://itsryanclayton.substack.com/p/ndp-promises" --type media --title "New democratic promises (Substack analysis of NDP platform)"
fetch --url "https://lims.leg.bc.ca/hdms/file/Debates/43rd2nd/20260218pm-Hansard-n118.html" --type hansard --title "Hansard - Feb 18 2026 Afternoon, Issue No. 118" --published "2026-02-18"
fetch --url "https://lims.leg.bc.ca/hdms/file/Debates/43rd2nd/20260330pm-House-Blues.htm" --type hansard --title "Hansard - Mar 30 2026 Afternoon, Issue No. 143" --published "2026-03-30"
fetch --url "https://lims.leg.bc.ca/hdms/file/Debates/43rd2nd/20260414am-Hansard-n151.html" --type hansard --title "Hansard - Apr 14 2026 Morning, Issue No. 151" --published "2026-04-14"
fetch --url "https://lims.leg.bc.ca/hdms/file/Debates/43rd2nd/20260219pm-Hansard-n120.html" --type hansard --title "Hansard - Feb 19 2026 Afternoon, Issue No. 120" --published "2026-02-19"
fetch --url "https://www.bcndp.ca/latest/reconciliation-respect-and-better-future" --type policy --title "Reconciliation, respect and a better future"
fetch --url "https://www.bcndp.ca/releases/past-mla-advocate-and-community-leader-jodie-wickens-nominated-coquitlam-burke-mountain" --type release --title "Jodie Wickens nominated in Coquitlam-Burke Mountain with plan to put people and families first"
fetch --url "https://news.gov.bc.ca/releases/2026AG0040-000711" --type other --title "BC welcomes Bail and Sentencing Reform Act receiving royal assent (gov.bc.ca)"
fetch --url "https://vancouver.citynews.ca/2026/04/21/dripa-reversal-npd-government-hot-seat-question-period" --type media --title "DRIPA reversal puts NDP government in hot seat (CityNews)"
fetch --url "https://www.leg.bc.ca/hansard-content/Debates/43rd2nd/20260527pm-Hansard-n186.html" --type hansard --title "Hansard - May 27 2026 Afternoon, Issue No. 186" --published "2026-05-27"
echo "ALL DONE"
