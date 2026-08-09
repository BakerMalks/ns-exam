import time
import pathlib
import csv
import concurrent.futures
import logging
import json

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from typing import Any, Callable, Dict, List, Literal, Optional, Tuple, Type, TypeVar, Union
from dataclasses import dataclass, field

T = TypeVar("T")
R = TypeVar("R", bound="SamplerResult")  # the concrete SamplerResult subclass a sample was collected into
MAX_SAMPLEING_FREQUENCY = 0.001
PlotKind = Literal["line", "scatter", "hist"]
DEFAULT_FIGURE_SIZE = [8, 5]
DEFAULT_PLOT_KIND: PlotKind = "scatter"


def _json_default(value: Any) -> Any:
    """Fallback encoder for values `json` cant serialize on its own.
    """
    if isinstance(value, np.generic):
        return value.item()
    return str(value)


@dataclass
class SamplerResult:
    samples: Dict[float, Any] = field(default_factory=dict)
    initiate_sample_timer: bool = True
    sample_name: str = ""
    _init_time: float = 0.0

    def __post_init__(self):
        if self.initiate_sample_timer:
            self.start_timer()
    
    def start_timer(self):
        if self._init_time > 0:
            # Choose if a raise error should be used (probbly a good idea as this is for developing help)
            logging.error("Result sampler timer was already initiated")
        else:
            self._init_time = time.perf_counter()
    
    def add_sample(self, value):
        self.samples[time.perf_counter() - self._init_time] = value
    
    def get_summary(self, print_log: bool = True, add_sample_type: bool = True, split_literal: str = "", *args, **kwargs) -> str:
        """Returns a string thet sums up the results of the sample

        Args:
            print_log (bool, optional): Log the summary. Defaults to True.
            add_sample_type (bool, optional): Should log the type value of the sample (int / str / ...). Defaults to True.
            split_literal (str, optional): the split between the summary lines. Defaults "" will mean '\n - '.

        Returns:
            str: the summary as human readable text
        """
        summary_list = [self._get_summary_header()]
        summary_list.extend(
            f"{self._get_summary_label(key)}: {self._format_summary_value(value)}"
            for key, value in self._get_summary_body(add_sample_type).items()
        )
        split_literal = split_literal if split_literal else '\n - '
        summary = split_literal.join(summary_list)
        if print_log:
            logging.info(summary)
        return summary

    def get_summary_json(self, print_log: bool = False, add_sample_type: bool = True, indent: Optional[int] = 2, *args, **kwargs) -> str:
        """Same summary content as `get_summary`, serialized as JSON.

        Args:
            print_log (bool, optional): Log the summary. Defaults to False.
            add_sample_type (bool, optional): Should include the type value of the sample (int / str / ...). Defaults to True.
            indent (Optional[int], optional): `json.dumps` indent. Pass None for a single line. Defaults to 2.

        Returns:
            str: the summary as a JSON object
        """
        summary = json.dumps(self.get_summary_dict(add_sample_type), indent=indent, default=_json_default)
        if print_log:
            logging.info(summary)
        return summary

    def get_summary_dict(self, add_sample_type: bool = True, *args, **kwargs) -> Dict[str, Any]:
        """The summary as structured data. Single source of truth for both summary formats.

        Keys are machine friendly (snake_case), `get_summary` turns them into display
        labels via `_get_summary_label`.
        """
        return {"sample_name": self.sample_name, **self._get_summary_body(add_sample_type)}

    def _get_summary_body(self, add_sample_type: bool = True) -> Dict[str, Any]:
        """Metric key -> value. Subclasses extend this to add their own metrics."""
        body: Dict[str, Any] = {"sample_count": self.sample_count}
        if add_sample_type:
            body["sample_types"] = sorted(set(str(type(value)) for value in self.samples.values()))
        return body

    def _get_summary_header(self) -> str:
            return f"""Sample {self.sample_name + " " if self.sample_name else ""}Results:"""

    @staticmethod
    def _get_summary_label(key: str) -> str:
        """Display label for a summary key. `sample_count` -> `Sample count`."""
        return key.replace("_", " ").capitalize()

    @staticmethod
    def _format_summary_value(value: Any) -> str:
        """Renders one summary value for the text format."""
        if isinstance(value, (list, tuple, set)):
            return ", ".join(str(item) for item in value)
        return str(value)

    @property
    def sample_count(self) -> int:
        return len(self.samples)
    
    def get_csv(self, sample_colume_name: str = "", *args, **kwargs) -> str:
        return self.get_data_frame(sample_name=sample_colume_name).to_csv()

    def get_data_frame(self, sample_name: str = "", *args, **kwargs) -> pd.DataFrame:
        sample_name = sample_name if sample_name else (self.sample_name if self.sample_name else "Sample")
        df = pd.DataFrame(
            {
                "Index[#]": list(range(1, self.sample_count + 1)),
                "Time[s]": list(self.samples.keys()),
                sample_name: list(self.samples.values())
            }
        )
        return df


