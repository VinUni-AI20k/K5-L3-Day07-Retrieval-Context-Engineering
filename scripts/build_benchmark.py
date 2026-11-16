"""Build the Day 7 benchmark from the Day 6 corpus and verify every gold chunk ID/quote.

Evaluator-side only. Outputs:
  benchmark/questions.json    agent-visible: id, split, question (no answers, no gold)
  benchmark/gold/gold.json    evaluator-only: answers, gold evidence, chunk IDs, absence checks
Agent / retrieval code must never read benchmark/gold/. Run: python scripts/build_benchmark.py
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import day6_store as d6  # noqa: E402

P = "B-soc3e-p0"  # chunk ID prefix of collection soc3e_B

# (id, split, type, question, expected_answer, [(chunk_id, evidence_quote), ...], mode)
# mode "any": listed (chunk, quote) pairs are alternatives; "all": every pair is required (multi-hop).
ANSWERABLE = [
    ("d01", "dev", "direct", "What did Charles Cooley mean by the looking glass self?",
     "People's self understanding is constructed, in part, by their perception of how others view them.",
     [(P + "134-003", "self understanding is constructed, in part, by their perception of how others view them")], "any"),
    ("d02", "dev", "direct", "In George Herbert Mead's account of self development, what can children do during the preparatory stage?",
     "They are only capable of imitation: they copy the actions of people they regularly interact with, such as caregivers.",
     [(P + "134-004", "During the preparatory stage, children are only capable of imitation")], "any"),
    ("d03", "dev", "direct", "In Kohlberg's theory of moral development, at which stage do young children experience the world around them only through their senses?",
     "The preconventional stage.",
     [(P + "135-002", "In the preconventional stage, young children, who lack a higher level of cognitive ability, experience the world around them only through their senses")], "any"),
    ("d04", "dev", "direct", "What is the Egalia preschool in Sweden trying to do about gender socialization?",
     "It lets children develop in a genderless environment, using neutral terms like 'friend' and setting up play areas and toys to avoid reinforcing gender expectations.",
     [(P + "136-002", "Egalia preschool in Sweden, where children develop in a genderless environment")], "any"),
    ("d05", "dev", "direct", "How many days of subsidized time off for families with newborns does the Swedish government policy provide?",
     "480 days, which can be shared between mothers and fathers.",
     [(P + "140-003", "480 days for families with newborns")], "any"),
    ("d06", "dev", "direct", "What do sociologists call the informal teaching done by schools?",
     "The hidden curriculum.",
     [(P + "142-000", "the hidden curriculum, the informal teaching done by schools")], "any"),
    ("d07", "dev", "direct", "What is anticipatory socialization?",
     "The preparation for future life roles, e.g. a couple cohabiting before marriage or soon-to-be parents reading infant care books.",
     [(P + "147-003", "anticipatory socialization, the preparation for future life roles")], "any"),
    ("d08", "dev", "direct", "What must new members of an institution go through first in the two-part resocialization process?",
     "A degradation ceremony, in which they leave behind their old identity and are given a new one.",
     [(P + "148-001", "must leave behind their old identity through what is known as a degradation ceremony")], "any"),
    ("d09", "dev", "direct", "According to the textbook, what is the minimum number of people needed to form a group?",
     "At least two people who interact with some frequency and share a sense that their identity is somehow attached to the group.",
     [(P + "161-001", "any collection of at least two people who interact with some frequency")], "any"),
    ("d10", "dev", "direct", "What is a reference group?",
     "A group that people compare themselves to; it provides a standard of measurement.",
     [(P + "164-000", "A reference group is a group that people compare themselves to")], "any"),
    ("d11", "dev", "direct", "Which leadership style issues orders and assigns tasks with little to no feedback from group members?",
     "Authoritarian leadership.",
     [(P + "167-002", "authoritarian leaders issue orders and assign tasks with little to no feedback from group members")], "any"),
    ("d12", "dev", "direct", "In Asch's conformity study, how many of the fifty test subjects gave an obviously erroneous answer at least once?",
     "Thirty-seven out of fifty.",
     [(P + "170-002", "thirty-seven out of fifty test subjects")], "any"),
    ("d13", "dev", "multi-hop", "According to Etzioni, what are the three categories of formal organizations?",
     "Normative (voluntary), coercive and utilitarian organizations.",
     [(P + "171-003", "formal organizations fall into three categories"),
      (P + "172-000", "The third type is utilitarian organizations")], "all"),
    ("d14", "dev", "direct", "What four characteristics did Max Weber attribute to a bureaucracy?",
     "A hierarchy of authority, a clear division of labor, explicit rules, and impersonality.",
     [(P + "172-001", "hierarchy of authority, a clear division of labor, explicit rules, and impersonality")], "any"),
    ("d15", "dev", "direct", "How many ways did Robert Merton define people respond to the gap between a socially accepted goal and no socially accepted means to reach it?",
     "Five (conformity, innovation, and the others listed in his strain theory).",
     [(P + "191-003", "Merton defined five ways people respond to this gap")], "any"),
    ("d16", "dev", "direct", "In Edwin Lemert's work, what is primary deviance?",
     "A violation of norms that does not result in any long-term effects on the individual's self-image or interactions with others.",
     [(P + "194-001", "Primary deviance is a violation of norms that does not result in any long-term effects")], "any"),
    ("t01", "test", "direct", "How many stages of development does Erik Erikson's theory include?",
     "Eight stages, from birth to death.",
     [(P + "133-004", "His theory includes eight stages of development")], "any"),
    ("t02", "test", "direct", "What did Emile Durkheim attribute differences in suicide rates to?",
     "Social causes (religious differences) rather than psychological causes.",
     [(P + "134-002", "attributed differences in suicide rates among people to social causes")], "any"),
    ("t03", "test", "direct", "Which pair of reunited twins is described as an example for studying the impact of nature?",
     "Elyse Schein and Paula Bernstein, reunited at age thirty-five in 2003.",
     [(P + "137-002", "Elyse Schein and Paula Bernstein")], "any"),
    ("t04", "test", "direct", "How does the textbook define a peer group?",
     "People who are similar in age and social status and who share interests.",
     [(P + "141-000", "A peer group is made up of people who are similar in age and social status and who share interests")], "any"),
    ("t05", "test", "direct", "Who is associated with the term McDonaldization of society, and what does it refer to?",
     "Ritzer (1993); the increasing presence of the fast food business model (efficiency, predictability, calculability, control) in social institutions.",
     [(P + "174-000", "The McDonaldization of Society (Ritzer 1993) refers to the increasing presence of the fast food business model")], "any"),
    ("t06", "test", "direct", "What theory did Edwin Sutherland establish about how deviant behavior develops?",
     "Differential association theory: individuals learn deviant behavior from those close to them who model it.",
     [(P + "196-001", "established differential association theory")], "any"),
    ("t07", "test", "direct", "What is the difference between a prison and a jail?",
     "A jail provides temporary confinement (small, local); prisons are large state or federal facilities for sentences of more than a year.",
     [(P + "203-002", "Prisons are facilities built for individuals serving sentences of more than a year")], "any"),
    ("t08", "test", "multi-hop", "Which reports a higher crime rate, the FBI's Uniform Crime Reports or the National Crime Victimization Survey, and why?",
     "The NCVS, because as a victim survey it likely picks up crimes that were never reported to the police, which the UCR (police reports) misses.",
     [(P + "200-001", "fails to account for the many crimes that go unreported"),
      (P + "201-000", "The NCVS reports a higher rate of crime than the UCR")], "all"),
]

# (id, split, question, absence_reason, [terms that must have 0 occurrences in the corpus])
UNANSWERABLE = [
    ("d17", "dev", "According to Piaget, at what age do children reach the formal operational stage?",
     "Piaget is mentioned (p134) only as a psychologist focused on social interaction; his stages and ages are never given.",
     ["formal operational", "sensorimotor"]),
    ("d18", "dev", "What is the average recidivism rate of released US prisoners within five years?",
     "Corrections, prisons, parole and probation are covered (p203), but no recidivism figure exists.",
     ["recidivism"]),
    ("d19", "dev", "What does Vygotsky's zone of proximal development say about how children learn?",
     "Self-development theorists are covered (Erikson, Piaget, Mead, Kohlberg, Gilligan) but Vygotsky is never mentioned.",
     ["vygotsky", "zone of proximal"]),
    ("t09", "test", "What happened to the participants in Zimbardo's Stanford prison experiment?",
     "Total institutions and resocialization are covered (p148), but the Stanford prison experiment is never mentioned.",
     ["zimbardo", "stanford prison"]),
    ("t10", "test", "How many states still use the death penalty according to the textbook?",
     "Crime, courts and corrections are covered (p201-203), but the death penalty is never discussed.",
     ["death penalty", "capital punishment"]),
    ("t11", "test", "How many children attend the Egalia preschool in Sweden?",
     "Egalia is described (p136) but no enrollment number is given anywhere in the corpus.",
     ["enrollment", "enrolled children"]),
]


def norm(s):
    return re.sub(r"\s+", " ", s)


def main():
    chunks_b = {c["id"]: c for c in d6.load_chunks("soc3e_B")}
    chunks_a = d6.load_chunks("soc3e_A")
    pages = [json.loads(l) for l in open(d6.day6_dir() / "data" / "processed" / "pages.jsonl", encoding="utf-8")]
    corpus = norm(" ".join(c["text"] for c in chunks_b.values())).lower()
    page_text = norm(" ".join(p["text"] for p in pages)).lower()
    questions, gold, errors = [], [], []
    for qid, split, qtype, q, ans, ev, mode in ANSWERABLE:
        items = []
        for cid, quote in ev:
            c = chunks_b.get(cid)
            if c is None:
                errors.append(f"{qid}: chunk {cid} missing")
                continue
            if quote not in c["text"]:
                errors.append(f"{qid}: quote not in {cid}: {quote!r}")
            alt_a = [a["id"] for a in chunks_a if a["page"] == c["page"] and quote in a["text"]]
            items.append({"chunk_id": cid, "source_id": c["source_id"], "page": c["page"],
                          "section": c["metadata"]["section"], "evidence": quote,
                          "also_in_chunks_A": alt_a})
        questions.append({"id": qid, "split": split, "question": q})
        g = {"id": qid, "split": split, "type": qtype, "answerable": True, "question": q, "expected_answer": ans,
             "evidence_mode": mode, "evidence": items,
             # starter/baseline.py schema: alternatives, each evidence inside one chunk of the right page
             "gold": [{"source_id": i["source_id"], "page": i["page"], "evidence": i["evidence"]} for i in items]}
        if mode == "all":
            g["scoring"] = ("multi-hop: ALL evidence items are required. Hit@k / context sufficiency counts only if every "
                            "item's chunk is retrieved/in context; also report partial coverage separately. "
                            "starter/baseline.py treats gold as alternatives, so it gives credit for any one item.")
        gold.append(g)
    for qid, split, q, reason, terms in UNANSWERABLE:
        counts = {t: corpus.count(t) for t in terms}
        page_counts = {t: page_text.count(t) for t in terms}
        if any(counts.values()) or any(page_counts.values()):
            errors.append(f"{qid}: terms present in corpus: {counts} {page_counts}")
        questions.append({"id": qid, "split": split, "question": q})
        gold.append({"id": qid, "split": split, "type": "unanswerable", "answerable": False, "question": q,
                     "expected_behavior": "search_and_abstain", "absence_reason": reason,
                     "absence_check": {"method": "case-insensitive exact-term count over all 241 soc3e_B chunks and all 69 pages in Day 6 data/processed/pages.jsonl",
                                       "terms": terms, "chunk_counts": counts, "page_counts": page_counts,
                                       "caveat": "lexical check only; related topic pages were read manually"}})
    if errors:
        print("\n".join(errors))
        sys.exit(1)
    (ROOT / "benchmark" / "gold").mkdir(parents=True, exist_ok=True)
    (ROOT / "benchmark" / "questions.json").write_text(json.dumps(questions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "benchmark" / "gold" / "gold.json").write_text(json.dumps(gold, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(Counter((g["split"], g["type"]) for g in gold))
    ids = {i["chunk_id"] for g in gold for i in g.get("evidence", [])}
    print(f"OK: {len(ids)} distinct gold chunk IDs all exist in soc3e_B and every quote is an exact substring")


if __name__ == "__main__":
    main()
