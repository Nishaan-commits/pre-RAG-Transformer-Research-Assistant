""" 

Responsibility: Turn retrieved chunks + a question into a structured prompt.

"""

def build_prompt(question:str, chunks: list[str]) -> str:

    formatted_chunks = ""
    for i, chunk in enumerate(chunks, 1):
        formatted_chunks += f"[Chunk {i}]\n{chunk.strip()}\n\n---\n\n"

    prompt = f"""You are a research assistant specialized in reading and explaining academic papers.
 
            Your job is to answer questions based ONLY on the context provided below.
            Do not use any outside knowledge or make assumptions beyond what is written.
            When answering, reference the relevant chunk numbers (e.g. "According to Chunk 2...").
            If the answer can be reasonably inferred by combining information from the context, provide the inference and clearly label it as an inference.
 
            If the answer cannot be found in the context or inferred, respond with exactly:
            "I could not find the answer in the provided context."
 
            Context:
            {formatted_chunks}
            Question: {question}
 
            Answer:"""
    return prompt
