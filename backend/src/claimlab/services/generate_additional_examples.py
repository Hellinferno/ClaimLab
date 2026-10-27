"""Generates held-out and unsupported PDF examples for boundary testing."""
from pathlib import Path
from claimlab.services.generate_sample_pdf import create_minimal_pdf


def generate_all_examples():
    # 1. Unsupported Sample (Photosynthesis Botany Note)
    unsupported_pages = [
        (
            "Photosynthesis and Cellular Respiration in C3 Plants",
            "Chloroplasts absorb photons primarily in the blue and red wavelengths of light.\n\n"
            "The Calvin-Benson cycle fixes carbon dioxide into glyceraldehyde 3-phosphate.\n\n"
            "RuBisCO catalyzes the initial carboxylase reaction during the light-independent stage.\n\n"
            "This document discusses plant physiology and photosynthetic electron transport chains exclusively."
        )
    ]
    p1 = Path("examples/unsupported_sample.pdf").resolve()
    create_minimal_pdf(unsupported_pages, str(p1))
    print(f"Generated {p1}")

    # 2. Held-Out Attention Note (Separately worded transfer note)
    heldout_pages = [
        (
            "Held-Out Technical Note: Scaled Matrix Products",
            "When matching continuous queries against a memory bank of keys, the inner product "
            "magnitude scales proportionally to the dimensionality of the vector space.\n\n"
            "To preserve gradient dynamics across deep layers, scores are divided by the square root "
            "of the projection dimension before softmax normalization.\n\n"
            "In autoregressive generation, future token positions must be strictly masked to prevent "
            "information leakage across time steps."
        )
    ]
    p2 = Path("examples/heldout_attention_note.pdf").resolve()
    create_minimal_pdf(heldout_pages, str(p2))
    print(f"Generated {p2}")


if __name__ == "__main__":
    generate_all_examples()
