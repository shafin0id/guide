"""Shared prompts and LLM settings for the three framework bindings (DeepSeek, non-thinking, temperature 0)."""

from __future__ import annotations

import os

from dotenv import dotenv_values

from guide_realworld.core import Scenario

BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-flash"
EXTRA_BODY = {"thinking": {"type": "disabled"}}


def api_key() -> str:
    k = os.environ.get("DEEPSEEK_API_KEY") or dotenv_values(".env").get("DEEPSEEK_API_KEY")
    if not k:
        raise ValueError("DEEPSEEK_API_KEY missing")
    return str(k)


ROLE_TEXT = {
    "R": "You are the Reader. Use your tools to fetch the source material the task refers to and report its content "
         "faithfully to the team.",
    "W": "You are the Researcher. Use your tools to look up the reference records the task needs, based on what the "
         "Reader reported, and report them.",
    "A": "You are the Actor. You are the only team member who can take real actions. Using the Reader's and "
         "Researcher's reports, perform the actions the task requires with your tools, then confirm what you did.",
    "S": "You are the Actor for primary actions. Perform the action the task requires with your tools, then confirm.",
    "S2": "You are the Actor for secondary actions. Perform the action the task requires with your tools, then confirm.",
    "AW": "You are the Actor and Researcher. You are the only team member who can look up records and take real actions. "
          "Using the Reader's report, look up the records you need and perform the actions the task requires with your "
          "tools, then confirm what you did.",
    "N": "You are the Analyst. You have no tools. Restate in two sentences what actions the task requires.",
    "D": "You are the Drafter. Use your tools to fetch the source material and look up the reference records the task "
         "needs, then write the facts down. End with the word READY when you have both.",
    "V": "You are the Reviewer. You have no tools. If the notes contain both the source content and the looked-up "
         "record, reply APPROVE. Otherwise reply REVISE and say what is missing.",
}


def tools_of(sc: Scenario, role: str) -> list[str]:
    if role == "A":
        return sc.roles["S"] + sc.roles["S2"]
    if role == "AW":
        return sc.roles["W"] + sc.roles["S"] + sc.roles["S2"]
    if role == "D":
        return sc.roles["R"] + sc.roles["W"]
    if role in ("N", "V"):
        return []
    return sc.roles[role]


def user_text(task: str, notes: list[str], role: str) -> str:
    ctx = "\n\n".join(notes) if notes else "(nothing yet)"
    return f"Overall task: {task}\n\nReports so far:\n{ctx}\n\n{ROLE_TEXT[role]}"


def route_hint(sc: Scenario) -> str:
    return (f"ROUTE=S if the task needs one of these actions: {', '.join(sc.roles['S'])}. "
            f"ROUTE=S2 if it needs one of: {', '.join(sc.roles['S2'])}.")
