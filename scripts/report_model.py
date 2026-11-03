from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Dict, List, Literal, Optional, Union
from unicodedata import normalize

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator


Platform = Literal["xiaohongshu", "douyin"]
Priority = Literal["high", "medium", "low"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Diagnosis(StrictModel):
    dimension: Literal["定位", "内容", "表达", "转化"]
    conclusion: str = Field(max_length=100)
    evidence: str = Field(max_length=100)
    evidence_type: Literal["fact", "inference", "unknown"]


class Problem(StrictModel):
    title: str = Field(max_length=40)
    evidence: str = Field(max_length=80)
    impact: str = Field(max_length=80)
    action: str = Field(max_length=80)
    priority: Priority


class Pillar(StrictModel):
    name: str = Field(max_length=24)
    ratio: int = Field(ge=0, le=100)
    columns: List[str] = Field(min_length=1, max_length=4)
    purpose: str = Field(default="", max_length=60)
    format: str = Field(default="", max_length=40)


class Benchmark(StrictModel):
    name: str = Field(max_length=40)
    platform: Platform
    account_kind: Literal["brand", "creator", "unknown"] = "unknown"
    brand_identity_evidence: str = Field(default="", max_length=180)
    benchmark_type: Literal["same_industry", "same_stage", "format"]
    reason: str = Field(max_length=80)
    learn: str = Field(max_length=80)
    avoid: str = Field(max_length=80)
    verified: bool
    user_confirmed: bool = False
    recent_performance: str = Field(default="", max_length=240)
    content_analysis: str = Field(default="", max_length=240)
    screenshot: Optional[str] = None
    source_note: str = Field(default="", max_length=120)


class Topic(StrictModel):
    title: str = Field(max_length=40)
    direction: str = Field(max_length=20)
    format: str = Field(max_length=12)
    priority: Priority


class IPProfile(StrictModel):
    identity: str = Field(min_length=1, max_length=120)
    audience: str = Field(min_length=1, max_length=120)
    value: str = Field(min_length=1, max_length=120)
    expression: str = Field(min_length=1, max_length=120)

    @field_validator("identity", "audience", "value", "expression")
    @classmethod
    def require_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("IP profile answers must not be blank")
        return value.strip()


class ProjectReport(StrictModel):
    sample_mode: bool = False
    account_subject: Literal["person", "brand"]
    client_company_name: str = Field(max_length=40)
    platform: Platform
    generated_date: str
    benchmark_review_complete: bool = False
    benchmarks: List[Benchmark] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_benchmarks(self) -> "ProjectReport":
        if any(item.platform != self.platform for item in self.benchmarks):
            raise ValueError("benchmark platform must match report platform")
        if not self.sample_mode and any(not item.verified for item in self.benchmarks):
            raise ValueError("benchmark must be verified unless sample_mode is true")
        return self

    def require_benchmark_review(self) -> None:
        """Older inputs may be read before the user confirms the final list."""
        if self.sample_mode:
            return
        if not self.benchmark_review_complete or not self.benchmarks:
            raise ValueError("Final report requires benchmark_review_complete=true and a confirmed list for this case")
        for item in self.benchmarks:
            if not item.user_confirmed or not item.verified:
                raise ValueError(f"Final benchmark must be user_confirmed and verified: {item.name}")
            if self.account_subject == "brand" and (
                item.account_kind != "brand" or not item.brand_identity_evidence.strip()
            ):
                raise ValueError(f"对标账号须为可核实的品牌自营账号，请补充品牌归属依据或更换候选：{item.name}")
            if not item.recent_performance.strip() or not item.content_analysis.strip():
                raise ValueError(f"Include recent_performance and content_analysis for final benchmark: {item.name}")


class ReportData(ProjectReport):
    seeding_mode: Literal[False] = False
    account_name: str = Field(max_length=40)
    ip_profile: Optional[IPProfile] = None
    account_url: str
    data_date: str
    stage: str = Field(max_length=30)
    account_bio: str = Field(default="暂未获取", max_length=500)
    profile_screenshot: Optional[str] = None
    profile_screenshot_note: str = Field(default="", max_length=120)
    current_content_types: List[str] = Field(default_factory=list, max_length=6)
    goal: str = Field(default="关注", min_length=1, max_length=12)
    summary: str = Field(max_length=100)
    opportunity: str = Field(max_length=100)
    metrics: Dict[str, Optional[str]]
    diagnoses: List[Diagnosis]
    problems: List[Problem] = Field(min_length=3, max_length=5)
    positioning: str = Field(max_length=180)
    target_audience: str = Field(max_length=100)
    follow_reason: str = Field(max_length=100)
    persona: str = Field(default="", max_length=80)
    persona_suggestions: List[str] = Field(default_factory=list, max_length=5)
    persona_purpose: str = Field(default="", max_length=120)
    slogan: str = Field(default="", max_length=40)
    content_style: str = Field(default="", max_length=80)
    optimization_logic: List[str] = Field(default_factory=list, max_length=3)
    conversion_path: List[str] = Field(default_factory=list, max_length=5)
    production_loop: List[str] = Field(default_factory=list, max_length=6)
    closing_section_title: str = Field(default="落地路径", min_length=1, max_length=20)
    pillars: List[Pillar] = Field(min_length=3, max_length=5)
    benchmarks: List[Benchmark] = Field(min_length=1)
    topic_directions: List[str] = Field(min_length=3, max_length=5)
    trend_note: str = Field(max_length=140)
    topics: List[Topic] = Field(min_length=15, max_length=30)
    screenshots: List[str] = Field(max_length=5)

    @field_validator("metrics", mode="after")
    @classmethod
    def normalize_metrics(cls, value: Dict[str, Optional[str]]) -> Dict[str, str]:
        return {key: metric if metric not in (None, "") else "暂未获取" for key, metric in value.items()}

    @field_validator("topic_directions", mode="after")
    @classmethod
    def validate_topic_groups(cls, value: List[str]) -> List[str]:
        directions = [item.strip() for item in value]
        if any(not item or len(item) > 20 for item in directions):
            raise ValueError("topic directions must contain 1-20 characters")
        if len(set(directions)) != len(directions):
            raise ValueError("topic directions must be unique")
        return directions

    @model_validator(mode="after")
    def validate_report_invariants(self) -> "ReportData":
        if self.account_subject == "person" and self.ip_profile is None:
            raise ValueError("Personal accounts require all four ip_profile answers")
        required_metrics = ["粉丝量", "获赞与收藏", "更新频率", "近期平均互动", "最高互动内容"]
        unknown_metrics = set(self.metrics) - set(required_metrics) - {"数据截取日期"}
        if unknown_metrics:
            raise ValueError(f"unsupported metrics: {sorted(unknown_metrics)}")
        self.metrics = {key: self.metrics.get(key) or "暂未获取" for key in required_metrics}
        self.metrics["数据截取日期"] = self.data_date
        if len({item.dimension for item in self.diagnoses}) != 4 or len(self.diagnoses) != 4:
            raise ValueError("diagnoses must contain the four unique dimensions")
        if sum(item.ratio for item in self.pillars) != 100:
            raise ValueError("pillar ratios must total 100")
        if any(item.direction not in self.topic_directions for item in self.topics):
            raise ValueError("topic direction must match a declared topic_directions entry")
        for key in ("optimization_logic", "conversion_path", "production_loop"):
            if any(not item.strip() or len(item) > 36 for item in getattr(self, key)):
                raise ValueError(f"{key}: each step must contain 1-36 characters")
        url = self.account_url.lower()
        xhs_hosts = ("xiaohongshu.com", "xhslink.com")
        douyin_hosts = ("douyin.com", "iesdouyin.com")
        if self.platform == "xiaohongshu" and any(host in url for host in douyin_hosts):
            raise ValueError("account URL belongs to Douyin, not Xiaohongshu")
        if self.platform == "douyin" and any(host in url for host in xhs_hosts):
            raise ValueError("account URL belongs to Xiaohongshu, not Douyin")
        return self

NonblankText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
PositiveCount = Annotated[int, Field(strict=True, ge=1)]


class SeedDirection(StrictModel):
    name: NonblankText = Field(max_length=80)
    audience_or_scene: NonblankText = Field(max_length=160)
    angle: NonblankText = Field(max_length=240)
    titles: List[NonblankText] = Field(min_length=1)
    allocated_posts: Optional[int] = Field(default=None, ge=0, strict=True)


class SeedExample(StrictModel):
    screenshot: NonblankText
    takeaway: NonblankText = Field(max_length=240)
    source_platform: Optional[Platform] = None


class DerivedTopic(StrictModel):
    title: NonblankText = Field(max_length=120)
    example_numbers: List[PositiveCount] = Field(min_length=1)
    angle: NonblankText = Field(max_length=240)


def _require_distinct(values: List[str], label: str) -> None:
    keys = ["".join(normalize("NFKC", value).split()).casefold() for value in values]
    if len(set(keys)) != len(keys):
        raise ValueError(f"{label} must be distinct")


class SeedReportData(ProjectReport):
    seeding_mode: Literal[True]
    account_subject: Literal["brand"] = "brand"
    seeding_review_complete: bool = False
    goal: NonblankText = Field(default="种草", max_length=120)
    target_audience: str = Field(default="", max_length=240)
    target_volume: Optional[PositiveCount] = None
    brand_support: List[Annotated[NonblankText, Field(max_length=120)]] = Field(default_factory=list, max_length=3)
    seeding_directions: List[SeedDirection] = Field(default_factory=list)
    seeding_examples: List[SeedExample] = Field(default_factory=list)
    derived_topics: List[DerivedTopic] = Field(default_factory=list)

    def require_seeding_review(self) -> None:
        """Allow partial drafts, and check the complete plan before delivery."""
        if not self.seeding_review_complete and not self.sample_mode:
            raise ValueError("Final seeding report requires seeding_review_complete=true for this case")
        if len(self.seeding_directions) < 15:
            raise ValueError("Final seeding report requires at least 15 distinct directions")
        _require_distinct([item.name for item in self.seeding_directions], "Direction names")
        if not self.seeding_examples:
            raise ValueError("Final seeding report requires original post screenshots and takeaways")
        for item in self.seeding_examples:
            if not Path(item.screenshot).is_file():
                raise ValueError(f"Original post screenshot file was not found: {item.screenshot}")
        if not 3 <= len(self.derived_topics) <= 5:
            raise ValueError("Final seeding report requires 3–5 derived topics in total")
        for item in self.derived_topics:
            if max(item.example_numbers) > len(self.seeding_examples):
                raise ValueError(f"Derived topic references a missing example: {item.title}")
            if len(set(item.example_numbers)) != len(item.example_numbers):
                raise ValueError(f"Derived topic repeats an example number: {item.title}")
        titles = [title for item in self.seeding_directions for title in item.titles]
        _require_distinct(titles + [item.title for item in self.derived_topics], "Suggested titles")
        allocations = [item.allocated_posts for item in self.seeding_directions if item.allocated_posts is not None]
        if allocations:
            if self.target_volume is None or len(allocations) != len(self.seeding_directions):
                raise ValueError("Set target_volume and all direction allocations when providing a distribution")
            if sum(allocations) != self.target_volume:
                raise ValueError("Direction allocations must add up to target_volume")


Report = Union[ReportData, SeedReportData]


def validate_report(data: dict) -> Report:
    if data.get("seeding_mode") is True:
        return SeedReportData.model_validate(data)
    return ReportData.model_validate(data)


def load_report(path: Path) -> Report:
    return validate_report(json.loads(Path(path).read_text(encoding="utf-8")))

