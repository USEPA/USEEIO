""" Functions to support the processing of CEDA MRIO models"""

def clean_ceda_M_matrix(M, fields_to_rename, **kwargs):
    M = M.rename(columns=fields_to_rename)
    M_melted = M.melt(
        id_vars=['CountryCode', 'MRIO Sector'], value_name='EF', var_name='flow'
    )
    M_melted = M_melted.groupby(
        ['CountryCode', 'MRIO Sector', 'flow']
    ).sum().reset_index()

    M_flows_as_cols = M_melted.pivot(
        index=['CountryCode', 'MRIO Sector'], columns='flow', values='EF'
    ).reset_index()
    M_flows_as_cols.columns.name = None
    return M_flows_as_cols
