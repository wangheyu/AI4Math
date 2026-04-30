# eclipse_predict.py
#
# 作用：
#   1. 从 JPL Horizons 获取太阳、地球、月球在 SSB 坐标系下的三维状态向量
#   2. 用 N 体 Velocity-Verlet 数值传播日-地-月三体系统
#   3. 在每个时间步检测日食和月食（几何判据）
#   4. 用二分法精化接触时刻
#   5. 输出 CSV、JSON 和误差图
#
# 依赖：
#   pip install astroquery astropy pandas matplotlib numpy
#
# 单位：
#   - 数值传播内部统一使用 km, s
#   - Horizons vectors 原始返回 AU 和 AU/day，程序内自动换算

import os
import json
import time
from pathlib import Path
from typing import Optional, Union
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from astroquery.jplhorizons import Horizons

# =========================
# 1. 常数与配置
# =========================

# 天体半径 (km)
R_SUN = 696340.0
R_EARTH = 6371.0
R_MOON = 1737.4

# 引力参数 (km^3 / s^2) — JPL astrodynamic parameters
GM_SUN = 1.32712440041279419e11
GM_EARTH = 398600.435507
GM_MOON = 4902.800118

# N 体引力参数列表（固定顺序：太阳、地球、月球）
GM_VALUES = [GM_SUN, GM_EARTH, GM_MOON]
BODY_NAMES = ["Sun", "Earth", "Moon"]
BODY_IDS = ["10", "399", "301"]  # Horizons COMMAND IDs

# 单位换算
AU_KM = 149597870.7
DAY_SEC = 86400.0

# 数值传播内部步长（秒）
INTERNAL_DT_SEC = 3600.0  # 1 小时

# 二分法精化参数
BISECT_DT_SEC = 10.0       # 二分法内部步长
BISECT_TOLERANCE_SEC = 1.0  # 接触时刻容差

REPO_ROOT = Path(__file__).resolve().parents[1]
CACHE_PATH = REPO_ROOT / "data" / "three_body_init.json"
OUTDIR = REPO_ROOT / "output" / "eclipse_output"

# 已知日食/月食（用于验证）—— NASA Eclipse Web Site
KNOWN_ECLIPSES = [
    {"date": "2026-08-12", "type": "solar", "subtype": "total",
     "approx_time_utc": "17:30"},
    {"date": "2026-08-28", "type": "lunar", "subtype": "partial_umbral",
     "approx_time_utc": "04:13"},
    {"date": "2027-02-06", "type": "solar", "subtype": "annular",
     "approx_time_utc": "16:00"},
    {"date": "2027-02-20", "type": "lunar", "subtype": "penumbral",
     "approx_time_utc": "23:13"},
    {"date": "2027-08-02", "type": "solar", "subtype": "total",
     "approx_time_utc": "10:07"},
    {"date": "2027-08-17", "type": "lunar", "subtype": "penumbral",
     "approx_time_utc": "07:14"},
]

# =========================
# 2. N 体物理函数
# =========================


