# Blok: search, App Store and AI visibility plan

Goal: when a parent searches "parental control app", "screen time app for kids", "block apps on my child's iPhone"
(or the same in one of our 16 languages) in Google, the App Store or an AI assistant, the answer leads to
Blok's App Store page.

## How ranking actually works here

There are three places to win, and each runs on different signals:

| Where | What decides the ranking | What the website does for it |
|---|---|---|
| **App Store search** | App name, subtitle and keyword field per localization; download velocity; tap-through and install rate; ratings | Little directly. It sends traffic, and every web install counts as a download |
| **Google / Bing** | For "X app" searches Google often shows the `apps.apple.com` page itself. It ranks on the name and subtitle, the description, ratings and links pointing to it. Our site can rank next to it | Ranks on its own, links to the App Store page in every language, and gives search engines a consistent description of the app ("entity") |
| **AI answers** (ChatGPT, Perplexity, Gemini, Google AI Overviews, Copilot) | Pages that are crawled and quotable and say the same thing as other sources (Reddit, reviews, roundups, YouTube) | `llms.txt`, plain definitions, FAQ structured data, AI crawlers allowed, and the "not to be confused with" text |

Being called "Blok" means the bare name will never rank. **Win "Blok: Parental Control" plus the generic searches
that don't use a brand at all.** In the smaller-language markets (hr, hu, el, fi, da, no, pl, tr) there is far less
competition than in English or German, and that's where the first rankings will come from.

## Done in this repo

- 16 language versions (sv, en, da, de, el, es, fr, hr, it, hu, nl, no, pl, fi, tr, ar), each written around that
  country's own search terms, with Apple's local name for Screen Time. Arabic is laid out right to left and
  aimed at Saudi Arabia, the UAE and the wider Arab world.
- Full `hreflang` cross-links on every page and in `sitemap.xml`, with `x-default` pointing to English.
- Structured data per language: `MobileApplication` and `FAQPage`. After launch, `downloadUrl` and `sameAs` point
  to that country's App Store page.
- A fixed name in every language ("Blok: Parental Control" / "Blok: Kindersicherung" / …) and an FAQ entry
  "Are there other apps called Blok?" that AI answers can quote.
- New FAQ entries that match what parents search for: "block TikTok/YouTube/Snapchat/games", "how much does it cost".
- `llms.txt` with a "Not to be confused with" section; `robots.txt` allows search and AI crawlers.
- Launch switch: set `APP_STORE_ID` in `build.py`. Every "Coming soon" button then becomes a link to that
  language's App Store storefront, and the Smart App Banner and JSON-LD links are added.
- Custom domain switch: set `DOMAIN` in `build.py`. That rewrites every canonical, hreflang, sitemap and `llms.txt`
  URL and writes `CNAME`.
- Proposed App Store metadata per country in `marketing/aso/<lang>.json`: name, subtitle, keyword field,
  promotional text and search phrases.

## Phase 0: before launch (now)

1. **Move to your domain.** In GitHub, go to repo, Settings, Pages, Custom domain. Add the DNS records GitHub
   shows, tick "Enforce HTTPS", set `DOMAIN` in `build.py` and rebuild. GitHub then redirects the old
   `github.io` URLs to the new domain.
2. **Google Search Console and Bing Webmaster Tools.** Verify the domain in both and submit `sitemap.xml`. Bing
   matters for AI too: ChatGPT search and Copilot draw on Bing's index. In Bing, also turn on IndexNow or use the
   URL submission tool.
3. **Put all 14 new localizations in App Store Connect** using `marketing/aso/*.json`:
   - Use the name and subtitle as proposed.
   - The keyword field has 100 characters, commas without spaces, and no words already used in the name or
     subtitle.
   - Some storefronts also index a second localization (for example, the US storefront also indexes Spanish
     (Mexico)), so you can fill those with extra keywords. Check Apple's current list before you rely on it.
   - Set the Marketing URL to the site and the Support URL to `/support.html`.
4. **Use App Store pre-orders.** They give you the real `apps.apple.com` URL months before release. Set
   `APP_STORE_ID` at that point so the site, links and mentions all start building up for the store page early.
