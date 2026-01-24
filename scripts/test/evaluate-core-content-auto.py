import json
import sys


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("usage: python scripts/test/evaluate-core-content-auto.py <jsonl_path>")
    
    total = 0
    classified = 0
    correct = 0
    unclassified = 0
    
    with open(sys.argv[1], "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            total += 1
            expected = data.get("expected_sub_topic_id")
            predicted = data.get("predicted_sub_topic_id")
            confidence = data.get("confidence")
            min_confidence = data.get("min_confidence", 0.2)
            
            if confidence is None or confidence < min_confidence:
                unclassified += 1
                continue
            classified += 1
            if expected == predicted:
                correct += 1
    
    accuracy = correct / classified if classified else 0.0
    unclassified_rate = unclassified / total if total else 0.0
    
    print(f"total={total}")
    print(f"classified={classified}")
    print(f"accuracy={accuracy:.4f}")
    print(f"unclassified_rate={unclassified_rate:.4f}")


if __name__ == "__main__":
    main()
