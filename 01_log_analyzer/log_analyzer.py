import gzip
from pathlib import Path
from typing import Any

# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '  
#                     '$request_time';

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
}


def calculating_median(sample) -> float:
    n: int = len(sample)
    index: int = n // 2
    if n % 2:
        return sorted(sample)[index]
    return sum(sorted(sample)[index - 1:index + 1]) / 2


def read_log(file) -> str:
    open_file = gzip.open if file.endswith(".gz") else open
    with open_file(file, mode="rt", encoding="utf_8") as file:
        for line in file:
            yield line


def parse_log() -> dict:
    num_of_row: int = 0
    num_of_errors: int = 0
    summary: dict = {}
    for row in read_log(latest_file()):
        num_of_row += 1
        if not row:
            num_of_errors += 1
            continue
        elements: list[str] = row.split(' ')
        if not elements[7][0] == '/':
            num_of_errors += 1
            raise ValueError
        summary_information(row, summary)
    return summary


def statistics_generation(data) -> list:
    # count - сĸольĸо раз встречается URL, абсолютное значение
    # count_perc - сĸольĸо раз встречается URL, в процентах относительно общего числа запросов
    # time_sum - суммарный $request_time для данного URL'а, абсолютное значение
    # time_perc - суммарный $request_time для данного URL'а, в процентах относительно общего $request_time всех запросов
    # time_avg - средний $request_time для данного URL'а
    # time_max - маĸсимальный $request_time для данного URL'а
    # time_med - медиана $request_time для данного URL'а
    num_of_unique_elem: int = len(data)
    total_request_time: float = 0
    table_for_report: list[dict[str, float]] = list()
    for url, request_time in data.items():
        url_data: dict[str, float] = dict()
        url_data['url'] = url
        url_data['count'] = len(request_time)
        url_data['count_perc'] = url_data['count'] / num_of_unique_elem
        url_data['time_sum'] = sum(request_time)
        if total_request_time != 0:
            url_data['time_perc'] = 100 * url_data['time_sum'] / total_request_time
        else:
            url_data['time_perc'] = 0
        url_data['time_avg'] = url_data['time_sum'] / url_data['count']
        url_data['time_max'] = max(request_time)
        url_data['time_med'] = calculating_median(request_time)
        total_request_time += url_data['time_sum']
        table_for_report.append(url_data)
    return table_for_report


def summary_information(data, summary) -> dict:
    num_unique_elements: int = 0
    elements: Any = data.split(' ')
    if not elements[7][0] == '/':
        raise ValueError
    url: str = elements[7]
    request_time: float = float(elements[-1])
    if url not in summary.keys():
        summary[url] = []
        num_unique_elements += 1
    summary[url].append(request_time)
    return summary


def latest_file() -> str:
    path = config['LOG_DIR']
    files = [path.name for path in Path(path).glob('nginx-access-ui.log-*.gz')]
    return config["LOG_DIR"] + "/" + max(files)


def main() -> None:
    total_data = parse_log()
    print(statistics_generation(total_data))


if __name__ == "__main__":
    main()
