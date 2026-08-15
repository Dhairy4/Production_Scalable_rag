from unstructured.partition.auto import partition
import logfire


def parse_office(file_path: str):
    """
    Parses Office Documents (.docx,.pptx) using the unstructured library
    unlike pdf, these formats are structured and lightweight they are procesesed locally
    """
    with logfire.span("office parsing", filename= file_path):
        try:
            # unstructured automatically detects if it is docx or pptx 

            elements = partition(file_path)
            full_text = "\n".join([str(el) for el in elements])

            if not full_text.strip():
                logfire.warning(f"Returned empty text for file {file_path}.")
            else:
                logfire.info(f"successfully parsed {len(full_text)} characters")

            return full_text

        except Exception as e:
            logfire.error(f"Error parsing Office file{e}")
            raise e