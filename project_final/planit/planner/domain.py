from abc import ABC, abstractmethod
from decimal import Decimal, InvalidOperation


EXAM_WINDOW_DAYS = 14
URGENT_WINDOW_DAYS = 7
NORMAL_WINDOW_DAYS = 3


PRIORITY_WEIGHT = {
    "urgent": Decimal("3"),
    "normal": Decimal("2"),
    "later": Decimal("1"),
}


PRIORITY_RANK = {
    "urgent": 1,
    "normal": 2,
    "later": 3,
}


class PlannerItem(ABC):

    def __init__(
        self,
        id,
        title,
        area,
        kind,
        priority,
        due_date=None,
        completed=False,
    ):
        self.id = id
        self.title = title
        self.area = area
        self.kind = kind
        self.priority = priority
        self.due_date = due_date
        self.completed = completed

    @property
    @abstractmethod
    def type_multiplier(self):
        pass

    @abstractmethod
    def visible_in_exam_mode(self, today):
        pass

    def days_left(self, today):
        if self.due_date is None:
            return None

        return (self.due_date - today).days

    def days_overdue(self, today):
        if self.status(today) != "overdue":
            return 0

        return abs(self.days_left(today))

    def is_past_exam(self, today):
        return False

    def status(self, today):
        if self.completed:
            return "completed"

        if self.is_past_exam(today):
            return "past_exam"

        if self.due_date is None:
            return "no_date"

        days = self.days_left(today)

        if days < 0:
            return "overdue"

        if days == 0:
            return "today"

        return "upcoming"

    def attention_score(self, today):
        status = self.status(today)

        if status in ("completed", "past_exam"):
            return Decimal("0")

        base = (
            PRIORITY_WEIGHT[self.priority]
            * self.type_multiplier
        )

        days = self.days_left(today)

        if days is None or days < 0:
            return base

        return base / Decimal(days + 1)


class GeneralItem(PlannerItem):

    @property
    def type_multiplier(self):
        return Decimal("1.00")

    def visible_in_exam_mode(self, today):
        status = self.status(today)

        if status in ("completed", "past_exam"):
            return False

        if status == "overdue":
            return True

        days = self.days_left(today)

        if self.priority == "urgent":
            return (
                days is None
                or 0 <= days <= URGENT_WINDOW_DAYS
            )

        if self.priority == "normal":
            return (
                days is not None
                and 0 <= days <= NORMAL_WINDOW_DAYS
            )

        return False


class AssignmentItem(GeneralItem):
    pass


class StudyItem(PlannerItem):

    @property
    def type_multiplier(self):
        return Decimal("1.25")

    def visible_in_exam_mode(self, today):
        status = self.status(today)

        if status in ("completed", "past_exam"):
            return False

        if status == "overdue":
            return True

        days = self.days_left(today)

        if self.priority == "urgent":
            return (
                days is None
                or 0 <= days <= NORMAL_WINDOW_DAYS
            )

        if self.priority == "normal":
            return (
                days is not None
                and 0 <= days <= NORMAL_WINDOW_DAYS
            )

        return False


class ExamItem(PlannerItem):

    @property
    def type_multiplier(self):
        return Decimal("2.00")

    def is_past_exam(self, today):
        return (
            self.due_date is not None
            and self.due_date < today
        )

    def visible_in_exam_mode(self, today):
        if self.completed:
            return False

        days = self.days_left(today)

        return (
            days is not None
            and 0 <= days <= EXAM_WINDOW_DAYS
        )


class PersonalItem(PlannerItem):

    @property
    def type_multiplier(self):
        return Decimal("0.50")

    def visible_in_exam_mode(self, today):
        status = self.status(today)

        if status in ("completed", "past_exam"):
            return False

        if self.priority != "urgent":
            return False

        if status == "overdue":
            return True

        days = self.days_left(today)

        return (
            days is None
            or 0 <= days <= URGENT_WINDOW_DAYS
        )


def _to_decimal(value, field_name):
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(
            f"{field_name} must be a number."
        )


class GradeComponent:

    def __init__(
        self,
        name,
        weight,
        max_score,
        score=None,
    ):
        name = name.strip()

        if not name:
            raise ValueError(
                "Component name is required."
            )

        self.name = name

        self.weight = _to_decimal(
            weight,
            "Weight",
        )

        self.max_score = _to_decimal(
            max_score,
            "Maximum score",
        )

        if not Decimal("0") < self.weight <= Decimal("100"):
            raise ValueError(
                "Weight must be greater than 0 and at most 100."
            )

        if self.max_score <= 0:
            raise ValueError(
                "Maximum score must be greater than 0."
            )

        self._score = None
        self.score = score

    @property
    def score(self):
        return self._score

    @score.setter
    def score(self, value):
        if value is None:
            self._score = None
            return

        score = _to_decimal(
            value,
            "Score",
        )

        if score < 0:
            raise ValueError(
                "Score cannot be negative."
            )

        if score > self.max_score:
            raise ValueError(
                "Score cannot exceed maximum score."
            )

        self._score = score

    def earned_course_points(self):
        if self.score is None:
            return None

        return (
            self.weight
            * self.score
            / self.max_score
        )


class GradeBook:

    def __init__(self, components=()):
        self._components = []

        for component in components:
            self.add(component)

    @property
    def components(self):
        return tuple(self._components)

    @property
    def configured_weight(self):
        return sum(
            (
                component.weight
                for component in self._components
            ),
            Decimal("0"),
        )

    @property
    def graded_weight(self):
        return sum(
            (
                component.weight
                for component in self._components
                if component.score is not None
            ),
            Decimal("0"),
        )

    @property
    def ungraded_weight(self):
        return sum(
            (
                component.weight
                for component in self._components
                if component.score is None
            ),
            Decimal("0"),
        )

    @property
    def earned_course_points(self):
        return sum(
            (
                component.earned_course_points()
                for component in self._components
                if component.score is not None
            ),
            Decimal("0"),
        )

    @property
    def average_on_graded_work(self):
        if self.graded_weight == 0:
            return None

        return (
            self.earned_course_points
            / self.graded_weight
            * Decimal("100")
        )

    def add(self, component):
        if not isinstance(
            component,
            GradeComponent,
        ):
            raise TypeError(
                "GradeBook accepts GradeComponent objects only."
            )

        new_total = (
            self.configured_weight
            + component.weight
        )

        if new_total > Decimal("100"):
            raise ValueError(
                "Total assessment weight cannot exceed 100."
            )

        self._components.append(component)

    def required_average(self, target):
        target = _to_decimal(
            target,
            "Target",
        )

        if not Decimal("0") <= target <= Decimal("100"):
            raise ValueError(
                "Target must be between 0 and 100."
            )

        if self.configured_weight != Decimal("100"):
            return {
                "status": "incomplete_configuration",
                "required": None,
            }

        earned = self.earned_course_points

        if earned >= target:
            return {
                "status": "achieved",
                "required": Decimal("0"),
            }

        remaining = self.ungraded_weight

        if remaining == 0:
            return {
                "status": "impossible_no_remaining",
                "required": None,
            }

        required = (
            (target - earned)
            / remaining
            * Decimal("100")
        )

        status = (
            "possible"
            if required <= Decimal("100")
            else "impossible"
        )

        return {
            "status": status,
            "required": required,
        }