"""Isolated PDF parser entrypoint reading PDF bytes from stdin and emitting JSON to stdout."""
import json
import sys
from claimlab.services.pdf_service import extract_pdf_content


def main():
    try:
        pdf_bytes = sys.stdin.buffer.read()
        if not pdf_bytes:
            sys.stderr.write("Error: Empty PDF stream\n")
            sys.exit(1)

        result = extract_pdf_content(pdf_bytes)
        output = {
            "page_count": result.page_count,
            "warnings": result.warnings,
            "pages": [
                {
                    "page_number": p[0],
                    "normalized_text": p[1],
                    "status": p[2].value,
                    "warnings": p[3],
                }
                for p in result.pages
            ],
        }
        sys.stdout.write(json.dumps(output))
        sys.stdout.flush()
        sys.exit(0)

    except Exception as e:
        sys.stderr.write(f"Parser error: {str(e)}\n")
        sys.exit(2)


if __name__ == "__main__":
    main()
