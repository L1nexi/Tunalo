"""概率归一化、显著度激活、时间衰减、相位映射和周期语义的纯数学函数。"""

from __future__ import annotations

import math
from collections.abc import Mapping


def softmax[K](scores: Mapping[K, float], temperature: float) -> dict[K, float]:
    """把一组分数转换为总和为 1 的概率分布。

    对每个键 k，计算 exp(scores[k] / temperature)，再除以所有
    键的指数值之和。返回字典保留原来的键，分数越高，得到的概率越大。

    temperature 是温度：越小越集中于高分项，越大越接近均匀分配。
    输入分数必须非空且有限，temperature 必须为正数。

    异常：
        ValueError：输入分数为空时抛出。
    """
    # 所有分数先减去最大值，不改变理论概率，并避免直接对很大的正数求指数。
    peak = max(scores.values())
    weights = {key: math.exp((value - peak) / temperature) for key, value in scores.items()}
    total = math.fsum(weights.values())
    return {key: weight / total for key, weight in weights.items()}


def salience_activation(value: float, alpha: float = 2.0) -> float:
    """将 [-1, 1] 的支持依据映射为同一区间的有符号显著度。

    对称幂函数保持零点和端点，中心斜率为 alpha，两端斜率为零。
    value 必须位于 [-1, 1]，alpha 必须有限且大于 1。
    """
    support = 1 + value
    opposition = 1 - value
    # 同比缩放底数不改变结果，避免较大 alpha 引起幂运算溢出。
    scale = max(support, opposition)
    support = (support / scale) ** alpha
    opposition = (opposition / scale) ** alpha
    return (support - opposition) / (support + opposition)


def time_decaying_activation(age: float, *, scale: float = 1.0, alpha: float = 2.0) -> float:
    """将非负年龄转换为 [0, 1] 内的衰减权重。

    年龄为零时权重为 1，scale 时为 0.5，2 * scale 及之后为零。
    scale 必须为正数，alpha 必须有限且大于 1。

    异常：
        ZeroDivisionError：scale 为零时抛出。
    """
    value = max(1 - age / scale, -1.0)
    return (1 + salience_activation(value, alpha)) / 2


def mirrored_phase(progress: float, *, phase_gamma: float = 2.0, reverse: bool = False) -> float:
    """将 [0, 1] 的段内进度映射为保持端点的幂相位。

    默认返回 progress ** phase_gamma；reverse 时返回其镜像
    1 - (1 - progress) ** phase_gamma。phase_gamma 必须有限且不小于 1，
    默认值为 2，取 1 时保留线性映射。
    """
    if reverse:
        return 1 - (1 - progress) ** phase_gamma
    return progress**phase_gamma


def periodic_salience(position: float, peak: float, period: float, *, plateau_half_width: float = 0.0, alpha: float = 2.0) -> float:
    """按距本位峰值的最短周期距离计算有符号显著度。

    本位峰值为 +1，四分之一周期为零，半周期为 -1。
    本位与相对位置可各保留前后 plateau_half_width 的常值平台。
    period 必须为正数，平台半宽必须非负且小于 period / 4；
    alpha 必须有限且大于 1。

    异常：
        ZeroDivisionError：period 为零时抛出。
    """
    delta = abs(position - peak) % period
    distance = min(delta, period - delta)
    half_period = period / 2
    if distance <= plateau_half_width:
        return 1.0
    if distance >= half_period - plateau_half_width:
        return -1.0
    value = (half_period - 2 * distance) / (half_period - 2 * plateau_half_width)
    return salience_activation(value, alpha)
