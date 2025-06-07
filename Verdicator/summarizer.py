from transformers import pipeline
def sum(verdict_txt):
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    return summarizer(verdict_txt, max_length=80, min_length=5, do_sample=False)[0]['summary_text']