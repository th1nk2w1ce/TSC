def get_qualification(balance_stacked, first_lvl_staked, all_referals) -> int:
    if ((balance_stacked >= 1000000000 * 250000) & (first_lvl_staked >= 1000000000 * 1250000) & (all_referals >= 25000)):
        return 12
    elif ((balance_stacked >= 1000000000 * 100000) & (first_lvl_staked >= 1000000000 * 500000) & (all_referals >= 10000)):
        return 11
    elif ((balance_stacked >= 1000000000 * 50000) & (first_lvl_staked >= 1000000000 * 250000) & (all_referals >= 5000)):
        return 10
    elif ((balance_stacked >= 1000000000 * 25000) & (first_lvl_staked >= 1000000000 * 125000) & (all_referals >= 2500)):
        return 9
    elif ((balance_stacked >= 1000000000 * 10000) & (first_lvl_staked >= 1000000000 * 50000) & (all_referals >= 1000)):
        return 8
    elif ((balance_stacked >= 1000000000 * 5000) & (first_lvl_staked >= 1000000000 * 25000) & (all_referals >= 500)):
        return 7
    elif ((balance_stacked >= 1000000000 * 2500) & (first_lvl_staked >= 1000000000 * 12500) & (all_referals >= 250)):
        return 6
    elif ((balance_stacked >= 1000000000 * 1000) & (first_lvl_staked >= 1000000000 * 5000) & (all_referals >= 100)):
        return 5
    elif ((balance_stacked >= 1000000000 * 500) & (first_lvl_staked >= 1000000000 * 2500) & (all_referals >= 50)):
        return 4
    elif ((balance_stacked >= 1000000000 * 250) & (first_lvl_staked >= 1000000000 * 1250) & (all_referals >= 25)):
        return 3
    elif ((balance_stacked >= 1000000000 * 100) & (first_lvl_staked >= 1000000000 * 500) & (all_referals >= 10)):
        return 2
    elif ((balance_stacked >= 1000000000 * 20) & (first_lvl_staked >= 1000000000 * 0) & (all_referals >= 0)):
        return 1
    return 0


def get_bon(balance_stacked, first_lvl_staked, all_referals):
    if ((balance_stacked >= 1000000000 * 250000) & (first_lvl_staked >= 1000000000 * 1250000) & (all_referals >= 25000)):
        return 4629629629629628
    elif ((balance_stacked >= 1000000000 * 100000) & (first_lvl_staked >= 1000000000 * 500000) & (all_referals >= 10000)):
        return 4243827160493826
    elif ((balance_stacked >= 1000000000 * 50000) & (first_lvl_staked >= 1000000000 * 250000) & (all_referals >= 5000)):
        return 4243827160493826
    elif ((balance_stacked >= 1000000000 * 25000) & (first_lvl_staked >= 1000000000 * 125000) & (all_referals >= 2500)):
        return 3858024691358024
    elif ((balance_stacked >= 1000000000 * 10000) & (first_lvl_staked >= 1000000000 * 50000) & (all_referals >= 1000)):
        return 3858024691358024
    elif ((balance_stacked >= 1000000000 * 5000) & (first_lvl_staked >= 1000000000 * 25000) & (all_referals >= 500)):
        return 3472222222222222
    elif ((balance_stacked >= 1000000000 * 2500) & (first_lvl_staked >= 1000000000 * 12500) & (all_referals >= 250)):
        return 3472222222222222
    elif ((balance_stacked >= 1000000000 * 1000) & (first_lvl_staked >= 1000000000 * 5000) & (all_referals >= 100)):
        return 3086419753086419
    elif ((balance_stacked >= 1000000000 * 500) & (first_lvl_staked >= 1000000000 * 2500) & (all_referals >= 50)):
        return 3086419753086419
    elif ((balance_stacked >= 1000000000 * 250) & (first_lvl_staked >= 1000000000 * 1250) & (all_referals >= 25)):
        return 2700617283950617
    elif ((balance_stacked >= 1000000000 * 100) & (first_lvl_staked >= 1000000000 * 500) & (all_referals >= 10)):
        return 2700617283950617
    elif ((balance_stacked >= 1000000000 * 20) & (first_lvl_staked >= 1000000000 * 0) & (all_referals >= 0)):
        return 2314814814814814
    return 1