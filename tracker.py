"""Outreach pipeline automation.
Reads the tracker CSV and automatically:
  1. Flags overdue / due-soon follow-ups
  2. Drafts a follow-up message for each overdue lead
  3. Builds a stage-wise funnel with conversion and pipeline value
  4. Writes a weekly summary report (Markdown)

Run: python tracker.py [path_to_csv]
Outputs: reports/followups_due.csv, reports/weekly_report.md
"""
import sys
from datetime import date
import pandas as pd

CSV = sys.argv[1] if len(sys.argv) > 1 else "data/outreach_tracker.csv"
STAGE_ORDER = ["Lead Identified", "Contacted", "Pitch Sent",
               "Negotiation", "Closed Won", "Closed Lost"]
OPEN_STAGES = STAGE_ORDER[:4]

df = pd.read_csv(CSV, parse_dates=["last_contact_date", "next_followup_date"])
today = pd.Timestamp(date.today())

# ---------- 1. Follow-up flags ----------
open_df = df[df["stage"].isin(OPEN_STAGES)].copy()
open_df["days_overdue"] = (today - open_df["next_followup_date"]).dt.days
open_df["status"] = pd.cut(open_df["days_overdue"], bins=[-999, -4, 0, 999],
                           labels=["On track", "Due soon", "Overdue"])
due = open_df[open_df["status"].isin(["Overdue", "Due soon"])].sort_values(
    "days_overdue", ascending=False)

# ---------- 2. Draft follow-up messages ----------
TEMPLATES = {
    "Lead Identified": "Hi {c} team, we're reaching out about a partnership opportunity with our event. Could we schedule a quick call this week?",
    "Contacted": "Hi {c} team, following up on my earlier note. Happy to share how a partnership could reach your target audience. Are you free for a short call?",
    "Pitch Sent": "Hi {c} team, just checking whether you had a chance to review the proposal we sent. Happy to tailor it to your goals.",
    "Negotiation": "Hi {c} team, thanks for the discussion so far. Could we close the remaining points this week so we can finalise the partnership?",
}
due["draft_message"] = due.apply(lambda r: TEMPLATES[r["stage"]].format(c=r["company"]), axis=1)
due_out = due[["company", "owner", "stage", "next_followup_date", "days_overdue",
               "status", "expected_value_inr", "draft_message"]]
due_out.to_csv("reports/followups_due.csv", index=False)

# ---------- 3. Funnel & conversion ----------
funnel = df["stage"].value_counts().reindex(STAGE_ORDER, fill_value=0)
won, lost = funnel["Closed Won"], funnel["Closed Lost"]
win_rate = won / (won + lost) * 100 if (won + lost) else 0
open_value = open_df["expected_value_inr"].sum()
won_value = df.loc[df["stage"] == "Closed Won", "expected_value_inr"].sum()

by_owner = df.groupby("owner").agg(
    leads=("company", "count"),
    won=("stage", lambda s: (s == "Closed Won").sum()),
    value_won=("expected_value_inr", lambda v: v[df.loc[v.index, "stage"] == "Closed Won"].sum()),
).sort_values("value_won", ascending=False)

by_sector = df[df["stage"].isin(["Closed Won", "Closed Lost"])].groupby("sector")["stage"].agg(
    closed="count", won=lambda s: (s == "Closed Won").sum())
by_sector["win_rate_%"] = (by_sector["won"] / by_sector["closed"] * 100).round(1)
by_sector = by_sector.sort_values("win_rate_%", ascending=False)

# ---------- 4. Weekly report ----------
lines = [
    f"# Weekly Outreach Report - {today.date()}", "",
    "## Snapshot",
    f"- Total leads: **{len(df)}**",
    f"- Closed won: **{won}** (value: INR {won_value:,})",
    f"- Win rate (won / closed): **{win_rate:.1f}%**",
    f"- Open pipeline value: **INR {open_value:,}**",
    f"- Follow-ups overdue: **{(due['status'] == 'Overdue').sum()}**, due soon: **{(due['status'] == 'Due soon').sum()}**",
    "", "## Funnel", funnel.to_markdown(), "",
    "## Performance by owner", by_owner.to_markdown(), "",
    "## Win rate by sector (closed deals only)", by_sector.to_markdown(), "",
    "## Top 5 follow-ups to do first (by days overdue)",
    due_out.head(5)[["company", "owner", "stage", "days_overdue"]].to_markdown(index=False), "",
    "_Full list with draft messages: reports/followups_due.csv_",
]
with open("reports/weekly_report.md", "w") as f:
    f.write("\n".join(lines))

print("\n".join(lines))
