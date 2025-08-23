import argparse
import csv
import logging
import os
import shutil
import sys
import urllib.parse
from csv import DictReader
from datetime import datetime
from pathlib import Path

import freeform_to_csv
import rq.convert_to_csv
import rq.fetch_routes
import rq.produce_report
from rq.utils import sanitize_path, setup_logger

logger: logging.Logger = logging.getLogger(Path(__file__).stem)

NO_REQUESTS_STR = "number"
MBX_API_PARAMS_PER_COORDINATE = [
    "snapping_include_closures",
    "snapping_include_static_closures",
    "bearings",
    "layers",
    "waypoint_names",
    "waypoint_targets",
    "approaches",
]


def transform_query_params_to_relaxed_form(queryparams: str):
    """
    Transforms the query parameters for a request with several waypoints into the parameters
    for two waypoints: starting and destination
    :param queryparams: query parameters string (in a URI-encoded or decoded form)
    :returns: a transformed query string (in decoded form)
    """
    if not queryparams:
        return queryparams

    def extract_src_and_dst_property(properties: str, delim):
        return delim.join([properties.split(delim)[0], properties.split(delim)[-1]])

    params = urllib.parse.parse_qs(urllib.parse.unquote(queryparams))
    for name in MBX_API_PARAMS_PER_COORDINATE:
        if name in params:
            params[name][0] = extract_src_and_dst_property(params[name][0], ";")

    return urllib.parse.unquote(urllib.parse.urlencode(params, doseq=True, safe=":/"))


def create_relaxed_testset(ground_truth_file: str, relaxed_testset_file: str):
    """
    Create relaxed testset from ground truth testset
    :param ground_truth_file: path to ground truth csv file
    :param relaxed_testset_file: path to new relaxed testset csv file with removed 'waypoints'
    :return: whether both files are the same
    """
    same_file = True
    no_requests = 0
    fieldnames = [
        "id",
        "desc",
        "expected",
        "src",
        "waypoints",
        "dst",
        "query",
    ]
    with open(sanitize_path(relaxed_testset_file), "w", newline="") as relaxed_testset:
        writer = csv.DictWriter(relaxed_testset, fieldnames=fieldnames)
        writer.writeheader()
        with open(sanitize_path(ground_truth_file), "r", newline="") as csvfile:
            reader = DictReader(csvfile)
            for row in reader:
                if row["waypoints"]:
                    same_file = False
                row["waypoints"] = ""
                row["query"] = transform_query_params_to_relaxed_form(row["query"])
                writer.writerow(row)
                no_requests += 1
    return no_requests, same_file


def produce_testsets(args, input_files: list, output_dir: str):
    """
    Produce the ground-truth and relaxed testsets
    :param args: program arguments
    :param input_files: a list of input free-form or csv files
    :param output_dir: directory in which to create working directories
    :return: dictionary with keys as testset labels (extracted from file names),
    and values as paths to generated testsets for both ground-truth and relaxed forms, and number of requests in each
    { label : {'ground_truth' : path, 'test' : path, NO_REQUESTS_STR : number }}
    """
    testsets = {}

    for file_name in input_files:
        sanitized_file_name = sanitize_path(file_name)
        if not os.path.exists(sanitized_file_name):
            raise FileNotFoundError(f"File {sanitized_file_name} does not exist!")

        basename = os.path.splitext(os.path.basename(sanitized_file_name))[0]
        if basename in testsets:
            raise ValueError(f"Testset {basename} repeats!")

        ground_truth_dir = os.path.join(output_dir, basename, args.first_label)
        test_dir = os.path.join(output_dir, basename, args.second_label)

        os.makedirs(ground_truth_dir, exist_ok=True)
        os.makedirs(test_dir, exist_ok=True)

        ground_truth_file = sanitize_path(
            os.path.join(ground_truth_dir, f"{basename}_{args.first_label}.csv")
        )
        test_file = os.path.join(test_dir, f"{basename}_{args.second_label}.csv")

        extension = os.path.splitext(sanitized_file_name)[1]
        if extension == ".csv":
            # todo validate the present csv
            shutil.copy(sanitized_file_name, ground_truth_file)
        else:
            freeform_to_csv.input_to_csv(sanitized_file_name, ground_truth_file)

        num, requests_are_same = create_relaxed_testset(ground_truth_file, test_file)
        if requests_are_same:
            logger.warning(
                f"Testset {basename}: {args.second_label} file '{test_file}' generated from {args.first_label} file '{ground_truth_file}' is the same!"
            )
        testsets[basename] = {
            args.first_label: ground_truth_file,
            args.second_label: test_file,
            NO_REQUESTS_STR: num,
        }

    return testsets


def fetch_routes(args, testsets: dict, label: str):
    """
    Fetch routes for specified testsets from a Mapbox API
    :param args: program arguments
    :param testsets: list of paths to csv testsets in form { args.first_label : csv_path, args.second_label : csv_path }
    :param label: label to name response files with
    :return: paths to API response JSON files in form { name : json_path }
    """
    responses = {}
    for name in [args.first_label, args.second_label]:
        csv_file = testsets[name]
        logger.info(f"Fetching routes specified in '{csv_file}'")
        output_json = os.path.join(os.path.dirname(csv_file), f"{label}_response.json")
        responses[name] = output_json
        rq.fetch_routes.main(
            [
                args.host,
                csv_file,
                args.token,
                output_json,
                "--profile",
                args.profile,
                "--query",
                args.query,
                "--threads",
                str(args.threads),
                "--logger",
                args.logger,
            ]
        )
    return responses


