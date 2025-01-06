import logging  
from typing import Any, Sequence, Tuple  

import numpy as np  


def cost_per_axis(  
    origin: np.ndarray[float],  
    x: Sequence[Tuple[float, float]],  
    cost_func_params: dict[str, Any] = {},  
) -> Sequence[float]:  
    """计算从原点到一系列点的移动成本。  

    成本计算为原点与目标点之间绝对差值的总和（曼哈顿距离），除以每个轴上扫描仪的速度。  

    参数：  
        origin (np.ndarray): 计算成本的原点。形状为 (n_dim,)  
        x (Sequence[Tuple[float, float]]): 要评估成本的目标点列表。  
            形状为 (n_points, n_dim)  
        cost_func_params (dict[str, Any], 可选): 成本函数参数。默认为 {}。  
            参数：  
            - speed (float): 扫描仪的速度，以 mm/s 表示（默认值：250）  
            - weight (float): 每个轴的权重（默认值：1）  
            - n_tasks (int): 任务数量（默认值：1）  
            - n_dim (int): 维度数量（默认值：2）  
            - axes (Sequence[Sequence[float]]): 要舍入的点的网格  
            - prev_points (np.ndarray): 之前测量的点  

    返回：  
        Sequence[float]: 从原点到每个点的移动成本  
    """  
    logger = logging.getLogger("cost_per_axis")  
    logger.debug("成本函数参数:")  
    for k, v in cost_func_params.items():  
        if isinstance(v, np.ndarray):  
            logger.debug(f"\t{k}: {v.shape}")  
        else:  
            logger.debug(f"\t{k}: {v}")  

    cfp = cost_func_params.copy()  
    speed = cfp.get("speed", 250)  
    if np.array(speed).size == 1:  
        speed = np.ones_like(origin) * speed  
    elif np.array(speed).shape != origin.shape:  
        raise ValueError(f"速度必须是标量或大小为 {origin.shape} 的数组")  
    for i in range(len(speed)):  
        if not speed[i] > 0:  
            speed[i] = 0  
    weight = cfp.get("weight", np.ones_like(origin))  
    if np.array(weight).size == 1:  
        weight = np.ones_like(origin) * weight  
    elif np.array(weight).shape != origin.shape:  
        raise ValueError(f"权重必须是标量或大小为 {origin.shape} 的数组")  

    n_tasks = cfp.get("n_tasks")  
    n_dim = cfp.get("n_dim")  
    axes = cfp.get("axes")  
    prev_points = np.array(cfp.get("prev_points"))[::n_tasks, :-1]  

    distances = np.zeros((len(x), n_dim))  
    out = np.zeros((len(x)))  
    for i, xx in enumerate(x):  
        rounded = round_to_axes(xx, axes)  
        if np.any(np.all(np.isclose(rounded, prev_points), axis=1)):  
            logger.warning(  
                f"点 {np.asarray(xx).ravel()} 舍入到 {rounded}，该点已被测量"  
            )  
            out[i] = 1_000_000_000  
        else:  
            distances[i, :] = np.abs(xx - origin)  
            out[i] = 1 + np.sum(weight * distances / speed)  
    assert len(out) == len(x)  
    return out  


def round_to_axes(  
    x: np.ndarray[float],  
    axes: Sequence[Sequence[float]],  
) -> np.ndarray[float]:  
    """将点舍入到网格上最近的点  

    参数：  
        x (np.ndarray): 要舍入的点  
        axes (Sequence[Sequence[float]]): 要舍入到的点的网格  

    返回：  
        np.ndarray: 舍入后的点  
    """  
    new = np.empty_like(x)  
    for i in range(len(x)):  
        new[i] = np.argmin(np.abs(axes[i] - x[i]))  
    return new