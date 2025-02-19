import argparse
import asyncio
import logging
import shutil
import time
import traceback
from functools import partial
from pathlib import Path
import threading  # 导入threading模块

import matplotlib.pyplot as plt
import numpy as np
import yaml
from gpcam.gp_optimizer import fvGPOptimizer
from typing import Optional  #临时加入
from scipy.stats import qmc # 导入qmc模块

from . import TCP, gp, plot, sgm4commands, tasks, utils

# 定义初始点字典  
RELATIVE_INITIAL_POINTS = {  
    # 已有的二维布局  
    "center_2D": [[0.5, 0.5]],  
    "border_2D_8": [  
        [0, 0],  
        [0, 0.5],  
        [0, 1],  
        [0.5, 1],  
        [1, 1],  
        [1, 0.5],  
        [1, 0],  
        [0.5, 0],  
    ],  
    "border_2D_16": [  
        [0, 0],  
        [0, 0.25],  
        [0, 0.5],  
        [0, 0.75],  
        [0, 1],  
        [0.25, 1],  
        [0.5, 1],  
        [0.75, 1],  
        [1, 1],  
        [1, 0.75],  
        [1, 0.5],  
        [1, 0.25],  
        [1, 0],  
        [0.75, 0],  
        [0.5, 0],  
        [0.25, 0],  
    ],  
    "grid_2D_9": [  
        [0, 0],  
        [0, 0.5],  
        [0, 1],  
        [0.5, 1],  
        [1, 1],  
        [1, 0.5],  
        [1, 0],  
        [0.5, 0],  
        [0.5, 0.5],  
    ],  
    "grid_2D_25": [  
        [0, 0],  
        [0, 0.25],  
        [0, 0.5],  
        [0, 0.75],  
        [0, 1],  
        [0.25, 1],  
        [0.5, 1],  
        [0.75, 1],  
        [1, 1],  
        [1, 0.75],  
        [1, 0.5],  
        [1, 0.25],  
        [1, 0],  
        [0.75, 0],  
        [0.5, 0],  
        [0.25, 0],  
        [0.5, 0.5],  
        [0.5, 0.25],  
        [0.5, 0.75],  
        [0.25, 0.5],  
        [0.75, 0.5],  
        [0.25, 0.25],  
        [0.25, 0.75],  
        [0.75, 0.25],  
        [0.75, 0.75],  
    ],  
    "hexgrid_2D_13": [  
        [0, 0.5],  
        [0, 1],  
        [0.25, 0.75],  
        [0.25, 0.25],  
        [0.5, 0],  
        [0.5, 0.5],  
        [0.5, 1],  
        [0.75, 0.75],  
        [0.75, 0.25],  
        [1, 0],  
        [1, 0.5],  
        [1, 1],  
        [0, 0],  
    ],  
    "hexgrid_2D_19": [  
        [0, 0],  
        [0, 0.5],  
        [0, 1],  
        [0.25, 0.75],  
        [0.25, 0.25],  
        [0.5, 0],  
        [0.5, 0.5],  
        [0.5, 1],  
        [0.75, 0.75],  
        [0.75, 0.25],  
        [1, 0],  
        [1, 0.5],  
        [1, 1],  
        [0.25, 0.5],  
        [0.5, 0.25],  
        [0.5, 0.75],  
        [0.75, 0.5],  
        [0.5, 0.5],  
        [0.5, 0.5],  
    ],  

    # 已有的三维布局  
    "center_3D": [[0.5, 0.5, 0.5]],  
    "border_3D_25": [  
        [0, 0, 0],  
        [0, 0, 0.5],  
        [0, 0, 1],  
        [0, 0.5, 1],  
        [0, 1, 1],  
        [0, 1, 0.5],  
        [0, 1, 0],  
        [0, 0.5, 0],  
        [0.5, 0, 0],  
        [0.5, 0, 0.5],  
        [0.5, 0, 1],  
        [0.5, 0.5, 1],  
        [0.5, 1, 1],  
        [0.5, 1, 0.5],  
        [0.5, 1, 0],  
        [0.5, 0.5, 0],  
        [1, 0, 0],  
        [1, 0, 0.5],  
        [1, 0, 1],  
        [1, 0.5, 1],  
        [1, 1, 1],  
        [1, 1, 0.5],  
        [1, 1, 0],  
        [1, 0.5, 0],  
        [0.5, 0.5, 0.5],  
    ],  
    "grid_3D_27": [  
        [0, 0, 0],  
        [0, 0, 0.5],  
        [0, 0, 1],  
        [0, 0.5, 1],  
        [0, 1, 1],  
        [0, 1, 0.5],  
        [0, 1, 0],  
        [0, 0.5, 0],  
        [0.5, 0, 0],  
        [0.5, 0, 0.5],  
        [0.5, 0, 1],  
        [0.5, 0.5, 1],  
        [0.5, 1, 1],  
        [0.5, 1, 0.5],  
        [0.5, 1, 0],  
        [0.5, 0.5, 0],  
        [1, 0, 0],  
        [1, 0, 0.5],  
        [1, 0, 1],  
        [1, 0.5, 1],  
        [1, 1, 1],  
        [1, 1, 0.5],  
        [1, 1, 0],  
        [1, 0.5, 0],  
        [0.5, 0.5, 0.5],  
        [0.5, 0.5, 0.25],  
        [0.5, 0.5, 0.75],  
    ],  

    # 动态生成的点集（直接生成点集）  
    "random_2D_50": np.random.rand(50, 2).tolist(),  
    "latin_hypercube": qmc.LatinHypercube(d=2).random(n=50).tolist(),  
    "sobol": qmc.Sobol(d=2, scramble=False).random_base2(m=6).tolist(),  # 2^6 = 64 个点  
    "halton": qmc.Halton(d=2, scramble=False).random(n=50).tolist(),  
}  

