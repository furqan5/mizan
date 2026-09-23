"""Immutable multirate timing contracts; no optimizer or machine defaults.

[J] See docs/control_timeline_scope.md for preregistered acceptance cases.
Prediction cells are 900 s; a first-move proposal has at most a 300 s lease.
All physical limits and feedback-age policy are supplied explicitly. A
proposal always requires independent fresh activation admission; this module
does not evaluate thermal, chemical, permit, local-mode or interlock safety.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import fsum, isfinite
from numbers import Real
from types import MappingProxyType
from typing import ClassVar, Mapping


CHANNELS = (
    "C_target", "f_fan", "f_CW_pump", "f_TCS_pump", "T_CW_sp",
    "T_FWS_sp", "lift", "u_BD", "F_acid", "Q_store",
)
PHYSICAL_CHANNELS = frozenset(CHANNELS) - {"C_target", "lift"}
CHANNEL_UNITS = MappingProxyType(dict(zip(CHANNELS, (
    "1", "Hz", "Hz", "Hz", "degC", "degC", "K", "1", "mol/s", "kW",
))))


class TimelineError(ValueError):
    """Malformed, unavailable or inadmissible timing/command data."""


def _utc(value, name):
    if not isinstance(value, datetime):
        raise TimelineError(f"{name}: timezone-aware datetime required")
    try:
        if value.tzinfo is None or value.utcoffset() is None:
            raise TimelineError(f"{name}: timezone-aware datetime required")
        return value.astimezone(timezone.utc)
    except (ValueError, OverflowError, TypeError) as exc:
        raise TimelineError(f"{name}: invalid timezone-aware datetime") from exc


def _number(value, name):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TimelineError(f"{name}: finite numeric value required")
    try:
        value = float(value)
    except (ValueError, OverflowError) as exc:
        raise TimelineError(f"{name}: finite numeric value required") from exc
    if not isfinite(value):
        raise TimelineError(f"{name}: finite numeric value required")
    return value


def _sum_finite(values, name):
    try:
        value = fsum(values)
    except (OverflowError, ValueError) as exc:
        raise TimelineError(f"{name}: nonfinite sum") from exc
    if not isfinite(value):
        raise TimelineError(f"{name}: nonfinite sum")
    return value


def _sequence(value, name):
    if isinstance(value, (str, bytes, Mapping)):
        raise TimelineError(f"{name}: sequence required")
    try:
        return tuple(value)
    except TypeError as exc:
        raise TimelineError(f"{name}: sequence required") from exc


def _commands(value, name):
    if not isinstance(value, Mapping) or not value:
        raise TimelineError(f"{name}: nonempty physical-channel mapping required")
    if any(key not in PHYSICAL_CHANNELS for key in value):
        raise TimelineError(f"{name}: unknown or nonphysical command channel")
    return MappingProxyType({key: _number(val, f"{name}.{key}")
                             for key, val in value.items()})


@dataclass(frozen=True)
class ActivationHorizon:
    activation_at: datetime
    steps: ClassVar[int] = 96
    step_seconds: ClassVar[int] = 900
    channels: ClassVar[tuple[str, ...]] = CHANNELS

    def __post_init__(self):
        object.__setattr__(self, "activation_at", _utc(self.activation_at, "activation_at"))
        try:
            self.activation_at + timedelta(seconds=self.steps * self.step_seconds)
        except OverflowError as exc:
            raise TimelineError("horizon exceeds datetime range") from exc

    @property
    def boundaries(self):
        return tuple(self.activation_at + timedelta(seconds=k * self.step_seconds)
                     for k in range(self.steps + 1))

    @property
    def end_at(self):
        return self.boundaries[-1]


@dataclass(frozen=True)
class PredictionPlan:
    horizon: ActivationHorizon
    values: tuple[tuple[float, ...], ...]
    issued_at: datetime

    def __post_init__(self):
        if not isinstance(self.horizon, ActivationHorizon):
            raise TimelineError("horizon: ActivationHorizon required")
        issued = _utc(self.issued_at, "issued_at")
        if issued > self.horizon.activation_at:
            raise TimelineError("plan issued after activation")
        rows = _sequence(self.values, "plan")
        if len(rows) != self.horizon.steps:
            raise TimelineError("plan must contain 96 rows")
        frozen = []
        for k, row in enumerate(rows):
            row = _sequence(row, f"plan[{k}]")
            if len(row) != len(CHANNELS):
                raise TimelineError("each plan row must contain ten named channels")
            frozen.append(tuple(_number(x, f"plan[{k}].{name}")
                                for name, x in zip(CHANNELS, row)))
        object.__setattr__(self, "values", tuple(frozen))
        object.__setattr__(self, "issued_at", issued)


@dataclass(frozen=True)
class IssuedLoadInterval:
    start_at: datetime
    end_at: datetime
    load_kw: float
    issued_at: datetime
    available_at: datetime

    def __post_init__(self):
        for name in ("start_at", "end_at", "issued_at", "available_at"):
            object.__setattr__(self, name, _utc(getattr(self, name), name))
        if self.end_at <= self.start_at:
            raise TimelineError("load interval must have positive duration")
        if self.available_at < self.issued_at:
            raise TimelineError("load cannot be available before issuance")
        power = _number(self.load_kw, "load_kw")
        if power < 0:
            raise TimelineError("load_kw must be nonnegative")
        object.__setattr__(self, "load_kw", power)


@dataclass(frozen=True)
class ResampledLoad:
    horizon: ActivationHorizon
    as_of: datetime
    mean_kw: tuple[float, ...]
    energy_kwh: tuple[float, ...]
    source_min_kw: tuple[float, ...]
    source_max_kw: tuple[float, ...]
    covered_source_energy_kwh: float

    def __post_init__(self):
        if not isinstance(self.horizon, ActivationHorizon):
            raise TimelineError("horizon: ActivationHorizon required")
        object.__setattr__(self, "as_of", _utc(self.as_of, "as_of"))
        if self.as_of > self.horizon.activation_at:
            raise TimelineError("resampled load as-of time is after activation")
        for name in ("mean_kw", "energy_kwh", "source_min_kw", "source_max_kw"):
            values = tuple(_number(value, name) for value in
                           _sequence(getattr(self, name), name))
            if len(values) != self.horizon.steps or any(value < 0 for value in values):
                raise TimelineError(f"{name}: 96 nonnegative values required")
            object.__setattr__(self, name, values)
        total = _number(self.covered_source_energy_kwh, "covered_source_energy_kwh")
        if total < 0 or any(lo > hi for lo, hi in
                            zip(self.source_min_kw, self.source_max_kw)):
            raise TimelineError("invalid source energy or extrema")
        object.__setattr__(self, "covered_source_energy_kwh", total)

    @property
    def energy_residual_kwh(self):
        return fsum(self.energy_kwh) - self.covered_source_energy_kwh


def _ordered_coverage(intervals, expected_type, start, end):
    rows = _sequence(intervals, "intervals")
    if not rows or any(not isinstance(row, expected_type) for row in rows):
        raise TimelineError(f"nonempty {expected_type.__name__} sequence required")
    rows = tuple(sorted(rows, key=lambda row: row.start_at))
    for previous, current in zip(rows, rows[1:]):
        if previous.end_at != current.start_at:
            kind = "overlap" if previous.end_at > current.start_at else "gap"
            raise TimelineError(f"interval {kind}")
    if rows[0].start_at > start or rows[-1].end_at < end:
        raise TimelineError("intervals do not cover requested time range")
    return rows


def resample_load(intervals, horizon: ActivationHorizon, *, as_of: datetime):
    """Integrate source load over each activation-anchored cell; retain extrema."""
    if not isinstance(horizon, ActivationHorizon):
        raise TimelineError("horizon: ActivationHorizon required")
    cutoff = _utc(as_of, "as_of")
    if cutoff > horizon.activation_at:
        raise TimelineError("forecast as-of time is after activation")
    rows = _ordered_coverage(intervals, IssuedLoadInterval,
                             horizon.activation_at, horizon.end_at)
    if any(row.issued_at > cutoff or row.available_at > cutoff for row in rows):
        raise TimelineError("future-issued or unavailable load interval")
    energies, minima, maxima = [], [], []
    boundaries = horizon.boundaries
    for start, end in zip(boundaries, boundaries[1:]):
        pieces, powers = [], []
        for row in rows:
            seconds = (min(end, row.end_at) - max(start, row.start_at)).total_seconds()
            if seconds > 0:
                pieces.append(row.load_kw * (seconds / 3600.0))
                powers.append(row.load_kw)
        energy = _sum_finite(pieces, "load energy")
        energies.append(energy)
        minima.append(min(powers))
        maxima.append(max(powers))
    source_energy = _sum_finite((
        row.load_kw * (max(0., (min(horizon.end_at, row.end_at) -
                               max(horizon.activation_at, row.start_at)).total_seconds()) / 3600.)
        for row in rows
    ), "source energy")
    means = tuple(e / (horizon.step_seconds / 3600.) for e in energies)
    if not all(isfinite(value) for value in means):
        raise TimelineError("resampled power overflow")
    return ResampledLoad(horizon, cutoff, means, tuple(energies), tuple(minima),
                         tuple(maxima), source_energy)


@dataclass(frozen=True)
class AppliedControlInterval:
    event_id: str
    start_at: datetime
    end_at: datetime
    commands: Mapping[str, float]
    recorded_at: datetime

    def __post_init__(self):
        if not isinstance(self.event_id, str) or not self.event_id.strip():
            raise TimelineError("actual interval requires a nonempty event ID")
        for name in ("start_at", "end_at", "recorded_at"):
            object.__setattr__(self, name, _utc(getattr(self, name), name))
        if self.end_at <= self.start_at:
            raise TimelineError("actual interval must have positive duration")
        if self.recorded_at < self.end_at:
            raise TimelineError("actual interval cannot be recorded before it ends")
        object.__setattr__(self, "commands", _commands(self.commands, "actual commands"))

    @property
    def elapsed_seconds(self):
        return (self.end_at - self.start_at).total_seconds()


def validate_actual_intervals(intervals, *, start_at, end_at, as_of):
    """Validate exact recorded coverage; caller splits records with provenance."""
    start, end, cutoff = (_utc(value, name) for value, name in (
        (start_at, "start_at"), (end_at, "end_at"), (as_of, "as_of")))
    if end <= start or end > cutoff:
        raise TimelineError("actual coverage must be positive and already elapsed")
    rows = _ordered_coverage(intervals, AppliedControlInterval, start, end)
    if rows[0].start_at != start or rows[-1].end_at != end:
        raise TimelineError("actual records must match requested endpoints exactly")
    if any(row.recorded_at > cutoff for row in rows):
        raise TimelineError("actual record is unavailable as of requested time")
    if len({row.event_id for row in rows}) != len(rows):
        raise TimelineError("duplicate actual event ID")
    if any(set(row.commands) != set(rows[0].commands) for row in rows):
        raise TimelineError("actual command channel coverage changed")
    return rows


@dataclass(frozen=True)
class CapabilityMask:
    enabled: frozenset[str]

    def __post_init__(self):
        names = _sequence(self.enabled, "capabilities")
        if any(not isinstance(name, str) or name not in PHYSICAL_CHANNELS for name in names):
            raise TimelineError("only physical command channels may be enabled")
        if len(set(names)) != len(names):
            raise TimelineError("duplicate capability channel")
        enabled = frozenset(names)
        if {"f_fan", "T_CW_sp"} <= enabled:
            raise TimelineError("fan-Hz and CW-setpoint authority are mutually exclusive")
        object.__setattr__(self, "enabled", enabled)


@dataclass(frozen=True)
class ChannelLimits:
    minimum: float
    maximum: float
    max_slew_per_second: float

    def __post_init__(self):
        for name in ("minimum", "maximum", "max_slew_per_second"):
            object.__setattr__(self, name, _number(getattr(self, name), name))
        if self.minimum > self.maximum or self.max_slew_per_second < 0:
            raise TimelineError("invalid channel range or slew rate")


@dataclass(frozen=True)
class FirstMoveProposal:
    activation_at: datetime
    expires_at: datetime
    checked_at: datetime
    actual_at: datetime
    commands: Mapping[str, float]
    requires_activation_recheck: ClassVar[bool] = True

    def __post_init__(self):
        for name in ("activation_at", "expires_at", "checked_at", "actual_at"):
            object.__setattr__(self, name, _utc(getattr(self, name), name))
        if not self.actual_at <= self.checked_at <= self.activation_at:
            raise TimelineError("invalid proposal feedback/check/activation chronology")
        if not 0 < (self.expires_at-self.activation_at).total_seconds() <= 300:
            raise TimelineError("first release must be positive and at most 300 seconds")
        commands = _commands(self.commands, "proposal commands")
        if {"f_fan", "T_CW_sp"} <= set(commands):
            raise TimelineError("fan-Hz and CW-setpoint authority are mutually exclusive")
        object.__setattr__(self, "commands", commands)

    @property
    def duration_seconds(self):
        return (self.expires_at - self.activation_at).total_seconds()

    def active_at(self, instant):
        at = _utc(instant, "instant")
        return self.activation_at <= at < self.expires_at


def propose_first_move(plan: PredictionPlan, actual_commands, capabilities: CapabilityMask,
                       limits: Mapping[str, ChannelLimits], *, actual_at, checked_at,
                       expires_at, max_feedback_age_s):
    """Bounded proposal only; mandatory independent activation check remains."""
    if not isinstance(plan, PredictionPlan) or not isinstance(capabilities, CapabilityMask):
        raise TimelineError("PredictionPlan and CapabilityMask required")
    if not capabilities.enabled:
        raise TimelineError("no physical command authority enabled")
    if not isinstance(limits, Mapping) or any(key not in PHYSICAL_CHANNELS for key in limits):
        raise TimelineError("limits must be a physical-channel mapping")
    actual = _commands(actual_commands, "actual_commands")
    observed = _utc(actual_at, "actual_at")
    checked = _utc(checked_at, "checked_at")
    expires = _utc(expires_at, "expires_at")
    activation = plan.horizon.activation_at
    age_limit = _number(max_feedback_age_s, "max_feedback_age_s")
    if age_limit < 0:
        raise TimelineError("feedback age limit must be nonnegative")
    if not plan.issued_at <= checked <= activation:
        raise TimelineError("plan unavailable at check or check after activation")
    if observed > checked or (checked - observed).total_seconds() > age_limit:
        raise TimelineError("future or stale actual feedback")
    duration = (expires - activation).total_seconds()
    if not 0 < duration <= 300:
        raise TimelineError("first release must be positive and at most 300 seconds")
    commands = {}
    for name in CHANNELS:
        if name not in capabilities.enabled:
            continue
        if name not in actual or name not in limits or not isinstance(limits[name], ChannelLimits):
            raise TimelineError(f"{name}: actual feedback and explicit limits required")
        bound = limits[name]
        target, current = plan.values[0][CHANNELS.index(name)], actual[name]
        if not bound.minimum <= current <= bound.maximum:
            raise TimelineError(f"{name}: actual feedback outside supplied range")
        if not bound.minimum <= target <= bound.maximum:
            raise TimelineError(f"{name}: target outside supplied range")
        delta = bound.max_slew_per_second * duration
        if not isfinite(delta):
            raise TimelineError(f"{name}: slew calculation overflow")
        if not current - delta <= target <= current + delta:
            raise TimelineError(f"{name}: target unreachable within first-release slew")
        commands[name] = target
    return FirstMoveProposal(activation, expires, checked, observed,
                              MappingProxyType(commands))
