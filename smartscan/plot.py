import matplotlib.pyplot as plt  
import numpy as np  
from scipy.spatial import Voronoi  
from itertools import product  
from typing import Any, Callable, Sequence  


def plot_aqf_panel(  
    gp,  
    fig: plt.Figure | None,  
    pos: np.ndarray,  
    val: np.ndarray,  
    shape: tuple | None = None,  
    old_aqf: np.ndarray | None = None,  
    last_spectrum: np.ndarray | None = None,  
    settings: dict | None = None,  
) -> tuple[plt.Figure | Any, np.ndarray]:  
    """实时可视化高斯过程的采集函数，驱动数据采集。"""  

    positions = gp.x_data  # 获取当前数据点的位置  

    # 如果没有提供形状，则从设置中获取  
    if shape is None:  
        shape = settings["plots"]["posterior_map_shape"]  

    # 初始化预测点  
    x_pred_0 = np.empty((np.prod(shape), 3))  
    x_pred_1 = np.empty((np.prod(shape), 3))  
    counter = 0  
    x = np.linspace(0, shape[0] - 1, shape[0])  
    y = np.linspace(0, shape[1] - 1, shape[1])  

    # 获取输入空间的边界  
    lim_x = gp.input_space_bounds[0]  
    lim_y = gp.input_space_bounds[1]  

    # 计算每个预测点的增量  
    delta_x = (lim_x[1] - lim_x[0]) / shape[0]  
    delta_y = (lim_y[1] - lim_y[0]) / shape[1]  

    # 填充预测点  
    for i in x:  
        for j in y:  
            x_pred_0[counter] = np.array(  
                [delta_x * i + lim_x[0], delta_y * j + lim_y[0], 0]  
            )  
            x_pred_1[counter] = np.array(  
                [delta_x * i + lim_x[0], delta_y * j + lim_y[0], 1]  
            )  
            counter += 1  

    # 计算后验均值和方差  
    PM0 = np.reshape(gp.posterior_mean(x_pred_0)["f(x)"], shape)  
    PV0 = np.reshape(gp.posterior_covariance(x_pred_0)["v(x)"], shape)  
    sPV0 = np.sqrt(PV0)  
    PM1 = np.reshape(gp.posterior_mean(x_pred_1)["f(x)"], shape)  
    PV1 = np.reshape(gp.posterior_covariance(x_pred_1)["v(x)"], shape)  
    sPV1 = np.sqrt(PV1)  

    # 计算采集函数  
    a = settings["acquisition_function"]["params"]["a"]  
    norm = settings["acquisition_function"]["params"]["norm"]  
    w = settings["acquisition_function"]["params"]["weights"]  
    if w is None:  
        w = (1, 1)  

    aqf = norm * (a * np.sqrt(w[0] * PV0 + w[1] * PV1) + (w[0] * PM0 + w[1] * PM1))  
    aqf = np.rot90(aqf, k=-1)[:, ::-1]  # 旋转采集函数以适应显示  

    # 创建或清空图形  
    if fig is None:  
        fig = plt.figure("图像", figsize=(12, 8), layout="constrained")  
    else:  
        fig.clear()  

    # 创建子图  
    ax = [  
        fig.add_subplot(331),  
        fig.add_subplot(332),  
        fig.add_subplot(333),  
        fig.add_subplot(334),  
        fig.add_subplot(335),  
        fig.add_subplot(336),  
        fig.add_subplot(337),  
        fig.add_subplot(338),  
        fig.add_subplot(339),  
    ]  

    ax = np.asarray(ax).reshape(3, 3)  

    # 调整子图间距  
    fig.subplots_adjust(wspace=0.4, hspace=0.6)  # 增加水平和垂直间距  

    # 动态调整字体大小  
    title_fontsize = 10  
    label_fontsize = 8  

    # 绘制后验均值和方差  
    for i, PM, PV in zip(range(2), [PM0, PM1], [sPV0, sPV1]):  
        PM = np.rot90(PM, k=-1)[:, ::-1]  
        PV = np.rot90(PV, k=-1)[:, ::-1]  
        pmmax = PM.max()  
        pvmax = PV.max()  
        PM /= pmmax  # 归一化后验均值  
        PV /= pvmax  # 归一化后验方差  

        # 绘制后验均值  
        ax[i, 0].imshow(  
            PM, clim=[0, 1], extent=[*lim_x, *lim_y], origin="lower", aspect="equal"  
        )  
        ax[i, 0].set_title(f"Posterior Mean (PM): {pmmax:.3f}", fontsize=title_fontsize)  
        ax[i, 0].set_xlabel("X-axis Label", fontsize=label_fontsize)  
        ax[i, 0].set_ylabel("Y-axis Label", fontsize=label_fontsize)  
        ax[i, 0].grid(True, linestyle="--", alpha=0.5)  

        # 绘制后验方差  
        ax[i, 1].imshow(  
            PV, clim=[0, 1], extent=[*lim_x, *lim_y], origin="lower", aspect="equal"  
        )  
        ax[i, 1].set_title(f"Posterior Variance (PV): {a * np.sqrt(pvmax):.3f}", fontsize=title_fontsize)  
        ax[i, 1].set_xlabel("X-axis Label", fontsize=label_fontsize)  
        ax[i, 1].set_ylabel("Y-axis Label", fontsize=label_fontsize)  
        ax[i, 1].grid(True, linestyle="--", alpha=0.5)  

        # 绘制数据点和上一个点  
        ax[i, 0].scatter(positions[:, 0], positions[:, 1], s=15, c="r", alpha=0.5)  
        ax[i, 1].scatter(positions[:, 0], positions[:, 1], s=15, c="r", alpha=0.5)  
        ax[i, 0].scatter(positions[-1, 0], positions[-1, 1], s=30, c="white")  
        ax[i, 1].scatter(positions[-1, 0], positions[-1, 1], s=30, c="white")  

    # 绘制位置散点图  
    ax[0, 2].imshow(  
        np.zeros_like(PM),  
        clim=[0, 1],  
        extent=[*lim_x, *lim_y],  
        origin="lower",  
        aspect="equal",  
    )  
    ax[0, 2].scatter(  
        pos[:, 0], pos[:, 1], s=25, c=val[:, 0], cmap="viridis", marker="o"  
    )  
    ax[1, 2].imshow(  
        np.zeros_like(PM),  
        clim=[0, 1],  
        extent=[*lim_x, *lim_y],  
        origin="lower",  
        aspect="equal",  
    )  
    ax[1, 2].scatter(  
        pos[:, 0], pos[:, 1], s=25, c=val[:, 1], cmap="viridis", marker="o"  
    )  
    ax[0, 2].scatter(pos[-1, 0], pos[-1, 1], s=25, c="r", marker="o")  
    ax[1, 2].scatter(pos[-1, 0], pos[-1, 1], s=25, c="r", marker="o")  

    # 绘制移动轨迹线  
    ax[0, 2].plot(pos[:, 0], pos[:, 1], c="w", alpha=0.5)  
    ax[1, 2].plot(pos[:, 0], pos[:, 1], c="w", alpha=0.5)  

    # 绘制采集函数  
    ax[2, 0].set_title(f"Acquisition Function (Max: {aqf.max():.2f})", fontsize=title_fontsize)  
    ax[2, 0].imshow(  
        aqf,  
        extent=[*lim_x, *lim_y],  
        origin="lower",  
        clim=np.quantile(aqf, (0.01, 0.99)),  
        aspect="equal",  
    )  
    ax[2, 0].set_xlabel("X-axis Label", fontsize=label_fontsize)  
    ax[2, 0].set_ylabel("Y-axis Label", fontsize=label_fontsize)  
    ax[2, 0].grid(True, linestyle="--", alpha=0.5)  

    # 绘制AQF变化  
    if old_aqf is not None:  
        diff = old_aqf - aqf  
        ax[2, 1].set_title("AQF Changes", fontsize=title_fontsize)  
        ax[2, 1].imshow(  
            diff, extent=[*lim_x, *lim_y], origin="lower", cmap="bwr", aspect="equal"  
        )  
        ax[2, 1].set_xlabel("X-axis Label", fontsize=label_fontsize)  
        ax[2, 1].set_ylabel("Y-axis Label", fontsize=label_fontsize)  
        ax[2, 1].grid(True, linestyle="--", alpha=0.5)  

    # 绘制上一次的光谱  
    if last_spectrum is not None:  
        ax[2, 2].imshow(  
            last_spectrum,  
            clim=np.quantile(last_spectrum, (0.02, 0.98)),  
            origin="lower",  
            cmap="terrain",  
            aspect="equal",  
        )  
        ax[2, 2].set_title("Last Spectrum", fontsize=title_fontsize)  
        ax[2, 2].set_xlabel("X-axis Label", fontsize=label_fontsize)  
        ax[2, 2].set_ylabel("Y-axis Label", fontsize=label_fontsize)  
        ax[2, 2].grid(True, linestyle="--", alpha=0.5)  

    plt.tight_layout()  # 自动调整子图参数  
    plt.pause(0.01)  # 暂停以更新图形  
    return fig, aqf  


if __name__ == "__main__":  
    pass