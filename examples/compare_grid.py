#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import argparse
from netCDF4 import Dataset

SEP = "-" * 80

def read_nc_summary(path):
    ds = Dataset(path, "r")
    try:
        dims = {name: len(dim) for name, dim in ds.dimensions.items()}

        vars_info = {}
        for vname, var in ds.variables.items():
            # shape and dims as tuple/list
            shape = tuple(var.shape)
            dims_of_var = tuple(var.dimensions)
            dtype = str(var.dtype)
            # collect a few common attrs if present
            attrs = {}
            for k in ("units", "long_name", "standard_name", "_FillValue", "scale_factor", "add_offset"):
                if k in var.ncattrs():
                    attrs[k] = getattr(var, k)
            vars_info[vname] = {
                "shape": shape,
                "dims": dims_of_var,
                "dtype": dtype,
                "attrs": attrs,
            }

        gattrs = {k: getattr(ds, k) for k in ds.ncattrs()}
    finally:
        ds.close()

    return {
        "dims": dims,            # dict: dim_name -> length
        "vars": vars_info,       # dict: var_name -> info
        "gattrs": gattrs,        # dict of global attributes
    }

def format_shape(shape):
    return "(" + ", ".join(str(s) for s in shape) + ")"

def print_dict_sorted(d, title):
    print(title)
    for k in sorted(d):
        print(f"  {k}: {d[k]}")
    print()

def compare(file1, file2):
    info1 = read_nc_summary(file1)
    info2 = read_nc_summary(file2)

    print(SEP)
    print(f"Comparing files:\n  A: {file1}\n  B: {file2}")
    print(SEP)

    # Dimensions summary
    print("Dimensions:")
    d1 = info1["dims"]
    d2 = info2["dims"]
    all_dims = sorted(set(d1) | set(d2))
    for dn in all_dims:
        a = d1.get(dn, None)
        b = d2.get(dn, None)
        status = "==" if a == b else "!="
        print(f"  {dn:<20} A:{str(a):>8}  B:{str(b):>8}  [{status}]")
    print(SEP)

    # Variables present only in one file
    vset1 = set(info1["vars"].keys())
    vset2 = set(info2["vars"].keys())
    only_a = sorted(vset1 - vset2)
    only_b = sorted(vset2 - vset1)
    common = sorted(vset1 & vset2)

    print("Variables only in A:")
    if only_a:
        for v in only_a:
            sh = info1["vars"][v]["shape"]
            print(f"  {v}  shape={format_shape(sh)}")
    else:
        print("  None")
    print()

    print("Variables only in B:")
    if only_b:
        for v in only_b:
            sh = info2["vars"][v]["shape"]
            print(f"  {v}  shape={format_shape(sh)}")
    else:
        print("  None")
    print(SEP)

    # Compare common variables: shape, dtype, dims
    print("Common variables (shape, dtype, dims):")
    max_name_len = max([len(v) for v in common], default=1)
    for v in common:
        a = info1["vars"][v]
        b = info2["vars"][v]
        same_shape = a["shape"] == b["shape"]
        same_dtype = a["dtype"] == b["dtype"]
        same_dims  = a["dims"]  == b["dims"]

        status = []
        status.append("shape==" if same_shape else "shape!=")
        status.append("dtype==" if same_dtype else "dtype!=")
        status.append("dims=="  if same_dims  else "dims!=")

        print(f"  {v:<{max_name_len}}  "
              f"A{format_shape(a['shape'])}/{a['dtype']}/{a['dims']}  |  "
              f"B{format_shape(b['shape'])}/{b['dtype']}/{b['dims']}  "
              f" -> {'; '.join(status)}")
    print(SEP)

    # Optional: show a few attribute mismatches for common variables
    print("Attribute quick check (units, long_name, standard_name, _FillValue, scale_factor, add_offset):")
    for v in common:
        a_attrs = info1["vars"][v]["attrs"]
        b_attrs = info2["vars"][v]["attrs"]
        keys = sorted(set(a_attrs) | set(b_attrs))
        diffs = []
        for k in keys:
            if a_attrs.get(k, None) != b_attrs.get(k, None):
                diffs.append(k)
        if diffs:
            print(f"  {v}: differs in {', '.join(diffs)}")
    print(SEP)

    # Global attributes that differ (names or values)
    print("Global attributes differences:")
    ga1 = info1["gattrs"]
    ga2 = info2["gattrs"]
    all_g = sorted(set(ga1) | set(ga2))
    any_diff = False
    for k in all_g:
        a = ga1.get(k, None)
        b = ga2.get(k, None)
        if a != b:
            any_diff = True
            # print short versions to avoid huge outputs
            a_str = str(a)
            b_str = str(b)
            if len(a_str) > 80: a_str = a_str[:77] + "..."
            if len(b_str) > 80: b_str = b_str[:77] + "..."
            print(f"  {k}:")
            print(f"    A: {a_str}")
            print(f"    B: {b_str}")
    if not any_diff:
        print("  None")
    print(SEP)

def main():
    parser = argparse.ArgumentParser(
        description="Compare two NetCDF grid files by variable names and shapes."
    )
    parser.add_argument("file_a", help="Path to first NetCDF file")
    parser.add_argument("file_b", help="Path to second NetCDF file")
    args = parser.parse_args()

    try:
        compare(args.file_a, args.file_b)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"I/O error: {e}", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
