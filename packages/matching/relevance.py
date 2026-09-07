from dataclasses import dataclass

from packages.domain.job import Job


@dataclass(frozen=True)
class RelevanceResult:
    """Result of evaluating a job's relevance."""

    score: float
    is_relevant: bool
    reasons: list[str]


class JobRelevanceEngine:
    """Evaluate relevance for electronics, hardware, and embedded roles."""

    TITLE_PHRASES: dict[str, float] = {
        "embedded hardware design engineer": 45.0,
        "embedded hardware engineer": 45.0,
        "hardware design engineer": 45.0,
        "electronics hardware engineer": 45.0,
        "electronics design engineer": 42.0,
        "pcb design engineer": 42.0,
        "hardware validation engineer": 42.0,
        "hardware development engineer": 42.0,
        "embedded systems engineer": 42.0,
        "power electronics engineer": 42.0,
        "firmware engineer": 35.0,
        "fpga engineer": 35.0,
        "electrical engineer": 35.0,
        "robotics engineer": 30.0,
    }

    TITLE_KEYWORDS: dict[str, float] = {
        "hardware": 30.0,
        "embedded": 28.0,
        "electronics": 28.0,
        "pcb": 28.0,
        "circuit": 25.0,
        "firmware": 22.0,
        "microcontroller": 25.0,
        "fpga": 25.0,
        "robotics": 20.0,
        "electrical": 20.0,
    }

    TITLE_COMBINATIONS: tuple[tuple[tuple[str, ...], float], ...] = (
        (("pcb", "design", "engineer"), 42.0),
        (("electronics", "hardware", "engineer"), 45.0),
        (("hardware", "validation", "engineer"), 42.0),
        (("hardware", "development", "engineer"), 42.0),
        (("embedded", "hardware"), 45.0),
        (("embedded", "firmware", "engineer"), 35.0),
        (("firmware", "engineer"), 35.0),
    )

    DESCRIPTION_KEYWORDS: dict[str, float] = {
        "hardware": 10.0,
        "embedded": 10.0,
        "electronics": 10.0,
        "pcb": 12.0,
        "circuit design": 12.0,
        "schematic": 8.0,
        "microcontroller": 10.0,
        "firmware": 8.0,
        "fpga": 10.0,
        "robotics": 8.0,
        "iot": 8.0,
        "altium": 10.0,
        "kicad": 10.0,
        "ltspice": 8.0,
        "power electronics": 12.0,
        "rtl": 15.0,
        "asic": 15.0,
        "verilog": 12.0,
        "systemverilog": 12.0,
        "vhdl": 12.0,
        "vlsi": 15.0,
        "soc": 12.0,
        "tapeout": 15.0,
        "digital design": 12.0,
        "verification": 8.0,
        "testbench": 8.0,
        "analog design": 12.0,
        "opamp": 10.0,
        "pcb layout": 12.0,
    }

    NEGATIVE_KEYWORDS: dict[str, float] = {
        "account manager": -45.0,
        "account management": -45.0,
        "technical program manager": -45.0,
        "sales": -40.0,
        "business development": -40.0,
        "marketing": -40.0,
        "human resources": -40.0,
        "recruiter": -40.0,
        "recruitment": -35.0,
        "talent acquisition": -35.0,
        "customer support": -30.0,
        "customer service": -30.0,
        "finance": -30.0,
        "accountant": -40.0,
    }

    RELEVANCE_THRESHOLD = 30.0

    def evaluate(self, job: Job) -> RelevanceResult:
        """Evaluate a job and return an explainable relevance result."""

        title = job.title.lower()
        description = (job.description or "").lower()
        skills = " ".join(job.skills).lower()

        score = 0.0
        reasons: list[str] = []

        matched_title_phrase = self._match_title_phrase(title)

        if matched_title_phrase is not None:
            phrase, weight = matched_title_phrase
            score += weight
            reasons.append(f"title:{phrase}")
        else:
            matched_title_combination = self._match_title_combination(title)

            if matched_title_combination is not None:
                keywords, weight = matched_title_combination
                score += weight
                reasons.append(
                    f"title:{' '.join(keywords)}"
                )
            else:
                for keyword, weight in self.TITLE_KEYWORDS.items():
                    if keyword in title:
                        score += weight
                        reasons.append(f"title:{keyword}")

        for keyword, weight in self.DESCRIPTION_KEYWORDS.items():
            if keyword in description:
                score += weight
                reasons.append(f"description:{keyword}")

        for keyword, weight in self.DESCRIPTION_KEYWORDS.items():
            if keyword in skills:
                score += weight
                reasons.append(f"skill:{keyword}")

        if "pcb" in description and "pcb layout" in description:
            score += 15.0
            reasons.append("description:pcb+pcb layout")

        for keyword, penalty in self.NEGATIVE_KEYWORDS.items():
            if keyword in title:
                score += penalty
                reasons.append(f"title:-{keyword}")

        score = max(0.0, min(score, 100.0))

        return RelevanceResult(
            score=score,
            is_relevant=score >= self.RELEVANCE_THRESHOLD,
            reasons=reasons,
        )

    def _match_title_combination(
        self,
        title: str,
    ) -> tuple[tuple[str, ...], float] | None:
        """Return the strongest matching title keyword combination."""

        matches = [
            (keywords, weight)
            for keywords, weight in self.TITLE_COMBINATIONS
            if all(keyword in title for keyword in keywords)
        ]

        if not matches:
            return None

        return max(matches, key=lambda item: item[1])

    def _match_title_phrase(
        self,
        title: str,
    ) -> tuple[str, float] | None:
        """Return the most specific matching title phrase."""

        phrases = sorted(
            self.TITLE_PHRASES.items(),
            key=lambda item: len(item[0]),
            reverse=True,
        )

        for phrase, weight in phrases:
            if phrase in title:
                return phrase, weight

        return None