@dataclass
class NumericSamplerResult(SamplerResult):
    samples: Dict[float, float] = field(default_factory=dict)

    def max(self) -> float:
        return max(self.samples.values())

    def min(self) -> float:
        return min(self.samples.values())

    def mean(self) -> float:
        return sum(self.samples.values()) / self.sample_count

    def median(self) -> float:
        l = list(self.samples.values())
        l.sort()
        return l[self.sample_count // 2]

    def std(self, ddof: float = 0) -> float:
        """Standard deviation 

        Args:
            ddof (float, optional): Means Delta Degrees of Freedom. The divisor used in calculations is N - ddof, where N represents the number of elements. Defaults to 0.

        Returns:
            float: standard deviation
        """
        return np.std(list(self.samples.values()), ddof=ddof)
   
    def _get_summary_body(self, add_sample_type: bool = True) -> Dict[str, Any]:
        body = super()._get_summary_body(add_sample_type)
        body["max"] = self.max()
        body["min"] = self.min()
        body["mean"] = self.mean()
        body["median"] = self.median()
        body["std_ddof0"] = self.std()
        return body
        

@dataclass
class Sampler:
    measurements_count: int = -1  # -1 is dont sample
    total_duration_seconds: float = -1.0  # -1 is dont sample. measurements_count take priority if both set
    sampling_frequency_hz: float = MAX_SAMPLEING_FREQUENCY

    def __post_init__(self):
        # frequency must be positive
        if self.sampling_frequency_hz < 0: 
            self.sampling_frequency_hz = MAX_SAMPLEING_FREQUENCY
    
    def sample(self, sample_function: Callable[..., T], *args, result_class: Type[R] = SamplerResult, **kwargs) -> R:
        samples = result_class()
        target_period = 1.0 / self.sampling_frequency_hz
        if self.measurements_count > 0:
            start_time = time.perf_counter()
            for _ in range(self.measurements_count):
                time_before_sample = time.perf_counter()
                samples.add_sample(sample_function(*args, **kwargs))
                # To ensure precise measurment intervals we sleep remaining time after sample function ends
                elapsed = time.perf_counter() - time_before_sample
                sleep_time = target_period - elapsed
                time.sleep(max(sleep_time, 0.0))  # if sleep time gets negative

        elif self.total_duration_seconds > 0:
            start_time = time.perf_counter()
            # `:=` operator was added in python 3.8
            while (time_before_sample := time.perf_counter()) < self.total_duration_seconds + start_time:
                samples.add_sample(sample_function(*args, **kwargs))
                # To ensure precise measurment intervals we sleep remaining time after sample function ends
                elapsed = time.perf_counter() - time_before_sample
                sleep_time = target_period - elapsed
                time.sleep(max(sleep_time, 0.0))  # if sleep time gets negative

        return samples
    
    def sample_many(
        self,
        targets: Dict[str, Tuple[Callable[..., Any], Tuple[Any, ...], Dict[str, Any]]],
        result_class: Type[R] = SamplerResult
    ) -> Dict[str, R]:
        """
        Samples multiple functions concurrently using a thread pool.
        
        `targets` format: 
        {
           "sensor_1": (read_func, (arg1,), {"kwarg1": val}),
           "sensor_2": (read_func_2, (), {})
        }
        """
        results: Dict[str, R] = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(targets)) as executor:
            future_to_name = {}
            for name, (func, args, kwargs) in targets.items():
                future = executor.submit(self.sample, func, *args, result_class=result_class, **kwargs)
                future_to_name[future] = name
            for future in concurrent.futures.as_completed(future_to_name):
                name = future_to_name[future]
                results[name] = future.result()
        
        return results


