import numpy as np  


def acquisition_function_nd(  
    x: np.ndarray,  
    gp,  
    a: float,  
    weights: np.ndarray = None,  
    norm: float = 2.0,  
    c: float = 0.0,  
) -> float:  
    """  
    计算多任务高斯过程（GP）的采集函数值。  

    Args:  
        x (np.ndarray): 输入点，形状为 (n_samples, input_dim)。  
        gp (GaussianProcess): 高斯过程模型，需提供 posterior_mean 和 posterior_covariance 方法。  
        a (float): 探索与利用的权衡参数，值越大越倾向于探索。  
        weights (np.ndarray, optional): 各任务的权重，默认为等权重。  
        norm (float, optional): 归一化因子，默认为 2.0。  
        c (float, optional): 协方差的权衡参数，默认为 0.0。  

    Returns:  
        float: 采集函数值。  
    """  
    # 检查输入  
    if weights is None:  
        weights = np.ones(gp.output_number)  
    if len(weights) != gp.output_number:  
        raise ValueError("weights 的长度必须与 GP 的任务数量一致。")  

    # 初始化累积变量  
    total_mean, total_var, total_covar = 0.0, 0.0, 0.0  

    # 遍历每个任务  
    for i in range(gp.output_number):  
        # 构造预测点，添加任务索引  
        x_pred = np.c_[x, np.full(x.shape[0], i)].reshape(-1, gp.input_dim)  

        # 获取均值和方差  
        mean_i = gp.posterior_mean(x_pred)["f(x)"]  
        var_i = gp.posterior_covariance(x_pred, variance_only=(c == 0))["v(x)"]  

        # 累加均值和方差  
        total_mean += weights[i] * mean_i  
        total_var += weights[i] * var_i  

        # 如果 c 不为 0，计算协方差  
        if c != 0:  
            covar_i = gp.posterior_covariance(x_pred)["S(x)"][0]  
            total_covar += weights[i] * covar_i  

    # 计算采集函数值  
    acquisition_value = norm * (total_mean + a * np.sqrt(total_var) + c * total_covar)  
    return acquisition_value