5. **Localize the app itself.** Today the app is only in Swedish and English, and the App Store shows that. Parents
   in Germany or Poland install far less often when the app isn't in their language, and install rate feeds App
   Store ranking. Xcode String Catalogs make this mostly a translation job. Start with de, fr, es, it, nl and pl.
6. **Localized screenshots.** Use the caption text for the main benefit plus a keyword ("Kindersicherung in
   einem Tipp"). The first two screenshots carry most of the install decision.
7. **Get the translations checked by native speakers.** They are good, but one native parent per market reading
   them for an hour is cheap insurance.

## Phase 1: launch

- Set `APP_STORE_ID`, rebuild and push.
- Swap the text button for Apple's official localized "Download on the App Store" badges (Apple Marketing Tools).
- Add App Store campaign links (`?pt=<provider token>&ct=web-de`) so App Store Connect Analytics shows which
  language page brings installs.
- Ask for ratings at a good moment, for example after the parent's first confirmed lock, using
  `SKStoreReviewController`. Ratings drive both App Store ranking and Google's star display for the App Store page.
- Nominate the app in App Store Connect's featuring nomination form. Parental control and wellbeing are recurring
  editorial themes.

## Phase 2: content (months 1–6)

One page per search intent, in English first, then de, fr, es, nl and pl. Each page opens with a 40–60 word answer
an AI assistant can quote, followed by steps, an FAQ block and a visible "updated" date.

- How to lock your child's iPhone remotely (step by step, with and without Blok)
- How to block TikTok / YouTube / Roblox on a child's iPhone
- Apple Screen Time vs Blok: what Screen Time does well, and where a one-tap remote lock helps
- Best parental control apps for iPhone in 2026: an honest comparison including Apple Screen Time, Google Family
  Link, Qustodio, OurPact and Bark. Honest comparisons get linked and cited, while one-sided ones don't.
- Phone-free bedtime and homework routines (an age-by-age guide)
- What screen time is right at each age, citing public-health guidance per country (WHO, national agencies)

Also add an **About** page covering who builds Blok and why, with a photo and contact details. Link the social
profiles from the `Organization` JSON-LD with `sameAs`. It gives search engines and AI assistants a clear
real-world entity behind the name.

## Phase 3: authority and AI visibility (ongoing)

- **Roundups.** Email the authors of "best parental control apps" articles in each country and offer a free year
  and a short demo video. One link from a national parenting site is worth more than a hundred directory links.
- **Places AI assistants read:**
  - Answer real questions on Reddit (r/Parenting, r/ScreenTime, r/iphone) and local forums, saying openly that
    you're the developer.
  - Post a 60-second demo on YouTube in each language. YouTube shows up a lot in Google AI Overviews.
  - List Blok on AlternativeTo as an alternative to OurPact and Screen Time, and on Product Hunt at launch.
- **Wikidata.** Create an item for "Blok: Parental Control": instance of mobile app, platform iOS, developer,
  official website, App Store ID. Wikidata is used to tell apart things with the same name.
- **Press in Sweden first** (a local developer story), then pitch the "lock, not a spy" privacy angle to EU
  media.
- **Keep it consistent.** Use the same name, one-line description and icon on every profile and listing.

## Measuring it

| What | Where | Check |
|---|---|---|
| Impressions and clicks per country and query | Search Console, Bing Webmaster | Monthly |
| App Store impressions by source (Search vs Web Referrer) and install rate | App Store Connect Analytics | Weekly after launch |
| Keyword rank per storefront | An ASO tool (AppFigures, AppTweak, Astro) | Monthly; rework the keyword fields every 4–6 weeks |
| AI visibility | Ask ChatGPT, Perplexity, Gemini and Copilot the 5 main questions in en, de, sv and one small market; note whether Blok is named and which source is cited | Monthly |

Realistic timing: a new domain usually takes 2–4 months to rank for long-tail searches in small languages.
Head terms like "parental control app" in English take a year or more and plenty of links, and are dominated by
Apple, Google, Qustodio and Bark. So put the effort into App Store ranking, the small-language markets and
long-tail searches first.
