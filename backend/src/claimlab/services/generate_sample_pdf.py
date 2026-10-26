"""Generates the reference lesson PDF matching docs/27_REFERENCE_LESSONS.md."""
from pathlib import Path


def create_minimal_pdf(pages_text: list[tuple[str, str]], output_path: str):
    """Creates a standard multi-page PDF with native Helvetica text."""
    page_obj_ids = []
    content_obj_ids = []
    
    for i in range(len(pages_text)):
        page_obj_ids.append(5 + 2 * i)
        content_obj_ids.append(6 + 2 * i)
        
    num_objects = 4 + 2 * len(pages_text)
    
    # Object definitions
    obj_data = {}
    obj_data[1] = "<< /Type /Catalog /Pages 3 0 R >>"
    obj_data[2] = "<< /Type /Outlines /Count 0 >>"
    
    kids_str = " ".join(f"{pid} 0 R" for pid in page_obj_ids)
    obj_data[3] = f"<< /Type /Pages /Count {len(pages_text)} /Kids [ {kids_str} ] >>"
    obj_data[4] = "<< /Type /Font /Subtype /Type1 /Name /F1 /BaseFont /Helvetica >>"
    
    for i, (title, body) in enumerate(pages_text):
        p_id = page_obj_ids[i]
        c_id = content_obj_ids[i]
        
        # Build text stream
        stream_cmds = ["BT", "/F1 14 Tf", "50 750 Td"]
        stream_cmds.append(f"({title}) Tj")
        stream_cmds.append("/F1 10 Tf")
        stream_cmds.append("0 -24 Td")
        
        for line in body.split("\n"):
            line = line.strip()
            if not line:
                stream_cmds.append("0 -14 Td")
                continue
            # Escape parentheses in PDF string
            safe_line = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            # Wrap long line
            words = safe_line.split(" ")
            current_line = []
            for w in words:
                if len(" ".join(current_line + [w])) > 75:
                    stream_cmds.append(f"({' '.join(current_line)}) Tj")
                    stream_cmds.append("0 -14 Td")
                    current_line = [w]
                else:
                    current_line.append(w)
            if current_line:
                stream_cmds.append(f"({' '.join(current_line)}) Tj")
                stream_cmds.append("0 -14 Td")
                
        stream_cmds.append("ET")
        stream_content = "\n".join(stream_cmds)
        
        obj_data[c_id] = f"<< /Length {len(stream_content)} >>\nstream\n{stream_content}\nendstream"
        obj_data[p_id] = f"<< /Type /Page /Parent 3 0 R /MediaBox [ 0 0 612 792 ] /Contents {c_id} 0 R /Resources << /Font << /F1 4 0 R >> >> >>"

    # Assemble PDF with cross-reference table
    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = {}
    
    for obj_num in range(1, num_objects + 1):
        offsets[obj_num] = len(output)
        content = obj_data[obj_num]
        output.extend(f"{obj_num} 0 obj\n{content}\nendobj\n".encode("latin1"))
        
    xref_offset = len(output)
    output.extend(f"xref\n0 {num_objects + 1}\n".encode("latin1"))
    output.extend(b"0000000000 65535 f \n")
    for obj_num in range(1, num_objects + 1):
        output.extend(f"{offsets[obj_num]:010d} 00000 n \n".encode("latin1"))
        
    output.extend(f"trailer\n<< /Size {num_objects + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("latin1"))
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(output)


if __name__ == "__main__":
    pages = [
        (
            "ClaimLab Attention Lab - Section A: From scores to weights",
            "Softmax turns a finite vector of scores into nonnegative weights summing to one.\n\n"
            "Increasing all scores by the same amount preserves the weights.\n\n"
            "Multiplying unequal scores changes their relative influence.\n\n"
            "Equal scores receive equal weights.\n\n"
            "A numerical investigation can compare score vectors before and after multiplication. "
            "Its inputs and results should be visible so the learner can explain the relationship rather than memorize a picture."
        ),
        (
            "ClaimLab Attention Lab - Section B: Attention ingredients",
            "In a small attention example, a query is compared with keys to produce scores.\n\n"
            "A normalization step produces weights. Those weights combine values to produce an output.\n\n"
            "The objects participating in scoring and those contributing output information have different roles.\n\n"
            "A synthetic dot-product experiment can investigate the effect of score scaling under stated assumptions. "
            "Synthetic vectors do not represent a trained model's learned behavior or reproduce a translation benchmark."
        ),
        (
            "ClaimLab Attention Lab - Section C: Which positions may contribute?",
            "In a causal attention illustration, a position can use its current and earlier positions while future positions are excluded.\n\n"
            "A mask changes which entries contribute before row-wise normalization.\n\n"
            "Each row in this example retains at least one allowed entry.\n\n"
            "This explains one operation. A full language-model training procedure includes additional design choices and should not be inferred from the illustration alone."
        )
    ]
    out_file = Path("examples/claimlab_attention_lab.pdf").resolve()
    create_minimal_pdf(pages, str(out_file))
    print(f"Generated reference PDF at {out_file} ({out_file.stat().st_size} bytes)")
