# About BC Vote Match

## What this is

BC Vote Match is a free, independent tool that helps British Columbians see where their policy views line up with the parties contesting the 2026 provincial election. You answer 18 statements. We show you the distance between your answers and each party's published positions, on the topics and on a simple two-axis map.

## Why we built it

Snap elections compress the time anyone has to read five platforms. Most voters will never open a policy PDF, and the coverage they do see is framed by people with opinions. We wanted a small, honest instrument that does one thing: compares what you think to what the parties have actually said, in public, in their own words, and shows the receipts.

The condition for taking it seriously is transparency. If the questions, the codings, or the math were a black box, the tool would be just another bit of campaign noise. So the method is public, the coding table is public with every quote and source link, and the code and data are open source. If you think we got something wrong, you can check, and you can tell us.

## How it is built and funded

- **Open source.** The site code, the question set, the archived sources, and the full coding table are published in the project repository. The data is reusable under the repository's licence with attribution.
- **Independent.** This is a volunteer project. It is not affiliated with Elections BC, any political party, any candidate, Vote Compass, or Vox Pop Labs, and it accepts no money from parties, candidates, or their financial agents.
- **Versioned and dated.** Parties change positions during campaigns. When they do, we recode, version the change, and publish what moved. Every coding table carries its version and date.

## Who is behind it

The project is run by a small independent team of volunteers, listed in the repository. Nobody on the team holds a role with a registered party or candidate in this election. The work of collecting sources, coding positions, and verifying quotes is done by people and by tooling under human review, with the final publish decision made by a human every time.

## Corrections and how to submit them

We want corrections. A correction with evidence is a gift; it makes the tool more accurate for everyone who uses it next.

To submit one, contact us at the address in the repository README, or open an issue in the public repository. The most useful correction includes:

1. The question id (for example, q19) and the party.
2. The code you think is wrong, and the code you think it should be.
3. A verbatim quote from a public source (with the URL) that supports the change.

We evaluate every submission the same way: does the quote support a different code on our published scale? If yes, we recode, version it, and publish the change and the reason. If no, we publish the challenge and why we are leaving the code alone. Either way you get an answer, and either way the outcome is logged publicly.

Please note what a correction is not. "This party is bad" is not a correction. "The question is biased" is feedback about the question set, which we also read and log, but it does not change a code. A quote changes a code.

## Contact

See the project repository for the current contact address and issue tracker. We read everything. We are a small volunteer team during an election campaign, so replies may take a little time.
