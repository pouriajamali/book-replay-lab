"""Run the existing six-row Python recovery fixture without a compiler or benchmark."""
import json
from pathlib import Path
from book_replay import Book

def main():
    fixtures = json.loads((Path(__file__).resolve().parent / "fixtures.json").read_text(encoding="utf-8"))
    fixture = next(item for item in fixtures if item["name"] == "gap then snapshot recovery")
    book = Book()
    actual = [book.process(record) for record in fixture["input"]]
    if actual != fixture["expected"]:
        raise RuntimeError("Recovery fixture differs from fixed expected states")
    print("Synthetic Python replay: reason|ready|accepted_sequence|bid|qty|ask|qty")
    for record, state in zip(fixture["input"], actual):
        print(record + " -> " + state)
    print("PASS: gap retains prices/sequence but blocks updates; explicit non-regressing snapshot restores readiness.")
    print("Python demonstration only. Run verify.py for both language implementations; no live feed or performance evidence.")

if __name__ == "__main__":
    main()
