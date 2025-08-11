from rich.console import Console
from rich.text import Text
from rich.columns import Columns
from rich.panel import Panel
import difflib


def rich_diff_display(reference, comment, similarity_score):
    console = Console()

    # Create similarity indicator
    similarity_color = "gray"
    similarity_text = Text("Similarity: not provided")
    if similarity_score:
        if similarity_score >= 80:
            similarity_color = "green"
        elif similarity_score >= 60:
            similarity_color = "yellow"
        else:
            similarity_color = "red"
        similarity_text = Text(
            f"Similarity: {similarity_score}", style=f"bold {similarity_color}"
        )

    # Create diff
    matcher = difflib.SequenceMatcher(None, reference, comment)

    reference_display = Text()
    comment_display = Text()

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            reference_display.append(reference[i1:i2], style="dim")
            comment_display.append(comment[j1:j2], style="dim")
        elif tag == "delete":
            reference_display.append(reference[i1:i2], style="red strike")
        elif tag == "insert":
            comment_display.append(comment[j1:j2], style="orange1")
        elif tag == "replace":
            reference_display.append(reference[i1:i2], style="red strike")
            comment_display.append(comment[j1:j2], style="blue")

    # Create panels
    ref_panel = Panel(reference_display, title="Reference Comment", border_style="blue")
    comment_panel = Panel(
        comment_display, title="Submitted Comment", border_style="green"
    )

    # Display
    console.print(similarity_text)
    console.print(Columns([ref_panel, comment_panel]))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("reference", type=str)
    parser.add_argument("comment", type=str)
    parser.add_argument("similarity", type=float)

    args = parser.parse_args()

    rich_diff_display(
        reference=args.reference, comment=args.comment, similarity_score=args.similarity
    )