# 获取初始点的函数  
def get_initial_points(point_type):  
    if point_type not in RELATIVE_INITIAL_POINTS:  
        raise ValueError(f"未知的初始点类型: {point_type}")  
    points = RELATIVE_INITIAL_POINTS[point_type]  
    return points() if callable(points) else points  

import threading  
import asyncio  
import logging  
import traceback  

def run(settings: dict) -> None:
    """Run the scan asynchronously.

    Args:
        settings (dict): A dictionary with the settings.
    """
    # init logger
    logger = logging.getLogger(__name__)
    # init scan manager
    scan_manager = SmartScan(settings=settings)
    # start scan manager
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(scan_manager.start())
    except KeyboardInterrupt:
        loop.run_forever()
        loop.run_until_complete(scan_manager.stop())
        logger.warning("Terminated scan from keyboard")
    except Exception as e:
        logger.critical(
            f"Scan manager stopped due to {type(e).__name__}: {e} {traceback.format_exc()}"
        )
        logger.exception(e)
        loop.run_until_complete(scan_manager.stop())

    logger.info("Scan manager stopped.")
    logger.info("Scan finished")

global_pause = False  
def pause_scan():
    global global_pause
    global_pause = True
def resume_scan():
    global global_pause
    global_pause = False



class SmartScan:
    """AsyncScanManager class.

    This class is responsible for managing the scan.
    It connects to the SGM4, fetches data, reduces it, trains the GP and asks for the next position.


    Args:
        settings (dict | str | Path): A dictionary with the settings or a path to a yaml file with
            the settings.

    Attributes:
        gp (fvGPOptimizer): The GP object.
        hyperparameter_history (dict): A dictionary with the hyperparameters history.
        last_asked_position (np.ndarray): The last position provided by the GP.
        last_spectrum (np.ndarray): The last spectrum.
        logger (logging.Logger): A logger object.
        positions (list): A list of positions.
        remote (SGM4Commands): An object to communicate with the SGM4.
        settings (dict): A dictionary with the settings.
        task_labels (list): A list of task labels.
        values (list): A list of values.

    Properties:
        errors (np.ndarray): The errors associated with the values.
        filename (Path): The file stem.
        n_dim (int): The number of dimensions.
        n_positions (int): The number of unique points.
        n_spectra (int): The number of spectra.
        n_tasks (int): The number of tasks.
        positions (np.ndarray): The positions.
        task_weights (np.ndarray): The task weights.
        values (np.ndarray): The values.

    Flags:
        _has_new_data (bool): A flag to indicate new data.
        _ready_for_gp (bool): A flag to indicate that the GP can be trained.
        _should_replot (bool): A flag to replot the data.
        _should_stop (bool): A flag to stop the scan.
    """

    def __init__(
        self,
        settings: str | Path | dict = None,
    ) -> None:
        """
        Initialize the AsyncScanManager object.

        Args:
            settings (dict | str | Path): A dictionary with the settings or a path to a yaml file with
            the settings.
        """
        # load settings
        if isinstance(settings, str | Path):
            self.settings_file = settings
            with open(settings) as f:
                self.settings = yaml.load(f, Loader=yaml.FullLoader)
        elif isinstance(settings, dict):
            self.settings = settings.copy()
            self.settings_file = None
        else:
            raise ValueError("Settings must be a path to a yaml file or a dict.")

        self.logger = logging.getLogger("SmartScan")
        self.logger.info("Initialized AsyncScanManager.")

        self.task_labels: list[str] = list(self.settings["tasks"].keys())

        # connect to SGM4
        self.remote = sgm4commands.SGM4Commands(
            self.settings["TCP"]["host"],
            self.settings["TCP"]["port"],
            buffer_size=self.settings["TCP"]["buffer_size"],
        )

        # init data containers
        self._all_spectra_dict = {}  # dict of lists of spectra
        self._mean_spectra_dict = {}  # dict of mean of spectra per position
        self._task_dict = {}  # dict of tasks per position

        self._all_positions: list = []  # list of positions as measured
        self._all_spectra: list = []  # list of spectra as measured
        self._all_tasks: list = []  # list of tasks as measured

        self.hyperparameter_history = {}  # dict of hyperparameters history

        self.last_spectrum = None  # last spectrum as measured
        self.last_asked_position = None  # last position provided by the GP
        self.task_weights = None  # will be set by get_taks_normalization_weights

        # init flags
        self._paused: bool = False  # flag to pause the scan
        self._should_stop: bool = False  # flag to stop the scan
        self._ready_for_gp: bool = False  # flag to indicate that the GP can be trained
        self._has_new_data: bool = False  # flag to indicate new data
        self._should_replot: bool = False  # flag to replot the data

        # init GP
        self.gp = None  # the GP object

        # properties
        self._n_dim = None
        self.relative_initial_points = RELATIVE_INITIAL_POINTS[
            self.settings["scanning"]["initial_points"]
        ]

    @property
    def filename(self) -> Path:
        """Get the file stem."""
        filename: Path = Path(self.remote.filename)
        folder: Path = filename.parent
        if not filename.exists():
            if not folder.exists():
                raise FileNotFoundError(f"Folder {folder} does not exist.")
        self.logger.debug(f"Saving settings to {folder}.")
        return filename

    @property
    def n_positions(self) -> int:
        """Get the number of unique points."""
        return len(self.positions)

    @property
    def n_spectra(self) -> int:
        """Get the number of spectra."""
        each = [len(d) for d in self._all_spectra_dict.values()]
        return sum(each)

    @property
    def n_tasks(self) -> int:
        """Get the number of tasks."""
        return len(self.task_labels)

    @property
    def n_dim(self) -> int:
        """Get the number of dimensions."""
        if self._n_dim is None:
            self._n_dim = len(self.remote.axes)
        return self._n_dim

    @property
    def positions(self) -> np.ndarray:
        """Get the positions."""
        if self.settings["scanning"]["merge_unique_positions"]:
            return np.array([np.array(p) for p in self._mean_spectra_dict.keys()])
        else:
            return np.array(self._all_positions, dtype=float)

    @property
    def task_values(self) -> np.ndarray:
        """Get the values."""
        if self.settings["scanning"]["merge_unique_positions"]:
            return np.array(list(self._task_dict.values()))
        else:
            return np.array(self._all_tasks, dtype=float)

    @property
    def errors(self) -> np.ndarray:
        """Get the errors."""
        if self.settings["scanning"]["merge_unique_positions"]:
            base_error = self.settings["scanning"]["base_error"]
            return np.array(
                [
                    [base_error / np.sqrt(len(d))] * len(self.task_labels)
                    for d in self._all_spectra_dict.values()
                ],
                dtype=float,
            )
        else:
            return np.ones((len(self.task_labels), len(self._all_spectra)), dtype=float)

    async def fetch_and_reduce_loop(self) -> None:  
        """Fetch data from SGM4 and reduce it."""  
        self.logger.info("Starting fetch data loop.")  
        await asyncio.sleep(1)  # wait a bit before starting  
        while not self._should_stop:  
            if global_pause==True:  # 检查是否暂停  
                await asyncio.sleep(1)  # 暂停时等待  
                continue  
        
            self.logger.debug("Fetching data...")  
            pos, data = await self._fetch_data()  
            if data is not None:  
                self.logger.info(f"Data received: {data.shape}")  
                t0 = time.time()  
                if self.settings["scanning"]["merge_unique_positions"]:  
                    p = tuple(pos)  
                    if p in self._all_spectra_dict.keys():  
                        self._all_spectra_dict[p].append(data)  
                        self._mean_spectra_dict[p] = np.mean(  
                            np.array(self._all_spectra_dict[p]), axis=0  
                        )  
                        self.logger.debug(  
                            f"Pos {pos} has {len(self._all_spectra_dict[p])} spectra."  
                        )  
                    else:  
                        self._all_spectra_dict[p] = [data]  
                        self._mean_spectra_dict[p] = data  
                    self._task_dict[p] = self._reduce(pos, self._mean_spectra_dict[p])  
                    self.logger.info(  
                        f"Updated data: {p}: tasks {self._task_dict[p]} | {len(self._all_spectra_dict[p])} spectra | time: {time.time()-t0:.3f} s"  
                    )  
                else:  
                    self._all_positions.append(pos)  
                    self._all_spectra.append(data)  
                    self._all_tasks.append(self._reduce(pos, data))  
                self.last_spectrum = data  
                self._has_new_data = True  
            else:  
                self.logger.debug("No data received.")  
                await asyncio.sleep(0.2)

    # get data from SGM4
    async def _fetch_data(
        self,
    ) -> tuple[str, None] | tuple[np.ndarray, np.ndarray] | None:
        """Get data from SGM4.

        Returns:
            tuple[str, None] | tuple[np.ndarray, np.ndarray] | None:
                - tuple[str, None] if there was an error
                - tuple[np.ndarray, np.ndarray] if there was no error
                - None if no data was received
        """
        self.logger.debug("Fetching data...")
        message: str = TCP.send_tcp_message(
            host=self.settings["TCP"]["host"],
            port=self.settings["TCP"]["port"],
            msg="MEASURE",
            buffer_size=self.settings["TCP"]["buffer_size"],
            logger=self.logger,
        )
        msg: list[str] = message.strip("\r\n").split(" ")
        msg_code: str = msg[0]
        vals: list[str] = [v for v in msg[1:] if len(v) > 0]
        self.logger.debug(f"MEASURE answer: {msg_code}: {len(message)/1024:,.1f} kB")
        match msg_code:
            case "ERROR":
                self.logger.error(message)
                return message, None
            case "NO_DATA":
                self.logger.debug(f"No data received: {message}")
                return message, None
            case "MEASURE":
                try:
                    n_pos = int(vals[0])
                    pos: np.ndarray = np.asarray(vals[1 : n_pos + 1], dtype=float)
                    data: np.ndarray = np.asarray(vals[n_pos + 1 :], dtype=float)
                    data = data.reshape(self.remote.spectrum_shape)
                    return pos, data
                except ValueError as e:
                    self.logger.critical(
                        f"Failed interpreting received data with shape {data.shape}: {e} "
                    )
            case _:
                self.logger.warning(f"Unknown message code: {msg_code}")
                return message, None

    def _reduce(self, pos: np.ndarray, data: np.ndarray) -> np.ndarray:
        """reduce a single spectrum to tasks"""
        self.logger.debug(f"Reducing data for pos {pos}...")
        t0 = time.time()
        reduced = []
        for _, d in self.settings["tasks"].items():
            func = getattr(tasks, d["function"])
            kwargs = d.get("params", {})
            if kwargs is None:
                reduced.append(func(data))
            else:
                reduced.append(func(data, **kwargs))
        reduced = np.asarray(reduced, dtype=float).flatten()
        if len(reduced) != len(self.task_labels):
            raise RuntimeError(
                f"Length mismatch between tasks {len(reduced)}"
                f"and task labels {len(self.task_labels)}."
            )
        self.logger.debug(f"Reduction {pos} | {reduced} | time: {time.time()-t0:.3f} s")
        return reduced

    def get_taks_normalization_weights(self, update=False) -> np.ndarray:
        """Get the weights to normalize the tasks.

        Returns:
            np.ndarray: An array with the weights.
        """
        if self.settings["scanning"]["normalize_values"] == "fixed":
            self.task_weights = 1 / np.array(
                self.settings["scanning"]["fixed_normalization"]
            )
            self.logger.debug(f"Fixed Task weights: {self.task_weights}")
        elif self.task_weights is None or update:
            self.task_weights = 1 / self.task_values.mean(axis=0)
            self.logger.debug(f"Updated Task weights: {self.task_weights}")
        return self.task_weights

    def tell_gp(self, update_normalization: bool = False) -> None:
        """Tell the GP about the current available data.

        This method is called every time new data is added to the data queue.
        If scanning/normalize_values is not false, values are normalized.
            - 'init': values are normalized by the mean of the first batch of data
            - 'fixed': values are normalized by the value of scanning/fixed_normalization
            - 'dynamic': values are normalized by the mean of all the current data
        """
        self.logger.debug("Telling GP about new data.")
        if self.gp is not None:
            pos = np.asarray(self.positions)
            vals = np.asarray(self.task_values)
            if self.settings["scanning"]["normalize_values"] == "always":
                vals = vals * self.get_taks_normalization_weights(update=True)
            elif self.settings["scanning"]["normalize_values"] != "never":
                vals = vals * self.get_taks_normalization_weights(
                    update=update_normalization
                )
            self.logger.info(f"TELL GP | pos: {pos[-1]} | tasks: {vals[-1]}")
            self.gp.tell(pos, vals, variances=self.errors)
            self._has_new_data = False

    # GP loop
    def init_gp(self) -> None:
        """Initialize the GP.

        This method is called at the first iteration of the GP loop.
        """
        self.logger.debug("Starting GP initialization.")
        isd = len(self.remote.axes)
        osd = 1
        on = len(self.task_labels)
        self.gp = fvGPOptimizer(
            input_space_bounds=self.remote.limits,
            input_space_dimension=isd,
            output_space_dimension=osd,
            output_number=on,
        )
        self.logger.debug(
            f"GP object created. Input Space Dimension () = {isd} | "
            f"Output Space Dimension () = {osd} | "
            f"Output Number () = {on}"
        )
        self.tell_gp()
        self.logger.info(f"Initialized GP with {len(self.positions)} samples.")
        fvgp_pars = self.settings["gp"]["fvgp"].copy()
        init_hyperparameters = np.array(
            [float(n) for n in fvgp_pars.pop("init_hyperparameters")]
        )
        if len(init_hyperparameters) != isd + 2:
            raise ValueError(
                f"Length mismatch between init_hyperparameters ({len(init_hyperparameters)})"
                f"and input_space_dimension ({isd})."
            )
        self.logger.debug("Initializing GP:")
        self.logger.debug(f"\tinit_hyperparameters: {init_hyperparameters}")
        for k, v in fvgp_pars.items():
            self.logger.debug(f"\t{k} = {v}")
        self.gp.init_fvgp(init_hyperparameters=init_hyperparameters, **fvgp_pars)

        self.train_gp()

        cost_function_dict = self.settings.get("cost_function", None)
        if cost_function_dict is not None:
            self.logger.debug(
                "Initializing cost function: cost_function_dict['function']"
            )

            cost_func_callable = getattr(
                gp.cost_functions, cost_function_dict["function"]
            )
            cost_func_params = cost_function_dict.get("params", {})
            for k, v in cost_func_params.items():
                self.logger.debug(f"\t{k} = {v}")
            self.gp.init_cost(
                cost_func_callable,
                cost_function_parameters=cost_func_params.copy(),
            )

    def should_train(self) -> bool:
        if self.iter_counter in self.settings["scanning"]["train_at"]:
            return True
        if self.settings["scanning"]["train_every"] > 0:
            if self.iter_counter % self.settings["scanning"]["train_every"] == 0:
                return True
        return False

    def was_already_measured(self, pos: np.ndarray) -> bool:
        """check if the given position is in the positions list."""
        if len(self.positions) == 0:
            return False
        return np.any(np.all(np.isclose(self.positions, pos), axis=1))

    def train_gp(self) -> None:
        """Train the GP."""
        hps_old = self.gp.hyperparameters.copy()
        train_pars = self.settings["gp"]["training"].copy()
        hps_bounds = np.asarray(train_pars.pop("hyperparameter_bounds"))
        if len(hps_bounds) != len(hps_old):
            raise ValueError(
                f"Length mismatch between hyperparameter_bounds ({len(hps_bounds)})"
                f"and hyperparameters ({len(hps_old)})."
            )
        if "bounds" not in self.hyperparameter_history.keys():
            self.hyperparameter_history["bounds"] = hps_bounds.tolist()
        self.logger.info("Training GP:")
        self.logger.info(
            f"\titeration {self.iter_counter} | {len(self.positions)} samples"
        )
        self.logger.debug(f"\thyperparameter_bounds: {hps_bounds}")
        for k, v in train_pars.items():
            self.logger.debug(f"\t{k} = {v}")
        self.tell_gp(update_normalization=True)
        t = time.time()
        hps_new = self.gp.train_gp(hyperparameter_bounds=hps_bounds, **train_pars)
        if not all(hps_new == self.gp.hyperparameters):
            self.logger.warning(
                "Something wrong with training, hyperparameters not updated?"
            )
        self.logger.info(
            f"Training complete in {utils.pretty_print_time(time.time()-t)} s"
        )
        self.logger.info("Hyperparameters: ")
        for old, new, bounds in zip(hps_old, hps_new, hps_bounds):
            change = (new - old) / old
            message = f"\t{old:.2f} -> {new:.2f} ({change:.2%}) | {bounds}"
            if new in bounds:
                self.logger.warning(f"{message} Hit boundaries!!")
            else:
                self.logger.info(message)
        self.hyperparameter_history[f"training{self.iter_counter:04.0f}"] = {
            "hyperparameters": [float(f) for f in self.gp.hyperparameters],
            "time": time.time() - t,
            "iteration": self.iter_counter,
            "samples": len(self.positions),
        }
        self.save_hyperparameters()

    def ask_gp(self) -> None:
        """Ask the GP for the next position."""
        acq_func_callable = getattr(
            gp.aquisition_functions,
            self.settings["acquisition_function"]["function"],
        )
        acq_func_params = self.settings["acquisition_function"]["params"]
        aqf = partial(acq_func_callable, **acq_func_params)

        ask_pars = self.settings["gp"]["ask"]

        if self.gp.cost_function_parameters is not None:
            self.gp.cost_function_parameters.update(
                {
                    "prev_points": self.gp.x_data,
                    "n_dim": self.n_dim,
                    "n_tasks": self.n_tasks,
                    "axes": self.remote.axes,
                }
            )

        if self.last_asked_position is None:
            self.last_asked_position = self.positions[-1]

        self.logger.debug(f"ASK: Last asked position: {self.last_asked_position}")
        next_pos = self.gp.ask(
            position=np.array(self.last_asked_position),
            acquisition_function=aqf,
            **ask_pars,
        )["x"]
        for point in next_pos:
            rounded_point = utils.closest_point_on_grid(point, axes=self.remote.axes)
            self.logger.info(
                f"ASK GP          | Adding {rounded_point} to scan. rounded from {point}"
            )
            if any([all(rounded_point == prev) for prev in self.positions]):
                self.logger.warning(
                    f"ASK GP          | Point {rounded_point} already evaluated!"
                )
            self.remote.ADD_POINT(*rounded_point)
            self.last_asked_position = rounded_point
        return True

    async def gp_loop(self) -> None:  
        """GP loop.  

        This loop is responsible for training the GP and asking for the next position.  
        """  
        self.iter_counter = 0  
        self.logger.info("Starting GP loop.")  
        await asyncio.sleep(1)  # wait a bit before starting  
    
        # 等待数据准备  
        while self.relative_initial_points is not None:  
            if self.n_positions > len(self.relative_initial_points):  
                self.logger.info(f"Enough positions {self.n_positions} to start GP.")  
                break  
            elif all(  
                [self.was_already_measured(p) for p in self.relative_initial_points]  
            ):  
                self.logger.info(  
                    "All initial points already measured. Ready to start GP."  
                )  
                break  
            elif self.n_spectra > 1.2 * len(self.relative_initial_points):  
                self.logger.info(f"Enough spectra ({self.n_spectra}) to start GP.")  
                break  
            else:  
                self.logger.debug(  
                    f"Waiting for data to be ready for GP. {len(self.positions)}/{len(self.relative_initial_points)} "  
                )  
                await asyncio.sleep(0.5)  

        self.logger.info("Data ready for GP. Starting GP loop.")  
    
        while not self._should_stop:  
            if global_pause==True:  # 检查是否暂停  
                await asyncio.sleep(1)  # 暂停时等待  
                continue  
        
            self.logger.debug("GP looping...")  
            if self.iter_counter >= self.settings["scanning"]["max_points"]:  
                self.logger.warning(  
                    f"Max number of iterations of {self.settings['scanning']['max_points']}"  
                f" reached. Ending scan. It lasted {time.time()-self.start_time:.0f} s"  
                )  
                self._should_stop = True  
                break  
        
            if self._has_new_data:  
                self.iter_counter += 1  
                self.logger.info(  
                    f"GP iter: {self.iter_counter:3.0f}/{self.settings['scanning']['max_points']:4.0f} | {self.n_positions} samples | {self.n_spectra} spectra"  
                )  
                if self.gp is None:  
                    self.init_gp()  # initialize GP at first iteration  
                else:  
                    self.tell_gp()  
                    if self.should_train():  
                        self.train_gp()  
                    success = self.ask_gp()  
                    if not success:  
                        break  
                    self._should_replot = True  
            else:  
                self.logger.debug("No data to update.")  
                await asyncio.sleep(0.2)  

        self.remote.END()

    # plotting loop
    async def plotting_loop(self) -> None:  
        """Plotting loop.  

        This loop is responsible for plotting the data.  
        """  
        self.logger.info("Starting plotting loop.")  
        await asyncio.sleep(1)  # wait a bit before starting  
        self.logger.info("Starting plotting tool loop")  
        self.fig = None  
        aqf = None  
    
        while not self._should_stop:  
            if global_pause==True:  # 检查是否暂停  
                await asyncio.sleep(1)  # 暂停时等待  
                continue  
        
            if self._should_replot and self.n_dim == 2:  
                self._should_replot = False  
                self.logger.debug("Plotting...")  
                fig, aqf = plot.plot_aqf_panel(  
                    gp=self.gp,  
                    fig=self.fig,  
                    pos=np.asarray(self.positions),  
                    val=np.asarray(self.task_values),  
                    old_aqf=aqf,  
                    last_spectrum=self.last_spectrum,  
                    settings=self.settings,  
                )  
                self.fig = fig  
                plt.pause(0.01)  
            else:  
                await asyncio.sleep(0.2)  
                # if fig is not None and self.iter_counter % self.settings['plot']['save_every'] == 0:  
                #     fig.savefig(f'../results/{self.remote.filename.with_suffix("pdf").name}')

    async def killer_loop(self, duration=None) -> None:  
        self.logger.info(  
            f"Starting killer loop. Will kill process after {duration} seconds."  
        )  
        self.start_time = time.time()  

        if duration is None:  
            duration = self.settings["scanning"]["duration"]  
            end_time = self.start_time + duration  
            end_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time))  
            self.logger.warning(  
                f"Scan will end in {duration} seconds. At {end_time_str}"  
            )  
        
        if duration is not None:  
            time_left = duration  
            while not self._should_stop:  
                if global_pause==True:  # 检查是否暂停  
                    await asyncio.sleep(1)  # 暂停时等待  
                    continue  
            
                time_left -= 1  
                if time_left <= 0 or time.time() > self.start_time + duration:  
                    break  
                await asyncio.sleep(1)  

            self.logger.info(  
                f"Killer loop strikes! Scan interrupted after {duration} seconds."  
            )  
            await self.stop()  # 确保调用 stop 是异步的
    async def new_plotting_loop(self) -> None:  
        """Plotting loop. Refreshing the figure."""  
        self.logger.info("Starting plotting loop.")  
        await asyncio.sleep(1)  
        self.logger.info("Starting plotting tool loop")  
        plotter = plot.Plotter(self.settings)  
    
        while not self._should_stop:  
            if global_pause==True:  # 检查是否暂停  
                await asyncio.sleep(1)  # 暂停时等待  
                continue  
        
            if self._should_replot and self.n_dim == 2:  
                self._should_replot = False  
                self.logger.debug("Plotting...")  
                plotter.update(  
                    gp=self.gp,  
                    positions=np.asarray(self.positions),  
                    values=np.asarray(self.task_values),  
                    last_spectrum=self.last_spectrum,  
                )  
            else:  
                plt.pause(0.01)  
                await asyncio.sleep(0.2)
    # all loops and initialization
    async def all_loops(self) -> None:  
        """  
        Start all the loops.  
        """  
        self.logger.info("Starting all loops.")  
        tasks = (  
            self.killer_loop(),  
            self.fetch_and_reduce_loop(),  
            self.gp_loop(),  
            self.plotting_loop(),  
        )  
        try:  
            await asyncio.gather(*tasks)  
        except KeyboardInterrupt:  
            self.logger.warning("KeyboardInterrupt. Stopping all loops.")  
            for t in tasks:  
                try:  
                    t.cancel()  
                except Exception:  # noqa  
                    pass  
        except Exception as e:  
            self.logger.critical(f"{type(e).__name__} stopping all loops.")  
            error_traceback = "".join(traceback.format_tb(e.__traceback__))  
            self.logger.error(f"Traceback: {error_traceback}")  
            self.logger.error(f"{type(e).__name__}: {e}")  
        finally:  
            self.logger.info("Finalizing loop gathering: All loops finished.")  
            await self.stop()  # 确保调用 stop 是异步的

    async def start(self) -> None:
        """Initialize scan and start all loops."""
        self.init_scan()

        self._ready_for_gp = False
        self._should_stop = False
        self._paused = False

        await self.all_loops()

    def connect(self) -> None:
        self.remote.connect()
        if len(self.remote.axes[0]) == 0:
            raise ValueError("failed initializing axes!!")
        else:
            self.logger.info(
                f"Axes: {[a.shape for a in self.remote.axes]} | Limits: {self.remote.limits} | Step size: {self.remote.step_size} "
            )

    def init_scan(self) -> None:
        """Initialize the scan."""
        self.logger.info("Initializing scan.")
        # TODO: add this to settings and give more options
        try:
            self.remote.START()
        except AssertionError as e:
            self.logger.error(f"Assertion error when STARTing the scan: {e}")
            self.remote.END()
            time.sleep(10)
            self.remote.START()
        while True:
            try:
                s = self.remote.STATUS()
                break
            except Exception as e:
                self.logger.error(f"Error setting up scan: {e}")
                self.logger.info("Trying again in 1 second...")
                time.sleep(1)
        self.logger.info(f"Scan initialized. Status: {s}")
        if status := self.remote.STATUS() != "READY":
            raise RuntimeError(f"Scan not ready. Status: {status}")
        self.connect()
        self.save_log_to_file()
        self.save_settings()

        if self.relative_initial_points is not None:
            self.logger.info(
                f"Adding {len(self.relative_initial_points)} points to scan."
            )
            for pos in self.relative_initial_points:
                if len(pos) != self.n_dim:
                    raise ValueError(
                        f"Length mismatch between initial points ({len(pos)})"
                        f"and dimensions ({self.n_dim})."
                    )
                for i in range(self.n_dim):
                    pos[i] = (
                        pos[i] * self.remote.limits[i][1]
                        + (1 - pos[i]) * self.remote.limits[i][0]
                    )

                self.remote.ADD_POINT(*pos)
                self.last_asked_position = pos
                self.logger.debug(f"Added point {pos} to scan.")

    def pause(self) -> None:  
        """暂停扫描"""  
        global global_pause  
        global_pause = True  
        logging.info("Global scan paused.")  

    def resume(self) -> None:  
        """恢复扫描"""  
        global global_pause  
        global_pause = False 
        logging.info("Global scan paused.")  

    def stop(self) -> None:
        self.logger.info("Stopping all loops.")
        self.kill()

    async def interrupt(self) -> None:
        """Interrupt the scan."""
        self.logger.info("Interrupting scan.")
        self.kill()
        await asyncio.sleep(1)

    def kill(self) -> None:
        self.logger.info("Killing all loops.")
        self._should_stop = True

    def finalize(self) -> None:
        self.logger.info("Finalizing scan.")
        self.logger.info("Saving figure...")
        self.save_figure()
        self.logger.info("Saving hyperparameters...")
        self.save_hyperparameters()
        self.logger.info("Scan finalized.")

    def save_figure(self) -> None:
        try:
            self.fig.savefig(self.filename.with_suffix(".pdf"))
            self.logger.info(f"Saved figure to {self.filename.with_suffix('.pdf')}")
            plt.close(self.fig)
        except Exception as e:
            self.logger.error(f"{type(e)} saving figure: {e}")

    def save_hyperparameters(self) -> None:
        try:
            target = self.filename.parent / (self.filename.stem + "_hps.yaml")
            with open(target, "w") as f:
                yaml.dump(self.hyperparameter_history, f)
            self.logger.info(f"Saved hyperparameters to {target}")
        except Exception as e:
            self.logger.error(f"{type(e)} saving hyperparameters: {e}")

    def save_settings(self) -> Path:
        """Save the settings in the data directory next to the acquired data.

        Args:
            filename (Path | str, optional): _description_. Defaults to "settings.json".
            folder (Path | str, optional): _description_. Defaults to "./".

        Raises:
            NotImplementedError: _description_

        Returns:
            Path: _description_
        """
        target = self.filename.parent / (self.filename.stem + "_settings.yaml")
        # i = 0
        if not target.exists():
            if self.settings_file is None:
                with open(target, "w") as f:
                    yaml.dump(self.settings, f)
                self.logger.info(f"Settings saved to {target}")
            else:
                shutil.copy(self.settings_file, target)
                self.logger.info(f"Settings copied to {target}")
        else:
            self.logger.critical(f"FAILED TO SAVE SETTINGS TO {target}. File exists!!")

    def save_log_to_file(self) -> logging.Logger:
        """Setup the logger."""
        logging_filename = self.filename.with_suffix(".log")
        self.logger.info(f"Saving INFO log to {logging_filename}")
        fh = logging.FileHandler(logging_filename)
        fh.setLevel("DEBUG")
        formatter = logging.Formatter(self.settings["logging"]["formatter"])
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        self.logger.info(f"Logging to file: {logging_filename}.")

    def __del__(self) -> None:
        self.logger.critical("Deleted instance. scan stopping")
        try:
            self.finalize()
        except Exception as e:
            self.logger.warn(
                f"{type(e).__name__} while deleting asyncscanner instance: {e}"
            )

 