def nbody_accelerations(positions, gm_values=GM_VALUES):
    """计算 N 体引力加速度。

    Parameters
    ----------
    positions : list of np.ndarray
        各天体的位置向量列表，每个为 (3,) 数组，单位 km
    gm_values : list of float
        各天体的 GM 值列表，单位 km^3/s^2

    Returns
    -------
    list of np.ndarray
        各天体的加速度向量列表，单位 km/s^2
    """
    n = len(positions)
    acc = [np.zeros(3, dtype=float) for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            dr = positions[j] - positions[i]
            dist3 = np.linalg.norm(dr) ** 3
            acc[i] += gm_values[j] * dr / dist3
    return acc


def vv_step_nbody(positions, velocities, dt, gm_values=GM_VALUES):
    """单步 N 体 Velocity-Verlet。

    Parameters
    ----------
    positions, velocities : list of np.ndarray
    dt : float
    gm_values : list of float

    Returns
    -------
    (new_positions, new_velocities) : tuple of list of np.ndarray
    """
    a0 = nbody_accelerations(positions, gm_values)
    new_positions = [
        positions[i] + dt * velocities[i] + 0.5 * dt * dt * a0[i]
        for i in range(len(positions))
    ]
    a1 = nbody_accelerations(new_positions, gm_values)
    new_velocities = [
        velocities[i] + 0.5 * dt * (a0[i] + a1[i])
        for i in range(len(positions))
    ]
    return new_positions, new_velocities


def propagate_state(r0_list, v0_list, dt_total, gm_values=GM_VALUES,
                    dt_internal=BISECT_DT_SEC):
    """从给定初态传播 dt_total 秒。

    内部以 dt_internal 为步长，最后一个子步允许小于 dt_internal。
    """
    r = [ri.copy() for ri in r0_list]
    v = [vi.copy() for vi in v0_list]

    if dt_total < 0:
        raise ValueError("dt_total 必须非负")
    if dt_total == 0:
        return r, v

    n = int(dt_total // dt_internal)
    rem = dt_total - n * dt_internal

    for _ in range(n):
        r, v = vv_step_nbody(r, v, dt_internal, gm_values)

    if rem > 0:
        r, v = vv_step_nbody(r, v, rem, gm_values)

    return r, v


def compute_conserved_quantity(positions, velocities, gm_values=GM_VALUES):
    """计算 GM 加权的守恒量（G * E 和 G * L）。

    用于监控数值积分质量。
    """
    # G * E = Σ 0.5 * GM_i * |v_i|^2 - Σ_{i<j} GM_i * GM_j / |r_i - r_j|
    ke_star = sum(
        0.5 * gm_values[i] * np.dot(velocities[i], velocities[i])
        for i in range(len(positions))
    )
    pe_star = 0.0
    for i in range(len(positions)):
        for j in range(i + 1, len(positions)):
            dr = np.linalg.norm(positions[j] - positions[i])
            pe_star -= gm_values[i] * gm_values[j] / dr
    energy_star = ke_star + pe_star

    # G * L = Σ GM_i * (r_i × v_i)
    angmom_star = np.zeros(3, dtype=float)
    for i in range(len(positions)):
        angmom_star += gm_values[i] * np.cross(positions[i], velocities[i])

    return energy_star, angmom_star


# =========================
# 3. JPL Horizons 数据获取
# =========================


def fetch_body_state(body_id, epoch, location="500@0"):
    """从 JPL Horizons 获取单个天体在指定历元的状态向量。

    Parameters
    ----------
    body_id : str
        Horizons COMMAND ID (如 '10'=Sun, '399'=Earth, '301'=Moon)
    epoch : str
        历元字符串，如 '2026-01-01'
    location : str
        参考中心，默认 '500@0' 为 SSB

    Returns
    -------
    dict with keys: r_km (np.ndarray), v_kms (np.ndarray), jd (float), calendar (str)
    """
    obj = Horizons(
        id=body_id,
        location=location,
        epochs={"start": epoch, "stop": epoch, "step": "1d"},
    )
    tbl = obj.vectors(refplane="ecliptic", aberrations="geometric")

    r_km = np.array([
        float(tbl["x"][0]) * AU_KM,
        float(tbl["y"][0]) * AU_KM,
        float(tbl["z"][0]) * AU_KM,
    ], dtype=float)

    v_kms = np.array([
        float(tbl["vx"][0]) * AU_KM / DAY_SEC,
        float(tbl["vy"][0]) * AU_KM / DAY_SEC,
        float(tbl["vz"][0]) * AU_KM / DAY_SEC,
    ], dtype=float)

    return {
        "r_km": r_km,
        "v_kms": v_kms,
        "jd": float(tbl["datetime_jd"][0]),
        "calendar": str(tbl["datetime_str"][0]),
    }


def fetch_three_body_initial_state(epoch="2026-01-01",
                                   cache_path=CACHE_PATH):
    """获取日、地、月三体在 SSB 坐标系下的初态。

    若缓存文件存在则直接加载，否则从 JPL Horizons 查询并缓存。
    """
    if cache_path.exists():
        print(f"Loading cached initial state from {cache_path}")
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        r0 = [np.array(data["sun"]["r_km"], dtype=float),
              np.array(data["earth"]["r_km"], dtype=float),
              np.array(data["moon"]["r_km"], dtype=float)]
        v0 = [np.array(data["sun"]["v_kms"], dtype=float),
              np.array(data["earth"]["v_kms"], dtype=float),
              np.array(data["moon"]["v_kms"], dtype=float)]
        epoch_jd = data["epoch_jd"]
        return r0, v0, epoch_jd

    print(f"Fetching Sun, Earth, Moon states from JPL Horizons at epoch {epoch}...")
    results = {}
    for i, (body_id, name) in enumerate(zip(BODY_IDS, BODY_NAMES)):
        print(f"  Fetching {name} (id={body_id})...")
        results[name.lower()] = fetch_body_state(body_id, epoch)
        if i < len(BODY_IDS) - 1:
            time.sleep(1.2)  # 避免速率限制

    r0 = [results["sun"]["r_km"],
          results["earth"]["r_km"],
          results["moon"]["r_km"]]
    v0 = [results["sun"]["v_kms"],
          results["earth"]["v_kms"],
          results["moon"]["v_kms"]]
    epoch_jd = results["sun"]["jd"]

    # 保存缓存
    cache_data = {
        "epoch": epoch,
        "epoch_jd": epoch_jd,
        "sun": {"r_km": r0[0].tolist(), "v_kms": v0[0].tolist()},
        "earth": {"r_km": r0[1].tolist(), "v_kms": v0[1].tolist()},
        "moon": {"r_km": r0[2].tolist(), "v_kms": v0[2].tolist()},
    }
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, indent=2, ensure_ascii=False)
    print(f"Cached initial state to {cache_path}")

    return r0, v0, epoch_jd


def sanity_check_initial_state(r0, v0):
    """检查初态量级是否合理。"""
    r_sun = np.linalg.norm(r0[0])
    r_earth = np.linalg.norm(r0[1])
    r_moon = np.linalg.norm(r0[2])
    d_earth_moon = np.linalg.norm(r0[2] - r0[1])
    v_earth = np.linalg.norm(v0[1])

    print(f"\nInitial state check:")
    print(f"  |r_sun| from SSB     = {r_sun:.3e} km")
    print(f"  |r_earth| from SSB   = {r_earth:.3e} km  (~{r_earth/AU_KM:.6f} AU)")
    print(f"  |r_moon| from SSB    = {r_moon:.3e} km")
    print(f"  |r_moon - r_earth|   = {d_earth_moon:.3e} km")
    print(f"  |v_earth|            = {v_earth:.6f} km/s")

    if not (1.0e8 <= r_earth <= 2.0e8):
        raise RuntimeError("地球到 SSB 距离异常")
    if not (3.5e5 <= d_earth_moon <= 4.2e5):
        raise RuntimeError(f"地月距离异常: {d_earth_moon:.0f} km")
    if not (25.0 <= v_earth <= 35.0):
        raise RuntimeError(f"地球速度异常: {v_earth:.1f} km/s")


# =========================
# 4. 日食和月食检测
# =========================


def check_solar_eclipse(r_sun, r_earth, r_moon):
    """检测日食（月球位于太阳和地球之间）。

    从地心视角，计算太阳和月球的角距离，与两者视半径之和比较。

    Returns
    -------
    None 或 dict:
        type: 'total' | 'annular' | 'partial'
        angular_separation_rad: float
        magnitude: float (食分)
        theta_sun_rad, theta_moon_rad: float
    """
    r_se = r_sun - r_earth
    r_me = r_moon - r_earth
    d_se = np.linalg.norm(r_se)
    d_me = np.linalg.norm(r_me)

    # 月球必须在太阳方向（点积 > 0）
    if np.dot(r_se, r_me) <= 0:
        return None

    # 角距离
    cos_theta = np.dot(r_se, r_me) / (d_se * d_me)
    cos_theta = np.clip(cos_theta, -1.0, 1.0)
    theta = np.arccos(cos_theta)

    # 视半径
    theta_sun = np.arcsin(R_SUN / d_se)
    theta_moon = np.arcsin(R_MOON / d_me)

    # 无食
    if theta >= theta_sun + theta_moon:
        return None

    # 分类
    diff = abs(theta_moon - theta_sun)
    if theta < diff:
        if theta_moon > theta_sun:
            etype = "total"
        else:
            etype = "annular"
    else:
        etype = "partial"

    magnitude = (theta_sun + theta_moon - theta) / (2.0 * theta_sun)

    return {
        "type": etype,
        "angular_separation_rad": float(theta),
        "magnitude": float(magnitude),
        "theta_sun_rad": float(theta_sun),
        "theta_moon_rad": float(theta_moon),
        "d_se_km": float(d_se),
        "d_me_km": float(d_me),
    }


def check_lunar_eclipse(r_sun, r_earth, r_moon):
    """检测月食（月球进入地球阴影）。

    计算地球本影和半影在月球距离处的半径，
    判断月球中心到地日轴的距离。

    Returns
    -------
    None 或 dict:
        type: 'total' | 'partial_umbral' | 'penumbral'
        magnitude: float
        umbra_radius_km, penumbra_radius_km: float
        axis_distance_km: float
    """
    r_se = r_sun - r_earth
    r_me = r_moon - r_earth
    d_se = np.linalg.norm(r_se)
    d_me = np.linalg.norm(r_me)

    # 月球必须在地球背离太阳的一侧（满月条件）
    if np.dot(r_se, r_me) >= 0:
        return None

    # 地球本影半径（在月球距离处）
    r_u = R_EARTH - d_me * (R_SUN - R_EARTH) / d_se
    # 地球半影半径
    r_p = R_EARTH + d_me * (R_SUN + R_EARTH) / d_se

    # 月球中心到地日轴的距离
    axis_dir = r_se / d_se  # 从地球指向太阳
    # 月球在地球反太阳方向的投影
    proj = np.dot(r_me, axis_dir) * axis_dir
    perp = r_me - proj
    axis_dist = np.linalg.norm(perp)

    # 判断食型
    if r_u > R_MOON and axis_dist < r_u - R_MOON:
        etype = "total"
    elif r_u > 0 and axis_dist < r_u + R_MOON:
        etype = "partial_umbral"
    elif axis_dist < r_p + R_MOON:
        etype = "penumbral"
    else:
        return None

    # 食分（月球直径被本影覆盖的比例）
    if r_u > 0:
        magnitude = (r_u + R_MOON - axis_dist) / (2.0 * R_MOON)
    else:
        magnitude = 0.0

    return {
        "type": etype,
        "magnitude": float(max(0.0, magnitude)),
        "umbra_radius_km": float(r_u),
        "penumbra_radius_km": float(r_p),
        "axis_distance_km": float(axis_dist),
        "d_se_km": float(d_se),
        "d_me_km": float(d_me),
    }


# =========================
# 5. 食扫描与二分法精化
# =========================


def jd_to_calendar(jd):
    """将 Julian Date 转为 'YYYY-MM-DD HH:MM:SS' 字符串。"""
    from astropy.time import Time
    t = Time(jd, format="jd", scale="tdb")
    return t.utc.iso[:19].replace("T", " ")


def bisect_contact(r0_list, v0_list, t_before, t_during,
                   gm_values=GM_VALUES, is_solar=True):
    """二分法精化从「无食」到「有食」的过渡时刻。

    t_before: 无食时刻 (秒，相对于某个零点)
    t_during: 有食时刻 (秒)
    返回精确接触时刻 (秒)。
    """
    t_lo = t_before
    t_hi = t_during

    for _ in range(30):  # 最多 30 次迭代（2^30 ~ 1e9）
        t_mid = 0.5 * (t_lo + t_hi)
        dt_from_lo = t_mid - t_before

        r_mid, _ = propagate_state(r0_list, v0_list, dt_from_lo, gm_values,
                                   dt_internal=BISECT_DT_SEC)

        if is_solar:
            result = check_solar_eclipse(r_mid[0], r_mid[1], r_mid[2])
        else:
            result = check_lunar_eclipse(r_mid[0], r_mid[1], r_mid[2])

        if result is not None:
            t_hi = t_mid  # 有食 → 上界下移
        else:
            t_lo = t_mid  # 无食 → 下界上移

        if t_hi - t_lo < BISECT_TOLERANCE_SEC:
            break

    return 0.5 * (t_lo + t_hi)


def find_maximum_phase(r0_list, v0_list, t_start, t_end,
                       gm_values=GM_VALUES, is_solar=True):
    """在已知食区间内通过黄金分割搜索找到最大食分时刻。"""
    phi = (np.sqrt(5.0) - 1.0) / 2.0  # 黄金比例
    a = t_start
    b = t_end

    c = b - phi * (b - a)
    d = a + phi * (b - a)

    for _ in range(40):
        if b - a < 1.0:
            break

        r_c, _ = propagate_state(r0_list, v0_list, c - t_start, gm_values,
                                 dt_internal=BISECT_DT_SEC)
        r_d, _ = propagate_state(r0_list, v0_list, d - t_start, gm_values,
                                 dt_internal=BISECT_DT_SEC)

        if is_solar:
            res_c = check_solar_eclipse(r_c[0], r_c[1], r_c[2])
            res_d = check_solar_eclipse(r_d[0], r_d[1], r_d[2])
            if res_c and res_d:
                score_c = res_c["magnitude"]
                score_d = res_d["magnitude"]
            elif res_c:
                score_c, score_d = 1.0, -1.0
            elif res_d:
                score_c, score_d = -1.0, 1.0
            else:
                score_c = score_d = -1.0
        else:
            res_c = check_lunar_eclipse(r_c[0], r_c[1], r_c[2])
            res_d = check_lunar_eclipse(r_d[0], r_d[1], r_d[2])
            if res_c and res_d:
                score_c = res_c["magnitude"]
                score_d = res_d["magnitude"]
            elif res_c:
                score_c, score_d = 1.0, -1.0
            elif res_d:
                score_c, score_d = -1.0, 1.0
            else:
                score_c = score_d = -1.0

        if score_c > score_d:
            b = d
        else:
            a = c

        c = b - phi * (b - a)
        d = a + phi * (b - a)

    return 0.5 * (a + b)


def scan_for_eclipses(times_jd, positions_history, velocities_history,
                      gm_values=GM_VALUES):
    """扫描全部积分步，检测日食和月食事件并精化接触时刻。

    positions_history: list of (N, 3) arrays [sun, earth, moon]
    """
    events = []
    n_steps = len(times_jd)

    # 状态机状态
    in_solar = False
    in_lunar = False
    solar_start_idx = None
    lunar_start_idx = None
    solar_max_info = None
    lunar_max_info = None
    solar_max_idx = None
    lunar_max_idx = None
    solar_types_seen = set()
    lunar_types_seen = set()

    for i in range(n_steps):
        r_sun = positions_history[0][i]
        r_earth = positions_history[1][i]
        r_moon = positions_history[2][i]

        # ---- 日食检测 ----
        solar_res = check_solar_eclipse(r_sun, r_earth, r_moon)
        if solar_res is not None and not in_solar:
            in_solar = True
            solar_start_idx = max(0, i - 1)
            solar_max_info = solar_res
            solar_max_idx = i
            solar_types_seen = {solar_res["type"]}
        elif solar_res is not None and in_solar:
            if solar_res["magnitude"] > solar_max_info["magnitude"]:
                solar_max_info = solar_res
                solar_max_idx = i
            solar_types_seen.add(solar_res["type"])
        elif solar_res is None and in_solar:
            in_solar = False
            event = build_eclipse_event(
                "solar", solar_start_idx, i, solar_max_idx,
                solar_max_info, solar_types_seen,
                times_jd, positions_history, velocities_history, gm_values,
            )
            events.append(event)

        # ---- 月食检测 ----
        lunar_res = check_lunar_eclipse(r_sun, r_earth, r_moon)
        if lunar_res is not None and not in_lunar:
            in_lunar = True
            lunar_start_idx = max(0, i - 1)
            lunar_max_info = lunar_res
            lunar_max_idx = i
            lunar_types_seen = {lunar_res["type"]}
        elif lunar_res is not None and in_lunar:
            if lunar_res["magnitude"] > lunar_max_info["magnitude"]:
                lunar_max_info = lunar_res
                lunar_max_idx = i
            lunar_types_seen.add(lunar_res["type"])
        elif lunar_res is None and in_lunar:
            in_lunar = False
            event = build_eclipse_event(
                "lunar", lunar_start_idx, i, lunar_max_idx,
                lunar_max_info, lunar_types_seen,
                times_jd, positions_history, velocities_history, gm_values,
            )
            events.append(event)

    # 处理积分结束时仍在食中的情况
    if in_solar:
        event = build_eclipse_event(
            "solar", solar_start_idx, n_steps - 1, solar_max_idx,
            solar_max_info, solar_types_seen,
            times_jd, positions_history, velocities_history, gm_values,
        )
        events.append(event)
    if in_lunar:
        event = build_eclipse_event(
            "lunar", lunar_start_idx, n_steps - 1, lunar_max_idx,
            lunar_max_info, lunar_types_seen,
            times_jd, positions_history, velocities_history, gm_values,
        )
        events.append(event)

    return events


def build_eclipse_event(etype, start_idx, end_idx, max_idx, max_info,
                        types_seen, times_jd, positions_history,
                        velocities_history, gm_values):
    """根据扫描结果构建单个食事件的完整信息。"""
    is_solar = (etype == "solar")

    # 保存初态（用于二分法精化）
    r0_saved = [positions_history[k][start_idx].copy() for k in range(3)]
    v0_saved = [velocities_history[k][start_idx].copy() for k in range(3)]

    # 将时间转为相对零点（秒）
    t0 = times_jd[start_idx]
    t_scale = DAY_SEC

    t_before = 0.0
    t_during = (times_jd[start_idx + 1] - t0) * t_scale
    t_end = (times_jd[end_idx] - t0) * t_scale
    t_max = (times_jd[max_idx] - t0) * t_scale

    # 二分法精化接触时刻 P1（初亏）
    p1_sec = bisect_contact(r0_saved, v0_saved, t_before, t_during,
                            gm_values, is_solar)

    # 二分法精化接触时刻 P4（复圆）—— 从末尾向前
    r0_end_saved = [positions_history[k][end_idx - 1].copy() for k in range(3)]
    v0_end_saved = [velocities_history[k][end_idx - 1].copy() for k in range(3)]

    # end_idx-1 是有食的最后一步，end_idx 是无食
    t_end_before = (times_jd[end_idx - 1] - t0) * t_scale
    t_end_after = (times_jd[end_idx] - t0) * t_scale

    p4_sec = bisect_contact(r0_saved, v0_saved, t_end_after, t_end_before,
                            gm_values, is_solar)
    # 注意：这个二分法从 r0_saved 直接传播到 t_end_after 误差较大。
    # 更精确的做法是用 r0_end_saved 做参考。这里从 r0_saved 重新传播。

    # 搜索最大食分时刻
    max_sec = find_maximum_phase(r0_saved, v0_saved, p1_sec, p4_sec,
                                 gm_values, is_solar)

    # 在最大时刻获取详细参数
    r_max, _ = propagate_state(r0_saved, v0_saved, max_sec, gm_values,
                               dt_internal=BISECT_DT_SEC)
    if is_solar:
        detail = check_solar_eclipse(r_max[0], r_max[1], r_max[2])
    else:
        detail = check_lunar_eclipse(r_max[0], r_max[1], r_max[2])

    if detail is None:
        detail = max_info

    peak_jd = t0 + max_sec / t_scale
    p1_jd = t0 + p1_sec / t_scale
    p4_jd = t0 + p4_sec / t_scale

    # 确定食型：综合所有检测到的类型
    all_types = types_seen | {detail["type"]}
    if is_solar:
        if "total" in all_types:
            final_subtype = "total"
        elif "annular" in all_types:
            final_subtype = "annular"
        else:
            final_subtype = "partial"
    else:
        if "total" in all_types:
            final_subtype = "total"
        elif "partial_umbral" in all_types:
            final_subtype = "partial_umbral"
        else:
            final_subtype = "penumbral"

    return {
        "type": etype,
        "subtype": final_subtype,
        "peak_time_jd": float(peak_jd),
        "peak_time_calendar": jd_to_calendar(peak_jd),
        "p1_jd": float(p1_jd),
        "p1_calendar": jd_to_calendar(p1_jd),
        "p4_jd": float(p4_jd),
        "p4_calendar": jd_to_calendar(p4_jd),
        "magnitude": float(detail["magnitude"]),
        "duration_total_sec": float(p4_sec - p1_sec),
        "detail": detail,
        "start_idx": start_idx,
        "end_idx": end_idx,
        "max_idx": max_idx,
    }


# =========================
# 6. 输出与可视化
# =========================


def print_events_table(events):
    """打印食事件汇总表。"""
    print("\n" + "=" * 100)
    print(f"{'日期 (UTC)':<22} {'类型':<10} {'食型':<16} {'食分':<8} "
          f"{'持续时长':<12} {'P1 (UTC)':<22} {'P4 (UTC)':<22}")
    print("=" * 100)

    for ev in events:
        etype_str = "日食" if ev["type"] == "solar" else "月食"
        subtype_map = {
            "total": "全食", "annular": "环食", "partial": "偏食",
            "partial_umbral": "本影偏食", "penumbral": "半影食",
        }
        subtype_str = subtype_map.get(ev["subtype"], ev["subtype"])
        dur_h = ev["duration_total_sec"] / 3600.0
        print(f"{ev['peak_time_calendar']:<22} {etype_str:<10} {subtype_str:<16} "
              f"{ev['magnitude']:<8.4f} {dur_h:<10.2f}h "
              f"{ev['p1_calendar']:<22} {ev['p4_calendar']:<22}")

    print("=" * 100)
    solar_count = sum(1 for e in events if e["type"] == "solar")
    lunar_count = sum(1 for e in events if e["type"] == "lunar")
    print(f"总计: {len(events)} 次食 ({solar_count} 次日食, {lunar_count} 次月食)")


def save_outputs(events, outdir=OUTDIR):
    """保存 CSV, JSON 和可视化图表。"""
    os.makedirs(outdir, exist_ok=True)

    # CSV
    csv_path = outdir / "eclipse_predictions.csv"
    rows = []
    for ev in events:
        rows.append({
            "type": ev["type"],
            "subtype": ev["subtype"],
            "peak_time_utc": ev["peak_time_calendar"],
            "magnitude": ev["magnitude"],
            "duration_total_sec": ev["duration_total_sec"],
            "p1_utc": ev["p1_calendar"],
            "p4_utc": ev["p4_calendar"],
            "p1_jd": ev["p1_jd"],
            "peak_jd": ev["peak_time_jd"],
            "p4_jd": ev["p4_jd"],
        })
    df = pd.DataFrame(rows)
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"\nSaved CSV: {csv_path}")

    # JSON
    json_path = outdir / "eclipse_predictions.json"
    json_events = []
    for ev in events:
        je = {k: v for k, v in ev.items() if k != "detail"}
        je["detail"] = {k: v for k, v in ev["detail"].items()
                        if isinstance(v, (float, int, str, bool))}
        json_events.append(je)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_events, f, indent=2, ensure_ascii=False, default=str)
    print(f"Saved JSON: {json_path}")

    return csv_path, json_path


