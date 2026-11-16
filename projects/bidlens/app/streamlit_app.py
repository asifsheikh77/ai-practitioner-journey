"""BidLens Q&A demo.  Run from projects/bidlens:  streamlit run app/streamlit_app.py"""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bidlens.answering import answer_question
from bidlens.gate import EvidenceGate
from bidlens.llm import LLMError, make_client
from bidlens.runtime import DEFAULT_CORPUS, load_retriever

MAX_QUESTION_CHARS = 500
MIN_QUESTION_CHARS = 5
EXAMPLES = [
    "What minimum annual turnover must a bidder demonstrate?",
    "What is the contract period, and can it be extended?",
    "Which company ultimately won this tender?",
    "What is the capital of France?",
]

st.set_page_config(page_title="BidLens", layout="wide")
st.title("BidLens — grounded RFP Q&A")
st.caption("Ask any question about the Central Bank of India UPI RFP. Answers use only retrieved RFP passages "
           "and are evidence for human review, not a compliance or bid decision.")


@st.cache_resource(show_spinner="Loading corpus and embeddings…")
def get_retriever():
    return load_retriever(DEFAULT_CORPUS)


def use_example(text: str) -> None:
    st.session_state["question"] = text   # callback runs before the input is drawn


with st.sidebar:
    provider = st.radio("Model runtime", ["ollama", "openai", "gemini"])
    if provider != "ollama":
        st.warning(f"Retrieved RFP passages are sent to the {provider} API.")
    model = st.text_input("Model (blank = default)") or None
    use_judge = st.checkbox("LLM claim-support judge", value=False)
    min_sem = st.slider("Gate: min semantic similarity", 0.0, 0.8, EvidenceGate().min_semantic, 0.01)
    min_cov = st.slider("Gate: min query-term coverage", 0.0, 1.0, EvidenceGate().min_coverage, 0.05)

with st.form("ask_form"):
    st.text_input("Your question", key="question", max_chars=MAX_QUESTION_CHARS,
                  placeholder="Type any question about the RFP and press Enter…")
    submitted = st.form_submit_button("Ask", type="primary")

st.caption("Try an example:")
for col, text in zip(st.columns(len(EXAMPLES)), EXAMPLES):
    col.button(text, key=f"ex_{text}", on_click=use_example, args=(text,), use_container_width=True)

if submitted:
    question = " ".join(st.session_state.get("question", "").split())
    if len(question) < MIN_QUESTION_CHARS:
        st.warning("Please type a question (at least a few words).")
        st.session_state.pop("last", None)
    else:
        try:
            retriever, client = get_retriever(), make_client(provider, model)
            with st.spinner("Retrieving, generating, verifying…"):
                st.session_state["last"] = answer_question(
                    question, retriever.search, client, EvidenceGate(min_sem, min_cov), use_judge=use_judge)
        except (FileNotFoundError, LLMError) as e:
            st.session_state.pop("last", None)
            st.error(str(e))

r = st.session_state.get("last")
if r is not None:
    st.divider()
    st.markdown(f"**Question:** {r.question}")
    left, right = st.columns([3, 2])
    cited = {i for c in r.claims for i in c.citations}
    with left:
        if r.outcome in ("answered", "partial"):
            (st.success if r.outcome == "answered" else st.warning)(
                "Answer found in the RFP." if r.outcome == "answered"
                else "Partial answer: some statements were removed because they could not be verified.")
            for c in r.claims:
                st.markdown(f"- {c.text}  \n  " + " ".join(f"`{i}`" for i in c.citations))
        elif r.outcome == "out_of_scope":
            st.warning("**This question appears to be outside the scope of this RFP.** "
                       "I can only answer questions about the Central Bank of India UPI tender "
                       "(for example eligibility, scope of work, timelines or contract terms). "
                       "Try rephrasing it in terms of the document.")
        elif r.outcome == "not_in_document":
            st.info("**The RFP doesn't appear to state this.** Related sections exist, but none answers "
                    "the question, so I won't guess.")
            if r.gaps:
                st.caption(f"What's missing: {r.gaps}")
        elif r.outcome == "unverified":
            st.warning("**I found related passages but couldn't produce an answer that passed the citation "
                       "checks.** Try a more specific question, or check the source passages on the right.")
        else:
            hint = ("Check that Ollama is running and the model is pulled." if r.model.startswith("ollama")
                    else "Check your API key, model name and network; `python scripts/check_llm.py` can help.")
            st.error(f"**Something went wrong generating the answer.** {r.reason}  \n{hint}")
        if r.rejected:
            with st.expander(f"{len(r.rejected)} statement(s) removed by verification"):
                for x in r.rejected:
                    st.write(f"“{x['text']}” — {x['reason']}")
        with st.expander("Why this result? (gate signals, model, timings)"):
            st.json({"outcome": r.outcome, "reason": r.reason, "gate": r.gate,
                     "model": r.model, "timings_s": r.timings_s})
    with right:
        if r.outcome == "out_of_scope":
            st.subheader("Closest passages (not used)")
        else:
            st.subheader("Source passages")
        for e in r.evidence:
            with st.expander(f"p.{e['page_number']} · {e['chunk_id']}" + (" ✔ cited" if e["chunk_id"] in cited else ""),
                             expanded=e["chunk_id"] in cited):
                st.write(e["text"])
