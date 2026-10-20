#!/usr/bin/env python3
"""Regenerate templates/approved.json from the rulebook's "Every draft" section.

The template wording is copied programmatically, character for character, so
nobody retypes it. Metadata (id, kind, links, signer-only) is added here.
Variants are the rulebook text with its written alternatives split apart;
no words are added. Run after any rulebook change, then run the tests.

Usage: python3 scripts/build_templates.py [rulebook.md] [out.json]
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RULEBOOK = ROOT / "docs" / "build-engine-rulebook.md"
DEFAULT_OUT = ROOT / "templates" / "approved.json"

# title in the rulebook -> metadata
META = {
    "Layer 1: Gmail vacation reply (you set it)": dict(
        id="vacation_reply", kind="matt_sets", note="Set by Matt in Gmail. Never sent by the engine."),
    "Away line in every kickoff and welcome email": dict(
        id="away_line", kind="embedded_line", note="Goes inside kickoff and welcome emails Matt sends."),
    "Reminder 1 (day 2)": dict(id="reminder_1", kind="engine_auto", reminder=True,
                               links=["form_link", "upload_link"]),
    "Reminder 2 (day 4)": dict(id="reminder_2", kind="engine_auto", reminder=True,
                               links=["form_link", "upload_link"]),
    "Reminder 3 (day 7)": dict(id="reminder_3", kind="engine_auto", reminder=True,
                               links=["form_link", "upload_link"]),
    "Template 1: files saved": dict(id="template_1", kind="engine_auto"),
    "Template 2: photo worries": dict(id="template_2", kind="engine_auto", links=["upload_link"]),
    "Template 3: changes logged": dict(id="template_3", kind="engine_auto", client_words=["bullets"]),
    "Template 4: fact update": dict(id="template_4", kind="engine_auto", client_words=["fact"]),
    "Template 5: chasing": dict(id="template_5", kind="engine_auto"),
    "Photo origin check (once)": dict(id="photo_origin", kind="still_needed_line"),
    "ICO question (plain words)": dict(id="ico_question", kind="still_needed_line"),
    "Preview email (AG-16, you send)": dict(id="preview_email", kind="matt_sends", links=["preview_link"]),
    "+48h nudge (AG-16, you send)": dict(id="nudge_48h", kind="matt_sends"),
    "Approval question (you send)": dict(id="approval_question", kind="matt_sends", signer_only=True),
    "Contradictory feedback (to the signer only)": dict(id="contradictory_feedback", kind="matt_sends",
                                                         signer_only=True,
                                                         client_words=["item", "option_a", "option_b"]),
    "Holding line (red email, once per trip)": dict(id="holding_line", kind="engine_auto", red_allowed=True,
                                                     once_per_trip=True),
    "Link won't open": dict(id="link_wont_open", kind="engine_auto", links=["upload_link"]),
    "WhatsApp Business away message (you set it, clients who use WhatsApp)": dict(
        id="whatsapp_away", kind="matt_sets", note="Set by Matt in WhatsApp Business. Never sent by the engine."),
    "Trading name question (signer only)": dict(id="trading_name_question", kind="matt_sends", signer_only=True),
    "Logo file question (Still needed line)": dict(id="logo_file_question", kind="still_needed_line"),
    "Urgent, not ours (approved sender only)": dict(id="urgent_not_ours", kind="engine_auto", red_allowed=True),
    "Logo as PNG (only if SVG conversion fails)": dict(id="logo_png", kind="still_needed_line"),
}


def parse_every_draft(text):
    sec = text.split("## Every draft", 1)[1].split("\n## ", 1)[0]
    out = []
    for block in re.split(r"\n(?=\*\*)", sec.strip()):
        m = re.match(r"\*\*(.+?)\*\*\n(.*)", block, re.S)
        if not m:
            continue
        title, rest = m.group(1), m.group(2)
        lines = [ln[2:] if ln.startswith("> ") else ln[1:] if ln.startswith(">") else None
                 for ln in rest.rstrip("\n").split("\n")]
        lines = [ln for ln in lines if ln is not None]
        out.append((title, "\n".join(lines)))
    return out


def variants_for(tid, text):
    """Split written alternatives into renderable variants, words unchanged."""
    if tid == "template_1":
        head, tail = text.split("{Still needed:", 1)
        head = head.replace("{, other files}", "{other_files}")
        still = "Still needed: {missing_items}."
        alldone = "That's all the files I need for now."
        end = " Matt (automatic confirmation)"
        return [
            {"id": "still_needed", "text": head + still + end},
            {"id": "all_done", "text": head + alldone + end},
        ]
    if tid == "template_5":
        quoted = re.findall(r'"([^"]+)"', text)
        end = " Matt (automatic confirmation)"
        return [
            {"id": "preview_ready_or_later", "text": quoted[0] + end, "requires_build_status_min": 6},
            {"id": "otherwise", "text": quoted[1] + end},
        ]
    if tid == "template_4":
        return [{"id": "main", "text": text.replace("{fact, in their words}", "{fact}")}]
    return [{"id": "main", "text": text}]


def main():
    rb = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_RULEBOOK
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUT
    parsed = parse_every_draft(rb.read_text(encoding="utf-8"))
    templates = {}
    for title, text in parsed:
        if title not in META:
            raise SystemExit(f"Unknown draft title in rulebook: {title!r}. Add it to META.")
        meta = dict(META[title])
        tid = meta.pop("id")
        entry = {
            "title": title,
            "text": text,
            "variants": variants_for(tid, text),
            "kind": meta.pop("kind"),
            "links": meta.pop("links", []),
            "signer_only": meta.pop("signer_only", False),
            "reminder": meta.pop("reminder", False),
            "red_allowed": meta.pop("red_allowed", False),
            "once_per_trip": meta.pop("once_per_trip", False),
            "client_words": meta.pop("client_words", []),
        }
        entry.update(meta)
        templates[tid] = entry
    missing = set(m["id"] for m in META.values()) - set(templates)
    if missing:
        raise SystemExit(f"Rulebook is missing drafts: {sorted(missing)}")
    doc = {
        "_source": "docs/build-engine-rulebook.md, section 'Every draft'. Wording copied by script, word for word.",
        "_kinds": {
            "engine_auto": "Engine-labelled email. In supervised mode: a Gmail draft for Matt, never sent.",
            "matt_sends": "Drafted for Matt; Matt presses send.",
            "still_needed_line": "Only as the 'Still needed' line of a reminder or confirmation already due.",
            "embedded_line": "A fixed line inside an email Matt sends.",
            "matt_sets": "Matt sets it himself. The engine never sends it.",
        },
        "templates": templates,
    }
    out.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(templates)} templates to {out}")


if __name__ == "__main__":
    main()
