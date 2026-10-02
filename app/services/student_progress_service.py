from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class MilestoneProgress:
    name: str
    target_hours: Decimal
    achieved: bool
    current: bool
    progress_percent: int


@dataclass(frozen=True)
class StudentProgress:
    current_hours: Decimal
    milestones: list[MilestoneProgress]
    next_milestone: MilestoneProgress | None
    hours_to_next: Decimal


class StudentProgressService:
    MILESTONE_TARGETS = (
        Decimal("8"),
        Decimal("16"),
        Decimal("24"),
        Decimal("32"),
    )

    def build_roadmap(self, current_hours: Decimal) -> StudentProgress:
        hours = max(Decimal("0"), current_hours)
        next_index = next(
            (
                index
                for index, target in enumerate(self.MILESTONE_TARGETS)
                if hours < target
            ),
            None,
        )
        milestones = []
        previous_target = Decimal("0")

        for index, target in enumerate(self.MILESTONE_TARGETS):
            achieved = hours >= target
            current = index == next_index
            if achieved:
                progress_percent = 100
            elif current:
                progress_percent = int(
                    ((hours - previous_target) / (target - previous_target)) * 100
                )
            else:
                progress_percent = 0

            milestones.append(
                MilestoneProgress(
                    name=f"Milestone {index + 1}",
                    target_hours=target,
                    achieved=achieved,
                    current=current,
                    progress_percent=progress_percent,
                )
            )
            previous_target = target

        next_milestone = milestones[next_index] if next_index is not None else None
        hours_to_next = (
            next_milestone.target_hours - hours
            if next_milestone is not None
            else Decimal("0")
        )
        return StudentProgress(
            current_hours=hours,
            milestones=milestones,
            next_milestone=next_milestone,
            hours_to_next=hours_to_next,
        )