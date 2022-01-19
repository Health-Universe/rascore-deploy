# -*- coding: utf-8 -*-

"""
Copyright (C) 2022 Mitchell Isaac Parker <mitch.isaac.parker@gmail.com>

This file is part of the rascore project.

The rascore project cannot be copied, edited, and/or distributed without the express
permission of Mitchell Isaac Parker <mitch.isaac.parker@gmail.com>.
"""

import pandas as pd
from tqdm import tqdm

from ..functions import *


def get_index_interf(
    df,
    index,
    interf_dict,
    interf_resid_lst=None,
    min_area=200,
    cont_dist=5,
    iso_interf=False,
    het_interf=False,
    search_interf_cont_lst=None,
    search_cb_dist_lst=None,
    search_max_dist=0.7,
    coord_path_col=None,
):

    if coord_path_col is None:
        coord_path_col = renum_path_col

    index_df = get_df_at_index(df, index)

    coord_path = index_df.at[index, coord_path_col]
    modelid = index_df.at[index, modelid_col]
    chainid = index_df.at[index, chainid_col]

    interf_df = pd.DataFrame()

    for interf in list(interf_dict[coord_path][chainid].keys()):

        add_interf = True

        if float(interf_dict[coord_path][chainid][interf][interf_area_col]) < min_area:
            add_interf = False

        interf_iso_status = interf_dict[coord_path][chainid][interf][iso_col]
        if iso_interf:
            if not interf_iso_status:
                add_interf = False
        if het_interf:
            if interf_iso_status:
                add_interf = False

        if add_interf:
            interf_path = interf_dict[coord_path][chainid][interf][interf_path_col]

            structure = load_coord(interf_path)

            neighbors = get_neighbors(structure)

            resid_lst = str_to_lst(
                interf_dict[coord_path][chainid][interf][atomid_cont_col]
            )

            interf_cont_lst = list()
            cb_dist_lst = list()

            add_interf = True
            if interf_resid_lst is not None:
                add_interf = False

            for resid in resid_lst:

                if interf_resid_lst is not None:
                    if extract_int(resid) in interf_resid_lst:
                        add_interf = True

                if resid is not None and add_interf:

                    if has_resid(
                        structure, chainid, resid_to_tuple(resid), modelid=modelid
                    ):
                        residue = structure[fix_val(modelid, return_int=True)][chainid][
                            resid_to_tuple(resid)
                        ]

                        resname = get_resname(residue)

                        if resname == "GLY":
                            atomid = "CA"
                        else:
                            atomid = "CB"

                        for cont_residue in get_residue_cont(
                            neighbors, residue, max_dist=cont_dist, level="R"
                        ):
                            cont_chainid = get_reschainid(cont_residue)
                            cont_resid = get_resnum(cont_residue)
                            cont_resname = get_resname(cont_residue)

                            if is_aa(cont_residue) and cont_chainid != chainid:

                                if cont_resname == "GLY":
                                    cont_atomid = "CA"
                                else:
                                    cont_atomid = "CB"

                                if cont_resid is not None:

                                    interf_cont = lst_to_str(
                                        sort_lst([resid, cont_resid]),
                                        join_txt=":",
                                    )

                                    if interf_cont not in interf_cont_lst:

                                        cb_dist = calc_atom_dist(
                                            structure,
                                            modelid_1=modelid,
                                            chainid_1=chainid,
                                            resid_1=resid,
                                            atomid_1=atomid,
                                            modelid_2=modelid,
                                            chainid_2=cont_chainid,
                                            resid_2=cont_resid,
                                            atomid_2=cont_atomid,
                                        )

                                        interf_cont_lst.append(interf_cont)
                                        cb_dist_lst.append(cb_dist)

            if search_interf_cont_lst is not None and search_cb_dist_lst is not None:
                if (
                    calc_q_score(
                        i_cont_lst=search_interf_cont_lst,
                        j_cont_lst=interf_cont_lst,
                        i_dist_lst=search_cb_dist_lst,
                        j_dist_lst=cb_dist_lst,
                    )
                    > search_max_dist
                ):
                    add_interf = False

        if add_interf:
            temp_df = index_df.copy(deep=True)

            for col in list(interf_dict[coord_path][chainid][interf].keys()):
                temp_df.at[index, col] = interf_dict[coord_path][chainid][interf][col]

            temp_df.at[index, interf_col] = interf
            temp_df.at[index, interf_cont_col] = lst_to_str(interf_cont_lst)
            temp_df.at[index, cb_dist_col] = lst_to_str(cb_dist_lst)

            interf_df = pd.concat([interf_df, temp_df], sort=False)

    return interf_df


def build_interf_table(
    df,
    interf_dict,
    interf_table_path=None,
    interf_resids=None,
    min_area=200,
    cont_dist=5,
    iso_interf=False,
    het_interf=False,
    search_coord_path=None,
    search_chainid=None,
    search_interf=None,
    search_max_dist=0.7,
    coord_path_col=None,
):

    if coord_path_col is None:
        coord_path_col = renum_path_col

    interf_df = pd.DataFrame()

    interf_resid_lst = res_to_lst(interf_resids)

    search_interf_cont_lst = None
    search_cb_dist_lst = None

    if (
        search_coord_path is not None
        and search_chainid is not None
        and search_interf is not None
    ):
        search_df = mask_equal(df, coord_path_col, search_coord_path)
        search_df = mask_equal(search_df, chainid_col, search_chainid)

        search_df = get_index_interf(
            search_df,
            0,
            interf_dict,
            cont_dist=cont_dist,
            coord_path_col=coord_path_col,
        )

        if len(mask_equal(search_df, interf_col, str(search_interf))) > 0:
            search_interf = str(search_interf)
        elif len(mask_equal(search_df, interf_col, int(search_interf))) > 0:
            search_interf = int(search_interf)

        search_df = mask_equal(search_df, interf_col, search_interf)

        search_interf_cont_lst = str_to_lst(
            search_df.at[0, interf_cont_col], return_str=True
        )
        search_cb_dist_lst = str_to_lst(search_df.at[0, cb_dist_col], return_float=True)

    for index in tqdm(
        list(df.index.values), desc="Building interface table", position=0, leave=True
    ):

        interf_df = pd.concat(
            [
                interf_df,
                get_index_interf(
                    df,
                    index,
                    interf_dict,
                    min_area=min_area,
                    cont_dist=cont_dist,
                    interf_resid_lst=interf_resid_lst,
                    iso_interf=iso_interf,
                    het_interf=het_interf,
                    search_interf_cont_lst=search_interf_cont_lst,
                    search_cb_dist_lst=search_cb_dist_lst,
                    search_max_dist=search_max_dist,
                    coord_path_col=coord_path_col,
                ),
            ],
            sort=False,
        )

    interf_df = interf_df.reset_index(drop=True)

    interf_df[interf_id_col] = interf_df[pdb_id_col] + interf_df[interf_col]

    if interf_table_path is not None:
        save_table(interf_table_path, interf_df)
    else:
        return interf_df

    print("Built interface table!")
