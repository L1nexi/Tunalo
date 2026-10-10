"""语义曲线和概率计算共用的数学工具，不读取业务配置或运行时状态。"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence


def softmax[K](scores: Mapping[K, float], temperature: float, scale: float = 1.0) -> dict[K, float]:
    """把一组分数转换为总和为 1 的概率分布。

    对每个键 k，计算 exp(scores[k] * scale / temperature)，再除以所有
    键的指数值之和。返回字典保留原来的键，分数越高，得到的概率越大。

    temperature 是温度：越小越集中于高分项，越大越接近均匀分配。
    scale 用来恢复分数的原始尺度；若调用方预先将分数除以某个数以避免
    求和溢出，这里传入该数。未缩放的分数使用默认值 1。

    输入分数必须非空且有限，temperature 和 scale 必须为正数。

    异常：
        ValueError：输入分数为空时抛出。
    """
    # 所有分数先减去最大值，不改变理论概率，并避免直接对很大的正数求指数。
    peak = max(scores.values())
    weights = {key: math.exp(((value - peak) / temperature) * scale) for key, value in scores.items()}
    total = math.fsum(weights.values())
    return {key: weight / total for key, weight in weights.items()}


def s_curve(z: float, q: float) -> float:
    """将 [0, 1] 内的幅度 z 映射为同一区间内的非线性响应。

    计算 f(z) = (1 - 2 ** (-(z / q) ** 3)) / (1 - 2 ** (-(1 / q) ** 3))。
    分子是三次指数曲线，分母用 z=1 时的值归一化，使 f(0)=0、f(1)=1。
    它保留幅度的大小关系，避免把微弱证据直接当成完整支持。

    q 必须为正数，用来调节曲线形状；q 越小，响应越早接近 1。
    在归一化之前，z=q 对应分子值 0.5；归一化后的 f(q) 不一定等于 0.5。
    """
    # expm1(x) 直接计算 exp(x)-1，避免接近零时相减丢失有效数字。
    return -math.expm1(-math.log(2) * (z / q) ** 3) / -math.expm1(-math.log(2) * (1 / q) ** 3)


def periodic_salience(position: float, anchors: Sequence[tuple[float, float]], period: float, half_width: float, q: float) -> float:
    """根据周期锚点，计算当前位置的有符号曲线值。

    anchors 的每项是（位置，取值），按一个周期内的先后顺序排列。
    position 是待求值的位置，period 是周期长度；取模使最后一个锚点
    能接回第一个锚点，例如跨午夜或跨年。锚点取值可以为正、零或负。

    每个锚点前后 half_width 范围内保持该锚点的值，形成平台。
    相邻平台之间，将位置转换为进度 t，再计算：
        起点值 + (终点值 - 起点值) * s_curve(t, q)。
    half_width=0 时不保留平台，直接在相邻锚点间过渡。

    period 和 q 必须为正数，half_width 必须非负，相邻平台不能重叠。

    异常：
        ValueError：锚点未覆盖完整周期，无法定位当前区间时抛出。
    """
    for index, (start, start_value) in enumerate(anchors):
        distance = (position - start) % period
        # 取模后距离接近周期末尾，表示当前位置处于锚点之前的平台内。
        if distance <= half_width or distance >= period - half_width:
            return start_value
        end, end_value = anchors[(index + 1) % len(anchors)]
        span = (end - start) % period
        if distance < span - half_width:
            # 扣除两端平台，只在中间的过渡区间内将进度归一化到 [0, 1]。
            progress = (distance - half_width) / (span - 2 * half_width)
            return start_value + (end_value - start_value) * s_curve(progress, q)
    raise ValueError("periodic anchors must cover the complete cycle")
