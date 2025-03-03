from googletrans import Translator
from multilingual_pdf2text.pdf2text import PDF2Text
from multilingual_pdf2text.models.document_model.document import Document
import io, os

LOGGING_ENABLED = False

if LOGGING_ENABLED:
    import logging

    logging.basicConfig(level=logging.INFO)


class PDFTranslator:
    def __init__(
        self,
        pdf_file_path: str,
        pdf_language="hi",
        *args,
        **kwargs,
    ):
        self.pdf_file_path = pdf_file_path
        self.pdf_file_obj = io.StringIO()
        self.language = pdf_language

        self.tt_text_chunks = []

    def get_pdf_file_object(self):
        return self.pdf_file_obj

    def extract_text_from_pdf(self):
        print("Extractig text from pdf. Plese wait...")
        language = self.language
        if language == "hi":
            language = "hin"
        elif language == "en":
            language = "eng"

        pdf_document = Document(
            document_path=self.pdf_file_path,
            language=language,
        )
        pdf2text = PDF2Text(document=pdf_document)
        contents = pdf2text.extract()
        if contents:
            for content in contents:
                text = content.get("text")
                text = text.strip()
                self.pdf_file_obj.write(text)

        print("Extraction of text completed!")

    def translate_text(self, text):
        translator = Translator()
        tt_text = translator.translate(text, src=self.language, dest="en").text
        return tt_text

    def split_text(self, text, max_chars=5000):
        """Splits text into chunks of max_chars without breaking words."""
        chunks = []
        while len(text) > max_chars:
            split_index = text.rfind(" ", 0, max_chars)  # Find last space before limit
            if split_index == -1:  # If no space found, force split
                split_index = max_chars
            chunks.append(text[:split_index])
            text = text[split_index:].strip()
        chunks.append(text)
        return chunks

    def translate(self):
        text = self.pdf_file_obj.read()
        if not text:
            self.extract_text_from_pdf()

        text_chunks = self.split_text(self.pdf_file_obj.read())

        for chunk in text_chunks:
            translated_chunk = self.translate_text(chunk)
            self.tt_text_chunks.append(translated_chunk)

    def get_translated_text(self):
        self.translate()

        if self.tt_text_chunks:
            return "\n".join(self.tt_text_chunks)
        return ""


if __name__ == "__main__":
    pdf_file_path = "./hindi_document.pdf"
    pt = PDFTranslator(pdf_file_path=pdf_file_path)
    # print(pt.get_pdf_file_object())
    # pt.extract_text_from_pdf()

    tt_text = pt.get_translated_text()
