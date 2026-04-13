import streamlit as st
import os
import pypdf
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

w = WorkspaceClient()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "active_pdf_text" not in st.session_state:
    st.session_state.active_pdf_text = ""
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "show_pdf_prompt" not in st.session_state:
    st.session_state.show_pdf_prompt = False


def build_chat_history():
    history = []
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            role = ChatMessageRole.USER
        else:
            role = ChatMessageRole.ASSISTANT

        history.append(
            ChatMessage(
                role=role,
                content=msg["content"]
            )
        )
    return history


st.title("AI Compass")


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


st.markdown("""
<style>
    [data-testid="stFileUploader"] small {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    uploaded_file = st.file_uploader("📎 Attach PDF", type="pdf")
    if uploaded_file:
        if st.session_state.uploaded_file != uploaded_file:
            st.session_state.show_pdf_prompt = True
        st.session_state.uploaded_file = uploaded_file
        st.success(f"Attached: {uploaded_file.name}")


if st.session_state.show_pdf_prompt and st.session_state.uploaded_file:
    st.info(f"📎 PDF {st.session_state.uploaded_file.name} attached: - Ask a question about it!")

prompt = st.chat_input("Ask something...")

if prompt:
    st.session_state.show_pdf_prompt = False
    display_text = prompt

    if st.session_state.uploaded_file:
        with st.spinner("Processing document..."):
            pdf = pypdf.PdfReader(st.session_state.uploaded_file)
            pdf_text = ""
            for page in pdf.pages:
                pdf_text += page.extract_text() + "\n"

            st.session_state.active_pdf_text = pdf_text
            display_text = f"**Attached: {st.session_state.uploaded_file.name}**\n\n{prompt}"

    st.session_state.messages.append({
        "role": "user",
        "content": display_text
    })

    with st.chat_message("user"):
        st.markdown(display_text)

    with st.chat_message("assistant"):
        agent_name = os.getenv("SERVING_ENDPOINT_NAME", "compass_v_1")
        with st.spinner("Thinking..."):
            try:
                if st.session_state.active_pdf_text:
                    context_payload = (
                        f"DOCUMENT ATTACHED:\n"
                        f"{st.session_state.active_pdf_text}\n\n"
                        f"User Question: {prompt}"
                    )
                else:
                    context_payload = prompt

                chat_history = build_chat_history()

                chat_history.append(
                    ChatMessage(
                        role=ChatMessageRole.USER,
                        content=context_payload
                    )
                )

                db_resp = w.serving_endpoints.query(
                    name=agent_name,
                    messages=chat_history
                )

                response_text = db_resp.choices[0].message.content
                st.markdown(response_text)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_text
                })

            except Exception as e:
                st.error(f"Error: {e}")