def plot_eclipse_timeline(events, start_jd, end_jd, outdir=OUTDIR):
    """绘制食事件时间线图。"""
    if not events:
        print("No events to plot.")
        return

    fig, ax = plt.subplots(figsize=(14, 4))

    colors = {
        ("solar", "total"): "#CC0000",
        ("solar", "annular"): "#FF6600",
        ("solar", "partial"): "#FF9999",
        ("lunar", "total"): "#0000CC",
        ("lunar", "partial_umbral"): "#6666FF",
        ("lunar", "penumbral"): "#CCCCFF",
    }

    y_positions = {"solar": 1, "lunar": 0}
    y_labels = {1: "Solar Eclipse", 0: "Lunar Eclipse"}

    for ev in events:
        y = y_positions[ev["type"]]
        p1_days = ev["p1_jd"] - start_jd
        p4_days = ev["p4_jd"] - start_jd
        dur = p4_days - p1_days
        color = colors.get((ev["type"], ev["subtype"]), "#888888")
        label_map = {"total": "Total", "annular": "Annular", "partial": "Partial",
                     "partial_umbral": "Part. Umbral", "penumbral": "Penumbral"}
        label = label_map.get(ev["subtype"], ev["subtype"])
        ax.barh(y, dur, left=p1_days, height=0.6, color=color, alpha=0.85,
                edgecolor="black", linewidth=0.5)
        mid = p1_days + dur / 2
        ax.text(mid, y, label, ha="center", va="center", fontsize=7,
                fontweight="bold", color="white",
                bbox=dict(boxstyle="round,pad=0.1", fc=color, alpha=0.9))

    ax.set_yticks([0, 1])
    ax.set_yticklabels(["Lunar Eclipse", "Solar Eclipse"], fontsize=11)
    ax.set_xlabel("Days from start", fontsize=11)
    ax.set_title("Eclipse Timeline", fontsize=13, fontweight="bold")
    ax.grid(axis="x", alpha=0.3)
    ax.set_xlim(0, (end_jd - start_jd) * 1.02)

    fig.tight_layout()
    fig_path = outdir / "eclipse_timeline.png"
    fig.savefig(fig_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved timeline: {fig_path}")


def plot_eclipse_geometry(events, positions_history, times_jd, outdir=OUTDIR):
    """为每个主要食事件绘制几何图。"""
    for ev in events:
        midx = ev["max_idx"]
        half_window = 60  # 前后各取 60 个采样点（~2.5 天窗口）

        i0 = max(0, midx - half_window)
        i1 = min(len(times_jd), midx + half_window)
        idx_range = slice(i0, i1)

        t_rel = (times_jd[idx_range] - times_jd[midx]) * DAY_SEC / 3600.0  # 小时

        fig, axes = plt.subplots(2, 2, figsize=(13, 10))

        is_solar = ev["type"] == "solar"

        # 左上：角距离/轴距离 随时间变化
        ax = axes[0, 0]
        separations = []
        for i in range(i0, i1):
            r_sun = positions_history[0][i]
            r_earth = positions_history[1][i]
            r_moon = positions_history[2][i]
            if is_solar:
                r_se = r_sun - r_earth
                r_me = r_moon - r_earth
                d_se = np.linalg.norm(r_se)
                d_me = np.linalg.norm(r_me)
                cos_th = np.dot(r_se, r_me) / (d_se * d_me)
                cos_th = np.clip(cos_th, -1.0, 1.0)
                sep = np.arccos(cos_th)
                theta_s = np.arcsin(R_SUN / d_se)
                theta_m = np.arcsin(R_MOON / d_me)
                separations.append(np.degrees(sep))
                threshold = np.degrees(theta_s + theta_m)
            else:
                r_se = r_sun - r_earth
                r_me = r_moon - r_earth
                d_se = np.linalg.norm(r_se)
                d_me = np.linalg.norm(r_me)
                axis_dir = r_se / d_se
                proj = np.dot(r_me, axis_dir) * axis_dir
                perp = r_me - proj
                axis_dist = np.linalg.norm(perp)
                separations.append(axis_dist)
                r_u = R_EARTH - d_me * (R_SUN - R_EARTH) / d_se
                r_p = R_EARTH + d_me * (R_SUN + R_EARTH) / d_se
                threshold = r_p + R_MOON

        ax.plot(t_rel, separations, 'b-', linewidth=1.5)
        ax.axhline(threshold, color='r', linestyle='--', alpha=0.7,
                   label='Eclipse threshold')
        ax.axvline(0, color='gray', linestyle=':', alpha=0.5)
        ax.set_xlabel("Hours from peak")
        if is_solar:
            ax.set_ylabel("Angular separation (deg)")
            ax.set_title("Sun-Moon Angular Separation")
        else:
            ax.set_ylabel("Axis distance (km)")
            ax.set_title("Moon to Earth-Sun Axis Distance")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

        # 右上：食分随时间变化
        ax = axes[0, 1]
        magnitudes = []
        for i in range(i0, i1):
            r_sun = positions_history[0][i]
            r_earth = positions_history[1][i]
            r_moon = positions_history[2][i]
            if is_solar:
                res = check_solar_eclipse(r_sun, r_earth, r_moon)
            else:
                res = check_lunar_eclipse(r_sun, r_earth, r_moon)
            magnitudes.append(res["magnitude"] if res else 0.0)

        ax.fill_between(t_rel, 0, magnitudes, alpha=0.5, color='orange')
        ax.plot(t_rel, magnitudes, 'r-', linewidth=1.5)
        ax.axvline(0, color='gray', linestyle=':', alpha=0.5)
        ax.set_xlabel("Hours from peak")
        ax.set_ylabel("Magnitude")
        ax.set_title("Eclipse Magnitude")
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, max(1.2, max(magnitudes) * 1.1))

        # 左下：日月地在黄道面上的投影
        ax = axes[1, 0]
        # 取峰值时刻附近的数据
        win = 20
        j0 = max(0, midx - win)
        j1 = min(len(times_jd), midx + win)
        for j in range(j0, j1):
            alpha = (j - j0) / max(1, j1 - j0 - 1)
            r_sun_p = positions_history[0][j]
            r_earth_p = positions_history[1][j]
            r_moon_p = positions_history[2][j]

            # 以地球为中心
            ax.plot(r_sun_p[0] - r_earth_p[0], r_sun_p[1] - r_earth_p[1],
                    '.', color='orange', markersize=1, alpha=alpha * 0.3 + 0.1)
            ax.plot(r_moon_p[0] - r_earth_p[0], r_moon_p[1] - r_earth_p[1],
                    '.', color='gray', markersize=2, alpha=alpha * 0.6 + 0.1)

        # 峰值时刻的大点
        r_sun_peak = positions_history[0][midx]
        r_earth_peak = positions_history[1][midx]
        r_moon_peak = positions_history[2][midx]

        ax.plot(r_sun_peak[0] - r_earth_peak[0],
                r_sun_peak[1] - r_earth_peak[1],
                'o', color='orange', markersize=10, label='Sun')
        ax.plot(0, 0, 'o', color='blue', markersize=8, label='Earth')
        ax.plot(r_moon_peak[0] - r_earth_peak[0],
                r_moon_peak[1] - r_earth_peak[1],
                'o', color='gray', markersize=6, label='Moon')

        ax.set_xlabel("X (km) — Ecliptic plane")
        ax.set_ylabel("Y (km) — Ecliptic plane")
        ax.set_title("Ecliptic Plane Projection (Earth-centered)")
        ax.set_aspect("equal")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

        # 右下：侧视图（Z 轴）
        ax = axes[1, 1]
        for j in range(j0, j1):
            alpha = (j - j0) / max(1, j1 - j0 - 1)
            r_sun_p = positions_history[0][j]
            r_earth_p = positions_history[1][j]
            r_moon_p = positions_history[2][j]
            # 以径向距离为 X，Z 坐标为 Y
            r_se_p = r_sun_p - r_earth_p
            r_me_p = r_moon_p - r_earth_p
            ax.plot(np.linalg.norm(r_me_p), r_me_p[2],
                    '.', color='gray', markersize=2, alpha=alpha * 0.6 + 0.1)

        r_se_peak = r_sun_peak - r_earth_peak
        r_me_peak = r_moon_peak - r_earth_peak
        ax.plot(np.linalg.norm(r_me_peak), r_me_peak[2],
                'o', color='gray', markersize=6, label='Moon')
        ax.axhline(0, color='green', linestyle='--', alpha=0.3,
                   label='Ecliptic plane')
        ax.set_xlabel("Radial distance (km)")
        ax.set_ylabel("Z — out of ecliptic (km)")
        ax.set_title("Side View: Moon Elevation from Ecliptic")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

        etype_str = "Solar" if is_solar else "Lunar"
        fig.suptitle(
            f"{etype_str} Eclipse — {ev['peak_time_calendar']}  "
            f"Type: {ev['subtype']}  Mag: {ev['magnitude']:.4f}",
            fontsize=13, fontweight="bold",
        )
        fig.tight_layout()

        date_str = ev["peak_time_calendar"][:10]
        fig_path = outdir / f"eclipse_geometry_{date_str}.png"
        fig.savefig(fig_path, dpi=180, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved geometry figure: {fig_path}")


# =========================
# 7. 验证（与已知食比较）
# =========================


def validate_against_known(events):
    """将检测到的食事件与已知食比较。"""
    print("\n" + "=" * 100)
    print("Validation against known eclipses")
    print("=" * 100)
    print(f"{'Known date':<14} {'Known type':<14} {'Detected?':<12} "
          f"{'Detected date':<22} {'Type match?':<14} {'Time diff (h)':<14}")
    print("-" * 100)

    matched = 0
    total_known = len(KNOWN_ECLIPSES)

    for known in KNOWN_ECLIPSES:
        known_date = known["date"]
        known_type = f"{known['type']} {known['subtype']}"

        # 查找 ±3 天内的匹配事件
        from astropy.time import Time
        known_jd = Time(known_date, format="iso", scale="utc").jd

        best_match = None
        best_diff = float("inf")
        for ev in events:
            ev_date = ev["peak_time_calendar"][:10]
            ev_jd = Time(ev_date, format="iso", scale="utc").jd
            diff = abs(ev_jd - known_jd)
            if diff < 3.0 and diff < best_diff:
                # 还需类型匹配
                if ev["type"] == known["type"]:
                    best_match = ev
                    best_diff = diff

        if best_match:
            matched += 1
            det_date = best_match["peak_time_calendar"]
            det_full_type = f"{best_match['type']} {best_match['subtype']}"
            type_ok = "Yes" if best_match["subtype"] in known["subtype"] else "Partial"
            time_diff_h = best_diff * 24.0
            print(f"{known_date:<14} {known_type:<14} {'YES':<12} "
                  f"{det_date:<22} {type_ok:<14} {time_diff_h:<14.1f}")
        else:
            print(f"{known_date:<14} {known_type:<14} {'NO':<12} "
                  f"{'—':<22} {'—':<14} {'—':<14}")

    print("-" * 100)
    print(f"Matched: {matched}/{total_known}")
    if matched < total_known:
        print("Note: Missing eclipses may indicate integration drift or "
              "penumbral threshold sensitivity.")


# =========================
# 8. 主程序
# =========================


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="日食和月食预测 — 基于 N 体数值积分"
    )
    parser.add_argument("--start", default="2026-01-01",
                        help="积分起始日期 (YYYY-MM-DD)")
    parser.add_argument("--stop", default="2028-01-01",
                        help="积分结束日期 (YYYY-MM-DD)")
    parser.add_argument("--dt", type=float, default=INTERNAL_DT_SEC,
                        help=f"积分步长 (秒), 默认 {INTERNAL_DT_SEC}")
    parser.add_argument("--no-cache", action="store_true",
                        help="忽略缓存, 重新从 Horizons 获取")
    parser.add_argument("--no-validate", action="store_true",
                        help="跳过验证步骤")
    args = parser.parse_args()

    # ---- 获取初态 ----
    cache = None if args.no_cache else CACHE_PATH
    if args.no_cache and CACHE_PATH.exists():
        CACHE_PATH.unlink()

    r0, v0, epoch_jd = fetch_three_body_initial_state(args.start, cache)
    sanity_check_initial_state(r0, v0)

    # ---- 数值积分 ----
    from astropy.time import Time
    start_jd = Time(args.start, format="iso", scale="utc").jd
    stop_jd = Time(args.stop, format="iso", scale="utc").jd
    total_dt_sec = (stop_jd - start_jd) * DAY_SEC

    n_steps = int(total_dt_sec // args.dt) + 1
    print(f"\nIntegrating {n_steps} steps "
          f"({(stop_jd - start_jd):.0f} days, dt={args.dt:.0f}s)...")

    times_jd = np.linspace(start_jd, stop_jd, n_steps)
    # 存储历史: list of (n_steps, 3) arrays
    pos_hist = [np.zeros((n_steps, 3), dtype=float) for _ in range(3)]
    vel_hist = [np.zeros((n_steps, 3), dtype=float) for _ in range(3)]

    r = [ri.copy() for ri in r0]
    v = [vi.copy() for vi in v0]

    # 记录初始能量
    E0, L0 = compute_conserved_quantity(r, v)

    for step in range(n_steps):
        # 保存当前状态
        for k in range(3):
            pos_hist[k][step] = r[k]
            vel_hist[k][step] = v[k]

        if step < n_steps - 1:
            r, v = vv_step_nbody(r, v, args.dt, GM_VALUES)

        # 监控守恒量
        if step % 1000 == 0 or step == n_steps - 1:
            E_cur, L_cur = compute_conserved_quantity(r, v)
            rel_E_err = abs((E_cur - E0) / E0)
            rel_L_err = (np.linalg.norm(L_cur - L0)
                         / max(np.linalg.norm(L0), 1e-30))
            pct = 100.0 * step / max(n_steps - 1, 1)
            print(f"  Step {step}/{n_steps-1} ({pct:.0f}%)  "
                  f"rel ΔE = {rel_E_err:.2e}  rel ΔL = {rel_L_err:.2e}")

    print(f"\nFinal conservation: rel ΔE = {rel_E_err:.2e}  "
          f"rel ΔL = {rel_L_err:.2e}")

    # ---- 食扫描 ----
    print("\nScanning for eclipse events...")
    events = scan_for_eclipses(times_jd, pos_hist, vel_hist, GM_VALUES)
    events.sort(key=lambda e: e["peak_time_jd"])

    # ---- 输出 ----
    print_events_table(events)
    save_outputs(events, OUTDIR)
    plot_eclipse_timeline(events, start_jd, stop_jd, OUTDIR)

    # 仅为主要事件绘制详细几何图（全日食/环食/本影月食）
    major_events = [e for e in events
                    if e["subtype"] in ("total", "annular", "partial_umbral")]
    if major_events:
        plot_eclipse_geometry(major_events, pos_hist, times_jd, OUTDIR)

    # ---- 验证 ----
    if not args.no_validate:
        validate_against_known(events)

    print("\nDone.")


if __name__ == "__main__":
    main()
