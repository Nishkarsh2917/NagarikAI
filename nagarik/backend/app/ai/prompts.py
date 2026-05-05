"""
Per-step prompts. Each is narrow, deterministic, and JSON-output where possible.

Hard rules baked in:
  - Use ONLY facts present in the supplied text.
  - If unknown, return null — never guess.
  - Neutral, citizen-friendly tone.
  - Confidence is self-reported per step.
"""
from __future__ import annotations

CLASSIFY_PROMPT = """\
You are classifying a single Indian government / civic document.

Given the title and a text excerpt, choose ONE document_type from this exact list:
  - press_release
  - policy
  - budget
  - bill
  - affidavit
  - constituency_update
  - local_update
  - feedback
  - unknown

Respond with ONLY a JSON object, no prose, no markdown fences:
{{"document_type": "<one of the above>", "confidence": <0.0..1.0>}}

If you cannot tell, return "unknown" with low confidence.

TITLE: {title}

EXCERPT (first 1500 chars):
{excerpt}
"""

EXTRACT_PROMPT = """\
You are extracting structured facts from an Indian government / civic document.

Use ONLY information that is literally present in the text below.
If a field is not stated, set it to null. Do not infer or guess.

Respond with ONLY a JSON object in this exact shape:
{{
  "who": <string or null>,             // primary actor (ministry, official, body)
  "what": <string or null>,            // main action or announcement, in <=20 words
  "where": <string or null>,           // place, constituency, district, state — most specific available
  "when": <string or null>,            // date or timeframe as written in the text
  "affected_group": <string or null>,  // who is impacted (e.g. "farmers", "residents of Delhi")
  "key_numbers": [<strings>],          // amounts, percentages, counts as written; [] if none
  "deadlines": [<strings>],            // any explicit deadlines; [] if none
  "actions_required": [<strings>],     // anything citizens must do; [] if none
  "named_entities": [<strings>],       // people, orgs, places, schemes — deduplicated
  "confidence": <0.0..1.0>
}}

TITLE: {title}

TEXT:
{text}
"""

SUMMARIZE_PROMPT_EN = """\
You are writing a citizen-friendly summary of an Indian government / civic document.

Rules:
  - Use ONLY facts present in the text below.
  - Neutral and nonpartisan. No political spin, no opinion.
  - Plain language a non-expert can understand. No jargon.
  - If something isn't in the text, omit it. Do not invent.

Respond with ONLY a JSON object in this exact shape:
{{
  "one_line": <string>,               // <= 25 words, a single sentence
  "three_bullets": [<string>, <string>, <string>],   // each <= 25 words
  "why_it_matters": <string>,         // 1-2 sentences, plain impact, no rhetoric
  "who_is_affected": <string>,        // 1 sentence, concrete group(s)
  "confidence": <0.0..1.0>
}}

TITLE: {title}

TEXT:
{text}
"""

SUMMARIZE_PROMPT_HI = """\
आप एक भारतीय सरकारी / नागरिक दस्तावेज़ का सरल हिंदी सारांश लिख रहे हैं।

नियम:
  - केवल दिए गए पाठ में मौजूद तथ्यों का उपयोग करें।
  - तटस्थ और गैर-राजनीतिक भाषा। कोई राय नहीं।
  - सरल भाषा, बिना तकनीकी शब्दों के।
  - यदि कोई जानकारी पाठ में नहीं है, तो उसे शामिल न करें।

केवल JSON उत्तर दें, इस आकार में:
{{
  "one_line": <string>,
  "three_bullets": [<string>, <string>, <string>],
  "why_it_matters": <string>,
  "who_is_affected": <string>,
  "confidence": <0.0..1.0>
}}

शीर्षक: {title}

पाठ:
{text}
"""

MAP_TOPIC_PROMPT = """\
Given a document title and excerpt, choose up to 3 topic tags from this list:
{topic_list}

Also infer a likely Indian state, district, or constituency mentioned in the text — only if EXPLICITLY named.

Respond with ONLY a JSON object:
{{
  "topics": [<string>, ...],          // 0-3 items from the supplied list
  "state": <string or null>,          // state name as written, or null
  "district": <string or null>,
  "constituency": <string or null>,
  "confidence": <0.0..1.0>
}}

TITLE: {title}

EXCERPT:
{excerpt}
"""

CLUSTER_FEEDBACK_PROMPT = """\
You are summarising a cluster of citizen feedback messages on a single topic and constituency.

Rules:
  - Neutral tone. No political framing.
  - Use only what the messages actually say. No invention.
  - Identify recurring complaints if any.

Respond with ONLY a JSON object:
{{
  "summary": <string>,                  // 2-3 sentences
  "recurring_complaints": [<string>, ...],
  "suggested_actions": [<string>, ...], // only if citizens themselves suggest them
  "confidence": <0.0..1.0>
}}

FEEDBACK MESSAGES:
{messages}
"""
