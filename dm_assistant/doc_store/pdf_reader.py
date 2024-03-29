"""Docs parser.

Contains parsers pdf files using pypdf2.

"""
import logging
import struct
import zlib
from pathlib import Path
from typing import Any, Dict, List, Optional

from llama_index.readers.base import BaseReader
from llama_index.schema import Document


class PDF2Reader(BaseReader):
    """PDF2 parser."""

    def __init__(self, return_full_document: Optional[bool] = False) -> None:
        """
        Initialize PDF2Reader.
        """
        self.return_full_document = return_full_document

    def load_data(
        self, file: Path, extra_info: Optional[Dict] = None
    ) -> List[Document]:
        """Parse file."""
        try:
            import PyPDF2 as pypdf
        except ImportError:
            raise ImportError(
                "pypdf2 is required to read PDF files: `pip install pypdf2`"
            )
        with open(file, "rb") as fp:
            # Create a PDF object
            pdf = pypdf.PdfReader(fp)

            # Get the number of pages in the PDF document
            num_pages = len(pdf.pages)

            docs = []

            # This block returns a whole PDF as a single Document
            if self.return_full_document:
                text = ""
                metadata = {"file_name": fp.name}

                for page in range(num_pages):
                    # Extract the text from the page
                    page_text = pdf.pages[page].extract_text()
                    text += page_text

                docs.append(Document(text=text, metadata=metadata))

            # This block returns each page of a PDF as its own Document
            else:
                # Iterate over every page
                #logging.warn(pdf.pages[1].extract_text())
                for page in range(num_pages):
                    # Extract the text from the page
                    page_text = pdf.pages[page].extract_text()
                    #logging.warn(dir(pdf))
                    #page_label = pdf.page_labels[page]

                    metadata = {"page_label": page, "file_name": fp.name}
                    if extra_info is not None:
                        metadata.update(extra_info)

                    docs.append(Document(text=page_text, metadata=metadata))

            return docs