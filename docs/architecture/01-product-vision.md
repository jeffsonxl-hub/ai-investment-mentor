# Product Vision 〞 AI Investment Mentor

## Target User

The user is an individual A-share investor who:
- Trades part-time alongside a full-time job, with 30每60 minutes per day for research
- Has basic market literacy (understands PE ratios, sectors, market cap) but is not a professional analyst
- Currently relies on broker apps, financial news apps, and social media for stock ideas
- Feels overwhelmed by information volume 〞 too many stocks, too many news items, no clear signal
- Wants to learn *why* a stock moved or deserves attention, not just be told what to buy
- Makes their own final trading decisions 〞 they do not want a black-box trading bot

## The Problem

Existing tools for Chinese retail investors fall into two categories, and neither works well:

1. **Information firehoses** (Eastmoney, Xueqiu, Flush): Show everything 〞 real-time quotes, news feeds, forum posts, technical indicators. The user drowns in data but gets no synthesis. The cognitive load of filtering signal from noise is entirely on the human.

2. **Opaque recommendation engines** (broker research, paid stock-picking services): Deliver conclusions without explanations. "Buy this stock, target price X." The user cannot evaluate the reasoning, cannot learn from the recommendation, and cannot adapt it to their own risk tolerance.

Neither approach teaches the user to become a better investor over time.

## How We Solve It

The AI Investment Mentor sits between raw data and final decision. It does three things:

1. **Synthesizes** 〞 Gathers market context, news, fundamentals, and technical indicators into structured evidence packets
2. **Explains** 〞 Every recommendation comes with: the evidence chain that produced it, a confidence score, explicit risks, and what the user should watch next
3. **Teaches** 〞 The user sees the decision process step by step. Over weeks and months, they internalize the framework and become less dependent on the tool

The core mechanic: **AI narrows the A-share universe from ~5000 stocks to 5每10 explainable candidates, and the human makes the final choice.**

This is not a trading bot. It never executes orders. It produces a daily report, not real-time alerts.

## Daily User Journey (V1 Sketch)

The user opens the morning report at 8:30 AM. They see:

1. **Market regime summary** 〞 one paragraph: are we in a risk-on or risk-off environment? Which sectors have momentum? What policy or macro event matters today?

2. **Theme map** 〞 two or three leading themes (e.g., "AI semiconductor rotation continues," "precious metals strength on policy uncertainty"), each with 1每2 supporting data points

3. **Candidate watchlist** 〞 five stocks that match the current regime and themes. Each entry shows: why it was selected, which evidence supports it (fundamental, technical, news), a confidence rating, and key risks to watch

4. **One deep-dive pick** 〞 the highest-conviction candidate gets a longer section: business summary, catalyst, risk scenario, suggested price zone (not a target), and what would invalidate the thesis

Total reading time: 5每8 minutes. All supporting data is one click away, but the surface report is scannable.

## Success Criteria (V1)

- A user with basic market knowledge can read the morning report and articulate *why* a stock is interesting without memorizing raw data points
- At least 70% of recommendations include evidence from two or more independent sources (news + fundamentals, or technical + capital flow, etc.)
- The report generation pipeline runs end-to-end with zero manual intervention
- A user reviewing a past recommendation can trace the full evidence chain back to source data

## Non-Goals (What We Do Not Build)

- **Automated trading or order execution.** The human always pulls the trigger
- **Real-time alerting or streaming.** V1 is daily batch analysis, not intraday
- **Portfolio optimization or position sizing.** We recommend stocks, not allocation math
- **Backtesting or performance benchmarking against indices.** V1 is about explaining the present, not proving past returns
- **Multi-user or SaaS.** This is a single-user personal tool
- **Hong Kong, US, or other non-A-share markets.** Scope is mainland China A-shares only

## Future Vision (Not V1)

Later phases may add: personalized watchlist learning (the system adapts to stocks you care about), weekend portfolio review with performance attribution, and a feedback loop where the user's actual picks are tracked against the AI's recommendations to calibrate confidence scores over time.