class ResultManager:
    def __init__(self, result_folder_path: Union[str, pathlib.Path] = ".", analysis_config: Optional[Dict] = None):  # can also write str | pathlib.Path in ptrhon 3.10+
        self.result_folder_path: pathlib.Path = pathlib.Path(result_folder_path,)
        self._analysis_config = analysis_config if analysis_config is not None else {}
        self._default_figure: Dict = self._analysis_config.get("visualization", {}).get("default_figure", {})
        # The yaml `default_figure` block mixes figure geometry with our own plot defaults,
        # so map it to real matplotlib kwargs instead of forwarding the raw dict to plt.subplots.
        self._default_fig_kwargs: Dict = {"figsize": self._default_figure.get("figure_size", DEFAULT_FIGURE_SIZE)}
        self._default_plot_kind: PlotKind = self._default_figure.get("default_plot_type", DEFAULT_PLOT_KIND)
        self._sub_folder: pathlib.Path = pathlib.Path(".",)
        self.result_folder_path.mkdir(exist_ok=True, parents=True)
    
    @property
    def sub_folder(self) -> pathlib.Path:
        return self._sub_folder
    
    @property
    def save_path(self) -> pathlib.Path:
        path = pathlib.Path(self.result_folder_path, self.sub_folder)
        path.mkdir(exist_ok=True)
        return path
    
    @sub_folder.setter
    def sub_folder(self, path):
        self._sub_folder = pathlib.Path(path, )
    
    def reset_sub_folder(self):
        self.sub_folder = "."
        
    def save_result(self, file_name: str, result: SamplerResult, *args, save_summary=False, **kwargs):
        csv_path = pathlib.Path(self.save_path, file_name)
        csv_path = csv_path if csv_path.suffix == ".csv" else csv_path.with_suffix(".csv")
        result.get_data_frame(*args, **kwargs).to_csv(csv_path, index=False)
        if save_summary:
            self.save_summary(file_name, result, *args, **kwargs)

    def save_summary(self, file_name: str, result: SamplerResult, *args, **kwargs):
        """Saves the result summary as a json file."""
        self.save_json(file_name, result.get_summary_dict(*args, **kwargs))

    def save_csv(self, file_name: str, data: List[Dict[float, Any]]):
        headers = data[0].keys()
        path = pathlib.Path(self.save_path, file_name)
        path = path if path.suffix == ".csv" else path.with_suffix(".csv")
        with open(str(path), "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()  # Writes the column names
            writer.writerows(data)  # Writes all rows at once
    
    def save_text(self, file_name: str, data: str):
        self.save_file(file_name=file_name, data=data, file_suffix=".txt")

    def save_json(self, file_name: str, data: Any, indent: Optional[int] = 2):
        """Saves any json compatible object (dict / list / ...) as a json file."""
        self.save_file(file_name=file_name, data=json.dumps(data, indent=indent, default=_json_default), file_suffix=".json")


    def save_file(self, file_name: str, data: str, file_suffix=""):
        path =  pathlib.Path(self.save_path, file_name)
        if file_suffix:
            path = path if path.suffix == file_suffix else path.with_suffix(file_suffix)
        with open(str(path), "w", newline="") as f:
            f.write(data)

    def plot_results(self, *results: NumericSamplerResult,
                     title: Optional[str] = None,
                     kind: Optional[PlotKind] = None,
                     by_index: bool = False, fig_kwargs: Optional[Dict] = None,
                     value_label: str = "Value[#]", 
                     show_plot: bool = False,
                     save_plot: bool = True,
                     **kwargs):
        # fig
        fig_kwargs = fig_kwargs if fig_kwargs else self._default_fig_kwargs
        kind = kind if kind else self._default_plot_kind
        fig, ax = plt.subplots(**fig_kwargs)
        col_name = ""
        for i, result in enumerate(results):
            # kind
            df = result.get_data_frame(result.sample_name if result.sample_name else f"Sample{i}")
            
            x_col = df.columns[0] if by_index else df.columns[1]
            col_name = x_col
            y_col = df.columns[2]
            label_name = df.columns[2]

            # Dynamic plot dispatching on the SAME axis (ax=ax)
            if kind == "line":
                sns.lineplot(data=df, x=x_col, y=y_col, label=label_name, ax=ax, **kwargs)
            elif kind == "scatter":
                sns.scatterplot(data=df, x=x_col, y=y_col, label=label_name, ax=ax, **kwargs)
            elif kind == "hist":
                sns.histplot(data=df, x=y_col, label=label_name, ax=ax, **kwargs)
            else:
                raise ValueError(f"Unsupported plot kind '{kind}'. Use 'line', 'scatter', or 'hist'.")
        
        # Format axes
        if kind == "hist":
            ax.set_xlabel(value_label)
            ax.set_ylabel("Count[#]")
        else:
            ax.set_xlabel(col_name)
            ax.set_ylabel(value_label)

        ax.set_title(f"Overlay {kind.title()} Plot {title if title else ('Index' if by_index else 'Time')}")
        ax.legend()
        ax.grid(True, which='both')
        fig.tight_layout()
        
        if save_plot: 
            file_name = title.lower().replace(" ", "_") if title else "figure"
            fig.savefig(pathlib.Path(self.save_path, f"{file_name}_{kind}"), bbox_inches="tight")

        if show_plot or self._analysis_config.get("visualization", {}).get("enabled", False):
            plt.show()
        else:
            plt.close(fig)

        return fig, ax