def main(run_func: Optional[callable] = None) -> None:  
    """ Main function to run the smart scan.
    
    Args:
        run_func (callable | None): A callable function to run. Defaults to None.
            This function should take a dictionary with the settings as input.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--config", default="config.yaml", help="select a configuration file"
    )
    parser.add_argument(
        "-l",
        "--log",
        default=None,
        help="set the logging level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )

    args = parser.parse_args()

    with open(args.config) as f:
        settings = yaml.load(f, Loader=yaml.FullLoader)
    log_level = args.log or settings["logging"]["level"]
    log_level = log_level.upper()
    logging.root.setLevel(log_level)
    formatter = utils.ColoredFormatter(settings["logging"]["formatter"])

    sh = logging.StreamHandler()
    sh.setLevel(log_level)
    sh.setFormatter(formatter)
    logging.root.addHandler(sh)

    logger = logging.getLogger(__name__)

    logger.info(f"Starting scan with settings from {args.config}")

    # suppress user warnings
    import warnings

    warnings.simplefilter("ignore", UserWarning)

    # numpy compact printing
    np.set_printoptions(precision=3, suppress=True)


    if run_func is not None:
        run_func(settings)
    else:
       run(settings)

    asyncio.get_event_loop().stop()
    logger.info("Closed event loop")

def listen_for_commands(self):  
        """监听用户输入的命令"""  
        while True:  
            command = input("输入 'pause' 暂停，'resume' 恢复，'exit' 退出: ")  
            if command == 'pause':  
                pause_scan() 
            elif command == 'resume':  
                resume_scan() 
            elif command == 'exit':  
                asyncio.run(self.stop())  
                break  
            else:  
                print("无效命令，请输入 'pause'、'resume' 或 'exit'。") 


if __name__ == "__main__":
    main()
    listen_for_commands() 




