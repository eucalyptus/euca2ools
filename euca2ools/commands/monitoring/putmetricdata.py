# Copyright (c) 2013-2016 Hewlett Packard Enterprise Development LP
#
# Redistribution and use of this software in source and binary forms,
# with or without modification, are permitted provided that the following
# conditions are met:
#
#   Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import argparse
import csv
import io

from requestbuilder import Arg
import requestbuilder.exceptions

from euca2ools.commands.argtypes import delimited_list
from euca2ools.commands.monitoring import CloudWatchRequest
from euca2ools.commands.monitoring.argtypes import cloudwatch_dimension


POINTS_PER_REQUEST = 20
DATUM_KEYS = {'dim': 'Dimensions',
              'metric': 'MetricName',
              'max': 'Maximum',
              'min': 'Minimum',
              'count': 'SampleCount',
              'sum': 'Sum',
              'ts': 'Timestamp',
              'unit': 'Unit',
              'val': 'Value'}


class PutMetricData(CloudWatchRequest):
    """
    Add data values or statistics to a CloudWatch metric

    A metric datum consists of a metric name, any of several attributes,
    and either a simple, numeric value (-v) or a set of statistical
    values (-s).

    All metric data in a given invocation of %(prog)s must belong to one
    namespace.  %(prog)s supports the following attributes (and
    equivalent aliases, in parentheses) for all data.  Each of
    these attributes has a corresponding command line option that
    specifies that attribute for all metric data.

      * MetricName (metric)
      * Dimensions (dim)
      * Timestamp (ts)
      * Unit (unit)

    Simple metric data have one additional attribute for their values:

      * Value (val)

    Statistical metric data have four additional attributes:

      * Maximum (max)
      * Minimum (min)
      * SampleCount (count)
      * Sum (sum)

    The -v/--value option allows you to specify the value of a simple
    metric datum.  To specify other attributes for data given using
    this option, use the options that correspond to them, such as
    -d/--dimensions.  In particular, the -m/--metric-name option is
    required when -v/--value is used.

    The -s/--metric-datum option allows for full control of each data
    point's attributes.  This is necessary for statistical data
    points.  To specify a metric datum using this option, join each
    attribute's name or alias from the lists above with its value
    using an '=' character, and join each of those pairs with ','
    characters.  If a value contains a ',' character, surround the
    entire attribute with '"' characters.

    For example, each of the following is a valid string
    to pass to -s/--metric-datum:

        MetricName=MyMetric,Value=1.5

        MetricName=MyMetric,Maximum=5,Minimum=1,SampleCount=5,Sum=10

        metric=MyMetric,val=9,"dim=InstanceId:i-12345678,Volume:/dev/sda"

    Attributes specified via -s/--metric-datum take precedence over those
    specified with attribute-specific command line options, such as
    -d/--dimensions.

    Timestamps must use a format specified in ISO 8601, such as
    "1989-11-09T19:17:45.000+01:00".  Note that the CloudWatch
    service does not accept data with timestamps more than two weeks
    in the past.

    Dimensions' attributes are specified as a comma-separated list
    of dimension names and values that are themselves separated by
    ':' characters.  This means that when more than one dimension is
    necessary, the entire Dimensions attribute must be enclosed in '"'
    characters.  Most shell environments require this to be escaped.
    """

    ARGS = [Arg('-n', '--namespace', dest='Namespace', required=True,
                help='namespace for the new metric data (required)'),
            Arg('-v', '--value', dest='simple_values', route_to=None,
                metavar='FLOAT', type=float, action='append',
                help='''a simple value for a metric datum.  Each use
                specifies a new metric datum.'''),
            Arg('-s', '--metric-datum', dest='attr_values', route_to=None,
                action='append', metavar='KEY1=VALUE1,KEY2=VALUE2,...',
                help='''names and values of the attributes for a metric
                datum.  When values include ',' characters, enclose the
                entire name/value pair in '"' characters.'''),
            # Euca2ools 3.4 extended the "key=value"-based syntax to allow
            # one to supply arbitrary attributes of each datum.  Since this
            # this format is a strict superset of the original format for
            # statistic values we silently treat the old option names as
            # aliases for the newer, generic one.
            Arg('--statistic-values', '--statisticValues', action='append',
                dest='attr_values', route_to=None, help=argparse.SUPPRESS),
            Arg('-m', '--metric-name', route_to=None, metavar='METRIC',
                help='name of the metric to add metric data to'),
            Arg('-d', '--dimensions', metavar='KEY1=VALUE1,KEY2=VALUE2,...',
                route_to=None,
                type=delimited_list(',', item_type=cloudwatch_dimension),
                help='''one or more dimensions to associate with the new
                metric data'''),
            Arg('-t', '--timestamp', route_to=None,
                metavar='YYYY-MM-DDThh:mm:ssZ',
                help='timestamp for the new metric data'),
            Arg('-u', '--unit', route_to=None, metavar='UNIT',
                help='''unit in which to report the new metric data
                points (e.g. Bytes)''')]

    def configure(self):
        CloudWatchRequest.configure(self)
        data = []
        # Plain values
        for val in self.args.get('simple_values') or ():
            data.append(self.__build_datum_from_value(val))
        # Key/value-based data
        for val in self.args.get('attr_values') or ():
            data.append(self.__build_datum_from_pairs(val))
        self.args['data'] = data

    def main(self):
        # The API limits us to 20 points per request.  There are also
        # limits of 40 KB per POST request and 8 KB per GET request
        # that we do not consider here.
        data = self.args.get('data') or []
        for slice_start in range(0, len(data), POINTS_PER_REQUEST):
            slice_end = min(slice_start + POINTS_PER_REQUEST, len(data))
            self.params['MetricData'] = {'member': data[slice_start:slice_end]}
            self.send()
        return self.args['data']

    def __build_datum_from_value(self, value):
        datum = {}
        try:
            datum['Value'] = float(value)
        except ValueError:
            raise argparse.ArgumentTypeError(
                "argument -v/--value: value '{0}' must be numeric"
                .format(value))
        self.__complete_datum(datum)
        if not datum.get('MetricName'):
            raise requestbuilder.exceptions.ArgumentError(
                'argument -v/--value requires -m/--metric-name')
        return datum

    def __build_datum_from_pairs(self, pairs_as_str):
        statistic_set_keys = ['Maximum', 'Minimum', 'SampleCount', 'Sum']

        datum = {}
        if not pairs_as_str.strip():
            raise argparse.ArgumentTypeError(
                "argument -s/--metric-datum: value must not be empty")
        for pair in next(csv.reader(io.BytesIO(pairs_as_str))):
            try:
                key, val = pair.split('=')
            except ValueError:
                if pair.startswith('dim=') or pair.startswith('Dimensions='):
                    raise argparse.ArgumentTypeError(
                        "argument -s/--metric-datum: dimension names and "
                        "values in datum '{0}' must be separated with ':', "
                        "not '='".format(pairs_as_str))
                raise argparse.ArgumentTypeError(
                    "argument -s/--metric-datum: '{0}' in datum '{1}' must "
                    "have format KEY=VALUE,...".format(pair, pairs_as_str))
            key = DATUM_KEYS.get(key, key)
            if key in statistic_set_keys:
                try:
                    datum.setdefault('StatisticValues', {})[key] = float(val)
                except ValueError:
                    raise argparse.ArgumentTypeError(
                        "argument -s/--metric-datum: {0} value for datum "
                        "'{1}' must be numeric".format(key, pairs_as_str))
            elif key == 'Value':
                try:
                    datum[key] = float(val)
                except ValueError:
                    raise argparse.ArgumentTypeError(
                        "argument -s/--metric-datum: {0} value for datum "
                        "'{1}' must be numeric".format(key, pairs_as_str))
            elif key == 'Dimensions':
                datum.setdefault(key, {'member': []})
                for dim_pair in val.split(','):
                    try:
                        dim_name, dim_val = dim_pair.split(':')
                    except ValueError:
                        raise argparse.ArgumentTypeError(
                            "argument -s/--metric-datum: dimension '{0}' for "
                            "datum '{1}' must have format KEY:VALUE,..."
                            .format(dim_pair, pairs_as_str))
                    datum[key]['member'].append(
                        {'Name': dim_name, 'Value': dim_val})
            elif key in ('MetricName', 'Timestamp', 'Unit'):
                datum[key] = val
            else:
                raise argparse.ArgumentTypeError(
                    "argument -s/--metric-datum: datum '{0}' contains "
                    "unrecognized attribute '{1}'".format(pairs_as_str, key))
        self.__complete_datum(datum)

        # Validate
        if not datum.get('MetricName'):
            raise argparse.ArgumentTypeError(
                "argument -s/--metric-datum: datum '{0}' must have a "
                "metric name; supply one individually with 'MetricName=NAME' "
                "or set a default for this request with -m/--metric-name"
                .format(pairs_as_str))
        if 'StatisticValues' in datum:
            if 'Value' in datum:
                raise argparse.ArgumentTypeError(
                    "argument -s/--metric-datum: datum '{0}' must not "
                    "contain both Value and {1} attributes".format(
                        pairs_as_str, next(datum['StatisticValues'].values())))
            for key in statistic_set_keys:
                if key not in datum['StatisticValues']:
                    raise argparse.ArgumentTypeError(
                        "argument -s/--metric-datum: a {0} is required for "
                        "statistic datum '{1}'".format(key, pairs_as_str))
        elif 'Value' not in datum:
            raise argparse.ArgumentTypeError(
                "argument -s/--metric-datum: datum '{0}' must contain "
                "either a Value or a Maximum, Minimum, SampleCount, and Sum"
                .format(pairs_as_str))
        return datum

    def __complete_datum(self, datum):
        attr_map = {
            'MetricName': 'metric_name',
            'Timestamp': 'timestamp',
            'Unit': 'unit'}
        for key, val in attr_map.items():
            if self.args.get(val):
                datum.setdefault(key, self.args.get(val))
        if self.args.get('dimensions'):
            datum.setdefault('Dimensions',
                             {'member': self.args.get('dimensions')})
