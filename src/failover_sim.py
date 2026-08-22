#!/usr/bin/env python3
"""Deterministic multi-region failover state-machine simulator."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass(frozen=True)
class HealthSample:
    primary: bool
    secondary: bool


@dataclass(frozen=True)
class Transition:
    step: int
    event: str
    source: str
    destination: str
    reason: str


class FailoverController:
    def __init__(self, fail_threshold: int = 3, recover_threshold: int = 3) -> None:
        if fail_threshold < 1 or recover_threshold < 1:
            raise ValueError("thresholds must be >= 1")
        self.fail_threshold = fail_threshold
        self.recover_threshold = recover_threshold
        self.active = "primary"
        self.primary_failures = 0
        self.primary_recoveries = 0

    def step(self, number: int, sample: HealthSample) -> Transition | None:
        if sample.primary:
            self.primary_failures = 0
            self.primary_recoveries += 1
        else:
            self.primary_failures += 1
            self.primary_recoveries = 0

        if self.active == "primary" and self.primary_failures >= self.fail_threshold:
            if sample.secondary:
                previous = self.active
                self.active = "secondary"
                return Transition(
                    number,
                    "failover",
                    previous,
                    self.active,
                    f"primary unhealthy for {self.primary_failures} consecutive checks",
                )
            return None

        if self.active == "secondary" and sample.primary and self.primary_recoveries >= self.recover_threshold:
            previous = self.active
            self.active = "primary"
            return Transition(
                number,
                "failback",
                previous,
                self.active,
                f"primary healthy for {self.primary_recoveries} consecutive checks",
            )
        return None


def demo_samples() -> list[HealthSample]:
    return [
        HealthSample(True, True),
        HealthSample(True, True),
        HealthSample(False, True),
        HealthSample(False, True),
        HealthSample(False, True),
        HealthSample(False, True),
        HealthSample(True, True),
        HealthSample(True, True),
        HealthSample(True, True),
        HealthSample(True, True),
    ]


def simulate(samples: list[HealthSample], fail_threshold: int = 3, recover_threshold: int = 3) -> dict:
    controller = FailoverController(fail_threshold, recover_threshold)
    timeline = []
    for index, sample in enumerate(samples, start=1):
        before = controller.active
        transition = controller.step(index, sample)
        timeline.append({
            "step": index,
            "primary_healthy": sample.primary,
            "secondary_healthy": sample.secondary,
            "active_before": before,
            "active_after": controller.active,
            "transition": asdict(transition) if transition else None,
        })
    transitions = [row["transition"] for row in timeline if row["transition"]]
    return {
        "fail_threshold": fail_threshold,
        "recover_threshold": recover_threshold,
        "final_active_region": controller.active,
        "transitions": transitions,
        "timeline": timeline,
    }


def load_samples(path: Path) -> list[HealthSample]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [HealthSample(bool(item["primary"]), bool(item["secondary"])) for item in raw]


def main() -> int:
    parser = argparse.ArgumentParser(description="Simulate primary/secondary regional failover")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path)
    source.add_argument("--demo", action="store_true")
    parser.add_argument("--fail-threshold", type=int, default=3)
    parser.add_argument("--recover-threshold", type=int, default=3)
    parser.add_argument("--output", type=Path, default=Path("output/timeline.json"))
    args = parser.parse_args()

    samples = demo_samples() if args.demo else load_samples(args.input)
    report = simulate(samples, args.fail_threshold, args.recover_threshold)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"samples={len(samples)} transitions={len(report['transitions'])} final={report['final_active_region']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