def extract_data_from_responses(args, testsets: dict, responses: dict, label: str):
    """
    Extract data from response JSON files into a new CSV file
    :param args: program arguments
    :param testsets: list of paths to csv testsets that were used to generate the responses in form
    { args.first_label : csv_path, args.second_label : csv_path }
    :param responses: corresponding list of paths to API JSON responses in form { name : json_path }
    :param label: label to name each new file with
    :return: paths to new CSV files and number of extracted route responses in form { args.first_label : csv_path,
    args.second_label: csv_path, args.first_label-number : num, args.first_label-number : num }
    """
    extracted_data = {}
    for name in [args.first_label, args.second_label]:
        response_file = responses[name]
        logger.info(f"Extracting data specified in '{response_file}'")
        output_csv = os.path.join(
            os.path.dirname(response_file), f"{label}_response.csv"
        )
        extracted_data[name] = output_csv
        extracted_data[f"{name}-{NO_REQUESTS_STR}"] = rq.convert_to_csv.main(
            [
                args.host,
                testsets[name],
                response_file,
                args.token,
                "--output_file",
                output_csv,
                "--query",
                args.query,
                "--profile",
                args.profile,
                "--logger",
                args.logger,
            ]
        )
        logger.debug(
            f"Extracted data on responses in '{response_file}': {extracted_data[f'{name}-{NO_REQUESTS_STR}']} routes"
        )
    return extracted_data


def produce_report(args, response_csvs: dict, output_dir: str, label: str):
    """
    Generate a comparison report between ground-truth and relaxed testset runs
    :param args: program arguments
    :param response_csvs: paths to parsed CSV responses in form { args.first_label : csv_path , args.second_label : csv_path }
    :param output_dir: directory in which to save the report
    :param label: label prefix to name the report with
    :return: path to the generated report
    """
    output_file = os.path.join(output_dir, f"{label}_report.csv")
    num_requests = rq.produce_report.main(
        [
            "--first-label",
            args.first_label,
            "--second-label",
            args.second_label,
            "--first-csv",
            response_csvs[args.first_label],
            "--second-csv",
            response_csvs[args.second_label],
            "--output-file",
            output_file,
            "--experiment-name",
            f'"{label}: {args.first_label} vs {args.second_label}"',
            "--logger",
            args.logger,
        ]
    )
    return output_file, num_requests


def parse_args(sysargs: list):
    """
    Parse command line arguments
    :param sysargs: command line arguments
    :return: parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Program which produces a comparison of changes between ground-truth routes and the same routes with relaxed geometry constraints."
    )
    parser.add_argument(
        "input",
        nargs="+",
        help="a collection of ground-truth testsets, free-form or csv files",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=f"results/test-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}",
        help="directory to save the results to",
    )
    parser.add_argument(
        "--logger",
        type=str,
        help="Verbosity of output",
        required=False,
        default="INFO",
        choices=["INFO", "DEBUG", "ERROR", "CRITICAL"],
    )
    parser.add_argument(
        "--host",
        type=str,
        help="Address of the server (stack) to obtain route responses from. Example: https://api.mapbox.com",
        required=True,
    )
    parser.add_argument(
        "--first-label",
        type=str,
        help="Label prefix/suffix to assign to each ground-truth result and file",
        default="gt",
    )
    parser.add_argument(
        "--second-label",
        type=str,
        help="Label prefix/suffix to assign to each relaxed result and file",
        default="rel",
    )
    parser.add_argument(
        "--profile",
        type=str,
        help='Mapbox custom profile like "mapbox/driving-traffic"',
        required=True,
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Default query parameters for each request in URI form",
        required=False,
    )
    parser.add_argument(
        "--threads",
        type=int,
        help="Number of threads to use when fetching routes",
        required=False,
        default=1,
    )
    parser.add_argument(
        "--token", type=str, help="A mapbox API access token", required=True
    )

    return parser.parse_args(sysargs)


def setup_loggers(verbosity: str):
    """
    Setup program loggers
    :param verbosity: logger level 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    """
    logger = setup_logger(Path(__file__).stem, verbosity)
    freeform_to_csv.logger = setup_logger(freeform_to_csv.logger.name, verbosity)


def main(sysargs: list):
    """
    Main method: parse system arguments, create working directory, convert testsets, run route fetching, data extraction, report production
    :param sysargs: command-line arguments
    """
    args = parse_args(sysargs)
    setup_loggers(args.logger)
    logger.debug(f"Script is called with arguments: {args}")
    os.makedirs(args.output)
    # Sanitize input filenames
    sanitized_inputs = [sanitize_path(input_file) for input_file in args.input]
    testsets = produce_testsets(args, sanitized_inputs, args.output)
    reports = {}
    for label in testsets:
        no_requests = testsets[label][NO_REQUESTS_STR]
        responses = fetch_routes(args, testsets[label], label)
        response_csvs = extract_data_from_responses(
            args, testsets[label], responses, label
        )
        reports[label], num_processed = produce_report(
            args, response_csvs, os.path.join(str(args.output), label), label
        )
        logger.critical(
            f"Testset {label}: produced comparison for {num_processed}/{no_requests} "
            f"routes ({response_csvs[f'{args.first_label}-{NO_REQUESTS_STR}']} for {args.first_label}, "
            f"{response_csvs[f'{args.second_label}-{NO_REQUESTS_STR}']} for {args.second_label})"
        )
        if num_processed != no_requests:
            logger.error(
                f"Testset {label}: Number of requests {no_requests} does not match the "
                f"number of processed routes {num_processed}!"
            )

    logger.critical(f"Reports are {reports}")


if __name__ == "__main__":
    main(sys.argv[1:])
